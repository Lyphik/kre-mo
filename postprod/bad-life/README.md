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
| 5. Validation colorimétrie + effets | 🔁 V3 → V4 (tests A / B / C) → **V5 définitive** ([`docs/07`](docs/07-cahier-des-charges-v5.md)) |
| **V5 — étapes 1 à 3** (sécurisation, analyse complète, masques) | ✅ Fait — [`docs/08-v5-analyse.md`](docs/08-v5-analyse.md), [`data/v5/`](data/v5/) |
| **V5 — étapes 4 à 6** (étalonnage par famille, effets, contrôle) | ✅ Fait sur 5 extraits — [`docs/09-v5-tests-et-qc.md`](docs/09-v5-tests-et-qc.md) |
| **V5 — étape 7** (validation des 5 extraits) | ✅ V5 jugée trop chargée → **V5.1 passe de finition** ([`docs/10-v5-1-finition.md`](docs/10-v5-1-finition.md)) — validée le 2026-11-09 avec arbitrages définitifs |
| **V5 — étape 8** (master 4K) | ✅ **Master V5.1 prêt** — 4K 50 i/s HEVC Main 10, audio original bit à bit, tous les contrôles passés ([`docs/11-master-v5-1.md`](docs/11-master-v5-1.md) §11.6, [`data/master/`](data/master/)) — ⏳ arbitrage 1-bis à confirmer |
| **Teaser de sortie** (30 s, vertical 9:16) | ⏳ Export définitif en cours de contrôle — version PREMIUM validée sur aperçu ([`docs/12-teaser-sortie.md`](docs/12-teaser-sortie.md)) |

## Documentation

