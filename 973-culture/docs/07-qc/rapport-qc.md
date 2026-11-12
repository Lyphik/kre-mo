# Rapport de contrôle qualité — Épisode 01

> Version 1.1 · 12/11/2026 · Contrôles techniques automatisés : `production/src/qc.py` → `production/build/qc_report.json`
> Méthode : chaque étape a été vérifiée avant la suivante (images de contrôle, planches contact, mesures objectives). L'équipe ne peut pas **écouter** les fichiers : l'audio a été contrôlé par la mesure (niveaux, loudness, silences), pas à l'oreille. **Une écoute humaine reste indispensable avant publication.**

## 1. Contrôles techniques

Mesures sur les fichiers livrés (`production/src/qc.py`), après corrections :

| Fichier | Durée | Format | Taille | Loudness | True peak | Plans figés > 2,5 s | Images noires | SRT (ligne max / chevauchements) |
|---|---|---|---|---|---|---|---|---|
| Master `…_master_1080p25.mp4` | 7:41,5 | H.264 1920×1080 25 i/s · AAC 48 kHz stéréo | 95,9 Mo | −14,4 LUFS | −1,0 dBTP | 0 | 0 | 42 car. / 0 (159 sous-titres, durée max 5,4 s) |
| Bande-annonce 16:9 | 0:54,6 | 1920×1080 | 12,1 Mo | −14,7 LUFS | −0,9 dBTP | 0 | 0 | 41 / 0 |
| Short 1 « Lyphik en 55 s » | 0:54,6 | 1080×1920 | 9,3 Mo | −14,3 LUFS | −1,1 dBTP | 0 | 0 | 41 / 0 |
| Short 2 « Le paradoxe » | 0:24,3 | 1080×1920 | 3,7 Mo | −14,1 LUFS | −1,6 dBTP | 0 | 0 | 42 / 0 |
| Short 3 « P.M.L » | 0:26,1 | 1080×1920 | 4,9 Mo | −14,8 LUFS | −1,0 dBTP | 0 | 0 | 41 / 0 |
| Short 4 « Le débat » | 0:27,4 | 1080×1920 | 5,8 Mo | −14,4 LUFS | −1,7 dBTP | 0 | 0 | 40 / 0 |
| Short 5 « Bad Life » | 0:39,2 | 1080×1920 | 7,5 Mo | −14,6 LUFS | −1,8 dBTP | 0 | 0 | 39 / 0 |

Historique des corrections techniques :
- **v1.0 → v1.1** : 34 plans figés supprimés (mouvement continu des habillages) ; silence d'ouverture de 2 s comblé par l'ambiance ; true peak du master ramené de +0,1 à −1,0 dBTP (limiteur) ; SRT des Shorts recoupés à 42 caractères ; master réencodé en 2 passes (113 Mo → 95,9 Mo) pour respecter la limite de 100 Mo par fichier de GitHub.
- Le master a été réencodé à partir d'un rendu intermédiaire (CRF 20) : une génération de compression en plus, sans perte visible sur les planches de contrôle.

## 2. Contrôles éditoriaux (fiabilité)

