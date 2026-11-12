"""Étapes 6/8 — Compositeur : caméra virtuelle, comportement des personnages, habillage.

Une image = f(t). Toutes les animations sont des fonctions déterministes du temps,
ce qui permet un rendu parallèle par segments sans dérive entre les images.
"""
import bisect
import math
import random

import cairo

import characters as ch
import setdesign as sd
from config import FPS, H, W
from draw import P, clamp, ease_in_out, ease_out, lin, noise1, prog, rrect, set_src, text

CAMS = {
    "set_wide": (960, 540, 1.0),
    "two_shot": (960, 478, 1.62),
    "over_K": (900, 470, 1.9),
    "over_M": (1020, 470, 1.9),
    "single_K": (775, 494, 2.85),
    "single_M": (1145, 494, 2.85),
    "pip_K": (sd.CHAR_X["K"], 420, 4.4),
    "pip_M": (sd.CHAR_X["M"], 420, 4.4),
}


class Director:
    """Calcule l'état de chaque personnage à l'instant t à partir de la timeline."""

    def __init__(self, tl):
        self.tl = tl
        self.beats = tl["beats"]
        self.starts = [b["start"] for b in self.beats]
        self.mouth = tl["mouth"]
        self.n = tl["nframes"]
        self.dur = tl["duration"]
        self.blinks = {}
        self.nods = {}
        for who, seed in (("K", 1), ("M", 2)):
            r = random.Random(seed)
            t, bl = 0.8, []
            while t < self.dur + 5:
                bl.append(t)
                t += r.uniform(2.2, 5.0)
                if r.random() < 0.15:
                    bl.append(t - 0.35)       # double clignement
            self.blinks[who] = sorted(bl)
        # hochements de tête de l'auditeur pendant que l'autre parle
        for who in ("K", "M"):
            r = random.Random(10 + ord(who))
            evs = []
            for b in self.beats:
                if b["type"] == "line" and b["who"] != who and b["end"] - b["start"] > 2.5:
                    k = int((b["end"] - b["start"]) / 3.2)
                    for i in range(max(1, k)):
                        evs.append(b["start"] + 1.0 + i * 3.2 + r.uniform(-0.4, 0.4))
            self.nods[who] = sorted(evs)

    def beat_at(self, t):
        i = bisect.bisect_right(self.starts, t) - 1
        return self.beats[max(0, i)]

    def speaking(self, who, t):
        b = self.beat_at(t)
        return b["type"] == "line" and b["who"] == who and t <= b["end"]

    def mouth_at(self, who, t):
        f = int(t * FPS)
        if 0 <= f < self.n:
            return self.mouth[who]["open"][f], self.mouth[who]["shape"][f]
        return 0.0, "closed"

    def activity(self, who, t, win=0.6):
        f0 = int((t - win) * FPS)
        f1 = int((t + win) * FPS)
        vals = self.mouth[who]["open"][max(0, f0):min(self.n, f1)]
        return sum(vals) / max(1, len(vals))

    def tod(self, t):
        return 0.04 + 0.92 * clamp(t / self.dur) ** 1.15

    def state(self, who, t):
        st = ch.default_state()
        other = "M" if who == "K" else "K"
        toward = 1 if who == "K" else -1         # direction du partenaire
        b = self.beat_at(t)
        op, shape = self.mouth_at(who, t)
        st["open"], st["shape"] = op, shape
        talking = self.speaking(who, t)
        # regards : l'orateur alterne caméra / partenaire, l'auditeur regarde l'orateur
        seg = 2.7
        i = int(t / seg)
        def look(k):
            r = random.Random(hash((who, k)) & 0xFFFF)
            return 1.0 if r.random() < 0.45 else 0.0
        u = (t % seg) / seg
        w = ease_in_out(prog(u, 0.85, 1.0))
        look_partner = look(i) * (1 - w) + look(i + 1) * w
        if talking:
            gx = toward * (0.15 + 0.6 * look_partner)
            yaw = toward * (0.08 + 0.32 * look_partner)
        else:
            other_talk = self.speaking(other, t)
            gx = toward * (0.75 if other_talk else 0.3)
            yaw = toward * (0.38 if other_talk else 0.15)
        st["gaze_x"] = gx + noise1(t * 0.7, ord(who)) * 0.06
        st["gaze_y"] = noise1(t * 0.5, ord(who) + 3) * 0.15
        st["yaw"] = yaw + noise1(t * 0.35, ord(who) + 5) * 0.05
        st["tilt"] = noise1(t * 0.3, ord(who) + 7) * 0.6 + (toward * 0.3 if not talking else 0)
        # clignements
        bl = self.blinks[who]
        j = bisect.bisect_right(bl, t) - 1
        if j >= 0:
            dt = t - bl[j]
            if dt < 0.17:
                st["blink"] = 1 - abs(dt - 0.085) / 0.085
        # hochements
        nd = self.nods[who]
        k = bisect.bisect_right(nd, t) - 1
        if k >= 0 and t - nd[k] < 0.7:
            st["nod"] = math.sin((t - nd[k]) / 0.7 * math.pi * 2) * 0.9
        if talking:
            st["nod"] += noise1(t * 2.3, ord(who) + 11) * 0.35 * op
        # émotions
        emo = b.get("emotion") if b["type"] == "line" else None
        base_smile = 0.5
        if emo == "laugh":
            st["smile"] = 0.95
            st["brow"] = 0.4
            st["nod"] += math.sin(t * 9) * 0.25
        elif emo == "tease":
            st["smile"] = 0.7 if who == b["who"] else 0.5
            st["brow"] = 0.7 if who == b["who"] else 0.2
        elif emo == "argue":
            st["brow"] = 0.6 if who == b["who"] else -0.2
            st["smile"] = 0.5
        elif emo == "smile":
            st["smile"] = 0.85
        else:
            st["smile"] = base_smile + (0.15 if talking else 0) + noise1(t * 0.2, ord(who)) * 0.08
            st["brow"] = (0.35 * op if talking else 0) + noise1(t * 0.4, ord(who) + 2) * 0.15
        # gestes : liés à l'intensité de parole, une main dominante par réplique
        act = self.activity(who, t)
        r = random.Random(b["id"] if b["type"] == "line" else "v")
        dominant = r.choice(["arm_r", "arm_l", "both"])
        g = clamp((act - 0.12) * 2.4) if talking else 0.0
        g = ease_in_out(g)
        if dominant == "both":
            st["arm_l"], st["arm_r"] = g * 0.7, g * 0.85
        else:
            st[dominant] = g
        st["arm_phase"] = t * 2.1 + ord(who)
        st["breath"] = math.sin(t * 1.5 + ord(who))
        st["lean"] = toward * (0.4 if talking else 0.15) + noise1(t * 0.25, ord(who) + 13) * 0.2
        st["light"] = self.tod(t)
        return st


