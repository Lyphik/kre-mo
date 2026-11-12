# Bible des personnages — KENZO & MAËVA

> **Statut** : v1.0 validée pour l'épisode 01 · **Source de vérité technique** : `production/src/characters.py` (dictionnaire `DESIGN`)
> Les deux présentateurs sont des **personnages fictifs animés**. Ils ne représentent aucune personne réelle et ne doivent jamais être présentés comme ayant interviewé un artiste.

## 1. Principe de cohérence

Les personnages sont des **modèles vectoriels paramétriques**. Chacun est défini une seule fois (couleurs, proportions, coiffure, tenue) et redessiné à chaque image, à partir de ce modèle unique. Conséquences :

- **même visage, mêmes proportions, même coiffure, même tenue** dans tous les plans et dans tous les épisodes, sans aucune dérive ;
- aucune déformation entre les plans : pas de génération image par image ;
- seuls varient les **paramètres d'expression** : ouverture de la bouche, visème, clignement, regard, rotation de la tête, sourcils, sourire, gestes des bras, respiration.

Toute évolution de tenue (par exemple une tenue par saison) doit passer par une nouvelle version de ce document et du dictionnaire `DESIGN`.

## 2. KENZO — le présentateur

| Attribut | Valeur |
|---|---|
| Âge apparent | 28-35 ans |
| Origine évoquée | Guyanaise, caribéenne |
| Peau | Brun foncé `#5C3B2A` · ombre `#3E271B` · lumière `#7B5139` |
| Coiffure | High-top court en twists, contour net (line-up), dégradé sur les côtés |
| Pilosité | Barbe courte taillée, bouc, moustache fine |
| Tenue | Surchemise vert forêt `#0E4A35` (manches retroussées, poches poitrine) sur tee-shirt blanc cassé, pantalon anthracite |
| Accessoires | Chaîne fine dorée, montre acier au poignet gauche |
| Sneakers | Blanches, virgule verte (design original, sans marque), semelle gomme |
| Couleur signature | **Vert** |

**Personnalité éditoriale** : passionné, connaisseur de rap, drôle et direct. C'est lui qui **lance les débats** (« Je vais être un peu provocateur… ») sans agressivité. Il cadre les limites éthiques (« on ne va pas l'inventer »). Running gag de l'épisode 01 : « Pa mélé ».

**Voix** : Piper `fr_FR-tom-medium`, débit 0,93. Placée légèrement à gauche dans le mixage stéréo, comme à l'image.

## 3. MAËVA — la présentatrice

| Attribut | Valeur |
|---|---|
| Âge apparent | 25-32 ans |
| Origine évoquée | Chabine, teint caramel |
| Peau | `#C68A5E` · ombre `#A26C45` · lumière `#DCA477` |
| Coiffure | Volume bouclé jusqu'aux épaules, châtain `#5A3020` avec reflets caramel `#A2643A`, raie de côté, boucles encadrant le visage |
| Maquillage | Discret : trait d'eye-liner, lèvres terracotta `#9C4B3E` |
| Tenue | Blazer rouge brique `#B5332E` ouvert sur un top doré pâle, pantalon large noir |
| Accessoires | Créoles dorées, collier fin à pendentif, bracelet doré au poignet droit |
| Sneakers | Blanches, virgule dorée (design original, sans marque) |
| Couleur signature | **Rouge** |

**Personnalité éditoriale** : fine observatrice, avis tranché, n'hésite pas à **contredire** Kenzo (« Ou alors, c'est le public qui doit arrêter de vouloir ranger les artistes ! »). Elle porte la rigueur (« je préfère le dire franchement plutôt que de vous raconter des histoires ») et la perspective culturelle.

**Voix** : Piper `fr_FR-siwis-medium`, débit 0,94. Placée légèrement à droite.

## 4. Grammaire de jeu (animation)

| Comportement | Règle |
|---|---|
| Synchronisation labiale | Ouverture = enveloppe RMS réelle de la voix (25 i/s) ; forme = visème déduit des phonèmes (arrondi, étiré, fermé, f/v, ouvert) |
| Regard de l'orateur | Alterne caméra et partenaire, par segments d'environ 2,7 s, avec transitions douces |
| Regard de l'auditeur | Tourné vers l'orateur |
| Hochements | L'auditeur hoche la tête environ toutes les 3,2 s pendant une réplique longue |
| Clignements | Intervalles aléatoires de 2,2 à 5 s (15 % de doubles clignements) |
| Gestes | Main dominante tirée au sort pour chaque réplique, amplitude liée à l'intensité de la parole |
| Émotions | `laugh` (sourire large, sourcils levés), `tease`, `argue`, `smile` — annotées dans le script |
| Lumière | Lumière de contour bleutée qui augmente avec la tombée de la nuit |

## 5. Limites connues (honnêteté de production)

- Style **illustration vectorielle 2D**, et non photoréaliste. C'est un choix assumé, imposé par les outils disponibles, qui a un avantage : aucun risque d'« uncanny valley » ni de confusion avec des personnes réelles.
- Synchronisation labiale **approchée**. Le minutage est exact, puisqu'il suit l'audio réel, mais la forme des lèvres est estimée : les modèles vocaux utilisés ne fournissent pas l'alignement des phonèmes.
- Voix de synthèse neuronale **locale**, de qualité moyenne : intonation correcte mais perceptiblement artificielle. Pistes d'amélioration au § 6.

## 6. Évolutions recommandées (épisodes suivants)

1. **Voix** : faire enregistrer deux comédiens voix guyanais ou antillais, ou utiliser une synthèse vocale premium avec un consentement documenté. Le pipeline accepte n'importe quel fichier WAV par réplique (`build/voice/<id>.wav`).
2. **Visèmes** : forcer l'alignement des phonèmes (Montreal Forced Aligner, ou modèle Piper avec sortie des durées) pour une synchronisation labiale exacte.
3. **Version photoréaliste** : possible avec un générateur vidéo et un modèle de synchronisation labiale (non disponibles dans cet environnement : le compte Weave/Figma n'est pas relié). Dans ce cas, utiliser cette bible comme référence de personnage et activer la déclaration « contenu synthétique » sur YouTube.
