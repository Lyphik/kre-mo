"""Étape 7c — Mixage : voix + lit musical (ducking) → master audio stéréo, normalisé -14 LUFS.

- Voix : passe-haut 80 Hz, légère compression, présence (via ffmpeg), placement stéréo
  cohérent avec l'image (Kenzo légèrement à gauche, Maëva légèrement à droite).
- Musique : abaissée automatiquement sous la parole (enveloppe des voix lissée).
- Sorties : build/voices.wav, build/mix.wav (normalisé YouTube -14 LUFS / -1 dBTP)
"""
import json
import subprocess
import wave

import numpy as np

from config import BUILD, SR

PAN = {"K": -0.18, "M": 0.18}


def read(path):
    with wave.open(str(path)) as w:
        ch = w.getnchannels()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32767
    return a.reshape(-1, ch).T if ch > 1 else a


def write(path, buf):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(buf.shape[0])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(buf.T, -1, 1) * 32767).astype(np.int16).tobytes())


def build():
    tl = json.loads((BUILD / "timeline.json").read_text(encoding="utf-8"))
    total = int((tl["duration"] + 1.0) * SR)
    voices = np.zeros((2, total), dtype=np.float32)
    for b in tl["beats"]:
        if b["type"] != "line":
            continue
        v = read(BUILD / "voice" / f"{b['id']}.wav")
        # niveau constant d'une réplique à l'autre (RMS des zones parlées ≈ -18 dBFS)
        act = np.abs(v) > 0.02
        rms = np.sqrt(np.mean(v[act] ** 2)) if act.any() else 0.1
        v = v * min(4.0, (10 ** (-18 / 20)) / max(rms, 1e-4))
        v = np.tanh(v * 1.1) / 1.1 if np.abs(v).max() > 0.95 else v
        i = int(b["start"] * SR)
        j = min(total, i + len(v))
        p = PAN[b["who"]]
        voices[0, i:j] += v[: j - i] * np.sqrt(0.5 * (1 - p)) * 1.414
        voices[1, i:j] += v[: j - i] * np.sqrt(0.5 * (1 + p)) * 1.414
    write(BUILD / "voices_raw.wav", voices)
    # traitement voix (ffmpeg) : EQ + compression douce
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(BUILD / "voices_raw.wav"), "-af",
                    "highpass=f=80,equalizer=f=3200:t=q:w=1.2:g=2.5,equalizer=f=250:t=q:w=1:g=-1.5,"
                    "acompressor=threshold=-18dB:ratio=2.5:attack=8:release=120:makeup=2",
                    str(BUILD / "voices.wav")], check=True)
    voices = read(BUILD / "voices.wav")
    music = read(BUILD / "music.wav")
    n = min(voices.shape[1], music.shape[1])
    voices, music = voices[:, :n], music[:, :n]
    # enveloppe de parole → ducking
    mono = np.abs(voices).mean(axis=0)
    hop = 480
    env = np.array([mono[k:k + hop].max() for k in range(0, n, hop)])
    env = (env > 0.02).astype(np.float32)
    # lissage attaque rapide / relâche lente
    sm = np.zeros_like(env)
    acc = 0.0
    for k, e in enumerate(env):
        acc = acc + (e - acc) * (0.5 if e > acc else 0.04)
        sm[k] = acc
    duck = np.repeat(sm, hop)[:n]
    music_gain = 0.55 * (1 - 0.72 * duck)      # lit musical ≈ -20 dB sous la parole
    mix = voices * 1.0 + music * music_gain
    write(BUILD / "mix_raw.wav", mix)
    # normalisation loudness (2 passes)
    r = subprocess.run(["ffmpeg", "-i", str(BUILD / "mix_raw.wav"), "-af",
                        "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1]
    m = json.loads(js)
    af = (f"loudnorm=I=-14:TP=-1.0:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(BUILD / "mix_raw.wav"), "-af", af,
                    "-ar", str(SR), str(BUILD / "mix.wav")], check=True)
    print("mix :", BUILD / "mix.wav", "| mesuré avant normalisation :", m["input_i"], "LUFS")


if __name__ == "__main__":
    build()
