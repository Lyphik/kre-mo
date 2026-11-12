"""Étape 4 — Les deux présentateurs de 973 CULTURE : KENZO et MAËVA.

Personnages vectoriels paramétriques : un seul modèle par personnage, réutilisé dans
tous les plans → visages, proportions, coiffures et tenues strictement identiques.
Repère local : origine = centre de l'assise (bassin), y vers le bas, 1 unité ≈ 1 px en
plan serré de référence. Fiche de design : docs/03-direction-artistique/bible-personnages.md
"""
import math

from draw import ellipse, hexc, lin, mix, rad, smooth_path, set_src

# ---------------------------------------------------------------- design sheets
DESIGN = {
    "K": {
        "skin": hexc("#5C3B2A"), "skin_hi": hexc("#7B5139"), "skin_sh": hexc("#3E271B"),
        "lip": hexc("#4A2A20"), "lip_hi": hexc("#6A3E31"),
        "iris": hexc("#2B170E"), "brow": hexc("#140D0A"), "hair": hexc("#141010"),
        "hair_hi": hexc("#2C2420"), "beard": hexc("#18110E"),
        "shoulder": 132, "hip": 96, "neck": 34, "head_w": 78, "head_h": 98, "jaw": 0.88,
        "top": hexc("#F2EEE6"),          # tee-shirt blanc cassé
        "jacket": hexc("#0E4A35"), "jacket_hi": hexc("#1C6B4D"), "jacket_sh": hexc("#08301F"),
        "pants": hexc("#1B1F22"), "pants_hi": hexc("#2E3438"),
        "shoe": hexc("#F4F2EC"), "shoe_acc": hexc("#177A54"), "sole": hexc("#C79A5B"),
        "chain": hexc("#E9B949"),
    },
    "M": {
        "skin": hexc("#C68A5E"), "skin_hi": hexc("#DCA477"), "skin_sh": hexc("#A26C45"),
        "lip": hexc("#9C4B3E"), "lip_hi": hexc("#BD6A58"),
        "iris": hexc("#4A2C17"), "brow": hexc("#3A2216"), "hair": hexc("#5A3020"),
        "hair_hi": hexc("#A2643A"), "hair_sh": hexc("#3A1E14"),
        "shoulder": 112, "hip": 100, "neck": 27, "head_w": 72, "head_h": 94, "jaw": 0.74,
        "top": hexc("#F1D9A0"),          # top doré pâle
        "jacket": hexc("#B5332E"), "jacket_hi": hexc("#D2493F"), "jacket_sh": hexc("#7E1F1C"),
        "pants": hexc("#16181B"), "pants_hi": hexc("#2A2D31"),
        "shoe": hexc("#F6F4EF"), "shoe_acc": hexc("#F9BF3B"), "sole": hexc("#EDEAE3"),
        "chain": hexc("#F1C150"),
    },
}

NECK_Y = -372
HEAD_CY = -462


def default_state():
    return {"open": 0.0, "shape": "closed", "blink": 0.0, "gaze_x": 0.0, "gaze_y": 0.0,
            "yaw": 0.0, "tilt": 0.0, "nod": 0.0, "brow": 0.0, "smile": 0.25,
            "arm_l": 0.0, "arm_r": 0.0, "arm_phase": 0.0, "breath": 0.0, "light": 0.0,
            "lean": 0.0}


