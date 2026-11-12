"""Étape 6 — Habillages graphiques et motion design de l'épisode.

Chaque scène : fn(ctx, tl, dur, data, env) où tl = temps local (s) depuis le début du plan.
env = {"t": temps global, "director": Director, "who": orateur}
Les visuels de pochettes sont des CRÉATIONS TYPOGRAPHIQUES ORIGINALES (pas les pochettes
officielles, soumises à autorisation — voir docs/04-droits/autorisations.md).
"""
import json
import math
import random

import cairo

from config import H, PROJECT, W
from draw import (P, clamp, ease_back, ease_in_out, ease_out, ellipse, fmt_int, hexc, lin, mix, prog, rad,
                  rrect, set_src, smooth_path, text, text_width, wrap)

GEO = json.loads((PROJECT / "production" / "assets" / "geo" / "guyane_ne10m.json").read_text())["ring"]


# ------------------------------------------------------------------ fonds
def gfx_bg(ctx, t, tint="green", intensity=1.0):
    base = {"green": ("#06120F", "#0B3A2A"), "red": ("#140606", "#4A0E0C"), "night": ("#05080C", "#10202A"),
            "gold": ("#120D04", "#3A2A08")}[tint]
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(lin(0, 0, W, H, [(0, hexc(base[0])), (1, hexc(base[1]))]))
    ctx.fill()
    # faisceaux lumineux lents
    for i in range(3):
        a = -0.6 + i * 0.25 + math.sin(t * 0.15 + i) * 0.05
        ctx.save()
        ctx.translate(W * (0.2 + 0.3 * i), -100)
        ctx.rotate(a)
        ctx.rectangle(-60 - 30 * i, 0, 120 + 60 * i, 1800)
        ctx.set_source(lin(0, 0, 0, 1400, [(0, (1, 0.85, 0.5, 0.06 * intensity)), (1, (1, 0.85, 0.5, 0))]))
        ctx.fill()
        ctx.restore()
    # ombres de palmes (gobo) qui dérivent
    ctx.save()
    ctx.translate(W * 0.85 + math.sin(t * 0.2) * 30, H * 0.15)
    ctx.rotate(0.5 + math.sin(t * 0.3) * 0.04)
    for k in range(14):
        ctx.save()
        ctx.translate(k * 40, 0)
        ctx.rotate(0.9)
        ellipse(ctx, 0, -60, 14, 80)
        ctx.restore()
        ctx.save()
        ctx.translate(k * 40, 0)
        ctx.rotate(-0.9 + math.pi)
        ellipse(ctx, 0, -60, 14, 80)
        ctx.restore()
    ctx.set_source_rgba(0, 0, 0, 0.18)
    ctx.fill()
    ctx.restore()
    # poussières dorées
    r = random.Random(42)
    for i in range(46):
        x = (r.uniform(0, W) + t * r.uniform(4, 16)) % W
        y = (r.uniform(0, H) - t * r.uniform(3, 10)) % H
        a = (0.25 + 0.25 * math.sin(t * r.uniform(1, 2.5) + i)) * intensity
        ctx.arc(x, y, r.uniform(1, 2.6), 0, 6.3)
        ctx.set_source_rgba(0.98, 0.78, 0.35, a)
        ctx.fill()
    # cadre fin + repères d'angle
    ctx.set_line_width(2)
    ctx.set_source_rgba(1, 1, 1, 0.10)
    ctx.rectangle(48, 48, W - 96, H - 96)
    ctx.stroke()
    ctx.set_line_width(4)
    set_src(ctx, P("gold", 0.8))
    for (x, y, dx, dy) in ((48, 48, 1, 1), (W - 48, 48, -1, 1), (48, H - 48, 1, -1), (W - 48, H - 48, -1, -1)):
        ctx.move_to(x, y + dy * 40)
        ctx.line_to(x, y)
        ctx.line_to(x + dx * 40, y)
        ctx.stroke()


def source_line(ctx, s, a=1.0):
    text(ctx, "SOURCE", 96, H - 74, 14, P("gold", 0.9 * a), "bold", tracking=0.25)
    text(ctx, s, 180, H - 74, 17, P("white", 0.75 * a), "medium", family="Inter")


def kicker(ctx, s, x, y, a=1.0, color="gold"):
    w = text_width(ctx, s, 18, "bold", tracking=0.3)
    rrect(ctx, x - 14, y - 26, w + 28, 38, 4)
    set_src(ctx, P(color, 0.95 * a))
    ctx.fill()
    text(ctx, s, x, y, 18, P("night", a), "bold", tracking=0.3)


def fade_in_out(tl, dur, fin=0.35, fout=0.3):
    return ease_out(prog(tl, 0, fin)) * (1 - ease_out(prog(tl, dur - fout, dur)))


# ------------------------------------------------------------------ logo 3D
def logo_3d(ctx, cx, cy, size, t, rot=0.0, alpha=1.0, sweep=None):
    """« 973 » extrudé (pseudo-3D) avec balayage lumineux."""
    sx = math.cos(rot)
    depth = 16
    for k in range(depth, 0, -1):
        ctx.save()
        ctx.translate(cx + k * 1.6 * (1 if sx >= 0 else -1) * (1 - abs(sx)) * 0 + k * 0.9, cy + k * 1.2)
        ctx.scale(max(0.05, abs(sx)), 1)
        c = mix(hexc("#5A3A06"), hexc("#1A1004"), k / depth)
        text(ctx, "973", 0, 0, size, c[:3] + (alpha,), "black", "center")
        ctx.restore()
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(max(0.05, abs(sx)), 1)
    from draw import font
    font(ctx, size, "black")
    tw = ctx.text_extents("973").x_advance
    ctx.move_to(-tw / 2, 0)
    ctx.text_path("973")
    ctx.set_source(lin(0, -size * 0.8, 0, 0, [(0, hexc("#FFE39A")), (0.5, hexc("#F9BF3B")), (1, hexc("#C98A12"))]))
    ctx.fill_preserve()
    if sweep is not None:
        ctx.save()
        ctx.clip()
        sxp = -tw / 2 - 200 + sweep * (tw + 400)
        ctx.rectangle(sxp - 60, -size, 120, size * 1.2)
        ctx.set_source(lin(sxp - 60, 0, sxp + 60, 0, [(0, (1, 1, 1, 0)), (0.5, (1, 1, 1, 0.75 * alpha)), (1, (1, 1, 1, 0))]))
        ctx.fill()
        ctx.restore()
    ctx.new_path()
    ctx.restore()


