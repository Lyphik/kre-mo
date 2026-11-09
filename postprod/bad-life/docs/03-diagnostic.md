# 03 — Diagnostic (étape 2)

Sources : statistiques de la doc 02, planches contact (une image médiane par plan) et recadrages à 100 %.
Chaque constat indique s'il est **mesuré** (chiffré) ou **observé** (visuel, donc à confirmer).

## 3.1 Constats globaux

| # | Constat | Nature | Impact sur le cahier des charges |
|---|---|---|---|
| G1 | **Noirs relevés** : luma minimale typique 23–27 (au lieu de 16), percentile 10 entre 30 et 36. Image « voilée ». | Mesuré | §4 « noirs profonds » non atteint |
| G2 | **Saturation très faible** sur tout le clip (SATAVG 3 à 9 hors flashs). Rouges ternes, peaux quasi neutres sur certains plans (chroma ≈ 0,003 sur le visage du plan #32). | Mesuré | §4 « rouge profond et lumineux » non atteint. Contrainte forte : la peau ne peut pas être isolée par sa teinte seule. |
| G3 | **Hautes lumières** : 253 atteint (familles A et B). Écrêtage localisé probable sur ciel / murs blancs / tubes LED, **irrécupérable** en 8 bits. | Mesuré (valeurs) / observé (zones) | §4 « hautes lumières contrôlées » : seul l'adoucissement de la transition est possible, pas la récupération. |
| G4 | **Bruit faible**, compression propre (24,6 Mb/s). Légère douceur optique, détail correct sur les visages. | Observé (100 %) | §7 : **aucun débruitage nécessaire** pour l'instant, ce qui préserve la texture de peau. Hypothèse à revérifier sur les plans de nuit D/Outro. |
| G5 | Contraste plat, faible séparation sujets / fond, surtout dans la cité (murs clairs, sujets sombres). | Observé | §4 « séparation » : demande des masques (voir doc 05). |
| G6 | Aucun plan instable au point de justifier une stabilisation. La caméra à l'épaule fait partie du style. | Observé | §7 : pas de stabilisation proposée. |

## 3.2 Par famille

### A — Cité, jour couvert (25 plans, 82,7 s)
- Dominante vert-jaune sur les murs de la cage d'escalier ; ciel et murs blancs proches de l'écrêtage.
- **Variation d'exposition** entre plans : luma moyenne de 49 à 87. Une partie de l'écart vient du
  contenu (murs blancs ou foule sombre), pas seulement de l'exposition : **à arbitrer plan par
  plan** à l'étape 6, pas par une égalisation automatique.
- Visages à peau foncée souvent sous-exposés par rapport au fond clair : c'est le risque principal
  si l'on augmente le contraste.

### B — Décor rouge « BIENVENUE », nuit (12 plans, 42,1 s)
- Bonne base « nocturne » : tubes LED rose et bleu, rideaux rouges. C'est la famille la plus proche
  de la direction artistique.
- Noirs voilés, rouges désaturés et tirant vers le brique.
- Lumière d'appoint **verte** sur les sujets (plans #53, #82, #102, #110) : choix d'éclairage du
  tournage. Elle est conservée (on ne modifie pas la lumière réelle sur les artistes).

### C — Rideau métallique / grille (12 plans, 20,4 s)
- Lumière d'appoint frontale chaude, fond clair. Bonne exposition des visages. Rideau métallique
  beige-vert.

### D — Extérieur nuit / crépuscule (3 plans, 7,8 s)
- Très sombre ; point lumineux des lampadaires. Plan #125 : saturation 1,0, quasi N&B (à vérifier).

### Cas particuliers
- **#60 (75,16–76,84 s)** : noir et blanc dans la source. Intention présumée, **à confirmer**.
- **#130 (161,7–175,2 s, 13,5 s)** : très assombri et désaturé (fondu de fin présumé). Ne pas « corriger ».
- **Salves de flash** et image blanche (95,50 s) : effets de montage, conservés tels quels.

## 3.3 Liste des plans à améliorer (priorités)

1. **Tout le clip** : noirs (G1), saturation et rouges (G2), cohérence de palette → étalonnage global (LUT v3).
2. **Famille A** : harmonisation d'exposition plan par plan, séparation des sujets (masques), dominante verte.
3. **Famille B** : principale candidate aux effets (fumée discrète, halos des tubes LED, lumière derrière les artistes).
4. **Familles D / Outro** : contrôle du bruit après étalonnage.
5. **Plans #1–#3** : traitement des titres incrustés (décision D4, doc 05).
