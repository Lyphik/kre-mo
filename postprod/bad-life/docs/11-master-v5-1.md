# 11 — Master V5.1

> Validation de la direction V5.1 et arbitrages définitifs reçus le 2026-11-09, avec autorisation de
> lancer le master **si les vérifications des plans concernés passent**.

## 11.1 Arbitrages appliqués

Configuration : `tools/v5/v5_1_final_config.json` = V5.1 validée (`v5_1_config.json`, inchangée)
+ les arbitrages ci-dessous. Aucun pipeline recréé, aucune modification du montage, aucune
nouvelle exploration.

| # | Arbitrage | Mise en œuvre |
|---|---|---|
| 1 | Conteneur : couloir vert = étalonnage harmonisé seul, sans brume ni VFX ; ne pas l'appliquer aux autres plans de 114,1–120,7 s | 18 plans du **décor du couloir vert** (conteneur, tubes LED verts au sol, rideaux rouges), identifiés visuellement sur 4 images par plan : tous les effets à 0. Dans 114,1–120,7 s : 118,88–120,10 s et 120,42–120,74 s. Le rideau (114,14 s), le conteneur rouge (115,80–117,20 s) et la nuit extérieure (117,20 s) gardent la V5.1. |
| 1-bis | **Interprétation à confirmer** | Le même décor apparaît aussi à 38,46 / 44,48 / 69,58 / 76,84 / 97,10 / 105,76 / 122,76 / 128,32 s (et dans des micro-plans de salves). Par cohérence entre ambiances, la décision leur est appliquée. Réversible plan par plan (section `plans` de la configuration). |
| 2 | Particules : réduction actuelle conservée, aucune réintroduite | inchangé par rapport à la V5.1 |
| 3 | Contre-jour inventé retiré | `contre_jour_force = 0` pour toutes les familles (le contre-jour n'était dérivé d'aucune source réelle). Les rayons issus d'une vraie lampe du décor et toutes les lumières des prises de vues sont conservés. |
| 4 | Artistes légèrement harmonisés | inchangé (LUT globale `v5_1_sujets`, aucune retouche locale) |
| 5 | Les 4 transitions à intensité réduite, pas de speed ramp | inchangé (force 0,3, descente 90 ms, jamais sur un plan de jour) |
| 6 | Jour et N&B inchangés | inchangé |

Audio du master : **flux original copié bit à bit** (option `audio_copie`, uniquement pour le clip entier).

## 11.2 Vérification courte avant master (plans concernés)

7 fenêtres (couloir vert à 44,5 / 70,8–74,0 / 76,0–79,0 / 96,9–99,6 / 118,5–121,0 s ; transitions
88,5 et 148,8 s, hors extraits de validation).

| Contrôle | Résultat |
|---|---|
| Couloir vert : écart avec l'étalonnage seul (hors transitions) | **0,00000** sur 364 images |
| Contre-jour inventé | **0** partout |
| Artistes : pixels opaques = source + LUT globale | écart **0** |
| Trou de masque (second personnage partiellement détouré, 44,5 s) | aucune démarcation visible à 100 % : sur ces tons très sombres, étalonnages artistes et décor quasi identiques |
| Variation de luminosité sur les plans désactivés | impossible par construction : étalonnage image par image, sans traitement temporel |
| Transitions 72,02 / 76,84 / 88,51 / 148,82 s | déclenchées sur les vraies coupes, lisibles et sobres ; plans de jour sortants propres |

**Verdict : vérification passée → master lancé.**

## 11.3 Premier rendu du master : contrôle non passé, correction ciblée

Premier rendu complet (2 h 23, ≈ 1 image/s) puis contrôle du master
(`tools/v5/qc_master.py`) :

| Contrôle | Résultat |
|---|---|
| Audio original copié bit à bit (SHA-256 des paquets) | **identique** : `b567694f…bb1f4194` |
| Durées vidéo / audio, nombre d'images | 175,200 s / 175,200 s, **8760** images |
| Coupes (259 frontières validées) | **259 / 259** : même saut dans la source et dans le master |
| Montage image par image | 5 images signalées, toutes dans le **fondu au noir final** (168,42–168,74 s) |