1. [`docs/01-cahier-des-charges.md`](docs/01-cahier-des-charges.md) — cahier des charges de référence (version finale reçue).
2. [`docs/02-analyse-source.md`](docs/02-analyse-source.md) — caractéristiques techniques de la source, découpage en plans, familles de lumière.
3. [`docs/03-diagnostic.md`](docs/03-diagnostic.md) — défauts d'exposition, de colorimétrie et de netteté.
4. [`docs/04-look-et-controle-qualite.md`](docs/04-look-et-controle-qualite.md) — conception du look (v1 → v3), mesures de fidélité des tons chair, effets écartés.
5. [`docs/05-faisabilite-et-plan.md`](docs/05-faisabilite-et-plan.md) — ce qui est réalisable avec quels outils, décisions attendues, plan des étapes 6 à 9.
6. [`docs/06-corrections-v4.md`](docs/06-corrections-v4.md) — corrections V4 : masque des artistes, tests A (étalonnage), B (+ atmosphère), C (+ lumière), contrôle qualité.
7. [`docs/07-cahier-des-charges-v5.md`](docs/07-cahier-des-charges-v5.md) — cahier des charges V5 définitif (référence).
8. [`docs/08-v5-analyse.md`](docs/08-v5-analyse.md) — V5 : sécurisation, coupes refaites et validées, plans réels, ambiances, N&B, musique, masques.
9. [`docs/09-v5-tests-et-qc.md`](docs/09-v5-tests-et-qc.md) — V5 : étalonnage C hybride, effets, 5 extraits, rapport de contrôle qualité, décisions attendues.
10. [`docs/10-v5-1-finition.md`](docs/10-v5-1-finition.md) — V5.1 : passe de finition (moins d'effets, plus de profondeur), mesures d'amélioration, conservé / réduit / supprimé par extrait, autocritique.
11. [`docs/11-master-v5-1.md`](docs/11-master-v5-1.md) — master V5.1 : arbitrages définitifs, vérification courte, rendu par segments, défauts trouvés et corrigés (fondu, décalage d'assemblage, pulsation 25 Hz des halos), contrôles du master final, livrables.
12. [`docs/12-teaser-sortie.md`](docs/12-teaser-sortie.md) — teaser de sortie 30 s vertical : passage musical, montage, respect des artistes, identité typographique du clip, graphisme procédural, fin vivante, contrôles.

## Arborescence

```
postprod/bad-life/
├── README.md
├── docs/                  documentation (01 → 12)
├── data/
│   ├── families.json      classification des plans par famille de lumière (éditable)
│   ├── shots.csv          V1–V4 (OBSOLÈTE : sous-segmentation) — remplacé par data/v5/plans.csv
│   ├── v5/                plans.csv (204 segments validés), nb_images.json, musique.json,
│                          cuts_validation.json, familles_overrides.json, masques_qualite_par_plan.csv
│   └── master/            rapports de contrôle du master final (qc_master, qc_luma, qc_rapport,
│                          tables par image, SHA256SUMS des livrables)
├── luts/
│   ├── badlife_look_v1.cube   historique — rejeté (peaux foncées assombries/bleuies)
│   ├── badlife_look_v2.cube   historique — rejeté (peaux quasi neutres bleuies)
│   ├── badlife_look_v3.cube   look V3 (remplacé par la paire V4)
│   ├── badlife_look_v4_decor.cube   V4 — appliquée hors personnes
│   ├── badlife_look_v4_sujets.cube  V4 — appliquée sur les personnes
│   ├── badlife_look_v5_nuit.cube        V5 — décor des scènes nocturnes rouges
│   ├── badlife_look_v5_nuit_ambre.cube  V5 — décor rideau métallique / nuit extérieure
│   ├── badlife_look_v5_jour.cube        V5 — décor des scènes de jour
│   ├── badlife_look_v5_1_sujets.cube    V5.1 — harmonisation très légère et globale des artistes
│   └── badlife_look_v5_1_fondu.cube     V5.1 master — fondu de fin (noirs neutres, fondu non écrasé)
└── tools/
    ├── analyze.sh         étape 1 : détection des coupes + statistiques signal
    ├── shots.py           agrégation des statistiques par plan
    ├── build_shotlist.py  génération de data/shots.csv
    ├── make_lut.py        générateur des LUT (presets versionnés v1, v2, v3)
    ├── skin_probe.py      mesure de dérive des tons chair (source vs étalonné)
    ├── render.sh          rendu : LUT + N&B préservé + vignettage + upscale 4K + export HEVC
    ├── compare.sh         vidéo de validation AVANT / APRÈS (1080p)
    ├── v4/
    │   ├── test_segment.json  plans de l'extrait, gains d'exposition, effets par plan
    │   ├── matte.py           détourage des personnes (Robust Video Matting, ONNX)
    │   ├── beats.py           tempo et attaques de la musique (transitions)
    │   ├── composite.py       rendu simultané A / B / C, compositing derrière les artistes, QC
    │   └── compare4.sh        comparatif 4 vues SOURCE | A | B | C
    └── v5/
        ├── detect_cuts.py     détection robuste des coupes (couleur, contours, normalisation locale, flashs)
        ├── build_shots.py     table des plans, ambiances, passages N&B
        ├── music.py           tempo, kicks, snares, basses, sections, impacts (+ frise)
        ├── matte_full.py      détourage du clip entier + fiabilité par image
        ├── depth.py           profondeur du décor (Depth Anything V2 Small)
        ├── composite_v5.py    compositeur V5 (artistes = source, décor étalonné + effets)
        ├── qc_extract.py      contrôle qualité automatique d'un extrait
        ├── compare_v5.sh      comparatifs 4 vues + compilation
        ├── extracts.json      les 5 extraits de validation
        ├── v5_config.json / v5_config_V5_fige.json   réglages V5 (copie figée de référence)
        ├── v5_1_config.json   réglages V5.1 (surcharges par famille et par plan, artistes harmonisés)
        ├── metrics_v51.py     mesures d'amélioration (effets, détail, noirs, profondeur)
        ├── compare_v51.sh     comparatif SOURCE | ÉTALONNAGE | V5 | V5.1 + compilation
        ├── v5_1_final_config.json   réglages du master (V5.1 + arbitrages définitifs, doc 11)
        ├── master.json / master_segments.json   clip entier ; découpage du rendu en 4 segments
        ├── rendu_segments.sh  rendu du master par segments (reprenable) + assemblage sans réencodage
        ├── qc_master.py       contrôle du master : audio bit à bit, synchro, durées, coupes, montage
        ├── qc_luma.py         continuité de luminance par plan + fondu de fin
        ├── visuel_master.py   planches d'inspection : plans, zones protégées à 100 %, transitions
        └── teaser/            teaser de sortie (doc 12)
            ├── teaser_edl.json  liste de montage (segments, textes, fondus)
            ├── teaser.py        rendu 1080x1920 50 i/s : cadrage, effets décor, typographie derrière les artistes
            ├── graphisme.py     matières procédurales (or, métal), atmosphère, braises
            └── qc_teaser.py     contrôles : format, artistes, son, écrans noirs, scintillement, textes
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

### Master V5.1 (doc 11)

Prérequis : masques du clip entier (`tools/v5/matte_full.py`) et profondeur (`tools/v5/depth.py`), voir docs 08–09.

```bash
python3 tools/make_lut.py --preset v5_1_fondu luts/badlife_look_v5_1_fondu.cube
# rendu par segments, reprenable (segments termines conserves), assemblage sans reencodage + audio source copie
tools/v5/rendu_segments.sh "source.mov" . scratch_master/ python3
F=scratch_master/final
python3 tools/v5/qc_master.py "source.mov" $F/BADLIFE_V5_1_MASTER_4K_COMPLET.mp4 data/v5/plans.csv qc_master.json
python3 tools/v5/qc_luma.py $F/qc_effets.csv data/v5/plans.csv qc_luma.json
# qc_extract attend {ID}_V5_1_COMPLET.mp4 / _ETALONNAGE_SEUL.mp4 + qc_*.csv dans un meme dossier (liens symboliques)
python3 tools/v5/qc_extract.py "source.mov" tools/v5/master.json MASTER rendu_lien/ data/v5/plans.csv data/v5/nb_images.json V5_1
python3 tools/v5/visuel_master.py "source.mov" $F/BADLIFE_V5_1_MASTER_4K_COMPLET.mp4 data/v5/plans.csv matte/ \
        '[72.017, 76.812, 88.514, 148.817]' visuel/ 12
```

La LUT `badlife_look_v3.cube` (Rec.709 / BT.1886, entrée et sortie RGB pleine échelle, 33³)
s'importe aussi telle quelle dans DaVinci Resolve, Premiere Pro ou Final Cut Pro.

## Règles de version

- Une LUT publiée n'est **jamais modifiée** : toute évolution crée un nouveau preset (`v4`, …) dans `tools/make_lut.py`.
- `tools/make_lut.py --preset v1` régénère `luts/badlife_look_v1.cube` à l'octet près (vérifié).
- Aucun média n'est commité (`.gitignore`).
