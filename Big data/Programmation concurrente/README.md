# Programmation concurrente — mini-projet "Serveur / Bariste"

Ce dossier contient une série d'exercices progressifs pour explorer la programmation concurrente en Python : une version synchrone, une version `asyncio` et des notes pédagogiques.

Arborescence importante

- `Partie1.py` : implémentation synchrone (threads et structures de données simples). Écrit des logs dans `borabora.log`.
- `Partie2.py` : réécriture asynchrone en `asyncio` (utilise `asyncio.Queue`, `await`, tâches concurrentes).
- `Partie3` / README_Partie3.md : notes et variations (productivity, debug, suggestions).
- `README_Partie1.md`, `README_Partie2.md`, `README_Partie3.md` : explications détaillées par partie (déjà présentes).
- `borabora.log` : fichier de log généré par les scripts.

But pédagogique

- Simuler un flux de travail "prise de commandes → préparation → service".
- Introduire des structures LIFO (pile `Pic`) et FIFO (`Bar`) adaptées au problème.
- Montrer la différence entre approche synchrone et approches asynchrones coopératives (avec `asyncio`).
- Montrer comment organiser la terminaison propre (quand tous les clients ont envoyé leurs commandes et que toutes ont été traitées).

Exécution et exemples

- Partie1 (synchrone) :
```powershell
python "Big data\Programmation concurrente\Partie1.py" commandes.txt
```
Si `commandes.txt` n'existe pas il est créé d'exemple et le script écrit `borabora.log`.

- Partie2 (asyncio) :
```powershell
python "Big data\Programmation concurrente\Partie2.py" commandes.txt
```

Notes de debug

- Ouvrez `borabora.log` pour lire les traces d'exécution.
- Activez `verbose=True` à la création des objets (`Pic`, `Bar`, `Serveur`, `Bariste`) pour logs plus détaillés.
- Ajustez les `await asyncio.sleep(...)` ou le paramètre `productivity` dans les scripts pour accélérer/réduire les temps de simulation.

Souhaitez-vous que je :
- Ajoute des exemples de fichiers `commandes.txt` dans ce dossier ?
- Ajoute des tests unitaires simples pour valider la logique `Pic`/`Bar`/`Clients` ?