| Contrôle | Résultat |
|---|---|
| Chaque affirmation factuelle du script renvoie au dossier (`dossier-lyphik.md`) | ✅ 67 répliques relues ; affirmations classées ci-dessous |
| Biographie systématiquement attribuée (« selon sa bio », « d'après sa biographie officielle ») | ✅ S2-01, S2-02, S2-03, S2-07, S2-11, S3-10, S5-09 |
| Chiffres affichés = relevé du 12/11/2026, sources à l'écran | ✅ 595 204 · ≈384 k · 52 771 · ≈167 k · 63 152 · 388 · ≈1,6 M |
| Aucune relation personnelle supposée entre artistes | ✅ Dit à l'antenne (S4-08) et à l'écran (graphe) |
| Aucun faux témoignage, aucune fausse interview, aucune parole prêtée à Lyphik | ✅ Les présentateurs sont fictifs (carton à 0:32, générique, description) |
| Observations visuelles limitées à ce qui a été vu | ✅ **Correction v1.1** : 4 répliques qui décrivaient « l'image » des clips ont été réécrites pour parler de la **miniature** (seul élément réellement consulté) |
| Formulations trop affirmatives | ✅ **Correction v1.1** : « sa vidéo la plus vue » → « la plus vue des vidéos recensées » ; « il ne raconte pas sa vie » → « on a trouvé très peu d'infos publiques » |
| Caméra cachée : pas d'association de l'artiste à de faux délits | ✅ Seuls le concept, le lieu et l'audience sont évoqués |
| Images d'armes | ✅ Aucune |
| Contenus tiers sans autorisation | ✅ Aucun (pochettes et presse recréées typographiquement) |

### Points éditoriaux à valider par un humain

| Réplique | Point | Niveau de risque |
|---|---|---|
| S2-04 | « P.M.L, pour Pa Mélé… le nom de sa **première** mixtape » — #PML est le premier projet cité par la bio et la presse de 2017, mais « première » reste une déduction | Faible |
| S3-02 | « son titre le plus écouté » — vrai parmi les titres populaires affichés par Spotify (52 771 écoutes) ; le décompte de chaque titre n'a pas été relevé | Faible |
| S1-04 / S7-01 | « plus de dix ans de musique » — débuts en 2015 (déclaratif) et clip « La zone » vers 2016 (confirmé) | Faible |
| S6-02 | Jahsik : présence sur Yana et Eveil confirmée (Spotify) | — |
| Lexique | Prononciations hypothétiques : « 1K 5K », « Tout x3 », « Kyenn Cho », « Allnice », « Three7 », « Lyphik », « Jahsik » | **À valider avec l'artiste** |

## 3. Contrôles visuels (planches contact)

| Contrôle | Résultat |
|---|---|
| Cohérence des personnages d'un plan à l'autre | ✅ Modèle paramétrique unique : aucune variation de visage, de coiffure ou de tenue |
| Cadrage des gros plans (l'enseigne néon dépassait du haut de l'image) | ✅ Corrigé (caméra recentrée) |
| Graphe des featurings illisible (croisements) | ✅ Corrigé (disposition en étoile) |
| Traits parasites (bug de chemin Cairo après un texte) | ✅ Corrigé à la source (`draw.text`) |
| Chevauchement médaillon / texte (fact-check, encart Kourou) | ✅ Corrigé |
| Plans figés > 2,5 s sur les habillages (34 détections en v1.0) | ✅ Corrigé : 0 détection sur tous les fichiers |
| Banding (paliers) dans les dégradés sombres | ⚠️ **Atténué, pas supprimé** (`aq-mode=3`). Le grain anti-banding est disponible (`GRAIN=True`) mais multiplie la taille par 2,5 ; à activer pour l'envoi à YouTube si l'on accepte un fichier d'environ 150 Mo |

## 4. Contrôles audio

| Contrôle | Résultat |
|---|---|
| Loudness intégrée (cible YouTube −14 LUFS) | ✅ Entre −14,8 et −14,1 LUFS selon les fichiers ; true peak ≤ −0,9 dBTP |
| Homogénéité des voix (niveau RMS par réplique) | ✅ Écart-type 0,45 dB (−17,2 à −15,3 dBFS avant traitement) |
| Rapport voix / musique pendant les dialogues | ✅ Lit musical à environ −16 à −19 dB sous la voix (atténuation automatique) |
| Silence en ouverture (2,1 s en v1.0) | ✅ Corrigé : ambiance extérieure (feuillage, grillons qui s'intensifient avec la nuit) |
| Placement stéréo cohérent avec l'image | ✅ Kenzo à −18 %, Maëva à +18 % |
| Naturel des voix | ⚠️ **Limite connue** : synthèse neuronale de qualité moyenne, intonations parfois plates, pas de rires audio. Recommandation : comédiens voix |
| Prononciations créoles et noms propres | ⚠️ Lexique phonétique appliqué ; écoute humaine nécessaire (« tout moun », « Mèsi », noms d'artistes) |

## 5. Défauts connus et acceptés pour la v1.1

1. Style illustré 2D (et non photoréaliste) — limite d'outillage, documentée.
2. Synchronisation labiale approchée (minutage exact, forme des lèvres estimée).
3. Voix de synthèse ; licence de la voix de Kenzo à régler avant monétisation.
4. Pas d'extraits de clips (autorisations à obtenir : EX-01 à EX-05).
5. Décor stylisé, non vérifié par un repérage sur place.

## 6. Verdict

**Publiable en l'état sur une chaîne non monétisée**, sous réserve de trois actions humaines : une **écoute complète**, la **validation des prononciations** et, idéalement, la **relecture du script par l'artiste**. Pour une chaîne monétisée, remplacer d'abord la voix de Kenzo (voir `../04-droits/autorisations.md`).