def apply_cam(ctx, cam, depth):
    cx, cy, z = cam
    zf = 1 + (z - 1) * depth
    ctx.translate(W / 2, H / 2)
    ctx.scale(zf, zf)
    ctx.translate(-(960 + (cx - 960) * depth), -(540 + (cy - 540) * depth))


def cam_for(name, t_local, dur):
    cx, cy, z = CAMS[name]
    # lente poussée caméra + flottement « opérateur »
    u = clamp(t_local / max(dur, 0.1))
    z *= 0.985 + 0.03 * ease_in_out(u)
    cx += noise1(t_local * 0.4, 1) * 4 / z * 2
    cy += noise1(t_local * 0.33, 2) * 3 / z * 2
    return (cx, cy, z)


def draw_background(ctx, cam, tod, t, blur_k):
    """couches lointaines, rendues en basse résolution pour simuler la profondeur de champ"""
    if blur_k <= 1:
        _bg_layers(ctx, cam, tod, t)
        return
    sw, sh = int(W / blur_k) + 2, int(H / blur_k) + 2
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, sw, sh)
    c2 = cairo.Context(surf)
    c2.scale(1 / blur_k, 1 / blur_k)
    _bg_layers(c2, cam, tod, t)
    ctx.save()
    ctx.scale(blur_k, blur_k)
    ctx.set_source_surface(surf, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_BILINEAR)
    ctx.paint()
    ctx.restore()


def _bg_layers(ctx, cam, tod, t):
    for depth, fn in ((0.05, sd.draw_sky), (0.15, sd.draw_skyline)):
        ctx.save()
        apply_cam(ctx, cam, depth)
        fn(ctx, tod, t)
        ctx.restore()
    ctx.save()
    apply_cam(ctx, cam, 0.6)
    sd.draw_ground(ctx, tod, t)
    ctx.restore()
    for p in sd.PALMS:
        ctx.save()
        apply_cam(ctx, cam, p["depth"])
        sd.draw_palm(ctx, p, tod, t)
        ctx.restore()


