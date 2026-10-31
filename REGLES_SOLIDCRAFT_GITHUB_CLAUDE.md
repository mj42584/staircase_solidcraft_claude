# Règles de travail — SolidCraft + GitHub + Claude Code

Version spécialisée des règles génériques ([REGLES_AGENT_3D.md](https://github.com/mj42584/cad-agent-rules/blob/main/REGLES_AGENT_3D.md), dépôt `cad-agent-rules`) pour un seul outillage : modèle dans SolidCraft piloté par son connecteur MCP, dépôt GitHub, agent Claude Code. Ce qui est propre au projet est dans `CONCEPTION.md`.

## 1. Qui décide

- **Sans demander** : lire le dépôt, inspecter le modèle (`inspect_design`, `measure`, `body_topology`, `screenshot`, interférences), lire l'historique Git et les PR.
- **Le « oui » au plan couvre tout le plan**, y compris enregistrer, commiter et pousser sur la branche de la tâche : tout y est réversible. Au moindre écart (erreur, étape imprévue), s'arrêter et redemander.
- **Toujours demander** : installer un logiciel, lancer un calcul (jamais relancé automatiquement), toucher à `main`.
- **Fusion** : toujours par l'utilisateur.
- **Aucune donnée inventée** : une valeur non fournie est demandée, ou notée « supposé ». Les calculs de l'agent sont des ordres de grandeur, jamais une note de calcul.

## 2. Réponses

- **Cinq lignes au plus** : le résultat, puis ce qui demande une décision. Pas de récapitulatif de ce qui a été fait étape par étape, pas de liste de fichiers, pas de redite de `CONCEPTION.md`.
- Le détail (mesures, balayages, volumes) va dans la description de la PR, pas dans la réponse.
- Un plan tient en une liste numérotée courte ; une question à la fois.

## 3. Déroulé d'une tâche

1. **Constater** : version de SolidCraft (`flatpak info --user io.tangencylabs.solidcraft`), modèle ouvert, nombre de corps, erreurs. Signaler seulement les écarts avec `CONCEPTION.md`.
2. **Plan** → « oui » → branche depuis `main` à jour (nom court de la tâche). Git ne fusionne pas les modèles (binaires) : une seule branche à la fois touche un modèle.
3. **Réaliser** par lots (`batch`), puis **tester** : faire varier un ou deux paramètres concernés puis revenir, 0 erreur, 0 interférence. Le projet d'assemblage n'est pas ouvert : il relit le modèle lié à sa prochaine ouverture, et les interférences avec l'environnement se contrôlent à la demande.
   Les variations de paramètres se font **en ligne de commande** (§5), sur une copie du modèle enregistré, en arrière-plan : l'app reste libre et le modèle ouvert n'est pas touché. Les interférences se contrôlent dans l'app (`inspect.interference`).
4. **Enregistrer** (§4) avant les tests en ligne de commande, puis en fin de tâche ; mettre à jour `CONCEPTION.md`, commit, push, ouvrir la PR. La description de la PR est le compte rendu complet ; elle dit aussi ce qui n'est pas fait ou pas vérifié.

Tâche non terminée enregistrée à la demande : PR en brouillon (*draft*), et ce qui reste suspendu ou non vérifié dans les points ouverts.

## 4. Enregistrer

Le connecteur n'enregistre que dans les dossiers qu'on lui autorise. Lancer le serveur MCP avec `--allow-path <projet>/cad` pour enregistrer **directement dans `cad/`**, sans passer par le dossier `recovery` ni copier (sans cette option, il n'écrit que dans `~/.var/app/io.tangencylabs.solidcraft/data/solidcraft/recovery` et dans le dossier d'un modèle ouvert).

À chaque enregistrement, dans cet ordre :

1. `save {path: "<projet>/cad/<modèle>.solidcraft"}` : le seul format enregistré ; l'app continue sur ce fichier, pas besoin de le rouvrir.
2. Un commit qui contient le modèle et `CONCEPTION.md`.

Pas de `.json` ni d'exports (STL, STEP, images) dans le dépôt : ils se font à la demande, hors commit (`.gitignore`). Le modèle étant binaire, `CONCEPTION.md` et la description de la PR sont la seule trace lisible de ses modifications.

Chemins absolus. Le fichier courant se lit dans le retour de `open` ou de `save` (`inspect_design` donne `path: null`). Chaque `save` garde la version précédente en `<fichier>.bak`, en écrasant le `.bak` existant : ne rien laisser d'utile sous ce nom. Ne pas commiter les `*.bak` ni les verrous `.~*.lock` (`.gitignore`).

## 5. Tester en ligne de commande

`solidcraft-cli` est livré dans le Flatpak de SolidCraft. `run` rejoue un script sur une **copie** du modèle et n'enregistre rien ; il échoue si une fonction casse.

- Script : `{"commands": [{"command": "parameters.change", "params": {"name": "<paramètre>", "expression": "<valeur>"}}, …]}`, l'aller puis le retour.
- Commande, lancée en arrière-plan : `flatpak run --user --filesystem=<dossier du script> --command=solidcraft-cli io.tangencylabs.solidcraft run <script.json> --in "<projet>/cad/<modèle>.solidcraft" --results --timings --json-out <résultat.json>`. Sans `--filesystem`, le Flatpak ne voit pas `/tmp`.
- Lire dans le résultat les `errors` de chaque étape.
- Ce n'est pas plus rapide que dans l'app : le modèle est recalculé une fois à l'ouverture, puis à chaque changement. Lancer plusieurs scripts en parallèle (un par paramètre) fait gagner un peu.
- Le modèle testé est celui **enregistré** : enregistrer avant de tester.

## 6. `CONCEPTION.md`

Il est relu à chaque session : le garder court.

- **Paramètres** : valeur seulement dans le tableau des paramètres ; ailleurs, on cite le nom.
- **Décisions** : D1, D2… en deux ou trois lignes, la décision et son pourquoi.
- **Pièges** : ceux du modèle seulement (ceux de SolidCraft sont au §8), une ligne par piège (symptôme → contournement, version). L'enquête va dans une issue (chez SolidCraft si c'est un bug), avec le lien dans la ligne.
- **Points ouverts** : en tête, « Calculs à relancer : <paramètres> » dès qu'un paramètre utilisé par un calcul change.
- **Historique** : une ligne par PR, avec date, titre et lien. Le détail est dans la PR.

## 7. Modélisation

- **Modifiable à la main** : des cotes pilotées par des paramètres nommés, pas de points définis par expression ni de valeurs en dur. Une ligne projetée dans une esquisse de profil passe en construction (`sketch.construction`), sinon elle peut couper le profil.
- **Tout renommer tout de suite** : esquisses, fonctions, corps, plans, et tous les paramètres, y compris ceux des fonctions (extrusions, décalages, réseaux), qu'on liste avec `parameters.list {filter: all}` (ils n'apparaissent pas dans `inspect_design`). Cotes nommées `<pièce>_<rôle>` (ex. `limon_v1_bas`). Renommer par petits lots : chaque renommage relance le recalcul.
- **Squelette** : s'appuyer sur des esquisses maîtresses et des plans pilotés, jamais sur les faces d'autres corps.
- **Esquisses à 0 degré de liberté.**
- **Un corps par pièce réelle**, avec son matériau dès sa création ; un corps qui apparaît plus tard (copie de réseau au-delà du nombre affecté) reste en « Default » : l'affecter.
- **Réseaux et symétries** pilotés par des paramètres plutôt que des copies ; de préférence la symétrie du corps entier.
- **Simplifications déclarées** dans `CONCEPTION.md`.

