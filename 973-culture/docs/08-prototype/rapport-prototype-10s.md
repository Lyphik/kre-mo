# Rapport — Prototype 3D de 10 s (Kenzo & Maëva)

> 24/11/2026 · Suite au refus du Short 1. Diagnostic préalable : [`diagnostic-faisabilite-3d.md`](diagnostic-faisabilite-3d.md).
> Fichiers : `deliverables/proto10s/` · Pipeline : `production/proto10s/`

## 1. Ce qui a été produit

| Livrable | Spécification |
|---|---|
| `973culture_proto10s_3d_16x9_720p.mp4` | 10 s, 1280×720, 25 i/s, rendu Cycles (CPU) + débruitage OIDN, son stéréo −14 LUFS |
| `973culture_proto10s_3d_vertical_720x1280.mp4` | 10 s, 720×1280, **cadrages verticaux dédiés** (et non un recadrage), sous-titres incrustés |
| `973culture_proto10s_3d_16x9_720p.srt` | Sous-titres séparés pour la version 16:9 |
| `preuves/` | Planches contact, comparatif avant/après, mesures techniques |

## 2. Réponse point par point au retour sur le Short 1

| Problème signalé | Traitement dans le prototype | Résultat |
|---|---|---|
| Personnages trop proches d'illustrations 2D | Humains **3D** paramétriques (MPFB / MakeHuman), peau à diffusion sous la surface, yeux, dents, cils et cheveux en maillage | ✅ Rupture nette avec le 2D ; ⚠️ rendu « personnage de jeu vidéo soigné », pas photoréaliste |
| Kenzo peu naturel | Rotations de tête mesurées sur le squelette, regards qui précèdent la tête, hochements, geste de la main motivé par le texte, respiration, rire partagé | ✅ Nettement plus crédible ; ⚠️ animation procédurale, sans micro-expressions |
| Décor sans profondeur | Vraie scène 3D : gradins en bois de teck, palmiers royaux sur quatre profondeurs, guirlande guinguette, enseigne néon, façades créoles, ciel physique, brume, **profondeur de champ optique** (f/1,8 à f/2,8) | ✅ Profondeur réelle et lumière de fin de journée |
| Trop de cartes graphiques | **Aucune carte** : le prototype est un pur moment de plateau | ✅ |
| Musique réelle insuffisante | Lit musical original ; **aucun morceau de Lyphik** sans autorisation (choix de droits, pas limite technique) | ⚠️ Non traité (bloqué par les droits) |
| Vertical sous-exploité | Rendu vertical natif : duo étagé en profondeur, couronnes de palmiers et ciel en haut, sous-titres dans le tiers inférieur | ✅ |
| Duo presque pas exploité | Scène commune, réplique coupée par Maëva (chevauchement), réactions croisées, rire partagé, découpage champ / contrechamp | ✅ |

## 3. Découpage

| Plan | TC | Caméra | Action |
|---|---|---|---|
| A | 0:00 → 2:00 | Plan à deux, 35 mm, légère contre-plongée, f/2 | Kenzo : « Cinq cent quatre-vingt-quinze mille vues ! », main levée vers Maëva ; elle l'écoute, se penche |
| B | 2:00 → 5:35 | Plan serré Maëva, 70 mm, f/1,8 | Maëva le coupe : « Attends… sur un clip où il n'est même pas l'artiste principal ? » (sourcils levés, geste « attends », regard vers Kenzo puis caméra) |
| C | 5:35 → 7:85 | Plan serré Kenzo, 70 mm, f/1,8 | « Exactement. Ça, c'est Lyphik. » (se tourne vers la caméra, paume ouverte) |
| D | 7:85 → 10:00 | Plan large, 30 mm, poussée lente | Maëva : « Pa mélé ! », rire partagé |

## 4. Auto-évaluation (grille du diagnostic, §4)

Je note avec exigence, en comparant à une production d'animation 3D professionnelle.