def draw_set_shot(ctx, director, cam, t, chars_visible=("K", "M")):
    tod = director.tod(t)
    z = cam[2]
    blur_k = 1 if z < 1.3 else (2 if z < 2.5 else 4)
    draw_background(ctx, cam, tod, t, blur_k)
    ctx.save()
    apply_cam(ctx, cam, 1.0)
    sd.draw_stage(ctx, tod, t)
    for who in chars_visible:
        st = director.state(who, t)
        ctx.save()
        ctx.translate(sd.CHAR_X[who], sd.SEAT_Y)
        ctx.scale(sd.CHAR_SCALE, sd.CHAR_SCALE)
        ch.draw_character(ctx, who, st, t)
        ch.draw_microphone(ctx, -1 if who == "K" else 1, tod)
        ctx.restore()
    ctx.restore()
    # amorces de feuillage en plan serré
    ctx.save()
    apply_cam(ctx, cam, 1.3)
    sd.draw_foreground(ctx, tod, t, clamp((z - 1.6) / 1.5))
    ctx.restore()
    # étalonnage : vignette + teinte crépuscule
    ctx.set_source(cairo.RadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.95))
    g = ctx.get_source()
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.42)
    ctx.paint()
    ctx.set_source_rgba(0.98, 0.6, 0.25, 0.06 * (1 - tod))
    ctx.paint()
    ctx.set_source_rgba(0.1, 0.2, 0.5, 0.08 * tod)
    ctx.paint()


def draw_pip(ctx, director, who, t, x, y, r):
    """médaillon : gros plan du personnage qui parle (pendant les habillages graphiques)"""
    ctx.save()
    ctx.arc(x, y, r + 6, 0, 2 * math.pi)
    set_src(ctx, P("gold"))
    ctx.fill()
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.clip()
    ctx.translate(x - W / 2 * (2 * r / H), y - r)
    ctx.scale(2 * r / H, 2 * r / H)
    cam = CAMS[f"pip_{who}"]
    tod = director.tod(t)
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(lin(0, 0, 0, H, [(0, (0.12, 0.25, 0.22, 1)), (1, (0.04, 0.08, 0.08, 1))]))
    ctx.fill()
    ctx.save()
    apply_cam(ctx, cam, 1.0)
    st = director.state(who, t)
    ctx.translate(sd.CHAR_X[who], sd.SEAT_Y)
    ctx.scale(sd.CHAR_SCALE, sd.CHAR_SCALE)
    ch.draw_character(ctx, who, st, t)
    ctx.restore()
    ctx.restore()
    name = "KENZO" if who == "K" else "MAËVA"
    rrect(ctx, x - 62, y + r - 4, 124, 30, 15)
    set_src(ctx, P("night", 0.92))
    ctx.fill()
    text(ctx, name, x, y + r + 17, 15, P("white"), "bold", "center", tracking=0.18)


def lower_third(ctx, who, t_local):
    if t_local > 4.6:
        return
    a_in = ease_out(prog(t_local, 0.15, 0.7))
    a_out = 1 - ease_out(prog(t_local, 4.0, 4.6))
    a = a_in * a_out
    name = "KENZO" if who == "K" else "MAËVA"
    role = "Co-animateur · 973 Culture" if who == "K" else "Co-animatrice · 973 Culture"
    x = 120 if who == "K" else W - 120 - 520
    y = 840
    ctx.save()
    ctx.translate((1 - a_in) * (-60 if who == "K" else 60), 0)
    ctx.rectangle(x, y, 10, 104)
    set_src(ctx, P("gold", a))
    ctx.fill()
    rrect(ctx, x + 18, y, 520 * a_in, 64, 4)
    set_src(ctx, P("night", 0.88 * a))
    ctx.fill()
    text(ctx, name, x + 40, y + 46, 38, P("white", a), "black", tracking=0.06)
    rrect(ctx, x + 18, y + 70, 420 * a_in, 34, 4)
    set_src(ctx, P("green", 0.95 * a))
    ctx.fill()
    text(ctx, role, x + 36, y + 94, 19, P("white", a), "semibold")
    ctx.restore()


def bug(ctx, alpha=0.85):
    """logo discret en haut à droite"""
    text(ctx, "973", W - 210, 78, 34, P("gold", alpha), "black")
    text(ctx, "CULTURE", W - 140, 78, 15, P("white", alpha), "bold", tracking=0.3)
    ctx.rectangle(W - 210, 88, 162, 3)
    set_src(ctx, P("red", alpha))
    ctx.fill()
