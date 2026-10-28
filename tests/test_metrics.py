import numpy as np
import pytest

from opc_osc import metrics as mt
from opc_osc.model import Model, solve_direct


def edge(n, E0=1.0):
    E = np.zeros(n)
    E[0] = E0
    return E


def test_mask_variation_window():
    x = mt.positions_um(200, 0.08)
    u = np.zeros(200)
    u[5] = 9.0  # x = 0.40 um, outside window
    u[20], u[50] = 1.5, -0.5  # x = 1.6, 4.0 um
    assert mt.mask_variation(u, x, (0.8, 8.0)) == pytest.approx(2.0)
    assert mt.window_mask(x, (0.8, 8.0)).sum() == 91  # 0.80 .. 8.00 inclusive
    with pytest.raises(ValueError):
        mt.window_mask(x, (8.0, 0.8))


@pytest.mark.parametrize("c,M", [(0.25, 9), (0.22, 12), (0.4, 13)])
def test_roots_satisfy_characteristic_equation_and_are_reciprocal(c, M):
    m = Model(c, 1.0, M)
    r = mt.characteristic_roots(m)
    assert r.size == 2 * M
    N = 2 * M + 1
    val = c + np.array([np.sum(z ** np.arange(-M, M + 1)) for z in r]) / N
    assert np.max(np.abs(val)) < 1e-10
    inside = r[np.abs(r) < 1]
    assert inside.size == M
    for z in inside:
        assert np.min(np.abs(r - 1 / z)) < 1e-8
    assert not np.any((np.abs(r.imag) < 1e-12) & (r.real > 0))  # no positive-real root


def test_theory_note_baseline_values():
    """Theory note section 7: a=0.22, b=1, d=0.08 um, M=9, E=1 nm."""
    dm = mt.boundary_solution(Model(0.22, 1.0, 9), 1.0)
    assert dm.A0_nm == pytest.approx(1.35087026, abs=5e-9)
    assert dm.gamma_per_um == pytest.approx(0.10720785, abs=5e-9)
    assert dm.L_um == pytest.approx(1.06184467, abs=5e-9)


def test_prd_v02_root_values():
    assert mt.boundary_solution(Model(0.25, 1, 9), 1).gamma_per_um == pytest.approx(0.690250, abs=5e-7)
    assert mt.boundary_solution(Model(0.25, 1, 12), 1).gamma_per_um == pytest.approx(0.532470, abs=5e-7)


def test_near_threshold_crossing():
    """Between the M=9 threshold and c ~ 0.22046339, M=12 decays faster; above it, slower."""
    g = lambda c, M: mt.boundary_solution(Model(c, 1, M), 1).gamma_per_um
    assert g(0.2204, 12) > g(0.2204, 9)
    assert g(0.2206, 12) < g(0.2206, 9)
    assert mt.bulk_threshold(9) == pytest.approx(0.2193, abs=1e-4)


def test_mode_sum_reproduces_direct_solution():
    for c, M in [(0.25, 9), (0.22, 9), (0.25, 13)]:
        m = Model(c, 1.0, M)
        dm = mt.boundary_solution(m, 1.0)
        u = solve_direct(m, edge(4096))
        np.testing.assert_allclose(mt.mode_sum(dm, 300), u[:300], atol=1e-11)


def test_A0_is_not_u0_and_scales_with_E():
    m = Model(0.25, 1.0, 9)
    d1, d2 = mt.boundary_solution(m, 1.0), mt.boundary_solution(m, -2.0)
    assert d2.A0_nm == pytest.approx(2 * d1.A0_nm)
    assert d2.L_um == pytest.approx(d1.L_um) and d2.gamma_per_um == pytest.approx(d1.gamma_per_um)
    u0 = solve_direct(m, edge(512))[0]
    assert abs(u0 - d1.A0_nm) > 1.0


def test_continuum_limit_c022():
    """Large ambit: L ~ 1.398897 R_c, gamma ~ 0.159433 / R_c (theory note section 6)."""
    m = Model(0.22, 1.0, 400)
    r = mt.characteristic_roots(m)
    inside = r[(np.abs(r) < 1) & (np.abs(r.imag) > 1e-12)]
    z = inside[np.argmax(np.abs(inside))]
    L = 2 * np.pi * m.d_um / abs(np.angle(z))
    g = -np.log(abs(z)) / m.d_um
    assert L / m.Rc_um == pytest.approx(1.398897, rel=2e-3)
    assert g * m.Rc_um == pytest.approx(0.159433, rel=2e-2)


def test_fit_tail_recovers_synthetic_damped_cosine():
    """Independent oracle: a known damped cosine, not produced by the model."""
    x = mt.positions_um(600, 0.08)
    A, L, g, ph = 0.8, 1.3, 0.35, 0.7
    u = A * np.exp(-g * x) * np.cos(2 * np.pi * x / L + ph)
    ft = mt.fit_tail(u, x, (2.0, 20.0))
    assert ft.A0_nm == pytest.approx(A, rel=1e-8)
    assert ft.L_um == pytest.approx(L, rel=1e-8)
    assert ft.gamma_per_um == pytest.approx(g, rel=1e-8)


def test_fit_tail_rejects_inadequate_signal():
    x = mt.positions_um(100, 0.08)
    with pytest.raises(ValueError):
        mt.fit_tail(np.exp(-x), x, (0.8, 4.0))


def test_measured_tail_matches_roots_within_gates():
    for c, M in [(0.25, 9), (0.25, 13), (0.25, 24), (0.40, 9)]:
        m = Model(c, 1.0, M)
        dm = mt.boundary_solution(m, 1.0)
        u = solve_direct(m, edge(4096))
        ft = mt.fit_tail(u, mt.positions_um(4096, m.d_um), mt.dominant_window(dm))
        assert abs(ft.L_um / dm.L_um - 1) <= 0.02
        assert abs(ft.gamma_per_um / dm.gamma_per_um - 1) <= 0.05
