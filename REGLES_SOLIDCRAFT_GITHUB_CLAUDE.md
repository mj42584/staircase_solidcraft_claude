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
   Les variations de paramètres se font avec l'outil `check_parameters {set: {<paramètre>: <valeur>, …}, report: ["errors"]}` (0.29) : il essaie les valeurs dans l'app puis remet le modèle ; ou **en ligne de commande** (§5), sur une copie du modèle enregistré, en arrière-plan, pour garder l'app libre. Un lot de construction porte un `expect {volume_mm3, bodies, bbox}` quand on connaît le résultat attendu. Les interférences se contrôlent dans l'app (`inspect.interference`).
4. **Enregistrer** (§4) avant les tests en ligne de commande, puis en fin de tâche ; mettre à jour `CONCEPTION.md`, commit, push, ouvrir la PR. La description de la PR est le compte rendu complet ; elle dit aussi ce qui n'est pas fait ou pas vérifié.

Tâche non terminée enregistrée à la demande : PR en brouillon (*draft*), et ce qui reste suspendu ou non vérifié dans les points ouverts.

## 4. Enregistrer

Le connecteur n'enregistre que dans les dossiers qu'on lui autorise. Lancer le serveur MCP avec `--allow-path <projet>/cad` pour enregistrer **directement dans `cad/`**, sans passer par le dossier `recovery` ni copier (sans cette option, il n'écrit que dans `~/.var/app/io.tangencylabs.solidcraft/data/solidcraft/recovery` et dans le dossier d'un modèle ouvert).

À chaque enregistrement, dans cet ordre :

1. `file.save {path: "<projet>/cad/<modèle>.solidcraft", cache: false, overwrite: true}` (par `execute`) : le seul format enregistré ; l'app continue sur ce fichier, pas besoin de le rouvrir. Sans `cache: false`, le cache de géométrie est écrit (fichier ×13) ; `overwrite` est nécessaire quand Git a réécrit le fichier (changement de branche).
2. Un commit qui contient le modèle et `CONCEPTION.md`.

Pas de `.json` ni d'exports (STL, STEP, images) dans le dépôt : ils se font à la demande, hors commit (`.gitignore`). Le modèle étant binaire, `CONCEPTION.md` et la description de la PR sont la seule trace lisible de ses modifications.

Chemins absolus. Le fichier courant se lit dans le retour de `open` ou de `save` (`inspect_design` donne `path: null`). Chaque `save` garde la version précédente en `<fichier>.bak`, en écrasant le `.bak` existant : ne rien laisser d'utile sous ce nom. Ne pas commiter les `*.bak` ni les verrous `.~*.lock` (`.gitignore`).

## 5. Tester en ligne de commande

`solidcraft-cli` est livré dans le Flatpak de SolidCraft. `run` rejoue un script sur une **copie** du modèle et n'enregistre rien ; il échoue si une fonction casse.