# ---------------------------------------------------------------- helpers
def _limb(ctx, p0, p1, w0, w1, fill):
    """segment de membre arrondi (trapèze à bouts ronds)"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    ctx.move_to(p0[0] + nx * w0, p0[1] + ny * w0)
    ctx.line_to(p1[0] + nx * w1, p1[1] + ny * w1)
    ang = math.atan2(dy, dx)
    ctx.arc(p1[0], p1[1], w1, ang - math.pi / 2, ang + math.pi / 2)
    ctx.line_to(p0[0] - nx * w0, p0[1] - ny * w0)
    ctx.arc(p0[0], p0[1], w0, ang + math.pi / 2, ang + 3 * math.pi / 2)
    ctx.close_path()
    set_src(ctx, fill) if not hasattr(fill, "add_color_stop_rgba") else ctx.set_source(fill)
    ctx.fill()


def _shade(c, k):
    return mix(c, (0, 0, 0, 1), k)


def _light(c, k):
    return mix(c, (1, 0.93, 0.8, 1), k)


# ---------------------------------------------------------------- body
def draw_legs(ctx, d, st):
    hip = d["hip"]
    pants = lin(-hip, 0, hip, 0, [(0, _light(d["pants"], 0.10)), (0.5, d["pants"]), (1, _shade(d["pants"], 0.35))])
    for side in (-1, 1):
        kx = side * (hip * 0.62)
        # cuisse (raccourcie, vers la caméra)
        _limb(ctx, (side * hip * 0.48, 4), (kx, 70), 52, 50, pants)
        # tibia (jambe droite, pantalon droit)
        ax = kx + side * 4
        _limb(ctx, (kx, 74), (ax, 268), 44, 38, pants)
        # chaussure
        ctx.save()
        ctx.translate(ax + side * 4, 300)
        ctx.scale(1.12, 1.12)
        ellipse(ctx, 0, 14, 50, 20)
        set_src(ctx, d["sole"])
        ctx.fill()
        smooth_path(ctx, [(-44, 10), (-38, -22), (-10, -36), (22, -34), (44, -14), (46, 10)], closed=True)
        ctx.set_source(lin(0, -36, 0, 12, [(0, _light(d["shoe"], 0.05)), (1, _shade(d["shoe"], 0.18))]))
        ctx.fill()
        # virgule d'accent (design original, pas de marque)
        smooth_path(ctx, [(-30, 0), (-6, -10), (30, -20), (-4, -2)], closed=True)
        set_src(ctx, d["shoe_acc"])
        ctx.fill()
        ctx.restore()


def draw_torso(ctx, d, st, who):
    sh, hip = d["shoulder"], d["hip"]
    b = st["breath"] * 3
    top_y = NECK_Y + 14 - b
    # silhouette du buste
    if who == "K":
        pts = [(-sh, top_y + 30), (-sh * 0.98, top_y + 120), (-hip * 1.05, -60), (-hip * 1.0, 6),
               (hip * 1.0, 6), (hip * 1.05, -60), (sh * 0.98, top_y + 120), (sh, top_y + 30),
               (sh * 0.55, top_y), (-sh * 0.55, top_y)]
    else:
        pts = [(-sh, top_y + 30), (-sh * 0.86, top_y + 140), (-hip * 0.80, -110), (-hip * 1.02, -10),
               (hip * 1.02, -10), (hip * 0.80, -110), (sh * 0.86, top_y + 140), (sh, top_y + 30),
               (sh * 0.55, top_y), (-sh * 0.55, top_y)]
    # tee / top (dessous)
    smooth_path(ctx, pts, closed=True, tension=0.35)
    ctx.set_source(lin(0, top_y, 0, 0, [(0, _light(d["top"], 0.05)), (1, _shade(d["top"], 0.22))]))
    ctx.fill()
    # veste ouverte : deux pans
    jac = lin(-sh, 0, sh, 0, [(0, d["jacket_hi"]), (0.45, d["jacket"]), (1, d["jacket_sh"])])
    open_w = 34 if who == "K" else 42
    for side in (-1, 1):
        ctx.save()
        if side == 1:
            ctx.scale(-1, 1)
        smooth_path(ctx, [(-sh, top_y + 30), (-sh * 0.55, top_y - 2), (-open_w * 0.7, top_y + 6),
                          (-open_w, top_y + 90), (-open_w * 1.2, -40), (-open_w * 1.3, 8),
                          (-hip * (1.06 if who == 'K' else 0.98), 8), (-hip * 1.08, -60),
                          (-sh * (0.99 if who == 'K' else 0.88), top_y + 130)], closed=True, tension=0.3)
        ctx.set_source(jac if side == -1 else lin(-sh, 0, sh, 0, [(0, d["jacket_sh"]), (0.55, d["jacket"]), (1, d["jacket_hi"])]))
        ctx.fill()
        # revers / col
        ctx.move_to(-sh * 0.55, top_y - 2)
        ctx.line_to(-open_w * 0.6, top_y + 4)
        ctx.line_to(-open_w * 1.05, top_y + 96)
        ctx.line_to(-open_w * 1.9, top_y + 40)
        ctx.close_path()
        set_src(ctx, _shade(d["jacket"], 0.25))
        ctx.fill()
        # couture / pli
        ctx.move_to(-sh * 0.70, top_y + 60)
        ctx.curve_to(-sh * 0.66, top_y + 160, -sh * 0.60, -120, -sh * 0.62, -20)
        ctx.set_line_width(2.2)
        set_src(ctx, _shade(d["jacket"], 0.35)[:3] + (0.55,))
        ctx.stroke()
        ctx.restore()
    if who == "K":
        # poche poitrine overshirt
        for side in (-1, 1):
            ctx.save()
            ctx.translate(side * sh * 0.52, top_y + 92)
            ctx.rectangle(-22, -16, 44, 40)
            set_src(ctx, _shade(d["jacket"], 0.12))
            ctx.fill()
            ctx.rectangle(-24, -18, 48, 12)
            set_src(ctx, _light(d["jacket"], 0.08))
            ctx.fill()
            ctx.restore()
    # chaîne discrète
    ctx.set_line_width(2.4 if who == "K" else 1.8)
    set_src(ctx, d["chain"])
    ctx.move_to(-d["neck"] * 1.2, top_y + 2)
    ctx.curve_to(-d["neck"] * 0.9, top_y + (64 if who == "K" else 46), d["neck"] * 0.9,
                 top_y + (64 if who == "K" else 46), d["neck"] * 1.2, top_y + 2)
    ctx.stroke()
    if who == "M":
        ellipse(ctx, 0, top_y + 40, 4.5, 5.5)
        ctx.fill()


def arm_points(d, st, side):
    """Position épaule-coude-main ; side=-1 gauche écran, 1 droite écran."""
    sh = d["shoulder"]
    s = (side * (sh - 20), NECK_Y + 64)
    g = st["arm_l"] if side == -1 else st["arm_r"]
    ph = st["arm_phase"]
    # pose de repos : avant-bras posé sur la cuisse
    e_rest = (side * (sh - 8), -138)
    h_rest = (side * 66, 30)
    # pose de geste : main levée devant le buste, oscillation
    osc = math.sin(ph * 2.0 + (0 if side == 1 else 1.7))
    e_g = (side * (sh + 6), -136 + osc * 6)
    h_g = (side * (60 + osc * 22), -250 + math.sin(ph * 3.1) * 18)
    e = (e_rest[0] + (e_g[0] - e_rest[0]) * g, e_rest[1] + (e_g[1] - e_rest[1]) * g)
    h = (h_rest[0] + (h_g[0] - h_rest[0]) * g, h_rest[1] + (h_g[1] - h_rest[1]) * g)
    return s, e, h, g


def draw_arm(ctx, d, st, side, who):
    s, e, h, g = arm_points(d, st, side)
    jac = lin(s[0] - 40, 0, s[0] + 40, 0, [(0, d["jacket_hi"]), (1, d["jacket_sh"])])
    uw = 34 if who == "K" else 27
    _limb(ctx, s, e, uw, uw - 2, jac)
    # pli du coude
    ctx.arc(e[0], e[1], uw - 2, 0, 2 * math.pi)
    set_src(ctx, d["jacket_sh"][:3] + (0.35,))
    ctx.fill()
    # avant-bras : manche retroussée (K) / manche longue (M)
    if who == "K":
        mid = (e[0] + (h[0] - e[0]) * 0.32, e[1] + (h[1] - e[1]) * 0.32)
        _limb(ctx, e, mid, uw - 2, uw - 4, jac)
        _limb(ctx, mid, h, 22, 19, lin(e[0], e[1], h[0], h[1], [(0, d["skin_sh"]), (1, d["skin"])]))
        # montre au poignet gauche
        if side == -1:
            wx, wy = mid[0] + (h[0] - mid[0]) * 0.75, mid[1] + (h[1] - mid[1]) * 0.75
            ellipse(ctx, wx, wy, 13, 9)
            set_src(ctx, hexc("#C9CED2"))
            ctx.fill()
            ellipse(ctx, wx, wy, 8, 5.5)
            set_src(ctx, hexc("#0D1A16"))
            ctx.fill()
    else:
        cuff = (e[0] + (h[0] - e[0]) * 0.86, e[1] + (h[1] - e[1]) * 0.86)
        _limb(ctx, e, cuff, uw - 2, 20, jac)
        _limb(ctx, cuff, h, 15, 14, d["skin"])
        if side == 1:
            # bracelet doré
            ellipse(ctx, cuff[0], cuff[1] + 4, 13, 6)
            ctx.set_line_width(2.4)
            set_src(ctx, d["chain"])
            ctx.stroke()
    # main
    ang = math.atan2(h[1] - e[1], h[0] - e[0])
    ctx.save()
    ctx.translate(*h)
    ctx.rotate(ang - math.pi / 2)
    hs = 1.0 if who == "K" else 0.84
    ctx.scale(hs, hs)
    smooth_path(ctx, [(-17, -6), (-19, 18), (-12, 34), (2, 38), (15, 32), (20, 14), (18, -6)], closed=True)
    ctx.set_source(lin(-18, 0, 18, 0, [(0, d["skin_hi"]), (1, d["skin_sh"])]))
    ctx.fill()
    # pouce
    _limb(ctx, (side * -14, 4), (side * -24 * (1 - g * 0.4), 22), 6.5, 5.5, d["skin"])
    # séparation des doigts
    ctx.set_line_width(1.4)
    set_src(ctx, _shade(d["skin"], 0.3)[:3] + (0.6,))
    for fx in (-6, 2, 10):
        ctx.move_to(fx, 24)
        ctx.line_to(fx + 1, 36)
    ctx.stroke()
    ctx.restore()


# ---------------------------------------------------------------- head
def head_path(ctx, d, yaw):
    hw, hh, jaw = d["head_w"], d["head_h"], d["jaw"]
    sk = yaw * 6
    pts = [(0 + sk, -hh), (hw * 0.80 + sk * 0.5, -hh * 0.82), (hw, -hh * 0.30), (hw * 0.98, hh * 0.12),
           (hw * jaw, hh * 0.60), (hw * 0.38 + sk, hh * 0.94), (0 + sk * 1.4, hh), (-hw * 0.38 + sk, hh * 0.94),
           (-hw * jaw, hh * 0.60), (-hw * 0.98, hh * 0.12), (-hw, -hh * 0.30), (-hw * 0.80 + sk * 0.5, -hh * 0.82)]
    smooth_path(ctx, pts, closed=True, tension=0.55)


def draw_mouth(ctx, d, st, who):
    op = st["open"]
    shape = st["shape"]
    sm = st["smile"]
    w = 27 if who == "K" else 24
    h = op * 25
    if shape == "round":
        w *= 0.72
        h *= 0.95
    elif shape == "wide":
        w *= 1.12
        h *= 0.62
    elif shape == "closed":
        h *= 0.12
    elif shape == "fv":
        h *= 0.35
    elif shape == "open":
        h *= 1.15
    lift = sm * 6
    y0 = 0
    if h > 1.5:
        # intérieur
        ctx.move_to(-w, y0 - lift * 0.4)
        ctx.curve_to(-w * 0.5, y0 - h * 0.45, w * 0.5, y0 - h * 0.45, w, y0 - lift * 0.4)
        ctx.curve_to(w * 0.6, y0 + h, -w * 0.6, y0 + h, -w, y0 - lift * 0.4)
        ctx.close_path()
        set_src(ctx, hexc("#2A0D0C"))
        ctx.fill_preserve()
        ctx.save()
        ctx.clip()
        # dents
        ctx.rectangle(-w, y0 - h * 0.5, 2 * w, h * 0.42 + 2)
        set_src(ctx, hexc("#F4EFE6"))
        ctx.fill()
        # langue
        ellipse(ctx, 0, y0 + h * 0.85, w * 0.55, h * 0.45)
        set_src(ctx, hexc("#8E3B3A"))
        ctx.fill()
        ctx.restore()
    # lèvre supérieure
    ctx.move_to(-w - 2, y0 - lift * 0.4)
    ctx.curve_to(-w * 0.6, y0 - 7 - h * 0.45, -w * 0.15, y0 - 8 - h * 0.45, 0, y0 - 5.5 - h * 0.45)
    ctx.curve_to(w * 0.15, y0 - 8 - h * 0.45, w * 0.6, y0 - 7 - h * 0.45, w + 2, y0 - lift * 0.4)
    ctx.curve_to(w * 0.5, y0 - h * 0.40, -w * 0.5, y0 - h * 0.40, -w - 2, y0 - lift * 0.4)
    ctx.close_path()
    set_src(ctx, d["lip"])
    ctx.fill()
    # lèvre inférieure
    lb = h * 0.75 if h > 1.5 else 0
    ctx.move_to(-w * 0.95, y0 - lift * 0.3 + 1)
    ctx.curve_to(-w * 0.5, y0 + lb + 1, w * 0.5, y0 + lb + 1, w * 0.95, y0 - lift * 0.3 + 1)
    ctx.curve_to(w * 0.55, y0 + lb + 11, -w * 0.55, y0 + lb + 11, -w * 0.95, y0 - lift * 0.3 + 1)
    ctx.close_path()
    ctx.set_source(lin(0, y0 + lb, 0, y0 + lb + 11, [(0, d["lip"]), (1, d["lip_hi"])]))
    ctx.fill()
    # reflet
    ellipse(ctx, w * 0.2, y0 + lb + 5.5, w * 0.25, 1.6)
    ctx.set_source_rgba(1, 1, 1, 0.18 if who == "K" else 0.32)
    ctx.fill()
    # commissures (sourire)
    if sm > 0.3:
        ctx.set_line_width(1.6)
        set_src(ctx, _shade(d["skin"], 0.35)[:3] + (0.5 * sm,))
        for s in (-1, 1):
            ctx.move_to(s * (w + 1), y0 - lift * 0.4)
            ctx.curve_to(s * (w + 5), y0 - lift * 0.8 - 2, s * (w + 6), y0 - lift - 5, s * (w + 4), y0 - lift - 8)
            ctx.stroke()


def draw_eye(ctx, d, st, side, who, yaw):
    ex = side * (d["head_w"] * 0.42) + yaw * 13
    ey = -8
    far = (side * yaw) < 0
    sx = 1.0 - (abs(yaw) * 0.25 if far else 0)
    ctx.save()
    ctx.translate(ex, ey)
    ctx.scale(sx, 1)
    ew, eh = (15, 7.5) if who == "K" else (15.5, 8.5)
    blink = st["blink"]
    # blanc de l'œil (amande)
    ctx.move_to(-ew, 1)
    ctx.curve_to(-ew * 0.5, -eh * 1.25, ew * 0.5, -eh * 1.25, ew, -1)
    ctx.curve_to(ew * 0.5, eh * 1.05, -ew * 0.5, eh * 1.05, -ew, 1)
    ctx.close_path()
    ctx.save()
    ctx.clip_preserve()
    set_src(ctx, hexc("#F3EEE6"))
    ctx.fill()
    gx = st["gaze_x"] * 6.5
    gy = st["gaze_y"] * 3
    ellipse(ctx, gx, gy, 7.6, 7.6)
    ctx.set_source(rad(gx, gy, 1, 7.6, [(0, _light(d["iris"], 0.25)), (1, d["iris"])]))
    ctx.fill()
    ellipse(ctx, gx, gy, 3.6, 3.6)
    set_src(ctx, hexc("#080505"))
    ctx.fill()
    ellipse(ctx, gx - 2.4, gy - 2.6, 1.8, 1.8)
    ctx.set_source_rgba(1, 1, 1, 0.9)
    ctx.fill()
    # paupière (clignement)
    if blink > 0.02:
        lid = -eh * 1.3 + (eh * 2.6) * blink
        ctx.rectangle(-ew - 2, -eh * 1.6, 2 * ew + 4, lid + eh * 1.6)
        set_src(ctx, d["skin"])
        ctx.fill()
    # ombre de paupière supérieure
    ctx.rectangle(-ew - 2, -eh * 1.6, 2 * ew + 4, eh * 0.75)
    set_src(ctx, _shade(d["skin"], 0.25)[:3] + (0.45,))
    ctx.fill()
    ctx.restore()
    # ligne de cils
    lid_y = -eh * 1.0 + (eh * 2.2) * blink
    ctx.move_to(-ew - 1, 1)
    ctx.curve_to(-ew * 0.5, lid_y - 1, ew * 0.5, lid_y - 1, ew + 2, -2)
    ctx.set_line_width(2.6 if who == "K" else 3.4)
    set_src(ctx, hexc("#120C0A"))
    ctx.stroke()
    if who == "M":
        # trait d'eye-liner discret + cils
        ctx.move_to(ew + 1, -2)
        ctx.line_to(ew + 6, -5)
        ctx.set_line_width(2.2)
        ctx.stroke()
    # pli de paupière
    ctx.move_to(-ew * 0.8, -eh * 1.15)
    ctx.curve_to(-ew * 0.3, -eh * 1.85, ew * 0.4, -eh * 1.85, ew * 0.9, -eh * 1.2)
    ctx.set_line_width(1.3)
    set_src(ctx, _shade(d["skin"], 0.4)[:3] + (0.5,))
    ctx.stroke()
    ctx.restore()


def draw_brows(ctx, d, st, who, yaw):
    for side in (-1, 1):
        bx = side * (d["head_w"] * 0.42) + yaw * 12
        by = -34 - st["brow"] * 7
        ctx.save()
        ctx.translate(bx, by)
        ctx.move_to(-side * 17, 4)
        ctx.curve_to(-side * 8, -4 - (2 if who == "M" else 0), side * 6, -5, side * 18, 1 + (2 if who == "M" else 0))
        ctx.set_line_width(5.5 if who == "K" else 4.2)
        ctx.set_line_cap(1)
        set_src(ctx, d["brow"])
        ctx.stroke()
        ctx.restore()


def draw_nose(ctx, d, yaw, who):
    nx = yaw * 16
    w = 14 if who == "K" else 11
    # ombre de l'arête
    ctx.move_to(nx - 4, -18)
    ctx.curve_to(nx - 6, 0, nx - 9, 14, nx - w, 24)
    ctx.set_line_width(2)
    set_src(ctx, _shade(d["skin"], 0.25)[:3] + (0.5,))
    ctx.stroke()
    # ailes du nez
    ellipse(ctx, nx, 27, w, 7)
    set_src(ctx, _shade(d["skin"], 0.12))
    ctx.fill()
    for s in (-1, 1):
        ellipse(ctx, nx + s * w * 0.48, 29, 3.4, 2.2)
        set_src(ctx, _shade(d["skin"], 0.55))
        ctx.fill()
    ellipse(ctx, nx + 2, 21, 4, 3)
    ctx.set_source_rgba(1, 0.9, 0.8, 0.18)
    ctx.fill()


def _curl_texture(ctx, rnd, cx, cy, rx, ry, n, cols, rmin=5, rmax=10, lw=2.6, clip_y=None):
    """Texture de boucles : petits arcs en spirale répartis dans une ellipse."""
    ctx.set_line_cap(1)
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        r = math.sqrt(rnd.random())
        x = cx + math.cos(a) * rx * r
        y = cy + math.sin(a) * ry * r
        if clip_y is not None and y > clip_y:
            continue
        rr = rnd.uniform(rmin, rmax)
        a0 = rnd.uniform(0, 2 * math.pi)
        ctx.new_path()
        ctx.arc(x, y, rr, a0, a0 + rnd.uniform(3.2, 4.6))
        ctx.set_line_width(lw)
        set_src(ctx, cols[i % len(cols)])
        ctx.stroke()


def draw_hair_back(ctx, d, st, who, t):
    if who != "M":
        return
    import random
    hw, hh = d["head_w"], d["head_h"]
    sway = math.sin(t * 1.3) * 2.0
    rnd = random.Random(7)
    ctx.save()
    # silhouette du volume (nuage de boucles jusqu'aux épaules)
    pts = []
    for k in range(28):
        a = math.pi * 0.62 + k / 27 * math.pi * 1.76
        r = 1.0 + 0.07 * math.sin(k * 2.7) + 0.05 * math.sin(k * 5.3)
        x = math.cos(a) * hw * 1.62 * r
        y = math.sin(a) * hh * 1.18 * r - 6
        y = min(y, hh * 1.35)
        x += sway * (y + hh) / (2.4 * hh)
        pts.append((x, y))
    pts.append((hw * 0.7, hh * 1.25))
    pts.append((-hw * 0.7, hh * 1.25))
    smooth_path(ctx, pts, closed=True, tension=0.6)
    ctx.set_source(rad(-hw * 0.3, -hh * 0.4, 20, hw * 2.0,
                       [(0, d["hair"]), (0.6, d["hair_sh"]), (1, _shade(d["hair_sh"], 0.2))]))
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    _curl_texture(ctx, rnd, sway * 0.5, -hh * 0.1, hw * 1.65, hh * 1.3, 360,
                  [d["hair_hi"][:3] + (0.75,), _light(d["hair"], 0.12)[:3] + (0.8,), d["hair_sh"][:3] + (0.9,)],
                  5, 10, 2.6)
    ctx.restore()
    ctx.restore()


def draw_hair_front(ctx, d, st, who, yaw, t):
    import random
    hw, hh = d["head_w"], d["head_h"]
    if who == "K":
        rnd = random.Random(3)
        ctx.save()
        # dessus : high-top court, contour net (line-up), dégradé sur les côtés
        smooth_path(ctx, [(-hw * 1.01, -hh * 0.22), (-hw * 1.00, -hh * 0.70), (-hw * 0.78, -hh * 1.12),
                          (yaw * 4, -hh * 1.26), (hw * 0.78, -hh * 1.12), (hw * 1.00, -hh * 0.70),
                          (hw * 1.01, -hh * 0.22), (hw * 0.90, -hh * 0.48), (hw * 0.55, -hh * 0.66),
                          (yaw * 6, -hh * 0.70), (-hw * 0.55, -hh * 0.66), (-hw * 0.90, -hh * 0.48)],
                    closed=True, tension=0.45)
        ctx.set_source(lin(0, -hh * 1.25, 0, -hh * 0.25, [(0, d["hair"]), (0.62, d["hair"]),
                                                        (1, d["hair"][:3] + (0.35,))]))
        ctx.fill()
        # twists denses sur le dessus
        for i in range(190):
            x = rnd.uniform(-hw * 0.9, hw * 0.9)
            top = -hh * (1.24 - 0.30 * (x / hw) ** 2)
            y = rnd.uniform(top, -hh * 0.78)
            r = rnd.uniform(3.8, 6.2)
            ctx.arc(x + yaw * 3, y, r, 0, math.pi * 2)
            set_src(ctx, d["hair_hi"] if rnd.random() < 0.35 else d["hair"])
            ctx.fill()
        # reflet doux
        ellipse(ctx, -hw * 0.35, -hh * 1.08, hw * 0.35, hh * 0.08)
        ctx.set_source_rgba(1, 1, 1, 0.05)
        ctx.fill()
        ctx.restore()
    else:
        rnd = random.Random(11)
        sway = math.sin(t * 1.3) * 1.5
        ctx.save()
        # masse frontale avec raie de côté
        path = [(-hw * 1.14, hh * 0.05), (-hw * 1.16, -hh * 0.66), (-hw * 0.72, -hh * 1.14),
                (-hw * 0.05 + yaw * 6, -hh * 1.20), (hw * 0.68, -hh * 1.14), (hw * 1.16, -hh * 0.70),
                (hw * 1.14, hh * 0.05), (hw * 0.95, -hh * 0.36), (hw * 0.62, -hh * 0.74),
                (hw * 0.18 + yaw * 6, -hh * 0.66), (-hw * 0.40, -hh * 0.84), (-hw * 0.94, -hh * 0.40)]
        smooth_path(ctx, path, closed=True, tension=0.5)
        ctx.set_source(lin(-hw, -hh, hw, 0, [(0, d["hair_hi"]), (0.5, d["hair"]), (1, d["hair_sh"])]))
        ctx.fill_preserve()
        ctx.save()
        ctx.clip()
        _curl_texture(ctx, rnd, sway, -hh * 0.75, hw * 1.2, hh * 0.55, 150,
                      [d["hair_hi"], _light(d["hair_hi"], 0.15)[:3] + (0.8,), d["hair_sh"][:3] + (0.8,)],
                      4.5, 8.5, 2.4)
        ctx.restore()
        # boucles qui retombent le long des joues
        for s in (-1, 1):
            for k in range(6):
                x = s * hw * (1.05 + 0.03 * k) + sway + math.sin(k * 1.9) * 3
                y = -hh * 0.28 + k * 17
                ctx.new_path()
                ctx.arc(x, y, 8.5, k * 1.1, k * 1.1 + 4.2)
                ctx.set_line_width(4.2)
                set_src(ctx, d["hair_hi"] if k % 2 else d["hair"])
                ctx.stroke()
        ctx.restore()


def draw_head(ctx, d, st, who, t):
    yaw = st["yaw"]
    hw, hh = d["head_w"], d["head_h"]
    # oreilles
    for s in (-1, 1):
        vis = 1.0 - max(0.0, s * yaw) * 0.6
        ex = s * (hw * 0.97) + yaw * 4
        ellipse(ctx, ex, 0, 11 * vis, 20)
        set_src(ctx, _shade(d["skin"], 0.08))
        ctx.fill()
        if who == "M":
            # créoles dorées
            ctx.arc(ex + s * 2, 34, 15, 0, math.pi * 2)
            ctx.set_line_width(2.6)
            set_src(ctx, d["chain"])
            ctx.stroke()
    # visage
    head_path(ctx, d, yaw)
    ctx.set_source(rad(-hw * 0.35 + yaw * 10, -hh * 0.35, 8, hw * 1.7,
                       [(0, d["skin_hi"]), (0.55, d["skin"]), (1, d["skin_sh"])]))
    ctx.fill()
    # ombre latérale (lumière de fin de journée depuis la gauche)
    ctx.save()
    head_path(ctx, d, yaw)
    ctx.clip()
    ctx.rectangle(hw * 0.35 + yaw * 10, -hh * 1.2, hw, hh * 2.4)
    ctx.set_source(lin(hw * 0.35, 0, hw, 0, [(0, d["skin_sh"][:3] + (0.0,)), (1, d["skin_sh"][:3] + (0.55,))]))
    ctx.fill()
    # lumière d'appoint bleutée (rim) côté droit, plus forte la nuit
    rim = 0.10 + 0.25 * st["light"]
    ctx.rectangle(hw * 0.75, -hh * 1.2, hw, hh * 2.4)
    ctx.set_source(lin(hw * 0.75, 0, hw * 1.05, 0, [(0, (0.35, 0.6, 1, 0)), (1, (0.45, 0.7, 1, rim))]))
    ctx.fill()
    # pommettes
    for s in (-1, 1):
        ellipse(ctx, s * hw * 0.52 + yaw * 10, hh * 0.18, 17, 10)
        ctx.set_source_rgba(0.85, 0.35, 0.3, 0.10 if who == "K" else 0.16)
        ctx.fill()
    ctx.restore()
    # barbe (K)
    if who == "K":
        ctx.save()
        head_path(ctx, d, yaw)
        ctx.clip()
        ctx.move_to(-hw * 1.0, hh * 0.12)
        ctx.curve_to(-hw * 0.95, hh * 0.70, -hw * 0.4, hh * 1.05, yaw * 8, hh * 1.05)
        ctx.curve_to(hw * 0.4, hh * 1.05, hw * 0.95, hh * 0.70, hw * 1.0, hh * 0.12)
        ctx.line_to(hw * 0.90, hh * 0.20)
        ctx.curve_to(hw * 0.78, hh * 0.66, hw * 0.40, hh * 0.86, yaw * 8, hh * 0.86)
        ctx.curve_to(-hw * 0.40, hh * 0.86, -hw * 0.78, hh * 0.66, -hw * 0.90, hh * 0.20)
        ctx.close_path()
        set_src(ctx, d["beard"][:3] + (0.80,))
        ctx.fill()
        # bouc + moustache
        ellipse(ctx, yaw * 12, hh * 0.86, 22, 12)
        ctx.fill()
        ctx.restore()
        ctx.save()
        ctx.translate(yaw * 14, 46)
        ctx.move_to(-26, -1)
        ctx.curve_to(-14, -9, 14, -9, 26, -1)
        ctx.curve_to(14, -4, -14, -4, -26, -1)
        set_src(ctx, d["beard"][:3] + (0.9,))
        ctx.fill()
        ctx.restore()
    draw_brows(ctx, d, st, who, yaw)
    for s in (-1, 1):
        draw_eye(ctx, d, st, s, who, yaw)
    draw_nose(ctx, d, yaw, who)
    ctx.save()
    ctx.translate(yaw * 14, 58 if who == "K" else 56)
    draw_mouth(ctx, d, st, who)
    ctx.restore()
    draw_hair_front(ctx, d, st, who, yaw, t)


def draw_character(ctx, who, st, t=0.0):
    """Dessine le personnage complet (assis) dans le repère courant."""
    d = DESIGN[who]
    ctx.save()
    draw_legs(ctx, d, st)
    ctx.save()
    ctx.rotate(st["lean"] * 0.05)
    # cheveux arrière (derrière le cou et le buste)
    ctx.save()
    ctx.translate(0, NECK_Y - st["breath"] * 3)
    ctx.rotate(st["tilt"] * 0.10)
    ctx.translate(0, HEAD_CY - NECK_Y + st["nod"] * 7)
    draw_hair_back(ctx, d, st, who, t)
    ctx.restore()
    draw_torso(ctx, d, st, who)
    # cou
    ctx.save()
    ctx.translate(0, -st["breath"] * 3)
    nw = d["neck"]
    ctx.rectangle(-nw, NECK_Y - 60, nw * 2, 78)
    ctx.set_source(lin(-nw, 0, nw, 0, [(0, d["skin"]), (1, d["skin_sh"])]))
    ctx.fill()
    ellipse(ctx, 0, NECK_Y - 4, nw, 10)
    set_src(ctx, _shade(d["skin"], 0.25)[:3] + (0.55,))
    ctx.fill()
    # tête : pivot à la base du cou
    ctx.translate(0, NECK_Y)
    ctx.rotate(st["tilt"] * 0.10)
    ctx.translate(0, HEAD_CY - NECK_Y + st["nod"] * 7)
    draw_head(ctx, d, st, who, t)
    ctx.restore()
    for side in (-1, 1):
        draw_arm(ctx, d, st, side, who)
    ctx.restore()
    ctx.restore()


def draw_microphone(ctx, side, light=0.0):
    """Micro de podcast sur bras articulé, posé devant le personnage (côté extérieur)."""
    ctx.save()
    # bras
    ctx.set_line_width(9)
    ctx.set_line_cap(1)
    ctx.set_source_rgba(0.08, 0.09, 0.1, 1)
    ctx.move_to(side * 210, 130)
    ctx.line_to(side * 190, -140)
    ctx.line_to(side * 120, -250)
    ctx.stroke()
    # suspension + micro
    ctx.translate(side * 110, -270)
    ctx.rotate(-side * 0.35)
    from draw import rrect
    rrect(ctx, -22, -56, 44, 92, 20)
    ctx.set_source(lin(-22, 0, 22, 0, [(0, (0.28, 0.3, 0.32, 1)), (0.5, (0.12, 0.13, 0.14, 1)), (1, (0.05, 0.05, 0.06, 1))]))
    ctx.fill()
    # grille
    ctx.set_line_width(1.2)
    ctx.set_source_rgba(1, 1, 1, 0.10)
    for k in range(7):
        ctx.move_to(-18, -46 + k * 9)
        ctx.line_to(18, -46 + k * 9)
    ctx.stroke()
    # bague dorée
    ctx.rectangle(-23, 20, 46, 8)
    ctx.set_source_rgba(0.98, 0.75, 0.23, 1)
    ctx.fill()
    ctx.restore()
