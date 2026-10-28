"""Metrics, characteristic-root predictions and numerical-tail measurement.

Root and boundary-matrix formulas follow the theory note (sections 2-4), written
in the PRD sign convention: equilibrium A u = E e0, hence B C = +E e0.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares

from .model import Model


def positions_um(n: int, d_um: float) -> np.ndarray:
    """Control centers; control 0 sits at the left block edge (s = 0)."""
    return np.arange(n) * d_um


def max_abs_error(e: np.ndarray) -> float:
    return float(np.max(np.abs(e)))


def window_mask(x_um: np.ndarray, window_um: tuple[float, float]) -> np.ndarray:
    lo, hi = window_um
    if not lo < hi:
        raise ValueError("window must satisfy lo < hi")
    m = (x_um >= lo - 1e-12) & (x_um <= hi + 1e-12)
    if not m.any():
        raise ValueError("window contains no controls")
    return m


def mask_variation(u: np.ndarray, x_um: np.ndarray, window_um=(0.8, 8.0)) -> float:
    """max(u) - min(u) over a stored spatial window (nm)."""
    w = window_mask(x_um, window_um)
    return float(u[w].max() - u[w].min())


# --------------------------------------------------------------------------- roots

def characteristic_roots(model: Model) -> np.ndarray:
    """All 2M roots of P_M(r) = a r^M + (b/N) sum_{h=0}^{2M} r^h."""
    if model.b == 0 or model.M == 0:
        return np.array([], dtype=complex)
    M, N = int(model.M), model.N
    coef = np.full(2 * M + 1, model.b / N)  # ascending powers
    coef[M] += model.a
    return np.roots(coef[::-1])


def bulk_threshold(M: int, samples: int = 200_001) -> float:
    """c_N = -min_theta (1/N)[1 + 2 sum cos(l theta)]: bulk stability threshold for c = a/b."""
    N = 2 * M + 1
    th = np.linspace(0, np.pi, samples)
    k = np.arange(1, M + 1)
    resp = (1 + 2 * np.cos(np.outer(th, k)).sum(axis=1)) / N
    return float(-resp.min())


@dataclass
class DominantMode:
    A0_nm: float  # dominant envelope extrapolated to s = 0 (not u_0)
    L_um: float
    gamma_per_um: float
    phi: float
    root: complex
    roots: np.ndarray  # decaying roots, |r| < 1
    C: np.ndarray  # mode coefficients (PRD sign)
    next_gamma_per_um: float  # decay of the next-slowest excited mode
    next_ratio: float  # |C_next| / |C_dom| (in envelope terms)


def boundary_solution(model: Model, E0: float) -> DominantMode:
    """Solve the M x M boundary system for an edge-delta forcing E0 at control 0."""
    r_all = characteristic_roots(model)
    r = r_all[np.abs(r_all) < 1.0]
    M, N = int(model.M), model.N
    if r.size != M:
        raise ValueError(f"expected {M} decaying roots, found {r.size} (unstable or critical c?)")
    j = np.arange(M)[:, None]
    B = model.a * r[None, :] ** j + (model.b / N) * (1 - r[None, :] ** (j + M + 1)) / (1 - r[None, :])
    rhs = np.zeros(M, dtype=complex)
    rhs[0] = E0
    C = np.linalg.solve(B, rhs)

    scale = np.abs(C).max()
    excited = np.abs(C) > 1e-12 * scale
    cplx = (np.abs(r.imag) > 1e-12) & excited
    if not cplx.any():
        raise ValueError("no excited complex root")
    idx = np.flatnonzero(cplx)
    k = idx[np.argmax(np.abs(r[idx]))]
    if r[k].imag < 0:  # choose the member with positive argument
        k = idx[np.argmin(np.abs(r[idx] - np.conj(r[k])))]
    rs = r[k]

    d = model.d_um
    gam = lambda z: -np.log(np.abs(z)) / d
    # next-slowest excited mode (excluding the conjugate partner)
    others = [i for i in np.flatnonzero(excited) if not np.isclose(np.abs(r[i]), np.abs(rs), rtol=1e-12, atol=0)]
    if others:
        i2 = max(others, key=lambda i: np.abs(r[i]))
        weight = 1.0 if abs(r[i2].imag) <= 1e-12 else 2.0
        g2, ratio = gam(r[i2]), weight * abs(C[i2]) / (2 * abs(C[k]))
    else:
        g2, ratio = np.inf, 0.0
    return DominantMode(
        A0_nm=float(2 * abs(C[k])),
        L_um=float(2 * np.pi * d / np.angle(rs)),
        gamma_per_um=float(gam(rs)),
        phi=float(np.angle(C[k])),
        root=complex(rs),
        roots=r,
        C=C,
        next_gamma_per_um=float(g2),
        next_ratio=float(ratio),
    )


def mode_sum(dm: DominantMode, n: int) -> np.ndarray:
    """u_j = sum_nu C_nu r_nu^j for j < n (real part; imaginary part cancels)."""
    j = np.arange(n)[:, None]
    return np.real((dm.C[None, :] * dm.roots[None, :] ** j).sum(axis=1))


def dominant_window(dm: DominantMode, contamination: float = 1e-4, span_decays: float = 6.0) -> tuple[float, float]:
    """Tail window where secondary modes are below `contamination` of the dominant pair."""
    dg = dm.next_gamma_per_um - dm.gamma_per_um
    start = 0.0
    if np.isfinite(dg) and dg > 0 and dm.next_ratio > 0:
        start = max(0.0, np.log(dm.next_ratio / contamination) / dg)
    return float(start), float(start + span_decays / dm.gamma_per_um)


# --------------------------------------------------------------------------- tail fit

@dataclass
class TailFit:
    A0_nm: float
    L_um: float
    gamma_per_um: float
    phi: float
    window_um: tuple[float, float]
    n_extrema: int
    rel_rms: float


def _extrema(y: np.ndarray) -> np.ndarray:
    dy = np.diff(y)
    return np.flatnonzero(np.sign(dy[:-1]) * np.sign(dy[1:]) < 0) + 1


def fit_tail(u: np.ndarray, x_um: np.ndarray, window_um: tuple[float, float]) -> TailFit:
    """Fit A e^{-g s} cos(2 pi s / L + phi) over the window.

    Initialized from measured extrema only (no theoretical roots), then refined
    by envelope-weighted least squares on the raw samples.
    """
    w = window_mask(x_um, window_um)
    xs, ys = x_um[w], u[w]
    ext = _extrema(ys)
    if ext.size < 4:
        raise ValueError(f"only {ext.size} extrema in window {window_um}; signal inadequate for a fit")
    xe, ye = xs[ext], ys[ext]
    L0 = 2 * np.median(np.diff(xe))
    g0 = -np.polyfit(xe, np.log(np.abs(ye)), 1)[0]
    A0 = np.abs(ye[0]) * np.exp(g0 * xe[0])
    phi0 = -2 * np.pi * xe[0] / L0 + (0.0 if ye[0] > 0 else np.pi)
    weight = np.exp(g0 * (xs - xs[0]))

    def resid(p):
        A, L, g, ph = p
        return (A * np.exp(-g * xs) * np.cos(2 * np.pi * xs / L + ph) - ys) * weight

    sol = least_squares(resid, [A0, L0, g0, phi0], x_scale="jac", xtol=1e-15, ftol=1e-15, gtol=1e-15)
    A, L, g, ph = sol.x
    if A < 0:
        A, ph = -A, ph + np.pi
    rel = float(np.sqrt(np.mean(sol.fun**2)) / np.sqrt(np.mean((ys * weight) ** 2)))
    return TailFit(float(A), float(L), float(g), float(np.angle(np.exp(1j * ph))), tuple(window_um), int(ext.size), rel)
