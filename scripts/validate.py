"""Numerical acceptance gates on the stored data -> docs/validation_report.md.

Reads data/*.npz written by generate_data.py and checks it against independent
oracles (banded direct solve, CG, boundary-matrix mode sum, doubled domain).
Exit code 1 if any gate fails. Gates are never loosened to force a pass.
"""

import sys
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from opc_osc import metrics as mt  # noqa: E402
from opc_osc import store  # noqa: E402
from opc_osc.model import Model, apply, p_iterate, solve_cg, solve_direct  # noqa: E402
from opc_osc.scenarios import PRESETS  # noqa: E402

rows: list[tuple[str, str, str, bool]] = []


def gate(name, value, limit, ok=None, fmt="{:.2e}"):
    ok = (value <= limit) if ok is None else ok
    rows.append((name, fmt.format(value) if isinstance(value, float) else str(value), str(limit), bool(ok)))


def main():
    data = {sid: store.load(sid) for sid in PRESETS}  # digest-verified

    for sid, (arr, meta) in data.items():
        s = PRESETS[sid]
        gate(f"{sid}: direct residual max|E-Au*| (nm)", meta["direct_residual_nm"], 1e-12)
        if meta["config_hash"] != s.config_hash():
            gate(f"{sid}: config hash matches preset", "mismatch", "match", ok=False)
        if s.iterate:
            gate(f"{sid}: P final residual (nm) [iter {meta['final_iter']}]", meta["final_residual_nm"], s.tol_nm)
            gate(f"{sid}: max|u_P - u*| (nm)", meta["max_abs_u_final_minus_direct_nm"], 1e-8)
        # right boundary: same scenario on a doubled domain
        u2 = solve_direct(s.model, s.forcing(2 * s.n_controls))
        gate(f"{sid}: right-boundary influence, 0-20.48 um (nm)",
             float(np.max(np.abs(arr["u_star_nm"][:256] - u2[:256]))), 1e-12)
        tf = meta.get("tail_fit")
        if tf and "error" not in tf:
            gate(f"{sid}: tail-fit |L/L_root-1| [{tf['window_um'][0]:.1f}-{tf['window_um'][1]:.1f} um]",
                 abs(tf["rel_err_L"]), 0.02)
            gate(f"{sid}: tail-fit |gamma/gamma_root-1|", abs(tf["rel_err_gamma"]), 0.05)
        elif tf:
            gate(f"{sid}: tail fit", tf["error"], "fit possible", ok=False)

    # mode sum (boundary-matrix oracle) vs direct solve
    for sid in ("main", "range_24", "damp_040", "counter_9"):
        s = PRESETS[sid]
        dm = mt.boundary_solution(s.model, s.E0_nm)
        gate(f"{sid}: max|mode sum - u*|, j<300 (nm)",
             float(np.max(np.abs(mt.mode_sum(dm, 300) - data[sid][0]["u_star_nm"][:300]))), 1e-10)

    # CG secondary check
    s = PRESETS["main"]
    u_cg, n_cg = solve_cg(s.model, s.forcing())
    gate(f"main: max|u_CG - u*| (nm) [{n_cg} CG steps]", float(np.max(np.abs(u_cg - data["main"][0]["u_star_nm"]))), 1e-8)

    # error-update identity on stored consecutive states (interior of the stored crop)
    arr = data["main"][0]
    it, k, worst = list(arr["iters"]), s.store_controls, 0.0
    for i in range(len(it) - 1):
        if it[i + 1] == it[i] + 1:
            du = np.zeros(s.n_controls)
            du[:k] = arr["du_hist_nm"][i]
            pred = arr["e_hist_nm"][i] - apply(s.model, du)[:k]
            worst = max(worst, float(np.max(np.abs(pred[: k - s.M] - arr["e_hist_nm"][i + 1][: k - s.M]))))
    gate("main: e(n+1) = e(n) - A du(n) on stored steps (nm)", worst, 1e-13)
    gate("main: retained iterations include 6, 7, 8, 9", str(sorted({6, 7, 8, 9} & set(it))), "[6, 7, 8, 9]",
         ok={6, 7, 8, 9} <= set(it))
    gate("main: displayed final index = convergence-test index", f"{it[-1]} / {data['main'][1]['final_iter']}", "equal",
         ok=it[-1] == data["main"][1]["final_iter"])

    # P update counts at both tolerances (PRD v0.2 record)
    n10 = p_iterate(s.model, s.forcing(), tol_nm=1e-10).final_iter
    gate("main: P updates to 1e-10 nm (PRD: 631)", n10, 631, ok=n10 == 631, fmt="{}")
    gate("main: P updates to 1e-12 nm (PRD: 806)", data["main"][1]["final_iter"], 806,
         ok=data["main"][1]["final_iter"] == 806, fmt="{}")

    # scaling and sign reversal (exact for the additional response)
    u1 = data["main"][0]["u_star_nm"]
    for sid, kf in (("scale_050", 0.5), ("scale_200", 2.0), ("scale_neg", -1.0)):
        rel = float(np.max(np.abs(data[sid][0]["u_star_nm"] - kf * u1)) / np.max(np.abs(kf * u1)))
        gate(f"{sid}: max|u(kE) - k u(E)| / max|k u|", rel, 1e-12)
    extra = data["bg_total"][0]["u_star_nm"] - data["bg_ref"][0]["u_star_nm"]
    gate("bg: max|(u_total - u_bg) - u_main| (nm)", float(np.max(np.abs(extra - u1))), 1e-13)
    ub = data["bg_ref"][0]["u_star_nm"]
    gate("bg_ref: uniform error gives non-flat correction near edge (u0 - u_bulk, nm)",
         float(abs(ub[0] - ub[2000])), "> 1e-3", ok=abs(ub[0] - ub[2000]) > 1e-3, fmt="{:.4f}")

    # local-only case
    ul = solve_direct(Model(0.25, 0.0, 9), s.forcing())
    gate("local-only (b=0): max|u - E/a| (nm)", float(np.max(np.abs(ul - s.forcing() / 0.25))), 1e-15)

    # S6 trends required in the exact discrete calculation
    pr = lambda sid: data[sid][1]["prediction"]
    Ls = [pr(f"range_{M}")["L_um"] for M in (13, 18, 24)]
    gs = [pr(f"range_{M}")["gamma_per_um"] for M in (13, 18, 24)]
    gate("range M=13->18->24: period increases", " -> ".join(f"{v:.3f}" for v in Ls), "increasing",
         ok=Ls[0] < Ls[1] < Ls[2])
    gate("range M=13->18->24: gamma decreases (1/um)", " -> ".join(f"{v:.3f}" for v in gs), "decreasing",
         ok=gs[0] > gs[1] > gs[2])
    gd = [pr(f"damp_{k}")["gamma_per_um"] for k in ("025", "030", "040")]
    gate("damp a=0.25->0.30->0.40: gamma increases (1/um)", " -> ".join(f"{v:.3f}" for v in gd), "increasing",
         ok=gd[0] < gd[1] < gd[2])
    g9, g12 = pr("counter_9")["gamma_per_um"], pr("counter_12")["gamma_per_um"]
    gate("notes c=0.22: gamma(M=12) > gamma(M=9) (counterexample)", f"{g9:.4f} -> {g12:.4f}", "increase", ok=g12 > g9)

    write_report(data)
    failed = [r for r in rows if not r[3]]
    print(f"{len(rows) - len(failed)}/{len(rows)} gates passed")
    for r in failed:
        print("FAIL:", r)
    return 1 if failed else 0


