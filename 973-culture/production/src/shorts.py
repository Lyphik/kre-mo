"""Étape 10 — Formats courts : Shorts verticaux 9:16 et bande-annonce 16:9 du programme.

Chaque format court est un montage de répliques du master (aucun texte nouveau, aucune
information hors dossier). Plans plateau : recadrage vertical net sur l'orateur (rendu
haute définition puis découpe). Habillages : présentés en carte 16:9. Sous-titres
dynamiques incrustés (mot courant surligné). Audio : voix + lit musical continu, -14 LUFS.

Usage : python shorts.py [id ...]     (sans argument : tous les formats)
"""
import json
import math
import subprocess
import sys
import wave
from multiprocessing import Process

import cairo
import numpy as np

import setdesign as sd
from compositor import CAMS, cam_for
from config import BUILD, DELIVER, FPS, H, SR, W
from draw import P, ease_out, lin, prog, rrect, set_src, text, text_width, wrap
from render import Renderer
from subtitles import split_text, tc

SHORTS = [
    {"id": "short1_lyphik_en_55s", "vertical": True, "title": ["LYPHIK", "EN 55 SECONDES"],
     "ranges": [("S0-02", "S0-04"), ("S1-06", "S1-07"), ("S2-08", "S2-08"),
                ("S3-01", "S3-01"), ("S6-01", "S6-02"), ("S7-04", "S7-04")]},
    {"id": "short2_le_paradoxe", "vertical": True, "title": ["1,6 MILLION DE VUES…", "ET 388 AUDITEURS ?"],
     "ranges": [("S0-02", "S0-03"), ("S7-01", "S7-03")]},
    {"id": "short3_pa_mele", "vertical": True, "title": ["P.M.L :", "ÇA VEUT DIRE QUOI ?"],
     "ranges": [("S2-04", "S2-06"), ("S4-08", "S4-10")]},
    {"id": "short4_le_debat", "vertical": True, "title": ["TROP POLYVALENT", "POUR PERCER ?"],
     "ranges": [("S3-10", "S3-13")]},
    {"id": "short5_bad_life", "vertical": True, "title": ["BAD LIFE", "LYPHIK feat. JAHSIK"],
     "ranges": [("S6-01", "S6-04"), ("S6-07", "S6-08")]},
    {"id": "teaser_programme_16x9", "vertical": False, "title": ["973 CULTURE", "LE PODCAST"],
     "ranges": [("S0-05", "S0-05"), ("S1-01", "S1-03"), ("S5-08", "S5-09"), ("S7-08", "S7-08")]},
]
VW, VH = 1080, 1920
PAD = 0.12


def build_segments(tl, spec):
    idx = {b["id"]: i for i, b in enumerate(tl["beats"])}
    segs = []
    for a, b in spec["ranges"]:
        ba, bb = tl["beats"][idx[a]], tl["beats"][idx[b]]
        segs.append((max(0, ba["start"] - PAD), bb["end"] + PAD, idx[a], idx[b]))
    return segs


def src_time(segs, t):
    acc = 0.0
    for s, e, *_ in segs:
        d = e - s
        if t < acc + d:
            return s + (t - acc)
        acc += d
    return segs[-1][1]


def caption_cues(tl, segs):
    """sous-titres (avec mots) dans le temps du Short"""
    cues = []
    acc = 0.0
    for s, e, ia, ib in segs:
        for b in tl["beats"][ia:ib + 1]:
            if b["type"] != "line":
                continue
            parts = split_text(b["text"])
            total = sum(len(p) for p in parts)
            t = b["start"]
            for p in parts:
                d = (b["end"] - b["start"]) * len(p) / total
                cues.append((acc + t - s, acc + t + d - s, p))
                t += d
        acc += e - s
    return cues


