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
- **Final** : le plan P222 (LYPHIK et JAHSIK côte à côte devant « BIENVENUE ») joue depuis sa première
  image, de 25,20 à 25,74 s, puis **se fige** jusqu'à 30 s sur **l'image la plus nette du plan**
  (130,90 s). La netteté est mesurée par la variance du laplacien sur les pixels des artistes ; l'image
  d'abord prévue, à 131,66 s, était floue de bougé. L'image arrêtée évite toute désynchronisation
  labiale pendant la lecture des textes.

**Règle de cadrage vertical (cohérence)**

- **Plans d'un artiste seul** : recadrage 9:16 **plein écran**.
- **Plans de duo** : l'image 16:9 est placée dans une **bande cinéma** centrale de 1080 × 720, soit
  84 % de la largeur de l'image, sur un fond noir et rouge généré. Les textes occupent les zones
  au-dessus et au-dessous de la bande.
- **Position du cadre** : elle est automatique et reste fixe dans chaque plan source. C'est la fenêtre
  qui garde **le plus de pixels d'artistes visibles**, d'après les masques, sur quelques images du plan.
- **Final** : le cadre est imposé (x = 0 à 1620 en coordonnées 1080p), car le masque couvre presque toute
  la largeur à cause du bras tendu de JAHSIK. Les deux artistes sont entiers, seule la main tendue sort
  du cadre ; le cadrage automatique donne d'ailleurs la même fenêtre.
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
| 9,16–10,96 s | **BAD LIFE** (apparition frappée sur la coupe du duo, durée du plan du duo) | Anton, rouge |
| dès 20,0 s | **BAD LIFE** | Anton, rouge |
| dès 20,37 s | **LYPHIK feat. JAHSIK** | Inter Display Black |
| dès 23,11 s (kick + snare) | **MAINTENANT DISPONIBLE !** sur bandeau rouge | Anton, blanc |
| dès 26,41 s | **DISPONIBLE SUR YOUTUBE** / **REGARDEZ LE CLIP !** | Inter Display Black |

- **Durée de lecture** : « MAINTENANT DISPONIBLE ! » reste à l'écran 6,9 s, jusqu'à la dernière image.
- **Animation « frappée »** : agrandissement de 1,10 à 1,0 en 0,18 s. Le texte agrandi reste dans les
  marges, donc il n'est jamais coupé, même pendant l'animation.
- **Bandeau rouge** : sa largeur est calculée d'après le texte, avec 40 px de chaque côté.
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

## 12.8 Contrôles et corrections

`tools/teaser/qc_teaser.py` vérifie le format, les artistes, le son, les écrans noirs, le scintillement
(une image signalée est « expliquée » si la source a le même saut au même instant) et l'emprise des
textes. Le rendu enregistre, image par image, l'écart des artistes et la boîte englobante des lettres.

**Premier rendu (v1)** : contrôle automatique CONFORME. La seule image signalée, 2,6 s, est expliquée
par un éclair présent dans la source (72,18 s). L'inspection visuelle a toutefois relevé quatre défauts,
corrigés en v2 :

1. « MAINTENANT DISPONIBLE ! » débordait de son bandeau, et le « ! » touchait presque le bord de l'écran.
   Le corps passe à 86 px et le bandeau est calculé d'après le texte.
2. Le titre de la révélation (7,70 s) était à moitié caché derrière la tête de LYPHIK. Les textes étant
   derrière les artistes, ils ne doivent pas se superposer à eux. Le titre apparaît donc à 9,16 s, sur la
   bande du duo, où la zone haute est libre.
3. L'insert de 5,89 s (P249) était sombre de bout en bout. Il est remplacé par LYPHIK au rideau
   métallique (P232).
4. L'image arrêtée du final était floue de bougé. Elle est remplacée par l'image la plus nette du plan.

Le contrôle de l'emprise des textes a été ajouté à cette occasion (lettres à 40 px au moins des bords,
entre y = 100 et y = 1650).

**Deuxième rendu (v2)** : contrôle automatique CONFORME, textes compris (emprise x = 59 à 1021,
y = 178 à 1608). L'inspection visuelle a relevé deux défauts, corrigés en v3 :

1. Sur les bandes de duo, le cadre se centrait sur la plus grande personne : LYPHIK était coupé au bord
   gauche sur l'image arrêtée du final, et JAHSIK sur le plan P204. Le cadre garde désormais le plus de
   pixels d'artistes visibles, et celui du final est imposé.
