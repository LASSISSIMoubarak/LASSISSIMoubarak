# Big data - vue d'ensemble

Ce dossier regroupe plusieurs exercices et petits projets permettant d'explorer la concurrence (threads, multiprocessing, asyncio), la communication inter‑processus, ainsi que quelques expérimentations de performance et de calcul scientifique.

## Structure et points d'entrée

- `Hadoop/` : notebooks MapReduce Streaming et PySpark, documentés dans
  `Hadoop/README.md`.
- `Programmation concurrente/` : exercices en trois parties, chacun documenté
  par un README.
- `exo1.py`, `exo2.py` : premiers exercices sur les threads.
- `exo4_1.py`, `exo4_2.py`, `exo5.py` : verrous, conditions de course et
  producteur/consommateur.
- `exo6.py`, `exo7.py`, `exo8.py` : multiprocessing, Pipe et Queue.
- `exo9.py` : benchmark numérique ; `exo11_blank.py` : exercice de régression
  avec PyTorch.
- `thread (1).ipynb` : notebook complémentaire sur les threads.

## Objectifs pédagogiques

- Illustrer le multi-threading en Python et montrer pourquoi protéger les ressources partagées avec des `Lock`.
- Comparer threads vs processes (multiprocessing) et démontrer l'utilisation de `Pipe` et `Queue` pour l'IPC.
- Montrer la programmation asynchrone avec `asyncio` (version coopérative du même problème).
- Présenter des patterns producteur/consommateur et la terminaison propre des travailleurs.
- Exemples de vectorisation et d'impact des bibliothèques (PyTorch, NumPy) pour la performance.

## Exécution (PowerShell)

```powershell
# Exemple : exécuter un script simple
python "Big data\exo1.py"

# Partie 1
python "Big data\Programmation concurrente\Partie1.py" commandes.txt

# Partie 2
python "Big data\Programmation concurrente\Partie2.py" commandes.txt

# Exécuter le benchmark (nécessite torch, matplotlib)
python "Big data\exo9.py"
```

Lance ces commandes depuis `Statistiques/` pour les chemins montrés. La
programmation concurrente attend notamment un fichier `commandes.txt` fourni
localement ; vérifie le README de chaque partie pour les arguments exacts.
Les environnements virtuels et les sorties ne sont pas distribués avec le
projet.
