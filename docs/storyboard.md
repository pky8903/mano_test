# Storyboard (as implemented)

1920×1080, 30 fps. Light background; mask correction = blue, solid line, round markers; remaining error = orange, dashed line, square markers. All profiles come from `data/*.npz` (digest-verified on load). Durations are measured from the rendered clips.

| Scene | File | Duration | Data | Principal result (held ≥ 3 s) |
|---|---|---|---|---|
| S1 What oscillates | `scenes/s1_measured.py` | 20.9 s | `main` final (n = 806) | Error converged (max\|e\| < 10⁻¹² nm), final mask correction not flat |
| S2 Coupling | `scenes/s2_coupling.py` | 28.5 s | `main` columns of A (control 40, control 0) | One +1 nm change: self +0.30, each neighbor +0.053; edge window truncated |
| S3 Causal iterations | `scenes/s3_iterations.py` | 75.1 s | `main` retained states 0–10, 15…400, 806 | Read → preview Δu → apply → recompute → label; converged error, oscillating correction |
| S4 Two decays | `scenes/s4_two_decays.py` | 27.5 s | `main` residual history, final u | Iteration-n convergence vs distance damping (peaks +0.50, +0.24, +0.12, …) |
| S5 Contrast | `scenes/s5_contrast.py` | 30.5 s | `scale_050`, `main`, `scale_200`, `bg_ref`, `bg_total` | Exact scaling with edge deviation; background compared as u_total − u_bg |
| S6 Held fixed | `scenes/s6_held_fixed.py` | 41.2 s | `range_13/18/24`, `damp_025/030/040` | In this example: wider range → longer period, slower decay; larger a → stronger decay and smaller amplitude |
| S7 Observations | `scenes/s7_observations.py` | 22.2 s | none (reported, qualitative) | Reduced / returned cards; calibration ≠ target layout; hypothesis card |
| S8 Action | `scenes/s8_action.py` | 19.3 s | none | Three next steps (final hold 10.5 s) |
| **Total** | | **≈265 s** | | |

## Fixed scales

| Where | Quantity | Range | Off-scale handling |
|---|---|---|---|
| S1 | u | −1 … 4.5 nm (full) | none needed |
| S1, S3 | e | ±0.06 nm | ▲ + signed true value |
| S3 | u | ±0.6 nm | ▲ + signed true value (any control) |
| S4 | max\|e\| | 10⁻¹³ … 10^0.5 nm (log) | — |
| S4 | u | −1 … 4.5 nm (full, "배율 변경" note) | — |
| S5 | u | ±1.2 nm (all magnitudes) | ▲ marker; first-control values in labels |
| S6 | u | ±0.6 nm, unnormalized (both sweeps) | ▲ marker |

Horizontal axis: Distance from left edge (µm), 0–8 µm (S1–S5), 0–12 µm (S6, both sweeps); Iteration n in S4 left.

## S3 iteration timeline

0→1, 1→2, 2→3 detailed (five phases each); 3→10 fast (u then e, then label); "Intermediate iterations skipped" then 15, 20, 30, 50, 100, 200, 400, 806 (= convergence-test index).

## Approved design decisions (2026-10-28)

- S3 fixed zoom axes (u ±0.6 nm, e ±0.06 nm) with signed off-scale values instead of an inset; S4 states the scale change.
- S1 omits correction width for 0–0.8 µm; dashed = nominal outline; ×50 applies to u only.
- Final screens state `max|e| < 10⁻¹² nm`, not "exactly 0".
