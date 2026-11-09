# 09 — V5 : étalonnage C hybride, effets, extraits de validation et rapport de contrôle qualité

> Étapes 4 à 7 du pipeline V5. **Aucun master n'est lancé** : les 5 extraits sont présentés pour
> validation (étape 7).

## 9.1 Principe de composition (règle absolue §2)

```
sortie = alpha × SOURCE + (1 − alpha) × (DÉCOR étalonné + effets)
```

| Élément | Traitement |
|---|---|
| Artistes (alpha = 1) | **image source décodée, sans aucune opération** : pas de LUT, pas d'effet, pas de netteté, pas de correction de chroma |
| Bords (0 < alpha < 1 : cheveux, contours) | mélange physique source / décor (comme un vrai compositing) |
| Décor (alpha = 0) | LUT de la famille du plan + effets |
| Redimensionnement 4K | Lanczos **uniforme** sur l'image entière (zscale), après la vérification |
| Vérification | image par image, **avant** redimensionnement : pixels opaques de la sortie contre source décodée (`qc_artistes.csv`) |

Masque : RVM (doc 08), lissé dans le temps (75/25), alpha ≥ 0,97 ramené à 1.

### Conséquence visuelle de la règle stricte — décision à prendre
Comme les artistes ne reçoivent plus aucun étalonnage, ils gardent le contraste et les noirs
légèrement relevés de la source, alors que le décor est approfondi. Sur les scènes de nuit, l'artiste
paraît un peu moins dense que le décor (maillot rouge plus terne que les rideaux étalonnés). Une
planche compare la **règle stricte** à une **option** où les artistes reçoivent un étalonnage
uniforme protégeant les carnations (LUT « sujets » V4 : pas de cyan, pas de rotation de teinte,
saturation modérée) : `BADLIFE_V5_artistes_strict_vs_option.jpg`. L'option améliore l'intégration
mais modifie les pixels des artistes (couleur uniquement, sans retouche locale). **Le choix
appartient à la production.**

## 9.2 Étalonnage par famille (décor uniquement)

| Famille (doc 08) | LUT | Intention |
|---|---|---|
| B — Nuit rouge | `badlife_look_v5_nuit.cube` | base C : rouges intenses (gain 0,78, gamut compressé pour éviter le fluo), noirs profonds détaillés (0,10 → 0,088), cyan / pétrole dans les ombres froides (0,040), ambre maîtrisé (0,020) |
| C — Rideau métallique, D — Nuit extérieure | `badlife_look_v5_nuit_ambre.cube` | même base, rouge modéré (0,50), ambre plus présent (0,026) |
| A — Cité de jour, fondu de fin | `badlife_look_v5_jour.cube` | base A : contraste naturel, épaule douce (blancs maîtrisés, 1,0 → 0,970), saturation 1,20, **pas de dominante rouge** (gain 0,25), cyan et ambre très légers |
| X — Effets de montage, N&B | LUT du plan voisin le plus ressemblant | aucun effet ajouté |

**Passages N&B et rampes** : la chrominance du décor (et des effets) est remplacée par **la
chrominance exacte de la source** dès que la source passe sous le seuil N&B, avec une transition
progressive. Aucune dominante cyan, rouge ou ambre ne peut apparaître pendant ces passages.

## 9.3 Effets par famille

| Effet | B nuit rouge | D nuit ext. | C rideau | A jour |
|---|---|---|---|---|
| Fumée volumétrique (2 couches de bruit, parallaxe, suivi caméra, **densité selon la profondeur**) | rouge 0,80 | ambre-neutre 0,60 | ambre 0,35 | — |
| Fumée ambre près des vraies sources | 0,6 | 0,8 | 0,6 | — |
| Particules (300 max, 3 plans de netteté, **cachées par le décor plus proche**, plus lumineuses dans les faisceaux) | 1,0 | 0,6 | 0,45 | — |
| Halos (glow sur les sources du décor) | 1,0 | 1,0 | 0,6 | — |
| Halation rouge-orangé | 1,0 | 0,7 | 0,5 | — |
| Flares anamorphiques (traînées horizontales rouge-ambre sur les sources ponctuelles) | 0,8 | 1,0 | 0,4 | — |
| Rayons volumétriques (depuis la vraie source du décor, ou contre-jour) | 1,0 | 0,8 | 0,3 | — |
| Contre-jour derrière l'artiste principal | rouge 0,18 | — | ambre 0,09 | — |

