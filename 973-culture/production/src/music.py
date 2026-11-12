"""Étape 7b — Identité sonore originale de 973 CULTURE (synthèse procédurale, libre de droits).

Composition originale (aucun échantillon, aucune reprise) :
  - 96 BPM, la mineur, progression Am – F – C – G ;
  - rythmique trap/dancehall stylisée (kick, clap, charleston swingué) ;
  - « steelpan » de synthèse (partiels inharmoniques) pour la couleur caribéenne ;
  - nappe chaude, basse 808 ;
  - effets : montée + impact (logo, révélation du nom, BAD LIFE), whoosh sur transitions.
Sortie : build/music.wav (stéréo 48 kHz) — piste « lit musical » non mixée.
"""
import json
import wave

import numpy as np

from config import BUILD, SR

BPM = 96
BEAT = 60 / BPM
STEP = BEAT / 4
BAR = BEAT * 4
rng = np.random.default_rng(973)

NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def hz(name, octave):
    """fréquence d'une note (notation scientifique, La4 = 440 Hz)"""
    midi = 12 * (octave + 1) + NOTE[name]
    return 440.0 * 2 ** ((midi - 69) / 12)


CHORDS = [  # (fondamentale basse, notes de nappe)
    (hz("A", 2), [hz("A", 3), hz("C", 4), hz("E", 4)]),
    (hz("F", 2), [hz("F", 3), hz("A", 3), hz("C", 4)]),
    (hz("C", 3), [hz("G", 3), hz("C", 4), hz("E", 4)]),
    (hz("G", 2), [hz("G", 3), hz("B", 3), hz("D", 4)]),
]
PENTA = [hz("A", 4), hz("C", 5), hz("D", 5), hz("E", 5), hz("G", 5), hz("A", 5)]
MOTIF = [(0, 3, 0.9), (2, 2, 0.6), (3, 4, 0.8), (6, 3, 0.7), (8, 1, 0.9), (10, 2, 0.6), (11, 0, 0.7), (14, 1, 0.6)]
MOTIF_B = [(0, 4, 0.9), (3, 3, 0.7), (6, 2, 0.8), (8, 3, 0.7), (10, 5, 0.9), (12, 4, 0.6), (14, 3, 0.6)]


def env_exp(n, decay):
    t = np.arange(n) / SR
    return np.exp(-t / decay)


def onepole_lp(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    # filtrage vectorisé par blocs via scipy si disponible
    try:
        from scipy.signal import lfilter
        return lfilter([1 - a], [1, -a], x)
    except Exception:
        for i, v in enumerate(x):
            acc = (1 - a) * v + a * acc
            y[i] = acc
        return y


def kick(n=int(0.45 * SR)):
    t = np.arange(n) / SR
    f = 45 + 90 * np.exp(-t / 0.045)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.tanh(1.6 * np.sin(ph) * env_exp(n, 0.16))


def clap(n=int(0.25 * SR)):
    from scipy.signal import butter, lfilter
    b, a = butter(2, [900 / (SR / 2), 4000 / (SR / 2)], btype="band")
    nz = lfilter(b, a, rng.standard_normal(n))
    e = env_exp(n, 0.07)
    # triple attaque caractéristique d'un clap
    for d in (0.008, 0.017):
        k = int(d * SR)
        e[k:] += 0.6 * env_exp(n - k, 0.03)
    return nz * e * 0.5


def hat(n=int(0.05 * SR), open_=False):
    from scipy.signal import butter, lfilter
    if open_:
        n = int(0.22 * SR)
    b, a = butter(2, 7000 / (SR / 2), btype="high")
    return lfilter(b, a, rng.standard_normal(n)) * env_exp(n, 0.06 if open_ else 0.012) * 0.35


def pan_note(freq, dur, vel):
    n = int(dur * SR)
    t = np.arange(n) / SR
    partials = [(1.0, 1.0, 0.9), (2.0, 0.5, 0.45), (2.76, 0.28, 0.25), (3.98, 0.16, 0.18), (5.4, 0.08, 0.1)]
    out = np.zeros(n)
    for ratio, amp, dec in partials:
        out += amp * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-t / dec)
    att = np.minimum(1, t / 0.004)
    return out * att * vel * 0.32


def pad(freqs, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0.0, 0.11):
            ff = f * 2 ** (det / 12)
            ph = rng.uniform(0, 1)
            saw = 2 * ((ff * t + ph) % 1) - 1
            out += saw
    out = onepole_lp(out, 1100)
    a = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.5).clip(0, 1)
    return out * a * 0.035


