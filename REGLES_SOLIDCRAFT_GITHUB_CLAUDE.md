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
2. **Plan** → « oui » → branche depuis `main` à jour (nom court de la tâche).
3. **Réaliser** par lots (`batch`), puis **tester** : faire varier un ou deux paramètres concernés puis revenir, 0 erreur, 0 interférence. Projet d'assemblage : mettre à jour les liens.
4. **Enregistrer une seule fois, en fin de tâche** (§4), mettre à jour `CONCEPTION.md`, commit, push, ouvrir la PR. La description de la PR est le compte rendu complet ; elle dit aussi ce qui n'est pas fait ou pas vérifié.

Tâche non terminée enregistrée à la demande : PR en brouillon (*draft*), et ce qui reste suspendu ou non vérifié dans les points ouverts.

## 4. Enregistrer

Le connecteur n'enregistre que dans les dossiers qu'on lui autorise. Lancer le serveur MCP avec `--allow-path <projet>/cad` pour enregistrer **directement dans `cad/`**, sans passer par le dossier `recovery` ni copier.

À chaque enregistrement, dans cet ordre :

1. `save {path: "cad/<modèle>.json"}` : le texte, lisible dans `git diff`.
2. `save {path: "cad/<modèle>.solidcraft"}` : le natif, en dernier ; l'app enregistre ensuite dans ce fichier, pas besoin de le rouvrir.
3. Exports (liste dans `CONCEPTION.md`) seulement si la géométrie a changé : `export {path: "cad/<modèle>.stl"}`.
4. Un commit qui contient tout : modèles, exports, `CONCEPTION.md`.

Chemins absolus. Le fichier courant se lit dans le retour de `open` ou de `save` (`inspect_design` donne `path: null`). Chaque `save` garde la version précédente en `<fichier>.bak`, en écrasant le `.bak` existant : ne rien laisser d'utile sous ce nom. Ne pas commiter les `*.bak` ni les verrous `.~*.lock` (`.gitignore`).

## 5. `CONCEPTION.md`

Il est relu à chaque session : le garder court.

- **Paramètres** : valeur seulement dans le tableau des paramètres ; ailleurs, on cite le nom.
- **Décisions** : D1, D2… en deux ou trois lignes, la décision et son pourquoi.
- **Pièges** : une ligne par piège (symptôme → contournement, version). L'enquête va dans une issue (chez SolidCraft si c'est un bug), avec le lien dans la ligne.
- **Points ouverts** : en tête, « Calculs à relancer : <paramètres> » dès qu'un paramètre utilisé par un calcul change.
- **Historique** : une ligne par PR, avec date, titre et lien. Le détail est dans la PR.

## 6. Modélisation

- **Modifiable à la main** : des cotes pilotées par des paramètres nommés, pas de points définis par expression ni de valeurs en dur.
- **Tout renommer tout de suite** : esquisses, fonctions, corps, plans, et tous les paramètres, y compris ceux des fonctions (extrusions, décalages, réseaux), qu'on liste avec `parameters.list {filter: all}` (ils n'apparaissent pas dans `inspect_design`). Renommer par petits lots : chaque renommage relance le recalcul.
- **Squelette** : s'appuyer sur des esquisses maîtresses et des plans pilotés, jamais sur les faces d'autres corps.
- **Esquisses à 0 degré de liberté.**
- **Un corps par pièce réelle**, avec son matériau dès sa création.
- **Réseaux et symétries** pilotés par des paramètres plutôt que des copies ; de préférence la symétrie du corps entier.
- **Simplifications déclarées** dans `CONCEPTION.md`.

## 7. Quand SolidCraft résiste

- **Recalcul lent** : regrouper les fonctions lentes dans un dossier de la timeline et le suspendre (`timeline.suppress`) pendant les modifications ; le réactiver avant de tester.
- **Commande qui ne répond pas** (`still running:`) : ne pas la renvoyer, attendre avec `pending`.
- **Plantage** : récupérer la sauvegarde automatique, puis reprendre à l'étape « Constater ».
- **Nouvelle version de SolidCraft** : ouvrir chaque modèle, comparer le nombre de corps, les erreurs et les volumes, puis réenregistrer les deux formats. Le format de fichier change souvent : une version plus ancienne n'ouvre plus le fichier.