def scene_logo(ctx, tl, dur, data, env):
    gfx_bg(ctx, tl, "night", 1.0)
    a = fade_in_out(tl, dur, 0.2, 0.4)
    ctx.set_source(rad(W / 2, H / 2 - 40, 20, 700, [(0, (0.98, 0.7, 0.2, 0.35 * a)), (1, (0.98, 0.7, 0.2, 0))]))
    ctx.paint()
    # anneaux
    for i in range(3):
        rr = 180 + i * 90 + ease_out(prog(tl, 0.1 * i, 1.2 + 0.1 * i)) * 60
        ctx.arc(W / 2, H / 2 - 50, rr, 0, 6.3)
        ctx.set_line_width(2)
        set_src(ctx, [P("green2"), P("red"), P("blue")][i][:3] + (0.35 * a * (1 - prog(tl, 2.5, 4.5)) + 0.1 * a,))
        ctx.stroke()
    rot = (1 - ease_out(prog(tl, 0.1, 1.4))) * math.pi * 0.9
    sc = 0.6 + 0.4 * ease_back(prog(tl, 0.1, 1.2))
    logo_3d(ctx, W / 2, H / 2 + 30, 300 * sc, tl, rot, a, sweep=prog(tl, 1.6, 2.6))
    b = ease_out(prog(tl, 1.3, 2.0)) * a
    text(ctx, "CULTURE", W / 2, H / 2 + 120, 64, P("white", b), "black", "center", tracking=0.42)
    ctx.rectangle(W / 2 - 260 * b, H / 2 + 150, 520 * b, 5)
    set_src(ctx, P("red", b))
    ctx.fill()
    c = ease_out(prog(tl, 2.0, 2.7)) * a
    text(ctx, "LE PODCAST", W / 2, H / 2 + 200, 28, P("gold", c), "bold", "center", tracking=0.5)
    d = ease_out(prog(tl, 2.7, 3.4)) * a
    text(ctx, "« Les talents d'ici méritent une audience mondiale. »", W / 2, H / 2 + 270, 30,
         P("white", 0.85 * d), "medium", "center", family="Inter")


def scene_name_reveal(ctx, tl, dur, data, env):
    gfx_bg(ctx, tl, "red", 0.8)
    a = fade_in_out(tl, dur, 0.1, 0.35)
    letters = "LYPHIK"
    size = 300
    total = text_width(ctx, letters, size, "black", tracking=0.04)
    x = W / 2 - total / 2
    for i, chr_ in enumerate(letters):
        p = ease_back(prog(tl, 0.08 * i, 0.08 * i + 0.45), 2.2)
        wdt = text_width(ctx, chr_, size, "black")
        ctx.save()
        ctx.translate(x + wdt / 2, H / 2 + 90)
        ctx.scale(1, max(0.01, p))
        # ombre portée
        text(ctx, chr_, 8, 10, size, (0, 0, 0, 0.45 * a), "black", "center")
        text(ctx, chr_, 0, 0, size, P("white", a) if i % 2 == 0 else P("gold", a), "black", "center")
        ctx.restore()
        x += wdt + 0.04 * size
    # barre et sous-titres
    b = ease_out(prog(tl, 0.7, 1.3)) * a
    ctx.rectangle(W / 2 - 520 * b, H / 2 + 130, 1040 * b, 6)
    set_src(ctx, P("gold", b))
    ctx.fill()
    c = ease_out(prog(tl, 1.0, 1.6)) * a
    text(ctx, "LYPHIK PML  ·  MATOURY, GUYANE", W / 2, H / 2 + 196, 36, P("white", c), "bold", "center", tracking=0.2)
    d = ease_out(prog(tl, 1.4, 2.0)) * a
    text(ctx, "RAP  ·  TRAP  ·  DRILL  ·  DANCEHALL", W / 2, H / 2 + 252, 26, P("gold", d), "semibold", "center", tracking=0.35)
    # éclair de lumière au moment de l'impact
    flash = max(0.0, 1 - abs(tl - 0.55) / 0.25) * 0.35
    ctx.set_source_rgba(1, 0.95, 0.85, flash)
    ctx.paint()


# ------------------------------------------------------------------ data
def scene_stat(ctx, tl, dur, data, env):
    gfx_bg(ctx, env["t"], "night")
    a = fade_in_out(tl, dur)
    v = data["value"]
    p = 1.0 if data.get("hold") else ease_out(prog(tl, 0.15, min(1.6, dur * 0.7)))
    shown = v * p
    s = fmt_int(round(shown, -3) if data.get("approx") and p >= 1 else shown)
    if data.get("approx"):
        s = "≈ " + s
    kicker(ctx, "CHIFFRE VÉRIFIÉ", 160, 300, a, "blue")
    text(ctx, s, 150, 560, 230, P("white", a), "black")
    text(ctx, data["unit"].upper(), 160, 650, 54, P("gold", a), "black", tracking=0.2)
    text(ctx, data["label"], 160, 730, 40, P("white", 0.9 * a), "semibold", family="Inter")
    # mini-graphique de progression (électrique)
    ctx.save()
    ctx.translate(1300, 640)
    ctx.set_line_width(5)
    set_src(ctx, P("blue", a))
    pts = [(0, 0), (90, -40), (170, -30), (260, -120), (340, -110), (430, -260)]
    n = max(1, int(len(pts) * p))
    ctx.move_to(*pts[0])
    for pt in pts[1:n]:
        ctx.line_to(*pt)
    ctx.stroke()
    for pt in pts[:n]:
        ctx.arc(pt[0], pt[1], 8, 0, 6.3)
        set_src(ctx, P("gold", a))
        ctx.fill()
    ctx.restore()
    source_line(ctx, data["source"], a)


def _proj(lon, lat, view):
    (lon0, lat0, lon1, lat1), (x0, y0, x1, y1) = view
    k = min((x1 - x0) / (lon1 - lon0), (y1 - y0) / (lat1 - lat0))
    cxw, cyw = (x0 + x1) / 2, (y0 + y1) / 2
    clon, clat = (lon0 + lon1) / 2, (lat0 + lat1) / 2
    return cxw + (lon - clon) * k, cyw - (lat - clat) * k


PLACES = {  # coordonnées approximatives (centres de commune / quartier)
    "cayenne": ("Cayenne", -52.326, 4.937),
    "matoury": ("Matoury · Copaya", -52.330, 4.846),
    "larivot": ("Le Larivot", -52.374, 4.902),
    "kourou": ("Kourou", -52.650, 5.160),
}


