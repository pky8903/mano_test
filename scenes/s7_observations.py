"""S7 — user-reported production observations (qualitative cards) and what they do not establish.

No production numbers are shown: the amplitude convention and measurement window of
the two reported values have not been confirmed as equivalent (PRD S7 default).
"""

from manim import DOWN, LEFT, RIGHT, UP, Arrow, FadeIn, FadeOut, GrowArrow, Rectangle, VGroup

from common import (ERR, INK, MASK, MUTED, SAFE_X, SMALL, Base, T, card, pill)

OBS = "#5B6B7A"
HYP = "#8A5A00"


class S7Observations(Base):
    def construct(self):
        self.play(FadeIn(self.title("보고된 관측과 해석의 한계")), FadeIn(self.evidence("Reported observation")),
                  run_time=0.8)

        c1 = card("EP-only calibration",
                  ["CD gauge (T/L/TL/TR/R/B/BL/BR/C) 제외",
                   "CD 예측은 나빠짐",
                   "Target layout 초기 오차 분포는 개선",
                   "보고된 OPC 막대 폭 진동: 감소"],
                  width=6.1, accent=OBS, tag=pill("Reported observation", OBS))
        c2 = card("CD + EP fitting (CNN 계열 모델)",
                  ["CD gauge와 왼쪽 블록 경계 EP gauge 함께 fitting",
                   "Target layout 초기 오차 분포: 미제공",
                   "보고된 OPC 막대 폭 진동: 다시 나타남"],
                  width=6.1, accent=OBS, tag=pill("Reported observation", OBS))
        VGroup(c1, c2).arrange(RIGHT, buff=0.35, aligned_edge=UP).move_to([0, 1.3, 0])
        s1 = pill("Reduced oscillation", MASK).next_to(c1, DOWN, buff=0.15)
        s2 = pill("Oscillation returned", ERR).next_to(c2, DOWN, buff=0.15)
        self.play(FadeIn(c1), run_time=0.8)
        self.play(FadeIn(s1), run_time=0.4)
        self.say("사용자 보고 1: EP-only 모델에서 막대 폭 진동이 줄었습니다")
        self.wait(3.5)
        self.play(FadeIn(c2), FadeIn(s2), run_time=0.8)
        self.say("사용자 보고 2: CD와 EP를 함께 맞춘 모델에서 진동이 다시 나타났습니다")
        self.wait(3.5)

        # calibration layout != target layout
        lay = self.layouts().move_to([-3.4, -1.75, 0])
        self.play(FadeIn(lay), run_time=0.8)
        self.say("모델을 맞춘 layout과 보정할 target layout은 다릅니다")
        self.wait(3.0)

        hyp = card("해석 (가설)",
                   ["두 모델은 초기 오차 분포와 공간 응답을 함께 바꿨을 수 있음",
                    "→ 이 비교만으로 어느 쪽이 원인인지 특정할 수 없음",
                    "보고된 진동 크기는 측정 정의가 확인될 때까지 수치 비교하지 않음"],
                   width=6.4, accent=HYP, tag=pill("Hypothesis", HYP)).move_to([3.2, -1.75, 0])
        self.play(FadeIn(hyp), run_time=0.8)
        self.say("calibration이 좋아져도 target layout의 초기 오차가 같이 좋아진다는 보장은 없습니다")
        self.wait(5.5)

    def layouts(self):
        def icon(title, bars, color):
            frame = Rectangle(width=2.3, height=1.15, stroke_color=color, stroke_width=2)
            g = VGroup()
            for k, (w, h) in enumerate(bars):
                g.add(Rectangle(width=w, height=h, stroke_width=0, fill_color=color, fill_opacity=0.6))
            g.arrange(RIGHT, buff=0.12).move_to(frame)
            return VGroup(frame, g, T(title, SMALL, INK).next_to(frame, DOWN, buff=0.08))

        cal = icon("Calibration layout", [(0.12, 0.9), (0.3, 0.5), (0.12, 0.9), (0.5, 0.3), (0.12, 0.7)], OBS)
        tgt = icon("Target layout", [(0.6, 0.9)] + [(0.08, 0.9)] * 8, INK)
        ne = T("≠", 40, INK)
        return VGroup(cal, ne, tgt).arrange(RIGHT, buff=0.3)