def bass808(freq, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return np.tanh(2.2 * np.sin(2 * np.pi * freq * t)) * np.exp(-t / 0.9) * np.minimum(1, t / 0.005) * 0.42


def place(buf, sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= buf.shape[1] or i < 0:
        return
    j = min(buf.shape[1], i + len(sig))
    s = sig[: j - i] * gain
    buf[0, i:j] += s * np.sqrt(0.5 * (1 - pan)) * 1.414
    buf[1, i:j] += s * np.sqrt(0.5 * (1 + pan)) * 1.414


def riser(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    from scipy.signal import butter, lfilter
    nz = rng.standard_normal(n)
    out = np.zeros(n)
    seg = 2048
    for k in range(0, n, seg):
        fc = 400 + 7000 * (k / n) ** 2
        b, a = butter(2, min(0.99, fc / (SR / 2)), btype="low")
        out[k:k + seg] = lfilter(b, a, nz[k:k + seg])
    return out * (t / dur) ** 2 * 0.35


def impact():
    n = int(2.2 * SR)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (38 + 60 * np.exp(-t / 0.08)) * t) * np.exp(-t / 0.7)
    from scipy.signal import butter, lfilter
    b, a = butter(2, 2500 / (SR / 2), btype="low")
    nz = lfilter(b, a, rng.standard_normal(n)) * np.exp(-t / 0.25) * 0.5
    return np.tanh(1.5 * (boom + nz)) * 0.8


def whoosh(dur=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    from scipy.signal import butter, lfilter
    nz = rng.standard_normal(n)
    out = np.zeros(n)
    seg = 1024
    for k in range(0, n, seg):
        u = k / n
        fc = 300 + 5000 * np.sin(np.pi * u)
        b, a = butter(2, [max(0.01, fc * 0.5 / (SR / 2)), min(0.99, fc * 1.5 / (SR / 2))], btype="band")
        out[k:k + seg] = lfilter(b, a, nz[k:k + seg])
    return out * np.sin(np.pi * t / dur) ** 2 * 0.5


def build():
    tl = json.loads((BUILD / "timeline.json").read_text(encoding="utf-8"))
    total = tl["duration"] + 1.0
    buf = np.zeros((2, int(total * SR)))
    beats = {b["id"]: b for b in tl["beats"]}
    logo = beats["S0-05"]
    name = beats["S1-07"]
    end = beats["S7-08"]
    bad0 = beats["S6-01"]["start"]
    bad1 = beats["S6-08"]["end"]
    drop = logo["start"] + 0.0
    K, C, H, Ho = kick(), clap(), hat(), hat(open_=True)

    # grille musicale calée pour que l'impact du logo tombe sur un temps fort
    t0 = drop - 4 * BAR
    nbars = int((total - t0) / BAR) + 1
    for bi in range(nbars):
        bt = t0 + bi * BAR
        if bt + BAR < 0:
            continue
        root, notes = CHORDS[bi % 4]
        intro = bt < drop
        outro = bt >= end["start"]
        in_bad = bad0 <= bt < bad1
        # nappe : partout
        place(buf, pad(notes, BAR + 0.4), bt, 1.0 if not intro else 0.8, 0.0)
        # steelpan : motif (A puis B), plus présent en intro / outro
        motif = MOTIF if (bi // 2) % 2 == 0 else MOTIF_B
        pg = 1.0 if (intro or outro) else 0.55
        for step, deg, vel in motif:
            place(buf, pan_note(PENTA[deg], 1.4, vel), bt + step * STEP, pg, 0.25 * ((step % 3) - 1))
        if intro and bt < drop - 2 * BAR:
            continue
        # rythmique
        for s in range(16):
            ts = bt + s * STEP + (0.018 if s % 2 else 0)       # swing
            if s in (0, 10) or (in_bad and s == 7):
                place(buf, K, ts, 0.9 if not intro else 0.5)
            if s in (4, 12):
                place(buf, C, ts, 0.75 if not intro else 0.35, 0.05)
            if s % 2 == 0 and not intro:
                place(buf, H, ts, 0.55 + 0.2 * (s % 4 == 2), 0.3)
            if s == 14 and bi % 2 == 1 and not intro:
                place(buf, Ho, ts, 0.45, 0.3)
            if in_bad and s in (3, 11):
                place(buf, H, ts, 0.5, -0.3)
        if not intro:
            place(buf, bass808(root, BAR * 0.62), bt, 1.1 if in_bad else 0.9)
            place(buf, bass808(root * (1.5 if bi % 2 else 1.0), BAR * 0.3), bt + 10 * STEP, 0.7)

    # ambiance extérieure : feuillage (bruit filtré) + grillons qui s'intensifient avec la nuit
    from scipy.signal import butter, lfilter
    n_all = buf.shape[1]
    b_, a_ = butter(2, [250 / (SR / 2), 1800 / (SR / 2)], btype="band")
    wind = lfilter(b_, a_, rng.standard_normal(n_all)) * 0.05
    tt = np.arange(n_all) / SR
    wind *= 0.6 + 0.4 * np.sin(tt * 0.21) * np.sin(tt * 0.073 + 1)
    night = np.clip(tt / tl["duration"], 0, 1) ** 1.1
    chirp = np.sin(2 * np.pi * 4300 * tt) * (np.sin(2 * np.pi * 28 * tt) > 0.55) * (np.sin(2 * np.pi * 0.9 * tt) > 0.2)
    chirp2 = np.sin(2 * np.pi * 3900 * tt) * (np.sin(2 * np.pi * 31 * tt + 1) > 0.6) * (np.sin(2 * np.pi * 0.7 * tt + 2) > 0.35)
    crick = (chirp * 0.010 + chirp2 * 0.008) * (0.25 + 0.75 * night)
    fade_in = np.clip(tt / 0.25, 0, 1)
    buf[0] += (wind + crick) * fade_in
    buf[1] += (np.roll(wind, 4800) + np.roll(crick, 2400)) * fade_in
    # effets
    place(buf, riser(3.0), drop - 3.0, 1.0)
    place(buf, impact(), drop, 1.0)
    place(buf, impact(), name["start"] + 0.5, 0.8)
    place(buf, impact(), bad0, 0.7)
    shots = tl["shots"]
    for a, b in zip(shots, shots[1:]):
        if a["kind"] != b["kind"] or (a["kind"] == "gfx" and a.get("scene") != b.get("scene")):
            place(buf, whoosh(0.5), b["start"] - 0.25, 0.55, 0.0)

    # fondu de fin
    fe = int((end["end"] - 1.5) * SR)
    n = buf.shape[1] - fe
    if n > 0:
        buf[:, fe:] *= np.linspace(1, 0, n) ** 2
    buf /= max(1e-6, np.max(np.abs(buf))) / 0.9
    out = BUILD / "music.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((buf.T * 32767).astype(np.int16).tobytes())
    print("musique :", out, f"{total:.1f}s")


if __name__ == "__main__":
    build()