def scene_map(ctx, tl, dur, data, env):
    gfx_bg(ctx, env["t"], "green", 0.7)
    a = fade_in_out(tl, dur)
    focus = data.get("focus", "matoury")
    full = (-54.8, 2.0, -51.4, 5.9)
    zoom_box = {"matoury": (-52.75, 4.62, -52.05, 5.08), "larivot": (-52.75, 4.62, -52.05, 5.08),
                "kourou": (-53.2, 4.55, -52.0, 5.45)}[focus]
    z = ease_in_out(prog(tl, 0.6, 2.2))
    box = tuple(f + (zb - f) * z for f, zb in zip(full, zoom_box))
    view = (box, (420, 140, 1500, 960))
    # mer
    ctx.rectangle(0, 0, W, H)
    ctx.set_source_rgba(0.05, 0.25, 0.4, 0.25 * a)
    ctx.fill()
    # contour progressif
    pts = [_proj(lon, lat, view) for lon, lat in GEO]
    reveal = ease_out(prog(tl, 0.0, 0.9))
    ctx.move_to(*pts[0])
    for pnt in pts[1:]:
        ctx.line_to(*pnt)
    ctx.close_path()
    ctx.set_source(lin(0, 140, 0, 960, [(0, hexc("#1F7A52", 0.9 * a * reveal)), (1, hexc("#0C3A28", 0.95 * a * reveal))]))
    ctx.fill_preserve()
    ctx.set_line_width(3)
    set_src(ctx, P("gold", a))
    ctx.stroke()
    # étiquettes géographiques
    ga = a * (1 - z)
    text(ctx, "OCÉAN ATLANTIQUE", 1450, 230, 24, P("white", 0.5 * ga), "semibold", "center", tracking=0.3)
    text(ctx, "SURINAME", 330, 560, 24, P("white", 0.45 * ga), "semibold", "center", tracking=0.3)
    text(ctx, "BRÉSIL", 1420, 880, 24, P("white", 0.45 * ga), "semibold", "center", tracking=0.3)
    text(ctx, "GUYANE", 960 - 40, 640, 64, P("white", 0.85 * ga), "black", "center", tracking=0.25)
    # repères
    for i, key in enumerate(data.get("pins", [])):
        name, lon, lat = PLACES[key]
        x, y = _proj(lon, lat, view)
        pa = ease_back(prog(tl, 0.9 + i * 0.35, 1.4 + i * 0.35)) * a
        hot = key == focus
        col = P("red") if hot else P("gold")
        r = (16 if hot else 11) * pa
        if hot:
            pul = (tl * 1.2) % 1.0
            ctx.arc(x, y, 16 + pul * 50, 0, 6.3)
            ctx.set_line_width(3)
            set_src(ctx, col[:3] + ((1 - pul) * 0.8 * a,))
            ctx.stroke()
        ctx.arc(x, y, r, 0, 6.3)
        set_src(ctx, col[:3] + (pa,))
        ctx.fill()
        ctx.arc(x, y, r * 0.4, 0, 6.3)
        set_src(ctx, P("white", pa))
        ctx.fill()
        # étiquette
        dx = 30 if key != "larivot" else -30
        al = "left" if dx > 0 else "right"
        dy = {"cayenne": -18, "matoury": 26, "larivot": -18, "kourou": -18}[key]
        tw = text_width(ctx, name, 30 if hot else 24, "bold")
        bx = x + dx - (tw + 24 if al == "right" else 0) - 12 * (0 if al == "left" else -1)
        rrect(ctx, (x + dx - 12) if al == "left" else (x + dx - tw - 12), y + dy - 30, tw + 24, 42, 6)
        set_src(ctx, P("night", 0.85 * pa))
        ctx.fill()
        text(ctx, name, x + dx, y + dy, 30 if hot else 24, P("white", pa), "bold", al)
    if data.get("event"):
        e = ease_out(prog(tl, 1.6, 2.2)) * a
        rrect(ctx, 520, 860, 880, 70, 8)
        set_src(ctx, P("night", 0.9 * e))
        ctx.fill()
        kicker(ctx, "CONFIRMÉ", 548, 908, e, "green2")
        text(ctx, data["event"], 730, 906, 24, P("white", e), "semibold", family="Inter")
    kicker(ctx, "CARTE", 96, 120, a)
    source_line(ctx, "Fond de carte Natural Earth (domaine public) · positions approximatives · biographie officielle de l'artiste", a)


def scene_quote(ctx, tl, dur, data, env):
    gfx_bg(ctx, env["t"], "gold", 0.6)
    a = fade_in_out(tl, dur)
    text(ctx, "“", 170, 470, 420, P("gold", 0.35 * a), "black")
    lines = wrap(ctx, data["quote"], 64, 1350, "semibold")
    for i, ln in enumerate(lines):
        la = ease_out(prog(tl, 0.2 + i * 0.25, 0.7 + i * 0.25)) * a
        text(ctx, ln, 300, 430 + i * 92, 64, P("white", la), "semibold", family="Inter")
    y = 430 + len(lines) * 92 + 30
    b = ease_out(prog(tl, 1.0, 1.5)) * a
    kicker(ctx, "DÉCLARATION DE L'ARTISTE", 300, y + 20, b)
    text(ctx, data["source"], 300, y + 80, 28, P("white", 0.7 * b), "medium", family="Inter")


def scene_pml(ctx, tl, dur, data, env):
    gfx_bg(ctx, env["t"], "night")
    a = fade_in_out(tl, dur)
    xs = [560, 960, 1360]
    for i, L in enumerate("PML"):
        p = ease_back(prog(tl, 0.1 + i * 0.18, 0.6 + i * 0.18))
        ctx.save()
        ctx.translate(xs[i], 520)
        ctx.scale(p, p)
        text(ctx, L, 0, 0, 360, P("gold", a) if i != 1 else P("white", a), "black", "center")
        ctx.restore()
    b = ease_out(prog(tl, 1.0, 1.6)) * a
    # « PA MÉLÉ » avec lettres-clés en couleur
    words = [("P", "gold"), ("A", "white"), (" ", "white"), ("M", "gold"), ("É", "white"), ("L", "gold"), ("É", "white")]
    total = sum(text_width(ctx, c, 96, "black") for c, _ in words)
    x = W / 2 - total / 2
    for c, col in words:
        wdt = text_width(ctx, c, 96, "black")
        text(ctx, c, x, 700, 96, P(col, b), "black")
        x += wdt
    c2 = ease_out(prog(tl, 1.6, 2.2)) * a
    if data.get("label"):
        text(ctx, "Mixtape #PML (débuts)   →   Label P.M.L (2026)", W / 2, 800, 34, P("white", 0.85 * c2), "semibold", "center", family="Inter")
        source_line(ctx, "Crédits Spotify / Deezer (« 2026 P.M.L ») · France-Guyane (mixtape #PML)", a)
    else:
        text(ctx, "Nom de sa première mixtape  ·  devenu sa signature : Lyphik PML", W / 2, 800, 34, P("white", 0.85 * c2), "semibold", "center", family="Inter")
        source_line(ctx, "France-Guyane · chaîne ALLNICE Production · traduction approximative du créole", a)


ERAS = [
    (2015, 2018.0, "ALLNICE · BHP", "Mixtape #PML · La Rage · La zone (feat.)", "green2"),
    (2018.0, 2022.0, "ÈRE HYT", "Dadada · Link Up · BDMW · Diss", "gold"),
    (2022.0, 2025.0, "FA7", "EP FA7 · Renta · Forward · Cataracte", "red"),
    (2025.0, 2026.95, "FEATS & P.M.L", "Malus · Focus · Impulsif · Bad Life", "blue"),
]


