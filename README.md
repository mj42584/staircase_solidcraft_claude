# Projet Escalier avec SolidCraft et Claude

Escalier à demi-tour en acier et chêne, modélisé de façon paramétrique dans **SolidCraft** et vérifié par un calcul de structure en Python.

*Parametric half-turn steel and oak staircase, modelled in SolidCraft, with a Python structural check (PyNite, Eurocodes).*

[![Vue de l'escalier dans son environnement](cad/apercu.png)](cad/projet_escalier.stl)

**[Voir en 3D →](cad/projet_escalier.stl)** (vue interactive GitHub, à faire tourner à la souris) : l'escalier en place sur le site, avec la dalle, le mur et la mezzanine d'arrivée.

## L'escalier

| | |
|---|---|
| Hauteur à monter | 3 848 mm (mesurée sur site), 22 contremarches de 174,91 mm |
| Giron, angle, Blondel | 274 mm, 32,55°, 624 mm |
| Volées | 16 + 6 contremarches, emmarchement 1 000 mm, jour 270 mm |
| Palier | 1 000 mm sur 4 pieds en tube 100×100×5 |
| Ossature | limons et cadre du palier en UPE 220, platines boulonnées M12 |
| Marches et plancher | chêne de 60 mm sur cornières 30×30×3 |
| Arrivée | mezzanine existante en IPE 200, dessus à 3 788 mm + plancher de 60 mm |

## Calcul de structure

Résultat principal du [rapport de calcul](calc/rapport/RAPPORT.md) : l'acier est largement dimensionné (taux ≤ 12 %), mais **les marches en chêne doivent faire au moins 38 mm**. Ce calcul a été fait sur l'ancienne version (3 800 mm, 17 + 5, marches de 30 mm) ; le modèle est passé depuis à 3 848 mm, 16 + 6 et des marches de 60 mm, sans que le calcul soit relancé. Ce sont des ordres de grandeur : ils ne remplacent pas une note de calcul validée par un bureau d'études.

| Script | Rôle | Lancer |
|---|---|---|
| [`calc/predim.py`](calc/predim.py) | Prédimensionnement manuel | `python3 calc/predim.py` |
| [`calc/portique.py`](calc/portique.py) | Modèle en barres PyNite : stabilité, torsion, efforts aux appuis | `pip install PyNiteFEA` puis `python3 calc/portique.py` |
| [`calc/visu.py`](calc/visu.py) | Vue 3D PyVista des moments et de la déformée | `pip install pyvista` puis `python3 calc/visu.py` (ou `--png DOSSIER`) |

## Modifier l'escalier

Ouvrir [`cad/escalier.solidcraft`](cad/escalier.solidcraft) dans SolidCraft et changer les paramètres pilotes (`hauteur_totale`, `nb_contremarches`, `nb_volee1`, `giron`, `emmarchement`, `jeu_limons`, `palier_profondeur`…) : le squelette, les marches et leur nombre se recalculent. Ouvrir ensuite [`cad/projet_escalier.solidcraft`](cad/projet_escalier.solidcraft), faire « Update Links » et recaler l'escalier contre la mezzanine si la répartition a changé (le placement n'est pas encore automatique). L'architecture du modèle et toutes les décisions de conception sont dans [CONCEPTION.md](CONCEPTION.md).

## Contenu

| Chemin | Contenu |
|---|---|
| `cad/escalier.solidcraft` | Modèle maître paramétrique de l'escalier |
| `cad/environnement.solidcraft` | Site : dalle, mur, mezzanine d'arrivée en IPE 200 |
| `cad/projet_escalier.solidcraft` | Assemblage : environnement + escalier (composants liés) |
| [`cad/projet_escalier.stl`](cad/projet_escalier.stl) | Export STL du projet, escalier dans son environnement (vue 3D) |
| [`cad/escalier.stl`](cad/escalier.stl) | Export STL de l'escalier seul, version actuelle (16 + 6, 3 848 mm), à sa place sur le site (vue 3D) |
| `calc/` | Scripts de calcul et [rapport](calc/rapport/RAPPORT.md) |
| `archive/` | Modèle FreeCAD d'origine et anciennes versions SolidCraft |
| `CONCEPTION.md` | Paramètres, décisions et historique de conception |

Conçu avec l'aide de [Claude Code](https://claude.com/claude-code).