class ShortRenderer:
    def __init__(self, spec):
        self.spec = spec
        self.r = Renderer()
        self.tl = self.r.tl
        self.segs = build_segments(self.tl, spec)
        self.dur = sum(e - s for s, e, *_ in self.segs)
        self.cues = caption_cues(self.tl, self.segs)
        self.hd = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(W * VH / H) + 2, VH)    # 3414 x 1920
        self.base = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)

    def speaker_screen_x(self, sh, ts):
        """abscisse écran (repère 1920) du personnage à cadrer"""
        b = self.r.beats[sh["beat"]]
        who = b.get("who") or "K"
        if sh["cam"].startswith("single_"):
            who = sh["cam"][-1]
        cx, cy, z = cam_for(sh["cam"], ts - sh["start"], sh["end"] - sh["start"])
        return W / 2 + (sd.CHAR_X[who] - cx) * z

    def frame(self, ctx, t):
        ts = src_time(self.segs, t)
        sh = self.r.shot_at(ts)
        if not self.spec["vertical"]:
            self.r.frame(ctx, ts)
            self.captions(ctx, t, W, H, 0.80)
            return
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()
        cam_shot = sh["kind"] == "cam" or sh.get("scene") == "disclaimer"
        if cam_shot:
            c2 = cairo.Context(self.hd)
            c2.scale(VH / H, VH / H)
            c2.set_source_rgb(0, 0, 0)
            c2.paint()
            self.r.frame(c2, ts)
            if sh["kind"] == "cam":
                x = self.speaker_screen_x(sh, ts) * VH / H
            else:
                x = self.hd.get_width() / 2
            x0 = min(max(0, x - VW / 2), self.hd.get_width() - VW)
            ctx.set_source_surface(self.hd, -x0, 0)
            ctx.paint()
        else:
            c3 = cairo.Context(self.base)
            c3.set_source_rgb(0, 0, 0)
            c3.paint()
            self.r.frame(c3, ts)
            # fond : image agrandie, assombrie et adoucie
            small = cairo.ImageSurface(cairo.FORMAT_RGB24, 96, 54)
            cs = cairo.Context(small)
            cs.scale(96 / W, 54 / H)
            cs.set_source_surface(self.base, 0, 0)
            cs.paint()
            ctx.save()
            k = VH / 54
            ctx.translate(-(96 * k - VW) / 2, 0)
            ctx.scale(k, k)
            ctx.set_source_surface(small, 0, 0)
            ctx.get_source().set_filter(cairo.FILTER_GOOD)
            ctx.paint()
            ctx.restore()
            ctx.set_source_rgba(0, 0, 0, 0.45)
            ctx.paint()
            # carte 16:9
            ctx.save()
            ctx.translate(0, 600)
            ctx.scale(VW / W, VW / W)
            ctx.set_source_surface(self.base, 0, 0)
            ctx.paint()
            ctx.restore()
            ctx.rectangle(0, 596, VW, 4)
            ctx.rectangle(0, 600 + VW * H / W, VW, 4)
            set_src(ctx, P("gold"))
            ctx.fill()
        self.header(ctx, t)
        self.captions(ctx, t, VW, VH, 0.70)
        self.footer(ctx, t)

    def header(self, ctx, t):
        a = ease_out(prog(t, 0.0, 0.5))
        ctx.rectangle(0, 0, VW, 330)
        ctx.set_source(lin(0, 0, 0, 330, [(0, (0, 0, 0, 0.85)), (1, (0, 0, 0, 0))]))
        ctx.fill()
        text(ctx, "973", 60, 110, 56, P("gold", a), "black")
        text(ctx, "CULTURE", 186, 110, 22, P("white", a), "bold", tracking=0.3)
        for i, ln in enumerate(self.spec["title"]):
            w = text_width(ctx, ln, 64, "black")
            sz = 64 if w < VW - 120 else 64 * (VW - 120) / w
            rrect(ctx, 50, 150 + i * 86, min(VW - 100, text_width(ctx, ln, sz, "black") + 40), 76, 8)
            set_src(ctx, (P("gold") if i == 0 else P("night", 0.9))[:3] + (a,))
            ctx.fill()
            text(ctx, ln, 70, 212 + i * 86, sz, (P("night") if i == 0 else P("white"))[:3] + (a,), "black")

    def captions(self, ctx, t, w, h, yrel):
        cur = [c for c in self.cues if c[0] <= t < c[1]]
        if not cur:
            return
        a0, a1, s = cur[0]
        size = 58 if self.spec["vertical"] else 46
        lines = wrap(ctx, s, size, w * 0.86, "black", family="Inter Display")
        words = s.split()
        k = int((t - a0) / max(0.01, a1 - a0) * len(words))
        y = h * yrel
        wi = 0
        for li, ln in enumerate(lines):
            lw = text_width(ctx, ln, size, "black")
            x = w / 2 - lw / 2
            yy = y + li * (size * 1.18)
            rrect(ctx, x - 20, yy - size * 0.95, lw + 40, size * 1.2, 10)
            set_src(ctx, P("night", 0.72))
            ctx.fill()
            for word in ln.split():
                col = P("gold") if wi == k else P("white")
                ww = text(ctx, word, x, yy, size, col, "black")
                x += ww + text_width(ctx, " ", size, "black")
                wi += 1

    def footer(self, ctx, t):
        ctx.rectangle(0, VH - 14, VW * t / self.dur, 14)
        set_src(ctx, P("gold"))
        ctx.fill()
        if t > self.dur - 2.6:
            a = ease_out(prog(t, self.dur - 2.6, self.dur - 2.1))
            rrect(ctx, 90, VH - 330, VW - 180, 150, 20)
            set_src(ctx, P("red", 0.95 * a))
            ctx.fill()
            text(ctx, "L'ÉPISODE COMPLET", VW / 2, VH - 262, 50, P("white", a), "black", "center")
            text(ctx, "sur la chaîne 973 Culture", VW / 2, VH - 210, 34, P("gold", a), "bold", "center")


