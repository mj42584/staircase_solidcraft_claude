# Conception — Escalier gab

Ce fichier décrit l'**état actuel** du projet et **le pourquoi des choix**. Les règles de travail avec l'agent sont dans [REGLES_AGENT_3D.md](REGLES_AGENT_3D.md).

## 1. Objectif

Escalier droit **à demi-tour**, deux volées séparées par un **palier intermédiaire sans différence de niveau**. Tout doit être **pilotable par des paramètres** : hauteur, giron, répartition des contremarches entre volées, profondeur du palier, largeur du jour.

## 2. Données d'entrée

Valeurs actuelles : voir les paramètres (§3). Ce tableau garde l'origine des données.

| Donnée | Origine |
|---|---|
| Hauteur totale (sol fini bas → sol fini haut) | **mesurée sur site** : dalle = sol fini bas, arrivée = dessus de la planche du cadre (`cadre_dessus` + `planche_ep`, §4) ; 3800 au départ → `hauteur_totale` |
| Angle de volée annoncé au départ | 32,4° — voir D1 |
| Répartition | choix de l'utilisateur dans l'app → `nb_volee1` — voir D2 ; volée 2 décalée d'un giron, voir D6 |
| Jour (vide entre volées) | 60 mm au départ, désormais calculé → `jour` — voir D9 |
| Marche | plaque (`marche_epaisseur`), deux équerres en cornière (`equerre_*`) symétriques |
| Limons | UPE 220, cotes **vérifiées au catalogue** EN 10365 (2026-10-26) → `limon_*` ; congés non modélisés (§4) — voir D8 |
| Palier | autoporté sur 4 pieds, sans appui sur le mur du site — voir D11 |
| Plancher du palier | même matériau et même épaisseur que les marches (`palier_ep` = `marche_epaisseur`) |
| Matériaux | marches et plancher en **chêne** (« Oak », 0,75 g/cm³) ; tout le reste en **acier** (« Steel », 7,85 g/cm³) — voir D13 |

## 3. Paramètres du modèle (`cad/escalier.solidcraft`)

**Pilotes**

