# 10 — V5.1 : passe de finition artistique

> Demande du 2026-11-09 : la V5 est jugée prometteuse mais trop chargée en effets. Objectif :
> améliorer la qualité cinématographique, **pas** augmenter la quantité de VFX. Aucun master avant
> validation explicite.

## 10.1 Méthode : corrections localisées et réversibles

| Exigence | Mise en œuvre |
|---|---|
| Ne pas reconstruire le pipeline | même compositeur (`tools/v5/composite_v5.py`) ; **seules des options** ont été ajoutées |
| Sauvegarder les paramètres V5 | `tools/v5/v5_config_V5_fige.json` (SHA-256 identique à la config V5) ; code V5 au commit `c8f9630` ; rendus V5 conservés |
| Réversibilité prouvée | la config V5 figée, passée dans le compositeur modifié, **reproduit la V5 à l'identique** (extrait 5 : 270 images × 10 mesures, 0 différence) |
| Réglages dépendants des plans | `tools/v5/v5_1_config.json` : surcharges par famille + section `plans` (clé = image de début du plan) |
| Fiabilité des masques, coupes, synchro | inchangées (mêmes masques, même table des plans, mêmes contrôles) |

### Options ajoutées (absentes = comportement V5)

| Option | Effet |
|---|---|
| `particules_n`, `particules_justifiees`, `particules_seuil_source` | nombre de particules ; **suppression** (pas atténuation) des particules hors de l'influence d'une vraie source lumineuse du décor (halo ou faisceau) |
| `particules_scintillement` | désactive le scintillement décoratif des particules |
| `fumee_profondeur: "loin"` | brume **réservée au lointain** (décor proche net) ; elle ne peut plus traverser le décor proche |
| `rayons_source: "lampe"` | rayons uniquement depuis une **vraie lampe** du décor, plus jamais depuis un contre-jour inventé |
| `sources_persistantes` | halos, halation et flares uniquement sur les sources **stables** |
| `sources_marge_bord` | une source en lisière du cadre ne déclenche ni halo ni flare (sinon l'effet « pulse » quand elle entre ou sort) |
| `effets_duree_min_images` | plans de 1 ou 2 images : **aucun effet procédural** |
| `transitions.jour_exclu`, `descente_s`, `force` | pas de voile lumineux sur un plan de jour ; transition plus courte et plus douce |
| `artistes.mode: "harmonise"` | LUT globale très légère appliquée **identiquement à chaque pixel** des artistes (option comparée au mode strict) |

## 10.2 Réglages V5 → V5.1

| Paramètre | Nuit rouge (B) | Rideau (C) | Nuit ext. (D) | Conteneur 114,1–120,7 s (plans) |
|---|---|---|---|---|
| Particules | 300 → **40, justifiées seulement, sans scintillement** (−87 %, puis suppression de celles sans source) | 135 → **0** | 180 → **18, justifiées** | → **0** |
| Brume ajoutée | 0,80 → **0,35, lointain seulement** | 0,35 → 0,15, lointain | 0,60 → 0,30, lointain | 0,80 → **0,25, lointain** (−69 %) |
| Halos | 1,0 → 0,45, sources stables, hors bords | 0,6 → 0,35 | 1,0 → 0,5 | → 0,2 (LED vertes non amplifiées) |
| Halation | 1,0 → 0,35 | 0,5 → 0,25 | 0,7 → 0,3 | → 0,15 |
| Flares anamorphiques | 0,8 → 0,35, sources stables, hors bords | 0,4 → 0,15 | 1,0 → 0,4 | → **0** |
| Rayons | 1,0 → 0,35, **vraie lampe seulement** | 0,3 → **0** | 0,8 → 0,3, lampe | → **0** |
| Contre-jour inventé | 0,18 → 0,07 | 0,09 → 0,04 | — | → **0** |
| Jour (A), N&B, effets de montage | aucun effet (inchangé) | | | |

Transitions : les 4 sont conservées (72,0 / 76,84 / 88,5 / 148,8 s), force 0,6 → **0,3**, descente
140 → **90 ms**, **aucun voile sur le plan de jour sortant**. Constat V5 : à 76,84 s, le voile orange
délavait le plan rouge qu'il introduisait et commençait déjà sur le plan de jour.

## 10.3 Artistes : strict ou harmonisé

LUT `badlife_look_v5_1_sujets.cube` : noirs 0,04 → 0,020 et 0,06 → 0,044, tons moyens et hauts
inchangés (±0,006), saturation +4 % (carnations plafonnées à +1 %), **aucune rotation de teinte,
aucun cyan, ambre ni rouge ajouté**. Peau type (0,26 ; 0,17 ; 0,13) → (0,261 ; 0,170 ; 0,129).

| Mesure (conteneur, 3 images) | Strict | Harmonisé |
|---|---|---|
| Écart entre noirs des artistes et noirs du décor voisin (p5 de luminance) | +0,046 | **+0,036** (−23 %) |

**Choix : harmonisé.** Les artistes s'intègrent mieux (barbe, casquette et cheveux rejoignent la
densité du décor) ; carnations, expressions et vêtements visuellement inchangés. Le contrôle reste
strict : les pixels opaques des artistes sont comparés à « source + LUT globale » ; un écart de 0
prouve qu'aucune retouche locale ni aucun effet n'a touché les artistes.

