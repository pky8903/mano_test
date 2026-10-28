"""S2 — one control changes its own prediction and its neighbors' (columns of A from data)."""

import numpy as np
from manim import (DOWN, LEFT, RIGHT, UP, UR, Arrow, Brace, Circle, FadeIn, FadeOut, GrowArrow, Line, Rectangle,
                   Transform, VGroup)

from common import (HILITE, INK, LABEL, MASK, MUTED, SMALL, Base, Panel, T, load)

STRIP_Y = 2.35


class S2Coupling(Base):
    def construct(self):
        arr, meta = load("main")
        cfg = meta["config"]
        M, d = cfg["M"], cfg["d_um"]
        x = arr["x_um"][: arr["resp_interior_nm"].size]
        ri, re_ = arr["resp_interior_nm"], arr["resp_edge_nm"]
        j0 = meta["response_control"]
        R = M * d

        self.play(FadeIn(self.title("보정 하나가 이웃의 예측도 바꿉니다")), FadeIn(self.evidence()), run_time=0.8)
        self.p = Panel(-1.9, 3.3, (0.0, 0.35), (0, 0.1, 0.2, 0.3), "Predicted CD change (nm)", INK,
                       x_title="Distance from left edge (µm)", unit_note="한 control의 마스크를 +1 nm 바꿨을 때",
                       tick_fmt="{:.1f}")
        strip = self.control_strip(x)
        self.play(FadeIn(strip), FadeIn(self.p), run_time=1.0)

        hl, du_lab = self.highlight(x[j0])
        self.play(FadeIn(hl), FadeIn(du_lab), run_time=0.8)
        self.say("한 control의 마스크를 1 nm 넓힌다고 해 봅시다 (설명을 위한 강조)")
        self.wait(2.0)

        local, local_lab = self.local_arrow(x[j0], ri[j0])
        self.play(GrowArrow(local), FadeIn(local_lab), run_time=1.2)
        self.say(f"자기 자신의 예측 CD가 가장 크게 바뀝니다 (+{ri[j0]:.2f} nm)")
        self.wait(2.5)

        nb, nb_lab = self.neighbor_arrows(x, ri, j0)
        self.play(*[GrowArrow(a) for a in nb], FadeIn(nb_lab), run_time=1.2)
        self.say(f"범위 안 이웃들도 같은 방향으로 조금씩 바뀝니다 (각 +{ri[j0 + 1]:.3f} nm)")
        self.wait(2.5)

        band, brace = self.range_marks(x[j0] - R, x[j0] + R, x[j0], R, M)
        self.play(FadeIn(band), FadeIn(brace), run_time=1.0)
        self.say("영향 범위 R은 control 배열 위의 거리입니다 — 퍼져 나가는 파동이 아닙니다")
        self.wait(3.0)

        # move to the first control at the left boundary: truncated window, not renormalized
        hl2, du2 = self.highlight(x[0])
        local2, local2_lab = self.local_arrow(x[0], re_[0])
        nb2, nb2_lab = self.neighbor_arrows(x, re_, 0)
        band2, brace2 = self.range_marks(0.0, R, None, R, M)
        outside = T("← 블록 쪽에는 이웃 없음 (창을 다시 정규화하지 않음)", SMALL, MUTED).move_to(
            self.p.c2p(1.7, 0.31), aligned_edge=LEFT)
        self.play(FadeOut(VGroup(nb, nb_lab, band, brace, local_lab)), run_time=0.5)
        self.play(Transform(hl, hl2), Transform(du_lab, du2), Transform(local, local2), run_time=1.0)
        self.play(*[GrowArrow(a) for a in nb2], FadeIn(nb2_lab), FadeIn(local2_lab), FadeIn(band2), FadeIn(brace2),
                  FadeIn(outside), run_time=1.0)
        self.say(f"첫 control은 경계에 있어 오른쪽 이웃 {M}개에만 영향을 줍니다")
        self.wait(3.0)
        self.say("그래서 한 곳을 고치면 이웃의 오차가 바뀌고, 다음 보정이 이어집니다")
        self.wait(3.5)

    # ---------------------------------------------------------------- helpers
    def control_strip(self, x):
        g = VGroup()
        for xi in x[x <= self.p.xr[1] + 1e-9]:
            p = self.p.c2p(xi, 0)
            g.add(Line([p[0], STRIP_Y - 0.12, 0], [p[0], STRIP_Y + 0.12, 0], stroke_color=MUTED, stroke_width=2))
        x_left = self.p.c2p(0, 0)[0]
        block = Rectangle(width=0.7, height=0.4, stroke_width=0, fill_color=INK, fill_opacity=0.75)
        block.move_to([x_left - 0.12, STRIP_Y, 0], aligned_edge=RIGHT)
        g.add(block, T("블록", SMALL, MUTED).next_to(block, LEFT, buff=0.1))
        g.add(T("control 배열 (간격 80 nm, 예시)", SMALL, MUTED).next_to(g[0], UP, buff=0.12, aligned_edge=LEFT))
        return g

    def highlight(self, xi):
        p = self.p.c2p(xi, 0)
        c = Circle(radius=0.17, stroke_color=HILITE, stroke_width=5).move_to([p[0], STRIP_Y, 0])
        lab = T("Δu = +1 nm", SMALL, MASK, weight="BOLD").next_to(c, DOWN, buff=0.06)
        return c, lab

    def local_arrow(self, xi, v):
        a = Arrow(self.p.c2p(xi, 0), self.p.c2p(xi, v), buff=0, color=INK, stroke_width=9,
                  max_stroke_width_to_length_ratio=30, tip_length=0.2)
        lab = T(f"자기 자신 +{v:.2f}", SMALL, INK, weight="BOLD").next_to(self.p.c2p(xi, v), RIGHT, buff=0.12)
        return a, lab

    def neighbor_arrows(self, x, col, j0):
        g = VGroup()
        for j in np.flatnonzero(col):
            if j == j0:
                continue
            g.add(Arrow(self.p.c2p(x[j], 0), self.p.c2p(x[j], col[j]), buff=0, color=MASK, stroke_width=3,
                        max_stroke_width_to_length_ratio=30, tip_length=0.1, max_tip_length_to_length_ratio=0.5))
        right = max(np.flatnonzero(col))
        lab = T(f"이웃 각 +{col[right]:.3f}", SMALL, MASK).next_to(self.p.c2p(x[right], col[right]), UR, buff=0.08)
        return g, lab

    def range_marks(self, x_from, x_to, xc, R, M):
        band = self.p.band(max(x_from, 0.0), x_to, opacity=0.6).set_z_index(-1)
        top = self.p.c2p(0, 0.17)[1]
        seg = Line(self.p.c2p(xc if xc is not None else x_from, 0) * [1, 0, 0] + [0, top, 0],
                   self.p.c2p(x_to, 0) * [1, 0, 0] + [0, top, 0])
        br = Brace(seg, UP, color=MUTED, buff=0.05)
        lab = T(f"R = {R:.2f} µm (이웃 {M}개)", SMALL, INK).next_to(br, RIGHT, buff=0.12)
        return band, VGroup(br, lab)
