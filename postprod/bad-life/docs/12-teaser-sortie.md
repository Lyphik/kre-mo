# 12 — Teaser de sortie officiel (30 s, vertical)

> Brief reçu le 2026-11-10 : teaser de 30 s, vertical 9:16, annonçant « BAD LIFE — LYPHIK feat. JAHSIK —
> MAINTENANT DISPONIBLE ! », pour Instagram Reels, TikTok, Facebook Reels et YouTube Shorts. Il est
> monté exclusivement à partir du clip officiel, avec une règle absolue de respect des artistes.

## 12.1 Sources et identification

| Élément | Source |
|---|---|
| Images | master V5.1 4K validé (`BADLIFE_V5_1_MASTER_4K_COMPLET.mp4`, doc 11) : aucune autre image, aucune image générée |
| Son | piste audio **originale** de la source (même flux, bit à bit, que le master) |
| Masques des artistes | masques alpha du clip entier (doc 08–09), une image par image source |
| Rythme | `data/v5/musique.json` : tempo 99,4 BPM, temps, kicks, snares, sections |
| Identification | **LYPHIK = B et C** (cagoule noire et sacoche ; dreadlocks et doudoune rouge), **JAHSIK = A et D** (maillot rouge Manchester Athletics ; casquette « L » et maillot gris). Indiquée par l'utilisateur sur la planche des personnes récurrentes ; elle n'est pas déduite. |

## 12.2 Choix du passage musical

Le passage est un extrait **continu** de 30 s du morceau, de **69,58 à 99,58 s**. Il a été choisi
parmi toutes les fenêtres de 30 s calées sur les temps, selon deux critères : la part d'images de nuit
et la part de rouge (61 % et 36 % autour de ce départ, le maximum du clip), puis l'énergie musicale.

| Teaser | Morceau | Section | Rôle dans le brief |
|---|---|---|---|
| 0–1,7 s | 69,6–71,2 s | C (moyenne) | introduction |
| 1,7–8,3 s | 71,2–77,9 s | E (**forte**) | introduction → révélation |
| 8,3–15,5 s | 77,9–85,1 s | D (moyenne) | révélation → explosion |
| 15,5–25,2 s | 85,1–94,8 s | C (**forte**) | explosion → annonce |
| 25,2–30 s | 94,8–99,6 s | D (moyenne) | final |

Le départ (69,58 s) est la coupe d'origine du plan du couloir vert où LYPHIK et JAHSIK apparaissent
ensemble.

## 12.3 Montage

Liste de montage : `tools/teaser/teaser_edl.json` (24 segments, vérifiés contre la table des plans).

- **Segments calés** : 10 segments, dont la synchronisation labiale exacte de tous les plans d'artistes
  du passage. L'image vient du même instant que le son : couloir vert, rideau métallique,
  LYPHIK au conteneur, duo de nuit, JAHSIK en maillot rouge, LYPHIK devant « BIENVENUE »…
