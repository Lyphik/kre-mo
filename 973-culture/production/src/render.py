"""Étape 8b — Rendu image par image et encodage H.264 (parallèle, par segments).

Usage :
  python render.py stills 12.5 60 130      → PNG de contrôle dans build/stills/
  python render.py video [--from S --to E]  → build/video_<a>_<b>.mp4 (sans audio)
"""
import argparse
import bisect
import json
import math
import os
import subprocess
import sys
from multiprocessing import Process

import cairo

from compositor import (CAMS, Director, bug, cam_for, draw_pip, draw_set_shot, lower_third)
from config import BUILD, FPS, H, W
from draw import P, ease_in_out, ease_out, prog, rrect, set_src, text
from scenes import SCENES, scene_cold_open_overlay, scene_disclaimer_overlay

GRAIN = False   # tramage anti-banding : coûteux en débit (×2,5), désactivé pour le master versionné
NO_PIP = {"logo", "name_reveal", "end_logo", "cold_open", "disclaimer"}


class Renderer:
    def __init__(self):
        self.tl = json.loads((BUILD / "timeline.json").read_text(encoding="utf-8"))
        self.d = Director(self.tl)
        self.shots = self.tl["shots"]
        self.starts = [s["start"] for s in self.shots]
        self.beats = {b["id"]: b for b in self.tl["beats"]}
        self.chapters = [b for b in self.tl["beats"] if b.get("chapter")]
        self.chapter_index = {b["id"]: i + 1 for i, b in enumerate(self.chapters)}
        # frontières nécessitant une transition (changement de nature de plan)
        # grain de tramage (anti-banding) : 4 textures pré-calculées, alternées
        import numpy as np
        rng = np.random.default_rng(7)
        self.grain = []
        for _ in range(1):
            a = rng.integers(0, 5, size=(H, W), dtype=np.uint8)
            white = rng.random((H, W)) < 0.5
            px = np.zeros((H, W, 4), dtype=np.uint8)
            px[..., 3] = a
            for c in range(3):
                px[..., c] = np.where(white, a, 0)
            surf = cairo.ImageSurface.create_for_data(bytearray(px.tobytes()), cairo.FORMAT_ARGB32, W, H, W * 4)
            self.grain.append(surf)
        self.trans = []
        for a, b in zip(self.shots, self.shots[1:]):
            ka = a["kind"] + (a.get("scene") or "")
            kb = b["kind"] + (b.get("scene") or "")
            if a["kind"] != b["kind"] or (a["kind"] == "gfx" and ka != kb):
                if b.get("scene") not in ("logo",) and a.get("scene") not in ("cold_open",):
                    self.trans.append(b["start"])

    def shot_at(self, t):
        i = max(0, bisect.bisect_right(self.starts, t) - 1)
        return self.shots[i]

    def frame(self, ctx, t):
        sh = self.shot_at(t)
        tl = t - sh["start"]
        dur = sh["end"] - sh["start"]
        beat = self.beats[sh["beat"]]
        env = {"t": t, "director": self.d, "who": sh.get("who")}
        if sh["kind"] == "cam":
            draw_set_shot(ctx, self.d, cam_for(sh["cam"], tl, dur), t)
            bug(ctx)
        else:
            sc = sh["scene"]
            if sc == "cold_open":
                u = ease_in_out(prog(tl, 0, dur + 4))
                cam = (960, 300 + 240 * u, 1.25 - 0.25 * u)
                draw_set_shot(ctx, self.d, cam, t)
                scene_cold_open_overlay(ctx, tl, dur, sh["data"], env)
            elif sc == "disclaimer":
                draw_set_shot(ctx, self.d, cam_for("two_shot", tl, dur), t)
                bug(ctx)
                scene_disclaimer_overlay(ctx, tl, dur, sh["data"], env)
            else:
                # mouvement de caméra continu sur les habillages (aucun plan figé)
                u = ease_in_out(prog(tl, 0, dur))
                z = 1.0 + 0.045 * u
                from draw import noise1
                dx = noise1(t * 0.35, 21) * 10
                dy = noise1(t * 0.3, 22) * 7
                ctx.save()
                ctx.translate(W / 2 + dx, H / 2 + dy)
                ctx.scale(z, z)
                ctx.translate(-W / 2, -H / 2)
                SCENES[sc](ctx, tl, dur, sh["data"], env)
                ctx.restore()
            if sh.get("who") and sc not in NO_PIP:
                pa = ease_out(prog(tl, 0.25, 0.6)) * (1 - ease_out(prog(tl, dur - 0.25, dur)))
                if pa > 0.01:
                    ctx.push_group()
                    x = 170 if sh["who"] == "K" else W - 170
                    draw_pip(ctx, self.d, sh["who"], t, x, H - 210, 96)
                    ctx.pop_group_to_source()
                    ctx.paint_with_alpha(pa)
        # bandeau sous-titre nominatif (première prise de parole)
        if beat.get("lower_third") and sh["kind"] == "cam":
            lower_third(ctx, beat["lower_third"], t - beat["start"])
        # carton de chapitre
        if beat.get("chapter"):
            self.chapter_card(ctx, beat, t - beat["start"])
        self.transition(ctx, t)
        if GRAIN:
            ctx.set_source_surface(self.grain[0], 0, 0)
            ctx.paint()

    def chapter_card(self, ctx, beat, tl):
        if tl > 3.4:
            return
        a = ease_out(prog(tl, 0.2, 0.6)) * (1 - ease_out(prog(tl, 2.9, 3.4)))
        n = self.chapter_index[beat["id"]]
        label = beat["chapter"].upper()
        ctx.save()
        ctx.translate((1 - a) * -40, 0)
        rrect(ctx, 96, 150, 90, 90, 8)
        set_src(ctx, P("gold", a))
        ctx.fill()
        text(ctx, f"{n:02d}", 141, 212, 46, P("night", a), "black", "center")
        from draw import text_width
        w = text_width(ctx, label, 40, "black", tracking=0.08)
        rrect(ctx, 196, 150, w + 60, 90, 8)
        set_src(ctx, P("night", 0.88 * a))
        ctx.fill()
        text(ctx, label, 226, 210, 40, P("white", a), "black", tracking=0.08)
        ctx.restore()

    def transition(self, ctx, t):
        i = bisect.bisect_left(self.trans, t - 0.25)
        for b in self.trans[i:i + 2]:
            if abs(t - b) < 0.25:
                u = (t - (b - 0.25)) / 0.5            # 0 → 1
                cols = [P("green"), P("gold"), P("red")]
                for k, col in enumerate(cols):
                    off = (u - k * 0.06) * (W + 1400) * 1.15 - 900
                    ctx.save()
                    ctx.translate(off, 0)
                    ctx.move_to(-500 + k * 0, 0)
                    ctx.line_to(400, 0)
                    ctx.line_to(400 - 300, H)
                    ctx.line_to(-500 - 300, H)
                    ctx.close_path()
                    set_src(ctx, col)
                    ctx.fill()
                    ctx.restore()