2. De 10,96 à 12 s, la main levée de JAHSIK passait devant « BAD LIFE », ce qui est normal puisque le
   texte est derrière les artistes. Le titre de la révélation s'arrête donc à la fin du plan du duo
   (10,96 s), après 1,8 s pleinement lisible.

## 12.9 Version PREMIUM : refonte de la direction artistique

Directive reçue après les premiers aperçus : la présentation graphique était jugée trop simple (bandeau
rouge, pochette basique). Le montage de 0 à 20 s est **conservé**. La refonte porte sur la
typographie, la pochette, l'annonce, l'écran final et la cohérence graphique. Livrable :
`BAD_LIFE_TEASER_30S_PREMIUM.mp4`. Un aperçu est soumis à l'utilisateur avant l'export définitif.

### Identité typographique reprise du clip

| Élément du clip (0–7,4 s) | Analyse | Teaser |
|---|---|---|
| « BAD LIFE » | capitales à empattements triangulaires de type inscription romaine (famille Trajan), très grasses, inclinées, empilées sur deux lignes ; matière **or en fusion** (paillettes, reflets diagonaux, liseré sombre) | **Cinzel 900** inclinée de 12° (alternative la plus proche ; la police exacte n'est pas identifiable), empilée sur deux lignes, matière or recalculée |
| « LYPHIK X JAHSIK » | capitales linéales condensées blanches | **Bebas Neue** (correspondance visuelle) |

- **Polices du clip** : leur nom n'est consigné nulle part. L'identification repose sur une comparaison
  visuelle, côte à côte (planche `comparaison_polices.jpg`, non versionnée).
- **Polices du teaser** : Cinzel et Bebas Neue (SIL OFL 1.1), via les paquets npm `@fontsource/cinzel`
  5.2.8 et `@fontsource/bebas-neue` 5.0.18. Ce sont **deux familles seulement**, comme dans le clip.
- **« feat. »** : il est composé en Cinzel or, plus petit. Les deux familles de l'identité n'ont que des
  capitales, donc « feat. » s'affiche en petites capitales.

### Graphisme (`tools/teaser/graphisme.py`)

Toutes les matières sont **procédurales** : elles sont calculées, aucune image n'est importée, et le
calcul est déterministe.

- **Or** : biseau calculé d'après la distance au bord, éclairage diffus et spéculaire, reflets
  diagonaux, grain et paillettes, reflet **rouge** sur les faces tournées vers le bas (la lumière du
  conteneur), liseré sombre, relief extrudé, ombre portée et lueur.
- **Métal** (« MAINTENANT DISPONIBLE ! ») : métal clair brossé, bande de reflet rouge, biseau, relief
  extrudé rouge sombre.
- **Atmosphère** : fumée rouge veloutée qui dérive lentement, rayons de lumière venus du haut,
  vignettage, grain fin, braises qui s'élèvent autour du titre.

### Composition

- **Introduction et duo de la révélation** : l'image 16:9 est placée **entière** dans une bande de
  1080 × 608, aucune tête n'est coupée. Le décor se fond dans l'atmosphère aux bords, avec des filets or.
- **Pochette (20–30 s)** : l'image est ancrée en bas de l'écran, donc aucune coupe du corps n'est
  visible. L'échelle garde les artistes entiers en largeur quand le plan le permet ; sinon elle suit
  leurs têtes, avec de larges marges. Les têtes restent toujours sous le bloc typographique (y ≥ 990).
  Le décor se fond vers le haut dans l'atmosphère. Le bloc typographique reste fixe, et les plans
  défilent dessous sur les temps.
- **Image finale** : **P154 à 99,44 s**, LYPHIK et JAHSIK côte à côte devant « BIENVENUE ». C'est
  l'une des images où les deux artistes sont entiers et nets (recherche automatique sur les plans de
  duo : silhouettes entières, netteté). Avancée lente de 2 %.
- **Plein écran** : la fenêtre doit contenir la **tête de chaque artiste**. Le contrôle compte les
  têtes coupées image par image (colonne `tetes_coupees`).

### Animations calées sur la musique

| Temps | Animation |
|---|---|
| 0,55 s | « LYPHIK » dévoilé par un front lumineux, puis « présente… » |
| 9,16 s (coupe) puis 9,41 s | « BAD », puis « LIFE », forgés par un front incandescent, avec braises |
| 20,00 s (coupe) puis 20,37 s (temps) | « BAD », puis « LIFE », en grand ; éclats de lumière tous les 4 temps |
| 20,98 s (temps) | « LYPHIK feat. JAHSIK » (fondu, montée de 18 px) |
| 23,11 s (kick + snare) | « MAINTENANT DISPONIBLE ! » lettre par lettre, en cascade (18 ms par lettre), éclair de lumière sur le décor, éclat métallique au temps suivant |
| 26,41 s (temps) | « DISPONIBLE SUR YOUTUBE — REGARDEZ LE CLIP ! » sur une ligne, avec le tiret du brief |

