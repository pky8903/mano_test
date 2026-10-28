# Completion report — OPC mask CD oscillation film

Date: 2026-10-28 · Basis: PRD v0.2, theory note (2026-09-23), [plan.md](plan.md)

## Deliverables

| Item | Location | State |
|---|---|---|
| Main film (1920×1080, 30 fps, H.264, 265.0 s, 7950 frames, 19.4 MB) | `out/opc_mask_cd_oscillation.mp4` | Rendered; not in git (`out/` ignored) — rebuild with `scripts/render_all.sh` |
| Per-scene clips | `out/media/videos/<scene>/1080p30/*.mp4` | Rendered |
| Keyframes (1080p, 16 frames incl. every S3 detailed phase sample) | `out/keyframes_1080/` | Extracted from the final film |
| Scenario configuration + arrays + metrics | `data/<id>.json`, `data/<id>.npz` | Committed; digest-verified on every load |
| Validation report | [validation_report.md](validation_report.md) | 99/99 gates pass |
| Storyboard (as implemented) | [storyboard.md](storyboard.md) | — |
| Presenter notes (Korean, incl. Appendix A counterexample) | [presenter_notes_ko.md](presenter_notes_ko.md) | — |

Scene start times in the film: S1 0:00 · S2 0:21 · S3 0:50 · S4 2:04 · S5 2:32 · S6 3:03 · S7 3:43 · S8 4:06.

## Verification

| Level | What ran | Result |
|---|---|---|
| Unit | `pytest` — operator vs element-wise definition, boundaries (no renormalization/wrap), invalid parameters, sign of first updates, local-only case, iteration identity, PRD counts 631/806, CG, scaling laws, right-boundary insensitivity, roots/reciprocity, theory-note baseline (8 digits), near-threshold crossing, mode sum vs direct solve, tail fit on an independent synthetic oracle | 40 pass |
| Flow | config → arrays → store → load (digest) → scene-input consistency; scene modules import and do not bypass the store | pass (incl. 2 scene checks) |
| Numerical gates | `scripts/validate.py` | 99/99 pass |
| Job | `pytest -m slow`: real `manim render` of S2 and S8 + ffprobe; full `scripts/render_all.sh` at 1080p30 + concat + full decode (`ffmpeg -f null`, no errors) | pass |
| Visual | Keyframes of every scene at 480p during development, 16 frames from the final 1080p film, three densest frames re-checked at 1280×720 | Reviewed by the implementer only (see open items) |

Text sizes: captions font_size 24 ≈ 40 px glyph height at 1080p (≥ 34 px), smallest labels 16 ≈ 27 px (≥ 26 px); titles/captions inside the 5 % safe area; principal results held ≥ 3 s; final frame 10.5 s.

## Design decisions and deviations from the PRD

1. **S3 zoom (approved):** fixed axes u ±0.6 nm, e ±0.06 nm with ▲ + signed true values instead of an inset; S4 states the scale change to the full range.
2. **S1 (approved):** no correction width drawn for 0–0.8 µm (dashed = nominal outline); ×50 exaggeration on u only.
3. **Final wording (approved):** `max|e| < 10⁻¹² nm`; asserted against the stored residual (9.96×10⁻¹³ nm) at render time.
4. **S4 spatial damping** is shown by measured peak values (+0.50, +0.24, +0.12, +0.05, +0.03 nm) instead of an envelope: on the full-range axis the dominant-mode envelope (valid only from 1.8 µm) is too small to read. Envelopes appear in S6, drawn only from the distance where the dominant pair matches the solved profile within 5 %.
5. **S6** uses 0–12 µm (both mini-sequences) so that the M = 24 case shows several periods; S1–S5 use 0–8 µm. Period brackets carry no number because sampled peak positions are quantized by d; the exact root-predicted period is in the tag.
6. **S5:** the optional sign-reversal example was not animated (scenario `scale_neg` is solved and gated).
7. **S7:** reported numbers (< 0.5 nm, ≈ 2 nm) are not shown — amplitude convention and window not yet confirmed equivalent (PRD default).
8. **Tail metrics** are measured on the banded direct solution; the P-iteration result is checked against it separately (max difference 3.1×10⁻¹¹ nm). At the far end of fast-decaying tails the signal approaches the iteration tolerance.
9. **Duration** 265 s vs 270 s planned. No audio (PRD §15 default).

## Environment

conda env `mano` (conda-forge): Python 3.12.16, manim 0.19.1, numpy 2.5.4, scipy 1.18.1, pycairo 1.29.2, manimpango 0.7.1, PyAV 13.1.0, ffmpeg 7.1.1, cairo 1.18.6, pango 1.58.2; full lock in `environment.lock.yml`. Font Noto Sans CJK KR (system). No TeX. Encoder: Manim/PyAV H.264, concat by ffmpeg stream copy.

## Open items

- **Viewer acceptance (PRD §12.3)** not run: needs a technically informed reviewer who did not author the film; target ≥ 4/5 with item 1 correct.
- **User visual review** of the final film and keyframes is pending (decisions 1–3 were approved from description only).
- Reported production amplitudes: add only after the measurement definition and window are confirmed.
- Theory-note figure `validation_portrait.png` was not supplied (not needed for the film).