L'examen du fondu a mis en évidence un **défaut réel** : le pied de courbe de la LUT de jour et
l'harmonisation des artistes assombrissaient le fondu plus vite que la source, qui atteignait
10 % de son niveau initial **0,48 s trop tôt** (168,60 s contre 169,08 s). Le fondu fait partie
du montage : il doit suivre la source. **Le master n'a pas été déclaré prêt.**

Correction minimale, limitée à la famille `OUTRO_fondu` (161,7–175,2 s) :

- nouvelle LUT `v5_1_fondu` : preset `v5_jour` avec une courbe **neutre sous 0,20** (aucune
  LUT existante modifiée, `v5_jour` et `v5_1_sujets` régénérées à l'octet près) ;
- `artistes_mode: source` sur ce plan : pixels des artistes = source.

Vérification sur la fenêtre 161,7–175,2 s avant de relancer : luminance sortie / source
identique à chaque image (résidu ≤ 0,0025), seuils 50 / 25 / 10 % atteints **à la même image**,
écart des artistes **0**.

Le contrôle du montage a aussi été **renforcé** : la première version excluait 5532 images
« quasi fixes » (doublons 25p dans 50p) comme non décidables. Désormais, chaque image est
comparée à ±3 images. Elle n'est fausse que si elle ressemble davantage à une image source
réellement différente de la sienne. Seules les images quasi uniformes (noir) restent non
décidables.

Le premier rendu est conservé hors dépôt, à titre de traçabilité ; il n'est pas livré.

## 11.4 Second rendu : interruption du conteneur, rendu par segments

Le second rendu monolithique a été **interrompu à l'image 5050 / 8760** par un redémarrage du
conteneur de travail (incident d'infrastructure, sans lien avec les réglages). Le MP4 écrit avec
`faststart` n'a son index qu'en fin de fichier : il était tronqué et **inexploitable**. Pour qu'une
nouvelle interruption ne fasse perdre qu'un segment, le master est désormais rendu en **4 segments
reprenables**, puis assemblé sans réencodage.

**Condition : le résultat doit être identique au rendu monolithique.** Le compositeur remet son
état à zéro à chaque coupe (caméra, masque lissé, sources lumineuses, particules), sauf quatre
éléments qui traversent les plans. L'option `PREROLL=1` (désactivée par défaut, comportement
inchangé sans elle) les rejoue :

| État inter-plans | Rejoué par |
|---|---|
| Générateur aléatoire des particules (un tirage par plan) | mêmes tirages, dans le même ordre, pour tous les plans précédant le segment |
| Moyenne glissante de la confiance du masque | recalculée sur toutes les images précédentes (table de qualité des masques) |
| Transitions musicales (alternance gauche / droite) | calculées sur le clip entier |
| Gain des effets lors des flashs du montage | bornes choisies après ≥ 45 images sans flash : le gain vaut alors exactement 1 |

Bornes retenues (débuts de plans, à plus de 1 s de toute transition, sans flash avant) :
**45,60 s** (image 2280), **90,54 s** (4527), **130,36 s** (6518).

**Preuve d'équivalence**, avant de lancer le rendu, contre les tables par image écrites par le
rendu interrompu (images 0–5007) :

| Fenêtre | Contenu | Écarts (qc_effets 17 colonnes + qc_artistes) |
|---|---|---|
| 45,60–47,60 s, avec `PREROLL` | nuit rouge, avec fumée, rayons, halos, flares, particules ; franchit une coupe | **0** sur 100 images |
| 90,54–92,54 s, avec `PREROLL` | jour | **0** sur 100 images |
| 45,60–47,60 s, **sans** `PREROLL` (témoin) | — | **311** cellules sur 1700 |

Le témoin montre que le test est sensible. L'assemblage (`tools/v5/rendu_segments.sh`)
concatène les flux vidéo **sans réencodage**. Il y ajoute le flux audio **original de la source,
copié tel quel**. Chaque segment est encodé avec les mêmes réglages (x265 Main10, CRF 16, VBV
80 Mb/s) et commence par une image clé : la qualité d'encodage est la même que celle d'un rendu
d'un seul tenant. Seule la position des images clés change.

## 11.5 Contrôles du master assemblé : deux défauts trouvés et corrigés

### 11.5.1 Décalage vidéo / audio de 21 ms à l'assemblage

Premier assemblage : la vidéo démarrait à 0,021 s et l'audio à 0, contre 0 / 0 dans la source.
La vidéo était donc **en retard d'une image** sur le son. Cause : le démultiplexeur `concat` calait le
départ sur la piste AAC des segments (délai d'amorçage de −21 ms). Le contrôle image par image ne
pouvait pas le voir : il compare des indices d'images, pas des horodatages.

- Correction : concaténation des **seules pistes vidéo**, puis ajout de l'audio original de la
  source (`rendu_segments.sh`). Aucun re-rendu : seul l'assemblage est refait.
- Contrôle ajouté (`qc_master.py`, `synchro_horodatage`) : l'écart de départ vidéo − audio doit
  être celui de la source. Il aurait signalé le fichier fautif (0,021 s contre 0).

### 11.5.2 Pulsation à 25 Hz des halos sur la source 25p doublée

Le contrôle du scintillement (`qc_extract.py`) a signalé plusieurs images au-dessus du seuil de 12 %.
Leur examen a mis en évidence un **défaut réel, introduit par le traitement**. La source est en 25p
doublée en 50p : une image sur deux est identique à la précédente. Sur ces images doublons, les
halos, la halation et les flares anamorphiques changeaient quand même, alors que l'image ne bougeait
pas. Le résultat était une **pulsation à 25 Hz** des halos pendant les mouvements de caméra.

| Mesure (pixels du master, effet = COMPLET − ÉTALONNAGE SEUL, codes 10 bits) | Avant |
|---|---|
| Variation de l'effet sur une image doublon, p99,9 | 41 à 48 |
| Variation maximale sur une image doublon | 90 à 118 (≈ 11 % de la pleine échelle) |
| Images à halos sur doublon | 140, dans les 4 segments |

Cause : la carte des sources lumineuses est lissée dans le temps avec compensation du mouvement
caméra, puis seuillée de façon non linéaire. Sur un doublon, le mouvement mesuré est nul ; sur
l'image suivante, il est double. La carte lissée se recale donc différemment d'une image sur l'autre
et franchit le seuil différemment. La fumée et les rayons n'étaient pas touchés.

Ce plan (30, 40,60–41,86 s) et le plan 46 (52,34–54,22 s) ne faisaient pas partie des 5 extraits de
validation.

Correction, minimale et réversible : option `sources_doublons_25p`, désactivée par défaut, donc V5 et
V5.1 inchangées. Elle est activée dans `v5_1_final_config.json`. Sur une image source doublon, la
carte des sources est **conservée** au lieu d'être relissée. Critère de doublon : différence < 0,006
**et** < 35 % de celle de la dernière image nouvelle. Ce critère couvre les séries de 3 images
identiques ou plus (pauses caméra) ; sur un plan fixe sans cadence 25p, il ne s'applique pas.

| Vérification (fenêtres rendues avec la correction) | Résultat |
|---|---|
| Variation de l'effet sur doublon, pixels, p99,9 | 41–48 → **5–7** codes (résidu : fumée qui dérive lentement, bruit HEVC) |
| Halos sur doublons, plan 30 / plan 46 | **0,7 % / 0,0 %** du niveau du plan (seuil 12 %) |
| Même contrôle sur l'ancien master, plan 46 (témoin) | **34,9 % : signalé** |
| Plan 34, sans doublon (non-régression) | **identique**, 0 cellule différente |
| Artistes | écart **0** |

Contrôles ajoutés à `qc_extract.py` :

- `halos_sur_doublons` : contrôle direct, seuil 12 %. Le témoin montre que lui seul détecte ce défaut.
- `scintillement` : mesuré sur les **images nouvelles**. Un effet qui suit la cadence de l'image forme
  un escalier, ce qui n'est pas une pulsation. L'ancienne mesure image par image reste affichée.

Le master est **re-rendu entièrement** (4 segments) avec cette correction. Les deux masters
précédents ne sont pas livrés.

_Contrôles du master final : §11.6._

## 11.6 Master final : contrôles et livraison

Rendu : 4 segments (05:05 → 07:49 UTC), assemblés sans réencodage vidéo, piste audio de la source
copiée. Contrôles exécutés sur les fichiers livrés eux-mêmes.

### 11.6.1 Contrôles techniques

| Contrôle | Outil | Résultat |
|---|---|---|
| Format (COMPLET et ÉTALONNAGE SEUL) | `qc_extract.py` | 3840×2160, SAR 1:1, 50 i/s, 8760 images, HEVC Main 10 `hvc1`, BT.709 plage TV, 29,7 Mb/s — **OK** |
| Audio | `qc_master.py` | flux identique **bit à bit** à la source (SHA-256 des paquets `b567694f…bb1f4194`), y compris dans l'aperçu 1080p — **OK** |
| Synchronisation (horodatage, image, audio) | `qc_master.py`, `qc_extract.py` | décalage vidéo − audio 0,000 s (source : 0,000 s) ; corrélation audio 0,00 ms ; échantillon image : 1201 images testées (50 uniformes non décidables exclues), 0 décalée — **OK** |
| Durées | `qc_master.py` | vidéo et audio 175,200 s, 8760 images, comme la source — **OK** |
| Montage, 8760 images | `qc_master.py` | 0 image mieux corrélée à une autre image source (fenêtre ±3) ; 329 images uniformes non décidables — **OK** |
| Coupes | `qc_master.py` | 259 / 259 frontières validées, même saut source / master — **OK** |
| Luminance par plan | `qc_luma.py` | 8319 images ; 4 au-dessus du seuil, toutes expliquées (réponse de la LUT fixe à un saut de lumière de la source, effets constants) ; 0 inexpliquée — **OK** |
| Fondu de fin | `qc_luma.py` | 50 / 25 / 10 % atteints à 162,26 / 168,08 / 168,94 s, **identiques à la source** — **OK** |
| N&B | `qc_extract.py` | U/V sortie = témoin à 0,07 près au maximum ; chroma brute max 3,07 (source) — **OK** |

### 11.6.2 Contrôles des protections et des arbitrages

| Contrôle | Résultat |
|---|---|
| Artistes : pixels opaques = source + LUT globale (source seule sur le fondu) | écart max **0** sur 8760 images (≈ 686 000 px opaques par image en moyenne) |
| Contre-jour inventé | **0** sur 8760 images |
| Couloir vert (18 plans, 750 images) | effet **0** sur les 710 images hors transitions |
| Jour, N&B, effets de montage, fondu | effet **0** |
| Transitions | 4 (72,02 / 76,84 / 88,51 / 148,82 s), 10 images de pic ; 62 images de flash de montage (effets suspendus) |
| Halos sur images doublons (correctif §11.5.2) | 132 images doublons avec halos : variation max **0,7 %** (seuil 12 %) |
| Scintillement (images source nouvelles) | 2 images au-dessus de 12 % (2785 : 16,2 % ; 5804 : 13,1 %), toutes deux **expliquées par la variation de la source** (écart rapporté à la luminance source : max 11,5 %) ; 0 inexpliquée — **OK** (§11.6.3) |
| Comparaison avec le master précédent | tables artistes **identiques** ; tables d'effets différentes uniquement sur 13 plages (mouvements de caméra sur doublons), colonnes halos / halation / anamorphique / rayons ; fumée et particules : écarts au 5ᵉ chiffre décimal sur 10 images |

### 11.6.3 Deux signalements du premier passage, analysés

Le premier passage de `qc_extract.py` a rendu « À VÉRIFIER » sur deux points. Aucun ne révèle
un défaut introduit par le traitement ; deux faiblesses de la méthode de mesure ont été corrigées,
puis le contrôle a été relancé sur le master entier.

1. **`sync_image`, 1 image sur 1251 (image 8543, 170,86 s).** C'est le noir de la fin du fondu.
   L'image source est parfaitement uniforme (écart-type 0,0), donc sa corrélation est indéfinie.
   `qc_master.py` exclut déjà ces images comme non décidables, mais `qc_extract.py` ne le faisait pas.
   Même règle appliquée (écart-type < 2, images exclues comptées).
2. **`scintillement`, image 2785 (plan 48, 55,64–55,84 s, 10 images).**
   - **Biais de mesure trouvé.** Le niveau de référence « du plan » était moyenné sur une fenêtre
     (début du plan → image + 50) qui débordait sur les plans suivants, sans effet. Sur ce plan court,
     cela gonflait le pourcentage : 33,4 % au lieu de 16,2 %. Fenêtre désormais bornée au plan.
   - **Cause réelle.** La source clignote image par image sur ce plan : alternance nette / flou,
     flash cyan à 2785, luminance 68,7 → 81,3 → 74,7. La fumée éclairée suit cette lumière.
     Rapportée à la luminance de la source, la variation de l'effet est de **2,5 %**.
     À l'image, la couche d'effets reste stable ; sa contribution moyenne passe de 2,0 à 2,25 codes
     sur 255.
   - **Critère ajouté, sur le principe de `qc_luma.py`.** Une image au-dessus du seuil est
     « expliquée » si l'écart, rapporté à la luminance source, reste sous le seuil.
     Témoin : des pulsations de +30 à +40 % injectées sans variation de la source restent
     **inexpliquées** (4 sur 4 détectées). Le critère ne masque donc pas une vraie pulsation.
   - **Seconde image : 5804** (conteneur rouge, 116,08 s ; brut 13,1 % du niveau du plan, rapporté à la source 11,5 %).
     Pendant un panoramique rapide, la porte du conteneur entre dans le cadre au premier plan et la
     brume du décor s'y pose : jusqu'à 12 codes sur 1023 (≈ 3,6 % de la luminosité locale), puis un
     palier. Ce n'est pas une pulsation répétée : l'effet suit le contenu qui entre dans l'image.
     Ce plan appartient à l'extrait conteneur (114,1–120,7 s) validé en V5.1, avec ses réglages
     conservés (arbitrage 1). Il n'a pas été modifié : pas de nouvelle exploration.

### 11.6.4 Inspection visuelle

`visuel_master.py` (planches dans le dossier de livraison, non versionnées) :

- **84 plans réels** (≥ 0,3 s, hors effets de montage), source | master : cadrage et montage identiques, ambiances conformes aux
  familles, passage N&B (75,2–76,8 s) resté N&B, fondu de fin fidèle.
- **12 zones protégées** recadrées à 100 % en 4K (toutes les familles, dont le fondu) : écart
  faible et uniforme, dû à la LUT globale et à la compression. Ni halo, ni démarcation, ni bord
  de masque.
- **4 transitions** (t − 0,10 à t + 0,20 s) : sobres, déclenchées sur la vraie coupe, sans speed ramp.

### 11.6.5 Verdict et livrables

**Tous les contrôles passent** : `qc_master.py` CONFORME, `qc_luma.py` OK, `qc_extract.py` CONFORME
(second passage, méthode corrigée, §11.6.3), inspection visuelle conforme. **Le master V5.1 est prêt.**

| Fichier | Contenu | SHA-256 |
|---|---|---|
| `BADLIFE_V5_1_MASTER_4K_COMPLET.mp4` | **master** : étalonnage + effets V5.1 finale, 4K 50 i/s HEVC Main 10, audio original (652,7 Mo) | `dba214d73bf69d3ce0fed28388544fdf004a7d1258a583fa5f801d5e31b60009` |
| `BADLIFE_V5_1_MASTER_4K_ETALONNAGE_SEUL.mp4` | même master sans effets (étalonnage seul), référence et secours (653,3 Mo) | `df894828b26844dfd751261b67c858f7fa09021ab8b7f98297a08421113f86e2` |
| `BADLIFE_V5_1_APERCU_1080p.mp4` | aperçu de visionnage, H.264 High 1080p 50 i/s CRF 20, issu du master COMPLET, audio original (138,7 Mo) | `c8c52959b1752a544ab057ebd30c64053464eeb6ce6de9691f69d04b2d9ab5cc` |

Transmission : les deux masters 4K dépassant la limite de transfert de 500 Mio, ils sont envoyés en deux
morceaux (découpe binaire exacte, `.part1` / `.part2`) avec `LISEZMOI_REASSEMBLAGE.txt`. Le
réassemblage a été vérifié : il redonne exactement les SHA-256 ci-dessus.

Rapports versionnés : `data/master/` (`qc_master.json`, `qc_luma.json`, `qc_rapport.json` = second passage,
`qc_effets.csv`, `qc_artistes.csv`, `SHA256SUMS.txt`). Les médias ne sont pas versionnés.

**Point ouvert, à confirmer par vous.** L'arbitrage 1-bis (§11.1) étend le traitement « couloir
vert » aux autres apparitions du même décor : 38,46 / 44,48 / 69,58 / 76,84 / 97,10 / 105,76 /
122,76 / 128,32 s, plus les micro-plans des salves. C'est une interprétation de cohérence, pas une
instruction explicite. Si vous préférez y garder la V5.1, il suffit de retirer ces plans de la
section `plans` de la configuration et de re-rendre les segments concernés.
