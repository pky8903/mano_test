"""S6 — what is changed and what is held fixed: range sweep (M) and damping sweep (a).

Each case is an independently solved scenario; switching between them is a
cross-fade between solutions, never an intermediate physical state.
"""

import numpy as np
from manim import (DOWN, LEFT, RIGHT, UP, Brace, Create, FadeIn, FadeOut, Line, VGroup)

from common import (INK, MASK, MUTED, SAFE_X, SMALL, TITLE_Y, Base, Panel, T, card, envelope, envelope_valid_from,
                    load, series)

X_RANGE = (0.0, 12.0)  # one horizontal mapping for both mini-sequences
Y_RANGE = (-0.6, 0.6)  # one fixed amplitude scale for both mini-sequences
SHADES = ("#9DB8DC", "#4F82C3", MASK)  # ordered: light -> dark
RANGE = ("range_13", "range_18", "range_24")
DAMP = ("damp_025", "damp_030", "damp_040")


class S6HeldFixed(Base):
    def construct(self):
        self.play(FadeIn(self.title("무엇을 바꾸고, 무엇을 고정했나")), FadeIn(self.evidence()), run_time=0.8)
        self.p = Panel(-1.75, 2.85, Y_RANGE, (-0.5, 0, 0.5), "Mask correction (nm)", MASK, x_range=X_RANGE,
                       x_ticks=range(0, 13, 2), x_title="Distance from left edge (µm)",
                       unit_note="고정 축 ±0.6 nm (정규화하지 않음) · 첫 control은 축 밖")
        self.play(FadeIn(self.p), run_time=0.6)

        # ---- range comparison: M changes, total nonlocal strength b fixed
        rng = {s: load(s) for s in RANGE}
        cfg = [rng[s][1]["config"] for s in RANGE]
        assert len({(c["a"], c["b"], c["d_um"], c["E0_nm"]) for c in cfg}) == 1
        c0 = cfg[0]
        info = self.info_card("범위 비교",
                              [f"바꾼 것: 영향 범위 M = {' → '.join(str(c['M']) for c in cfg)} "
                               f"(R = {' → '.join(f'{c['M'] * c['d_um']:.2f}' for c in cfg)} µm)",
                               f"고정: 자기 감도 a = {c0['a']:g}, 이웃 전체 감도 b = {c0['b']:g}, 간격 d, 경계 오차",
                               "b 총합 고정 → 이웃 하나당 가중치 b/(2M+1)은 줄어듦"])
        self.play(FadeIn(info), run_time=0.8)
        self.say("a: 자기 자신에 대한 감도 · b: 범위 안 이웃 전체에 나눠진 감도")
        self.wait(2.5)
        self.sweep(rng, RANGE, lambda c: f"M={c['M']}")
        self.say("이 예에서는: 범위가 넓을수록 주기는 길어지고, 감쇠는 느려집니다")
        self.wait(3.5)
        self.play(FadeOut(self.drawn), FadeOut(info), run_time=0.7)

        # ---- damping comparison: a changes at fixed b, M, d, forcing
        dmp = {s: load(s) for s in DAMP}
        cfg = [dmp[s][1]["config"] for s in DAMP]
        assert len({(c["b"], c["M"], c["d_um"], c["E0_nm"]) for c in cfg}) == 1
        c0 = cfg[0]
        info = self.info_card("국소/비국소 균형 비교",
                              [f"바꾼 것: 자기 감도 a = {' → '.join(f'{c['a']:g}' for c in cfg)}",
                               f"고정: b = {c0['b']:g}, M = {c0['M']}, 간격 d, 경계 오차",
                               "진폭과 감쇠가 함께 바뀜 (감쇠만 분리한 실험 아님)"])
        self.play(FadeIn(info), run_time=0.8)
        self.sweep(dmp, DAMP, lambda c: f"a={c['a']:g}")
        self.say("이 예에서는: a가 클수록 감쇠가 강해지고 진폭도 함께 줄어듭니다")
        self.wait(3.5)
        self.say("법칙은 이 모델 조건에서의 결과입니다 — 모든 범위·모델에 일반화하지 않습니다", size=22)
        self.wait(2.5)

    # ---------------------------------------------------------------- helpers
    def info_card(self, title, lines):
        c = card(title, lines, width=7.4, accent=INK)
        c.scale(0.85)
        return c.move_to([SAFE_X - c.width / 2, 2.45, 0])

    def sweep(self, data, ids, name):
        """Draw each independently solved case; keep earlier ones as lighter references."""
        self.drawn = VGroup()
        for k, sid in enumerate(ids):
            arr, meta = data[sid]
            c, pred = meta["config"], meta["prediction"]
            s = series(self.p, arr["x_um"], arr["u_star_nm"], "mask", color=SHADES[k], width=2.4 + 0.6 * k,
                       offscale_labels=False)
            x0 = envelope_valid_from(arr["x_um"][:400], arr["u_star_nm"][:400], pred)
            env = envelope(self.p, pred, x0, color=SHADES[k])
            per = self.period_mark(arr["x_um"], arr["u_star_nm"], x0, SHADES[k])
            tag = T(f"{name(c)}: 주기 {pred['L_um']:.2f} µm · 감쇠 길이 {pred['decay_length_um']:.2f} µm · "
                    f"변동 {meta['mask_variation_nm']:.2f} nm", SMALL, SHADES[k], weight="BOLD")
            tag.move_to(self.p.c2p(3.0, -0.33 - 0.09 * k), aligned_edge=LEFT)
            self.play(Create(s["line"]), FadeIn(s["marks"]), FadeIn(s["off"]), run_time=1.1)
            self.play(Create(env), FadeIn(per), FadeIn(tag), run_time=0.9)
            self.wait(1.4)
            prev_extras = VGroup(env, per)
            if k < len(ids) - 1:
                self.play(prev_extras.animate.set_opacity(0.0), s["marks"].animate.set_opacity(0.35),
                          s["line"].animate.set_stroke(opacity=0.45), run_time=0.4)
            self.drawn.add(s["line"], s["marks"], s["off"], env, per, tag)
        note = T(f"점선: 지배 모드 포락선(근사, 여러 모드가 겹치는 경계 근처 제외)", SMALL, MUTED)
        note.next_to(self.p.c2p(X_RANGE[1], Y_RANGE[1]), DOWN, buff=0.08, aligned_edge=RIGHT)
        self.play(FadeIn(note), run_time=0.4)
        self.drawn.add(note)

    def period_mark(self, x, u, x_from, color):
        """Distance between two successive measured maxima beyond x_from (equivalent phases)."""
        j = np.flatnonzero((x > x_from) & (x < X_RANGE[1]))
        peaks = [k for k in j if u[k] > u[k - 1] and u[k] >= u[k + 1] and u[k] > 0][:2]
        if len(peaks) < 2:
            return VGroup()
        y = self.p.c2p(0, max(u[peaks[0]], u[peaks[1]]) + 0.08)[1]
        seg = Line(self.p.c2p(x[peaks[0]], 0) * [1, 0, 0] + [0, y, 0], self.p.c2p(x[peaks[1]], 0) * [1, 0, 0] + [0, y, 0])
        br = Brace(seg, UP, color=color, buff=0.02)
        # positions are sampled peaks (quantized by d); the exact period is in the tag
        return VGroup(br, T("주기", SMALL, color).next_to(br, UP, buff=0.03))
