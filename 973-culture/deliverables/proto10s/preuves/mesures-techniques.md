# Preuves techniques — Prototype 3D de 10 s

> Mesures réalisées le 24/11/2026 sur les fichiers livrés (ffprobe, filtres FFmpeg `ebur128`, `freezedetect` et `blackdetect`).

## Fichiers

| Fichier | Vidéo | Images | Durée | Taille | Loudness | True peak | Plans figés > 1,5 s | Images noires |
|---|---|---|---|---|---|---|---|---|
| `973culture_proto10s_3d_16x9_720p.mp4` | H.264 1280×720, 25 i/s | 250 | 10,00 s | 5,9 Mo | −15,0 LUFS | −1,1 dBTP | 0 | 0 |
| `973culture_proto10s_3d_vertical_720x1280.mp4` | H.264 720×1280, 25 i/s, sous-titres incrustés | 250 | 10,00 s | 6,2 Mo | −15,0 LUFS | −1,1 dBTP | 0 | 0 |

Son : AAC 192 kb/s, stéréo 48 kHz (voix légèrement placées dans l'espace : Kenzo à gauche, Maëva à droite). Sur un extrait de 10 s, la mesure de loudness intégrée est moins stable : l'écart de −1 LU par rapport à la cible YouTube (−14) est accepté.

## Chaîne de fabrication

| Étape | Outil | Détail |
|---|---|---|
| Personnages | Blender 4.2.23 LTS + MPFB 2.0.18 (empreinte SHA-256 vérifiée) | Corps MakeHuman, peau à diffusion sous la surface, squelette « default » (163 os), 22 + 15 visèmes et 52 unités faciales ARKit en shape keys |
| Poses | Poses 01 (CC0), BVH | `callharvey3d_sittingnatural` (Kenzo), `callharvey3d_sittinglegscrossed` (Maëva) |
| Décor | Script Python Blender (`build_scene.py`) | 493 objets : gradins, palmiers procéduraux (folioles pennées), façades, guirlande émissive, enseigne néon, ciel physique Nishita |
| Animation | Script, 250 images clés | Bouche (enveloppe audio + visèmes), clignements, sourcils, sourires, regards (os des yeux), tête et cou (axes **mesurés** sur le squelette), colonne, gestes |
| Caméras | 4 caméras physiques | 35 / 70 / 70 / 30 mm, ouvertures de f/1,8 à f/2,4, mise au point sur les yeux, poussées lentes |
| Rendu | Cycles CPU (4 cœurs, sans GPU), 20 échantillons adaptatifs + OIDN, AgX | ≈ 37 s par image en 16:9, ≈ 33 s en vertical ; ≈ 2 h 30 par version |
| Compositing | Brume (passe mist), fog glow, légère dispersion | — |
| Montage | FFmpeg, libx264 CRF 16, `aq-mode=3` | Sous-titres ASS (libass) pour le vertical |

## Itérations de contrôle qualité (avant le rendu final)

| # | Défaut détecté sur image de contrôle | Cause | Correction |
|---|---|---|---|
| 1 | Visages devenus des masques sombres décalés, membres détachés | Accessoires (cheveux, yeux, vêtements) ajoutés **avant** le squelette, donc non liés ; pose perdue lors de la conversion Euler → quaternion | Squelette créé avant les accessoires ; conversion de rotation sans perte. **Ce rendu défectueux a été supprimé, jamais livré** |
| 2 | Dominante rose saumon, bois lisse | Ciel trop bas, brume orange, texture de bois à mauvaise échelle | Étalonnage neutralisé, bois de teck avec veinage et joints |
| 3 | Troncs en « barreaux », guirlande hors cadre | Rangée de palmiers trop proche | Palmiers moyens au second plan, guirlande abaissée (bokeh) |
| 4 | Têtes qui penchent au lieu de tourner, Maëva regardant du mauvais côté | Axes d'os supposés au lieu d'être mesurés | Axes **mesurés numériquement** (sonde de rotation) puis appliqués |
| 5 | Coiffure de Kenzo en « casque » | Cartes de cheveux de `afro01` visibles | Remplacée par `short01` |
| 6 | Teint de Maëva pâle, lèvres grises | Mauvais paramètre de mélange de couleur ; matière des lèvres claire | Texture de peau plus foncée, lèvres issues de la texture de peau. *Résultat final plus foncé que le « caramel » visé : écart signalé* |
| 7 | Plans verticaux coupant un personnage, sol vide | Duo trop large pour le 9:16 | Caméras de 3/4 : duo étagé en profondeur, palmiers et ciel en haut |
| 8 | Étiquette « KENZO » peu lisible | Vert trop foncé | Vert éclairci |
