# Décor & charte visuelle — 973 CULTURE

> **Source de vérité technique** : `production/src/setdesign.py` (décor), `production/src/config.py` (palette), `production/src/scenes.py` (habillages).

## 1. Le décor : plateau éphémère, Place des Palmistes (Cayenne)

### 1.1 Ce qui est fidèle au lieu (sources L1-L2 de `../01-recherche/sources.md`)

| Élément | Traitement |
|---|---|
| Palmiers royaux (« palmistes ») en rangées | Deux rangées en profondeur, troncs lisses gris clair, manchon vert, palmes animées par le vent |
| Architecture créole de Cayenne | Façades à étage, balcons filants, persiennes, toits à quatre pans en tôle, couleurs pastel |
| Monument Félix Éboué (portique avec statue en pied, 1957) | **Évocation lointaine et stylisée**, sans prétention documentaire |
| Lieu de vie du soir, lampadaires | Lampadaires qui s'allument au fil de l'épisode |

### 1.2 Ce qui relève de la mise en scène (à assumer)

- **Les gradins sont un plateau éphémère installé par la production.** Aucune source consultée ne confirme l'existence de gradins permanents sur la place. Le décor montre donc des gradins en bois avec lumière LED, une guirlande guinguette, une enseigne néon « 973 CULTURE », des héliconias en pot et deux micros sur bras articulés.
- La disposition exacte de la place (orientation, position du monument, alignement des bâtiments) est **simplifiée**. Avant une communication qui présenterait le décor comme fidèle, faire valider par un repérage photo sur place. Recommandation : photographier la place pour les prochains épisodes, sous licence propre à 973 Culture.
- **Aucune foule et aucun événement réel** ne sont représentés.

### 1.3 Lumière

L'épisode commence à l'**heure dorée** (soleil couchant, ciel orangé) et se termine **de nuit** (étoiles, fenêtres allumées, guirlandes et LED à pleine intensité). Le paramètre `tod` passe de 0,04 à 0,96 au fil de l'épisode.

### 1.4 Grammaire caméra

| Plan | Usage |
|---|---|
| `set_wide` | Respirations, ouverture et fin de séquence |
| `two_shot` / `over_K` / `over_M` | Échanges, réactions |
| `single_K` / `single_M` | Prise de parole ; bascule automatique vers le plan à deux après 62 % d'une réplique longue (plus de 7 s) |
| Habillages graphiques | Médaillon de l'orateur en bas d'écran, pour garder la présence des présentateurs |

Effets : parallaxe sur 6 profondeurs, profondeur de champ simulée (arrière-plan rendu en basse résolution sur les plans serrés), poussée lente de la caméra, léger flottement de type opérateur, amorces de feuillage en premier plan.

## 2. Palette officielle

| Nom | Hex | Usage |
|---|---|---|
| Noir profond | `#0A1012` | Fonds, cartouches |
| Vert forêt | `#084D35` | Identité, Kenzo |
| Vert feuille | `#177A54` | Nœuds pivots, statut « CONFIRMÉ » |
| Jaune doré | `#F9BF3B` | Accent principal, logo, chiffres |
| Rouge | `#D93434` | Alertes, Lyphik au centre du graphe, Maëva |
| Blanc cassé | `#F8F6F0` | Textes |
| Bleu électrique | `#2E8DFF` | Données vérifiées, transparence, fact-check |

Règle : les couleurs évoquent la Guyane sans reproduire le drapeau. Le liseré vert/jaune/rouge reste un filet discret.

## 3. Typographie

| Usage | Police |
|---|---|
| Titres, chiffres, logo | **Inter Display Black / Bold** |
| Textes courants, sources | **Inter Medium / SemiBold** |
| Codes techniques (EX-01, PLAY) | JetBrains Mono |

Polices sous licence SIL Open Font License, installées dans l'environnement de rendu.

## 4. Bibliothèque d'habillages réutilisables

`logo` · `name_reveal` · `stat` (compteur vérifié) · `map` (Natural Earth, domaine public) · `quote` · `pml` (typo-concept réutilisable pour toute signature d'artiste) · `timeline` · `clip_slot` (emplacement d'extrait sous autorisation) · `cards` (pochettes **typographiques originales**) · `ep` · `network` (graphe en étoile) · `press` · `persona` · `factcheck` · `badlife` (gabarit « sortie de la semaine ») · `paradox` · `playlist` · `cta` · `end_logo`.

Chaque habillage affiche sa **ligne SOURCE** en bas d'écran. C'est une signature éditoriale de l'émission.
