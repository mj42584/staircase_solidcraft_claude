# Règles de travail avec l'agent — projet de conception 3D

Règles génériques, valables pour tout projet de conception 3D : ce fichier se copie tel quel d'un projet à l'autre. Tout ce qui est propre au projet (versions des logiciels, outil de gestion des versions, dossier de travail du connecteur, fichiers liés, pièges) est dans le **fichier de conception** ([CONCEPTION.md](CONCEPTION.md), chapitre « Outils et pièges du projet ») ; ses chapitres portent les mêmes noms d'un projet à l'autre (§3).

## 1. Principes

- **Libre, sans demander** : lire les fichiers du projet, inspecter le modèle (paramètres, corps, erreurs, mesures, interférences), consulter l'historique des versions.
- **Avec accord explicite** : toute modification du modèle 3D, tout enregistrement du modèle, la copie d'un fichier vers le projet, l'enregistrement d'une version, l'installation de logiciels, le lancement des calculs ou simulations. Les calculs ne sont **jamais relancés automatiquement**, même après un changement de paramètre.
- **Plan validé** : l'agent annonce un plan numéroté ; le « oui » de l'utilisateur couvre tout le plan. Au moindre écart (imprévu, erreur, étape non prévue), l'agent s'arrête et redemande.
- **Aucune donnée inventée** : une donnée non fournie (cote, matériau, charge, nuance d'acier…) est demandée à l'utilisateur, ou utilisée avec la mention « supposé » dans le fichier de conception, jamais présentée comme acquise.
- **Statut des calculs** : les calculs de l'agent sont des ordres de grandeur ; ne jamais les présenter comme une note de calcul validée, qui reste l'affaire d'un bureau d'études.
- **Réponses synthétiques** : le résultat d'abord, puis seulement ce qui demande une décision de l'utilisateur. Phrases et listes courtes, pas de redite du fichier de conception ni d'options qu'on ne retient pas ; le détail va dans le fichier, pas dans la réponse.

## 2. Déroulé d'une tâche

**Gestion des versions** : ces règles valent avec Git, un PLM ou un simple gestionnaire de fichiers. Elles parlent de quatre notions ; le fichier de conception dit quel outil le projet utilise et comment chacune s'y fait.

| Notion | Git | PLM | Gestionnaire de fichiers |
|---|---|---|---|
| **Version de travail** : on modifie sans toucher la référence | branche | extraction (*check-out*) | copie dans un dossier de travail |
| **Enregistrer une version** | commit + push | nouvelle révision (*check-in*) | copie datée ou indicée |
| **Version de référence** | `main` | révision libérée | dossier « validé » |
| **Valider** : l'utilisateur relit puis intègre | fusion (merge) | processus d'approbation | copie vers le dossier « validé » par l'utilisateur |

1. **Constater** : relever les versions des logiciels et les comparer à celles du fichier de conception (§4) ; relever l'état du modèle (paramètres pilotes, nombre de corps, erreurs) et le comparer au fichier de conception, pour repérer les modifications faites à la main entre deux sessions. Rien n'est encore écrit.
2. **Proposer** le plan, avec les écarts constatés, et attendre le « oui ».
   Puis, **avant toute modification**, créer une **version de travail** depuis la version de référence à jour (nom court de la tâche). Jamais de modification directe de la version de référence : c'est l'utilisateur qui valide, après avoir relu les modifications du fichier de conception. Une seule version de travail à la fois sur un fichier binaire (modèle 3D) : deux versions modifiées en parallèle ne se fusionnent pas.
   Première écriture dans la version de travail : les écarts constatés, dans l'historique.
3. **Réaliser**, puis **tester** : faire varier un ou deux paramètres concernés puis revenir, 0 erreur. Si une pièce d'un assemblage a changé : mettre à jour les liens, puis contrôler les interférences.
4. **Exports** (liste dans le fichier de conception) : si la **géométrie 3D** a changé, les régénérer. Pas pour une modification sans effet sur la géométrie (renommage, matériau, réorganisation de l'arbre) : le noter dans l'historique.
5. **Documenter** : mettre à jour le fichier de conception (et le README si ce qu'il décrit change), ajouter une ligne à l'historique.
6. **Enregistrer** (dossier de travail du connecteur → projet → enregistrer une version), ou écrire explicitement « non enregistré » dans l'historique. Puis **proposer la validation** : un message à l'utilisateur qui résume ce que contient la version de travail (ou la demande prévue par l'outil : pull request, processus d'approbation…). Si l'agent n'a pas accès à l'outil de gestion des versions, il prépare les fichiers et l'utilisateur enregistre.

## 3. Tenue du fichier de conception

**Plan du fichier** (`CONCEPTION.md`) :

| Chapitre | Contenu |
|---|---|
| 1. Objectif | Ce qu'on conçoit et ce qui doit être paramétrable |
| 2. Données d'entrée | Origine des données (mesures sur site, valeurs de départ, catalogues) ; les valeurs actuelles sont au chapitre 3 |
| 3. Paramètres du modèle | Pilotes (valeur, ce qu'ils pilotent) et calculés (expression, valeur) : seul endroit où les valeurs sont écrites |
| 4. Architecture du modèle | Repère, arbre de construction, environnement et assemblage |
| 5. Journal des décisions | D1, D2… : la décision et son pourquoi |
| 6. Outils et pièges du projet | Versions des logiciels, fichiers et dossiers, pièges connus, état des lieux des logiciels, gestion des versions |
| 7. Points ouverts | En tête, « Calculs à relancer » s'il y a lieu ; ensuite seulement des questions non tranchées |
| 8. Prochaines étapes | Liste fixée par l'utilisateur, et ce qui est en attente |
| 9. Historique | Tableau date / demande / réalisé / fichiers |

- **Une information, un seul endroit** : la valeur d'un paramètre n'est écrite que dans le tableau des paramètres ; ailleurs, on cite le paramètre par son nom. Une cote dérivée n'est recopiée que si elle est utile, avec la configuration pour laquelle elle vaut. Un piège n'est décrit que dans la liste des pièges ; ailleurs, on y renvoie.
- Seul l'historique garde des valeurs datées ; il n'est jamais réécrit.
- **Calculs périmés** : dès qu'un paramètre utilisé par un calcul change, ajouter en tête des points ouverts « Calculs à relancer : <paramètres changés> (calcul fait en <configuration>) ». La ligne est retirée quand l'utilisateur relance les calculs.
- Le modèle 3D étant binaire, **le fichier de conception tient lieu de description lisible des modifications** : toute modification du modèle doit y être décrite. Sans outil de gestion des versions, il en est la seule trace.

## 4. Logiciels et leurs versions

- Le fichier de conception tient le **tableau des versions des logiciels** : logiciel, rôle, version, commande pour la vérifier.
- **État des lieux à chaque mise à jour** : pour chaque logiciel dont la version a changé, lire les notes de version intermédiaires, les croiser avec les contournements et les pièges du projet, noter ce qui peut changer à côté du tableau des versions des logiciels, puis mettre à jour ce tableau. Tester seulement avec accord.
- Un changement de version du logiciel de CAO peut changer le format de fichier ; un changement des bibliothèques de calcul peut changer les résultats : ajouter alors la ligne « Calculs à relancer ».
- **Fichiers liés** (assemblages) : les garder ensemble, liens en chemins relatifs.
- **Session sans accès au logiciel de CAO** (agent dans le cloud, autre poste) : elle a ses propres versions des logiciels, on n'y fait pas d'état des lieux ; elle sert à la doc, aux calculs et aux audits. Le 3D se fait sur le poste qui a le logiciel ; l'outil de gestion des versions fait le lien.

## 5. Pièges

Le fichier de conception tient la liste des pièges du projet, une ligne par piège : le symptôme, le contournement, et la version à partir de laquelle il est peut-être corrigé.

## 6. Modélisation

- **Un modèle modifiable par un humain** : toujours préférer la méthode qu'un utilisateur peut reprendre à la main dans le logiciel de CAO, même si une autre est plus rapide pour l'agent. Par exemple : dans les esquisses, des **cotes** pilotées par des paramètres plutôt que des points calculés par expression ; des paramètres nommés plutôt que des valeurs en dur.
- **Tout renommer** : chaque élément créé (esquisse, fonction, corps, plan, paramètre, composant) reçoit tout de suite un nom explicite qui dit ce qu'il est et où il est (ex. `Profil limon V1`, `Limon ext V2`), jamais le nom par défaut du logiciel (`Sketch3`, `Extrude12`). Un humain doit pouvoir s'y retrouver dans l'arbre sans lire le fichier de conception.
- **Construire depuis un squelette** : la géométrie s'appuie sur des esquisses maîtresses et des plans de référence pilotés par les paramètres, jamais sur les faces ou arêtes d'autres corps, qui changent ou disparaissent quand un paramètre change.
- **Esquisses entièrement contraintes** (0 degré de liberté) : sinon elles peuvent bouger sans prévenir au recalcul.
- **Un corps par pièce réelle** : chaque pièce fabriquée ou achetée est un corps séparé ; c'est ce qui permet la nomenclature, les matériaux et le contrôle des interférences.
- **Répéter plutôt que copier** : un élément répété est produit par un réseau dont le nombre et le pas sont pilotés par des paramètres, pas par des copies indépendantes.
- **Symétriser plutôt que redessiner** : une pièce symétrique d'une autre est produite par une symétrie par rapport à un plan de référence, pas redessinée ; de préférence la symétrie du corps entier, plus robuste que celle des fonctions (qui peuvent se joindre au corps d'origine).
- **Matériau à la création** : affecter le matériau dès qu'un corps est créé.
- **Simplifications déclarées** : ne modéliser que ce qui sert (pas de visserie détaillée ni de congés sauf demande) ; toute simplification est notée dans le fichier de conception avec son effet (masse, section…).
- Quand le logiciel impose une méthode moins lisible, la noter comme contournement dans les pièges du projet.

## 7. Arborescence du projet

| Chemin | Contenu |
|---|---|
| `README.md` | Vitrine : ce qu'est le projet, image, vue 3D, comment il est fait |
| `AGENTS.md` | Point d'entrée d'un agent : ordre de lecture |
| `REGLES_AGENT_3D.md` | Ces règles |
| `CONCEPTION.md` | Fichier de conception : état du projet, décisions, outils, pièges, historique |
| `cad/` | Modèles 3D (pièces, environnement, assemblage) et leurs exports (STL, aperçus, plans) |
| `calc/` | Scripts de calcul ; `calc/rapport/` : rapport de calcul et figures |
| `archive/` | Anciennes versions et fichiers d'origine, jamais modifiés |

Un nouveau type de fichier va dans le dossier existant qui lui correspond ; créer un dossier seulement si aucun ne convient, et l'ajouter à ce tableau. Si l'outil de gestion des versions (un PLM) impose sa propre structure, le fichier de conception dit où se trouve chaque élément.
