# BAD LIFE — Lyphik feat. Jahsik · Post-production vidéo

Dossier de travail versionné pour l'étalonnage et la finition du clip **BAD LIFE**.
Les médias (source, rendus) ne sont **pas** versionnés : seuls les scripts, la LUT, les données
d'analyse et la documentation le sont.

## Statut

| Étape (cahier des charges §9) | Statut |
|---|---|
| 1. Analyse intégrale de la vidéo | ⚠️ Fait, mais **liste des coupes à refaire** (sous-segmentation découverte en V4, voir erratum doc 02) — [`data/shots.csv`](data/shots.csv) est provisoire |
| 2. Diagnostic | ✅ Fait — [`docs/03-diagnostic.md`](docs/03-diagnostic.md) |
| 3. Copie de sauvegarde de l'original | ✅ Fait — copie en lecture seule, SHA-256 vérifié (voir doc 02) |
| 4. Test représentatif 10–15 s | ✅ Fait — 39,36 → 52,34 s (12,98 s), 4K, look v3, contrôlé (doc 04 §4.5) |
| 5. Validation colorimétrie + effets | 🔁 V3 commentée → **corrections V4** : 3 tests comparatifs A / B / C ([`docs/06-corrections-v4.md`](docs/06-corrections-v4.md)) — ⏳ en attente de validation |
| 6–9. Plan par plan, harmonisation, QC, master 4K | 🔒 Bloqué par l'étape 5 — voir [`docs/05-faisabilite-et-plan.md`](docs/05-faisabilite-et-plan.md) |

## Documentation

1. [`docs/01-cahier-des-charges.md`](docs/01-cahier-des-charges.md) — cahier des charges de référence (version finale reçue).
2. [`docs/02-analyse-source.md`](docs/02-analyse-source.md) — caractéristiques techniques de la source, découpage en plans, familles de lumière.
3. [`docs/03-diagnostic.md`](docs/03-diagnostic.md) — défauts d'exposition, de colorimétrie et de netteté.
4. [`docs/04-look-et-controle-qualite.md`](docs/04-look-et-controle-qualite.md) — conception du look (v1 → v3), mesures de fidélité des tons chair, effets écartés.
5. [`docs/05-faisabilite-et-plan.md`](docs/05-faisabilite-et-plan.md) — ce qui est réalisable avec quels outils, décisions attendues, plan des étapes 6 à 9.
6. [`docs/06-corrections-v4.md`](docs/06-corrections-v4.md) — corrections V4 : masque des artistes, tests A (étalonnage), B (+ atmosphère), C (+ lumière), contrôle qualité.

## Arborescence

```
postprod/bad-life/
├── README.md
├── docs/                  documentation (01 → 05)
├── data/
│   ├── families.json      classification des plans par famille de lumière (éditable)
│   └── shots.csv          table des 130 segments détectés (généré, PROVISOIRE : coupes manquées)
├── luts/
│   ├── badlife_look_v1.cube   historique — rejeté (peaux foncées assombries/bleuies)
│   ├── badlife_look_v2.cube   historique — rejeté (peaux quasi neutres bleuies)
│   ├── badlife_look_v3.cube   look V3 (remplacé par la paire V4)
│   ├── badlife_look_v4_decor.cube   V4 — appliquée hors personnes
│   └── badlife_look_v4_sujets.cube  V4 — appliquée sur les personnes
└── tools/
    ├── analyze.sh         étape 1 : détection des coupes + statistiques signal
    ├── shots.py           agrégation des statistiques par plan
    ├── build_shotlist.py  génération de data/shots.csv
    ├── make_lut.py        générateur des LUT (presets versionnés v1, v2, v3)
    ├── skin_probe.py      mesure de dérive des tons chair (source vs étalonné)
    ├── render.sh          rendu : LUT + N&B préservé + vignettage + upscale 4K + export HEVC
    ├── compare.sh         vidéo de validation AVANT / APRÈS (1080p)
    └── v4/
        ├── test_segment.json  plans de l'extrait, gains d'exposition, effets par plan
        ├── matte.py           détourage des personnes (Robust Video Matting, ONNX)
        ├── beats.py           tempo et attaques de la musique (transitions)
        ├── composite.py       rendu simultané A / B / C, compositing derrière les artistes, QC
        └── compare4.sh        comparatif 4 vues SOURCE | A | B | C
```

## Reproduire

Prérequis : `ffmpeg` ≥ 6.1 (libx265, filtres `lut3d`, `zscale`), Python 3 avec `numpy` et `Pillow`.

```bash
# 1. Analyse
tools/analyze.sh "source.mov" analysis/
python3 tools/build_shotlist.py analysis/shots.json data/families.json data/shots.csv

# 2. LUT (presets figés : v1, v2, v3)
python3 tools/make_lut.py --preset v3 luts/badlife_look_v3.cube

# 3. Test (extrait) puis master complet
tools/render.sh "source.mov" test.mp4 39.36 52.34
tools/compare.sh "source.mov" test.mp4 39.36 52.34 comparaison.mp4
BW_RANGES="75.16-76.84" tools/render.sh "source.mov" BADLIFE_MASTER_4K.mp4   # après validation uniquement
```

### V4 (tests A / B / C)

Dépendances supplémentaires : `onnxruntime`, `opencv-python-headless`, `scipy` ; modèle
`rvm_mobilenetv3_fp32.onnx` (release v1.0.0 de PeterL1n/RobustVideoMatting, SHA-256 dans la doc 06).

```bash
python3 tools/make_lut.py --preset v4_decor  luts/badlife_look_v4_decor.cube
python3 tools/make_lut.py --preset v4_sujets luts/badlife_look_v4_sujets.cube
python3 tools/v4/matte.py  "source.mov" rvm_mobilenetv3_fp32.onnx tools/v4/test_segment.json matte/
python3 tools/v4/beats.py  "source.mov" 39.36 12.98 beats.json
python3 tools/v4/composite.py "source.mov" tools/v4/test_segment.json matte/ beats.json \
        luts/badlife_look_v4_decor.cube luts/badlife_look_v4_sujets.cube rendus_v4/
tools/v4/compare4.sh "source.mov" 39.36 12.98 rendus_v4/BADLIFE_V4_TEST_{A,B,C}.mp4 comparatif.mp4
```

La LUT `badlife_look_v3.cube` (Rec.709 / BT.1886, entrée et sortie RGB pleine échelle, 33³)
s'importe aussi telle quelle dans DaVinci Resolve, Premiere Pro ou Final Cut Pro.

## Règles de version

- Une LUT publiée n'est **jamais modifiée** : toute évolution crée un nouveau preset (`v4`, …) dans `tools/make_lut.py`.
- `tools/make_lut.py --preset v1` régénère `luts/badlife_look_v1.cube` à l'octet près (vérifié).
- Aucun média n'est commité (`.gitignore`).
