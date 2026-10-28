"""S8 — management action frame (PRD suggested Korean copy). Held >= 8 s."""

from manim import DOWN, LEFT, RIGHT, UP, FadeIn, LaggedStart, Line, VGroup

from common import (BODY, INK, MASK, MUTED, SAFE_X, SMALL, Base, T)

ACTIONS = (
    "Target layout의 초기 오차 분포를 확인합니다.",
    "CD·EP fitting 정확도를 유지하며 공간 응답 조건을 개선합니다.",
    "필요하면 correction에 평탄성 조건을 추가하고 EPE 영향을 평가합니다.",
)
FINAL_HOLD_S = 10.5


class S8Action(Base):
    def construct(self):
        self.play(FadeIn(self.title("다음 단계")), run_time=0.8)
        summary = VGroup(
            T("오차가 수렴해도, 최종 마스크 보정은 진동할 수 있습니다.", BODY, INK, weight="BOLD"),
            T("진폭은 경계의 초기 오차와 모델의 공간 응답(범위, 국소/비국소 균형)이 함께 결정합니다.", BODY - 2, MUTED),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([-SAFE_X, 2.2, 0], aligned_edge=LEFT)
        self.play(FadeIn(summary), run_time=1.0)
        self.wait(4.0)

        rule = Line([-SAFE_X, 1.25, 0], [SAFE_X, 1.25, 0], stroke_color=MUTED, stroke_width=1.5)
        rows = VGroup()
        for k, s in enumerate(ACTIONS, start=1):
            num = T(f"{k}", 34, MASK, weight="BOLD")
            rows.add(VGroup(num, T(s, BODY + 2, INK)).arrange(RIGHT, buff=0.4))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.55).move_to([-SAFE_X + 0.3, -0.6, 0], aligned_edge=LEFT)
        self.play(FadeIn(rule), LaggedStart(*[FadeIn(r, shift=0.1 * RIGHT) for r in rows], lag_ratio=0.5), run_time=2.5)
        foot = T("Toy-model simulation · Reported observation · Hypothesis를 구분해 해석하십시오", SMALL, MUTED)
        foot.move_to([0, -3.3, 0])
        self.play(FadeIn(foot), run_time=0.5)
        self.wait(FINAL_HOLD_S)
