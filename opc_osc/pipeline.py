"""Scenario -> solved arrays -> metrics. Pure numerics; no rendering."""

from __future__ import annotations

import numpy as np

from . import metrics as mt
from .model import p_iterate, solve_direct
from .scenarios import Scenario


def run_scenario(s: Scenario) -> tuple[dict[str, np.ndarray], dict]:
    """Returns (arrays, summary). Full-domain arrays are kept for u*, u_final and E;
    retained iteration states are cropped to s.store_controls."""
    model = s.model
    E = s.forcing()
    x = mt.positions_um(s.n_controls, s.d_um)
    u_star = solve_direct(model, E)
    arrays: dict[str, np.ndarray] = {"x_um": x, "E_nm": E, "u_star_nm": u_star}
    summary: dict = {
        "id": s.id,
        "config_hash": s.config_hash(),
        "config": s.config(),
        "direct_residual_nm": mt.max_abs_error(E - _apply(model, u_star)),
    }

    # single-control responses (columns of A) for the coupling scene: interior and left-edge control
    k = s.store_controls
    for name, j in (("resp_interior_nm", s.response_control), ("resp_edge_nm", 0)):
        unit = np.zeros(s.n_controls)
        unit[j] = 1.0
        arrays[name] = _apply(model, unit)[:k]
    summary["response_control"] = s.response_control

    if s.iterate:
        it = p_iterate(model, E, tol_nm=s.tol_nm, keep=list(s.keep))
        if not it.converged:
            raise RuntimeError(f"{s.id}: P iteration did not converge")
        k = s.store_controls
        arrays.update(
            iters=np.asarray(it.kept),
            u_hist_nm=np.stack(it.u)[:, :k],
            e_hist_nm=np.stack(it.e)[:, :k],
            du_hist_nm=np.stack(it.du)[:, :k],
            u_final_nm=it.u[-1],
            e_final_nm=it.e[-1],
            residual_history_nm=it.residual_history,
        )
        summary.update(
            final_iter=it.final_iter,
            final_residual_nm=it.final_residual_nm,
            tol_nm=it.tol_nm,
            eta=it.eta,
            max_abs_u_final_minus_direct_nm=float(np.max(np.abs(it.u[-1] - u_star))),
        )
        u_view = it.u[-1]
    else:
        u_view = u_star

    summary["mask_variation_nm"] = mt.mask_variation(u_view, x, s.window_um)
    summary["window_um"] = list(s.window_um)
    summary["u0_nm"] = float(u_view[0])

    if s.E_bulk_nm == 0.0 and s.E0_nm != 0.0 and model.b > 0:
        dm = mt.boundary_solution(model, s.E0_nm)
        summary["prediction"] = {
            "A0_nm": dm.A0_nm,
            "L_um": dm.L_um,
            "gamma_per_um": dm.gamma_per_um,
            "decay_length_um": 1.0 / dm.gamma_per_um,
            "phi": dm.phi,
            "root_abs": abs(dm.root),
            "root_arg": float(np.angle(dm.root)),
            "amplitude_note": "A0 = dominant envelope extrapolated to s=0; not u_0 and not peak-to-peak",
        }
        # Tail measured on the direct solution: at the far end of a fast-decaying tail the
        # signal approaches the P-iteration tolerance. P vs direct is checked separately.
        win = mt.dominant_window(dm)
        try:
            ft = mt.fit_tail(u_star, x, win)
            summary["tail_fit"] = {
                "window_um": list(win),
                "A0_nm": ft.A0_nm,
                "L_um": ft.L_um,
                "gamma_per_um": ft.gamma_per_um,
                "n_extrema": ft.n_extrema,
                "rel_rms": ft.rel_rms,
                "rel_err_L": ft.L_um / dm.L_um - 1,
                "rel_err_gamma": ft.gamma_per_um / dm.gamma_per_um - 1,
                "rel_err_A0": ft.A0_nm / dm.A0_nm - 1,
            }
        except ValueError as exc:
            summary["tail_fit"] = {"window_um": list(win), "error": str(exc)}
    return arrays, summary


def _apply(model, u):
    from .model import apply

    return apply(model, u)