## 8. Quand SolidCraft résiste

- **Recalcul lent** : regrouper les fonctions lentes dans un dossier de la timeline et le suspendre (`timeline.suppress`) pendant les modifications ; le réactiver avant de tester.
- **Commande qui ne répond pas** (`still running:`) : ne pas la renvoyer, attendre avec `pending`.
- **Plantage** : récupérer la sauvegarde automatique, puis reprendre à l'étape « Constater ».
- **Nouvelle version de SolidCraft** : ouvrir chaque modèle, comparer le nombre de corps, les erreurs et les volumes, puis les réenregistrer. Le format de fichier change souvent : une version plus ancienne n'ouvre plus le fichier.

**Pièges connus** (0.27.1 sauf mention ; une ligne par piège, symptôme → contournement) :

- Contrainte verticale ou horizontale : commande `sketch.constraint.horizontal_vertical` (`mode`) ; il n'y a pas de `sketch.constraint.vertical`.
- Esquisse sur un plan décalé de XZ : l'axe vertical de l'esquisse va vers −Z, les coordonnées Z s'écrivent en négatif ; les cotes restent des distances positives.
- Point défini par une expression : pour le libérer, supprimer la ligne et la redessiner avec l'option `ids` (même identifiant, un Frame Member la retrouve) ; Fix/UnFix et le déplacement ne suffisent pas.
- La commande d'oblong n'accepte pas d'expressions : dessiner des rainures cotées.
- Union de deux corps en contact face contre face (tube mince sur une platine, balayage bout à bout d'une barre) : échec (`boolean Union: no result`) ou corps à 2 coques (`kernel.shells` = 2 dans `measure`) → faire pénétrer l'un dans l'autre (1 à 3 mm), ou faire repartir le balayage du début de la barre.
- Profilés avec congés (UPE…) : les booléens qui les percent reprennent (« Boolean retry ») et ralentissent le recalcul → congés à 0 si la section exacte n'est pas utile au modèle.
- Un réseau qui répète plusieurs corps numérote ses copies à la suite en les mélangeant : les noms (et les matériaux affectés par nom) tombent sur les mauvais corps → un réseau par corps.
- Depuis le Frame Member, l'enregistrement n'écrit plus le cache de géométrie : l'ouverture recalcule tout (cause non établie).
- Assemblage : `component.relink` n'accepte qu'un `.solidcraft` ; `component.insert_design` et `occurrence.move` ne prennent qu'un décalage chiffré (une pièce ne suit pas ses paramètres, la recaler à la main) ; les matériaux des composants liés n'y passent pas (« Default », masse fausse).
- Lister les commandes de liaison (`list_commands` filtre `joint`) a semblé faire planter l'app (0.22) : à éviter tant que ce n'est pas vérifié.
