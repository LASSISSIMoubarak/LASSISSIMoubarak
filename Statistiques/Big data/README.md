# Big data — Vue d'ensemble

Ce dossier regroupe plusieurs exercices et petits projets permettant d'explorer la concurrence (threads, multiprocessing, asyncio), la communication inter‑processus, ainsi que quelques expérimentations de performance et de calcul scientifique.

Structure et points d'entrée

- `.conda/`, `.vscode/`, `ven/` : environnements et settings locaux (à ignorer en `.gitignore`).
- `Hadoop/` : exercices / supports liés à Hadoop / Spark (voir sous-dossier).
- `Programmation concurrente/` : projet didactique en plusieurs parties (Partie1, Partie2, Partie3) avec READMEs.
- Scripts principaux (racine) :
  - `exo1 (1).py` — threads simples
  - `exo2 (1).py` — thread + input
  - `exo4_1.py` / `exo4_2.py` — locks et conditions de course
  - `exo5.py` — queue + threads (producteur/consommateur)
  - `exo6.py` / `exo7.py` / `exo8.py` — multiprocessing, Pipe, Queue
  - `exo9.py` — benchmark PyTorch vs boucles
  - `exo11_blank.py` — mini régression PyTorch pédagogique

Objectifs pédagogiques

- Illustrer le multi-threading en Python et montrer pourquoi protéger les ressources partagées avec des `Lock`.
- Comparer threads vs processes (multiprocessing) et démontrer l'utilisation de `Pipe` et `Queue` pour l'IPC.
- Montrer la programmation asynchrone avec `asyncio` (version coopérative du même problème).
- Présenter des patterns producteur/consommateur et la terminaison propre des travailleurs.
- Exemples de vectorisation et d'impact des bibliothèques (PyTorch, NumPy) pour la performance.

Comment exécuter (PowerShell)

```powershell
# Exemple : exécuter un script simple
python "Big data\exo1 (1).py"

# Partie 1 (synchrone)
python "Big data\Programmation concurrente\Partie1.py" commandes.txt

# Partie 2 (asyncio)
python "Big data\Programmation concurrente\Partie2.py" commandes.txt

# Exécuter le benchmark (nécessite torch, matplotlib)
python "Big data\exo9.py"
```

