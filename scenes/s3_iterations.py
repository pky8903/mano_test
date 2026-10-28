"""S3 — causal choreography of P-type correction on the `main` scenario.

Per detailed step: read e(n) -> preview du = eta e(n) -> apply to u -> recompute
e(n+1) -> only then advance the iteration label. All controls update at once.
"""

import numpy as np
from manim import (DOWN, LEFT, RIGHT, UP, Arrow, Circumscribe, Create, DashedVMobject, FadeIn, FadeOut, Transform,
                   VGroup)

from common import (ERR, HILITE, LABEL, MASK, MUTED, PLOT_W, PLOT_X0, SMALL, Base, Panel, T, load, residual_bound, series, visible)

U_RANGE = (-0.6, 0.6)  # fixed for the whole sequence
E_RANGE = (-0.06, 0.06)  # fixed for the whole sequence
DETAILED = 3  # 0->1, 1->2, 2->3
FAST_UNTIL = 10
JUMPS = (15, 20, 30, 50, 100, 200, 400)

STEP_NOTES = {
    0: "첫 control의 오차는 줄었지만, 이웃 control에는 음(−)의 오차가 생겼습니다",
    1: "음의 오차 → 이웃을 좁힘 → 그 영향으로 더 안쪽에 양(+)의 오차",
    2: "넓힘과 좁힘 영역이 번갈아 블록 안쪽으로 퍼집니다",
}


