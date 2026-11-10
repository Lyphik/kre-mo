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

_Contrôles du master final : §11.5._
