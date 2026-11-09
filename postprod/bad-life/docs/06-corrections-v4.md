# 06 — Corrections V4 : tests comparatifs A / B / C

> Demande reçue le 2026-11-09 : « BAD LIFE — CORRECTIONS V4 ». Le master complet n'est **pas**
> lancé. Trois tests comparatifs sont présentés pour validation.

## 6.1 Ce qui change par rapport à la V3

La V3 appliquait une seule LUT à toute l'image. La V4 introduit un **masque des artistes**
(détourage vidéo par IA), utilisé exclusivement comme **masque de protection et de compositing** :

| Usage du masque | Effet |
|---|---|
| Étalonnage différencié | LUT « sujets » sur les personnes, LUT « décor » ailleurs |
| Effets placés derrière | fumée, particules et lumières ajoutées à la seule plaque décor |
| Contrôle | mesure que les pixels des artistes sont identiques entre A, B et C |

**Aucun pixel d'artiste n'est généré, retouché ou déformé.** Les opérations sont : étalonnage
couleur pixel à pixel (LUT) et compositing *derrière* le sujet :
`sortie = masque × sujet + (1 − masque) × (décor + effets)`.

### Outil de détourage

| Élément | Valeur |
|---|---|
| Modèle | Robust Video Matting, MobileNetV3, ONNX FP32 — release v1.0.0 de `PeterL1n/RobustVideoMatting` |
| Licence | GPL-3.0 (outil de travail ; aucun code du modèle n'est intégré au livrable vidéo) |
| SHA-256 | `88d4531297118f595bf2fd60f6f566aec2e559393802d1f436c380f0cbbd2828` |
| Réglages | entrée 1080p originale (non étalonnée), `downsample_ratio` 0,25, état récurrent remis à zéro à chaque coupe |
| Vitesse | 8,3 i/s sur CPU 4 cœurs (clip complet estimé à environ 18 min) |
| Lissage | temporel léger (75/25) ; alpha ≥ 0,97 normalisé à 1 (cœur strictement opaque) |

**Qualité constatée (planche de contrôle, 8 images, 5 plans)** : très bonne sur les artistes
principaux (bords, dreadlocks, casquettes, mains). Limites :
- personnes floues en arrière-plan **non détectées** (plan 32, images 590–649) ; quelques
  personnes à droite au plan 31 ;
- second personnage très sombre du plan 30a (tunnel, lumière verte) **détecté partiellement**
  (seulement le bras).

Sur ces zones, les effets peuvent passer devant des personnes secondaires. C'est la raison pour
laquelle les effets sont faibles sur les plans 28a et 32 (particules à 45 %, pas de fumée). Pour le
master, ces cas demandent une retouche manuelle du masque (rotoscopie) dans un logiciel de
compositing, ou l'acceptation de cette limite plan par plan.

## 6.2 Test A — étalonnage v4 seul

| Demande V4 | Réponse |
|---|---|
| Contraste sélectif | Courbe plus marquée sur le décor (`v4_decor`) que sur les personnes (`v4_sujets`) |
| Noirs plus profonds sans écraser | 0,035 → 0,003 (décor) / 0,004 (sujets) ; 0,10 → 0,090 / 0,095 : le détail des bas-médiums est conservé |
| Rouges plus riches | gain rouge 0,45 → 0,70 (décor) et 0,50 (sujets), plage de teinte élargie |
| Cyan / pétrole uniquement dans les décors et ombres | ombres pétrole 0,036 sur le décor, **0 sur les personnes** ; rotation des verts **désactivée** sur les personnes (un maillot vert reste vert) |
| Carnations naturelles | protection peau v3 conservée dans les deux LUT ; ambre réduit sur les sujets (0,008) |
| Plans trop sombres ou délavés | table de gains par plan (`tools/v4/test_segment.json`) ; sur l'extrait, plan 29 (cité, luma moyenne 87, le plus clair de sa famille) : gain 0,94 |
| N&B préservé | **automatique** : la saturation de la source est mesurée image par image et toute baisse voulue (rampe ou plan N&B) est reproduite à l'identique dans A, B et C. L'extrait en contient une (plan 28b, images 87–124). |

Hypothèse à confirmer : « corriger les plans trop sombres » et « ne jamais éclaircir
artificiellement la peau » peuvent se contredire. J'interprète ainsi : une correction
d'exposition de **tout le plan** reste une correction légitime, alors qu'**ajouter** de la lumière
sur la peau est interdit. Sur l'extrait, aucun plan n'a été éclairci.

## 6.3 Test B — A + effets atmosphériques

| Effet | Plans | Réalisation |
|---|---|---|
| Fumée rouge volumétrique | 28b, 28c, 30a, 30b, 30c (décor rouge de nuit) | 2 couches de bruit fractal à profondeurs différentes, dérive lente, évolution des volutes, densité plus forte près du sol ; couleur rouge éclairée par la lumière locale de la scène ; voile léger du fond |
| Particules et poussières lumineuses | plans rouges (100 %), 28a et 32 (rideau métallique, 45 %) | 240 particules par plan, positions 3D, 3 plans de netteté (proches floues en bokeh), luminosité selon l'éclairage local, scintillement lent (< 1 Hz, pas de clignotement) |
| Parallaxe | couches atmosphériques | parallaxe par profondeur (×0,6 au fond, ×1,15 devant) **et suivi du mouvement caméra** (corrélation de phase sur le décor, personnes exclues) |

## 6.4 Test C — B + effets lumineux

| Effet | Plans | Réalisation |
|---|---|---|
| Halos autour des lumières existantes | plans rouges (100 %), 28a et 32 (60 %) | clé sur les sources ponctuelles très lumineuses **du décor** (luminance > 0,8 et fort contraste local, ce qui exclut les grands murs clairs), lueur à 3 échelles |
| Lumière derrière les artistes | rouge sur les plans rouges, ambre sur 28a et 32 | source douce placée derrière la tête et les épaules du sujet principal, qui suit le sujet (lissé) ; ajoutée au décor uniquement |
| Rayons / source directionnelle | plans rouges (rayons dans la fumée) | flou radial de la fumée depuis la source arrière : rayons volumétriques |
| Transitions lumineuses calées sur la musique | coupes à 3,76 s (rouge → cité) et 11,58 s (cité → rideau) | voile lumineux ambre-rouge depuis le bord du cadre, culminant sur le temps fort (tempo 100,4 BPM). Règle de sobriété : **seulement aux coupes qui changent d'ambiance** et qui tombent à ≤ 100 ms d'un temps fort (2 sur 9 dans l'extrait). Montée 50 ms, descente 120 ms ; **coupes inchangées** ; décor uniquement. |

### Non réalisé dans ce test (et pourquoi)

| Demande | Raison |
|---|---|
| Reflets lumineux sur les surfaces | Un reflet crédible demande un suivi planaire de la surface (Mocha) et sa géométrie. Un reflet « flottant » ne suivrait pas la surface et serait un artefact. |
| Parallaxe sur le décor filmé lui-même | Il faudrait une carte de profondeur et la reconstruction des zones cachées derrière les objets (inpainting), avec un fort risque de déformation. La parallaxe est appliquée aux couches atmosphériques ajoutées, pas à l'image filmée. |
| Relief lumineux sur les plans de jour (cité) | Une source directionnelle ajoutée en plein jour couvert contredit la lumière réelle du plan ; pas d'effet sur les plans 29, 30d et 31 par cohérence. |

## 6.5 Erreurs corrigées pendant la mise au point

| Version interne | Défaut constaté | Correction |
|---|---|---|
| Aperçu 1 | Fumée et particules quasi invisibles | Densité, éclairage et luminosité des particules relevés |
| Aperçu 1 | **Liseré sombre autour des silhouettes** (marge de protection dilatée qui empêchait la lueur d'atteindre le bord) | Compositing « derrière » avec le masque exact, sans marge |
| Aperçu 1 | Contre-jour rouge trop large (ciel de nuit entièrement rouge) | Intensité 0,20 → 0,14, source resserrée |
| Aperçu 2 | Jusqu'à 1,3 % d'effet sur le cœur des artistes (alpha 0,98–0,999) | Normalisation alpha ≥ 0,97 → 1 |
| Rendu 1 (**non livré**) | Saut d'intensité d'effet isolé à l'image 62, détecté par la mesure de stabilité. Cause : **coupe non détectée**. L'extrait compte 10 plans et non 5 : fumée et contre-jour rouges appliqués à tort sur le plan rideau métallique (images 0–61) et sur un plan de cité de jour (images 439–525). | Coupes vérifiées visuellement (doc 02, erratum) ; configuration à 10 plans ; détourage refait avec réinitialisation à chaque coupe ; transitions limitées aux changements d'ambiance ; rendu refait. |
| Rendu 1 | Rapport de pixel absent des métadonnées (SAR « N/A ») | `setsar=1` ajouté à l'encodage |
| Rendu 2 (**interrompu, non livré**) | Plan 28b : le montage original contient une **rampe couleur → N&B → couleur** (saturation source 12,7 → 0,8 entre les images 87 et 98, N&B jusqu'à 114, retour à la couleur à 124). La LUT décor recolorait ce passage en gris-cyan. | Mesure de la saturation de la source image par image : sous 80 % de la référence du plan (90e percentile), la chroma de la sortie (effets compris) est réduite dans la même proportion. Les intentions N&B du montage sont reproduites automatiquement, y compris le plan #60 du clip. |

## 6.6 Contrôle qualité des rendus livrés (rendu 3)

| Contrôle | Attendu | Mesuré (A / B / C) | Verdict |
|---|---|---|---|
| Format | 3840×2160, SAR 1:1 | 3840×2160, 1:1 | ✅ |
| Cadence, durée | 50 i/s, 649 images (12,98 s) | 50/1, 649 images | ✅ |
| Couleur | HEVC Main10, BT.709, plage TV | conforme | ✅ |
| Débit | adapté YouTube 4K | 37,3–37,6 Mb/s | ✅ |
| Montage | 9 coupes à 1,24 / 2,50 / 3,76 / 5,12 / 6,24 / 7,48 / 8,78 / 10,52 / 11,58 s | identiques sur les 3 versions | ✅ |
| **Artistes intacts** | pixels opaques des personnes identiques entre A, B et C | **écart max = 0,0** sur 649 images (≈ 609 000 px par image) | ✅ |
| Bords des silhouettes | aucun liseré, aucun trou | contrôle visuel à 100 % (cheveux bouclés, casquette, mains en mouvement) | ✅ |
| Effets hors plans de nuit | plans 29, 30d, 31 sans effet | écart A/C = 0,0 sur le plan 30d | ✅ |
| Intention N&B du montage | plan 28b, images 87–124 | 108 images à chroma réduite ; image 100 en N&B comme la source | ✅ |
| Scintillement des effets | pas de saut d'intensité hors coupes et transitions | variation image à image : B moy. 0,00008, max 0,00057 ; C moy. 0,00011, max 0,00184 (images 376–384 : mouvement rapide de caméra) | ✅ |
| Temps de rendu | — | 20 min pour A + B + C (CPU 4 cœurs) | info |

Remarque sur les images 374–389 : la source présente un score de scène élevé une image sur deux
(mouvement rapide en 25 i/s dans un fichier à 50 i/s). Ce motif est identique dans la source, A et C :
il ne s'agit pas d'un artefact ajouté.

## 6.7 Livrables de validation

| Fichier | Contenu |
|---|---|
| `BADLIFE_V4_COMPARATIF_source-A-B-C.mp4` | 1080p, 4 vues synchronisées avec le son : SOURCE / A / B / C |
| `BADLIFE_V4_TEST_A.mp4`, `_B.mp4`, `_C.mp4` | les trois tests en 4K HEVC 10 bits |
| `BADLIFE_V4_planche_source-A-B-C.jpg` | 6 plans × 4 versions |
| `BADLIFE_V4_zoom100_bords.jpg` | zoom à 100 %, bord de silhouette A contre C |

## 6.8 Décisions attendues

| ID | Question |
|---|---|
| V4-1 | Quel niveau retenir pour le master : **A**, **B** ou **C** ? Ou un mélange par famille de plans (ex. C sur les scènes rouges, A sur la cité) ? |
| V4-2 | Intensités : fumée, particules, contre-jour, transitions — plus, moins, ou en l'état ? |
| V4-3 | Personnes secondaires non détourées (plans au rideau métallique) : accepter la limite, ou prévoir une rotoscopie manuelle de ces plans ? |
| V4-4 | Interprétation « plans trop sombres » contre « ne jamais éclaircir la peau » (§6.2) : confirmer ? |

Avant le master, il faut aussi refaire la liste des coupes du clip entier (erratum doc 02), puis
étendre la configuration plan par plan à tout le clip.

## 6.9 Erratum (2026-11-09, découvert pendant la V5)

En diagnostiquant un scintillement en V5, une **erreur de signe** a été trouvée dans le suivi de
caméra appliqué à la fumée : dans les tests V4 (B et C), le motif de fumée se déplaçait **à l'opposé**
du décor lors des mouvements de caméra, au lieu de le suivre. Convention vérifiée sur un cas
synthétique : `cv2.phaseCorrelate` renvoie le déplacement du contenu. Les particules n'étaient pas
concernées. Le défaut est corrigé dans `tools/v5/composite_v5.py` ; les fichiers V4 ne sont pas
re-rendus, car ils sont remplacés par les tests V5.
