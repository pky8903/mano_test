"""S1 — establish the measured quantity (final state of the `main` simulation)."""

from manim import DOWN, LEFT, RIGHT, UP, Create, DashedVMobject, FadeIn, LaggedStart, Rectangle, VGroup

from common import (BODY, ERR, INK, LABEL, MASK, MUTED, NOMINAL, SMALL, Base, Panel, T, group, load, residual_bound, series,
                    visible)

NOMINAL_NM = 40.0  # illustrative only, not an experimental value
EXAGGERATION = 50  # drawn width change = EXAGGERATION x true change (labelled on screen)
WINDOW = (0.8, 8.0)


class S1Measured(Base):
    def construct(self):
        arr, meta = load("main")
        x, u, e = arr["x_um"], arr["u_final_nm"], arr["e_final_nm"]
        n_final = meta["final_iter"]

        title = self.title("무엇이 진동하는가?")
        self.play(FadeIn(title), FadeIn(self.evidence()), run_time=0.8)

        # --- schematic: straight bars, width = nominal + u (exaggerated, labelled)
        mask_p = Panel(0.0, 1.55, (-1.0, 4.5), (0, 2, 4), "Mask correction (nm)", MASK,
                       unit_note=f"수렴 후 최종 보정 · Iteration n = {n_final}")
        err_p = Panel(-2.0, 1.05, (-0.06, 0.06), (-0.05, 0, 0.05), "Remaining error (nm)", ERR,
                      x_title="Distance from left edge (µm)")
        bars = self.bars(mask_p, x, u)
        self.play(LaggedStart(*[FadeIn(b) for b in bars], lag_ratio=0.02), run_time=2.0)
        self.say("왼쪽 블록 경계에서 멀어지며 막대 폭이 번갈아 넓어지고 좁아집니다")
        self.wait(2.5)

        # --- the two quantities, explicitly named
        s_u = series(mask_p, x, u, "mask")
        self.play(FadeIn(mask_p), Create(s_u["line"]), FadeIn(s_u["marks"]), run_time=1.6)
        self.say("위: 마스크 보정 u — 진동하는 것은 이 값입니다")
        self.wait(2.0)
        s_e = series(err_p, x, e, "error")
        self.play(FadeIn(err_p), Create(s_e["line"]), FadeIn(s_e["marks"]), run_time=1.6)
        self.say(f"아래: 남은 웨이퍼 오차 — {residual_bound(meta)}")
        self.wait(3.0)
        self.say("오차는 수렴했지만, 최종 마스크 보정은 평탄하지 않습니다")
        self.wait(3.0)
        self.say("같은 시뮬레이션을 처음부터 따라가 봅니다")
        self.wait(1.5)

    def bars(self, panel, x, u):
        y_mid, height = 2.62, 0.5
        unit_per_um = panel.w / (panel.xr[1] - panel.xr[0])
        g = VGroup()
        block = Rectangle(width=0.55 * unit_per_um, height=height, stroke_width=0, fill_color=INK, fill_opacity=0.75)
        block.move_to(panel.c2p(-0.08, 0) * [1, 0, 0] + [0, y_mid, 0], aligned_edge=RIGHT)
        g.add(block, T("블록", SMALL, MUTED).next_to(block, LEFT, buff=0.1))
        idx = range(int(visible(x, panel.xr).sum()))
        for j in idx:
            cx = panel.c2p(x[j], 0)[0]
            nominal = Rectangle(width=NOMINAL_NM / 1000 * unit_per_um, height=height, stroke_color=NOMINAL,
                                stroke_width=1.2).move_to([cx, y_mid, 0])
            if x[j] < WINDOW[0] - 1e-9:
                g.add(DashedVMobject(nominal, num_dashes=8))
                continue
            w_nm = NOMINAL_NM + EXAGGERATION * u[j]
            g.add(Rectangle(width=w_nm / 1000 * unit_per_um, height=height, stroke_width=0, fill_color=MASK,
                            fill_opacity=0.85).move_to([cx, y_mid, 0]))
        note = T(f"OPC 후 마스크 막대 · 폭 = nominal(예시 {NOMINAL_NM:.0f} nm) + {EXAGGERATION}·u  (보정량 u만 ×{EXAGGERATION}) · "
                 f"점선 = nominal 윤곽(0–{WINDOW[0]:g} µm, 보정 폭 생략)", SMALL, MUTED)
        note.next_to(panel.c2p(0, 0) * [1, 0, 0] + [0, y_mid + height / 2, 0], UP, buff=0.1, aligned_edge=LEFT)
        g.add(note)
        return g