## 10.4 Ce qui a été corrigé pendant la passe

| # | Constat | Correction |
|---|---|---|
| 1 | Transition à 76,84 s plus forte que le plan qu'elle introduit (voile orange), et commencée sur le plan de jour | force 0,3, descente 90 ms, jour exclu |
| 2 | Brume rouge résiduelle dans l'ouverture sombre au fond (86,38 s) | brume nuit 0,45 → 0,35 |
| 3 | Vidéo de masque rendue facultative mais toujours écrite (plantage du premier lancement) | écriture conditionnelle |
| 4 | Halo et flare qui « pulsent » en 7 images quand un tube LED traverse le bord du cadre (extrait 1, 84,34–84,42 s) | estompage des effets de source près des bords (marge 8 %) |

## 10.5 Les effets améliorent-ils les plans ? (mesures)

Outil : `tools/v5/metrics_v51.py`, mesures sur le **décor** (hors artistes), aux images clés de
profondeur, rapportées à l'étalonnage seul. Données : [`../data/v5_1/`](../data/v5_1/).

| Extrait | Quantité d'effets V5 → V5.1 | Détail 1er plan V5 → V5.1 | Noirs : étal. / V5 / V5.1 | Séparation proche/lointain : étal. / V5 / V5.1 |
|---|---|---|---|---|
| 1 Nuit rouge | 0,0242 → **0,0068 (−72 %)** | 0,977 → **0,996** | 0,0751 / 0,0859 / **0,0797** | 1,64 / 1,64 / **1,66** |
| 2 Urbain jour | 0,0010 → **0** | 1,000 → 1,000 | identiques | 1,49 / 1,49 / 1,49 |
| 3 Conteneur | 0,0227 → **0,0054 (−76 %)** | 0,996 → **0,998** | 0,0744 / 0,0838 / **0,0772** | 1,17 / 1,14 / **1,16** |
| 4 Noir et blanc | 0,0196 → **0,0075 (−62 %)** | 1,006 → 0,995 | 0,0826 / 0,0981 / **0,0896** | 1,01 / 1,02 / 1,02 |
| 5 Mouvement rapide | 0,0229 → **0,0052 (−77 %)** | 0,984 → **0,997** | 0,0410 / 0,0485 / **0,0434** | 1,86 / 1,79 / **1,87** |

Lecture :
- **Moins d'effets** : de −62 à −77 % d'énergie ajoutée sur les extraits de nuit ; zéro sur le jour.
- **Particules** (contribution mesurée) : −99,6 % en nuit rouge, **−100 %** sur le conteneur, le N&B et
  le mouvement rapide. C'est **au-delà de la fourchette de départ demandée pour la nuit rouge**
  (−75 à −90 %) : le filtre « source physique » supprime presque tout. Réglable (seuil de source).
- **Détail** : la V5 retirait jusqu'à 2,3 % du micro-contraste du premier plan (brume devant le
  décor proche) ; la V5.1 le conserve (≥ 0,995). La valeur > 1 du lointain en V5 (1,007 à 1,017)
  était un **faux détail** : les particules ajoutaient des points, pas du détail réel.
- **Noirs** : la V5 relevait les noirs du décor de 13 à 19 % (voile) ; la V5.1 les limite à 4–8 %.
- **Profondeur** : la V5 réduisait la séparation proche/lointain sur 2 extraits (1,17 → 1,14 ;
  1,86 → 1,79) ; la V5.1 la rétablit et la dépasse légèrement sur 3 extraits (1,66 ; 1,16 ; 1,87).

## 10.6 Par extrait : conservé, réduit, supprimé

| Extrait | Conservé | Réduit | Supprimé | Pourquoi |
|---|---|---|---|---|
| **1 Nuit rouge** (81,6–88,5 s) | éclairage rouge / bleu, vraie vapeur exhalée, contraste du décor, cyan pétrole dans les ombres, un reflet anamorphique bref sur un tube stable | brume (lointain seulement, −56 %), halos, halation, contre-jour | particules décoratives (**−99,6 % mesurés** : quelques-unes sur 44 images / 346, dans un faisceau), scintillement, rayons depuis un contre-jour inventé, halos sur les sources en lisière de cadre | le voile rose écrasait le panneau et les noirs ; les points n'avaient pas de source |
| **2 Urbain jour** (9,8–15,8 s) | tout l'étalonnage jour | — | — (aucun effet en V5 non plus) | un plan de jour bien étalonné n'a pas besoin de VFX ; seule l'harmonisation légère des artistes change |
| **3 Conteneur** (114,1–120,7 s) | LED vertes, parois métalliques, couloir sombre, ombres naturelles | brume −69 %, au lointain seulement ; halos des LED (non amplifiés) | particules (100 %), rayons, flares, contre-jour inventé | les effets aplatissaient le relief ; la V5.1 est **très proche de l'étalonnage seul**, qui prime ici |
| **4 Noir et blanc** (72,0–78,7 s) | passage N&B exact (écart 0,01 au témoin), flashs du montage, transition à 76,84 s | transition (force ÷ 2, descente 90 ms), effets du plan rouge | voile de transition sur le plan de jour sortant | la transition délavait le plan rouge qu'elle introduisait |
| **5 Mouvement rapide** (44,5–49,9 s) | montage alterné, raccords de lumière, rythme | effets des plans rouges | effets sur les plans de 1–2 images, particules | sur un insert ultra-court, un effet procédural ne peut être perçu que comme un flash |