Garde-fous :
- **Sources lumineuses** : détectées dans le décor seulement (jamais sur les artistes ni les visages),
  carte lissée dans le temps et **compensée en mouvement**.
- **Source des rayons verrouillée par plan** : fondu si elle disparaît, jamais de bascule.
- **Couleur des rayons** : moyenne sur une zone de 61 px, lissée dans le temps.
- **Confiance du masque** : réduction automatique des effets si le détourage est incertain.
- **Flashs du montage** (image nettement plus claire que la médiane du plan) : effets suspendus.
- **Profondeur** : Depth Anything V2 Small (licence Apache-2.0 pour la variante Small ; ONNX de
  la release v2.0.0 de `fabio-sim/Depth-Anything-ONNX`, SHA-256 `d2b11a11c1d4a12b…f2562be`),
  1 image sur 4, normalisée par plan, interpolée dans le temps ; utilisée uniquement pour le décor.

### Transitions musicales
Une transition lumineuse (voile ambre-rouge depuis le bord du cadre, montée 50 ms, descente 140 ms,
décor uniquement, **coupes inchangées**) n'est posée qu'entre **deux plans réels** (≥ 0,3 s, jamais
sur un insert ni dans une salve) qui **changent d'ambiance**, et seulement si l'une de ces conditions
est remplie :
1. un impact musical à 80 ms au plus, en section forte ou à une frontière de section ;
2. un kick ou une snare à 40 ms au plus, dans une section forte.

Cela donne **4 transitions sur 175 s** : 72,02 / 76,84 / 88,50 / 148,84 s. L'extrait 4 en
contient une (76,84 s).

## 9.4 Non réalisé, et pourquoi

| Demande | Décision | Raison |
|---|---|---|
| Speed ramps | **Non** | Changer la vitesse d'un plan modifie le montage et la synchronisation des gestes avec la musique ; cela demande ton autorisation explicite (§11). |
| Flou de mouvement ajouté | **Non** | Le flou de bouger est déjà présent dans la source ; en ajouter toucherait les gestes des artistes ou ferait « glisser » le décor. |
| Reflets sur les surfaces | **Non** | Pas de suivi de surface fiable dans cet environnement (§5 : reflets seulement si le suivi est fiable). |
| Animation du décor, extension générative d'arrière-plan | **Non** | Risque d'éléments qui flottent ou contredisent la caméra (§5) ; l'extension « atmosphérique » est réalisée par la brume pondérée par la profondeur. |
| Étincelles | **Non** | Aucun contexte de la source ne les justifie (§4.2 : « lorsque le contexte le justifie »). |
| Netteté supplémentaire | **Non** | Interdite sur les visages ; sur le décor seul, elle créerait une différence de texture au bord des silhouettes. La source est propre et détaillée (doc 03). |
| Débruitage | **Non** | Non nécessaire (doc 03) ; préserve le grain d'origine. |
| Correction manuelle des masques | **Non réalisable ici** | Demande un compositeur humain (rotoscopie) ; compensée par la réduction automatique des effets (doc 08 §8.6). |

## 9.5 Défauts trouvés et corrigés pendant la mise au point (avant livraison)

