"""Scenario presets (PRD v0.2 section 7) and reproducibility hash.

These are dimensionless-response toy examples, not fitted production parameters.
d = 80 nm is a toy control-spacing assumption.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field

import numpy as np

from .model import Model

# Iterations retained for the movie: every early step through 10, then selected later states.
MOVIE_KEEP = list(range(11)) + [15, 20, 30, 50, 75, 100, 150, 200, 300, 400, 500, 600, 700, 800]


@dataclass(frozen=True)
class Scenario:
    id: str
    purpose: str
    a: float
    b: float
    M: int
    E0_nm: float  # edge deviation at control 0
    E_bulk_nm: float = 0.0  # uniform background error on every control
    d_um: float = 0.08
    n_controls: int = 4096
    tol_nm: float = 1e-12
    keep: tuple[int, ...] = ()
    iterate: bool = True  # run the P update (False: direct solve only, e.g. near-threshold notes)
    store_controls: int = 256  # history arrays are stored on the first controls only (20.48 um)
    window_um: tuple[float, float] = (0.8, 8.0)
    notes_only: bool = False
    held_fixed: tuple[str, ...] = field(default=())
    changed: tuple[str, ...] = field(default=())

    @property
    def model(self) -> Model:
        return Model(self.a, self.b, self.M, self.d_um)

    @property
    def eta(self) -> float:
        return self.model.default_eta()

    def forcing(self, n: int | None = None) -> np.ndarray:
        """E = E_bulk * 1 + E0 * delta_0. Zero outside the block (implicit)."""
        n = self.n_controls if n is None else n
        E = np.full(n, self.E_bulk_nm, dtype=np.float64)
        E[0] += self.E0_nm
        return E

    def config(self) -> dict:
        d = asdict(self)
        d["eta"] = self.eta
        d["forcing"] = "E_j = E_bulk + E0 * delta_{j0}; u_j = 0 outside [0, n_controls)"
        d["boundary"] = "zero outside block, no kernel renormalization, no periodic wrap"
        d["sign"] = "e = E - A u; u_next = u + eta e"
        return d

    def config_hash(self) -> str:
        blob = json.dumps(self.config(), sort_keys=True, default=list).encode()
        return hashlib.sha256(blob).hexdigest()[:16]


def _s(**kw) -> Scenario:
    kw["keep"] = tuple(kw.get("keep", ()))
    return Scenario(**kw)


BASE = dict(a=0.25, b=1.0, M=9, E0_nm=1.0)

PRESETS: dict[str, Scenario] = {
    s.id: s
    for s in [
        _s(id="main", purpose="S1-S4 causal example", keep=MOVIE_KEEP, **BASE),
        # S5: same edge shape, magnitude only
        _s(id="scale_050", purpose="S5 amplitude scaling", **{**BASE, "E0_nm": 0.5},
           changed=("E0",), held_fixed=("a", "b", "M", "d", "shape")),
        _s(id="scale_200", purpose="S5 amplitude scaling", **{**BASE, "E0_nm": 2.0},
           changed=("E0",), held_fixed=("a", "b", "M", "d", "shape")),
        _s(id="scale_neg", purpose="S5 optional sign reversal", **{**BASE, "E0_nm": -1.0},
           changed=("sign of E0",), held_fixed=("a", "b", "M", "d", "|E0|")),
        # S5 extension: background plus edge deviation, and its separately solved reference
        _s(id="bg_total", purpose="S5 background + edge", **{**BASE, "E_bulk_nm": 0.5}),
        _s(id="bg_ref", purpose="S5 uniform background reference", **{**BASE, "E0_nm": 0.0, "E_bulk_nm": 0.5}),
        # S6 range comparison: fixed total nonlocal strength b, per-neighbor weight b/(2M+1)
        *[
            _s(id=f"range_{M}", purpose="S6 range comparison", **{**BASE, "M": M},
               changed=("M",), held_fixed=("a", "b", "d", "forcing"))
            for M in (13, 18, 24)
        ],
        # S6 damping comparison at fixed b, M, d, forcing
        *[
            _s(id=f"damp_{int(round(a * 100)):03d}", purpose="S6 damping comparison", **{**BASE, "a": a},
               changed=("a",), held_fixed=("b", "M", "d", "forcing"))
            for a in (0.25, 0.30, 0.40)
        ],
        # Presenter-notes Appendix A: near-threshold finite-stencil counterexample (not in the film)
        *[
            _s(id=f"counter_{M}", purpose="Notes: near-threshold nonmonotonic decay", **{**BASE, "a": 0.22, "M": M},
               iterate=False, notes_only=True)
            for M in (9, 12)
        ],
    ]
}
