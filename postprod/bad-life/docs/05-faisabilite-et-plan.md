# 05 — Faisabilité, décisions attendues et plan des étapes 6 à 9

## 5.1 Ce qui est réalisé ici, et ce qui ne l'est pas

Environnement de traitement de cette session : ffmpeg 6.1 et Python (numpy, Pillow), CPU 4 cœurs,
**pas de GPU, pas de logiciel de compositing, pas de modèle d'IA de segmentation, de tracking ou
d'upscale**. Le tableau distingue ce qui peut être livré proprement de ce qui ne le peut pas
**sans enfreindre le §3 (préservation des artistes) ou le §10 (aucun artefact)**.

| Exigence | Ici ? | Outil professionnel adapté | Commentaire |
|---|---|---|---|
| Étalonnage global cohérent (§4) | ✅ | — | LUT v3, voir doc 04 |
| Harmonisation d'exposition plan par plan (§4, étape 6) | ✅ | — | Correction par plan avec activation temporelle, sans toucher aux coupes |
| Conservation N&B / outro (§3) | ✅ | — | `BW_RANGES` dans `render.sh` |
| Vignettage léger | ✅ | — | Vérifié sans artefact |
| Upscale 4K fidèle (§8) | ✅ | — | Lanczos : interpolation, aucun détail inventé |
| Export 4K 50 i/s, audio bit à bit, durée identique (§8) | ✅ | — | `render.sh` sans extrait = `-c:a copy` |
| Contrôle qualité outillé (étape 8) | ✅ (partiel) | — | Mesures de peau, comparaisons ; l'œil humain reste indispensable |
| Séparation sujets / fond par **masques + tracking** (§3, §4) | ❌ | DaVinci Resolve Studio (Magic Mask, tracker), After Effects (Roto Brush 3, Mocha) | Sans masque fiable, un effet de séparation déborde sur les artistes |
| Fumée volumétrique, particules, poussières (§5) | ❌ | Resolve Fusion (particules), After Effects + Trapcode Particular, éléments filmés (stock VFX) | Doit passer **derrière** les artistes : masques obligatoires |
| Halos, flares, lumière derrière les artistes (§5) | ❌ | Fusion / AE (Optical Flares, glow sur masque de luminance) | Le test ffmpeg a produit des artefacts (doc 04 §4.4) |
| Parallaxe de décor (§5) | ❌ | AE / Fusion (projection caméra, découpage en plans de profondeur) | Demande rotoscopie et reconstruction des zones masquées |
| Transitions sans modifier les coupes (§5) | ❌ | Fusion / AE (light leaks, flashs posés à cheval sur la coupe) | Faisable proprement uniquement en compositing |
| Enrichissement IA des décors, suppression d'éléments (§6) | ❌ | Outils d'inpainting vidéo (Resolve Object Removal, AE Content-Aware Fill, outils génératifs vidéo) | Risque de scintillement temporel ; plan par plan avec validation |
| Upscale IA (§6.6) | ⚠️ Déconseillé | Topaz Video AI, Resolve Super Scale | **Conflit avec le §3** : un upscale IA peut inventer de la texture de peau ou de cheveux. À n'utiliser qu'avec un modèle « fidélité » et une comparaison visage par visage. |

**Conclusion** : la partie étalonnage + harmonisation + 4K + export est entièrement réalisable et
déjà prototypée. La partie VFX (§5, §6) exige un poste de compositing et une étape de rotoscopie.
Elle n'a pas été simulée : un résultat approximatif violerait les §3 et §10.

## 5.2 Recommandation sur la source

Le fichier reçu est un **export H.264 8 bits à 24,6 Mb/s**. Il convient pour un étalonnage léger,
mais il limite l'amplitude des corrections (risque de cassures dans les dégradés, hautes lumières
écrêtées irrécupérables). Si elles existent, il est fortement recommandé de fournir :
1. un export de la timeline en **ProRes 422 HQ** (ou DNxHR HQX) **sans titres** ;
2. les **fichiers de titres** séparés (avec couche alpha), à réincruster après l'étalonnage ;
3. idéalement le **projet de montage avec les rushes caméra** (surtout s'ils sont en profil log).

## 5.3 Décisions attendues (bloquantes pour l'étape 6)

| ID | Décision | Options | Recommandation |
|---|---|---|---|
| **D1** | Validation du look v3 sur le test 12,98 s | Valider / ajuster (contraste, saturation, intensité du cyan ou de l'ambre, vignettage) | — (décision artistique) |
| **D2** | Plan #60 (N&B) et plan #125 (quasi N&B) | Garder N&B / étalonner en couleur | Garder N&B (intention présumée du montage) |
| **D3** | Plan final #130 (13,5 s sombre, désaturé) | Laisser tel quel / étalonner | Laisser l'intention ; appliquer seulement la cohérence des noirs |
| **D4** | Titres incrustés #1–#3 | (a) accepter qu'ils soient étalonnés avec l'image ; (b) fournir une version sans titres + titres séparés | (b) |
| **D5** | VFX (§5–§6) | (a) master « étalonnage seul » maintenant, VFX dans un second temps par un compositeur ; (b) attendre un poste de compositing | (a) : livrable utile rapidement, sans risque pour les artistes |
| **D6** | Méthode d'upscale | Lanczos (fidèle) / IA (plus « net », risque §3) | Lanczos |
| **D7** | Codec du master | HEVC Main10 (moins de cassures, accepté par YouTube) / H.264 8 bits (compatibilité maximale) | HEVC Main10 en master, H.264 en copie de diffusion si besoin |

## 5.4 Plan des étapes 6 à 9 (après validation)

0. **Préalable (ajouté en V4)** : refaire la liste des coupes du clip entier (détection à seuil
   bas, puis validation visuelle de chaque candidat) ; recalculer `data/shots.csv` et les familles.
1. **Étape 6 — Plan par plan** : table de corrections par plan (`data/grades.csv` : plan, correction
   d'exposition, réglage éventuel de la balance) à partir de `data/shots.csv`. Ces corrections
   s'appliquent avant la LUT, avec activation sur l'intervalle exact du plan, de sorte que les
   coupes restent intactes.
2. **Étape 7 — Harmonisation** : comparaison par famille (planches avant/après), cible de luma par
   famille, vérification des raccords plan à plan.
3. **Étape 8 — Contrôle qualité** : `skin_probe.py` étendu à un visage par plan principal ;
   inspection image par image des salves de flash, de l'image blanche (95,50 s), des plans de nuit
   et de l'outro ; vérification de l'absence de cassures dans les dégradés et de bruit amplifié.
4. **Étape 9 — Master** : `render.sh` sur le clip complet (environ 1 h 50 sur 4 cœurs CPU),
   puis vérification automatique : 3840×2160, 50 i/s, 8760 images, durée 175,200 s, flux audio
   identique à la source (hash du flux audio extrait), métadonnées BT.709.

## 5.5 Critères d'acceptation techniques du master

- `ffprobe` : 3840×2160, SAR 1:1, 50/1, 8760 images, durée 175,200 s.
- Audio : `ffmpeg -i X -map 0:a -c copy -f data -` → hash identique entre source et master.
- Couleur : `color_primaries=bt709`, `color_trc=bt709`, `colorspace=bt709`, `color_range=tv`.
- Aucun plan ajouté, retiré ou déplacé : coupes détectées sur le master identiques à `data/shots.csv`.
