# 04 — Look « BAD LIFE » et contrôle qualité

## 4.1 Principe

Le look est encodé dans une **LUT 3D** (`luts/badlife_look_vN.cube`, 33³, Rec.709 / BT.1886,
RGB pleine échelle) générée par script (`tools/make_lut.py`). Ce choix rend le look :
- **reproductible** : paramètres versionnés, régénération à l'octet près ;
- **portable** : la même LUT s'utilise dans ffmpeg, DaVinci Resolve, Premiere ou Final Cut ;
- **non destructif pour la géométrie** : une LUT ne transforme que les couleurs pixel par pixel.
  Elle ne peut pas modifier un visage, une silhouette, une coiffure ni un mouvement.

Le traitement se fait en Y'CbCr Rec.709, ce qui sépare luminance et chrominance :

| Étape | Rôle | Réponse au cahier des charges |
|---|---|---|
| Courbe de luma (pied de courbe) | 0,035 → 0,006 (noir), visages 0,10–0,20 conservés, épaule douce 1,0 → 0,985 | Noirs profonds avec détails, hautes lumières contrôlées |
| Saturation adaptative | ×1,30 + vibrance jusqu'à +0,55 sur les tons ternes ; **plafonnée à ×1,10 sur la peau** | Couleurs plus riches sans visages orangés |
| Rouges (teinte ≈ 103°, chroma > 0,06) | +0,45 de saturation | Rouge profond et lumineux |
| Verts jaunâtres (≈ 212°) | rotation de +16° vers le sarcelle, jamais sur la peau | Palette cyan / bleu pétrole |
| Ombres | teinte pétrole (300°), **uniquement sur les pixels déjà froids et chromatiques** | Touches nocturnes cyan / pétrole sans bleuir la peau |
| Hautes lumières | ambre (148°), léger, au-dessus de 0,55 | Lumières chaudes orange / ambre |
| Gamut | compression de chroma (teinte conservée) au lieu d'un écrêtage | Pas de couleurs artificielles ni de cassures |

## 4.2 Historique des versions

| Version | Statut | Raison |
|---|---|---|
| v1 | ❌ Rejetée (interne) | Étirement global du noir : luma des visages en baisse de 11 à 27 %. Split-toning cyan visible sur les peaux foncées dans l'ombre. |
| v2 | ❌ Rejetée (interne) | Bas-médiums relevés, mais peau quasi neutre (plan #32) basculée vers le cyan (dH ≈ +146°). Cause : la protection peau par teinte ne fonctionne pas sur une peau sans chroma. |
| **v3** | ⏳ Proposée à validation | Contraste par le pied de courbe, cyan réservé aux pixels déjà froids, ambre réduit. |

## 4.3 Mesures de fidélité des tons chair

Outil : `tools/skin_probe.py`. Patchs choisis à la main sur la peau, positions vérifiées sur image
annotée. Y = luma (0–1), C = chroma, H = teinte en degrés (vectorscope).

| Plan / patch | Source Y · C · H | v1 | v2 | **v3** |
|---|---|---|---|---|
| #32 joue (51,64 s) | 0,108 · 0,003 · 144° | Y 0,062 (−43 %), H +149° | Y 0,079 (−27 %), H +146° | **Y 0,100 (−7 %), C 0,003 (inchangée)** |
| #75 visage (87,12 s) | 0,195 · 0,024 · 145° | Y −22 %, dH +19° | Y −11 %, dH +14° | **Y −2 %, dH +3,6°** |
| #75 front (87,12 s) | 0,191 · 0,046 · 139° | Y −27 %, dH +8,6° | Y −14 %, dH +5,0° | **Y 0 %, dH +1,3°** |
| #105 visage nuit (117,94 s) | 0,138 · 0,034 · 131° | Y −36 %, dH +7,2° | Y −21 %, dH +4,0° | **Y −1 %, dH +0,8°** |
| #33 joue, lumière rouge (54,09 s) | 0,153 · 0,025 · 113° | — | Y −18 %, dH −2,9° | **Y −1 %, dH −1,8°** |

Lecture : en v3, la luminance des peaux reste à ±7 % et la teinte à ±4°. Sur le patch #32 (chroma
0,003, gris neutre), un écart de teinte n'a pas de sens perceptif : la chroma reste à 0,003.

> Limite : 5 patchs sur 4 plans. Le contrôle image par image des passages sensibles (étape 8)
> reste nécessaire sur le clip complet.

## 4.4 Effets testés et écartés pour le test

| Effet | Résultat | Décision |
|---|---|---|
| Halo / bloom des hautes lumières (ffmpeg `blend` en 16 bits) | Postérisation, aplats fluo, voile sur toute l'image | ❌ Écarté |
| Même effet en virgule flottante 32 bits | Image noire hors hautes lumières (filtres non fiables dans ffmpeg 6.1) | ❌ Écarté |
| Vignettage léger (angle 0,40 rad) | Propre, discret, sans artefact | ✅ Conservé |

Un halo propre reste possible, mais dans un outil de compositing (Resolve/Fusion, After Effects,
Nuke) avec masque de luminance et contrôle visuel. Voir doc 05.

## 4.5 Test représentatif (étape 4)

- Extrait : **39,36 → 52,34 s (12,98 s)**, plans #28 à #32. Il couvre les familles B (décor rouge),
  A (cité) et C (rideau métallique) et les transitions entre elles.
- Chaîne : RGB 16 bits → LUT v3 (tétraédrique) → vignettage 0,40 → upscale 3840×2160 Lanczos →
  YUV 4:2:0 10 bits BT.709 plage TV → HEVC Main10 (CRF 16, VBV 80 Mb/s) ; audio AAC 320k
  (extrait seulement : le master copiera l'audio original bit à bit).
- Livrables de validation : le test 4K et une comparaison avant/après en 1080p.

### Résultats du contrôle du test

| Contrôle | Attendu | Mesuré | Verdict |
|---|---|---|---|
| Résolution / ratio | 3840×2160, SAR 1:1 | 3840×2160, SAR 1:1 | ✅ |
| Fréquence / nombre d'images | 50 i/s, 12,98 s × 50 = 649 | 50/1, 649 images | ✅ |
| Codec / colorimétrie | HEVC Main10, BT.709 plage TV | HEVC Main 10, yuv420p10le, BT.709, tv | ✅ |
| Coupes (relatives au début) | 3,76 / 5,12 / 10,52 / 11,58 s (source) | 3,76 / 5,12 / 10,52 / 11,58 s | ✅ montage intact |
| Visage à 100 % en 4K (plan #32) | structure, texture, barbe identiques | identiques ; aucun halo, aucun artefact | ✅ |
| Débit | adapté YouTube 4K | 31,8 Mb/s (HEVC 10 bits, VBV max 80 Mb/s) | ✅ |
| Temps de rendu | — | 5 min 32 s (2,0 i/s, CPU 4 cœurs) → master estimé à ~75 min | info |

Remarque : le conteneur MP4 recopie la piste timecode de la source (00:00:00:00), ce qui est sans incidence.
