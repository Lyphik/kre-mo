# Diagnostic de faisabilité 3D — Prototype 10 s (Kenzo & Maëva)

> 13/11/2026 · Contexte : le Short 1 n'est pas validé (personnages trop « illustration 2D », Kenzo peu naturel, décor sans profondeur, trop de cartes graphiques, duo sous-exploité, vertical sous-exploité).
> Contraintes : aucun achat, ressources existantes conservées, pas de nouveau rendu de l'épisode complet.

## 1. Inventaire réel de l'environnement (mesuré)

| Ressource | État | Conséquence |
|---|---|---|
| CPU | 4 cœurs, 15 Go de RAM | Rendu 3D possible mais lent |
| GPU | **Aucun** (pas de `/dev/dri`, pas de pilote NVIDIA) | Pas d'accélération matérielle ; EEVEE seulement via Mesa logiciel (non garanti) ; Cycles en CPU |
| Mesa / llvmpipe | Présent | OpenGL logiciel : piste pour EEVEE, à tester |
| Blender 4.2 LTS (blender.org) | **Téléchargé (350 Mo), exécution refusée par le contrôle de sécurité de la session** (« code externe ») | Bloquant : nécessite ton autorisation explicite |
| MPFB 2.0.18 (MakeHuman pour Blender, GPL-3, extensions.blender.org) | Repéré, non installé (même blocage) | Générateur d'humains paramétriques réalistes |
| Actifs MakeHuman **CC0** | Disponibles (vérifiés) : système 267 Mo, **visèmes** (Visemes 01/02), **unités faciales** (Faceunits 01), **poses assises** (Poses 01), peaux (Skins 01-03), cheveux (Hair 01 CC0, Hair 02/03 CC-BY) | Matière première suffisante pour deux personnages cohérents, la synchronisation labiale et des expressions |
| HDRI Poly Haven (CC0) | API accessible, CDN `dl.polyhaven.org` en erreur 521 au moment du test | Alternative : ciel physique « Nishita » intégré à Blender |
| IA vidéo générative (Weave/Figma) | Compte non relié, **payant** | Exclu (aucun achat) |
| Voix | Piper local (existant) | Réutilisé ; dialogue du prototype déjà généré (`production/proto10s/`) |

## 2. Options comparées

| Critère | A. **Blender + MPFB + Cycles** (recommandé) | B. IA vidéo générative + synchro labiale | C. Moteur 2D actuel amélioré (2,5D) |
|---|---|---|---|
| Faisabilité ici | ✅ si exécution autorisée | ❌ payant, compte non relié | ✅ immédiate |
| Personnages | Humains 3D paramétriques, peau avec diffusion sous la surface (SSS), vrais cheveux en maillage | Photoréalistes | Illustration vectorielle |
| Cohérence d'un plan à l'autre | ✅ parfaite (même modèle 3D) | ⚠️ dérives fréquentes (visages, mains) | ✅ |
| Synchronisation labiale | ✅ visèmes en shape keys, pilotés par l'audio | ✅ (modèles dédiés) | ⚠️ approchée |
| Expressions / réactions | ✅ unités faciales (sourcils, sourire, yeux), regards, hochements, gestes par os | ✅ | ⚠️ limitées |
| Décor et profondeur | ✅ vraie 3D, profondeur de champ optique, lumière physique, parallaxe réelle | ✅ | ❌ |
| Cadrage cinéma (focale, mise au point, mouvement) | ✅ | ⚠️ peu contrôlable | ⚠️ simulé |
| Temps de rendu 10 s (250 images) | ≈ 1 à 4 h en CPU (720p à 1080p, débruitage OIDN) | Minutes | Minutes |
| **Plafond de qualité honnête** (grille §4) | **≈ 7/10** : les humains MakeHuman ont un rendu « CG de jeu vidéo » soigné, pas photoréel | 8-9/10 potentiel, risque de dérives | ≈ 5/10 |
| Déclaration YouTube « contenu synthétique » | Non requise (non photoréaliste), recommandée | **Obligatoire** | Non requise |

### Pourquoi 9/10 n'est pas garanti, même avec l'option A

- Les personnages MakeHuman, même bien éclairés, restent identifiables comme des personnages de synthèse : peau un peu lisse, cheveux en « cartes », micro-expressions limitées.
- La voix de synthèse (Piper) plafonne la crédibilité du dialogue, quelle que soit l'image.
- Sans GPU, le nombre d'échantillons et la résolution sont limités par le temps de rendu.
- Un 9/10 exigeant (production professionnelle) demanderait au minimum : comédiens voix, capture faciale ou animateur, et un GPU (ou un rendu déporté).

**Je ne déclarerai pas l'objectif de 9/10 atteint sans preuve visuelle.** L'auto-évaluation sera publiée avec la grille ci-dessous.

## 3. Plan du prototype (option A)

| Élément | Mise en œuvre |
|---|---|
| Durée | 10 s (dialogue de 8,45 s + 1,5 s de réaction) |
| Dialogue | K : « Cinq cent quatre-vingt-quinze mille vues ! » → M (le coupe) : « Attends… sur un clip où il n'est même pas l'artiste principal ? » → K : « Exactement. Ça, c'est Lyphik. » → M (rire) : « Pa mélé ! » |
| Scène commune | Les deux personnages assis côte à côte sur les gradins, tournés l'un vers l'autre, micros sur bras articulés |
| Découpage | Plan 1 : plan à deux en 3/4 (50 mm, f/2,8) avec lente poussée → Plan 2 : contrechamp sur Maëva par-dessus l'épaule de Kenzo (85 mm) → Plan 3 : retour en plan à deux pour le rire partagé |
| Réactions | Regards qui se croisent, Maëva qui se penche et lève les sourcils, Kenzo qui sourit et désigne la caméra, rire partagé, hochements |
| Décor | Gradins en bois, palmiers royaux modélisés en 3D (quatre profondeurs), façades créoles en volumes, guirlande lumineuse (sources réelles), enseigne néon émissive, ciel physique de fin de journée, brume atmosphérique, bokeh |
| Vertical | Version 9:16 cadrée sur le duo (les deux visages occupent l'image), sans zones vides |
| Musique | Lit musical original existant. **Les morceaux de Lyphik restent exclus sans autorisation** : c'est un choix de droits, pas une limite technique |

## 4. Grille d'évaluation (sur 10, pondérée)

| Critère | Poids | Ce qu'un 9/10 exige |
|---|---|---|
| Crédibilité des personnages (modelé, peau, cheveux) | 20 % | Indiscernable d'une production d'animation 3D professionnelle |
| Jeu et réactions (regards, expressions, timing) | 20 % | Réactions motivées, pas de mouvement mécanique |
| Synchronisation labiale | 10 % | Aucune désynchronisation perceptible |
| Décor et profondeur | 15 % | Lieu reconnaissable, profondeur optique, ambiance |
| Lumière et étalonnage | 10 % | Lumière motivée, palette cohérente |
| Cadrage et montage | 10 % | Grammaire champ / contrechamp, rythme |
| Son (voix, mixage) | 10 % | Voix naturelles, mixage propre |
| Dynamique du duo | 5 % | Complicité perceptible |

## 5. Décision requise

L'option A exige que tu **autorises l'exécution de Blender 4.2 LTS** (binaire officiel de blender.org) **et de l'extension MPFB** (extensions.blender.org, licence GPL-3) dans cette session. Sans cette autorisation, seule l'option C est possible : elle ne répond pas à ta demande de 3D et plafonne autour de 5/10.