def render_range(f0, f1, out, crf=19):
    r = Renderer()
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-tune", "animation",
           "-crf", str(crf), "-x264-params", "aq-mode=3", "-pix_fmt", "yuv420p", "-g", str(FPS * 2), str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        ctx.save()
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()
        r.frame(ctx, f / FPS)
        ctx.restore()
        surf.flush()
        p.stdin.write(bytes(surf.get_data()))
        if (f - f0) % 250 == 0:
            print(f"  [{out.name}] {f - f0}/{f1 - f0}", flush=True)
    p.stdin.close()
    p.wait()


def render_video(t0, t1, name, workers=4, crf=19):
    f0, f1 = int(t0 * FPS), int(t1 * FPS)
    chunk = math.ceil((f1 - f0) / workers)
    parts = []
    procs = []
    (BUILD / "parts").mkdir(parents=True, exist_ok=True)
    for k in range(workers):
        a, b = f0 + k * chunk, min(f1, f0 + (k + 1) * chunk)
        if a >= b:
            continue
        out = BUILD / "parts" / f"{name}_{k:02d}.mp4"
        parts.append(out)
        pr = Process(target=render_range, args=(a, b, out, crf))
        pr.start()
        procs.append(pr)
    for pr in procs:
        pr.join()
    lst = BUILD / "parts" / f"{name}.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    final = BUILD / f"{name}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(final)], check=True)
    print("vidéo :", final)
    return final


def stills(times, scale=0.5):
    r = Renderer()
    out = BUILD / "stills"
    out.mkdir(parents=True, exist_ok=True)
    for t in times:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        ctx = cairo.Context(surf)
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()
        r.frame(ctx, t)
        p = out / f"still_{t:07.2f}.png"
        surf.write_to_png(str(p))
        print(p)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["stills", "video"])
    ap.add_argument("times", nargs="*", type=float)
    ap.add_argument("--from", dest="t0", type=float, default=0)
    ap.add_argument("--to", dest="t1", type=float, default=None)
    ap.add_argument("--name", default="master_video")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--crf", type=int, default=19)
    a = ap.parse_args()
    if a.mode == "stills":
        stills(a.times)
    else:
        tl = json.loads((BUILD / "timeline.json").read_text(encoding="utf-8"))
        render_video(a.t0, a.t1 or tl["duration"], a.name, a.workers, a.crf)