## 12.10 Fin vivante (19,5–30 s) : décisions de l'utilisateur après l'aperçu premium

| Décision | Mise en œuvre |
|---|---|
| Supprimer l'appel à l'action | supprimé, remplacé par aucun texte. Textes : « BAD LIFE », « LYPHIK FEAT. JAHSIK », « MAINTENANT DISPONIBLE ! » |
| Cadrage des artistes, sans effet « découpé-collé » | disposition « couverture » abandonnée. La fin est en **plein écran vertical**, comme le reste du teaser, avec des cadrages naturels |
| Supprimer la grosse fumée rouge | la fin n'utilise plus de fond généré. Dans les bandes du début, la fumée est réduite au quart |
| Supprimer l'image figée | plus d'image arrêtée ni d'avancée sur la fin. Seuls les mouvements réels du clip sont utilisés, sans aucune interpolation |
| Or plus noble | paillettes réduites de 35 % (densité de 0,35 % à 0,23 % des pixels) ; relief et grands reflets conservés |
| Montage 0–20 s conservé | segments identiques. Seule la règle de cadrage est améliorée (voir ci-dessous) |

**Constats sur les rushs**

Ce sont des faits mesurés sur les masques, pas des hypothèses.

- **Pieds jamais visibles** : dans tous les plans de nuit, le corps des artistes dépasse le bas de
  l'image (bas des silhouettes à y = 1080). Montrer les artistes « entièrement » est impossible, et rien
  n'est généré.
- **Duos trop larges pour un cadre vertical** : en plein écran vertical, le cadre ne fait que 607 px de
  large dans l'image 1080p, alors que les têtes des duos sont écartées de 640 à 800 px. Les deux têtes ne
  tiennent ensemble que pendant 0,14 à 0,32 s (P194, P33, P87). Les deux artistes **alternent** donc au
  rythme de la musique.
- **Peu d'espace libre au-dessus des têtes** : dans les meilleurs plans, les têtes commencent à environ
  480 px du haut de l'écran.
  - Mesuré avec un cadrage naturel, le titre (noms et « BAD LIFE » à 75 % des proportions validées)
    passe de 0 à 8 % derrière les artistes sur les plans retenus.
  - Une ligne « MAINTENANT DISPONIBLE ! » placée sous le titre passerait de 25 à 84 % derrière les têtes.
  - Les textes se succèdent donc dans la même zone haute : d'abord le titre et les noms, puis
    l'annonce, sur deux lignes.

**Règle de cadrage (plein écran)**

Le cadre est fixe par plan, et sa position est choisie par un score calculé image par image :

- 3 × (part des images où la tête de l'artiste principal est entière) ;
- − 1,5 × (nombre moyen de visages tranchés par un bord) ;
- \+ (pixels d'artistes visibles).

Une première version, qui interdisait absolument toute coupe de visage, produisait des cadres sans
artiste : elle a été écartée. Pour P237, le masque fusionne le groupe : le cadre est imposé sur LYPHIK,
et le visage du voisin reste entièrement hors cadre.

**Nouvelle fin**

| Temps | Plan | Texte |
|---|---|---|
| 20,00–21,58 s | JAHSIK, P221 | « BAD » (20,00 s), « LIFE » (20,37 s), « LYPHIK FEAT. JAHSIK » (20,98 s) |
| 21,58–23,11 s | LYPHIK, P237 | le titre se dissipe sur 0,18 s avant 23,11 s |
| 23,11–24,60 s | JAHSIK de nuit, P236 | « MAINTENANT / DISPONIBLE ! » en cascade, lettre par lettre (kick + snare) |
| 24,60–25,81 s | JAHSIK, P31 | l'annonce s'efface, avec une légère montée, sur 0,35 s jusqu'à 25,81 s |
| 25,81–27,52 s | P194, P33 | aucun texte : conclusion entièrement vidéo |
| 27,52–30,00 s | P149, couloir vert, P154 | **synchronisation labiale exacte**. Le teaser se termine sur la dernière image de P154, en mouvement réel |

Le son se termine par un fondu de sortie de 1,8 s (28,2 → 30 s), calé sur le dernier plan.