def scene_timeline(ctx, tl, dur, data, env):
    gfx_bg(ctx, env["t"], "green", 0.6)
    a = fade_in_out(tl, dur)
    upto = data.get("era", 0)
    x0, x1, y = 160, 1760, 560
    def X(yr):
        return x0 + (yr - 2015) / (2027 - 2015) * (x1 - x0)
    pr = ease_out(prog(tl, 0, 1.0))
    ctx.rectangle(x0, y - 3, (x1 - x0) * pr, 6)
    set_src(ctx, P("white", 0.5 * a))
    ctx.fill()
    for yr in range(2015, 2027):
        xx = X(yr)
        ctx.rectangle(xx - 1.5, y - 14, 3, 28)
        set_src(ctx, P("white", 0.5 * a * pr))
        ctx.fill()
        text(ctx, str(yr), xx, y + 52, 22, P("white", 0.65 * a * pr), "semibold", "center")
    for i, (s, e, title, sub, col) in enumerate(ERAS):
        active = i <= upto
        ea = ease_out(prog(tl, 0.5 + i * 0.25, 1.0 + i * 0.25)) * a * (1.0 if active else 0.28)
        hl = i == upto
        top = y - (260 if i % 2 == 0 else 170)
        rrect(ctx, X(s) + 4, top, X(e) - X(s) - 8, 110 if hl else 96, 8)
        set_src(ctx, P(col, (0.95 if hl else 0.6) * ea))
        ctx.fill()
        text(ctx, title, X(s) + 22, top + 46, 32 if hl else 26, P("night", ea), "black")
        text(ctx, sub, X(s) + 22, top + 84, 19, P("night", 0.85 * ea), "semibold", family="Inter")
        ctx.rectangle(X(s) + 4, top + (110 if hl else 96), 3, y - top - (110 if hl else 96))
        set_src(ctx, P(col, ea))
        ctx.fill()
    # curseur « on est ici »
    cur = {0: 2015.6, 1: 2018.4}.get(upto, 2018.4)
    ctx.arc(X(cur), y, 14, 0, 6.3)
    set_src(ctx, P("red", a))
    ctx.fill()
    kicker(ctx, "PARCOURS", 96, 120, a)
    text(ctx, "Chronologie établie à partir des plateformes officielles et de la biographie de l'artiste", 160, 860, 22, P("white", 0.6 * a), "medium", family="Inter")
    source_line(ctx, "YouTube · Spotify · Deezer · biographie officielle (débuts 2015, HYT depuis 2018 : déclaratif)", a)


STYLES = {
    "vhs": ("#1B1B1F", "#3A3A44", "#E6E6E6"),
    "teal": ("#062A2C", "#0F6A6A", "#7FF5E6"),
    "fire": ("#2A0503", "#C0271A", "#FFD27A"),
    None: ("#0E2B22", "#1E6B4E", "#F9BF3B"),
}


def scene_clip_slot(ctx, tl, dur, data, env):
    gfx_bg(ctx, env["t"], "night", 0.6)
    a = fade_in_out(tl, dur)
    st = STYLES.get(data.get("style"), STYLES[None])
    p = ease_out(prog(tl, 0, 0.6))
    fw, fh = 1100, 619
    fx, fy = 120 + (1 - p) * -80, 210
    # écran 16:9 (emplacement d'extrait)
    rrect(ctx, fx - 10, fy - 10, fw + 20, fh + 20, 18)
    set_src(ctx, P("gold", 0.9 * a))
    ctx.fill()
    ctx.save()
    rrect(ctx, fx, fy, fw, fh, 10)
    ctx.clip()
    ctx.rectangle(fx, fy, fw, fh)
    ctx.set_source(lin(fx, fy, fx + fw, fy + fh, [(0, hexc(st[0])), (1, hexc(st[1]))]))
    ctx.fill()
    # texture animée selon l'esthétique
    style = data.get("style")
    r = random.Random(int(env["t"] * 12))
    if style == "vhs":
        for k in range(0, fh, 4):
            ctx.rectangle(fx, fy + k, fw, 1.5)
        ctx.set_source_rgba(1, 1, 1, 0.05)
        ctx.fill()
        yb = fy + (env["t"] * 160) % fh
        ctx.rectangle(fx, yb, fw, 26)
        ctx.set_source_rgba(1, 1, 1, 0.06)
        ctx.fill()
        text(ctx, "▶ PLAY", fx + 40, fy + 70, 34, (1, 1, 1, 0.8 * a), "bold", family="JetBrains Mono")
    elif style == "fire":
        for k in range(40):
            x = fx + r.uniform(0, fw)
            y = fy + fh - ((env["t"] * 120 + k * 37) % fh)
            ctx.arc(x, y, r.uniform(1.5, 4), 0, 6.3)
            ctx.set_source_rgba(1, 0.7, 0.3, 0.7)
            ctx.fill()
        ctx.set_source(lin(0, fy + fh * 0.4, 0, fy + fh, [(0, (1, 0.4, 0.1, 0)), (1, (1, 0.5, 0.1, 0.45))]))
        ctx.rectangle(fx, fy, fw, fh)
        ctx.fill()
    else:
        for k in range(6):
            ctx.save()
            ctx.translate(fx + fw / 2, fy + fh / 2)
            ctx.rotate(env["t"] * 0.1 + k)
            ctx.rectangle(-900, -2, 1800, 4)
            ctx.set_source_rgba(*hexc(st[2])[:3], 0.08)
            ctx.fill()
            ctx.restore()
    # bouton lecture central
    pul = 1 + 0.05 * math.sin(env["t"] * 4)
    ctx.arc(fx + fw / 2, fy + fh / 2, 70 * pul, 0, 6.3)
    ctx.set_source_rgba(0, 0, 0, 0.45)
    ctx.fill()
    ctx.move_to(fx + fw / 2 - 22, fy + fh / 2 - 36)
    ctx.line_to(fx + fw / 2 + 40, fy + fh / 2)
    ctx.line_to(fx + fw / 2 - 22, fy + fh / 2 + 36)
    ctx.close_path()
    set_src(ctx, hexc(st[2], a))
    ctx.fill()
    text(ctx, "CLIP OFFICIEL  ·  À VOIR SUR YOUTUBE", fx + fw / 2, fy + fh - 40, 24, (1, 1, 1, 0.85 * a), "bold", "center", tracking=0.2)
    text(ctx, data.get("slot", ""), fx + fw - 30, fy + 44, 18, (1, 1, 1, 0.35 * a), "bold", "right", family="JetBrains Mono")
    ctx.restore()
    # fiche
    b = ease_out(prog(tl, 0.3, 0.9)) * a
    x = 1290
    kicker(ctx, "LE CLIP", x, 290, b, "red")
    lines = wrap(ctx, data["title"], 54, 520, "black", family="Inter Display")
    for i, ln in enumerate(lines):
        text(ctx, ln, x, 380 + i * 62, 54, P("white", b), "black")
    yy = 380 + len(lines) * 62 + 20
    for ln in wrap(ctx, data["meta"], 26, 520, "medium"):
        text(ctx, ln, x, yy, 26, P("white", 0.75 * b), "medium", family="Inter")
        yy += 38
    text(ctx, data["views"], x, yy + 50, 44, P("gold", b), "black")
    source_line(ctx, "YouTube · relevé du 12/11/2026 · extrait officiel intégrable après autorisation des ayants droit", a)


