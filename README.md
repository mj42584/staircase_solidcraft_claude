# Escalier gab

Escalier droit à demi-tour avec palier intermédiaire, modélisé de façon paramétrique dans **SolidCraft**.

- Hauteur totale 3800 mm, 22 contremarches de 172,73 mm, giron 274 mm (angle 32,23°, Blondel 619)
- Deux volées de 1000 mm séparées par un jour de 60 mm, palier de 1000 mm
- Marches de 30 mm sur deux équerres 30×30×3

## Contenu

| Chemin | Contenu |
|---|---|
| `cad/escalier.solidcraft` | Modèle maître : squelette + marches, tout piloté par paramètres |
| `archive/freecad/` | Modèle FreeCAD d'origine |
| `archive/` | Anciennes versions SolidCraft (import du FreeCAD, ensemble marche autonome) |
| `calc/predim.py` | Prédimensionnement (ordres de grandeur) : `python3 calc/predim.py` |
| `calc/portique.py` | Modèle en barres PyNite (stabilité, torsion, efforts aux appuis) : `pip install PyNiteFEA` puis `python3 calc/portique.py` |
| `calc/visu.py` | Visualisation 3D PyVista (moments ELU, déformée ELS) : `pip install pyvista` puis `python3 calc/visu.py`, ou `--png DOSSIER` pour des images |
| `calc/rapport/` | Rapport de calcul (synthèse des trois scripts, figures) |
| `CONCEPTION.md` | Paramètres, architecture du modèle, décisions et historique de conception |

## Utilisation

Ouvrir `cad/escalier.solidcraft` dans SolidCraft et modifier les paramètres pilotes (`hauteur_totale`, `nb_contremarches`, `nb_volee1`, `giron`, `emmarchement`, `jour`, `palier_profondeur`…). Le squelette, les marches et leur nombre se recalculent. Le détail est dans [CONCEPTION.md](CONCEPTION.md).
