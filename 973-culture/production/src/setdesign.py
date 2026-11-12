"""Étape 5 — Décor : plateau éphémère 973 CULTURE, Place des Palmistes (Cayenne).

Évocation stylisée et non documentaire (voir docs/03-direction-artistique/decor.md) :
- palmiers royaux (« palmistes ») en rangées, façades créoles à étage avec balcons,
  évocation lointaine du portique du monument Félix Éboué, lampadaires ;
- les gradins sont un PLATEAU ÉPHÉMÈRE installé par la production (aucune source ne
  confirme de gradins permanents sur la place) ;
- lumière : fin d'après-midi dorée → nuit, au fil de l'épisode (paramètre tod 0→1).
Aucune foule, aucun événement réel n'est représenté.
"""
import math
import random

import cairo

from draw import ellipse, hexc, lin, mix, rad, rrect, set_src, smooth_path, text

WORLD_W, WORLD_H = 1920, 1080
SEAT_Y = 700
CHAR_SCALE = 0.66
CHAR_X = {"K": 735, "M": 1185}


def sky_colors(tod):
    top = mix(hexc("#2F5E93"), hexc("#070E22"), tod)
    mid = mix(hexc("#E99A5B"), hexc("#26305A"), tod ** 0.8)
    hor = mix(hexc("#FFD486"), hexc("#7A4B66"), tod ** 0.9)
    return top, mid, hor


# ------------------------------------------------------------------ static geometry
_rnd = random.Random(973)


def _gen_buildings():
    b = []
    x = -200
    cols = ["#E8C77A", "#D98E5F", "#9FC2A6", "#E6DCC8", "#7FA7C9", "#E7A9A0", "#F0D9A8", "#B9D4B5"]
    while x < WORLD_W + 200:
        w = _rnd.randint(150, 260)
        floors = 2 if _rnd.random() < 0.75 else 3
        b.append({"x": x, "w": w, "floors": floors, "col": hexc(_rnd.choice(cols)),
                  "roof": hexc(_rnd.choice(["#8C3B2B", "#A2492F", "#6E2F25", "#5E6A70"])),
                  "seed": _rnd.randint(0, 9999)})
        x += w + _rnd.randint(4, 30)
    return b


def _gen_palms():
    palms = []
    # rangée lointaine
    for i in range(16):
        palms.append({"x": -60 + i * 132 + _rnd.uniform(-30, 30), "base": 560, "h": _rnd.uniform(250, 310),
                      "s": 0.55, "depth": 0.35, "seed": _rnd.random() * 10})
    # rangée médiane
    for i in range(8):
        palms.append({"x": -80 + i * 300 + _rnd.uniform(-40, 40), "base": 610, "h": _rnd.uniform(420, 500),
                      "s": 0.85, "depth": 0.55, "seed": _rnd.random() * 10})
    return palms


BUILDINGS = _gen_buildings()
PALMS = _gen_palms()


# ------------------------------------------------------------------ layers
def draw_sky(ctx, tod, t):
    top, mid, hor = sky_colors(tod)
    ctx.rectangle(-400, -400, WORLD_W + 800, WORLD_H + 800)
    ctx.set_source(lin(0, -100, 0, 520, [(0, top), (0.62, mid), (1, hor)]))
    ctx.fill()
    # soleil couchant (s'efface avec la nuit)
    sun_a = max(0.0, 1 - tod * 2.2)
    if sun_a > 0:
        sy = 430 + tod * 260
        ctx.set_source(rad(1450, sy, 10, 420, [(0, (1, 0.9, 0.6, 0.55 * sun_a)), (1, (1, 0.7, 0.4, 0))]))
        ctx.paint()
        ellipse(ctx, 1450, sy, 46, 46)
        ctx.set_source_rgba(1, 0.93, 0.72, 0.95 * sun_a)
        ctx.fill()
    # étoiles
    if tod > 0.45:
        r = random.Random(5)
        for i in range(90):
            x, y = r.uniform(-200, WORLD_W + 200), r.uniform(-200, 300)
            tw = 0.5 + 0.5 * math.sin(t * r.uniform(1, 3) + i)
            ctx.arc(x, y, r.uniform(0.6, 1.6), 0, 6.3)
            ctx.set_source_rgba(1, 1, 1, (tod - 0.45) * 1.5 * tw * 0.8)
            ctx.fill()
    # nuages étirés
    r = random.Random(9)
    for i in range(7):
        cx = (r.uniform(-200, WORLD_W + 200) + t * 4 * (1 + i % 3)) % (WORLD_W + 600) - 300
        cy = r.uniform(80, 330)
        lit = mix(hexc("#FFC889"), hexc("#3A3F66"), tod)
        ellipse(ctx, cx, cy, r.uniform(160, 340), r.uniform(10, 22))
        set_src(ctx, lit[:3] + (0.35,))
        ctx.fill()