- **Inserts** : 14 segments. Ils remplacent les plans de **jour** et les **flashs blancs** du passage,
  hors de la direction nocturne et rouge du brief. Ce sont des plans de nuit du clip, coupés sur les
  temps. Chaque insert reste à l'intérieur d'un seul plan source (aucune coupe d'origine franchie) et
  aucun plan n'est répété. Ces inserts courts (0,4 à 1,5 s) ne sont pas synchronisés sur les paroles.
- **Final** : le plan P222 (LYPHIK et JAHSIK côte à côte devant « BIENVENUE ») joue de 25,2 à 26,0 s,
  puis **se fige sans rupture** à 131,66 s jusqu'à 30 s. L'image arrêtée évite toute
  désynchronisation labiale pendant la lecture des textes.

**Règle de cadrage vertical (cohérence)**

- **Plans d'un artiste seul** : recadrage 9:16 **plein écran**. Le centre est calculé automatiquement
  par plan source, d'après les masques, et le cadre reste fixe dans chaque plan.
- **Plans de duo** : l'image 16:9 est placée dans une **bande cinéma** centrale (1080 × 720), sur fond
  noir et rouge généré. Les deux artistes restent entièrement visibles, et les textes occupent les
  zones au-dessus et au-dessous de la bande.
- **Mouvement** : seule une lente avancée (homothétie de 2 à 6 %) est appliquée. Aucune déformation,
  aucun changement de vitesse.

Le teaser s'ouvre dans la bande (introduction), passe en **plein écran sur le temps fort de 5,2 s**
(révélation et explosion), puis revient à la bande pour l'annonce et le final.

## 12.4 Respect des artistes

Formule identique à celle du master :
`sortie = alpha × ARTISTES + (1 − alpha) × (DÉCOR + effets + textes)`, avec alpha ≥ 0,97 ramené à 1.

- **Artistes** : pixels du master, seulement recadrés et redimensionnés (même homothétie sur les deux
  axes). Aucune retouche, aucun visage modifié, aucune génération.
- **Effets, sur le décor uniquement** : assombrissement, virage rouge des ombres, vignettage,
  éclair de lumière rouge sur les coupes (de 5,2 à 20 s) et sur « MAINTENANT DISPONIBLE ».
- **Textes** : posés **derrière** les artistes, jamais par-dessus, ou dans les bandes hors image.
- **Seule exception** : l'ouverture au noir des 0,8 premières secondes. C'est une transition,
  autorisée par le brief, et elle est exclue du contrôle strict.
- **Contrôle** : `qc_teaser.csv` donne, pour chaque image, l'écart maximal entre la sortie et le
  master recadré sur les pixels d'artistes, **avant** l'encodage H.264. Il doit être nul.

## 12.5 Textes

| Moment | Texte | Typographie |
|---|---|---|
| 0,55–4,95 s | **LYPHIK** / présente… | Anton (titre), Inter Display SemiBold |
| 7,70–12,0 s | **BAD LIFE** (apparition frappée sur le temps) | Anton, rouge |
| dès 20,0 s | **BAD LIFE** | Anton, rouge |
| dès 20,37 s | **LYPHIK feat. JAHSIK** | Inter Display Black |
| dès 23,11 s (kick + snare) | **MAINTENANT DISPONIBLE !** sur bandeau rouge | Anton, blanc |
| dès 26,41 s | **DISPONIBLE SUR YOUTUBE** / **REGARDEZ LE CLIP !** | Inter Display Black |

- **Durée de lecture** : « MAINTENANT DISPONIBLE ! » reste à l'écran 6,9 s, jusqu'à la dernière image.
- **Typographie française** : espace insécable avant « ! ».
- **Appel à l'action** : il tient sur deux lignes. Le tiret cadratin du brief
  (« DISPONIBLE SUR YOUTUBE — REGARDEZ LE CLIP ! ») est remplacé par le retour à la ligne, c'est un
  choix de mise en page.
- **Zones sûres** : tous les textes restent entre y = 130 et y = 1610 et à plus de 60 px des bords.
  La partie basse de l'écran est ainsi laissée aux interfaces de Reels, TikTok et Shorts.
- **Polices** :
  - Anton (SIL Open Font License 1.1, paquet npm `@fontsource/anton` 5.0.20), non versionnée ici ;
  - Inter Display (police système).

## 12.6 Son

- **Extrait** : extrait original de 69,58 à 99,58 s.
- **Fondus** : fondu d'entrée de 0,8 s, calé sur l'ouverture au noir, et fondu de sortie de 1,4 s
  (28,6 → 30 s).
- **Encodage** : AAC 256 kb/s. Il y a un réencodage, imposé par les fondus, à un débit double de
  l'original (126 kb/s).
- **Effets sonores** : aucun ajouté (« éventuellement » dans le brief), pour préserver le son original.

## 12.7 Format

- **Image** : `BAD_LIFE_TEASER_30S_OFFICIAL.mp4`, 1080 × 1920, 50 i/s (cadence du clip), 30,00 s
  (1500 images).
- **Encodage** : H.264 High 4.2, CRF 16, BT.709 plage TV.
- **Son** : AAC 256 kb/s.

Reproduction : `tools/teaser/teaser.py` (rendu image par image, sortie brute vers ffmpeg). Les commandes
exactes et les contrôles sont donnés en §12.8.