- Script : `{"commands": [{"command": "parameters.change", "params": {"name": "<paramètre>", "expression": "<valeur>"}}, …]}`, l'aller puis le retour.
- Commande, lancée en arrière-plan : `flatpak run --user --filesystem=<dossier du script> --command=solidcraft-cli io.tangencylabs.solidcraft run <script.json> --in "<projet>/cad/<modèle>.solidcraft" --results --timings --json-out <résultat.json>`. Sans `--filesystem`, le Flatpak ne voit pas `/tmp`.
- Lire dans le résultat les `errors` de chaque étape. Pour placer une pièce posée plusieurs fois, `occurrence.properties` (bbox de l'exemplaire) avant et après.
- Mesurer la vitesse : `inspect.parameter_sweep {parameter, values}` donne la durée de recalcul de chaque valeur (`ms`) ; `document.inspect` celle de chaque fonction à l'ouverture.
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
- **Un corps par pièce réelle**, y compris dans un ensemble soudé, avec son matériau dès sa création ; un corps qui apparaît plus tard (copie de réseau au-delà du nombre affecté) reste en « Default » : l'affecter.
- **Réseaux et symétries** pilotés par des paramètres plutôt que des copies, pour les pièces de la racine (marches…) ; de préférence la symétrie du corps entier, et un réseau par corps.
- **Simplifications déclarées** dans `CONCEPTION.md`.

### Ensembles (depuis 2026-11-01)

- **Pièces soudées entre elles = un sous-composant** de type « inseparable » (`component.metadata.set {bom_type: inseparable}`) : une ligne de nomenclature, ses pièces dessous. Il porte **ses esquisses, plans et fonctions**, pas seulement ses corps.
- **Repère propre** : construire l'ensemble à l'origine du composant (origine sur sa face d'appui ou un angle utile, plans inclinés par `construct.plane.at_angle` si besoin), avec les paramètres globaux du modèle ; puis le poser.
- **Pièce identique répétée = un seul composant posé N fois** (`occurrence.copy`, puis `occurrence.move` avec une matrice), pas un réseau ni une symétrie de corps : une seule pièce à calculer et à modifier (recalcul ≈ 3,5 fois plus rapide sur l'escalier). Le nombre d'exemplaires devient fixe : le dire à l'utilisateur avant.
- **Chaque exemplaire est lié** par une liaison rigide `joint.as_built` à la géométrie qui le pilote, sur un ensemble ancré : `at: {occurrence, circle: [point du bord d'un trou]}` ou `{occurrence, edge, on, corner}`. Il suit alors les paramètres ; jamais un décalage chiffré seul.
- **Pièces au contact, sans pénétration** : dans un ensemble à plusieurs corps, couper au ras (une pénétration devient une interférence). Prolonger la pièce coupée en biais avant de la couper, sinon un coin n'atteint pas la face.
- **Noms de corps uniques dans tout le modèle**, même d'un composant à l'autre (`<pièce> <ensemble>` : `Platine basse potelet volée`).
- **Perçage commun à plusieurs ensembles** : l'esquisse reste à la racine, une découpe (ou un Trou) par ensemble, sur la même esquisse.
- **Remplacer sans perdre** : poser le nouvel ensemble avant de supprimer l'ancien arbre, et vérifier le recouvrement (`inspect.interference` : chaque paire ancien / nouveau a le volume entier du corps) ; puis supprimer, et contrôler 0 erreur, 0 interférence, les paramètres en aller-retour.

## 8. Quand SolidCraft résiste

- **Recalcul lent** : regrouper les fonctions lentes dans un dossier de la timeline et le suspendre (`timeline.suppress`) pendant les modifications ; le réactiver avant de tester.
- **Commande qui ne répond pas** (`still running:`) : ne pas la renvoyer, attendre avec `pending`.
- **Plantage** : récupérer la sauvegarde automatique, puis reprendre à l'étape « Constater ».
- **Nouvelle version de SolidCraft** : redémarrer l'app **et** la session de l'agent (le connecteur MCP garde l'ancien binaire et ses outils), vérifier le format dans `document.json` d'un fichier enregistré ; ouvrir chaque modèle, comparer le nombre de corps, les erreurs et les volumes, puis les réenregistrer. Le format de fichier change souvent : une version plus ancienne n'ouvre plus le fichier.

**Pièges connus** (0.27.1 sauf mention ; une ligne par piège, symptôme → contournement) :

- Contrainte verticale ou horizontale : commande `sketch.constraint.horizontal_vertical` (`mode`) ; il n'y a pas de `sketch.constraint.vertical`.
- Esquisse sur un plan décalé de XZ : l'axe vertical de l'esquisse va vers −Z, les coordonnées Z s'écrivent en négatif ; les cotes restent des distances positives.
- Point défini par une expression : pour le libérer, supprimer la ligne et la redessiner avec l'option `ids` (même identifiant, un Frame Member la retrouve) ; Fix/UnFix et le déplacement ne suffisent pas.
- La commande d'oblong (`sketch.slot.*`) n'accepte pas d'expressions (0.29 aussi) → la dessiner en chiffres, puis coter rayon et entraxe des centres en expressions et contraindre un côté (0 DDL, suit les paramètres).
- Union de deux corps en contact face contre face (tube mince sur une platine, balayage bout à bout d'une barre) : échec (`boolean Union: no result`) ou corps à 2 coques (`kernel.shells` = 2 dans `measure`) → corps séparés au contact (ensemble soudé), ou faire pénétrer l'un dans l'autre (1 à 3 mm), ou faire repartir le balayage du début de la barre.
- Profilés avec congés (UPE…) : les booléens qui les percent reprennent (« Boolean retry ») et ralentissent le recalcul → congés à 0 si la section exacte n'est pas utile au modèle.
- Un réseau qui répète plusieurs corps numérote ses copies à la suite en les mélangeant : les noms (et les matériaux affectés par nom) tombent sur les mauvais corps → un réseau par corps.
- L'outil `save` du connecteur écrit le cache de géométrie (474 Ko au lieu de 37 Ko, 2026-11-01) → `file.save` avec `cache: false` (§4).
- Assemblage : `component.relink` n'accepte qu'un `.solidcraft` ; `component.insert_design` ne prend qu'un décalage chiffré ; les matériaux des composants liés n'y passent pas (« Default », masse fausse). Le projet ne voit l'escalier que comme un bloc de corps à plat (sans ses sous-composants).
- `occurrence.move {matrix}` compose avec la position actuelle (relatif) ; un exemplaire neuf (`occurrence.copy`) est à l'identité, la matrice y est donc absolue. Placer puis lier (`joint.as_built`) pour qu'il suive les paramètres.
- `component.move_features` refuse une fonction qui touche des corps de plusieurs composants → la scinder (une fonction par composant sur la même esquisse) ; il refuse aussi de casser un `BodyTransfer`.
- Supprimer une fonction dont un paramètre sert ailleurs (répétition d'esquisse qui cite `reseau_…`) casse ces esquisses, et on ne peut plus les réparer après coup → **avant** de supprimer, remplacer la référence par son expression (`sketch.edit`, `sketch.pattern.rectangular {pattern, entities, count, spacing, spacing2}`).
- `timeline.edit` d'une extrusion : `operation` vaut `new_body`, `join`, `cut` ou `intersect` (pas `new`), pas de `body_name` → `body.rename` après ; un corps renommé ou créé ainsi repasse en « Default ».
- Un `batch` dont une commande échoue est entièrement annulé (`rolled_back`) : ne pas mettre un contrôle douteux à la fin d'un lot de construction.
- Cote `distance_y` entre deux points confondus (origine et début de ligne) refusée (« over-constrain ») → coter l'autre bout de la ligne.
- Rouvrir un chemin déjà ouvert garde le document en mémoire → `new_design` avant `open`.
- Lister les commandes de liaison (`list_commands` filtre `joint`) a semblé faire planter l'app (0.22) → `describe_command` ou `skill_reference {skill: solidcraft-mechanisms}` (formes des origines de liaison), sans souci en 0.27.1.
