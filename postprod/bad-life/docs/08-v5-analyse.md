# 08 — V5 : sécurisation et analyse complète (étapes 1 à 3)

## 8.1 Sécurisation (étape 1)

| Contrôle | Résultat |
|---|---|
| Source `lyphik jahsIK CLIP 2.mov` | 543 621 990 octets, SHA-256 `2a6a60eb…e7263`, identique à la réception |
| Sauvegarde en lecture seule | SHA-256 identique |
| Caractéristiques | H.264 1920×1080, 50 i/s, 8760 images, BT.709 plage TV ; AAC stéréo 48 kHz ; 175,200 s (doc 02) |
| Écrasement | aucun : tous les traitements lisent la source et écrivent ailleurs |

## 8.2 Détection des coupes refaite sur 175,2 s (étape 2)

Outil : `tools/v5/detect_cuts.py`, puis validation visuelle de chaque événement.

| Critère | Rôle |
|---|---|
| Distance d'histogramme couleur HSV (Bhattacharyya) | changement de contenu |
| Différence de luminance | changement d'image |
| Normalisation locale (médiane des 16 voisins) | ne pas confondre un mouvement rapide en 25 i/s dans un fichier 50 i/s avec une coupe |
| Corrélation des **contours** après compensation du mouvement | écarter les rampes couleur → N&B (contours conservés > 0,85, contre < 0,5 pour une coupe) |
| Luminance des images voisines | repérer les **flashs** (image claire entre deux images semblables) |

Calibration sur l'extrait de test V4 : les 9 coupes connues sont retrouvées, le faux positif
connu (44,22 s) est écarté, la rampe N&B du plan 28b est écartée.

**Découverte** : les « faux positifs » restants à 46,84–47,12 s sont en réalité **de vraies coupes**
d'un montage alterné toutes les 2 images entre deux angles (vérifié image par image). La
« vérité terrain » de la V4 était elle-même incomplète.

Résultat initial : 208 candidats (186 coupes, 22 flashs), regroupés en 141 événements (dont 28
salves), **tous revus visuellement** (6 planches avant / après).