def _cover(ctx, x, y, s, title, sub, seed, a):
    """pochette typographique originale (pas la pochette officielle)"""
    r = random.Random(seed)
    cols = [("#0E4A35", "#F9BF3B"), ("#7E1F1C", "#F8F6F0"), ("#0A1012", "#2E8DFF"), ("#3A2A08", "#F9BF3B"),
            ("#122A3A", "#D93434")]
    bgc, acc = cols[seed % len(cols)]
    rrect(ctx, x, y, s, s, 14)
    ctx.set_source(lin(x, y, x + s, y + s, [(0, hexc(bgc, a)), (1, mix(hexc(bgc), (0, 0, 0, 1), 0.5)[:3] + (a,))]))
    ctx.fill()
    ctx.save()
    rrect(ctx, x, y, s, s, 14)
    ctx.clip()
    for k in range(5):
        ctx.arc(x + r.uniform(0, s), y + r.uniform(0, s), r.uniform(s * 0.2, s * 0.6), 0, 6.3)
        ctx.set_line_width(r.uniform(2, 10))
        set_src(ctx, hexc(acc, 0.18 * a))
        ctx.stroke()
    ctx.restore()
    lines = wrap(ctx, title, s * 0.17, s - 40, "black", family="Inter Display")
    for i, ln in enumerate(lines[:3]):
        text(ctx, ln, x + 22, y + s * 0.30 + i * s * 0.17, s * 0.17, hexc(acc, a), "black")
    text(ctx, "LYPHIK", x + 22, y + s - 28, s * 0.08, P("white", 0.9 * a), "bold", tracking=0.3)
    text(ctx, sub, x + 22, y + s + 44, 26, P("white", 0.85 * a), "semibold", family="Inter")


def scene_cards(ctx, tl, dur, data, env):
    gfx_bg(ctx, env["t"], "night", 0.8)
    a = fade_in_out(tl, dur)
    items = data["items"]
    s = 420
    gap = 90
    x0 = W / 2 - (len(items) * s + (len(items) - 1) * gap) / 2
    for i, (title, sub) in enumerate(items):
        p = ease_back(prog(tl, 0.15 + i * 0.3, 0.75 + i * 0.3))
        ctx.save()
        cx = x0 + i * (s + gap) + s / 2
        ctx.translate(cx, 470)
        ctx.rotate((1 - p) * 0.3 * (1 if i % 2 else -1))
        ctx.scale(max(0.01, p), max(0.01, p))
        _cover(ctx, -s / 2, -s / 2, s, title, sub, hash(title) % 97, a)
        ctx.restore()
    source_line(ctx, "Spotify · Deezer · YouTube — visuels : créations typographiques 973 Culture (pas les pochettes officielles)", a)


def scene_ep(ctx, tl, dur, data, env):
    gfx_bg(ctx, env["t"], "gold", 0.7)
    a = fade_in_out(tl, dur)
    p = ease_back(prog(tl, 0, 0.6))
    ctx.save()
    ctx.translate(520, 520)
    ctx.scale(p, p)
    _cover(ctx, -300, -300, 600, data["title"], "EP · " + data["date"], 3, a)
    ctx.restore()
    kicker(ctx, "EP · 7 TITRES", 960, 250, a)
    for i, tr in enumerate(data["tracks"]):
        ta = ease_out(prog(tl, 0.3 + i * 0.16, 0.6 + i * 0.16)) * a
        hl = i == data.get("highlight")
        y = 330 + i * 78
        if hl:
            rrect(ctx, 940, y - 50, 820, 68, 8)
            set_src(ctx, P("red", 0.9 * ta))
            ctx.fill()
        text(ctx, f"{i + 1:02d}", 970, y, 30, P("gold" if not hl else "white", ta), "black")
        text(ctx, tr, 1050, y, 36, P("white", ta), "bold" if hl else "semibold")
    source_line(ctx, "Spotify (sortie : 17/03/2022) · Deezer", a)


NET_NODES = {  # disposition en étoile autour de Lyphik (lisibilité, pas de croisements)
    "LYPHIK": (960, 575, 0),
    "HYT": (960, 230, 1),
    "Jahsik": (1239, 270, 6),
    "AZ SOUND": (1454, 379, 6),
    "La Mala": (1556, 533, 3),
    "Stone Vybz": (1521, 697, 3),
    "Flémo Santana": (1358, 833, 5),
    "LaTrelle": (1104, 910, 4),
    "Pompis": (816, 910, 5),
    "Dasinga": (562, 833, 5),
    "Nesty Manhimselff": (399, 697, 4),
    "Brigistone": (364, 533, 5),
    "Banos": (466, 379, 2),
    "Donfly": (681, 270, 2),
}
NET_EDGES = [
    ("LYPHIK", "HYT", "Yana · Yana 2", 1), ("LYPHIK", "Donfly", "Guest Stars · Malus", 2),
    ("LYPHIK", "Banos", "Malus", 2), ("LYPHIK", "La Mala", "Renta · Malus", 3),
    ("LYPHIK", "Stone Vybz", "Diss · Encaisser", 3), ("LYPHIK", "Nesty Manhimselff", "Focus", 4),
    ("LYPHIK", "LaTrelle", "Impulsif", 4), ("LYPHIK", "Brigistone", "La zone", 5),
    ("LYPHIK", "Flémo Santana", "Scream", 5), ("LYPHIK", "Dasinga", "Bullets", 5),
    ("LYPHIK", "Pompis", "Everyday", 5), ("LYPHIK", "Jahsik", "Bad Life", 6),
    ("LYPHIK", "AZ SOUND", "Eveil", 6),
    # écosystème (projets communs documentés, pas de relations personnelles)
    ("HYT", "Donfly", "", 6), ("HYT", "Jahsik", "", 6), ("HYT", "La Mala", "", 6), ("HYT", "Stone Vybz", "", 6),
    ("AZ SOUND", "Jahsik", "", 6), ("HYT", "Pompis", "", 6),
]


