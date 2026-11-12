# Pipeline de production — 973 CULTURE

Pipeline 100 % local et reproductible : **script JSON → voix → timeline → audio → rendu vectoriel → MP4, SRT, Shorts, miniature.**

## Architecture

```
script/ep01.json        Source unique : répliques, plans, données des habillages, lexique de prononciation
assets/geo/             Contour de la Guyane (Natural Earth, domaine public)
src/
  config.py             Formats, chemins, palette
  tts.py                Étape 7a — voix Piper (WAV par réplique + phonèmes)
  timeline.py           Étape 8a — minutage, liste de plans, pistes de bouche (ouverture + visème)
  music.py              Étape 7b — identité sonore originale + ambiance + effets
  mix.py                Étape 7c — mixage voix/musique (ducking), -14 LUFS
  draw.py               Primitives Cairo (dégradés, texte, easing)
  characters.py         Étape 4 — Kenzo & Maëva (modèles paramétriques)
  setdesign.py          Étape 5 — décor Place des Palmistes (plateau éphémère)
  compositor.py         Caméra virtuelle, parallaxe, comportement des personnages, habillage
  scenes.py             Étape 6 — motion design (19 habillages)
  render.py             Étape 8b — rendu parallèle, encodage H.264
  subtitles.py          Étape 8c — SRT
  shorts.py             Étape 10 — Shorts 9:16 + bande-annonce 16:9
  thumbnail.py          Miniature YouTube
  export_script.py      Scénario Markdown généré depuis le JSON
build/                  Artefacts intermédiaires (non versionnés)
.cache/voices/          Modèles de voix téléchargés (non versionnés)
```

## Prérequis

- Python ≥ 3.11, FFmpeg (libx264, aac), ImageMagick (`convert`), polices **Inter**, **Inter Display** et **JetBrains Mono** installées.
- `pip install -r requirements.txt`

## Production complète d'un épisode

```bash
cd src
python tts.py            # voix (télécharge les modèles Piper au premier lancement)
python timeline.py       # minutage + plans + bouches
python music.py          # musique originale
python mix.py            # mixage -14 LUFS
python subtitles.py      # SRT
python export_script.py  # scénario Markdown
python render.py stills 12 60 140      # (contrôle) images fixes dans build/stills/
python render.py video --name master_video --workers 4 --crf 20
ffmpeg -i ../build/master_video.mp4 -i ../build/mix.wav -map 0:v -map 1:a -c:v copy \
       -c:a aac -b:a 192k -shortest -movflags +faststart ../../deliverables/ep01/<nom>.mp4
python shorts.py         # 5 Shorts + bande-annonce
python thumbnail.py      # miniature
```

Durées indicatives (4 cœurs) : voix ~2 min · rendu du master ~14 min · Shorts ~10 min.

## Créer un nouvel épisode

1. Dossier de recherche + sources dans `docs/` (règle : aucune information non étiquetée dans le script).
2. Copier `script/ep01.json` vers `epNN.json` : nouvelles répliques, scènes et données. Les habillages sont des gabarits paramétrés (`stat`, `map`, `network`, `badlife`…), mais chaque épisode doit avoir **sa propre** mise en scène (règle YouTube « contenu non authentique »).
3. Ajuster `SCRIPT` et `DELIVER` dans `config.py`, puis relancer la chaîne.
4. Remplacer des voix : déposer un WAV par réplique dans `build/voice/<id>.wav` (48 kHz mono), mettre à jour `build/voice/index.json`, puis relancer à partir de `timeline.py`.

## Options

- `render.GRAIN = True` : grain de tramage anti-banding (meilleur rendu des dégradés sombres, débit ×2,5 ; recommandé pour un envoi direct à YouTube, déconseillé pour Git).
- 4K : multiplier `W` et `H` par 2 et appliquer `ctx.scale(2, 2)` en tête de `Renderer.frame` (temps de rendu ×4).
