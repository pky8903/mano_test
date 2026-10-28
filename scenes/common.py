"""Shared style, layout and plotting widgets for all scenes.

Scenes consume validated arrays from data/ (via opc_osc.store.load, digest-checked);
nothing here synthesizes profiles. Text is Pango-only (no LaTeX).

Sizes: at 1080p one Manim unit is 135 px and font_size 1 renders a Hangul glyph
about 1.7 px tall, so BODY=24 -> ~40 px, TICK=16 -> ~27 px.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from manim import (
    DOWN, LEFT, RIGHT, UP, UL, UR,
    Dot, DashedVMobject, Line, Rectangle, RoundedRectangle, Scene, Square, Text, Triangle, VGroup, VMobject,
    config,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from opc_osc import store  # noqa: E402

# ---------------------------------------------------------------- palette (light, CVD-safe pair)
BG = "#F7F7F5"
INK = "#1F2933"
MUTED = "#6B7785"
GRID = "#D9DDE1"
MASK = "#1F5FAD"  # mask correction: blue, solid line, round markers
ERR = "#C8501E"  # remaining error: orange, dashed line, square markers
NOMINAL = "#9AA5B1"  # nominal mask outline
BAND = "#E8EEF6"
HILITE = "#F2C14E"

FONT = "Noto Sans CJK KR"
TITLE, BODY, LABEL, TICK, SMALL = 30, 24, 19, 16, 16

# safe area (5 %) and fixed regions
FW, FH = config.frame_width, config.frame_height
SAFE_X, SAFE_Y = FW / 2 * 0.95, FH / 2 * 0.95
TITLE_Y = SAFE_Y - 0.22
CAPTION_Y = -SAFE_Y + 0.28
PLOT_X0, PLOT_W = -5.3, 11.9  # shared horizontal mapping: 0..8 um
X_RANGE_UM = (0.0, 8.0)


def T(s, size=BODY, color=INK, weight="NORMAL", **kw) -> Text:
    return Text(s, font=FONT, font_size=size, color=color, weight=weight, **kw)


def load(sid):
    return store.load(sid)  # raises on digest mismatch


class Base(Scene):
    def setup(self):
        self.camera.background_color = BG
        self._caption = None

    # -- fixed text regions
    def title(self, s):
        t = T(s, TITLE, weight="BOLD").to_corner(UL, buff=0).move_to([-SAFE_X, TITLE_Y, 0], aligned_edge=LEFT)
        return t

    def evidence(self, s="Toy-model simulation"):
        txt = T(s, SMALL, MUTED)
        box = RoundedRectangle(corner_radius=0.08, width=txt.width + 0.3, height=txt.height + 0.18,
                               stroke_color=MUTED, stroke_width=1.5)
        g = VGroup(box, txt.move_to(box))
        return g.move_to([SAFE_X - g.width / 2, TITLE_Y, 0])

    def caption(self, s, size=BODY):
        c = T(s, size)
        if c.width > 2 * SAFE_X:
            c.scale_to_fit_width(2 * SAFE_X)
        return c.move_to([0, CAPTION_Y, 0])

    def say(self, s, run_time=0.6, size=BODY):
        """Swap the caption in the reserved caption band."""
        from manim import FadeIn, FadeOut

        new = self.caption(s, size)
        anims = [FadeIn(new, shift=0.1 * UP)]
        if self._caption is not None:
            anims.append(FadeOut(self._caption))
        self.play(*anims, run_time=run_time)
        self._caption = new
        return new


class Panel(VGroup):
    """Fixed-scale plot area. Values beyond the y-range are drawn at the edge with
    a break marker and their true value (no silent clipping, no autoscale)."""

    def __init__(self, y0, h, y_range, y_ticks, label, color, x_range=X_RANGE_UM, x_ticks=range(0, 9),
                 x_title=None, tick_fmt="{:g}", unit_note=None, x0=PLOT_X0, w=PLOT_W, x_tick_fmt="{:g}"):
        super().__init__()
        self.x0, self.y0, self.w, self.h = x0, y0, w, h
        self.xr, self.yr = x_range, y_range
        self.color = color
        xa, xb = x_range
        ya, yb = y_range
        for yt in y_ticks:
            p = self.c2p(xa, yt)
            self.add(Line(p, self.c2p(xb, yt), stroke_color=GRID, stroke_width=1.2))
            lab = tick_fmt(yt) if callable(tick_fmt) else tick_fmt.format(yt)
            self.add(T(lab, TICK, MUTED).next_to(p, LEFT, buff=0.12))
        if ya < 0 < yb:
            self.add(Line(self.c2p(xa, 0), self.c2p(xb, 0), stroke_color=MUTED, stroke_width=2))
        self.add(Line(self.c2p(xa, ya), self.c2p(xa, yb), stroke_color=MUTED, stroke_width=2))
        bottom = Line(self.c2p(xa, ya), self.c2p(xb, ya), stroke_color=MUTED, stroke_width=2)
        self.add(bottom)
        for xt in x_ticks:
            p = self.c2p(xt, ya)
            self.add(Line(p, p + 0.08 * DOWN, stroke_color=MUTED, stroke_width=2))
            if x_title:
                self.add(T(x_tick_fmt.format(xt), TICK, MUTED).next_to(p, DOWN, buff=0.12))
        lab = T(label, LABEL, color, weight="BOLD").next_to(self.c2p(xa, yb), UP, buff=0.12, aligned_edge=LEFT)
        self.label = lab
        self.add(lab)
        if unit_note:
            self.add(T(unit_note, SMALL, MUTED).next_to(lab, RIGHT, buff=0.35))
        if x_title:
            self.x_title = T(x_title, LABEL, INK).next_to(bottom, DOWN, buff=0.5)
            self.add(self.x_title)

    def c2p(self, x, y):
        xa, xb = self.xr
        ya, yb = self.yr
        return np.array([self.x0 + (x - xa) / (xb - xa) * self.w, self.y0 + (y - ya) / (yb - ya) * self.h, 0.0])

    def band(self, x_from, x_to, color=BAND, opacity=0.9):
        x_to = min(max(x_to, self.xr[0]), self.xr[1])
        r = Rectangle(width=max(1e-3, self.c2p(x_to, 0)[0] - self.c2p(x_from, 0)[0]), height=self.h,
                      stroke_width=0, fill_color=color, fill_opacity=opacity)
        return r.move_to(self.c2p(x_from, self.yr[0]), aligned_edge=DOWN + LEFT)


def visible(x_um, xr=X_RANGE_UM):
    return (x_um >= xr[0] - 1e-9) & (x_um <= xr[1] + 1e-9)


def series(panel: Panel, x_um, v, kind="mask", dash_count=160, offscale_fmt="{:+.2f} nm", color=None,
           width=None, offscale_labels=True):
    """Discrete samples joined by straight segments (no smoothing).

    Returns dict(line, marks, off). `off` holds break markers + true-value labels."""
    m = visible(x_um, panel.xr)
    xs, vs = x_um[m], np.asarray(v)[m]
    ya, yb = panel.yr
    vc = np.clip(vs, ya, yb)
    pts = [panel.c2p(x, y) for x, y in zip(xs, vc)]
    color = color or (MASK if kind == "mask" else ERR)
    width = width or (3.0 if kind == "mask" else 2.4)
    line = VMobject(stroke_color=color, stroke_width=width).set_points_as_corners(pts)
    if kind != "mask":
        line = DashedVMobject(line, num_dashes=dash_count, dashed_ratio=0.6)
    marks = VGroup(*[
        (Dot(p, radius=0.032, color=color) if kind == "mask"
         else Square(0.06, stroke_width=0, fill_color=color, fill_opacity=1).move_to(p))
        for p in pts
    ])
    off = VGroup()
    for x, val, y in zip(xs, vs, vc):
        if val == y:
            continue
        top = val > yb
        p = panel.c2p(x, y)
        tri = Triangle(fill_color=color, fill_opacity=1, stroke_width=0).scale(0.07)
        if not top:
            tri.rotate(np.pi)
        tri.move_to(p + (0.1 if top else -0.1) * UP)
        # value label sits inside the plot area, clear of the panel title
        lab = T(offscale_fmt.format(val), SMALL, color).next_to(tri, RIGHT, buff=0.1)
        lab.shift((-0.28 if top else 0.28) * UP)
        if not offscale_labels:
            lab = VGroup()
        brk = VGroup(Line(p + [-0.07, -0.03, 0], p + [0.07, 0.03, 0], stroke_color=color, stroke_width=2.5),
                     Line(p + [-0.07, -0.09, 0], p + [0.07, -0.03, 0], stroke_color=color, stroke_width=2.5))
        off.add(VGroup(tri, lab, brk))
    return {"line": line, "marks": marks, "off": off}


SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def pow10(exp):
    return f"10{str(int(exp)).translate(SUP)}"


def residual_bound(meta):
    """Final-screen wording approved by the user: max|e| < tol (checked, not assumed)."""
    res, tol = meta["final_residual_nm"], meta["tol_nm"]
    assert res < tol, "final residual must be strictly below the displayed bound"
    return f"max|e| < {pow10(np.log10(tol))} nm"


def sci(v, digits=1):
    """1.0×10⁻¹² style (Pango text, no TeX)."""
    if v == 0:
        return "0"
    mant, exp = f"{v:.{digits}e}".split("e")  # rounding handled by the formatter (9.96e-13 -> 1.0e-12)
    sup = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    return f"{mant}×10{str(int(exp)).translate(sup)}"


def group(s):
    return VGroup(s["line"], s["marks"], s["off"])


def envelope_valid_from(x_um, u, pred, tol=0.05, step=0.1):
    """Smallest distance beyond which the dominant pair matches the solved profile to `tol`
    of the envelope. Inside it several modes overlap and no envelope is drawn."""
    env = pred["A0_nm"] * np.exp(-pred["gamma_per_um"] * x_um)
    dom = env * np.cos(2 * np.pi * x_um / pred["L_um"] + pred["phi"])
    err = np.abs(u - dom) / env
    for xs in np.arange(step, x_um[-1], step):
        if err[x_um >= xs - 1e-9].max() <= tol:
            return float(np.round(xs, 6))
    raise ValueError("dominant-mode approximation never within tolerance")


def envelope(panel: Panel, pred, x_from, color=MUTED, samples=120):
    """+/- A0 exp(-gamma s) from the characteristic-root prediction (labelled approximation)."""
    xs = np.linspace(x_from, panel.xr[1], samples)
    g = VGroup()
    for sgn in (1, -1):
        ys = np.clip(sgn * pred["A0_nm"] * np.exp(-pred["gamma_per_um"] * xs), *panel.yr)
        line = VMobject(stroke_color=color, stroke_width=2).set_points_as_corners([panel.c2p(a, b) for a, b in zip(xs, ys)])
        g.add(DashedVMobject(line, num_dashes=40, dashed_ratio=0.5))
    return g


def card(title, lines, width, accent=INK, tag=None, body_size=SMALL):
    """Rounded card with a bold title and short lines (observation / held-fixed cards)."""
    head = T(title, LABEL, accent, weight="BOLD")
    body = VGroup(*[T(l, body_size, INK) for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    content = VGroup(head, body).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
    if tag is not None:
        content = VGroup(tag, content).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
    box = RoundedRectangle(corner_radius=0.12, width=width, height=content.height + 0.5, stroke_color=accent,
                           stroke_width=2, fill_color="#FFFFFF", fill_opacity=1)
    content.move_to(box).align_to(box, LEFT).shift(0.25 * RIGHT)
    return VGroup(box, content)


def pill(s, color=MUTED, size=SMALL):
    txt = T(s, size, color)
    box = RoundedRectangle(corner_radius=0.08, width=txt.width + 0.3, height=txt.height + 0.18, stroke_color=color,
                           stroke_width=1.5)
    return VGroup(box, txt.move_to(box))