| Critère | Poids | Short 1 refusé | Prototype 3D | Justification |
|---|---|---|---|---|
| Crédibilité des personnages | 20 % | 3 | **6** | 3D réelle et cohérente ; visages génériques MakeHuman, cheveux en cartes, teint de Maëva plus foncé que prévu |
| Jeu et réactions | 20 % | 3 | **6** | Regards, gestes et rire motivés ; pas de micro-expressions ni de jeu d'acteur capturé |
| Synchronisation labiale | 10 % | 4 | **5,5** | Visèmes 3D calés sur l'enveloppe audio ; forme des lèvres approchée |
| Décor et profondeur | 15 % | 4 | **7** | Profondeur optique, ambiance ; lieu évoqué, bâtiments simplifiés |
| Lumière et étalonnage | 10 % | 5 | **7** | Heure dorée cohérente, rim light, bokeh ; quelques ombres dures sur un visage |
| Cadrage et montage | 10 % | 4 | **7** | Grammaire champ / contrechamp, focales, poussées ; quatre plans seulement |
| Son (voix, mixage) | 10 % | 4 | **5** | Voix de synthèse Piper, intonation limitée ; mixage propre à −14 LUFS |
| Dynamique du duo | 5 % | 2 | **6,5** | Interruption, réactions croisées, rire partagé |
| **Note pondérée** | | **≈ 3,6 / 10** | **≈ 6,2 / 10** | |

### Verdict honnête

**L'objectif de 9/10 n'est pas atteint.** Le prototype est un saut réel : de l'illustration 2D figée à une scène 3D vivante, d'environ 3,6 à environ 6,2 sur une grille exigeante. Il plafonne pour des raisons identifiées, pas faute d'effort :

1. **Les personnages** : MakeHuman produit des humains crédibles mais génériques. Un 9/10 demande des personnages sculptés sur mesure, ou de type MetaHuman, et des cheveux en vraies fibres.
2. **Le jeu** : l'animation est procédurale. Un 9/10 demande une **capture faciale**. Le squelette du prototype accepte déjà les 52 formes ARKit : une simple capture avec un iPhone (applications de type Live Link Face, export CSV) pourrait les piloter directement.
3. **Les voix** : la synthèse vocale locale plafonne la crédibilité. Des comédiens voix guyanais ou antillais sont indispensables.
4. **Le calcul** : sans GPU, 20 échantillons en 720p à environ 35 s par image. Un GPU permettrait du 1080p ou du 4K, plus d'échantillons et des cheveux en fibres.

## 5. Recommandation pour atteindre 9/10

| Levier | Gain estimé | Coût / prérequis |
|---|---|---|
| Comédiens voix (2) | +1,0 | Cachets ; enregistrement en studio ou à domicile de bonne qualité |
| Capture faciale ARKit (iPhone) → 52 formes déjà en place | +1,0 | Un iPhone avec Face ID, une application de capture, le comédien |
| Personnages sur mesure (sculpt, cheveux en fibres) | +0,8 | Artiste 3D ou outils de type MetaHuman |
| Rendu GPU (local ou cloud) | +0,4 | Une carte graphique ou un service de rendu (budget à valider) |
| Repérage photo et HDRI de la Place des Palmistes | +0,3 | Une demi-journée sur place |

Avec ces leviers, un 8,5 à 9/10 devient atteignable. Sans eux, le plafond de cet environnement se situe autour de 6,5/10.

## 6. Défauts connus du prototype (à corriger à la prochaine itération)

1. Teint de Maëva plus foncé que le « caramel » de la bible : à éclaircir (texture `young_african_female` avec gain de luminosité).
2. Ombre portée dure traversant le visage de Maëva dans le plan B.
3. Cheveux de Kenzo en cartes, visibles en gros plan.
4. Rendu en 720p (et non 1080p), faute de GPU.

## 7. Crédits et licences des actifs 3D

- Blender 4.2 LTS (GPL), extension MPFB 2.0.18 (GPL-3).
- Actifs MakeHuman **CC0** : corps, peaux, yeux, sourcils, cils, dents, vêtements, poses (Poses 01), visèmes, unités faciales.
- Coiffure de Maëva : *punkduck_alpha7_curly* (pack Hair 03), **CC-BY**, auteur punkduck (attribution obligatoire).
- Voix : Piper (voir `../04-droits/autorisations.md` pour les licences des modèles).
- Musique : composition originale 973 Culture.