## 10.7 Contrôle qualité

| Critère | 1 Nuit | 2 Jour | 3 Conteneur | 4 N&B | 5 Rapide |
|---|---|---|---|---|---|
| Format 4K, 50 i/s, HEVC Main10, BT.709 TV, nombre d'images | ✅ | ✅ | ✅ | ✅ | ✅ |
| Artistes : pixels opaques = source + LUT globale (aucune retouche locale) | ✅ 0 | ✅ 0 | ✅ 0 | ✅ 0 | ✅ 0 |
| Synchronisation image / audio | ✅ / 0,00 ms | ✅ / 0,00 ms | ✅ / 0,00 ms | ✅ / 0,00 ms | ✅ / 0,00 ms |
| Scintillement (écart à la tendance, seuil 12 %) | ✅ 5,7 % | ✅ 0 % | ✅ 8,1 % | ✅ 3,7 % | ⚠️ 12,4 % (**vérifié : occultation réelle**) |
| N&B sans dominante (témoin) | — | — | — | ✅ 0,01 | — |

**Extrait 5, image 2391** : le halo du tube LED bleu baisse sur 2 images parce que le **bras et le
torse de l'artiste passent devant le tube** (vérifié image par image). L'effet suit la lumière réelle
qui disparaît : c'est physiquement correct, pas un scintillement ajouté. Le seuil n'a pas été relevé
pour obtenir un verdict favorable ; l'écart est documenté tel quel.

Contrôle visuel : zooms 4K à 100 % (visage, barbe, chaîne, panneau « BIENVENUE ») ; plus aucune
particule près des visages ; plus de voile sur le décor proche.

## 10.8 Autocritique

1. **La V5 en faisait trop, et c'est d'abord ma responsabilité** : je l'avais calibrée pour
   montrer les effets (« plus poussés »), pas pour servir l'image. Les mesures le confirment : la V5
   relevait les noirs, retirait du détail au premier plan et réduisait la profondeur sur 2 extraits.
2. **Dans le conteneur, la V5.1 n'apporte presque rien par rapport à l'étalonnage seul.** Sa
   profondeur mesurée (1,16) est même très légèrement inférieure à celle de l'étalonnage seul (1,17).
   Si le rendu te paraît équivalent, je recommande l'**étalonnage seul** sur ces plans : c'est le
   principe que tu as posé.
3. **Les particules restantes sont rares** (nuit rouge, nuit extérieure) et uniquement dans
   l'influence d'une vraie source. On peut les supprimer totalement sans perte ; je n'ai pas observé
   de plan où elles apportent une profondeur réellement identifiable.
4. **Le contre-jour rouge (0,07)** reste une lumière inventée. Il aide un peu la séparation de
   l'artiste sur le fond rouge, mais il est discutable au regard de « pas de source physique crédible ».
5. **L'harmonisation des artistes** a été choisie sur 3 images de conteneur et une revue visuelle.
   C'est un choix d'œil, que tu dois valider ; le mode strict reste disponible (une ligne de configuration).
6. **Limites persistantes** : personnes d'arrière-plan non détourées (aucun effet ne les traverse
   désormais dans le conteneur, mais la brume au lointain peut les voiler légèrement ailleurs) ;
   image de transition floue à 120,40 s un peu saturée par la LUT nuit.
7. **Les mesures ne remplacent pas le regard** : elles montrent que la V5.1 dégrade moins l'image
   que la V5, pas qu'elle est plus belle. Le jugement final t'appartient, sur les extraits seuls.

## 10.9 Décisions attendues avant le master

| ID | Question |
|---|---|
| V5.1-1 | Valider l'esthétique V5.1 sur les 5 extraits seuls (sans grille). |
| V5.1-2 | Conteneur : V5.1 allégée ou **étalonnage seul** ? |
| V5.1-3 | Particules : la réduction réelle (−99,6 % en nuit rouge) dépasse la fourchette demandée (−75 à −90 %) ; garder, supprimer totalement, ou en réintroduire quelques-unes dans les faisceaux ? Contre-jour rouge : garder ou supprimer ? |
| V5.1-4 | Artistes : harmonisé (retenu) ou strict ? |
| V5.1-5 | Transitions : les 4 à la force réduite, ou moins ? |
