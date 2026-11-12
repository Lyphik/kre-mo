"""Étape 7a — Génération des voix (Piper, synthèse neuronale locale).

Pour chaque réplique du script :
  1. applique le lexique de prononciation (affichage ≠ prononciation) ;
  2. synthétise avec la voix du personnage ;
  3. rogne les silences, rééchantillonne en 48 kHz ;
  4. enregistre WAV + phonèmes (utilisés pour les visèmes).
Sortie : build/voice/<beat_id>.wav et build/voice/index.json
"""
import json
import re
import subprocess
import sys
import urllib.request
import wave

import numpy as np
from scipy.signal import resample_poly

from config import BUILD, SCRIPT, SR, VOICE_BASE, VOICE_URLS, VOICES_DIR


def ensure_voices():
    VOICES_DIR.mkdir(parents=True, exist_ok=True)
    for name, rel in VOICE_URLS.items():
        for ext in (".onnx", ".onnx.json"):
            dst = VOICES_DIR / f"{name}{ext}"
            if not dst.exists():
                print("téléchargement", dst.name, file=sys.stderr)
                urllib.request.urlretrieve(VOICE_BASE + rel + ext, dst)


def apply_lexicon(text, lex):
    out = text
    for k in sorted(lex, key=len, reverse=True):
        out = re.sub(r"(?<![\wÀ-ÿ])" + re.escape(k) + r"(?![\wÀ-ÿ])", lex[k], out)
    # « … » en début de réplique : enchaînement, pas de pause
    out = out.replace("…", ",").replace("«", "").replace("»", "")
    out = out.replace("x3", "fois trois")
    return out.strip(" ,")


def trim(audio, sr, thresh=0.012, pad=0.04):
    env = np.abs(audio)
    idx = np.where(env > thresh)[0]
    if len(idx) == 0:
        return audio
    a = max(0, idx[0] - int(pad * sr))
    b = min(len(audio), idx[-1] + int(pad * sr * 2))
    return audio[a:b]


def main():
    from piper import PiperVoice, SynthesisConfig

    ensure_voices()
    script = json.loads(SCRIPT.read_text(encoding="utf-8"))
    lex = script["pronunciation"]
    out_dir = BUILD / "voice"
    out_dir.mkdir(parents=True, exist_ok=True)
    voices = {}
    index = {}
    rng = np.random.default_rng(973)
    for beat in script["beats"]:
        if beat["type"] != "line":
            continue
        cast = script["cast"][beat["who"]]
        vname = cast["voice"]
        if vname not in voices:
            voices[vname] = PiperVoice.load(str(VOICES_DIR / f"{vname}.onnx"))
        voice = voices[vname]
        spoken = apply_lexicon(beat["text"], lex)
        # légère variation de débit d'une réplique à l'autre (évite l'effet « lecture »)
        ls = cast.get("length_scale", 1.0) * float(rng.uniform(0.96, 1.03))
        if beat.get("emotion") in ("laugh", "tease"):
            ls *= 0.97
        cfg = SynthesisConfig(speaker_id=cast.get("speaker", 0), length_scale=ls,
                              noise_scale=0.72, noise_w_scale=0.85)
        chunks = list(voice.synthesize(spoken, cfg))
        sr0 = voice.config.sample_rate
        gap = np.zeros(int(0.16 * sr0), dtype=np.float32)   # respiration entre phrases
        parts, phon = [], []
        for i, c in enumerate(chunks):
            parts.append(c.audio_float_array.astype(np.float32))
            if i < len(chunks) - 1:
                parts.append(gap)
            phon.extend(c.phonemes + [" "])
        audio = np.concatenate(parts)
        audio = trim(audio, sr0)
        g = np.gcd(SR, sr0)
        audio = resample_poly(audio, SR // g, sr0 // g).astype(np.float32)
        peak = np.max(np.abs(audio)) or 1.0
        audio = audio / peak * 0.89
        path = out_dir / f"{beat['id']}.wav"
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((audio * 32767).astype(np.int16).tobytes())
        index[beat["id"]] = {"who": beat["who"], "duration": len(audio) / SR,
                             "spoken": spoken, "phonemes": "".join(phon)}
        print(f"{beat['id']} {beat['who']} {len(audio)/SR:5.2f}s  {spoken[:60]}")
    (out_dir / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(v["duration"] for v in index.values())
    print(f"TOTAL voix : {total:.1f}s ({len(index)} répliques)")


if __name__ == "__main__":
    main()