def render_part(spec, f0, f1, out):
    sr_ = ShortRenderer(spec)
    w, h = (VW, VH) if spec["vertical"] else (W, H)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(surf)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-tune", "animation", "-crf", "20", "-x264-params", "aq-mode=3",
           "-pix_fmt", "yuv420p", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        ctx.save()
        sr_.frame(ctx, f / FPS)
        ctx.restore()
        surf.flush()
        p.stdin.write(bytes(surf.get_data()))
    p.stdin.close()
    p.wait()


def read(path):
    with wave.open(str(path)) as w_:
        ch = w_.getnchannels()
        a = np.frombuffer(w_.readframes(w_.getnframes()), dtype=np.int16).astype(np.float32) / 32767
    return a.reshape(-1, ch).T


def audio_for(spec, segs, out):
    voices = read(BUILD / "voices.wav")
    music = read(BUILD / "music.wav")
    parts = []
    fade = int(0.03 * SR)
    for s, e, *_ in segs:
        seg = voices[:, int(s * SR):int(e * SR)].copy()
        seg[:, :fade] *= np.linspace(0, 1, fade)
        seg[:, -fade:] *= np.linspace(1, 0, fade)
        parts.append(seg)
    v = np.concatenate(parts, axis=1)
    n = v.shape[1]
    tl = json.loads((BUILD / "timeline.json").read_text(encoding="utf-8"))
    drop = [b for b in tl["beats"] if b["id"] == "S0-05"][0]["start"]
    if spec["vertical"]:
        m = music[:, int(drop * SR):int(drop * SR) + n]
        if m.shape[1] < n:
            m = np.pad(m, ((0, 0), (0, n - m.shape[1])))
        env = (np.abs(v).mean(0) > 0.02).astype(np.float32)
        hop = 480
        e2 = np.array([env[k:k + hop].max() for k in range(0, n, hop)])
        sm, acc = np.zeros_like(e2), 0.0
        for k, x in enumerate(e2):
            acc += (x - acc) * (0.5 if x > acc else 0.04)
            sm[k] = acc
        duck = np.repeat(sm, hop)[:n]
        m = m * 0.6 * (1 - 0.7 * duck)
        m[:, -SR:] *= np.linspace(1, 0, SR)
        mix = v + m
    else:
        # bande-annonce : musique et effets du master sur les mêmes plages
        mixm = read(BUILD / "mix.wav")
        mix = np.concatenate([mixm[:, int(s * SR):int(e * SR)] for s, e, *_ in segs], axis=1)
    raw = BUILD / f"{spec['id']}_raw.wav"
    with wave.open(str(raw), "wb") as w_:
        w_.setnchannels(2)
        w_.setsampwidth(2)
        w_.setframerate(SR)
        w_.writeframes((np.clip(mix.T, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af",
                    "loudnorm=I=-14:TP=-1.0:LRA=11", "-ar", str(SR), str(out)], check=True)


def render_short(spec, workers=4):
    sr_ = ShortRenderer(spec)
    nf = int(sr_.dur * FPS)
    chunk = math.ceil(nf / workers)
    (BUILD / "parts").mkdir(parents=True, exist_ok=True)
    parts, procs = [], []
    for k in range(workers):
        a, b = k * chunk, min(nf, (k + 1) * chunk)
        if a >= b:
            continue
        out = BUILD / "parts" / f"{spec['id']}_{k}.mp4"
        parts.append(out)
        pr = Process(target=render_part, args=(spec, a, b, out))
        pr.start()
        procs.append(pr)
    for pr in procs:
        pr.join()
    lst = BUILD / "parts" / f"{spec['id']}.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    vid = BUILD / f"{spec['id']}_v.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(vid)], check=True)
    aud = BUILD / f"{spec['id']}.wav"
    audio_for(spec, sr_.segs, aud)
    dst_dir = DELIVER / ("shorts" if spec["vertical"] else "")
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / f"973culture_ep01_{spec['id']}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(vid), "-i", str(aud), "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(dst)], check=True)
    # SRT du format court
    srt = dst.with_suffix(".srt")
    lines = [f"{i}\n{tc(a)} --> {tc(min(e, sr_.dur))}\n{s}\n" for i, (a, e, s) in enumerate(sr_.cues, 1)]
    srt.write_text("\n".join(lines), encoding="utf-8")
    print(f"{dst.name} : {sr_.dur:.1f}s")


if __name__ == "__main__":
    ids = sys.argv[1:]
    for spec in SHORTS:
        if not ids or spec["id"] in ids:
            render_short(spec)
