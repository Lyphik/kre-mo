"""Étape 8a — Construction de la timeline (minutage, plans, pistes de bouche).

Entrées : script/ep01.json + build/voice/index.json
Sortie  : build/timeline.json
  - beats  : début/fin de chaque réplique ou plan visuel
  - shots  : liste de plans (cadre caméra ou habillage graphique)
  - mouth  : par personnage, ouverture (0..1) et visème, à 25 i/s
"""
import json
import wave

import numpy as np

from config import BUILD, FPS, SCRIPT, SR

VOWEL_SHAPES = {
    "round": set("oɔuyøœw") | {"ʃ", "ʒ"},
    "wide": set("ieɛj") | {"ɪ"},
    "closed": set("mbp"),
    "fv": set("fv"),
    "open": set("aɑ"),
}
GRAPHIC_SCENES = {"stat", "map", "quote", "pml", "timeline", "clip_slot", "cards", "ep",
                  "network", "press", "persona", "factcheck", "badlife", "paradox",
                  "playlist", "cta", "disclaimer"}


def gap_after(text, next_text):
    if next_text and next_text.lstrip().startswith("…"):
        return 0.06
    t = text.rstrip()
    if t.endswith("…"):
        return 0.10
    if t.endswith("?"):
        return 0.38
    if t.endswith("!"):
        return 0.30
    return 0.26


def read_wav(path):
    with wave.open(str(path)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32767
    return a


def phoneme_shape(p):
    for k, s in VOWEL_SHAPES.items():
        if p in s:
            return k
    return "neutral"


def mouth_track(audio, phonemes):
    """Ouverture par image (enveloppe RMS lissée) + visème (phonèmes répartis sur le voisé)."""
    hop = SR // FPS
    n = int(np.ceil(len(audio) / hop))
    rms = np.array([np.sqrt(np.mean(audio[i * hop:(i + 1) * hop] ** 2) + 1e-9) for i in range(n)])
    rms = np.convolve(rms, [0.25, 0.5, 0.25], mode="same")
    ref = np.percentile(rms, 95) or 1.0
    op = np.clip((rms / ref - 0.08) / 0.92, 0, 1) ** 0.8
    voiced = np.where(op > 0.12)[0]
    seq = [phoneme_shape(c) for c in phonemes if c.strip() and c not in "ˈˌ̃,.!?:;"]
    shapes = ["closed"] * n
    if len(voiced) and seq:
        for j, fi in enumerate(voiced):
            shapes[fi] = seq[min(len(seq) - 1, int(j / len(voiced) * len(seq)))]
    return op.round(3).tolist(), shapes


def build():
    script = json.loads(SCRIPT.read_text(encoding="utf-8"))
    vidx = json.loads((BUILD / "voice" / "index.json").read_text(encoding="utf-8"))
    beats = script["beats"]
    t = 0.0
    out_beats = []
    for i, b in enumerate(beats):
        nb = beats[i + 1] if i + 1 < len(beats) else None
        if b["type"] == "visual":
            dur = b["duration"]
            out_beats.append({**b, "start": round(t, 3), "end": round(t + dur, 3)})
            t += dur
        else:
            dur = vidx[b["id"]]["duration"]
            out_beats.append({**b, "start": round(t, 3), "end": round(t + dur, 3),
                              "spoken": vidx[b["id"]]["spoken"]})
            nxt_text = nb["text"] if nb and nb["type"] == "line" else None
            t += dur + (gap_after(b["text"], nxt_text) if nb and nb["type"] == "line" else 0.35)
    total = t
    nframes = int(np.ceil(total * FPS))

    # pistes de bouche
    mouth = {k: {"open": [0.0] * nframes, "shape": ["closed"] * nframes} for k in ("K", "M")}
    for b in out_beats:
        if b["type"] != "line":
            continue
        audio = read_wav(BUILD / "voice" / f"{b['id']}.wav")
        op, sh = mouth_track(audio, vidx[b["id"]]["phonemes"])
        f0 = int(round(b["start"] * FPS))
        for j in range(len(op)):
            if f0 + j < nframes:
                mouth[b["who"]]["open"][f0 + j] = op[j]
                mouth[b["who"]]["shape"][f0 + j] = sh[j]

    # liste de plans
    shots = []
    prev_cam = None
    for i, b in enumerate(out_beats):
        scene = b.get("scene", "two_shot")
        s, e = b["start"], b["end"]
        # le plan dure jusqu'au début du beat suivant
        e_full = out_beats[i + 1]["start"] if i + 1 < len(out_beats) else e
        who = b.get("who")
        if scene in ("single",):
            dur = e_full - s
            if dur > 7.0:
                cut = s + dur * 0.62
                shots.append({"start": s, "end": cut, "kind": "cam", "cam": f"single_{who}", "beat": b["id"]})
                shots.append({"start": cut, "end": e_full, "kind": "cam", "cam": "two_shot", "beat": b["id"]})
            else:
                shots.append({"start": s, "end": e_full, "kind": "cam", "cam": f"single_{who}", "beat": b["id"]})
        elif scene in ("two_shot", "set_wide"):
            cam = scene
            if cam == prev_cam == "two_shot" and who:
                cam = f"over_{who}"   # variation : plan épaule
            shots.append({"start": s, "end": e_full, "kind": "cam", "cam": cam, "beat": b["id"]})
        else:
            shots.append({"start": s, "end": e_full, "kind": "gfx", "scene": scene, "beat": b["id"],
                          "data": b.get("data", {}), "who": who})
        prev_cam = shots[-1].get("cam")

    chapters = [{"title": b["chapter"], "start": b["start"]} for b in out_beats if b.get("chapter")]
    tl = {"fps": FPS, "duration": round(total, 3), "nframes": nframes, "beats": out_beats,
          "shots": shots, "mouth": mouth, "chapters": chapters}
    (BUILD / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False), encoding="utf-8")
    m, s_ = divmod(total, 60)
    print(f"Durée totale : {int(m)} min {s_:04.1f} s — {nframes} images — {len(shots)} plans")
    for c in chapters:
        mm, ss = divmod(c["start"], 60)
        print(f"  {int(mm)}:{int(ss):02d}  {c['title']}")


if __name__ == "__main__":
    build()
