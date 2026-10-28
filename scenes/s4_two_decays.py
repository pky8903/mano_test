"""S4 — temporal convergence (Iteration n) vs spatial damping (distance), both from `main`."""

import numpy as np
from manim import (DOWN, LEFT, RIGHT, UP, Create, DashedLine, DashedVMobject, Dot, FadeIn, Indicate, Line, VGroup,
                   VMobject)

from common import (ERR, INK, MASK, MUTED, SMALL, Base, Panel, T, load, pow10, residual_bound, sci, series)

ANNOTATE_ITERS = (10, 100)


class S4TwoDecays(Base):
    def construct(self):
        arr, meta = load("main")
        res = arr["residual_history_nm"]
        n_final = meta["final_iter"]
        assert res.size == n_final + 1
        x, u = arr["x_um"], arr["u_final_nm"]
        pred = meta["prediction"]

        self.play(FadeIn(self.title("두 가지 감쇠는 서로 다릅니다")), FadeIn(self.evidence()), run_time=0.8)

        # ---- left: temporal convergence on a log axis
        left = Panel(-1.55, 3.4, (-13.0, 0.5), (0, -4, -8, -12), "Remaining error max|e| (nm)", ERR,
                     x_range=(0, 850), x_ticks=(0, 200, 400, 600, 800), x_title="Iteration n",
                     tick_fmt=pow10, x0=-5.5, w=4.9, unit_note="로그 축")
        n = np.arange(res.size)
        pts = [left.c2p(k, np.log10(v)) for k, v in zip(n, res)]
        curve = DashedVMobject(VMobject(stroke_color=ERR, stroke_width=3).set_points_as_corners(pts), num_dashes=90)
        tol = DashedLine(left.c2p(0, np.log10(meta["tol_nm"])), left.c2p(850, np.log10(meta["tol_nm"])),
                         stroke_color=MUTED, stroke_width=2, dash_length=0.08)
        tol_lab = T("수렴 기준", SMALL, MUTED).next_to(left.c2p(0, np.log10(meta["tol_nm"])), UP, buff=0.06,
                                                   aligned_edge=LEFT).shift(0.1 * RIGHT)
        self.play(FadeIn(left), run_time=0.6)
        self.play(Create(curve), FadeIn(tol), FadeIn(tol_lab), run_time=2.2)
        notes = VGroup()
        for k in ANNOTATE_ITERS:
            p = left.c2p(k, np.log10(res[k]))
            notes.add(Dot(p, radius=0.05, color=ERR), T(f"n={k}: {sci(res[k])} nm", SMALL, ERR)
                      .next_to(p, RIGHT, buff=0.1))
        pf = left.c2p(n_final, np.log10(res[-1]))
        notes.add(Dot(pf, radius=0.06, color=ERR),
                  T(f"n={n_final}: {residual_bound(meta)}", SMALL, ERR).next_to(pf, UP, buff=0.35).shift(0.9 * LEFT))
        self.say("① 반복 방향: Iteration n이 늘수록 남은 오차가 줄어듭니다 (수렴)")
        self.play(FadeIn(notes), run_time=0.8)
        self.wait(3.0)

        # ---- right: spatial damping of the converged correction, full range (scale change from S3)
        right = Panel(-1.55, 3.4, (-1.0, 4.5), (0, 2, 4), "Mask correction (nm)", MASK,
                      x_title="Distance from left edge (µm)", x0=1.05, w=5.55)
        scale_note = T("배율 변경: 전체 범위 −1 ~ 4.5 nm (S3는 ±0.6 nm 확대 축)", SMALL, INK, weight="BOLD")
        scale_note.next_to(right.label, UP, buff=0.12, aligned_edge=LEFT)
        s_u = series(right, x, u, "mask")
        self.play(FadeIn(right), FadeIn(scale_note), run_time=0.8)
        self.play(Create(s_u["line"]), FadeIn(s_u["marks"]), run_time=1.6)
        self.play(Indicate(scale_note, color=MASK, scale_factor=1.05), run_time=0.8)
        self.say("② 공간 방향: 수렴한 최종 보정의 진폭이 경계에서 멀어질수록 줄어듭니다")
        self.wait(2.5)

        peaks = self.peak_labels(right, x, u)
        self.play(FadeIn(peaks), run_time=1.0)
        self.say(f"이 예: 주기 ≈ {pred['L_um']:.2f} µm, 진폭이 1/e로 줄어드는 거리 ≈ {pred['decay_length_um']:.2f} µm")
        self.wait(3.5)
        self.say("①의 오차는 사라지고, ②의 진동은 최종 마스크에 남습니다")
        self.wait(4.0)
        self.say("가로축이 다릅니다: Iteration n  ↔  Distance from left edge (µm)")
        self.wait(3.0)

    def peak_labels(self, panel, x, u, x_from=0.8, x_to=6.0):
        """Measured local maxima of the converged correction (data, not a fitted curve)."""
        g = VGroup()
        j = np.flatnonzero((x > x_from) & (x < x_to))
        for k in j:
            if u[k] > u[k - 1] and u[k] >= u[k + 1] and u[k] > 0:
                p = panel.c2p(x[k], u[k])
                g.add(T(f"+{u[k]:.2f}", SMALL, MASK).next_to(p, UP, buff=0.12))
        return g