class S3Iterations(Base):
    def construct(self):
        arr, meta = load("main")
        self.arr, self.meta = arr, meta
        x = arr["x_um"][: arr["u_hist_nm"].shape[1]]
        self.x = x
        self.iters = [int(n) for n in arr["iters"]]
        M = meta["config"]["M"]
        d = meta["config"]["d_um"]
        self.M, self.d = M, d
        eta = meta["eta"]
        assert self.iters[: FAST_UNTIL + 1] == list(range(FAST_UNTIL + 1))
        assert self.iters[-1] == meta["final_iter"]

        self.play(FadeIn(self.title("보정이 이웃으로 번지는 과정")), FadeIn(self.evidence()), run_time=0.8)
        self.up = Panel(0.35, 2.2, U_RANGE, (-0.5, 0, 0.5), "Mask correction (nm)", MASK,
                        unit_note="누적 보정 u · 고정 확대 축(축 밖 값은 숫자로 표시)")
        self.lo = Panel(-2.15, 1.9, E_RANGE, (-0.05, 0, 0.05), "Remaining error (nm)", ERR,
                        x_title="Distance from left edge (µm)", unit_note="고정 확대 축(축 밖 값은 숫자로 표시)")
        self.play(FadeIn(self.up), FadeIn(self.lo), run_time=1.0)

        k = 0
        self.su = series(self.up, x, arr["u_hist_nm"][k], "mask")
        self.se = series(self.lo, x, arr["e_hist_nm"][k], "error")
        self.band = self.support_band(0)
        self.label = self.iter_label(0)
        self.play(FadeIn(self.band), *[FadeIn(m) for m in self.su.values()], *[FadeIn(m) for m in self.se.values()],
                  FadeIn(self.label), run_time=1.0)
        self.say("시작: 마스크 보정 0, 첫 control에만 양(+)의 오차 (+ 오차 → 마스크를 넓힘)")
        self.wait(2.5)

        for n in range(DETAILED):
            self.detailed_step(n, eta)
            self.say(STEP_NOTES[n])
            self.wait(3.0 if n < 2 else 2.0)

        self.say("Iteration 3 → 10: 같은 순서를 빠르게 반복합니다")
        for n in range(DETAILED, FAST_UNTIL):
            self.fast_step(n, n + 1, run_time=0.55)
        self.wait(0.8)

        skip = T("Intermediate iterations skipped · 중간 반복 생략", SMALL, MUTED)
        skip.next_to(self.label, DOWN, buff=0.08, aligned_edge=RIGHT)
        # beyond ~10 iterations the possible support covers the whole view; drop the band
        self.play(FadeIn(skip), FadeOut(self.band), run_time=0.4)
        self.band = None
        self.say("이후 선택한 반복만 표시합니다")
        prev = FAST_UNTIL
        for n in (*JUMPS, self.iters[-1]):
            self.fast_step(prev, n, run_time=0.45)
            prev = n
        self.say(f"Iteration {prev}: 수렴 판정 통과 ({residual_bound(meta)}) — 오차는 수렴, 보정은 진동")
        self.wait(4.0)

    # ---------------------------------------------------------------- helpers
    def idx(self, n):
        return self.iters.index(n)

    def iter_label(self, n):
        t = T(f"Iteration n = {n}", LABEL, weight="BOLD")
        return t.move_to([PLOT_X0 + PLOT_W - t.width / 2, self.up.label.get_center()[1], 0])

    def support_band(self, n):
        """Controls that e(n) can reach: up to n*M controls from the edge (possible support, not a wave)."""
        reach = (n * self.M + 0.5) * self.d
        return VGroup(self.up.band(0, reach), self.lo.band(0, reach))

    def detailed_step(self, n, eta):
        a = self.arr
        i, i1 = self.idx(n), self.idx(n + 1)
        u, e, du = a["u_hist_nm"][i], a["e_hist_nm"][i], a["du_hist_nm"][i]

        # 1. read the current error
        self.say(f"① Iteration {n}: 현재 오차 e를 읽습니다")
        reach = n * self.M
        marks = VGroup(*[m for j, m in enumerate(self.se["marks"]) if j <= max(reach, 0)])
        targets = [marks]
        if len(self.se["off"]):
            targets.append(self.se["off"])
        self.play(*[Circumscribe(t, color=HILITE, buff=0.06, time_width=0.8) for t in targets], run_time=1.6)

        # 2. preview the increment du = eta * e (all controls at once)
        self.say(f"② 보정량 미리보기: Δu = η · e  (η = {eta:g}, 모든 control 동시에)")
        prev = series(self.up, self.x, u + du, "mask")
        ghost = DashedVMobject(prev["line"], num_dashes=160).set_stroke(opacity=0.55)
        arrows = self.increment_arrows(u, du)
        self.play(Create(ghost), *[Create(ar) for ar in arrows], run_time=1.8)
        self.wait(1.0)

        # 3. apply to the accumulated correction
        self.say("③ 누적 마스크 보정에 더합니다:  u ← u + Δu")
        new_u = series(self.up, self.x, a["u_hist_nm"][i1], "mask")
        self.morph(self.su, new_u, run_time=1.4, extra=[FadeOut(ghost), FadeOut(arrows)])
        self.wait(0.6)

        # 4. recompute the error caused by the changed mask
        self.say("④ 바뀐 마스크로 오차를 다시 계산합니다")
        new_e = series(self.lo, self.x, a["e_hist_nm"][i1], "error")
        new_band = self.support_band(n + 1)
        self.morph(self.se, new_e, run_time=1.4, extra=[Transform(self.band, new_band)])
        self.wait(0.5)

        # 5. only now advance the iteration label
        self.play(Transform(self.label, self.iter_label(n + 1)), run_time=0.5)

    def fast_step(self, n, m, run_time):
        a = self.arr
        j = self.idx(m)
        self.morph(self.su, series(self.up, self.x, a["u_hist_nm"][j], "mask"), run_time=run_time)
        extra = [Transform(self.band, self.support_band(m))] if self.band is not None else []
        self.morph(self.se, series(self.lo, self.x, a["e_hist_nm"][j], "error"), run_time=run_time, extra=extra)
        self.play(Transform(self.label, self.iter_label(m)), run_time=0.2)

    def morph(self, cur, new, run_time, extra=()):
        anims = [Transform(cur["line"], new["line"]), Transform(cur["marks"], new["marks"]), *extra]
        if len(cur["off"]) or len(new["off"]):
            anims += [FadeOut(cur["off"]), FadeIn(new["off"])]
        self.play(*anims, run_time=run_time)
        cur["off"] = new["off"]

    def increment_arrows(self, u, du):
        g = VGroup()
        ya, yb = self.up.yr
        m = visible(self.x, self.up.xr)
        for j in np.flatnonzero(m):
            if du[j] == 0:
                continue
            y0, y1 = np.clip(u[j], ya, yb), np.clip(u[j] + du[j], ya, yb)
            p0, p1 = self.up.c2p(self.x[j], y0), self.up.c2p(self.x[j], y1)
            if abs(p1[1] - p0[1]) < 0.05:
                continue
            g.add(Arrow(p0, p1, buff=0, color=MASK, stroke_width=3, tip_length=0.1,
                        max_tip_length_to_length_ratio=0.4, max_stroke_width_to_length_ratio=20))
            if u[j] + du[j] > yb or u[j] + du[j] < ya:
                g.add(T(f"Δu = {du[j]:+.2f} nm", SMALL, MASK).next_to(p1, RIGHT, buff=0.12).shift(0.15 * DOWN))
        return g