**Erratum (même jour)** : une étape de fusion des détections consécutives masquait 57 coupes, dont
des **inserts d'une seule image** (84,50 s, une image de la scène rouge dans un plan de cité) et une
vraie coupe suivant immédiatement une salve de flashs (93,30 s). Le défaut a été repéré grâce à un
saut de mesure dans le contrôle qualité de l'extrait 1. La fusion est supprimée ; les nouvelles
coupes situées hors des salves ont été revues visuellement. Le détourage a été refait sur les
30 images suivant chacune des 56 nouvelles coupes (réinitialisation de l'état RVM) ; la profondeur
et l'analyse musicale ont été recalculées.

Résultat final : 265 candidats (243 coupes, 22 flashs). 6 rejets
([`../data/v5/cuts_validation.json`](../data/v5/cuts_validation.json)) :
- 69,72 s et 98,34 s : pulsations lumineuses dans le même plan (même cadrage) ;
- 170,86 / 171,38 / 171,78 / 172,20 s : bruit dans le noir du fondu de fin.

**Table des plans réels** : [`../data/v5/plans.csv`](../data/v5/plans.csv), **260 segments**
(90 plans ≥ 0,3 s, 170 micro-segments de salves et inserts), couvrant exactement 175,2 s. Elle
remplace `data/shots.csv` (V1–V4, qui sous-segmentait). Les segments d'une seule image sont classés
« effet de montage ».

## 8.3 Classement par ambiance

Pré-classement automatique (luminance, saturation, parts de rouge, vert et beige), puis **revue
visuelle** des 90 plans ≥ 0,3 s : 23 corrections manuelles
([`../data/v5/familles_overrides.json`](../data/v5/familles_overrides.json)). **Deuxième revue**,
sur 4 images réparties sur chaque plan corrigé et non plus une seule vignette : 2 corrections
étaient fausses et ont été rectifiées (84,06 s : cité de jour, pas nuit rouge ; 55,90 s :
extérieur de jour nuageux, pas nuit). Les corrections s'appliquent avec une tolérance de 2 images
sur le début du plan, pour résister à l'ajout d'une coupe voisine. 13 plans de cité sous
la cage d'escalier étaient classés « nuit » parce qu'ils sont sombres ; 6 plans très sombres du décor
rouge étaient classés « nuit extérieure ». Les micro-segments héritent de l'ambiance du plan
voisin le plus ressemblant (distance d'histogramme).

| Famille | Segments | Durée |
|---|---:|---:|
| A — Cité de jour | 46 | 84,6 s |
| B — Nuit rouge (décor « BIENVENUE ») | 39 | 36,5 s |
| C — Rideau métallique (lumière chaude) | 16 | 24,9 s |
| D — Nuit extérieure (lampadaires) | 10 | 5,2 s |
| N&B (micro-plans) | 3 | 0,2 s |
| Fondu de fin | 2 | 13,2 s |
| X — Effets de montage (flash, filé, glitch, pulsation, inserts d'une image) | 144 | 10,6 s |

Les segments X ne reçoivent **aucun effet ajouté** : on ne superpose rien aux transitions du
monteur. Ils sont seulement étalonnés, avec la LUT du plan voisin le plus ressemblant.

## 8.4 Passages noir et blanc (image par image)

Mesure : chrominance YUV moyenne des tons moyens (Y entre 40 et 220). Calibration sur images
connues : N&B 1,8 à 2,0, couleur même très désaturée ≥ 4,0. Seuil retenu : 3,0. Une image dont moins
de 30 % des pixels sont en tons moyens (nuit très sombre, fondu au noir) n'est pas classée N&B.
La première mesure (saturation HSV) était fausse, car les pixels sombres bruités paraissent
saturés ; elle a été remplacée.

| Passage | Nature |
|---|---|
| 18,86–18,92 / 19,00–19,08 / 19,16–19,22 s | micro-plans N&B alternés avec la couleur (salve) |
| 41,28–41,68 s | rampe couleur → N&B → couleur (plan 28b) |
| 75,62–76,56 s | plan N&B (ancien plan #60) |

## 8.5 Analyse musicale

Outil : `tools/v5/music.py`, avec frise en [`img/v5_musique.png`](img/v5_musique.png).

| Mesure | Résultat |
|---|---|
| Tempo | **99,4 BPM** (temps 0,604 s, mesure 2,41 s) |
| Kicks / snares | 147 / 221 détectés (flux spectral 40–120 Hz / 1,5–8 kHz) |
| Coupes du montage sur un temps (≤ 60 ms) | 53 sur 259 |
| Impacts retenus (kick + snare + saut d'énergie) | 40 |

**Correction en cours d'analyse** : la première estimation donnait 132,5 BPM. Les pics
d'autocorrélation sont tous multiples d'une unité de 0,151 s (doubles croches). Le plus fort,
2,40 s, correspond à une mesure de 4 temps de 0,60 s. La valeur à 132,5 BPM correspondait à la
syncope « 3-3-2 » des kicks (intervalles de 3 doubles croches). L'estimateur retient désormais la
période dont les multiples sont les plus corrélés (filtre en peigne).

**Sections** : 20 sections détectées par rupture de timbre, classées par **intensité mesurée** (forte /
moyenne / calme). Les sections fortes sont à 33,2–39,2 / 71,2–77,9 / 85,1–94,8 / 148,5–154,6 s ; le
même timbre revient à 71–78, 104–114 et 148–155 s. **Hypothèse non vérifiée** : ce sont les
refrains. Dans ce morceau, la même boucle tourne du début à la fin et le timbre ne sépare pas
couplet et refrain ; le placement des refrains est à confirmer par l'artiste.

## 8.6 Masques (étape 3)

Détourage du clip entier : `tools/v5/matte_full.py` (RVM, état remis à zéro à chaque frontière de
plan), avec des indicateurs de fiabilité par image : part de bord incertain et instabilité
temporelle ([`../data/v5/masques_qualite_par_plan.csv`](../data/v5/masques_qualite_par_plan.csv)).

| Indicateur (plans ≥ 0,3 s) | Médiane | 90e percentile | Max |
|---|---:|---:|---:|
| Surface personnes | 0,387 | 0,553 | 0,736 |
| Part de bord incertain | 0,105 | 0,227 | 0,389 |
| Instabilité temporelle | 0,027 | 0,050 | 0,087 |

Un seul plan dépasse les seuils de difficulté (138,24 s, cité de jour, sans effet ajouté).
**Limite** : ces indicateurs mesurent la *stabilité* du masque, pas son *exhaustivité*. Une personne
d'arrière-plan jamais détectée (cas observé en V4 : silhouettes floues devant le rideau métallique)
n'y apparaît pas ; seul le contrôle visuel la repère.

### Correction manuelle des masques
Elle demande un compositeur humain (rotoscopie dans Resolve, Fusion, After Effects ou Mocha) et
n'est pas réalisable dans cet environnement. Mesure compensatoire, conforme au §2 (« réduire ou
supprimer l'effet ») : les effets sont **atténués automatiquement** quand le masque est instable ou
incertain (`confiance_masque` dans `tools/v5/v5_config.json`).