def scene_network(ctx, tl, dur, data, env):
    gfx_bg(ctx, env["t"], "night", 0.6)
    a = fade_in_out(tl, dur, 0.25, 0.25)
    step = data.get("step", 0)
    for (n1, n2, lab, s) in NET_EDGES:
        if s > step:
            continue
        eco = lab == ""
        ea = a * (ease_out(prog(tl, 0.1, 0.8)) if s == step else 1.0)
        x1, y1, _ = NET_NODES[n1]
        x2, y2, _ = NET_NODES[n2]
        ctx.move_to(x1, y1)
        if s == step:
            u = ease_out(prog(tl, 0.1, 0.9))
            ctx.line_to(x1 + (x2 - x1) * u, y1 + (y2 - y1) * u)
        else:
            ctx.line_to(x2, y2)
        ctx.set_line_width(2 if eco else 4)
        if eco:
            ctx.set_dash([8, 8])
        set_src(ctx, (P("blue") if eco else P("gold"))[:3] + ((0.55 if eco else 0.8) * ea,))
        ctx.stroke()
        ctx.set_dash([])
        if lab:
            mx, my = x1 + (x2 - x1) * 0.58, y1 + (y2 - y1) * 0.58
            text(ctx, lab, mx, my - 10, 17, P("white", 0.65 * ea), "semibold", "center", family="Inter")
    for name, (x, y, s) in NET_NODES.items():
        if s > step:
            continue
        p = ease_back(prog(tl, 0.0, 0.5)) if s == step else 1.0
        main = name == "LYPHIK"
        hub = name in ("HYT", "AZ SOUND")
        r = (92 if main else (70 if hub else 52)) * p
        ctx.arc(x, y, r, 0, 6.3)
        set_src(ctx, (P("red") if main else (P("green2") if hub else P("night")))[:3] + (0.95 * a,))
        ctx.fill_preserve()
        ctx.set_line_width(4)
        set_src(ctx, P("gold", a))
        ctx.stroke()
        size = 30 if main else (24 if hub else 19)
        lines = name.split(" ") if len(name) > 10 else [name]
        for i, ln in enumerate(lines):
            text(ctx, ln, x, y + 8 + (i - (len(lines) - 1) / 2) * 22, size * p, P("white", a), "black" if main else "bold", "center")
    if step >= 6:
        b = ease_out(prog(tl, 0.8, 1.4)) * a
        rrect(ctx, 96, 980, 740, 44, 6)
        set_src(ctx, P("night", 0.85 * b))
        ctx.fill()
        ctx.move_to(116, 1002)
        ctx.line_to(170, 1002)
        ctx.set_line_width(3)
        ctx.set_dash([8, 8])
        set_src(ctx, P("blue", b))
        ctx.stroke()
        ctx.set_dash([])
        text(ctx, "Autres projets communs (albums HYT, compilation AZ SOUND)", 184, 1009, 18, P("white", 0.8 * b), "medium", family="Inter")
    kicker(ctx, "FEATURINGS & COLLABORATIONS", 96, 120, a)
    text(ctx, "Projets documentés uniquement — aucune relation personnelle supposée", 1824, 132, 18, P("white", 0.55 * a), "medium", "right", family="Inter")


def scene_press(ctx, tl, dur, data, env):
    gfx_bg(ctx, env["t"], "night", 0.6)
    a = fade_in_out(tl, dur)
    p = ease_out(prog(tl, 0, 0.6))
    ctx.save()
    ctx.translate(W / 2, 520)
    ctx.rotate(-0.025 * p)
    ctx.translate(-560, -300 + (1 - p) * 80)
    rrect(ctx, 0, 0, 1120, 560, 10)
    set_src(ctx, hexc("#F3EFE6", a))
    ctx.fill()
    text(ctx, data["outlet"].upper(), 50, 80, 46, hexc("#151515", a), "black", tracking=0.05)
    text(ctx, data["date"], 1070, 80, 24, hexc("#555555", a), "semibold", "right", family="Inter")
    ctx.rectangle(50, 104, 1020, 3)
    set_src(ctx, hexc("#151515", a))
    ctx.fill()
    for i, ln in enumerate(wrap(ctx, data["headline"], 52, 1000, "black", family="Inter Display")):
        text(ctx, ln, 50, 190 + i * 64, 52, hexc("#101010", a), "black")
    text(ctx, "Par " + data["author"], 50, 360, 24, hexc("#555555", a), "medium", family="Inter")
    for k in range(4):
        ctx.rectangle(50, 400 + k * 30, 1020 - (k == 3) * 400, 12)
    set_src(ctx, hexc("#D5D0C6", a))
    ctx.fill()
    ctx.restore()
    if data.get("stat"):
        b = ease_back(prog(tl, 0.8, 1.3)) * a
        ctx.save()
        ctx.translate(1520, 820)
        ctx.rotate(0.06)
        ctx.scale(max(0.01, b), max(0.01, b))
        rrect(ctx, -230, -60, 460, 120, 12)
        set_src(ctx, P("red", a))
        ctx.fill()
        text(ctx, data["stat"], 0, 14, 40, P("white", a), "black", "center")
        ctx.restore()
    source_line(ctx, f"{data['outlet']}, {data['date']} — article de {data['author']}", a)


def scene_persona(ctx, tl, dur, data, env):
    gfx_bg(ctx, env["t"], "night", 0.5)
    a = fade_in_out(tl, dur)
    rv = data.get("reveal_right")
    for side, (title, items, col) in enumerate(((data["left"], data["left_items"], "gold"),
                                                (data["right"], data["right_items"], "blue"))):
        x = 200 + side * 820
        sa = a * (1.0 if side == 0 or rv else 0.25 + 0.75 * ease_out(prog(tl, 1.5, 2.2)) * 0)
        if side == 1 and not rv:
            sa = a * 0.35
        p = ease_out(prog(tl, 0.1 + side * 0.3, 0.7 + side * 0.3))
        rrect(ctx, x, 240, 700, 600, 16)
        set_src(ctx, P("ink", 0.85 * sa))
        ctx.fill()
        ctx.rectangle(x, 240, 700, 10)
        set_src(ctx, P(col, sa))
        ctx.fill()
        text(ctx, title, x + 50, 340, 58, P(col, sa * p), "black", tracking=0.04)
        for i, it in enumerate(items):
            ia = ease_out(prog(tl, 0.5 + i * 0.3 + side * 0.4, 0.9 + i * 0.3 + side * 0.4)) * sa
            ctx.arc(x + 66, 444 + i * 100, 10, 0, 6.3)
            set_src(ctx, P(col, ia))
            ctx.fill()
            text(ctx, it, x + 100, 456 + i * 100, 44, P("white", ia), "bold")
    text(ctx, "VS", W / 2 + 10, 560, 60, P("red", a), "black", "center")