def draw_skyline(ctx, tod, t):
    haze = mix(hexc("#F3C38A"), hexc("#1A2142"), tod)
    for bd in BUILDINGS:
        x, w = bd["x"], bd["w"]
        fh = 62
        h = bd["floors"] * fh + 14
        base = 560
        y = base - h
        col = mix(bd["col"], haze, 0.35 + tod * 0.45)
        ctx.rectangle(x, y, w, h)
        set_src(ctx, col)
        ctx.fill()
        # toit à quatre pans
        ctx.move_to(x - 10, y + 2)
        ctx.line_to(x + 26, y - 36)
        ctx.line_to(x + w - 26, y - 36)
        ctx.line_to(x + w + 10, y + 2)
        ctx.close_path()
        set_src(ctx, mix(bd["roof"], haze, 0.35 + tod * 0.45))
        ctx.fill()
        # balcon filant à l'étage
        ctx.rectangle(x - 4, y + fh - 4, w + 8, 5)
        set_src(ctx, mix(hexc("#3B2A22"), haze, 0.4 + tod * 0.4))
        ctx.fill()
        rr = random.Random(bd["seed"])
        for f in range(bd["floors"]):
            nwin = max(2, int(w / 52))
            for k in range(nwin):
                wx = x + 16 + k * (w - 32) / nwin
                wy = y + 14 + f * fh
                ww = (w - 32) / nwin - 12
                lit = rr.random() < 0.55
                on = max(0.0, min(1.0, (tod - 0.3 - rr.random() * 0.3) * 3)) if lit else 0
                c = mix(mix(hexc("#5A4636"), haze, 0.3), hexc("#FFCF7A"), on)
                ctx.rectangle(wx, wy, ww, fh - 26)
                set_src(ctx, c)
                ctx.fill()
                # persiennes
                ctx.rectangle(wx - 5, wy, 4, fh - 26)
                ctx.rectangle(wx + ww + 1, wy, 4, fh - 26)
                set_src(ctx, mix(hexc("#2E6B55"), haze, 0.45 + tod * 0.3))
                ctx.fill()
    # évocation lointaine du monument (portique + statue) — stylisée
    mx, my = 470, 560
    stone = mix(hexc("#E9E1D2"), hexc("#3A3F5C"), tod * 0.85)
    ctx.rectangle(mx - 120, my - 120, 240, 120)
    set_src(ctx, stone)
    ctx.fill()
    ctx.rectangle(mx - 40, my - 104, 80, 104)
    set_src(ctx, mix(stone, (0, 0, 0, 1), 0.25))
    ctx.fill()
    # silhouette en pied
    ctx.rectangle(mx - 9, my - 92, 18, 70)
    ellipse(ctx, mx, my - 100, 9, 10)
    set_src(ctx, mix(hexc("#5D6A66"), hexc("#20253A"), tod))
    ctx.fill()
    # voile atmosphérique
    ctx.rectangle(-400, 300, WORLD_W + 800, 280)
    ctx.set_source(lin(0, 300, 0, 580, [(0, haze[:3] + (0.0,)), (1, haze[:3] + (0.45,))]))
    ctx.fill()


