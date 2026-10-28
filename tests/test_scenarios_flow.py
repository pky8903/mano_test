import dataclasses

import numpy as np
import pytest

from opc_osc import store
from opc_osc.model import solve_direct
from opc_osc.pipeline import run_scenario
from opc_osc.scenarios import MOVIE_KEEP, PRESETS


def test_presets_hold_documented_quantities_fixed():
    base = PRESETS["main"]
    for sid in ("range_13", "range_18", "range_24"):
        s = PRESETS[sid]
        assert (s.a, s.b, s.d_um, s.E0_nm, s.E_bulk_nm) == (base.a, base.b, base.d_um, base.E0_nm, 0.0)
    for sid in ("damp_025", "damp_030", "damp_040"):
        s = PRESETS[sid]
        assert (s.b, s.M, s.d_um, s.E0_nm) == (base.b, base.M, base.d_um, base.E0_nm)
    assert [PRESETS[f"damp_{k}"].a for k in ("025", "030", "040")] == [0.25, 0.30, 0.40]
    for sid in ("scale_050", "scale_200", "scale_neg"):
        s = PRESETS[sid]
        assert (s.a, s.b, s.M) == (base.a, base.b, base.M)
    assert all(PRESETS[s].notes_only for s in ("counter_9", "counter_12"))
    assert {6, 7, 8, 9} <= set(base.keep)


def test_config_hash_is_stable_and_sensitive():
    s = PRESETS["main"]
    assert s.config_hash() == dataclasses.replace(s).config_hash()
    assert s.config_hash() != dataclasses.replace(s, a=0.26).config_hash()


def test_background_extension_isolates_edge_response():
    a_tot, _ = run_scenario(PRESETS["bg_total"])
    a_ref, _ = run_scenario(PRESETS["bg_ref"])
    a_main, _ = run_scenario(PRESETS["main"])
    extra = a_tot["u_star_nm"] - a_ref["u_star_nm"]
    np.testing.assert_allclose(extra, a_main["u_star_nm"], atol=1e-13)
    # the uniform-background response is NOT flat near the truncated boundary
    ub = a_ref["u_star_nm"]
    assert abs(ub[0] - ub[2000]) > 1e-3


def test_flow_config_to_store_to_scene_inputs(tmp_path):
    s = PRESETS["main"]
    arrays, summary = run_scenario(s)
    store.save(arrays, summary, tmp_path)
    loaded, meta = store.load("main", tmp_path)
    assert meta["config_hash"] == s.config_hash()
    assert list(loaded["iters"]) == MOVIE_KEEP + [summary["final_iter"]]
    assert meta["final_iter"] == 806
    # retained states are consistent: e = E - A u on the stored window (interior of the crop)
    from opc_osc.model import apply

    k = s.store_controls
    full_E = s.forcing()
    for i in (0, 3, 9):
        u = np.zeros(s.n_controls)
        u[:k] = loaded["u_hist_nm"][i]
        # crop is exact here: early states have support far below k controls
        np.testing.assert_allclose(full_E[: k - 20] - apply(s.model, u)[: k - 20], loaded["e_hist_nm"][i][: k - 20], atol=1e-14)
    np.testing.assert_allclose(loaded["u_final_nm"], solve_direct(s.model, full_E), atol=1e-10)
    assert meta["mask_variation_nm"] == pytest.approx(0.9140878, abs=1e-6)


def test_store_detects_tampering(tmp_path):
    arrays, summary = run_scenario(PRESETS["damp_040"])
    store.save(arrays, summary, tmp_path)
    z = dict(np.load(tmp_path / "damp_040.npz"))
    z["u_star_nm"][5] += 1e-9
    np.savez_compressed(tmp_path / "damp_040.npz", **z)
    with pytest.raises(ValueError):
        store.load("damp_040", tmp_path)