def scene_factcheck(ctx, tl, dur, data, env):
    gfx_bg(ctx, env["t"], "night", 0.6)
    a = fade_in_out(tl, dur)
    kicker(ctx, "FACT-CHECK 973", 334, 240, a, "blue")
    for i, (claim, status) in enumerate(data["items"]):
        ia = ease_out(prog(tl, 0.3 + i * 0.45, 0.8 + i * 0.45)) * a
        y = 330 + i * 160
        rrect(ctx, 320, y, 1440, 124, 12)
        set_src(ctx, P("ink", 0.9 * ia))
        ctx.fill()
        text(ctx, claim, 370, y + 78, 40, P("white", ia), "bold")
        ok = status == "CONFIRMÉ"
        sb = ease_back(prog(tl, 0.6 + i * 0.45, 1.0 + i * 0.45))
        ctx.save()
        ctx.translate(1600, y + 65)
        ctx.scale(max(0.01, sb), max(0.01, sb))
        rrect(ctx, -130, -34, 260, 68, 34)
        set_src(ctx, (P("green2") if ok else P("gold"))[:3] + (ia,))
        ctx.fill()
        text(ctx, ("✓ " if ok else "≈ ") + status, 0, 12, 28, P("night" if not ok else "white", ia), "black", "center")
        ctx.restore()
    text(ctx, "CONFIRMÉ = source indépendante  ·  DÉCLARÉ = affirmé par l'artiste (biographie officielle)", 334, 860, 24, P("white", 0.65 * a), "medium", family="Inter")
    source_line(ctx, "Bizouk (page de l'événement, 25/12/2021) · biographie officielle Spotify", a)


def scene_badlife(ctx, tl, dur, data, env):
    t = env["t"]
    ph = data.get("phase", 0)
    a = fade_in_out(tl, dur, 0.2, 0.3)
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(lin(0, 0, 0, H, [(0, hexc("#080202")), (0.6, hexc("#3A0705")), (1, hexc("#8E1A0E"))]))
    ctx.fill()
    # lueur de braises
    ctx.set_source(rad(W / 2, H + 200, 50, 1100, [(0, (1, 0.45, 0.1, 0.55 + 0.1 * math.sin(t * 6))), (1, (1, 0.3, 0.05, 0))]))
    ctx.paint()
    r = random.Random(77)
    for k in range(120):
        sp = r.uniform(60, 220)
        x = (r.uniform(0, W) + math.sin(t * r.uniform(0.5, 1.5) + k) * 40) % W
        y = H - ((t * sp + r.uniform(0, H)) % (H + 100))
        ctx.arc(x, y, r.uniform(1.2, 4.2), 0, 6.3)
        ctx.set_source_rgba(1, r.uniform(0.5, 0.85), 0.2, r.uniform(0.4, 0.95) * a)
        ctx.fill()
    # titre
    p = ease_back(prog(tl, 0.1, 0.8), 1.4)
    for blur, al in ((14, 0.15), (7, 0.25), (0, 1.0)):
        ctx.save()
        ctx.translate(W / 2, 560)
        ctx.scale(0.7 + 0.3 * p, 0.7 + 0.3 * p)
        from draw import font
        font(ctx, 250, "black")
        tw = ctx.text_extents("BAD LIFE").x_advance
        ctx.move_to(-tw / 2, 0)
        ctx.text_path("BAD LIFE")
        if blur:
            ctx.set_line_width(blur)
            ctx.set_source_rgba(1, 0.6, 0.15, al * a * p)
            ctx.stroke()
        else:
            ctx.set_source(lin(0, -200, 0, 10, [(0, hexc("#FFF1C4", a)), (0.5, hexc("#F9BF3B", a)), (1, hexc("#B5650F", a))]))
            ctx.fill()
        ctx.restore()
    b = ease_out(prog(tl, 0.6, 1.2)) * a
    text(ctx, "LYPHIK  feat.  JAHSIK", W / 2, 680, 54, P("white", b), "black", "center", tracking=0.18)
    c = ease_out(prog(tl, 1.0, 1.6)) * a
    text(ctx, "SINGLE  ·  09.11.2026  ·  LABEL P.M.L", W / 2, 750, 30, P("gold", c), "bold", "center", tracking=0.3)
    if ph >= 1:
        d = ease_out(prog(tl, 0.4, 1.0)) * a
        text(ctx, "Jahsik : déjà présent sur « Yana » (HYT, 2020) et « Eveil » (AZ SOUND, 2023)", W / 2, 830, 28,
             P("white", 0.8 * d), "medium", "center", family="Inter")
    if ph >= 2:
        d = ease_out(prog(tl, 0.3, 0.9)) * a
        rrect(ctx, W / 2 - 420, 860, 840, 84, 42)
        set_src(ctx, P("gold", d))
        ctx.fill()
        text(ctx, "▶  ÉCOUTE « BAD LIFE » MAINTENANT", W / 2, 914, 34, P("night", d), "black", "center", tracking=0.06)
    # bandeaux de drapeau abstraits (vert/jaune + étoile rouge stylisée)
    ctx.rectangle(0, 0, W, 10)
    set_src(ctx, P("green2", a))
    ctx.fill()
    ctx.rectangle(0, 10, W, 6)
    set_src(ctx, P("gold", a))
    ctx.fill()
    source_line(ctx, "Spotify / Deezer : sortie le 09/11/2026, label « P.M.L » · YouTube : visualizer + street clip", a)


def scene_paradox(ctx, tl, dur, data, env):
    gfx_bg(ctx, env["t"], "night", 0.6)
    a = fade_in_out(tl, dur)
    ph = data.get("phase", 0)
    p1 = ease_out(prog(tl, 0.1, 1.2)) if ph == 0 else 1.0
    text(ctx, "+ " + ("1,6 M" if p1 >= 1 else f"{1.6 * p1:.1f} M".replace(".", ",")), 520, 520, 190, P("gold", a), "black", "center")
    text(ctx, "VUES YOUTUBE RECENSÉES", 520, 600, 30, P("white", a), "bold", "center", tracking=0.2)
    text(ctx, "sur les vidéos que nous avons pu relever", 520, 645, 22, P("white", 0.6 * a), "medium", "center", family="Inter")
    b = (ease_out(prog(tl, 0.2, 1.0)) if ph == 1 else 0.0) * a
    text(ctx, "VS", W / 2, 520, 70, P("red", max(b, 0.25 * a)), "black", "center")
    p2 = ease_out(prog(tl, 0.3, 1.4))
    text(ctx, str(int(388 * p2)) if ph == 1 else "?", 1400, 520, 190, P("blue", b if ph == 1 else 0.25 * a), "black", "center")
    text(ctx, "AUDITEURS MENSUELS SPOTIFY", 1400, 600, 30, P("white", b), "bold", "center", tracking=0.2)
    text(ctx, "au 12/11/2026", 1400, 645, 22, P("white", 0.6 * b), "medium", "center", family="Inter")
    kicker(ctx, "LE PARADOXE", 96, 120, a, "red")
    source_line(ctx, "YouTube (cumul des vidéos relevées, ≈ 1 617 000) · Spotify (388 auditeurs mensuels)", a)


