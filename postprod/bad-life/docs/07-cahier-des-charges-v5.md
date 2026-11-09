# 07 — Cahier des charges V5 (référence)

> Version « V5 définitive » reçue le 2026-11-09. Elle remplace les demandes V1 à V4 pour la suite
> du projet. Ce document en conserve les exigences sous forme structurée ; toute évolution doit être
> versionnée.

| Paramètre | Valeur |
|---|---|
| Direction artistique | C hybride |
| Intensité des effets | plus poussée que la V4, toujours réaliste |
| Format final | 3840 × 2160, 50 i/s, 16:9 |
| Références | Sponge Production, Cole Bennett, William Thomas, cinéma urbain contemporain |

## 1. Objectif
Améliorer considérablement la qualité visuelle sans modifier le montage : colorimétrie, étalonnage
plan par plan, contraste et dynamique, profondeur des décors, atmosphère, lumière, transitions,
netteté et clarté, cohérence entre plans. Résultat cinématographique, immersif, moderne,
ultra-réaliste, qui garde l'identité originale du clip.

## 2. Règle absolue : protection des artistes
Interdiction de modifier leur apparence : visages, traits, mâchoires, morphologie, expressions,
proportions, silhouettes, cheveux et texture capillaire, texture de peau, bijoux, accessoires,
vêtements, logos, gestes.

Interdits : génération IA sur les artistes, face enhancement, face restoration, changement de
peau, remplacement de visage, lissage, changement de morphologie, éclaircissement sélectif de la
peau, netteté artificielle sur les visages.

Méthode obligatoire :
1. Détourage IA **uniquement** pour les masques de protection.
2. Conserver une copie originale de chaque image des artistes.
3. Effets sur une couche indépendante du décor.
4. **Recomposer les artistes au-dessus des effets à partir de leur image originale.**
5. Contrôler les contours (cheveux, vêtements, accessoires).
6. **Vérifier que les pixels opaques des artistes restent identiques à la source avant le
   redimensionnement final.** Ce redimensionnement 4K doit être uniforme, sans retouche sélective.

En cas de détourage incertain : réduire ou supprimer l'effet.

## 3. Direction colorimétrique C hybride
- **Nuit / rouge** (base C) : noirs profonds détaillés, rouges intenses mais pas fluorescents,
  ambre et orange maîtrisés, cyan / bleu pétrole dans les ombres du décor, contraste renforcé,
  profondeur atmosphérique.
- **Jour urbain** (base A) : contraste naturel, exposition équilibrée, blancs maîtrisés, couleurs
  réalistes, vert des vêtements préservé, détails dans les ombres, pas de dominante rouge.
- **Atmosphérique** (complément B) : profondeur, fumée réaliste, particules discrètes, transitions naturelles.
- **Noir et blanc** : intention du montage conservée exactement (couleur → N&B → couleur), aucune
  dominante cyan, rouge ou ambre.

## 4. Effets visuels V5
- 4.1 Fumée volumétrique : rouge de nuit, ambre autour des sources adaptées, mouvement organique,
  densité variable, profondeur selon la perspective, **toujours derrière les artistes**.
- 4.2 Particules : poussières lumineuses, micro-particules, étincelles très discrètes si le contexte
  le justifie, particules dans les faisceaux. Pas d'effet « jeu vidéo ».
- 4.3 Flares et halation : reflets anamorphiques, halation subtile, glow sur les sources, reflets
  rouges et ambre. **Localisés sur les vraies sources, jamais autour des visages.**
- 4.4 Lumière volumétrique : rayons dans la fumée, contre-jours rouges, ambre, cohérents avec les sources du décor.
- 4.5 Caméra : micro-parallaxe atmosphérique, speed ramps très ponctuels, flou de mouvement naturel,
  transitions lumineuses et raccords calés sur la musique. **Ne jamais désynchroniser les artistes
  et la musique.**

## 5. Effets IA sur le décor
À explorer, sans toucher aux artistes : profondeur, extension atmosphérique, lumière nocturne,
brume, particules dans la perspective, reflets seulement si le suivi de surface est fiable,
animation subtile du décor. Rien qui flotte, glisse ou contredise les mouvements de caméra.

## 6. Netteté et qualité
Image propre et lisible, débruitage seulement si nécessaire, grain et texture préservés, netteté
maîtrisée, aucun contour artificiel, halo de sharpening ou scintillement. Pas de détails inventés
par IA générative ; upscale 4K de qualité.

## 7. Synchronisation musicale
Analyser kicks, snares, basses, changements de rythme, impacts, transitions instrumentales,
moments forts. Synchroniser **certains** effets, pas systématiquement : seulement là où ils
renforcent l'émotion.

## 8. Pipeline
1. Sécurisation. 2. Analyse complète (coupes sur 175,2 s, plans réels, ambiances, N&B, zones de
détourage difficile). 3. Masques (détourage, suivi temporel, contours, correction manuelle si
nécessaire). 4. Étalonnage par famille (bases A, B, C ; pas de variation brutale entre plans
consécutifs). 5. Effets. 6. Contrôle. 7. **Validation sur 5 extraits** (nuit rouge, urbain jour,
atmosphérique, passage N&B, mouvement rapide), avec comparatifs avant / après. 8. Master **après
validation uniquement** (3840 × 2160, 50 i/s, HEVC Main10 ou ProRes, audio synchronisé, vérification intégrale).

## 9. Critères de rejet
Modification du visage, du corps, des cheveux ou des vêtements ; contours artificiels ; fumée
traversant les artistes ; effets qui apparaissent ou disparaissent brutalement ; scintillement ;
couleurs incohérentes ; transitions mal synchronisées ; perte de qualité audio ou vidéo.

## 10. Livrables
1. Master 4K V5. 2. Version avant / après. 3. Version sans effets supplémentaires. 4. LUT et
réglages. 5. Documentation technique. 6. Rapport de contrôle qualité. 7. Sauvegarde du projet et des scripts.

## 11. Règle de production
Pas d'accumulation d'effets ; chaque effet doit être justifié ; artistes strictement fidèles ;
décors plus profonds, couleurs plus marquées, rendu de vraie production professionnelle.
Aucune modification du montage sans autorisation ; aucun master avant validation des tests V5.