def write_report(data):
    L = [f"# Validation report\n",
         f"Generated by `scripts/validate.py` on {date.today().isoformat()} from `data/*.npz` (digest-verified).",
         f"Versions: {data['main'][1]['versions']}\n",
         "Toy-model simulation only. No production model, calibration or OPC job is validated here.\n",
         "## Gates\n", "| Gate | Value | Limit | Result |", "|---|---|---|---|"]
    esc = lambda t: str(t).replace("|", "\\|")
    L += [f"| {esc(n)} | {esc(v)} | {lim} | {'PASS' if ok else '**FAIL**'} |" for n, v, lim, ok in rows]
    L += ["\n## Scenario metrics\n",
          "Mask variation = max(u) - min(u) over 0.8-8.0 um. A0 = dominant envelope extrapolated to s=0 "
          "(not u0, not peak-to-peak). Tail values are measured on the direct solution in the stated window, "
          "initialized from measured extrema only.\n",
          "| ID | a | b | M | E0 | E_bulk | final iter | u0 (nm) | variation (nm) | L root (um) | L tail | "
          "gamma root (1/um) | gamma tail | A0 root (nm) | A0 tail | hash |",
          "|" + "---|" * 16]
    for sid, (arr, m) in data.items():
        c = m["config"]
        p, t = m.get("prediction", {}), m.get("tail_fit", {})
        f = lambda d, k, spec=".5f": format(d[k], spec) if k in d else "-"
        L.append(f"| {sid} | {c['a']} | {c['b']} | {c['M']} | {c['E0_nm']} | {c['E_bulk_nm']} | "
                 f"{m.get('final_iter', 'direct only')} | {m['u0_nm']:.4f} | {m['mask_variation_nm']:.4f} | "
                 f"{f(p, 'L_um')} | {f(t, 'L_um')} | {f(p, 'gamma_per_um')} | {f(t, 'gamma_per_um')} | "
                 f"{f(p, 'A0_nm')} | {f(t, 'A0_nm')} | `{m['config_hash']}` |")
    L += ["\n## Notes\n",
          "- Sign convention: e = E - A u, u <- u + eta e (PRD). Theory note: e_old = -e, E_old = -E; same u.",
          "- Boundary: zero outside the block, no renormalization, no periodic wrap. Domain 4096 controls, d = 80 nm (toy).",
          "- counter_9 / counter_12 (c = 0.22) are presenter-notes only; their P iteration converges slowly "
          "near the bulk stability threshold and is not run here.",
          "- bg_total / bg_ref: the edge response is compared as u_total - u_bg with the background solved separately."]
    (ROOT / "docs" / "validation_report.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main())
