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

_Rendu et contrôles du master : §11.3 et suivants (complétés après rendu)._
