# Projet Escalier avec SolidCraft et Claude

Escalier à demi-tour, modélisé de façon paramétrique dans **SolidCraft** et vérifié par un calcul de structure en Python.

*Parametric half-turn staircase, modelled in SolidCraft, with a Python structural check (PyNite, Eurocodes).*

## Comment le projet est fait

**SolidCraft** est un logiciel de CAO paramétrique. Le modèle de l'escalier y est construit à partir d'une vingtaine de paramètres pilotes (hauteur à monter, giron, répartition des marches entre les volées…). Squelette, marches, limons et palier se recalculent quand on en change un : on peut passer de 17 + 5 à 16 + 6 contremarches sans redessiner. Le site (dalle, mur, mezzanine d'arrivée) est un modèle séparé, assemblé avec l'escalier dans un fichier projet.

**Claude Code** est un agent IA qui travaille en ligne de commande. Il pilote SolidCraft par un **connecteur MCP** : il lit les paramètres, crée esquisses et fonctions, mesure, cherche les collisions et enregistre le modèle. Il écrit aussi les scripts de calcul de structure (Python, PyNite) et tient la documentation.

**Le travail à deux** : l'utilisateur décide, l'agent propose un plan et ne l'exécute qu'après accord. L'utilisateur modifie aussi le modèle directement dans l'application ; en début de session, l'agent relève ces changements avant d'agir. Chaque tâche se fait sur une branche Git, que l'utilisateur fusionne après relecture. Le modèle 3D est un fichier binaire illisible dans un diff : c'est le fichier de conception qui décrit chaque modification.

| Fichier | Rôle |
|---|---|
| [CONCEPTION.md](CONCEPTION.md) | État du projet : paramètres, architecture du modèle, décisions, points ouverts, historique |
| [REGLES_SOLIDCRAFT_GITHUB_CLAUDE.md](REGLES_SOLIDCRAFT_GITHUB_CLAUDE.md) | Règles de travail avec l'agent (SolidCraft + GitHub + Claude Code), issues de [cad-agent-rules](https://github.com/mj42584/cad-agent-rules) |
| [AGENTS.md](AGENTS.md) | Point d'entrée pour un agent (ordre de lecture) |

Conçu avec l'aide de [Claude Code](https://claude.com/claude-code).