def draw_palm(ctx, p, tod, t, cam_depth_alpha=1.0):
    x, base, h, s = p["x"], p["base"], p["h"], p["s"]
    sway = math.sin(t * 0.7 + p["seed"]) * 0.05 + math.sin(t * 1.9 + p["seed"] * 2) * 0.015
    haze = mix(hexc("#E8B57E"), hexc("#141A33"), tod)
    dim = 0.55 if p["depth"] < 0.5 else 0.25
    trunk = mix(mix(hexc("#BDB5A8"), haze, dim), (0, 0, 0, 1), tod * 0.5)
    leaf = mix(mix(hexc("#2F6B3A"), haze, dim), hexc("#0A1A16"), tod * 0.6)
    top_x = x + sway * h * 0.6
    top_y = base - h
    # tronc lisse légèrement renflé
    ctx.move_to(x - 11 * s, base)
    ctx.curve_to(x - 14 * s, base - h * 0.4, top_x - 7 * s, top_y + h * 0.3, top_x - 6 * s, top_y)
    ctx.line_to(top_x + 6 * s, top_y)
    ctx.curve_to(top_x + 7 * s, top_y + h * 0.3, x + 14 * s, base - h * 0.4, x + 11 * s, base)
    ctx.close_path()
    set_src(ctx, trunk)
    ctx.fill()
    # manchon vert (crownshaft)
    ctx.rectangle(top_x - 7 * s, top_y - 38 * s, 14 * s, 40 * s)
    set_src(ctx, mix(leaf, hexc("#6E9A4E"), 0.25))
    ctx.fill()
    cx, cy = top_x, top_y - 38 * s
    n = 13
    for i in range(n):
        a = -math.pi + (i + 0.5) / n * math.pi + math.sin(t * 1.1 + i + p["seed"]) * 0.05 + sway
        L = (120 + 40 * math.sin(i * 2.3 + p["seed"])) * s
        droop = 0.55 + 0.35 * abs(math.cos(a))
        ex = cx + math.cos(a) * L
        ey = cy + math.sin(a) * L * 0.55 + L * droop * 0.55
        mx_ = cx + math.cos(a) * L * 0.55
        my_ = cy + math.sin(a) * L * 0.55 - 6 * s
        # palme : nervure + folioles
        ctx.move_to(cx, cy)
        ctx.curve_to(mx_, my_, mx_, my_, ex, ey)
        ctx.set_line_width(2.4 * s)
        set_src(ctx, leaf)
        ctx.stroke()
        steps = 9
        for k in range(1, steps):
            u = k / steps
            px = (1 - u) ** 2 * cx + 2 * (1 - u) * u * mx_ + u * u * ex
            py = (1 - u) ** 2 * cy + 2 * (1 - u) * u * my_ + u * u * ey
            ll = (1 - abs(u - 0.4)) * 30 * s
            for sg in (-1, 1):
                ctx.move_to(px, py)
                ctx.line_to(px + sg * ll * 0.35, py + ll)
            ctx.set_line_width(3.2 * s)
            ctx.stroke()


def draw_ground(ctx, tod, t):
    grass = mix(hexc("#5E8C46"), hexc("#0E1D18"), tod * 0.85)
    path = mix(hexc("#D9C3A0"), hexc("#2B2A33"), tod * 0.8)
    ctx.rectangle(-400, 555, WORLD_W + 800, 600)
    ctx.set_source(lin(0, 555, 0, 1080, [(0, mix(grass, hexc("#E8B57E"), 0.25 * (1 - tod))), (1, grass)]))
    ctx.fill()
    # allée en perspective
    ctx.move_to(860, 560)
    ctx.line_to(1060, 560)
    ctx.line_to(1700, 1080)
    ctx.line_to(220, 1080)
    ctx.close_path()
    set_src(ctx, path)
    ctx.fill()
    # lampadaires
    for lx, ly, sc in ((300, 600, 0.9), (1640, 600, 0.9), (640, 575, 0.55), (1290, 575, 0.55)):
        ctx.rectangle(lx - 3 * sc, ly - 190 * sc, 6 * sc, 190 * sc)
        ctx.set_source_rgba(0.1, 0.12, 0.13, 1)
        ctx.fill()
        on = max(0.0, min(1.0, (tod - 0.25) * 3))
        ellipse(ctx, lx, ly - 196 * sc, 14 * sc, 9 * sc)
        set_src(ctx, mix(hexc("#5B6266"), hexc("#FFE2A0"), on))
        ctx.fill()
        if on > 0:
            ctx.set_source(rad(lx, ly - 196 * sc, 2, 160 * sc, [(0, (1, 0.85, 0.55, 0.45 * on)), (1, (1, 0.8, 0.5, 0))]))
            ctx.arc(lx, ly - 196 * sc, 160 * sc, 0, 6.3)
            ctx.fill()