| # | Défaut | Détection | Correction |
|---|---|---|---|
| 1 | Position du contre-jour non réinitialisée entre plans (elle aurait glissé après chaque coupe) | relecture du code avant rendu | état remis à zéro à chaque plan |
| 2 | Fumée rouge trop dense : panneau « BIENVENUE » noyé, cyan du décor effacé | revue d'images | fumée nuit 0,95 → 0,80 |
| 3 | Micro-plan de cité de jour étalonné avec la LUT nuit du voisin | revue d'images | LUT du voisin le plus ressemblant |
| 4 | Aucune transition déclenchée dans les extraits (règle trop stricte : 1 sur tout le clip) | revue | règle élargie : 6 transitions sur 175 s |
| 5 | **Rayons qui clignotent** (+18 % sur une image) | mesure de stabilité | diagnostic par composante : couleur des rayons lue sur **un seul pixel** → moyenne sur zone et lissage ; source verrouillée par plan |
| 6 | Halos instables d'une image à l'autre | instrumentation | carte des sources lissée et compensée en mouvement |
| 7 | **Erreur de signe : fumée se déplaçant à l'inverse du décor** lors des mouvements de caméra (présente depuis la V4) | vérification sur cas synthétique | signe corrigé (erratum doc 06 §6.9) |
| 8 | Teinte résiduelle pendant un passage N&B (chroma 4,34) : la LUT ajoute des teintes absolues | test N&B automatique | chroma exacte de la source pendant les passages N&B, appliquée après les effets |
| 9 | Correction N&B appliquée deux fois au décor de la version complète | instrumentation | une seule application |
| 10 | Halos pulsant sur une salve de flashs du montage (images surexposées) | revue image par image | détection des flashs, effets suspendus |
| 11 | **Décalage de chrominance de la chaîne de conversion** (V −0,57) visible même sans traitement | essai témoin | conversions et 4K par zscale (V −0,12, comme le chemin YUV direct) |
| 12 | **Coupes masquées par la fusion des détections consécutives** (57 dont inserts d'une image, coupe après une salve) | saut de mesure (extrait 1, image 4275) puis revue image par image | fusion supprimée, inserts classés « effet de montage », masques refaits après chaque nouvelle coupe (doc 08) |
| 13 | **Correction manuelle de classement fausse** : plan de cité de jour (84,06 s) traité en nuit rouge (fumée et flare sur un plafonnier de jour) | même revue | 2e revue des 23 corrections sur 4 images par plan : 2 erreurs rectifiées |
| 14 | Corrections manuelles perdues quand une coupe voisine décale le début du plan | vérification systématique | tolérance de ± 2 images |
| 15 | Transitions déclenchées sur des inserts d'une image (deux voiles à 20 ms d'intervalle) | recomptage après le nouveau découpage | transitions réservées aux coupes entre plans réels |

## 9.6 Les 5 extraits de validation

| # | Extrait | Intervalle | Contenu |
|---|---|---|---|
| 1 | Nuit rouge | 81,58–88,50 s | décor rouge, salves de montage, section forte |
| 2 | Urbain jour | 9,84–15,84 s | cité, longues prises |
| 3 | Atmosphérique | 114,14–120,74 s | rideau métallique → rouge → nuit extérieure (lampadaires) |
| 4 | Noir et blanc | 72,02–78,74 s | couleur → N&B (75,62–76,56 s) → rouge ; flashs du montage ; transition musicale à 76,84 s |
| 5 | Mouvement rapide | 44,48–49,88 s | montage alterné toutes les 2 images, mouvements de caméra |

Pour chaque extrait : `V5_COMPLET` (4K HEVC 10 bits), `V5_ETALONNAGE_SEUL` (livrable « sans
effets supplémentaires »), `MASQUE` (zone protégée), comparatif 4 vues, compilation des 5 extraits.

## 9.7 Rapport de contrôle qualité (rendu final des 5 extraits)

Outil : `tools/v5/qc_extract.py`. Rapports complets dans [`../data/v5/qc/`](../data/v5/qc/).

