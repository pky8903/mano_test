"""Discrete finite-range OPC toy model and P-type correction.

Sign convention (PRD v0.2, target minus model):

    e = E - A u,    u_next = u + eta * e,    A = a I + b W_M

The theory note uses e_old = E_old * delta + A u and u_next = u - eta * e_old.
Both describe the same physical correction u when e_old = -e and E_old = -E.
Characteristic roots, period and damping are identical in both conventions.

W_M is the centered (2M+1)-point average including the center. Controls outside
the simulated block are zero; the shortened stencil at either end is NOT
renormalized and the kernel is NOT wrapped periodically.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import scipy.linalg as sla
import scipy.sparse as sp
import scipy.sparse.linalg as spla


@dataclass(frozen=True)
class Model:
    """Local sensitivity a, total nonlocal sensitivity b, half-range M, spacing d (um)."""

    a: float
    b: float
    M: int
    d_um: float = 0.08

    def __post_init__(self):
        if not (np.isfinite(self.a) and self.a > 0):
            raise ValueError(f"a must be positive and finite, got {self.a}")
        if not (np.isfinite(self.b) and self.b >= 0):
            raise ValueError(f"b must be non-negative and finite, got {self.b}")
        if int(self.M) != self.M or self.M < 0:
            raise ValueError(f"M must be a non-negative integer, got {self.M}")
        if not (np.isfinite(self.d_um) and self.d_um > 0):
            raise ValueError(f"d_um must be positive, got {self.d_um}")

    @property
    def N(self) -> int:
        return 2 * int(self.M) + 1

    @property
    def c(self) -> float:
        return self.a / self.b if self.b > 0 else np.inf

    @property
    def Rc_um(self) -> float:
        return self.N * self.d_um / 2

    @property
    def diagonal(self) -> float:
        """Actual self-sensitivity: a + b/N (the center is part of the average)."""
        return self.a + self.b / self.N

    def default_eta(self) -> float:
        return 1.0 / (self.a + self.b)


def apply(model: Model, u: np.ndarray) -> np.ndarray:
    """A u, via zero-padded convolution (no renormalization, no wrap)."""
    u = np.asarray(u, dtype=np.float64)
    if model.b == 0:
        return model.a * u
    box = np.convolve(u, np.ones(model.N), mode="same")
    return model.a * u + (model.b / model.N) * box


def operator(model: Model, n: int) -> sp.csr_matrix:
    """Sparse banded A on n controls."""
    _check_n(model, n)
    M, N = int(model.M), model.N
    offsets = list(range(-M, M + 1))
    diags = [np.full(n - abs(k), model.b / N) for k in offsets]
    A = sp.diags(diags, offsets, shape=(n, n), format="csr")
    return (A + model.a * sp.eye(n, format="csr")).tocsr()


def solve_direct(model: Model, E: np.ndarray) -> np.ndarray:
    """Equilibrium A u* = E by a banded LU solve (independent of the iteration)."""
    E = np.asarray(E, dtype=np.float64)
    n = E.size
    _check_n(model, n)
    M, N = int(model.M), model.N
    ab = np.full((2 * M + 1, n), model.b / N)
    ab[M, :] += model.a
    return sla.solve_banded((M, M), ab, E)


def solve_cg(model: Model, E: np.ndarray, rtol: float = 1e-14) -> tuple[np.ndarray, int]:
    """Secondary check with conjugate gradients (its own algorithm, not the movie's P update)."""
    E = np.asarray(E, dtype=np.float64)
    A = operator(model, E.size)
    count = {"n": 0}

    def cb(_):
        count["n"] += 1

    u, info = spla.cg(A, E, rtol=rtol, atol=0.0, maxiter=20 * E.size, callback=cb)
    if info != 0:
        raise RuntimeError(f"CG did not converge (info={info})")
    return u, count["n"]


@dataclass
class IterationResult:
    """Retained P-iteration states. states[k] holds u(n), e(n), du(n) for n = kept[k]."""

    eta: float
    tol_nm: float
    converged: bool
    final_iter: int
    final_residual_nm: float
    kept: list[int]
    u: list[np.ndarray] = field(repr=False)
    e: list[np.ndarray] = field(repr=False)
    du: list[np.ndarray] = field(repr=False)
    residual_history: np.ndarray = field(repr=False)  # max|e(n)| for n = 0..final_iter


def p_iterate(
    model: Model,
    E: np.ndarray,
    eta: float | None = None,
    tol_nm: float = 1e-12,
    max_iter: int = 200_000,
    keep: list[int] | None = None,
) -> IterationResult:
    """P-type correction from u(0) = 0 until max|e(n)| <= tol_nm.

    final_iter is the first n whose error satisfies the tolerance. Every state
    listed in `keep` (up to final_iter) and the final state are retained.
    Error is recomputed from the mask each step (e = E - A u), not propagated.
    """
    E = np.asarray(E, dtype=np.float64)
    eta = model.default_eta() if eta is None else float(eta)
    if not (eta > 0):
        raise ValueError("eta must be positive")
    keep_set = set(keep or [])
    u = np.zeros_like(E)
    kept, us, es, dus, res = [], [], [], [], []
    n = 0
    while True:
        e = E - apply(model, u)
        r = float(np.max(np.abs(e)))
        res.append(r)
        done = r <= tol_nm
        du = eta * e
        if n in keep_set or done or n == max_iter:
            kept.append(n)
            us.append(u.copy())
            es.append(e.copy())
            dus.append(du.copy())
        if done or n == max_iter or not np.isfinite(r):
            break
        u = u + du
        n += 1
    return IterationResult(
        eta=eta,
        tol_nm=tol_nm,
        converged=bool(done),
        final_iter=n,
        final_residual_nm=res[-1],
        kept=kept,
        u=us,
        e=es,
        du=dus,
        residual_history=np.asarray(res),
    )


def _check_n(model: Model, n: int):
    if n < model.N:
        raise ValueError(f"need at least N={model.N} controls, got {n}")
