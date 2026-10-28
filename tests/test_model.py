import numpy as np
import pytest

from opc_osc.model import Model, apply, operator, p_iterate, solve_cg, solve_direct


def dense_reference(a, b, M, n):
    """Oracle: A built element by element from the definition, zero outside the block."""
    N = 2 * M + 1
    A = np.zeros((n, n))
    for j in range(n):
        A[j, j] += a
        for l in range(-M, M + 1):
            if 0 <= j + l < n:
                A[j, j + l] += b / N
    return A


def edge(n, E0=1.0):
    E = np.zeros(n)
    E[0] = E0
    return E


@pytest.mark.parametrize("a,b,M,n", [(0.25, 1.0, 9, 60), (0.4, 2.0, 3, 17), (1.0, 0.0, 4, 12), (0.3, 1.0, 0, 5)])
def test_operator_and_apply_match_definition(a, b, M, n):
    m = Model(a, b, M)
    ref = dense_reference(a, b, M, n)
    np.testing.assert_allclose(operator(m, n).toarray(), ref, rtol=0, atol=1e-15)
    u = np.random.default_rng(0).normal(size=n)
    np.testing.assert_allclose(apply(m, u), ref @ u, rtol=0, atol=1e-13)


def test_boundary_rows_not_renormalized_or_wrapped():
    m, n = Model(0.25, 1.0, 9), 100
    A = operator(m, n).toarray()
    N = 19
    assert A[0].sum() == pytest.approx(0.25 + 10 / N)  # only M+1 kernel taps remain at j = 0
    assert A[50].sum() == pytest.approx(0.25 + 1.0)
    assert A[0, -1] == 0.0 and A[-1, 0] == 0.0
    assert A[0, 0] == pytest.approx(m.diagonal) == pytest.approx(0.25 + 1 / N)


@pytest.mark.parametrize("kw", [dict(a=0, b=1, M=9), dict(a=-1, b=1, M=9), dict(a=1, b=-1, M=9),
                                dict(a=1, b=1, M=-1), dict(a=1, b=1, M=2.5), dict(a=1, b=1, M=3, d_um=0),
                                dict(a=np.nan, b=1, M=3)])
def test_invalid_parameters(kw):
    with pytest.raises(ValueError):
        Model(**kw)


def test_too_few_controls():
    with pytest.raises(ValueError):
        solve_direct(Model(0.25, 1, 9), np.zeros(10))


def test_local_only_case_is_flat_and_local():
    m = Model(0.5, 0.0, 9)
    E = edge(200, 2.0)
    u = solve_direct(m, E)
    np.testing.assert_allclose(u, E / 0.5, atol=1e-15)
    it = p_iterate(m, E)
    assert it.final_iter <= 1 and np.all(it.u[-1][1:] == 0)


def test_direct_solution_matches_dense_solve():
    m, n = Model(0.25, 1.0, 9), 300
    E = edge(n)
    np.testing.assert_allclose(solve_direct(m, E), np.linalg.solve(dense_reference(0.25, 1, 9, n), E), atol=1e-12)


def test_sign_convention_first_update():
    """Positive edge error asks for a wider mask; that widening creates negative error at neighbors."""
    m, n = Model(0.25, 1.0, 9), 200
    it = p_iterate(m, edge(n), keep=[0, 1, 2])
    e0, e1 = it.e[0], it.e[1]
    assert it.du[0][0] > 0 and np.all(it.du[0][1:] == 0)
    assert 0 < e1[0] < e0[0]  # first control improves but is not fully corrected in one step
    assert np.all(e1[1:10] < 0)  # neighbors within M now over-predicted
    assert np.all(e1[10:] == 0)  # nothing beyond M controls after one step
    # second update: narrowing reaches up to 2M controls
    assert np.all(it.e[2][2 * 9 + 1:] == 0) and np.any(it.e[2][10:19] != 0)


def test_error_update_identity_and_convergence():
    m, n = Model(0.25, 1.0, 9), 4096
    E = edge(n)
    keep = list(range(11)) + [50, 200]
    it = p_iterate(m, E, tol_nm=1e-12, keep=keep)
    assert it.converged and it.final_residual_nm <= 1e-12
    assert it.residual_history[-2] > 1e-12  # final index is the first one meeting tolerance
    for k in range(len(it.kept) - 1):
        if it.kept[k + 1] == it.kept[k] + 1:
            np.testing.assert_allclose(it.e[k + 1], it.e[k] - apply(m, it.du[k]), atol=1e-14)
            np.testing.assert_allclose(it.u[k + 1], it.u[k] + it.du[k], atol=0)
    np.testing.assert_allclose(it.u[-1], solve_direct(m, E), atol=1e-10)


def test_iteration_counts_reported_in_prd():
    m, E = Model(0.25, 1.0, 9), edge(4096)
    assert p_iterate(m, E, tol_nm=1e-10).final_iter == 631
    assert p_iterate(m, E, tol_nm=1e-12).final_iter == 806


def test_cg_secondary_check():
    m, E = Model(0.25, 1.0, 9), edge(4096)
    u_cg, _ = solve_cg(m, E)
    assert np.max(np.abs(u_cg - solve_direct(m, E))) <= 1e-8


def test_scaling_laws():
    m, E = Model(0.25, 1.0, 9), edge(2048)
    u = solve_direct(m, E)
    for k in (0.5, 2.0, -1.0):
        np.testing.assert_allclose(solve_direct(m, k * E), k * u, rtol=1e-12, atol=1e-15)
    u_k = solve_direct(Model(0.25 * 3, 1.0 * 3, 9), E)
    np.testing.assert_allclose(u_k, u / 3, rtol=1e-12, atol=1e-15)


def test_right_boundary_negligible_in_displayed_region():
    m = Model(0.25, 1.0, 24)
    u1 = solve_direct(m, edge(4096))
    u2 = solve_direct(m, edge(8192))
    assert np.max(np.abs(u1[:256] - u2[:256])) <= 1e-12


def test_unstable_eta_diverges_not_silently_converges():
    m = Model(0.25, 1.0, 9)
    it = p_iterate(m, edge(200), eta=2.5 / 1.25, max_iter=300)
    assert not it.converged
