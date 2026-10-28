# Règles de travail avec l'agent — projet de conception 3D

Règles génériques, valables pour tout projet de conception 3D : ce fichier se copie tel quel d'un projet à l'autre. Tout ce qui est propre au projet (versions de référence, dossier de travail du connecteur, fichiers liés, pièges) est dans le **fichier de conception** (ici [CONCEPTION.md](CONCEPTION.md), chapitre « Outils et pièges du projet »).

## 1. Autorisations et réponses

- **Libre, sans demander** : lire les fichiers du dépôt, inspecter le modèle (paramètres, corps, erreurs, mesures, interférences), `git status / diff / log`.
- **Avec accord explicite** : toute modification du modèle 3D, tout enregistrement, la copie d'un fichier vers le dépôt, commit et push, l'installation de logiciels, le lancement des calculs ou simulations. Les calculs ne sont **jamais relancés automatiquement**, même après un changement de paramètre.
- **Plan validé** : l'agent annonce un plan numéroté ; le « oui » de l'utilisateur couvre tout le plan. Au moindre écart (imprévu, erreur, étape non prévue), l'agent s'arrête et redemande.
- **Réponses synthétiques** : le résultat d'abord, puis seulement ce qui demande une décision de l'utilisateur. Phrases et listes courtes, pas de redite du fichier de conception ni d'options qu'on ne retient pas ; le détail va dans le fichier, pas dans la réponse.

## 2. Déroulé d'une tâche

1. **Constater** : relever les versions des outils et les comparer aux versions de référence (§4) ; relever l'état du modèle (paramètres pilotes, nombre de corps, erreurs) et le comparer au fichier de conception. Les écarts (modifications faites à la main entre deux sessions) sont notés dans l'historique **avant** toute autre action.
2. **Proposer** le plan, attendre le « oui ».
   Puis, **avant toute modification**, créer une branche depuis `main` à jour (nom court de la tâche). Jamais de commit direct sur `main` : c'est l'utilisateur qui fusionne (merge), après avoir relu le diff du fichier de conception. Une seule branche ouverte à la fois touchant un fichier binaire (modèle 3D) : Git ne sait pas les fusionner.
3. **Réaliser**, puis **tester** : faire varier un ou deux paramètres concernés puis revenir, 0 erreur. Si une pièce d'un assemblage a changé : mettre à jour les liens, puis contrôler les interférences.
4. **Enregistrer** (dossier de travail du connecteur → dépôt → commit sur la branche), ou écrire explicitement « non enregistré » dans l'historique.
5. **Documenter** : mettre à jour le fichier de conception (et le README si un chiffre qu'il cite change), ajouter une ligne à l'historique.
6. **Exports** : avant de proposer la fusion, régénérer sur la branche les exports versionnés (STL, aperçus, plans…) qui montrent le modèle modifié. Le fichier de conception dit lesquels et où est le contrôle automatique, s'il y en a un.

## 3. Tenue du fichier de conception

- **Une information, un seul endroit** : la valeur d'un paramètre n'est écrite que dans le tableau des paramètres ; ailleurs, on cite le paramètre par son nom. Une cote dérivée n'est recopiée que si elle est utile, avec la configuration pour laquelle elle vaut. Un piège n'est décrit que dans la liste des pièges ; ailleurs, on y renvoie.
- Seul l'historique garde des valeurs datées ; il n'est jamais réécrit.
- **Calculs périmés** : dès qu'un paramètre utilisé par un calcul change, ajouter en tête des points ouverts « Calculs à relancer : <paramètres changés> (calcul fait en <configuration>) ». La ligne est retirée quand l'utilisateur relance les calculs.
- Le modèle 3D étant binaire, **le fichier de conception tient lieu de diff lisible** : toute modification du modèle doit y être décrite.

## 4. Outils et versions

- Le fichier de conception tient le **tableau des versions de référence** : outil, rôle, version, commande pour la vérifier.
- **État des lieux à chaque mise à jour** : pour chaque outil dont la version a changé, lire les notes de version intermédiaires, les croiser avec les contournements et les pièges du projet, noter ce qui peut changer à côté du tableau des versions, puis mettre à jour la référence. Tester seulement avec accord.
- Un changement de version du logiciel de CAO peut changer le format de fichier ; un changement des bibliothèques de calcul peut changer les résultats : ajouter alors la ligne « Calculs à relancer ».
- **Fichiers liés** (assemblages) : les garder ensemble, liens en chemins relatifs.
- **Session sans accès au logiciel de CAO** (agent dans le cloud, autre poste) : elle a ses propres versions d'outils, on n'y fait pas d'état des lieux ; elle sert à la doc, aux calculs et aux audits. Le 3D se fait sur le poste qui a le logiciel ; le dépôt fait le lien.

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