def draw_stage(ctx, tod, t):
    """Plateau : gradins en bois, guirlande, enseigne, plantes."""
    wood = hexc("#B07A4A")
    wood_d = hexc("#7C5232")
    wood_l = hexc("#D39A63")
    night = tod
    # guirlande lumineuse (guinguette)
    poles = [(380, 150), (1540, 150)]
    for px, py in poles:
        ctx.rectangle(px - 5, py, 10, 520)
        ctx.set_source_rgba(0.08, 0.08, 0.09, 1)
        ctx.fill()
    on = 0.35 + 0.65 * min(1.0, tod * 1.6)
    for k in range(2):
        y0 = 160 + k * 30
        sag = 70 - k * 18
        ctx.move_to(380, y0)
        ctx.curve_to(760, y0 + sag, 1160, y0 + sag, 1540, y0)
        ctx.set_line_width(2)
        ctx.set_source_rgba(0.05, 0.05, 0.05, 0.9)
        ctx.stroke()
        nb = 16
        for i in range(1, nb):
            u = i / nb
            bx = (1 - u) ** 3 * 380 + 3 * (1 - u) ** 2 * u * 760 + 3 * (1 - u) * u * u * 1160 + u ** 3 * 1540
            by = (1 - u) ** 3 * y0 + 3 * (1 - u) ** 2 * u * (y0 + sag) + 3 * (1 - u) * u * u * (y0 + sag) + u ** 3 * y0 + 10
            fl = 0.9 + 0.1 * math.sin(t * 7 + i * 3.1 + k)
            ctx.set_source(rad(bx, by, 1, 34, [(0, (1, 0.82, 0.5, 0.55 * on * fl)), (1, (1, 0.7, 0.4, 0))]))
            ctx.arc(bx, by, 34, 0, 6.3)
            ctx.fill()
            ellipse(ctx, bx, by, 5, 7)
            ctx.set_source_rgba(1, 0.9, 0.65, 0.6 + 0.4 * on)
            ctx.fill()
    # panneau arrière + enseigne néon
    rrect(ctx, 850, 196, 220, 96, 14)
    ctx.set_source_rgba(0.05, 0.07, 0.07, 0.92)
    ctx.fill()
    glow = 0.5 + 0.5 * min(1.0, tod * 1.5)
    for blur, a in ((10, 0.18), (5, 0.3), (0, 1.0)):
        ctx.save()
        if blur:
            ctx.set_line_width(blur)
        text(ctx, "973", 960, 252, 50, (0.98, 0.75, 0.23, a * glow if blur else 0.95), "black", "center")
        text(ctx, "CULTURE", 960, 280, 19, (0.95, 0.95, 0.92, a * glow if blur else 0.95), "bold", "center", tracking=0.32)
        ctx.restore()
    ctx.set_source(rad(960, 244, 10, 260, [(0, (0.98, 0.75, 0.23, 0.18 * glow)), (1, (0.98, 0.75, 0.23, 0))]))
    ctx.arc(960, 244, 260, 0, 6.3)
    ctx.fill()
    # gradins (3 marches)
    steps = [(SEAT_Y - 150, 470, 1450), (SEAT_Y - 10, 420, 1500), (SEAT_Y + 150, 370, 1550)]
    for i, (y, x0, x1) in enumerate(steps):
        # contremarche
        ctx.rectangle(x0, y, x1 - x0, 150)
        ctx.set_source(lin(0, y, 0, y + 150, [(0, wood_d), (1, mix(wood_d, (0, 0, 0, 1), 0.35))]))
        ctx.fill()
        # assise (planche) avec lames
        ctx.rectangle(x0 - 10, y - 18, x1 - x0 + 20, 26)
        ctx.set_source(lin(0, y - 18, 0, y + 8, [(0, wood_l), (1, wood)]))
        ctx.fill()
        ctx.set_line_width(1.2)
        ctx.set_source_rgba(0.3, 0.18, 0.1, 0.5)
        for k in range(int((x1 - x0) / 120)):
            xx = x0 + 60 + k * 120
            ctx.move_to(xx, y - 18)
            ctx.line_to(xx, y + 8)
        ctx.stroke()
        # lumière d'ambiance LED sous la marche (s'allume la nuit)
        led = min(1.0, tod * 1.4)
        ctx.rectangle(x0, y + 8, x1 - x0, 6)
        ctx.set_source_rgba(0.98, 0.75, 0.23, 0.25 + 0.6 * led)
        ctx.fill()
        ctx.rectangle(x0, y + 14, x1 - x0, 60)
        ctx.set_source(lin(0, y + 14, 0, y + 74, [(0, (0.98, 0.75, 0.23, 0.25 * led)), (1, (0.98, 0.75, 0.23, 0))]))
        ctx.fill()
    # coussins sur l'assise
    for cx, col in ((CHAR_X["K"], hexc("#F9BF3B")), (CHAR_X["M"], hexc("#177A54"))):
        from draw import ellipse as _el
        ctx.set_source(rad(cx, SEAT_Y + 4, 10, 120, [(0, (0, 0, 0, 0.35)), (1, (0, 0, 0, 0))]))
        _el(ctx, cx, SEAT_Y + 4, 120, 26)
        ctx.fill()
        rrect(ctx, cx - 80, SEAT_Y - 30, 160, 26, 12)
        set_src(ctx, col)
        ctx.fill()
    # plantes en pot (héliconias / oiseaux de paradis stylisés)
    for px, flip in ((360, 1), (1560, -1)):
        draw_plant(ctx, px, SEAT_Y + 160, flip, tod, t)