| Critère (§9 du cahier des charges) | 1 Nuit rouge | 2 Jour | 3 Atmosph. | 4 N&B | 5 Mouv. rapide |
|---|---|---|---|---|---|
| Format 3840×2160, SAR 1:1, 50 i/s, HEVC Main10, BT.709 TV | ✅ 346 img | ✅ 300 img | ✅ 330 img | ✅ 336 img | ✅ 270 img |
| **Pixels opaques des artistes = source** (avant 4K) | ✅ écart 0 (≈ 659 k px/img) | ✅ 0 (≈ 837 k) | ✅ 0 (≈ 570 k) | ✅ 0 (≈ 815 k) | ✅ 0 (≈ 612 k) |
| Synchronisation image (corrélation max à décalage 0) | ✅ 49/49 | ✅ 42/42 | ✅ 47/47 | ✅ 48/48 | ✅ 38/38 |
| Synchronisation audio | ✅ 0,00 ms | ✅ 0,00 ms | ✅ 0,00 ms | ✅ 0,00 ms | ✅ 0,00 ms |
| Scintillement (écart max à la tendance, seuil 12 %) | ✅ 8,2 % | ✅ 0 % (sans effet) | ✅ 4,3 % | ✅ 3,6 % | ✅ 4,1 % |
| Variation progressive max (information) | 23,2 % (*) | 0 % | 7,1 % | 9,0 % | 11,2 % |
| N&B : dominante ajoutée (U/V contre témoin) | — | — | — | ✅ écart 0,01 | — |
| Flashs du montage (effets suspendus) | 0 img | 0 | 7 img | 9 img | 0 |
| Transitions musicales | 0 | 0 | 0 | 1 (76,84 s) | 0 |
| **Verdict** | **CONFORME** | **CONFORME** | **CONFORME** | **CONFORME** | **CONFORME** |

(*) Disparition naturelle des halos quand un tube LED sort du cadre (images 4190–4192, vérifiée
visuellement). C'est une variation progressive et non un clignotement : la mesure de scintillement
a été redéfinie sur l'écart à la tendance (différence seconde) après cette vérification.

**Contrôle visuel** : planches source / V5 sur chaque extrait et zooms à 100 % des contours
(cheveux bouclés, casquettes, dreadlocks, mains en mouvement). Pas de liseré, pas de fumée sur les
artistes, pas d'effet de nuit sur les plans de jour.

**Point d'attention** : à 120,40 s (extrait 3), une image de transition floue du monteur, déjà
orangée dans la source, ressort plus saturée avec la LUT nuit (aucun effet ajouté). C'est à juger à
l'œil.

**Limite du contrôle** : les tests automatiques ne détectent pas une personne d'arrière-plan
non détourée (cf. doc 08 §8.6) ; seule la revue visuelle des comparatifs le permet.

## 9.8 Décisions attendues avant le master

| ID | Question |
|---|---|
| V5-1 | **Règle stricte** (artistes = source, légèrement moins denses que le décor) ou **option** (artistes étalonnés uniformément, carnations protégées) ? Planche `BADLIFE_V5_artistes_strict_vs_option.jpg`. |
| V5-2 | Validation des intensités par famille (fumée, particules, halos, flares, rayons, contre-jour) sur les 5 extraits. |
| V5-3 | Les 4 transitions musicales (72,02 / 76,84 / 88,50 / 148,84 s) : à garder, à renforcer, ou à réduire ? |
| V5-4 | Confirmation des refrains présumés (71–78, 104–114, 148–155 s), si les effets doivent y être renforcés. |
| V5-5 | Speed ramps : demande d'autorisation explicite nécessaire (modification du montage), sinon aucun. |
| V5-6 | Personnes d'arrière-plan non détourées : accepter (effets réduits) ou rotoscopie manuelle par un compositeur. |

## 9.9 Master (étape 8, après validation uniquement)

| Étape | Durée estimée (CPU 4 cœurs) |
|---|---|
| Profondeur sur le clip entier (1 image sur 4) | ≈ 40 min |
| Rendu V5 complet + version étalonnage seul (4K HEVC Main10) | ≈ 3 h 30 à 4 h |
| Contrôle qualité intégral (mêmes tests sur 8760 images) + vérification finale | ≈ 30 min |

Pour le master, l'audio sera **copié bit à bit** depuis la source (pas de réencodage), ce que
vérifiera un hash du flux audio. Les extraits de test portent un AAC 320 kb/s réencodé, car un
extrait ne peut pas être coupé à l'échantillon près en copie de flux. ProRes 422 HQ est possible
sur demande.
