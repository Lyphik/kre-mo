# Note de production — Épisode 01 (pilote)

> 973 CULTURE – LE PODCAST · « LYPHIK : de Matoury à la scène, un parcours à découvrir »
> Version 1.1 · 12/11/2026

## 1. Ce qui a été produit

| # | Livrable obligatoire | Fichier | Statut |
|---|---|---|---|
| 1 | Vidéo complète MP4 | `deliverables/ep01/973culture_ep01_lyphik_master_1080p25.mp4` | ✅ 1920×1080, 25 i/s, H.264 + AAC stéréo 48 kHz, -14 LUFS, 7 min 41 s |
| 2 | Miniature YouTube | `deliverables/ep01/973culture_ep01_miniature_1280x720.jpg` | ✅ |
| 3 | Scénario final | `docs/02-scenario/scenario-ep01.md` (source : `production/script/ep01.json`) | ✅ |
| 4 | Sous-titres SRT | `deliverables/ep01/973culture_ep01_lyphik_fr.srt` | ✅ 159 sous-titres, sans chevauchement |
| 5 | 3 à 5 Shorts verticaux | `deliverables/ep01/shorts/` (5 Shorts + leurs SRT) | ✅ voir rapport QC |
| 6 | Description YouTube | `docs/05-publication/youtube-ep01.md` §2 | ✅ |
| 7 | Titres et hashtags | `docs/05-publication/youtube-ep01.md` §1, §3, §4 | ✅ |
| 8 | Liste des sources | `docs/01-recherche/sources.md` + `data/snapshot-2026-11-12.json` | ✅ |
| 9 | Droits et autorisations | `docs/04-droits/autorisations.md` | ✅ |
| 10 | Rapport de contrôle qualité | `docs/07-qc/rapport-qc.md` | ✅ |
| 11 | Branding de chaîne | `docs/06-branding/branding-chaine.md` | ✅ |
| + | Version courte de présentation du programme | `deliverables/ep01/973culture_ep01_teaser_programme_16x9.mp4` | ✅ |
| + | Stratégie de chaîne, monétisation, grille d'émissions | `docs/05-publication/strategie-chaine-monetisation.md` | ✅ |
| + | Bible personnages, décor, charte | `docs/03-direction-artistique/` | ✅ |
| + | Pipeline de production reproductible | `production/` | ✅ |

## 2. Outils réellement disponibles et choix techniques

| Besoin du brief | Outil disponible ici | Choix |
|---|---|---|
| Génération vidéo IA photoréaliste et synchronisation labiale | ❌ Aucun : les modèles Weave/Figma sont payants et le compte n'est pas relié | **Animation vectorielle 2D programmée** (Cairo), personnages paramétriques |
| Voix naturelles | ❌ Aucun service vocal premium | **Piper TTS** (synthèse neuronale locale, gratuite) |
| Musique originale | ❌ Aucun générateur de musique | **Composition procédurale** en Python (numpy/scipy) |
| Montage | FFmpeg | Compositeur Python → H.264 / AAC |
| Recherche | Recherche web, pages publiques, API publique Deezer | Relevé daté, archivé en JSON |

Conséquence assumée : le résultat est une **émission animée au style illustré**, pas un rendu photoréaliste. Ce choix supprime aussi les risques d'avatars qui se déforment, de visages qui changent entre les plans et de confusion avec des personnes réelles.

## 3. Écarts avec le brief (et pourquoi)

| Demande du brief | Réalisé | Raison |
|---|---|---|
| Titre « de **Cayenne** à la scène » | « de **Matoury** à la scène » | La biographie officielle situe son enfance à Copaya (Matoury), puis au Larivot. Cayenne reste le lieu du décor |
| Personnages réalistes, lèvres parfaitement synchronisées | Personnages illustrés 2D ; minutage de la bouche exact (enveloppe audio réelle), forme des lèvres estimée | Pas de générateur vidéo ni d'alignement des phonèmes disponibles (voir bible §5-6) |
| Voix naturelles avec rires | Voix de synthèse ; les rires sont joués à l'image (expressions), pas à l'audio | La synthèse vocale ne produit pas de rires crédibles |
| Photos de référence de la Place des Palmistes | Décor stylisé d'après des descriptions sourcées ; gradins présentés comme un plateau éphémère | Aucune photo libre de droits exploitable dans cet environnement ; existence de gradins non confirmée |
| Extraits de clips intégrés | Cartes « clip officiel — à voir sur YouTube » + 5 emplacements chronométrés (EX-01 à EX-05) | Autorisations non obtenues (voir `04-droits`) ; le master est publiable sans elles |
| Analyse des clips en réaction aux images | Analyse fondée sur les métadonnées et les **miniatures** (dit explicitement à l'antenne) | Les clips n'ont pas pu être visionnés (contrôle anti-robot de YouTube, non contourné) |
| Minutage indicatif des séquences (séquence 2 à 0:35…) | Séquence 2 à 0:58, total 7 min 41 s | Carton de transparence ajouté à l'introduction ; durée totale dans la fourchette de 6 à 8 min |
| 4K si possible | 1080p | Le moteur est vectoriel, donc un rendu 4K est possible (facteur d'échelle ×2), mais il multiplie par 4 le temps de rendu et la taille du fichier ; 1080p suffit pour le pilote |
| Anecdote de la caméra cachée de Linlin | Évoquée (concept, lieu, audience), détails non décrits | Le canular met en scène de faux délits : ne pas associer l'artiste à des faits imaginaires |

## 4. Décisions éditoriales structurantes

1. **Transparence** : carton « personnages animés fictifs » à 0:32, rappelé dans le générique et la description.
2. **Fiabilité visible** : ligne SOURCE sur chaque habillage, fact-check « confirmé / déclaré », biographie toujours attribuée (« selon sa bio »).
3. **Prudence sur les relations** : le graphe des featurings montre des projets, pas des liens personnels (dit à l'antenne).
4. **Aucune image d'arme**, aucun visuel officiel sans autorisation.

## 5. Prochaines actions recommandées (par priorité)

1. **Faire valider le script par Lyphik ou son entourage** : faits, prononciations (1K 5K, Kyenn Cho, Tout x3…), accord pour les extraits.
2. Obtenir les autorisations EX-01 à EX-05, puis produire la version 1.2 avec les extraits.
3. Remplacer les voix de synthèse par deux comédiens voix guyanais ou antillais (qualité, authenticité, sécurité juridique).
4. Vérifier la disponibilité des identifiants `@973culture`.
5. Faire un repérage photo de la Place des Palmistes pour fiabiliser le décor des prochains épisodes.
