"""S5 — same edge shape, magnitude only; then the background extension (u_total - u_bg)."""

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, Brace, Create, DashedVMobject, FadeIn, FadeOut, Line, Transform, VGroup

from common import (INK, MASK, MUTED, NOMINAL, SMALL, Base, Panel, T, load, series)

Y_RANGE = (-1.2, 1.2)  # one fixed scale for the whole amplitude comparison
SCALES = (("scale_050", "#9DB8DC", 2.4), ("main", "#4F82C3", 3.0), ("scale_200", MASK, 3.6))
WINDOW = (0.8, 8.0)


class S5Contrast(Base):
    def construct(self):
        self.play(FadeIn(self.title("비교할 것은 경계의 '편차'입니다")), FadeIn(self.evidence()), run_time=0.8)
        p = Panel(-1.9, 4.0, Y_RANGE, (-1, -0.5, 0, 0.5, 1), "Mask correction (nm)", MASK,
                  x_title="Distance from left edge (µm)", unit_note="고정 축 ±1.2 nm · ▲ 첫 control은 축 밖")
        self.p = p
        self.play(FadeIn(p), run_time=0.6)

        data = {sid: load(sid) for sid, _, _ in SCALES}
        E0 = {sid: data[sid][1]["config"]["E0_nm"] for sid in data}
        assert all(data[s][1]["config"]["E_bulk_nm"] == 0 for s in data)  # zero background, same shape

        curves, labels = {}, VGroup()
        sid, col, w = SCALES[1]
        curves[sid] = self.curve(data[sid][0], col, w)
        self.play(Create(curves[sid]["line"]), FadeIn(curves[sid]["marks"]), FadeIn(curves[sid]["off"]), run_time=1.2)
        labels.add(self.tag(data[sid], col, 1))  # rows ordered by size: 0.5, 1, 2 nm
        self.play(FadeIn(labels[-1]), run_time=0.4)
        self.say("경계 control에만 오차가 있고 나머지는 0인 예 (모양 고정)")
        self.wait(2.0)

        for k, (sid, col, w) in ((0, SCALES[0]), (2, SCALES[2])):
            curves[sid] = self.curve(data[sid][0], col, w)
            labels.add(self.tag(data[sid], col, k))
            self.play(Create(curves[sid]["line"]), FadeIn(curves[sid]["marks"]), FadeIn(curves[sid]["off"]),
                      FadeIn(labels[-1]), run_time=1.0)
        win = self.window_mark()
        self.play(FadeIn(win), run_time=0.5)
        self.say("크기만 바꾸면: 보정 전체가 같은 배율로 커지고 작아집니다 (주기·감쇠는 그대로)")
        self.wait(3.5)
        self.say("경계 편차를 줄이면 남는 진동도 같은 비율로 줄어듭니다 (이 모델에서 정확히 성립)")
        self.wait(3.0)

        # ---- background extension: compare the additional response to a separately solved reference
        a_tot, m_tot = load("bg_total")
        a_ref, m_ref = load("bg_ref")
        a_main, _ = data["main"]
        Eb = m_tot["config"]["E_bulk_nm"]
        assert m_ref["config"]["E_bulk_nm"] == Eb and m_ref["config"]["E0_nm"] == 0
        self.play(FadeOut(VGroup(*[v for c in curves.values() for v in c.values()], labels, win)), run_time=0.6)
        ref = self.curve(a_ref, NOMINAL, 3.0)
        tot = self.curve(a_tot, "#4F82C3", 3.0)
        ref_lab = T(f"균일 배경 오차 {Eb:g} nm만 있을 때 (별도 계산)", SMALL, MUTED).next_to(p.c2p(2.2, 0.62), UP, buff=0.05,
                                                                                aligned_edge=LEFT)
        tot_lab = T(f"배경 {Eb:g} nm + 경계 편차 {m_tot['config']['E0_nm']:g} nm", SMALL, "#4F82C3").next_to(
            p.c2p(2.2, 0.95), UP, buff=0.05, aligned_edge=LEFT)
        self.play(Create(ref["line"]), FadeIn(ref["marks"]), FadeIn(ref_lab), run_time=1.0)
        self.play(Create(tot["line"]), FadeIn(tot["marks"]), FadeIn(tot["off"]), FadeIn(tot_lab), run_time=1.0)
        self.say("배경 오차가 있으면: 균일한 오차도 경계 근처에서는 평탄하지 않은 보정을 만듭니다")
        self.wait(2.5)

        diff = a_tot["u_star_nm"] - a_ref["u_star_nm"]
        assert np.max(np.abs(diff - a_main["u_star_nm"])) < 1e-12
        add = self.curve({"x_um": a_tot["x_um"], "u_star_nm": diff}, MASK, 3.6)
        add_lab = T("추가 보정 = (배경+편차) − (배경만)", SMALL, MASK, weight="BOLD").move_to(tot_lab, aligned_edge=LEFT)
        ghost = self.curve(a_main, INK, 1.6)
        ghost_line = DashedVMobject(ghost["line"], num_dashes=120)
        ghost_lab = T("점선: 배경 없는 앞의 예", SMALL, INK).move_to(ref_lab, aligned_edge=LEFT)
        self.play(Transform(tot["line"], add["line"]), Transform(tot["marks"], add["marks"]),
                  FadeOut(tot["off"]), FadeIn(add["off"]), FadeOut(ref["line"]), FadeOut(ref["marks"]),
                  Transform(tot_lab, add_lab), Transform(ref_lab, ghost_lab), run_time=1.4)
        self.play(Create(ghost_line), run_time=1.0)
        self.say("편차가 만든 추가 보정만 보면 앞의 예와 같습니다 — 비교 대상은 이 추가분입니다")
        self.wait(3.0)
        self.say("오차의 모양(전이 폭)을 바꾸는 것은 별도 실험이며, 이 배율 관계를 그대로 쓰지 않습니다", size=22)
        self.wait(2.5)

    def curve(self, arr, color, width):
        return series(self.p, arr["x_um"], arr["u_star_nm"], "mask", color=color, width=width, offscale_labels=False)

    def tag(self, d, color, row):
        arr, meta = d
        E0 = meta["config"]["E0_nm"]
        s = f"경계 편차 E₀ = {E0:g} nm   첫 control {arr['u_star_nm'][0]:+.2f} nm · 변동 {meta['mask_variation_nm']:.2f} nm"
        return T(s, SMALL, color, weight="BOLD").move_to(self.p.c2p(2.2, 1.12 - 0.17 * row), aligned_edge=LEFT)

    def window_mark(self):
        y = self.p.c2p(0, -1.0)[1]
        seg = Line(self.p.c2p(WINDOW[0], 0) * [1, 0, 0] + [0, y, 0], self.p.c2p(WINDOW[1], 0) * [1, 0, 0] + [0, y, 0])
        br = Brace(seg, DOWN, color=MUTED, buff=0.02)
        lab = T(f"변동 = max(u) − min(u), {WINDOW[0]:g}–{WINDOW[1]:g} µm", SMALL, MUTED).next_to(br, UP, buff=0.05)
        return VGroup(br, lab)
