# 02 — Analyse de la source (étape 1) et sauvegarde (étape 3)

## 2.1 Provenance et intégrité

| Élément | Valeur |
|---|---|
| Lien de transfert | SwissTransfer, transfert `01a1be37-691d-7226-9c0f-4acef14d0379` (expire 15 jours après le 2026-11-09) |
| Fichier | `lyphik jahsIK CLIP 2.mov` |
| Taille | 543 621 990 octets (518,4 Mio) |
| SHA-256 | `2a6a60eb3c7b5f1aabf56b3430fdf13ed0e8b9719e551f19106f96fabd4e7263` |
| Sauvegarde (étape 3) | copie en lecture seule `lyphik jahsIK CLIP 2 - ORIGINAL.mov`, SHA-256 identique vérifié |

> ⚠️ La sauvegarde se trouve dans l'espace de travail **temporaire** de la session de traitement.
> Elle ne remplace pas une sauvegarde chez le propriétaire du projet (le fichier d'origine et le
> projet de montage doivent être conservés de votre côté).

## 2.2 Caractéristiques techniques (ffprobe)

| Flux | Caractéristiques |
|---|---|
| Conteneur | QuickTime `.mov`, durée **175,200 s**, débit global 24,8 Mb/s |
| Vidéo | H.264 High, **1920 × 1080**, SAR 1:1, **16:9**, **50 i/s** progressif (8760 images), 4:2:0 8 bits, ~24,6 Mb/s |
| Colorimétrie | BT.709 (primaires, transfert, matrice), plage **TV (limitée)** |
| Audio | AAC-LC, 48 kHz, stéréo, ~126 kb/s, 175,200 s |
| Autres | piste timecode `tmcd` 00:00:00:00 ; métadonnées QuickTime (titre « lyphik jahsaik », auteur renseigné) |

**Conséquences pour le livrable (§8 du cahier des charges)** :
- Format horizontal 16:9 → master **3840 × 2160**, **50 i/s**, durée **175,200 s**.
- Source en 1080p → l'image 4K est un **upscale** (×2 par axe). Il n'existe pas de détail 4K
  authentique dans la source ; voir doc 05 pour le choix de la méthode.
- Audio : copié **bit à bit** dans le master (aucun réencodage, synchronisation inchangée).

## 2.3 Découpage en plans

Méthode : détection de changement de scène ffmpeg (seuil 0,25) puis statistiques `signalstats`
image par image, agrégées par segment (`tools/analyze.sh`, `tools/shots.py`).

- **130 segments** détectés, dont **54 plans ≥ 0,5 s** et **76 micro-segments < 0,5 s**
  (7,0 s au total) : salves de strobe/flash du montage (27,6–28,9 s ; 66,0–67,1 s ;
  104,4–105,8 s ; 142,8–143,9 s), une image blanche pleine à 95,50 s et des coupes rapides.
- Limite connue : un détecteur de scène peut produire de fausses coupes sur un mouvement rapide.
  Les micro-segments n'ont pas été vérifiés un par un ; ils ne sont pas traités différemment du
  plan qui les entoure, donc cette limite n'a pas d'impact sur l'étalonnage.

Table complète : [`../data/shots.csv`](../data/shots.csv) (début/fin, luma moyenne, percentiles
10/90, min/max, saturation moyenne, famille, notes).

## 2.4 Familles de lumière

Classification **visuelle** sur l'image médiane de chaque plan ≥ 0,5 s
([`../data/families.json`](../data/families.json)) — à confirmer par la réalisation.

Valeurs de luma en codes 8 bits (noir légal = 16, blanc légal = 235). Saturation = `SATAVG` de signalstats.

| Famille | Plans | Durée | Y moy. [min–max] | Y p10 moy. | Y min moy. | Y max | Sat. moy. |
|---|---:|---:|---|---:|---:|---:|---:|
| A — Cité, jour couvert | 25 | 82,7 s | 66,6 [49,1–87,1] | 35,8 | 23,0 | 253 | 4,9 |
| B — Décor rouge « BIENVENUE », nuit | 12 | 42,1 s | 46,7 [38,9–59,8] | 33,2 | 24,7 | 253 | 7,7 |
| C — Rideau métallique / grille | 12 | 20,4 s | 78,1 [65,5–92,7] | 32,0 | 23,8 | 240 | 7,6 |
| D — Extérieur nuit / crépuscule | 3 | 7,8 s | 48,3 [35,3–61,7] | 30,7 | 23,3 | 249 | 4,1 |
| N&B (plan #60) | 1 | 1,7 s | 73,3 | 38,5 | 23,0 | 230 | 2,9 |
| Outro (plan #130) | 1 | 13,5 s | 35,1 | 25,6 | 16,0 | 238 | 1,9 |
| Micro-segments / flashs | 76 | 7,0 s | 92,1 [39,5–235] | 48,8 | 33,9 | 252 | 7,5 |

## 2.5 Éléments graphiques incrustés

- Plans #1–#2 : titre « LYPHIK x JAHSIK — BAD LIFE » (lettrage or).
- Plan #3 : logo « LBC ».

L'image étant déjà aplatie (titres incrustés dans les pixels), **tout étalonnage modifie aussi ces
graphismes**. Voir doc 05, décision D4.