def draw_plant(ctx, x, y, flip, tod, t):
    rrect(ctx, x - 55, y - 90, 110, 100, 12)
    ctx.set_source(lin(x - 55, 0, x + 55, 0, [(0, hexc("#E7E1D5")), (1, hexc("#A79F92"))]))
    ctx.fill()
    leaf = mix(hexc("#2E7D4A"), hexc("#0F2A20"), tod * 0.6)
    for i in range(7):
        a = -math.pi / 2 + (i - 3) * 0.32 + math.sin(t * 0.9 + i) * 0.03
        L = 260 + (i % 3) * 40
        ex, ey = x + math.cos(a) * L * 0.5 * flip, y - 90 + math.sin(a) * L
        ctx.save()
        ctx.translate(x, y - 90)
        ctx.rotate(a + math.pi / 2)
        smooth_path(ctx, [(0, 0), (-26, -L * 0.45), (0, -L), (26, -L * 0.45)], closed=True, tension=0.6)
        ctx.restore()
        set_src(ctx, leaf if i % 2 else mix(leaf, (0.6, 0.9, 0.5, 1), 0.12))
        ctx.fill()
    # fleurs d'héliconia (rouge/jaune)
    for k in range(3):
        fx = x + flip * (k - 1) * 40
        fy = y - 260 - k * 30
        for j in range(4):
            ctx.save()
            ctx.translate(fx, fy + j * 18)
            ctx.rotate(flip * (0.5 if j % 2 else -0.5))
            ctx.move_to(0, 0)
            ctx.line_to(flip * 34, -6)
            ctx.line_to(0, 10)
            ctx.close_path()
            set_src(ctx, hexc("#D93434") if j % 2 else hexc("#F2A23A"))
            ctx.fill()
            ctx.restore()


def draw_foreground(ctx, tod, t, strength):
    """feuilles de palmier floues en amorce (plans serrés)"""
    if strength <= 0:
        return
    leaf = mix(hexc("#123C26"), hexc("#050C0A"), tod)
    for (x, y, a, L) in ((-60, 980, -0.6, 520), (1990, 1010, -2.6, 560), (1960, -40, 2.4, 420)):
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(a + math.sin(t * 0.8 + x) * 0.03)
        for k in range(10):
            ctx.save()
            ctx.translate(k * L / 10, 0)
            ctx.rotate(0.9)
            ellipse(ctx, 0, -50, 16, 70)
            ctx.restore()
            ctx.save()
            ctx.translate(k * L / 10, 0)
            ctx.rotate(-0.9 + math.pi)
            ellipse(ctx, 0, -50, 16, 70)
            ctx.restore()
        ctx.restore()
        set_src(ctx, leaf[:3] + (0.85 * strength,))
        ctx.fill()
