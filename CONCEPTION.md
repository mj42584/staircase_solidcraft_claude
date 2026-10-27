# Conception — Escalier gab

Ce fichier décrit l'**état actuel** du projet et **le pourquoi des choix**. Il est mis à jour à chaque fin de tâche (sections 1 à 8) et complété d'une ligne dans l'historique (section 9). Un agent qui reprend le projet doit le lire en entier avant toute action.

## 1. Objectif

Escalier droit **à demi-tour**, deux volées séparées par un **palier intermédiaire sans différence de niveau**. Tout doit être **pilotable par des paramètres** : hauteur, giron, répartition des contremarches entre volées, profondeur du palier, largeur du jour.

## 2. Données d'entrée

| Donnée | Valeur |
|---|---|
| Hauteur totale (sol fini bas → sol fini haut) | 3800 mm |
| Giron | 274 mm |
| Hauteur de marche | 172,73 mm (= 3800 / 22) |
| Angle de volée annoncé au départ | 32,4° — voir décision D1 |
| Répartition | 17 / 5 au départ, puis 16 / 6 (14 / 8 et 15 / 7 essayés un temps), **17 / 5** actuellement (choix de l'utilisateur dans l'app) — voir D2 ; volée 2 décalée d'un giron, voir D6 |
| Profondeur du palier | 1000 mm |
| Jour (vide entre volées) | 60 mm au départ, désormais calculé (270 mm avec `jeu_limons` = 100) — voir D9 |
| Emmarchement (largeur d'une volée) | 1000 mm |
| Marche | plaque 30 mm, deux équerres (cornières 30×30×3, L 200) symétriques |
| Limons | UPE 220 (h 220, b 85, âme 6,5, ailes 12, congé r 13, 26,6 kg/m, A 33,9 cm² — **vérifié catalogue** EN 10365, 2026-10-26) — voir D8 |
| Environnement | **aucun mur** : le palier repose sur des pieds — voir D11 |
| Plancher du palier | même matériau que les marches (30 mm) |
| Matériaux | marches et plancher en **chêne** (« Oak », 0,75 g/cm³) ; tout le reste en **acier** (« Steel », 7,85 g/cm³) — voir D13 |

## 3. Paramètres du modèle (`cad/escalier.solidcraft`)

**Pilotes**

| Paramètre | Valeur | Pilote |
|---|---|---|
| `hauteur_totale` | 3800 mm | hauteur de marche, arrivée |
| `nb_contremarches` | 22 | hauteur de marche, nb_volee2 |
| `nb_volee1` | 17 | contremarches volée basse → hauteur du palier, nombre de marches V1 |
| `giron` | 274 mm | squelette, profondeur des marches, pas des réseaux |
| `emmarchement` | 1000 mm | largeur des volées et des marches, plans d'axe |
| `jeu_limons` | 100 mm | vide entre les deux limons intérieurs → `jour` (passé de 20 à 100 par l'utilisateur) |
| `palier_profondeur` | 1000 mm | squelette (élévation et plan) |
| `marche_epaisseur` | 30 mm | marches, position des équerres |
| `equerre_aile` | 30 mm | cornières (ailes égales) |
| `equerre_ep` | 3 mm | cornières |
| `equerre_longueur` | 200 mm | cornières, centrées sur le giron |
| `debord` | 0 mm | débord du nez de marche vers l'avant |
| `limon_h` | 220 mm | hauteur UPE |
| `limon_b` | 85 mm | largeur des ailes UPE, pilote `jour` |
| `limon_tw` | 6,5 mm | épaisseur d'âme |
| `limon_tf` | 12 mm | épaisseur d'aile |
| `limon_dessus` | 0 mm | haut du limon au-dessus de la ligne de nez, perpendiculairement (0 = au ras des nez) |
| `palier_ep` | `marche_epaisseur` (30 mm) | plancher du palier |
| `platine_ep` | 15 mm | platines d'about : bas des limons V1 et V2 (côté palier) et haut des limons V2 (arrivée) ; les limons sont raccourcis d'autant |
| `boulon_d` | 12 mm | boulons des platines (M12) |
| `trou_jeu` | 2 mm | jeu des trous : largeur des oblongs = `boulon_d + trou_jeu` (14 mm) |
| `oblong_course` | 10 mm | course verticale des oblongs (entre centres d'arcs ; longueur totale 24 mm) |
| `boulons_entraxe` | 100 mm | entraxe vertical des 2 trous de chaque platine |
| `poteau_cote` | 100 mm | pieds : tube carré |
| `poteau_ep` | 5 mm | pieds : épaisseur du tube |

**Calculés**

| Paramètre | Expression | Valeur |
|---|---|---|
| `hauteur_marche` | `hauteur_totale / nb_contremarches` | 172,73 mm |
| `nb_volee2` | `nb_contremarches - nb_volee1` | 6 |
| `angle_volee` | `atan(hauteur_marche / giron)` | 32,23° |
| `blondel` | `2 * hauteur_marche + giron` | 619 mm (confort 600–640) |
| `pas_volee` | `sqrt(giron ^ 2 + hauteur_marche ^ 2)` | 323,90 mm |
| `jour` | `2 * limon_b + jeu_limons` | 270 mm |

## 4. Architecture du modèle

**Repère** : origine au pied de la première contremarche, **au milieu du jour**. Volée 1 monte vers **+X** côté **Y négatif** ; volée 2 redescend en X (monte vers −X) côté **Y positif**. Z vers le haut. Ce repère **diffère** de celui du FreeCAD d'origine (voir points ouverts).

**Timeline**

1. `Squelette élévation` (plan XZ, Z vers le haut, 0 DDL) — première contremarche, ligne des nez volée 1, palier horizontal à `nb_volee1 × h`, prolongé côté volée 2 d'un giron (ligne `l6`, au niveau du palier, vers −X), première contremarche volée 2 à `rive − giron`, ligne des nez volée 2 jusqu'à `hauteur_totale`.
2. `Squelette plan` (XY, 0 DDL) — emprise volée 1, palier pleine largeur (`2 × emmarchement + jour`), emprise volée 2.
3. `Axe volée 1` / `Axe volée 2` — plans de construction décalés de XZ de ∓(`jour/2 + emmarchement/2`).
4. `Foulée volée 1` / `Foulée volée 2` — ligne de nez projetée depuis le squelette d'élévation sur chaque plan d'axe.
5. `Profil marche V1` → `Marche V1` — rectangle accroché au premier nez projeté, extrudé symétrique sur `emmarchement`.
6. `Profil équerre V1` → `Équerre V1` (côté mur, « ext ») → `Symétrie équerre V1` (côté jour, « int ») par rapport à `Axe volée 1`.
7. `Réseau marches V1` — réseau sur chemin le long de `Foulée volée 1` : `nb_volee1 - 1` occurrences, pas `pas_volee`.
8. Idem volée 2 : `Profil marche V2`, `Marche V2`, `Équerre V2`, `Symétrie équerre V2`, `Réseau marches V2` (`nb_volee2` occurrences, marche orientée vers −X). `Profil marche V2` est accroché au nez du palier (`l2.end` du squelette) : la première marche V2 est **au niveau du palier**, entre `rive − giron` et la rive ; `Équerre V2` à `nb_volee1 * hauteur_marche - marche_epaisseur`. En plan, l'emprise V2 vaut `nb_volee2 * giron`.
9. `Rive ext V1` — plan décalé de `Axe volée 1` de `-emmarchement / 2` (bout des marches côté mur).
10. `Profil limon V1` → `Âme limon V1` (extrusion `limon_tw`, corps `Limon ext V1`), `Profil ailes limon V1` → `Ailes limon V1` (deux bandes de `limon_tf`, extrusion `limon_b`, jointes). Ailes tournées vers l'extérieur, âme contre le bout des marches.
11. `Symétrie limon V1` — symétrie du **corps** `Limon ext V1` par `Axe volée 1` → `Limon int V1`.
12. Idem volée 2 : `Rive ext V2` (décalage `+emmarchement / 2` de `Axe volée 2`), `Profil limon V2`, `Âme limon V2`, `Profil ailes limon V2`, `Ailes limon V2`, `Symétrie limon V2` → `Limon ext V2`, `Limon int V2`.

13. `Dessus cadre palier` — plan XY décalé de `nb_volee1 * hauteur_marche - palier_ep` (dessus du cadre = dessous du plancher).
14. `Plancher palier` — rectangle X `(nb_volee1 - 1) * giron` → `+ palier_profondeur`, Y ±(`jour/2 + emmarchement + limon_b`), extrudé de `palier_ep` vers le haut : il couvre tout le cadre, limons extérieurs compris.
15. `Pieds palier` — 4 tubes `poteau_cote` × `poteau_ep` aux coins du cadre, du sol au dessous des poutres : `Pied avant V1`, `Pied avant V2`, `Pied arrière V1`, `Pied arrière V2`.
16. Cadre en **onglet à 45°** : pour chaque poutre, une esquisse `Âme poutre …` (trapèze d'épaisseur `limon_tw`, extrudé de `limon_h` vers le bas, nouveau corps) et une esquisse `Ailes poutre …` (trapèze de largeur `limon_b`, extrudé deux fois de `limon_tf` : aile haute, et aile basse avec `start_offset`, jointes au corps). Les 4 UPE ont l'**âme à l'extérieur et les ailes vers l'intérieur**, pleine longueur jusqu'aux angles extérieurs, coupées à 45° : `Poutre avant palier`, `Poutre arrière palier`, `Poutre latérale V1`, `Poutre latérale V2`. Une esquisse et un corps par poutre, pour que les onglets jointifs ne fusionnent pas les corps.

**Limons** : les profils sont des polygones dont chaque sommet est une **expression** (pas de cotes) : bord haut = ligne de nez + `limon_dessus`, bord bas = ligne de nez − (`limon_h` − `limon_dessus`), décalages verticaux = décalage perpendiculaire × `pas_volee / giron`. Extrémités provisoires : V1 coupé horizontalement au sol et verticalement au premier nez (X = 0). En haut de V2 (arrivée), même détail que V1 côté palier : limon coupé verticalement à `(nb_volee1 - nb_volee2 - 1) * giron + platine_ep`, platine `Profil platine V2` → `Platine limon V2` en corps séparé (`Platine ext V2`), contre le plan vertical du dernier nez. `Symétrie limon V2` symétrise `Limon ext V2` et `Platine ext V2` → `Limon int V2` et `Platine int V2`. Rien n'est encore modélisé derrière (plancher ou chevêtre d'arrivée). Côté palier : les **limons V1** sont coupés verticalement à `rive − platine_ep`, et une **platine d'about** (`Profil platine V1` → `Platine limon V1`, `platine_ep` × `limon_b` × hauteur du bout de limon) est un **corps séparé** (`Platine ext V1`), distinct du limon, à la demande de l'utilisateur. Cette fonction est insérée **avant** `Symétrie limon V1`, qui symétrise les deux corps (`Limon ext V1` et `Platine ext V1`) → `Limon int V1` et `Platine int V1`. La platine arrive contre l'âme de la poutre avant ; l'assemblage platine / poutre n'est pas modélisé. Les **limons V2**, côté palier, ont le même détail que V1 : coupés verticalement à `rive − platine_ep`, avec une platine d'about en corps séparé (`Profil platine palier V2` → `Platine palier limon V2` → `Platine palier ext V2`, sketch sur `Rive ext V2`, extrusion `limon_b`), insérée avant `Symétrie limon V2`, qui produit `Platine palier int V2`. Comme la volée 2 est décalée d'un giron (D6), la ligne de nez passe au niveau du palier à la rive ; la platine (2513,0 → 2773,1) couvre la poutre avant (2513,6 → 2733,6) et dépasse de 9,5 mm le dessus du plancher, puisque la ligne de nez remonte sur 15 mm de recul. Formules des sommets (Z, à écrire en négatif) : rive = `nb_volee1 * hauteur_marche + platine_ep * hauteur_marche / giron` ± décalages, haut = `hauteur_totale - platine_ep * hauteur_marche / giron` ± décalages. **Perçage des 6 platines** (identiques en taille, 15 × `limon_b` × `limon_h * pas_volee / giron`, et en perçage) : 2 trous oblongs verticaux centrés sur la platine, à ± `boulons_entraxe / 2` du milieu. `Perçage platine V1` (plan YZ) → `Trous platine V1` (découpe de `Platine ext V1`, insérée avant `Symétrie limon V1`) ; `Perçage platines V2` (plan YZ, 4 oblongs) → `Trous platines V2` (découpe ciblée sur `Platine ext V2` et `Platine palier ext V2`, de `(nb_volee1 - nb_volee2 - 1) * giron` sur `nb_volee2 * giron`, insérée avant `Symétrie limon V2`). Les oblongs sont des rainures cotées en expressions (centres par rapport à l'origine, rayon, course, entraxe), la commande d'oblong n'acceptant pas d'expressions. Côté palier, les trous tombent entre les ailes de la poutre avant (V1 : 2574 / 2674 ; V2 : 2593 / 2693). **Perçage de la poutre avant** : `Perçage poutre avant` (plan YZ, 8 cercles cotés en expressions) → `Trous poutre avant` (découpe de `Poutre avant palier` sur `limon_tw` depuis la rive) : trous **ronds** Ø `boulon_d + trou_jeu` (14 mm) dans l'âme, en face du **milieu** des oblongs des 4 platines côté palier ; le réglage se fait par les oblongs. Limite : côté V2 les trous sont 19,5 mm au-dessus du milieu de la poutre, il faut `boulons_entraxe / 2 + (boulon_d + trou_jeu) / 2` < ≈ 78 mm pour ne pas mordre l'aile haute (OK à 100 / M12 ; entraxe 140 + M16 mord de 0,4 mm). Ni visserie, ni cornière d'appui, ni arasage pour l'instant (choix de l'utilisateur). Les congés de laminage de l'UPE (r = 13 mm) sont ignorés : section modélisée 33,1 cm² contre 33,9 au catalogue, masse des UPE sous-estimée de 2,2 % (26,0 au lieu de 26,6 kg/m). Les esquisses de rive V2 ont l'axe Y vers −Z : les Z y sont écrits en négatif.

**Point d'intégration de la marche** : nez de marche, face supérieure, milieu de la largeur — c'est le point par lequel passent les lignes de nez du squelette.

Nombre de marches : chaque volée a une marche de moins que de contremarches (la dernière contremarche arrive sur le palier ou l'arrivée). Exception : la volée 2 a une marche de plus, au niveau du palier (D6). Avec 16/6 : 15 + 6 = 21 marches (palier à 2763,6 mm, rive à X = 4110, première contremarche V2 à X = 3836, arrivée à X = 2466).

## 5. Journal des décisions

- **D1 — Angle calculé, non piloté.** 32,4° est incohérent avec giron 274 et hauteur 172,73 (arctan → 32,23°). On pilote hauteur totale + nombre de contremarches + giron ; l'angle en découle.
- **D2 — Répartition pilotable.** Départ 17/5 (palier à 2936 mm, comme le FreeCAD). L'utilisateur est ensuite passé à **16/6** dans l'app, puis à **14/8** un temps, puis de nouveau à **16/6** ; 16/6 est la valeur actuelle. Le modèle suit ces changements sans erreur.
- **D3 — Ensemble marche intégré au squelette, pas en fichier lié.** SolidCraft permet un composant lié (`component.insert_design`), mais les paramètres ne traversent pas les fichiers et le réseau sur chemin n'accepte pas les composants. Intégré, la marche est pilotée directement par `giron` et `emmarchement`.
- **D4 — Réseau sur chemin plutôt que rectangulaire.** Le chemin est une courbe du squelette : la direction suit l'angle de volée. Le nombre d'occurrences accepte une expression (vérifié).
- **D5 — Débord sans cote nulle.** SolidCraft refuse une cote de 0. L'arrière de la marche est coté depuis le nez (`giron`) et la longueur totale vaut `giron + debord`.
- **D6 — Volée 2 décalée d'un giron.** Au départ, volée 2 à l'aplomb du nez du palier (disposition classique). Changé à la demande de l'utilisateur (2026-10-26) : la première marche de V2 est au niveau du palier et la première contremarche V2 recule d'un giron (`rive − giron`). Cela règle la jonction limon V2 / palier (D12). L'escalier s'allonge d'un giron ; c'est proche de la disposition du FreeCAD d'origine.
- **D7 — Pas de Git LFS ni d'exports** : GitHub sert de sauvegarde uniquement, les fichiers sont petits.
- **D8 — Limons UPE 220, ailes vers l'extérieur.** Comparé : fer plat 300×10 (≈ L/300), UPE 160 (≈ L/120 sur 4,1 m, trop souple, et l'équerre L 200 ne rentre pas entre les ailes), UPE 200 (≈ L/255), UPE 220 (≈ L/345). Avec `limon_dessus = 0`, la zone boulonnable de l'âme (≈ 170 mm) couvre l'équerre (≈ 45 → 177 mm sous la ligne de nez). Ordres de grandeur seulement, pas un calcul de structure.
- **D9 — Jour calculé depuis les limons.** Les ailes des deux limons intérieurs se font face dans le jour : `jour = 2 * limon_b + jeu_limons`. Le jeu est libre pour l'instant (20 mm).
- **D10 — Symétrie de corps, pas de fonctions.** Une symétrie des fonctions « âme + ailes » joignait les ailes copiées au limon d'origine (l'extrusion des ailes est une jonction ciblée) : on symétrise le corps entier.
- **D11 — Palier : cadre UPE + plancher dessus + 4 pieds.** Pas de mur autour. Cadre de 4 UPE (même profil que les limons, piloté par `limon_*`), âmes à l'extérieur, ailes vers l'intérieur, angles coupés à 45° et soudés (demande de l'utilisateur : poutres latérales retournées de 180° par rapport à la première version), dessus à `16 h − palier_ep`, plancher de 30 mm posé dessus. La poutre avant reçoit les 4 limons ; le limon V1 couvre toute sa hauteur (bas du limon à 2503,5 contre 2513,6 pour la poutre). Pieds en tube 100×100×5 aux 4 coins.

- **D12 — Jonction limon V2 / palier par décalage de la volée.** But de l'utilisateur : supprimer la face verticale du limon V2 qui dépassait au-dessus du palier. Une première version (limon prolongé et posé sur le plancher) a été écartée : on a plutôt ajouté une contremarche à la volée 1 (15/7 → 16/6) et mis la première marche V2 au niveau du palier (D6). Toutes les contremarches restent égales. Le limon V2 arrive à la rive au ras du palier et couvre toute la hauteur de la poutre avant.

- **D13 — Matériaux.** Chêne pour les 21 marches (17/5) et le plancher du palier, acier pour limons, platines, équerres, cadre et pieds. Masse totale ≈ 893 kg (acier 708, chêne 184) en 17/5. L'affectation se fait par nom de corps (`material.assign`) ; elle tient au recalcul et quand un corps de réseau disparaît puis revient (test 17 → 16 → 17), mais une marche créée au-delà du nombre affecté resterait « Default ».

- **D14 — Prédimensionnement par script Python** (`calc/predim.py`, bibliothèque standard seule). Il reprend à la main les paramètres du §3 et vérifie, en ordres de grandeur : marches (flexion et flèche, D30), limons V1 / V2, poutre avant (4 réactions de limons + demi-palier), flambement des pieds (libres en tête, L_cr = 2 H), cisaillement des boulons M12. Hypothèses : q = 2,5 kN/m², Q = 2 kN (AN française, cat. A), chêne D30, acier **S235 supposé**, boulons 8.8 supposés, flèche L/300. Résultats en 17/5 : **marches de 30 mm insuffisantes** (contrainte 100 %, flèche 6,3 mm pour 3,3 admis, **38 mm minimum**) ; limons, poutre avant, pieds et boulons à ≤ 12 %. Le limon V1 donne une flèche de 2,0 mm sur 5,18 m (≈ L/2580), bien moins que les ≈ L/345 de D8 : les hypothèses de charge de D8 ne sont pas connues, on garde le script comme référence. Pas un calcul de structure.

- **D15 — Modèle en barres PyNite** (`calc/portique.py`, PyNiteFEA 3.2, paramètres et hypothèses importés de `predim.py`). Barres : 4 pieds, cadre du palier (poutre avant coupée aux 4 limons), 4 limons, liaisons rigides courtes pour l'excentricité des platines sur l'âme de la poutre avant (≈ 29 mm, centre de cisaillement de l'UPE à 32 mm de l'âme). Appuis (choix de l'utilisateur) : **pieds et pieds de limons V1 encastrés** (platines chevillées dans une dalle béton, à terme), haut des limons V2 articulé (boulonné à la structure supérieure), limons articulés sur la poutre avant. **Pas de garde-corps** pour l'instant : seules forces horizontales = défauts de verticalité EN 1993-1-1 (φ ≈ 1/253). Les marches ne relient pas les limons (côté sécurité). UPE 220 : A et I fort du catalogue, Iz (244 cm⁴) et J (11,6 cm⁴) calculés sans congés. Résultats ELU en 17/5 : déplacement horizontal du palier 0,12 mm, poutre avant 7 % en flexion et 9 % en torsion (Saint-Venant), pieds 1 %, limons V1 11 %. Efforts aux appuis : poteau N 7,3 kN, M 0,15 kN·m ; **pied de limon V1 N 10,4 kN, V 5,6 kN, M 6,2 kN·m** ; **arrivée V2 N 5,3 kN, V 5,7 kN**. Équilibre vérifié (43,5 kN de charges = réactions). Le palier est tenu horizontalement par les limons (effet de bracon entre la dalle et l'arrivée), pas par les pieds.

- **D16 — Visualisation PyVista directe** (`calc/visu.py`). Le module `Pynite.Rendering` impose IPython et trame (pile Jupyter) : écarté, on dessine directement avec PyVista à partir des résultats de `portique.py`. Deux vues en projection parallèle, côté V1 : moment fléchissant |M| ELU_X en couleur, déformée ELS_X × 300 sur la géométrie initiale ; appuis en points noirs. Sans écran : `xvfb-run -a python3 calc/visu.py --png DOSSIER`. Les liaisons rigides (excentricité des platines) ne sont pas dessinées.

## 6. Règles de travail avec l'agent

- **Ne rien exécuter sans autorisation explicite** : ni commande shell, ni génération ou modification 3D dans SolidCraft. Proposer, attendre le « oui », puis agir. Une autorisation vaut pour l'étape annoncée seulement.
- Le connecteur MCP SolidCraft ne lit/écrit que dans `~/.var/app/ai.storyteller.solidcraft/data/solidcraft/recovery`. Flux : enregistrer là, puis copier dans `cad/` (avec accord), puis commit/push.
- Lister les commandes de liaison (`list_commands` filtre `joint`) a semblé faire planter l'app : à éviter.
- FreeCAD est disponible en flatpak (`org.freecad.FreeCAD`, FreeCADCmd) ; l'import direct d'un `.FCStd` dans SolidCraft est incomplet, passer par un export STEP depuis FreeCAD.

## 7. Points ouverts

- Repère différent du FreeCAD d'origine (`archive/freecad/`) : recaler si on réutilise ses éléments de bâti (sol, terrasse, plateforme).
- Dans le FreeCAD, la volée haute semblait décalée d'environ un giron : c'est désormais aussi le cas du modèle (D6), à recaler si besoin.
- L'app ouvre désormais directement `cad/escalier.solidcraft` (verrou `cad/.~escalier.solidcraft.lock`, non suivi). L'utilisateur avait passé `jour` à 100 à la main avant que D9 le rende calculé.
- **Visserie à faire** (platines et poutre avant déjà percées). **Arrivée en haut de V2 : boulonnée à la structure supérieure** (décision de l'utilisateur) ; la structure elle-même n'est pas modélisée. Pas de cornière d'appui pour l'instant. La platine V2 dépasse de 9,5 mm le dessus du plancher, à côté de la marche V2 au niveau du palier : à araser si gênant. Côté jour, la marche V2 au niveau du palier est contre le limon V2, entre les deux limons intérieurs.
- **Marches et plancher en chêne de 30 mm** : insuffisants d'après `calc/predim.py` (38 mm minimum sur 1000 mm de portée, D14). Le plancher du palier (30 mm sur 1000 mm) n'est pas vérifié. À trancher : épaisseur, essence ou appui intermédiaire.
- La poutre avant reçoit les 4 limons, dont les deux intérieurs près du milieu de sa portée. En flexion elle est large (11 %, D14), et 9 % en torsion de Saint-Venant (D15) ; le gauchissement n'est pas calculé.
- Pieds des limons V1 au sol et platines des pieds : non modélisés.
- **Stabilité** : d'après `calc/portique.py` (D15), le palier est stable sans contreventement **à condition** que l'arrivée en haut de V2 reprenne ≈ 5,7 kN horizontaux par limon (ELU) : c'est elle, avec les limons, qui tient le palier. À reprendre quand le garde-corps sera ajouté (poussée horizontale non prise en compte).
- **Pieds de limons V1 encastrés** : l'encastrement attire ≈ 6,2 kN·m par limon (ELU), lourd pour une platine chevillée. Une platine articulée (moment repris en travée, voir `predim.py`) serait plus simple ; à trancher avant de dimensionner les chevilles.
- Noms HG / HD / BD / BG non confirmés ; le modèle utilise `Limon ext/int V1/V2`.
- Matériaux affectés corps par corps (D13) : un corps nouvellement créé (autre répartition, nouvelle pièce) reste en « Default » et doit être affecté à la main.

## 8. Prochaines étapes

Liste fixée par l'utilisateur (2026-10-26) :

1. **Fixation de l'arrivée** : platines du haut de V2 boulonnées à la structure supérieure.
2. **Garde-corps.**
3. **Plans** (mise en plan).
4. **Nomenclature.**
5. **Vérification par le calcul** (poutre avant en priorité, stabilité / contreventement). Prédimensionnement fait (`calc/predim.py`, D14), modèle en barres fait (`calc/portique.py`, D15) ; restent les assemblages et chevilles, le garde-corps dans le modèle et la validation par un bureau d'études.

Restent aussi en attente : visserie des platines, pieds des limons V1 au sol, contreventement, recalage avec le bâti du FreeCAD si nécessaire.

## 9. Historique

| Date | Demande | Réalisé | Fichiers |
|---|---|---|---|
| 2026-10-25 | Dessiner le FreeCAD dans SolidCraft | Export STEP via FreeCADCmd puis import (13 corps) | `archive/escalier-gab-import.solidcraft` |
| 2026-10-25 | Retracer l'ensemble marche proprement | Marche + 2 équerres paramétriques, autonome | `archive/ensemble-marche.solidcraft` |
| 2026-10-25 | Esquisse squelette pilotée | Paramètres, squelettes élévation et plan, 0 DDL | `cad/escalier.solidcraft` |
| 2026-10-25 | Placer l'ensemble marche automatiquement | Plans d'axe, lignes de foulée, marches de référence, réseaux sur chemin (15 + 5) | `cad/escalier.solidcraft` |
| 2026-10-25 | Mise en place du dépôt GitHub | Arborescence, README, CONCEPTION, AGENTS | dépôt |
| 2026-10-25 | Limons | 4 limons UPE 220 paramétriques, jour calculé, test `jeu_limons` 20 → 40 → 20 OK | `cad/escalier.solidcraft` |
| 2026-10-25 | Palier | Plancher 30 mm, cadre 4 UPE, 4 pieds tube 100×100×5 ; test `palier_profondeur` 1000 → 1200 → 1000 OK ; liaison limon V2 en attente (non enregistré) | `cad/escalier.solidcraft` (dans l'app) |
| 2026-10-25 | Cadre en onglet | Poutres latérales retournées (âme dehors), 4 UPE coupés à 45° aux angles ; volumes vérifiés, test profondeur OK | `cad/escalier.solidcraft` |
| 2026-10-25 | Pied du limon V2 | Coupe verticale à la rive (esquisses `Profil limon V2` et `Profil ailes limon V2` redessinées) ; répartition constatée à 14/8 | `cad/escalier.solidcraft` |
| 2026-10-25 | Platines d'about | Platine de 15 mm soudée en bout des 4 limons, puis **retirée de la volée 2** à la demande de l'utilisateur (limons V2 revenus à la coupe à la rive) ; volumes vérifiés, test `platine_ep` 25 → 15 OK ; répartition revenue à 16/6 | `cad/escalier.solidcraft` (dans l'app) |
| 2026-10-25 | Platines V1 séparées | Platine V1 passée d'une jonction au limon à un corps à part (`Platine ext V1` / `Platine int V1`), incluse dans la symétrie ; volumes vérifiés (limon + platine = ancien corps) | `cad/escalier.solidcraft` |
| 2026-10-26 | Platines en haut de V2 | Même platine que V1, en haut des limons V2 (arrivée), corps séparés, incluses dans la symétrie ; volumes vérifiés, test `platine_ep` 25 → 15 OK (non enregistré) | `cad/escalier.solidcraft` (dans l'app) |
| 2026-10-26 | Supprimer la coupe verticale du limon V2 au-dessus du palier | `Profil limon V2` et `Profil ailes limon V2` : arête haute prolongée jusqu'au plancher, assise horizontale sur un giron ; volumes OK, test `nb_volee1` 15 → 16 → 15 OK (non enregistré) | `cad/escalier.solidcraft` (dans l'app) |
| 2026-10-26 | Palier au niveau de la 1re marche V2, une contremarche de plus en V1 | Version précédente (limon prolongé sur le plancher) annulée. Squelette : ligne de giron au niveau du palier, contremarche V2 à `rive − giron` ; marche V2 accrochée au nez du palier, réseau `nb_volee2` ; équerre, emprise en plan, limons et platines V2 redessinés en expressions ; `nb_volee1` 15 → 16 ; contrôles des positions OK, test 16 → 15 → 16 OK, aucune erreur (non enregistré) | `cad/escalier.solidcraft` (dans l'app) |
| 2026-10-26 | Platine de 15 mm palier / V2 comme V1 | Limons V2 raccourcis de `platine_ep` côté palier, platine en corps séparé (`Platine palier ext/int V2`) incluse dans la symétrie ; volume identique aux platines V1 ; tests `jeu_limons` 100 → 140 → 100, `platine_ep` 15 → 25 → 15, `nb_volee1` 16 → 15 → 16 OK (non enregistré) | `cad/escalier.solidcraft` (dans l'app) |
| 2026-10-26 | Perçage identique des 6 platines | Paramètres `boulon_d`, `trou_jeu`, `oblong_course`, `boulons_entraxe` ; 2 oblongs verticaux M12 (14 × 24) centrés par platine, découpés avant les symétries ; 6 volumes identiques ; tests `boulons_entraxe` 140, `boulon_d` 16, `nb_volee1` 15, `jeu_limons` 140 puis retour OK (non enregistré) | `cad/escalier.solidcraft` (dans l'app) |
| 2026-10-26 | Perçage du palier | 8 trous ronds Ø14 dans l'âme de la poutre avant, en face du milieu des oblongs des platines V1 et V2 côté palier ; volume retiré conforme (8 × Ø14 × 6,5) ; tests entraxe 140, M16, 15/7, jeu 140 puis retour OK (non enregistré) | `cad/escalier.solidcraft` (dans l'app) |
| 2026-10-26 | Matériaux | Répartition constatée à 17/5 ; chêne sur 22 corps (marches, plancher), acier sur 60 corps ; aucun « Default » restant ; masse ≈ 893 kg ; test `nb_volee1` 17 → 16 → 17 OK (non enregistré) | `cad/escalier.solidcraft` (dans l'app) |
| 2026-10-26 | Liste des prochaines étapes | §8 réécrit d'après l'utilisateur (arrivée boulonnée à la structure supérieure, garde-corps, plans, nomenclature, calcul) ; point ouvert obsolète sur les platines V1 retiré | `CONCEPTION.md` |
| 2026-10-26 | Vérifier les cotes UPE 220 | h 220, b 85, tw 6,5, tf 12 conformes aux catalogues (Stad, ArcelorMittal, beamdimensions) ; seul écart : congés r 13 non modélisés (−2,2 % de masse) ; point ouvert retiré | `CONCEPTION.md` |
| 2026-10-27 | Prédimensionnement | Script `calc/predim.py` (marches, limons, poutre avant, pieds, boulons) ; marches de 30 mm insuffisantes (38 mm mini), le reste ≤ 12 % ; D14, points ouverts, §8 et README mis à jour | `calc/predim.py`, `CONCEPTION.md`, `README.md` |
| 2026-10-27 | Modèle en barres PyNite | `calc/portique.py` : pieds et limons V1 encastrés, arrivée V2 articulée, défauts de verticalité, sans garde-corps ; tout ≤ 11 %, palier stable grâce à l'arrivée V2 (5,7 kN horizontaux par limon), 6,2 kN·m en pied de limon V1 ; `afficher()` sorti dans `predim.py` ; D15, points ouverts, §8 et README mis à jour | `calc/portique.py`, `calc/predim.py`, `CONCEPTION.md`, `README.md` |
| 2026-10-27 | Visualisation PyVista | `calc/visu.py` : fenêtre interactive ou PNG (moments ELU_X, déformée ELS_X × 300) ; moment maxi au pied des limons V1 (6,2 kN·m) ; D16 et README mis à jour | `calc/visu.py`, `CONCEPTION.md`, `README.md` |
| 2026-10-27 | Rapport de calcul | Rapport de synthèse (description, hypothèses, méthode, vérifications, efforts aux appuis, figures, limites) dans un doc Claude (https://claude.ai/artifact/S7D154tdD82mPPB65nKBjT), copie Markdown + figures dans `calc/rapport/` | `calc/rapport/`, `CONCEPTION.md`, `README.md` |