| Paramètre | Valeur | Pilote |
|---|---|---|
| `hauteur_totale` | 3848 mm | hauteur de marche, arrivée |
| `nb_contremarches` | 22 | hauteur de marche, nb_volee2 |
| `nb_volee1` | 16 | contremarches volée basse → hauteur du palier, nombre de marches V1 |
| `giron` | 274 mm | squelette, profondeur des marches, pas des réseaux |
| `emmarchement` | 1000 mm | largeur des volées et des marches, plans d'axe |
| `jeu_limons` | 100 mm | vide entre les deux limons intérieurs → `jour` (passé de 20 à 100 par l'utilisateur) |
| `palier_profondeur` | 1000 mm | squelette (élévation et plan) |
| `marche_epaisseur` | 60 mm (passé de 30 à 60 par l'utilisateur) | marches, position des équerres, plancher du palier |
| `equerre_aile` | 30 mm | cornières (ailes égales) |
| `equerre_ep` | 3 mm | cornières |
| `equerre_longueur` | 200 mm | cornières, centrées sur le giron |
| `debord` | 0 mm | débord du nez de marche vers l'avant |
| `limon_h` | 220 mm | hauteur UPE |
| `limon_b` | 85 mm | largeur des ailes UPE, pilote `jour` |
| `limon_tw` | 6,5 mm | épaisseur d'âme |
| `limon_tf` | 12 mm | épaisseur d'aile |
| `limon_r` | 13 mm | congé de laminage de l'UPE (catalogue EN 10365) ; utilisé par les limons en Frame Member (limon V1 pour l'instant) |
| `limon_dessus` | `-30 mm * giron / pas_volee` (−25,3 mm ; 0 jusqu'au 2026-10-29) | haut du limon au-dessus de la ligne de nez, perpendiculairement (0 = au ras des nez) ; négatif : limon descendu de 30 mm en vertical, pour centrer le bout du limon V1 sur la poutre avant (D17) |
| `palier_ep` | `marche_epaisseur` (60 mm) | plancher du palier |
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
| `hauteur_marche` | `hauteur_totale / nb_contremarches` | 174,91 mm |
| `nb_volee2` | `nb_contremarches - nb_volee1` | 6 |
| `angle_volee` | `atan(hauteur_marche / giron)` | 32,55° |
| `blondel` | `2 * hauteur_marche + giron` | 624 mm (confort 600–640) |
| `pas_volee` | `sqrt(giron ^ 2 + hauteur_marche ^ 2)` | 325,07 mm |
| `jour` | `2 * limon_b + jeu_limons` | 270 mm |
| `rive_x` | `(nb_volee1 - 1) * giron` | 4110 mm (X de la rive du palier) |
| `cadre_y` | `jour / 2 + emmarchement + limon_b` | 1220 mm (demi-largeur hors tout du cadre) |
| `limon_hv` | `limon_h * pas_volee / giron` | 261,0 mm (hauteur d'un limon en coupe verticale) |

**Cotes des esquisses** : toutes nommées `<pièce>_<rôle>` (ex. `limon_v1_bas`, `pied_avant_v2_ep_3`, `trou_poutre_v2_int_haut_z`) ; préfixes `sqe_` / `sqp_` pour les squelettes d'élévation et de plan. Aucun point n'est défini par une expression : les esquisses sont faites de lignes cotées (2026-10-29).

## 4. Architecture du modèle

**Repère** : origine au pied de la première contremarche, **au milieu du jour**. Volée 1 monte vers **+X** côté **Y négatif** ; volée 2 redescend en X (monte vers −X) côté **Y positif**. Z vers le haut.

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
14. `Plancher palier` — rectangle coté X `rive_x` → `+ palier_profondeur`, Y ±`cadre_y`, extrudé de `palier_ep` vers le haut : il couvre tout le cadre, limons extérieurs compris.
15. `Pieds palier` — 4 tubes `poteau_cote` × `poteau_ep` aux coins du cadre, du sol au dessous des poutres : `Pied avant V1`, `Pied avant V2`, `Pied arrière V1`, `Pied arrière V2`.
16. Cadre en **onglet à 45°** : pour chaque poutre, une esquisse `Âme poutre …` (trapèze d'épaisseur `limon_tw`, extrudé de `limon_h` vers le bas, nouveau corps) et une esquisse `Ailes poutre …` (trapèze de largeur `limon_b`, extrudé deux fois de `limon_tf` : aile haute, et aile basse avec `start_offset`, jointes au corps). Les 4 UPE ont l'**âme à l'extérieur et les ailes vers l'intérieur**, pleine longueur jusqu'aux angles extérieurs, coupées à 45° : `Poutre avant palier`, `Poutre arrière palier`, `Poutre latérale V1`, `Poutre latérale V2`. Une esquisse et un corps par poutre, pour que les onglets jointifs ne fusionnent pas les corps.

**Limon V1 en Frame Member** (prototype, 2026-10-29) : `Axe limon V1` (plan `Rive ext V1`, ligne des nez projetée en construction, ligne du bas du limon parallèle, cotée `limon_h - limon_dessus`, prolongée de `limon_h` à chaque bout) → `Barre limon V1` (Frame Member, profilé `channel` piloté par `limon_h`, `limon_b`, `limon_tw`, `limon_tf`, `limon_r`, ancrage `bottom_right`, miroir) → `Coupes limon V1` (U coté autour du limon : coupe verticale au premier nez, horizontale au sol, verticale à `rive_x - platine_ep`) → `Coupe limon V1` (enlèvement de `limon_b` ciblé sur le limon). Section réelle avec congés : 33,9 cm², 26,6 kg/m (+2,2 % par rapport aux esquisses). Les limons V2 sont encore dessinés en esquisses (ci-dessous).

**Limons** : chaque esquisse de limon (`Profil limon …`, `Profil ailes limon …`, sur les plans de rive) **projette la ligne des nez du squelette** (`Squelette élévation`, en construction) ; le bord bas est parallèle à cette ligne, coté `limon_h - limon_dessus` (toujours positif), le bord haut parallèle au bord bas, coté `limon_h`, les ailes parallèles aux bords, cotées `limon_tf` ; les coupes verticales sont cotées en X depuis l'origine. Platines : rectangles cotés (coin en X et en Z depuis l'origine, `platine_ep` × `limon_hv`). Cotes en distances positives, y compris sur les rives V2 (axe vertical vers −Z). Extrémités provisoires : V1 coupé horizontalement au sol et verticalement au premier nez (X = 0). En haut de V2 (arrivée), même détail que V1 côté palier : limon coupé verticalement à `(nb_volee1 - nb_volee2 - 1) * giron + platine_ep`, platine `Profil platine V2` → `Platine limon V2` en corps séparé (`Platine ext V2`), contre le plan vertical du dernier nez. `Symétrie limon V2` symétrise `Limon ext V2` et `Platine ext V2` → `Limon int V2` et `Platine int V2`. La structure d'arrivée est modélisée à part (`cad/environnement.solidcraft`, voir plus bas) ; l'assemblage platine / arrivée ne l'est pas. Côté palier : les **limons V1** sont coupés verticalement à `rive − platine_ep`, et une **platine d'about** (`Profil platine V1` → `Platine limon V1`, `platine_ep` × `limon_b` × hauteur du bout de limon) est un **corps séparé** (`Platine ext V1`), distinct du limon, à la demande de l'utilisateur. Cette fonction est insérée **avant** `Symétrie limon V1`, qui symétrise les deux corps (`Limon ext V1` et `Platine ext V1`) → `Limon int V1` et `Platine int V1`. La platine arrive contre l'âme de la poutre avant ; l'assemblage platine / poutre n'est pas modélisé. Les **limons V2**, côté palier, ont le même détail que V1 : coupés verticalement à `rive − platine_ep`, avec une platine d'about en corps séparé (`Profil platine palier V2` → `Platine palier limon V2` → `Platine palier ext V2`, sketch sur `Rive ext V2`, extrusion `limon_b`), insérée avant `Symétrie limon V2`, qui produit `Platine palier int V2`. Comme la volée 2 est décalée d'un giron (D6), la ligne de nez passe au niveau du palier à la rive ; la platine (V2 côté palier) s'arrête ≈ 20 mm sous le dessus du plancher (avec `limon_dessus` actuel). Bouts de limons sur la poutre avant (16/6, 60 mm) : V1 centré (2498 → 2759, poutre 2518,5 → 2738,5), V2 19 mm plus haut (2517 → 2778), écart dû aux platines sur des pentes opposées (2 × `platine_ep * hauteur_marche / giron`). Formules des hauts de platines (cotes `platine_*_haut_z`) : rive = `nb_volee1 * hauteur_marche + platine_ep * hauteur_marche / giron` ± décalages, haut = `hauteur_totale - platine_ep * hauteur_marche / giron` ± décalages. **Perçage des 6 platines** (identiques en taille, 15 × `limon_b` × `limon_h * pas_volee / giron`, et en perçage) : 2 trous oblongs verticaux à ± `boulons_entraxe / 2` d'un centre : milieu de la platine à l'arrivée, **milieu de la poutre avant** côté palier (`nb_volee1 * hauteur_marche - palier_ep - limon_h / 2`). `Perçage platine V1` (plan YZ) → `Trous platine V1` (découpe de `Platine ext V1`, insérée avant `Symétrie limon V1`) ; `Perçage platines V2` (plan YZ, 4 oblongs) → `Trous platines V2` (découpe ciblée sur `Platine ext V2` et `Platine palier ext V2`, de `(nb_volee1 - nb_volee2 - 1) * giron` sur `nb_volee2 * giron`, insérée avant `Symétrie limon V2`). Les oblongs sont des rainures cotées en expressions (centres par rapport à l'origine, rayon, course, entraxe) (piège des oblongs, §6.3). Côté palier, V1 et V2 ont les mêmes trous, symétriques sur la poutre (16/6, 60 mm : 2578,5 / 2678,5). **Perçage de la poutre avant** : `Perçage poutre avant` (plan YZ, 8 cercles cotés en expressions) → `Trous poutre avant` (découpe de `Poutre avant palier` sur `limon_tw` depuis la rive) : trous **ronds** Ø `boulon_d + trou_jeu` (14 mm) dans l'âme, en face du **milieu** des oblongs des 4 platines côté palier ; le réglage se fait par les oblongs. Marges avec 100 / M12 (16/6, 60 mm) : côté V2, bas de l'oblong bas à ≈ 35 mm de la face intérieure de l'aile basse du limon ; trous ronds de la poutre à ≈ 36 mm de ses ailes (congés non modélisés). Les congés de laminage de l'UPE (r = 13 mm) sont ignorés : section modélisée 33,1 cm² contre 33,9 au catalogue, masse des UPE sous-estimée de 2,2 % (26,0 au lieu de 26,6 kg/m).

**Point d'intégration de la marche** : nez de marche, face supérieure, milieu de la largeur — c'est le point par lequel passent les lignes de nez du squelette.

Nombre de marches : chaque volée a une marche de moins que de contremarches (la dernière contremarche arrive sur le palier ou l'arrivée). Exception : la volée 2 a une marche de plus, au niveau du palier (D6). Avec 16/6 : 15 + 6 = 21 marches (palier à 2798,5 mm, rive à X = 4110, première contremarche V2 à X = 3836, arrivée à X = 2466).

**Environnement et assemblage**

**Site** (photos du 2026-10-27, mesures au téléphone à quelques cm près) : grange, dalle béton = sol fini. **Arrivée** sur un cadre en acier brut (plateforme ≈ 2,57 × 5,51 m, planche dessus), tout en **IPE 200** pour l'instant, sur poteaux avec platines au sol. **V2 arrive perpendiculairement à la poutre de 2,57 m**, en venant de l'extérieur du cadre. Autres mesures : 2,95 m sur le mur depuis une poutre grise, 1,45 m entre deux poteaux au sol, 1,1 m entre une attache de solive et l'angle du cadre. Environnement modélisé à part : **cadre rouillé, sol, mur en pierre** ; la charpente grise est ignorée (choix de l'utilisateur). Vue de dessus (croquis de l'utilisateur) : mur le long du grand côté, 6 poteaux (3 par petit côté ; 4 dans le modèle, voir ci-dessous), 2 solives parallèles au mur ; **V2 côté mur**, palier hors du cadre, **V1 côté extérieur, qui passe sous le cadre** entre le poteau du milieu et le poteau avant côté arrivée (1,45 m libres, mesure faite avec les 6 poteaux).

**`cad/environnement.solidcraft`** (2026-10-27, SolidCraft 0.24.1) : repère **X = 0 sur la face côté escalier de la poutre d'arrivée** (cadre vers −X), **Y = 0 sur la face côté mur du cadre** (cadre vers −Y, mur vers +Y), Z = 0 dessus de dalle. Paramètres : `cadre_longueur` 3788 (croquis, à confirmer, §7), `cadre_largeur` 2670, `cadre_dessus` 3788, `planche_ep` 60, `ipe_h/b/tw/tf` 200/100/5,6/8,5, `poteau_milieu` 1400 (axe depuis la face côté mur), `poutre_mur_longueur` 5510 (poutre le long du mur prolongée **au-delà** du cadre côté escalier, sens à confirmer, §7), `mur_ecart` 50, `mur_ep` 500, `mur_h` 3800, `dalle_ep` 200 ; 4 poteaux (poteaux avant supprimés par l'utilisateur). Poutres et poteaux en **Frame Member** (onglet Mécano-soudure, profilé `i_beam` piloté par `ipe_*`). **Esquisses cotées** (demande de l'utilisateur : des cotes pilotées par paramètres, pas des points en expressions) : lignes horizontales / verticales, cotes depuis l'origine en expressions (`d16`… `d53`), 0 DDL partout. Corps : `Poutre mur`, `Poutre avant`, `Poutre arrivée`, `Poutre fond`, `Solive 1`, `Solive 2` (à 1/3 et 2/3), 4 poteaux `Poteau mur/milieu arrivée/fond` (âme suivant Y), `Planche`, `Dalle`, `Mur` (plaques). Contrôles à la création : encombrements OK, 1450 libres entre poteaux, dessus planche à 3848 ; test `cadre_largeur` 2570 → 2700 → 2570 OK. Ni porte, ni matériaux.

**`cad/projet_escalier.solidcraft`** (2026-10-27) : assemblage, **composants liés** `Environnement` (à l'origine, fixé / grounded) et `Escalier`, décalé de **[−2466, −1446,6, 0]** : X = −(`nb_volee1` − `nb_volee2` − 1) × `giron` (−3014 en 17/5), platine du haut de V2 plaquée contre `Poutre arrivée` ; Y choisi par l'utilisateur (jeu V2 / face du cadre, §7) ; Z = 0, pieds sur la dalle. L'escalier est **fixé (grounded)** lui aussi, contre les déplacements accidentels : le libérer avant de le repositionner, puis le refixer.

## 5. Journal des décisions

- **D1 — Angle calculé, non piloté.** 32,4° est incohérent avec giron 274 et hauteur 172,73 (arctan → 32,23°). On pilote hauteur totale + nombre de contremarches + giron ; l'angle en découle.
- **D2 — Répartition pilotable.** Départ 17/5 (palier à 2936 mm). L'utilisateur est ensuite passé à **16/6** dans l'app, puis à **14/8** un temps, puis de nouveau à **16/6**, revenu à **17/5** (2026-10-26) et enfin à **16/6** (2026-10-27) ; 16/6 est la valeur actuelle. Le modèle suit ces changements sans erreur.
- **D3 — Ensemble marche intégré au squelette, pas en fichier lié.** SolidCraft permet un composant lié (`component.insert_design`), mais les paramètres ne traversent pas les fichiers et le réseau sur chemin n'accepte pas les composants. Intégré, la marche est pilotée directement par `giron` et `emmarchement`.
- **D4 — Réseau sur chemin plutôt que rectangulaire.** Le chemin est une courbe du squelette : la direction suit l'angle de volée. Le nombre d'occurrences accepte une expression (vérifié).
- **D5 — Débord sans cote nulle.** SolidCraft refuse une cote de 0. L'arrière de la marche est coté depuis le nez (`giron`) et la longueur totale vaut `giron + debord`.
- **D6 — Volée 2 décalée d'un giron.** Au départ, volée 2 à l'aplomb du nez du palier (disposition classique). Changé à la demande de l'utilisateur (2026-10-26) : la première marche de V2 est au niveau du palier et la première contremarche V2 recule d'un giron (`rive − giron`). Cela règle la jonction limon V2 / palier (D12). L'escalier s'allonge d'un giron.
- **D7 — Pas de Git LFS** : les fichiers sont petits. Seuls exports versionnés, pour la vue 3D du README : `cad/escalier.stl` (escalier seul), `cad/projet_escalier.stl` et `cad/apercu.png` (projet complet). Une modification de géométrie de `escalier.solidcraft` touche les trois ; une de `environnement.solidcraft` ou `projet_escalier.solidcraft`, les deux derniers.
- **D8 — Limons UPE 220, ailes vers l'extérieur.** Comparé : fer plat 300×10 (≈ L/300), UPE 160 (≈ L/120 sur 4,1 m, trop souple, et l'équerre L 200 ne rentre pas entre les ailes), UPE 200 (≈ L/255), UPE 220 (≈ L/345). Avec `limon_dessus = 0`, la zone boulonnable de l'âme (≈ 170 mm) couvre l'équerre (≈ 45 → 177 mm sous la ligne de nez). Ordres de grandeur seulement, pas un calcul de structure.
- **D9 — Jour calculé depuis les limons.** Les ailes des deux limons intérieurs se font face dans le jour : `jour = 2 * limon_b + jeu_limons`. Le jeu est libre (`jeu_limons`).
- **D10 — Symétrie de corps, pas de fonctions.** Une symétrie des fonctions « âme + ailes » joignait les ailes copiées au limon d'origine (l'extrusion des ailes est une jonction ciblée) : on symétrise le corps entier.
- **D11 — Palier : cadre UPE + plancher dessus + 4 pieds.** Pas de mur autour. Cadre de 4 UPE (même profil que les limons, piloté par `limon_*`), âmes à l'extérieur, ailes vers l'intérieur, angles coupés à 45° et soudés (demande de l'utilisateur : poutres latérales retournées de 180° par rapport à la première version), plancher posé dessus (détail : §4, étapes 13 à 16). La poutre avant reçoit les 4 limons ; le bout du limon V1 est centré sur sa hauteur, celui de V2 19 mm plus haut (§4, D17). Pieds aux 4 coins (`poteau_*`).

- **D12 — Jonction limon V2 / palier par décalage de la volée.** But de l'utilisateur : supprimer la face verticale du limon V2 qui dépassait au-dessus du palier. Une première version (limon prolongé et posé sur le plancher) a été écartée : on a plutôt ajouté une contremarche à la volée 1 (15/7 → 16/6) et mis la première marche V2 au niveau du palier (D6). Toutes les contremarches restent égales. Le limon V2 arrive à la rive au ras du palier et couvre toute la hauteur de la poutre avant.

- **D13 — Matériaux.** Chêne pour les 21 marches (17/5) et le plancher du palier, acier pour limons, platines, équerres, cadre et pieds. Masse totale ≈ 893 kg (acier 708, chêne 184) en 17/5 avec des marches de 30 mm ; à remesurer (chêne à peu près doublé à 60 mm). L'affectation se fait par nom de corps (`material.assign`) ; elle tient au recalcul et quand un corps de réseau disparaît puis revient (test 17 → 16 → 17) ; piège des corps nouveaux : §6.3.

- **D14 — Prédimensionnement par script Python** (`calc/predim.py`, bibliothèque standard seule). Il reprend à la main les paramètres du §3 et vérifie, en ordres de grandeur : marches (flexion et flèche, D30), limons V1 / V2, poutre avant (4 réactions de limons + demi-palier), flambement des pieds (libres en tête, L_cr = 2 H), cisaillement des boulons M12. Hypothèses : q = 2,5 kN/m², Q = 2 kN (AN française, cat. A), chêne D30, acier **S235 supposé**, boulons 8.8 supposés, flèche L/300. Résultats (en 3800 / 17/5 / 30 mm, voir §7) : **marches de 30 mm insuffisantes** (contrainte 100 %, flèche 6,3 mm pour 3,3 admis, **38 mm minimum**) ; limons, poutre avant, pieds et boulons à ≤ 12 %. Le limon V1 donne une flèche de 2,0 mm sur 5,18 m (≈ L/2580), bien moins que les ≈ L/345 de D8 : les hypothèses de charge de D8 ne sont pas connues, on garde le script comme référence. Pas un calcul de structure.

- **D15 — Modèle en barres PyNite** (`calc/portique.py`, PyNiteFEA 3.2, paramètres et hypothèses importés de `predim.py`). Barres : 4 pieds, cadre du palier (poutre avant coupée aux 4 limons), 4 limons, liaisons rigides courtes pour l'excentricité des platines sur l'âme de la poutre avant (≈ 29 mm, centre de cisaillement de l'UPE à 32 mm de l'âme). Appuis (choix de l'utilisateur) : **pieds et pieds de limons V1 encastrés** (platines chevillées dans une dalle béton, à terme), haut des limons V2 articulé (boulonné à la structure supérieure), limons articulés sur la poutre avant. **Pas de garde-corps** pour l'instant : seules forces horizontales = défauts de verticalité EN 1993-1-1 (φ ≈ 1/253). Les marches ne relient pas les limons (côté sécurité). UPE 220 : A et I fort du catalogue, Iz (244 cm⁴) et J (11,6 cm⁴) calculés sans congés. Résultats ELU (en 3800 / 17/5 / 30 mm) : déplacement horizontal du palier 0,12 mm, poutre avant 7 % en flexion et 9 % en torsion (Saint-Venant), pieds 1 %, limons V1 11 %. Efforts aux appuis : poteau N 7,3 kN, M 0,15 kN·m ; **pied de limon V1 N 10,4 kN, V 5,6 kN, M 6,2 kN·m** ; **arrivée V2 N 5,3 kN, V 5,7 kN**. Équilibre vérifié (43,5 kN de charges = réactions). Le palier est tenu horizontalement par les limons (effet de bracon entre la dalle et l'arrivée), pas par les pieds.

- **D16 — Visualisation PyVista directe** (`calc/visu.py`). Le module `Pynite.Rendering` impose IPython et trame (pile Jupyter) : écarté, on dessine directement avec PyVista à partir des résultats de `portique.py`. Deux vues en projection parallèle, côté V1 : moment fléchissant |M| ELU_X en couleur, déformée ELS_X × 300 sur la géométrie initiale ; appuis en points noirs. Sans écran : `xvfb-run -a python3 calc/visu.py --png DOSSIER`. Les liaisons rigides (excentricité des platines) ne sont pas dessinées.

- **D17 — Limons descendus de 30 mm** (2026-10-29, demande de l'utilisateur). Avec le plancher de 60 mm posé sur le cadre, la poutre avant était 30 mm trop bas par rapport aux bouts de limons : trous excentrés, écrous difficiles d'accès près des ailes. Plutôt que de toucher au palier, `limon_dessus` = −30 mm vertical : V1 centré sur la poutre, V2 à 19 mm, entraxe 100 retrouvé. Effets : les marches dépassent de 30 mm au-dessus des limons (moitié de leur épaisseur), la platine V2 côté palier ne dépasse plus du plancher, les équerres sortent du congé bas de l'UPE (≈ 20 mm de marge). Ne règle pas l'accès aux écrous des limons intérieurs, côté jour (`jeu_limons`, §7).

## 6. Outils et pièges du projet

Les règles de travail sont dans [REGLES_AGENT_3D.md](REGLES_AGENT_3D.md) ; ce chapitre n'en garde que ce qui est propre à ce projet.

### 6.1 Versions des logiciels (poste local de l'utilisateur)

| Logiciel | Rôle | Référence | Vérifier avec |
|---|---|---|---|
| SolidCraft (Flatpak utilisateur `ai.storyteller.solidcraft`, installé depuis les releases GitHub de `tangency-labs/solidcraft`, pas Flathub) | modèle 3D | **0.24.1** | `flatpak info --user ai.storyteller.solidcraft` |
| Connecteur MCP SolidCraft | pilotage du 3D par l'agent | à relever | selon son installation |
| Python 3 | calculs | à relever | `python3 --version` |
| PyNiteFEA | modèle en barres (`portique.py`) | **3.2** | `pip show PyNiteFEA` |
| PyVista, NumPy | visualisation (`visu.py`) | à relever | `pip show pyvista numpy` |
| Claude Code | agent | à relever | `claude --version` |

SolidCraft change de format de fichier à chaque version : un fichier enregistré en 0.24.1 ne s'ouvre pas en 0.24.0 ou avant.

### 6.2 Fichiers et dossiers

- **Dossier de travail du connecteur MCP** : `~/.var/app/ai.storyteller.solidcraft/data/solidcraft/recovery` (il ne lit et n'écrit que là).
- **Fichiers liés** : `cad/escalier.solidcraft`, `cad/environnement.solidcraft`, `cad/projet_escalier.solidcraft`.
- **Non versionné** : les photos du site, le verrou `cad/.~escalier.solidcraft.lock` (l'app ouvre directement `cad/escalier.solidcraft`).

### 6.3 Pièges connus

- Lister les commandes de liaison (`list_commands` filtre `joint`) a semblé faire planter l'app. Peut-être corrigé en 0.23.1 : à éviter tant que ce n'est pas vérifié.
- Esquisse sur un plan décalé de XZ (rives V2, environnement) : l'axe vertical va vers −Z, les coordonnées Z s'écrivent en négatif ; les cotes, elles, restent des distances positives.
- Ligne du squelette projetée dans une esquisse de profil : la passer en construction (`sketch.construction`), sinon elle peut couper le profil et casser l'extrusion (par ex. si `limon_dessus` devient positif).
- Paramètres de fonctions (distances d'extrusion, décalages de plans, réseaux, profilés) : ils sont nommés `dN` comme les cotes mais n'apparaissent pas dans `inspect_design` ; les lister avec `parameters.list` (`filter: all`).
- Depuis l'ajout du Frame Member, l'enregistrement n'écrit plus le cache de géométrie (fichier ≈ 28 Ko au lieu de ≈ 200 Ko) : l'ouverture recalcule tout, sans erreur (vérifié). Cause non établie.
- Contrainte verticale / horizontale : commande `sketch.constraint.horizontal_vertical` (`mode`), il n'y a pas de `sketch.constraint.vertical`.
- Point défini par une expression : pour le libérer, supprimer la ligne et la redessiner avec l'option `ids` (même identifiant, un Frame Member la retrouve). Fix/UnFix et le déplacement ne suffisent pas.
- La commande d'oblong n'accepte pas d'expressions : rainures cotées à la place (§4).
- `component.insert_design` et `occurrence.move` ne prennent qu'un décalage chiffré : l'escalier ne suit pas la répartition dans le projet, il faut le recaler à la main.
- Un corps nouvellement créé reste en matériau « Default » (D13), par exemple une marche au-delà du nombre affecté : l'affecter à la main.

### 6.4 État des lieux des logiciels

*SolidCraft 0.22.1 → 0.24.1* (2026-10-27, d'après les notes de version, **rien testé dans l'app**) :
- D5 : une cote de longueur zéro garde l'esquisse contrainte (0.23.0) ; `debord = 0` pourrait être accepté directement. À tester.
- Oblongs (§4) : corrections des rainures en esquisse (0.24.0), mais rien n'indique qu'elles acceptent des expressions. Garder les rainures actuelles tant que ce n'est pas testé.
- `Perçage poutre avant` : les répétitions d'esquisse prennent nombre et espacement dans les paramètres (0.23.1) ; les 8 cercles pourraient devenir une répétition.
- D10 : symétries et répétitions désignent leurs sources par identifiant (0.24.1), plus robustes aux renommages. Rien à changer.
- Garde-corps : onglet Mécano-soudure (structures, 0.24.0) et Pipe avec opération joindre / découper (0.23.1). Vérifier si la bibliothèque de profilés a des tubes et des UPE.
- Plans et nomenclature : rien de nouveau.

### 6.5 Gestion des versions

Git, dépôt GitHub `mj42584/staircase_solidcraft_claude`. Version de travail = branche (nom court de la tâche) ; enregistrer = commit + push sur la branche ; version de référence = `main` ; valider = fusion (merge) par l'utilisateur. Git ne fusionne pas les `.solidcraft` (binaires).

## 7. Points ouverts

- **Calculs à relancer** : `hauteur_totale` (3800 → 3848), `nb_volee1` (17 → 16), `marche_epaisseur` / `palier_ep` (30 → 60), `limon_dessus` (0 → −25,3). Calculs faits en 3800 / 17/5 / 30 mm (D14, D15, `calc/rapport/`).
- **Accès aux écrous des limons intérieurs** (platines côté palier) : le U du limon s'ouvre côté jour, avec seulement `jeu_limons` entre les deux limons intérieurs. Pistes : augmenter `jeu_limons` (≈ 150) ou remplacer les platines par des cornières d'attache (D17).
- **Hauteur libre au-dessus de V1** sous la poutre d'arrivée : `cadre_dessus − ipe_h − (nb_volee1 − nb_volee2) × hauteur_marche` = 3588 − 10 h = **1,84 m** en 16/6 (1,49 m en 17/5) ; ≈ 2 m visés en général.
- **Collision dans le projet** (`inspect.interference`, 16/6) : `Poteau milieu arrivée` / `Limon int V1` (3,4 mm). Celle de `Poutre mur` avec le haut de V2 (limon, platine, équerre) a disparu avec le jeu en Y (il faut au moins ≈ 100 mm).
- **Jeu V2 / face du cadre** (≈ 227 mm, choisi par l'utilisateur) : à revoir.
- **Placement de l'escalier dans le projet** : tester les liaisons (joints) pour qu'il suive la répartition (piège du décalage chiffré, §6.3).
- **Environnement à confirmer** : `cadre_longueur` 3788 vient du croquis, alors que la plateforme mesurée fait ≈ 5,51 m et que 3788 est aussi la hauteur du cadre ; sens de prolongement de `poutre_mur_longueur`.
- **Marches et plancher en chêne** : 38 mm minimum d'après D14 ; passés à 60 mm par l'utilisateur, à confirmer en relançant le calcul (le plancher du palier n'a jamais été vérifié).
- **Poutre avant** : elle reçoit les 4 limons, dont les deux intérieurs près du milieu de sa portée (taux en D14 et D15) ; le gauchissement n'est pas calculé.
- **Stabilité** : le palier n'est stable sans contreventement que si l'arrivée en haut de V2 reprend les efforts horizontaux (D15). À reprendre quand le garde-corps sera ajouté (poussée horizontale non prise en compte).
- **Pieds de limons V1 encastrés** : le moment d'encastrement (D15) est lourd pour une platine chevillée. Une platine articulée (moment repris en travée, voir `predim.py`) serait plus simple ; à trancher avant de dimensionner les chevilles.
- Noms HG / HD / BD / BG non confirmés ; le modèle utilise `Limon ext/int V1/V2`.

## 8. Prochaines étapes

Liste fixée par l'utilisateur (2026-10-26) :

1. **Fixation de l'arrivée** : platines du haut de V2 boulonnées à la structure supérieure.
2. **Garde-corps.**
3. **Plans** (mise en plan).
4. **Nomenclature.**
5. **Vérification par le calcul** (poutre avant en priorité, stabilité / contreventement) : prédimensionnement et modèle en barres faits (D14, D15) ; restent les assemblages et chevilles, le garde-corps dans le modèle et la validation par un bureau d'études.

**En attente** (pas pour l'instant, choix de l'utilisateur) : visserie (platines, poutre avant, arrivée), cornière d'appui, assemblage platines / poutre avant et platines / arrivée, pieds des limons V1 au sol et platines des pieds (non modélisés).

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
| 2026-10-27 | Dépôt déplacé, SolidCraft à jour | Clone de `staircase_solidcraft_claude` à la place de l'ancien dossier ; SolidCraft 0.22.1 → 0.24.1 (Flatpak GitHub) ; règle d'état des lieux à chaque mise à jour (§6) et premier état des lieux (§7) | `CONCEPTION.md` |
| 2026-10-27 | Environnement du site | Photos et croquis : arrivée sur un cadre IPE 200, hauteur mesurée 3848 ; fichier séparé `cad/environnement.solidcraft` (cadre, 6 poteaux, 2 solives, poutre le long du mur, planche, dalle, mur) en Frame Member ; insertion à décalage chiffré seulement (vérifié) ; escalier pas touché | `cad/environnement.solidcraft`, `CONCEPTION.md` |
| 2026-10-27 | Coter les esquisses de l'environnement | Modifications de l'utilisateur relevées (largeur 2670, poteaux milieu 1400, mur 3800, poteaux avant supprimés) ; 6 esquisses redessinées avec de vraies cotes en paramètres, 0 DDL ; positions inchangées ; test `cadre_largeur` 2900, `cadre_longueur` 4000, `poteau_milieu` 1200 puis retour OK | `cad/environnement.solidcraft`, `CONCEPTION.md` |
| 2026-10-27 | Retouches de l'utilisateur relevées | Dalle et mur raccourcis : 100 mm au-delà du cadre (X −3888) et de la poutre le long du mur (X 5610), au lieu de 3000 ; dalle prolongée sous le mur (bord à `mur_ecart + mur_ep`) ; rien d'autre de changé, aucune erreur ; enregistré | `cad/environnement.solidcraft`, `CONCEPTION.md` |
| 2026-10-27 | Hauteur mesurée dans l'escalier | `hauteur_totale` 3800 → 3848 (h = 174,91, Blondel 624) ; répartition 17/5 et `marche_epaisseur` 60 constatés ; palier à 2973,45, haut des platines V2 à 3838,4 (conforme au calcul) ; 82 corps, aucune erreur (avertissement booléen de `Trous poutre avant` déjà présent) ; calculs `calc/` **pas relancés** (leurs paramètres sont à 3800 / 30) | `cad/escalier.solidcraft`, `CONCEPTION.md` |
| 2026-10-27 | Projet escalier | Assemblage `cad/projet_escalier.solidcraft` : environnement fixé à l'origine, escalier lié décalé de [−3014, −1220, 0] (17/5, jeu V2 / cadre 0 provisoire) ; liens relatifs ; 6 collisions (poutre le long du mur / haut de V2, poteau du milieu / V1) ; hauteur libre 1,49 m au-dessus de V1 | `cad/projet_escalier.solidcraft`, `CONCEPTION.md` |
| 2026-10-27 | Escalier plaqué dans le projet | L'utilisateur avait déplacé l'escalier (+181 X, −227 Y, +320 Z) ; recalé en X (platine V2 contre la poutre d'arrivée, X = 0) et Z (pieds sur la dalle), Y gardé ; décalage [−3014, −1446,6, 0] ; reste 1 collision : `Poteau milieu arrivée` / `Limon int V1` (3,4 mm) | `cad/projet_escalier.solidcraft`, `CONCEPTION.md` |
| 2026-10-27 | Fixer l'escalier dans le projet | Occurrence `Escalier` fixée (grounded), position inchangée (platine V2 à X = 0) | `cad/projet_escalier.solidcraft`, `CONCEPTION.md` |
| 2026-10-27 | Recaler après modification de l'escalier | L'utilisateur est passé en **16/6** (palier à 16 h = 2798,5) et a mis à jour le lien : arrivée à X = −548 dans le cadre ; escalier libéré, décalé de +548 en X (deux girons), refixé ; décalage [−2466, −1446,6, 0], pieds à Z = 0 ; reste 1 collision `Poteau milieu arrivée` / `Limon int V1` (3,4 mm) ; hauteur libre au-dessus de V1 sous la poutre d'arrivée : 3588 − 10 h = **1,84 m** ; `cad/escalier.solidcraft` mis à jour depuis `recovery` | `cad/escalier.solidcraft`, `cad/projet_escalier.solidcraft`, `CONCEPTION.md` |
| 2026-10-27 | Export STL du projet et README | `cad/projet_escalier.stl` (binaire, 379 Ko, environnement + escalier) ; nouvel aperçu `cad/apercu.png` (vue côté V1) ; README : lien 3D vers le projet, valeurs 3848 / 16 + 6 / marches 60 mm, mention du calcul non relancé, nouveaux fichiers ; `cad/escalier.stl` réexporté depuis le projet (escalier seul, 16/6, 82 corps, coordonnées du site) | `cad/projet_escalier.stl`, `cad/apercu.png`, `README.md`, `CONCEPTION.md` |
| 2026-10-28 | Audit de CONCEPTION.md, §6 réécrit | FreeCAD retiré (plus utilisé) ; §6 en 5 sous-parties (autorisations, déroulé, tenue du fichier, outils et versions, pièges) ; valeurs périmées corrigées (16/6, 60 mm, palier 2798,5) ; contradictions levées ; §7 : calculs à relancer, effets probables de `palier_ep` 60 à vérifier, hauteur libre 1,84 m | `CONCEPTION.md` |
| 2026-10-28 | Règle des branches | 6.2 : une branche par tâche avant toute modification, fusion dans `main` par l'utilisateur, une seule branche à la fois sur un `.solidcraft` | `CONCEPTION.md` |
| 2026-10-28 | Règles génériques à part | Règles de travail sorties dans `REGLES_AGENT_3D.md` (réutilisable sur d'autres projets 3D) ; §6 réduit aux outils, fichiers et pièges du projet ; pièges dédoublonnés (§4, D13, §7 renvoient au §6.3) ; AGENTS.md et README mis à jour | `REGLES_AGENT_3D.md`, `CONCEPTION.md`, `AGENTS.md`, `README.md` |
| 2026-10-28 | Chasse aux doublons | §2 réduit à l'origine des données ; environnement et projet déplacés à la fin du §4, état des lieux des outils en §6.4 ; §7 ne garde que des points ouverts (renvois à D14 / D15 au lieu des chiffres) ; « en attente » regroupé au §8 ; petits doublons (D9, D11, `poteau_*`, verrou) retirés | `CONCEPTION.md`, `REGLES_AGENT_3D.md` |
| 2026-10-28 | README allégé | Chapitres escalier, calcul, modification et contenu retirés (doublons de CONCEPTION.md) ; ajout de « Comment le projet est fait » (SolidCraft, Claude Code, connecteur MCP, travail à deux) | `README.md`, `CONCEPTION.md` |
| 2026-10-28 | Règle de modélisation | `REGLES_AGENT_3D.md` §6 : toujours préférer une méthode modifiable par un humain (cotes dans les esquisses, paramètres nommés, noms explicites) | `REGLES_AGENT_3D.md`, `CONCEPTION.md` |
| 2026-10-28 | Règle de nommage | `REGLES_AGENT_3D.md` §6 : renommer tout élément créé avec un nom explicite, jamais le nom par défaut | `REGLES_AGENT_3D.md`, `CONCEPTION.md` |
| 2026-10-28 | Règles de modélisation | `REGLES_AGENT_3D.md` §6 : squelette, esquisses à 0 DDL, un corps par pièce, réseaux, symétries, matériau à la création, simplifications déclarées | `REGLES_AGENT_3D.md`, `CONCEPTION.md` |
| 2026-10-28 | Exports à jour | `REGLES_AGENT_3D.md` §2 étape 6 : régénérer les exports avant de proposer la fusion ; « fusion (merge) » ; contrôle GitHub Actions `.github/workflows/exports.yml` qui met en échec une PR modifiant un `.solidcraft` sans ses exports ; D7 renvoie au contrôle | `REGLES_AGENT_3D.md`, `CONCEPTION.md`, `.github/workflows/exports.yml` |
| 2026-10-28 | Exports : géométrie seulement | Étape 6 limitée aux changements de géométrie 3D ; étiquette `geometrie-inchangee` sur la PR pour passer le contrôle | `REGLES_AGENT_3D.md`, `.github/workflows/exports.yml`, `CONCEPTION.md` |
| 2026-10-28 | Contrôle GitHub abandonné | `.github/workflows/exports.yml` supprimé (choix de l'utilisateur) ; la règle des exports reste ; D7 liste les exports et ce qui les touche | `REGLES_AGENT_3D.md`, `CONCEPTION.md` |
| 2026-10-28 | Arborescence du dépôt | `REGLES_AGENT_3D.md` §7 : arborescence type et création de celle d'un nouveau projet (ce qui manque seulement, squelette de CONCEPTION.md) | `REGLES_AGENT_3D.md`, `CONCEPTION.md` |
| 2026-10-28 | Arborescence : création retirée | Partie « Créer l'arborescence d'un nouveau projet » supprimée de `REGLES_AGENT_3D.md` §7 (choix de l'utilisateur) | `REGLES_AGENT_3D.md`, `CONCEPTION.md` |
| 2026-10-28 | Plan du fichier de conception | `REGLES_AGENT_3D.md` §3 : tableau des 9 chapitres de CONCEPTION.md et de leur contenu | `REGLES_AGENT_3D.md`, `CONCEPTION.md` |
| 2026-10-28 | Corrections de l'audit des règles | `REGLES_AGENT_3D.md` : §1 renommé « Principes », ajout « aucune donnée inventée » et « statut des calculs » ; §2 : rien n'est écrit avant la branche, ordre réaliser → exports → documenter → enregistrer, demande de fusion définie | `REGLES_AGENT_3D.md`, `CONCEPTION.md` |
| 2026-10-28 | Règles indépendantes de Git | `REGLES_AGENT_3D.md` : quatre notions (version de travail, enregistrer, version de référence, valider) avec leur équivalent Git / PLM / gestionnaire de fichiers ; vocabulaire Git retiré des règles ; « Arborescence du projet » ; CONCEPTION §6.5 : gestion des versions du projet (Git) | `REGLES_AGENT_3D.md`, `CONCEPTION.md` |
| 2026-10-28 | « Versions des logiciels » | Renommage pour ne plus confondre avec la version de référence du projet : `REGLES_AGENT_3D.md` §1, §2, §3, §4 (« Logiciels et leurs versions »), CONCEPTION §6.1 | `REGLES_AGENT_3D.md`, `CONCEPTION.md` |
| 2026-10-28 | Relecture des règles | `REGLES_AGENT_3D.md` : « logiciels » partout au lieu de « outils » pour les versions, « enregistrement du modèle », « enregistrer une version » à l'étape 6, README « si ce qu'il décrit change », noms des chapitres de conception communs aux projets ; CONCEPTION §6.1 et §6.4 alignés | `REGLES_AGENT_3D.md`, `CONCEPTION.md` |
| 2026-10-29 | Impacts de la mise à jour documentaire sur le 3D | Écarts constatés (16/6, 82 corps, 0 erreur, 0 interférence, SolidCraft 0.24.1) : avec le palier à 60 mm, trous hauts V2 de la poutre avant dans le pied de l'aile haute (≈ 8 mm, avertissement booléen), platines côté palier plus courtes que la poutre (V1 9,5 mm, V2 28,6 mm). Corrigé (choix de l'utilisateur) : `boulons_entraxe` 100 → 80 ; trous côté palier (platines V1, V2 et poutre avant) centrés sur le milieu de la poutre ; `Profil platine V1` et `Profil platine palier V2` redessinés (mêmes ids), bas au bas de la poutre ; trous d'arrivée restés centrés sur leur platine ; avertissement disparu, 0 erreur, 0 interférence dans l'escalier ; tests `nb_volee1` 16 → 15 → 16 et `marche_epaisseur` 60 → 40 → 60 OK ; projet : liens mis à jour, seule collision `Poteau milieu arrivée` / `Limon int V1` (déjà connue) ; STL régénérés, `cad/apercu.png` gardé (changement invisible à cette échelle) | `cad/escalier.solidcraft`, `cad/projet_escalier.solidcraft`, `cad/escalier.stl`, `cad/projet_escalier.stl`, `CONCEPTION.md` |
| 2026-10-29 | Recentrer les limons sur la poutre avant (montage des boulons difficile) | `limon_dessus` 0 → `-30 mm * giron / pas_volee` (D17) ; platines côté palier revenues à la section du limon (6 platines identiques), trous côté palier toujours centrés sur la poutre ; `boulons_entraxe` 80 → 100 ; V1 centré (2498 → 2759), V2 à +19 mm ; platine V2 côté palier 20 mm sous le plancher ; 0 erreur, 0 avertissement, 0 interférence ; tests `nb_volee1` 16 → 15 → 16, `marche_epaisseur` 60 → 40 → 60 OK ; projet : liens mis à jour, seule collision `Poteau milieu arrivée` / `Limon int V1` (déjà connue) ; STL régénérés, `cad/apercu.png` gardé | `cad/escalier.solidcraft`, `cad/projet_escalier.solidcraft`, `cad/escalier.stl`, `cad/projet_escalier.stl`, `CONCEPTION.md` |
| 2026-10-29 | Refonte des esquisses (règles de `REGLES_AGENT_3D.md` §6) — constat | 16 esquisses en points définis par expression, sans cote (108 points) : limons (4), platines (4), plancher, pieds, cadre (8) ; elles ne s'appuient pas sur le squelette ; 77 paramètres sur 108 au nom par défaut (`dN`) ; 0 DDL partout, noms d'esquisses / fonctions / corps explicites | `CONCEPTION.md` |
| 2026-10-29 | Refonte des esquisses — réalisé | Paramètres ajoutés `rive_x`, `cadre_y`, `limon_hv` ; 16 esquisses redessinées en lignes cotées (mêmes identifiants de courbes) : plancher, pieds (4 tubes), cadre (8 trapèzes, onglets cotés 45°), 4 platines (rectangles), 4 limons (ligne des nez du squelette projetée en construction, bords parallèles cotés) ; 194 cotes renommées `<pièce>_<rôle>` (les 50 paramètres de fonctions `dN` ont été oubliés, corrigé le 2026-10-29 sur la branche `limons-frame-member`) ; 82 corps identiques à la référence (volumes et encombrements), 0 erreur ; balayages sans échec de `nb_volee1` 14–18, `giron`, `hauteur_totale`, `marche_epaisseur`, `limon_h`, `limon_dessus` (−50 / 0 / 20), `emmarchement`, `platine_ep`, `boulons_entraxe`, `limon_tf`, `palier_profondeur`, `jeu_limons`, `poteau_cote`, `limon_b` ; contrôle à `giron` 300 / `limon_dessus` 20 : platines et limons jointifs, 0 interférence ; projet : lien mis à jour, seule collision connue ; géométrie inchangée → exports non régénérés | `cad/escalier.solidcraft`, `cad/projet_escalier.solidcraft`, `CONCEPTION.md` |
| 2026-10-29 | Prototype : limon V1 en Frame Member | Paramètre `limon_r` ; `Axe limon V1`, `Barre limon V1` (profilé channel), `Coupes limon V1`, `Coupe limon V1` insérés avant la platine V1 ; anciennes esquisses `Profil limon V1` / `Profil ailes limon V1` supprimées ; corps renommé `Limon ext V1`, `Symétrie limon V1` mise à jour, acier ; encombrement identique, volume +2,2 % (congés) ; 0 erreur, 0 interférence ; balayages `nb_volee1`, `giron`, `limon_dessus`, `limon_h`, `limon_r`, `hauteur_totale` sans échec ; 59 paramètres `dN` restants renommés (50 de fonctions oubliés par la refonte, 9 nouveaux) ; fichier rouvert identique ; projet et exports pas encore mis à jour (prototype) | `cad/escalier.solidcraft`, `CONCEPTION.md` |
