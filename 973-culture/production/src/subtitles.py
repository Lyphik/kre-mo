"""Étape 8c — Sous-titres SRT (texte affiché = texte du script, pas la graphie phonétique).

Règles : ≤ 42 caractères par ligne, ≤ 2 lignes, ≤ 7 s par sous-titre, découpage aux
ponctuations, minutage proportionnel au nombre de caractères dans la réplique.
Sorties : deliverables/ep01/973culture_ep01_lyphik_fr.srt (+ fonction réutilisée pour les Shorts)
"""
import json
import re

from config import BUILD, DELIVER

MAX_LINE = 42
MAX_CHARS = 84


def tc(t):
    t = max(0.0, t)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    ms = int(round((s - int(s)) * 1000))
    if ms == 1000:
        s, ms = s + 1, 0
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{ms:03d}"


def split_text(text):
    """découpe une réplique en segments ≤ MAX_CHARS, de préférence aux ponctuations"""
    parts = re.split(r"(?<=[\.\!\?…:;])\s+", text.strip())
    out = []
    for p in parts:
        while len(p) > MAX_CHARS:
            cut = p.rfind(", ", 0, MAX_CHARS)
            if cut < 25:
                cut = p.rfind(" ", 0, MAX_CHARS)
            out.append(p[: cut + (1 if p[cut] == "," else 0)].strip())
            p = p[cut + 1:].strip()
        if p:
            out.append(p)
    # fusion des segments très courts
    merged = []
    for s in out:
        if merged and len(merged[-1]) + 1 + len(s) <= MAX_CHARS and len(s) < 22:
            merged[-1] += " " + s
        else:
            merged.append(s)
    return merged


def two_lines(s):
    if len(s) <= MAX_LINE:
        return s
    mid = len(s) // 2
    best = None
    for i, ch in enumerate(s):
        if ch == " ":
            if best is None or abs(i - mid) < abs(best - mid):
                best = i
    return s[:best] + "\n" + s[best + 1:]


def cues_for(beats, t_offset=0.0, t_min=None, t_max=None):
    cues = []
    for b in beats:
        if b["type"] != "line":
            continue
        segs = split_text(b["text"])
        total = sum(len(s) for s in segs)
        t = b["start"]
        dur = b["end"] - b["start"]
        for s in segs:
            d = dur * len(s) / total
            a, e = t, t + d
            t = e
            if t_min is not None and (e <= t_min or a >= t_max):
                continue
            if t_min is not None:
                a, e = max(a, t_min), min(e, t_max)
            cues.append((a - t_offset, e - t_offset + 0.05, two_lines(s)))
    return cues


def write_srt(cues, path):
    cues = sorted(cues)
    fixed = []
    for i, (a, e, s) in enumerate(cues):
        if i + 1 < len(cues):
            e = min(e, cues[i + 1][0] - 0.02)
        fixed.append((a, e, s))
    cues = fixed
    lines = []
    for i, (a, e, s) in enumerate(cues, 1):
        lines.append(f"{i}\n{tc(a)} --> {tc(e)}\n{s}\n")
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    tl = json.loads((BUILD / "timeline.json").read_text(encoding="utf-8"))
    DELIVER.mkdir(parents=True, exist_ok=True)
    cues = cues_for(tl["beats"])
    out = DELIVER / "973culture_ep01_lyphik_fr.srt"
    write_srt(cues, out)
    longest = max(len(l) for _, _, s in cues for l in s.split("\n"))
    maxdur = max(e - a for a, e, _ in cues)
    print(f"SRT : {out} — {len(cues)} sous-titres, ligne max {longest} car., durée max {maxdur:.1f}s")


if __name__ == "__main__":
    main()
