"""Primitives de dessin Cairo partagées (couleurs, dégradés, texte, easing)."""
import math

import cairo

from config import FONT_DISPLAY, FONT_TEXT, PALETTE


def hexc(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    n = max(len(c1), len(c2))
    c1 = tuple(c1) + (1.0,) * (n - len(c1))
    c2 = tuple(c2) + (1.0,) * (n - len(c2))
    return tuple(a + (b - a) * t for a, b in zip(c1, c2))


def P(name, a=1.0):
    return PALETTE[name] + (a,)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp(t)
    return 3 * t * t - 2 * t * t * t


def ease_back(t, s=1.70158):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def prog(t, a, b):
    """progression linéaire 0..1 de t entre a et b"""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def noise1(x, seed=0):
    """bruit lisse déterministe (somme de sinus) dans [-1, 1]"""
    s = seed * 1.618
    return (math.sin(x * 1.0 + s) * 0.5 + math.sin(x * 2.31 + s * 2.1) * 0.3
            + math.sin(x * 4.73 + s * 3.7) * 0.2)


def set_src(ctx, c):
    if len(c) == 4:
        ctx.set_source_rgba(*c)
    else:
        ctx.set_source_rgb(*c)


def lin(x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for off, c in stops:
        if len(c) == 4:
            g.add_color_stop_rgba(off, *c)
        else:
            g.add_color_stop_rgb(off, *c)
    return g


def rad(cx, cy, r0, r1, stops, cx1=None, cy1=None):
    g = cairo.RadialGradient(cx, cy, r0, cx if cx1 is None else cx1, cy if cy1 is None else cy1, r1)
    for off, c in stops:
        if len(c) == 4:
            g.add_color_stop_rgba(off, *c)
        else:
            g.add_color_stop_rgb(off, *c)
    return g


def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def ellipse(ctx, cx, cy, rx, ry):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def smooth_path(ctx, pts, closed=True, tension=0.5):
    """Catmull-Rom → Bézier à travers une liste de points."""
    n = len(pts)
    if n < 3:
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        return
    ctx.move_to(*pts[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if closed or i > 0 else pts[0]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if closed or i + 2 < n else pts[-1]
        c1 = (p1[0] + (p2[0] - p0[0]) * tension / 3, p1[1] + (p2[1] - p0[1]) * tension / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * tension / 3, p2[1] - (p3[1] - p1[1]) * tension / 3)
        ctx.curve_to(*c1, *c2, *p2)
    if closed:
        ctx.close_path()


def font(ctx, size, weight="bold", family=None):
    fam = family or FONT_DISPLAY
    if weight == "black":
        fam = f"{fam} Black"
        w = cairo.FONT_WEIGHT_NORMAL
    elif weight == "extrabold":
        fam = f"{fam} ExtraBold"
        w = cairo.FONT_WEIGHT_NORMAL
    elif weight == "semibold":
        fam = f"{fam} SemiBold"
        w = cairo.FONT_WEIGHT_NORMAL
    elif weight == "medium":
        fam = f"{fam} Medium"
        w = cairo.FONT_WEIGHT_NORMAL
    elif weight == "light":
        fam = f"{fam} Light"
        w = cairo.FONT_WEIGHT_NORMAL
    elif weight == "bold":
        w = cairo.FONT_WEIGHT_BOLD
    else:
        w = cairo.FONT_WEIGHT_NORMAL
    ctx.select_font_face(fam, cairo.FONT_SLANT_NORMAL, w)
    ctx.set_font_size(size)


def text(ctx, s, x, y, size, color, weight="bold", align="left", family=None, tracking=0.0, alpha=1.0):
    """Texte sur une ligne. align : left|center|right. y = ligne de base. Retourne la largeur."""
    font(ctx, size, weight, family)
    if tracking:
        widths = [ctx.text_extents(ch).x_advance + tracking * size for ch in s]
        total = sum(widths) - tracking * size
    else:
        total = ctx.text_extents(s).x_advance
    if align == "center":
        x -= total / 2
    elif align == "right":
        x -= total
    c = tuple(color)
    c = c[:3] + ((c[3] if len(c) == 4 else 1.0) * alpha,)
    ctx.set_source_rgba(*c)
    if tracking:
        cx = x
        for ch, wd in zip(s, widths):
            ctx.move_to(cx, y)
            ctx.show_text(ch)
            cx += wd
    else:
        ctx.move_to(x, y)
        ctx.show_text(s)
    ctx.new_path()          # évite qu'un arc() suivant ne parte du point courant du texte
    return total


def text_width(ctx, s, size, weight="bold", family=None, tracking=0.0):
    font(ctx, size, weight, family)
    if tracking:
        return sum(ctx.text_extents(ch).x_advance + tracking * size for ch in s) - tracking * size
    return ctx.text_extents(s).x_advance


def wrap(ctx, s, size, max_w, weight="medium", family=None):
    font(ctx, size, weight, family or FONT_TEXT)
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if ctx.text_extents(trial).x_advance <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fmt_int(n):
    return f"{int(n):,}".replace(",", " ")