def scene_playlist(ctx, tl, dur, data, env):
    gfx_bg(ctx, env["t"], "green", 0.6)
    a = fade_in_out(tl, dur)
    kicker(ctx, "TA PLAYLIST DÉCOUVERTE", 560, 200, a)
    items = data["items"]
    cur = min(len(items) - 1, int(tl / max(0.1, dur / len(items))))
    for i, it in enumerate(items):
        ia = ease_out(prog(tl, 0.1 + i * 0.15, 0.4 + i * 0.15)) * a
        y = 290 + i * 120
        hl = i == cur
        rrect(ctx, 560, y, 800, 96, 14)
        set_src(ctx, (P("gold") if hl else P("ink"))[:3] + (0.92 * ia,))
        ctx.fill()
        ctx.arc(620, y + 48, 26, 0, 6.3)
        set_src(ctx, (P("night") if hl else P("gold"))[:3] + (ia,))
        ctx.fill()
        ctx.move_to(612, y + 34)
        ctx.line_to(634, y + 48)
        ctx.line_to(612, y + 62)
        ctx.close_path()
        set_src(ctx, (P("gold") if hl else P("night"))[:3] + (ia,))
        ctx.fill()
        text(ctx, it, 680, y + 64, 44, (P("night") if hl else P("white"))[:3] + (ia,), "black")
        text(ctx, f"0{i + 1}", 1320, y + 62, 30, (P("night") if hl else P("gold"))[:3] + (ia * 0.8,), "black", "right")
        if hl:
            for k in range(5):
                hh = 10 + 26 * abs(math.sin(env["t"] * 6 + k))
                ctx.rectangle(1180 + k * 14, y + 48 - hh / 2, 8, hh)
            set_src(ctx, P("night", ia))
            ctx.fill()
    source_line(ctx, "Spotify · YouTube · liens en description", a)


def scene_cta(ctx, tl, dur, data, env):
    gfx_bg(ctx, env["t"], "red", 0.7)
    a = fade_in_out(tl, dur)
    p = ease_back(prog(tl, 0.2, 0.8))
    clicked = tl > 1.6
    ctx.save()
    ctx.translate(W / 2, 400)
    ctx.scale(p * (0.94 if 1.6 < tl < 1.8 else 1.0), p * (0.94 if 1.6 < tl < 1.8 else 1.0))
    rrect(ctx, -330, -70, 660, 140, 70)
    set_src(ctx, (P("night") if clicked else P("red"))[:3] + (a,))
    ctx.fill()
    ctx.set_line_width(4)
    set_src(ctx, P("gold", a))
    rrect(ctx, -330, -70, 660, 140, 70)
    ctx.stroke()
    text(ctx, "ABONNÉ ✓" if clicked else "S'ABONNER", 0, 20, 58, P("white", a), "black", "center", tracking=0.06)
    ctx.restore()
    b = ease_out(prog(tl, 0.8, 1.4)) * a
    text(ctx, "Liens de Lyphik et sources : en description", W / 2, 590, 40, P("white", b), "bold", "center")
    c = ease_out(prog(tl, 1.4, 2.0)) * a
    rrect(ctx, W / 2 - 620, 650, 1240, 110, 16)
    set_src(ctx, P("ink", 0.85 * c))
    ctx.fill()
    text(ctx, "💬", W / 2 - 560, 724, 44, P("white", c), "bold", family="Noto Color Emoji")
    text(ctx, "En commentaire : quel artiste d'ici pour l'épisode 2 ?", W / 2 + 30, 722, 38, P("gold", c), "black", "center")


def scene_cold_open_overlay(ctx, tl, dur, data, env):
    a = fade_in_out(tl, dur + 0.6, 0.6, 0.6)
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(lin(0, 0, 0, H, [(0, (0, 0, 0, 0.0)), (0.6, (0, 0, 0, 0.0)), (1, (0, 0, 0, 0.55 * a))]))
    ctx.fill()
    kicker(ctx, data["kicker"], 140, 880, a)
    text(ctx, data["line"], 140, 960, 50, P("white", a), "bold")
    # fondu depuis le noir
    ctx.set_source_rgba(0, 0, 0, 1 - ease_out(prog(tl, 0, 1.2)))
    ctx.paint()


def scene_disclaimer_overlay(ctx, tl, dur, data, env):
    a = fade_in_out(tl, dur, 0.4, 0.4)
    p = ease_out(prog(tl, 0, 0.5))
    y = 760 + (1 - p) * 60
    rrect(ctx, 260, y, 1400, 210, 18)
    set_src(ctx, P("night", 0.9 * a))
    ctx.fill()
    ctx.rectangle(260, y, 12, 210)
    set_src(ctx, P("blue", a))
    ctx.fill()
    kicker(ctx, "TRANSPARENCE", 310, y + 62, a, "blue")
    text(ctx, "Kenzo et Maëva sont des personnages animés fictifs.", 310, y + 128, 38, P("white", a), "bold")
    text(ctx, "Ils n'ont pas rencontré Lyphik. Infos vérifiées · sources en description.", 310, y + 180, 30, P("gold", a), "semibold", family="Inter")


def scene_end_logo(ctx, tl, dur, data, env):
    gfx_bg(ctx, tl, "night", 1.0)
    a = fade_in_out(tl, dur, 0.4, 1.2)
    rot = (1 - ease_out(prog(tl, 0.1, 1.0))) * -math.pi * 0.6
    logo_3d(ctx, W / 2, 470, 240, tl, rot, a, sweep=prog(tl, 1.0, 2.0))
    text(ctx, "CULTURE", W / 2, 550, 54, P("white", a), "black", "center", tracking=0.42)
    b = ease_out(prog(tl, 0.8, 1.4)) * a
    text(ctx, "Les talents d'ici méritent une audience mondiale.", W / 2, 630, 32, P("gold", b), "semibold", "center", family="Inter")
    c = ease_out(prog(tl, 1.4, 2.0)) * a
    text(ctx, "Épisode 2 très bientôt · Abonne-toi", W / 2, 720, 30, P("white", 0.85 * c), "bold", "center")
    d = ease_out(prog(tl, 2.0, 2.6)) * a
    for i, ln in enumerate([
        "Une production 973 Culture · Animation, décor et musique originaux",
        "Personnages fictifs · Aucune interview réelle · Sources publiques citées en description",
        "Musique de Lyphik et clips : propriété de leurs ayants droit",
    ]):
        text(ctx, ln, W / 2, 880 + i * 34, 20, P("white", 0.55 * d), "medium", "center", family="Inter")


SCENES = {
    "logo": scene_logo, "name_reveal": scene_name_reveal, "stat": scene_stat, "map": scene_map,
    "quote": scene_quote, "pml": scene_pml, "timeline": scene_timeline, "clip_slot": scene_clip_slot,
    "cards": scene_cards, "ep": scene_ep, "network": scene_network, "press": scene_press,
    "persona": scene_persona, "factcheck": scene_factcheck, "badlife": scene_badlife,
    "paradox": scene_paradox, "playlist": scene_playlist, "cta": scene_cta, "end_logo": scene_end_logo,
}
