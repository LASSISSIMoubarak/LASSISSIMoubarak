# Application Flask de partage de topics

Petite application pédagogique qui affiche des topics et des liens à partir
d'un fichier JSON local. Elle contient aussi des routes expérimentales pour
consulter un annuaire distant et fusionner les topics de serveurs accessibles.

## Installation

Depuis ce dossier, dans PowerShell :

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item data_base.example.json data_base.json
```

## Lancement local

```powershell
python Flask_project_Moubarak_LASSISSI.py
```

Ouvre ensuite `http://127.0.0.1:5000/`. Adapte `data_base.json` pour ajouter des
topics. Le fichier de données local et le journal ne sont pas versionnés ; le
dépôt contient seulement `data_base.example.json`. Les chemins sont résolus
relativement au script, quel que soit le répertoire courant.

Pour configurer l'annuaire distant, définis `ANNUAIRE_URL`. Les routes qui
consultent ou fusionnent des serveurs nécessitent un service compatible et une
connexion réseau. Par défaut, le serveur Flask écoute uniquement sur la machine
locale et le mode debug est désactivé. N'active `FLASK_DEBUG=1` que pendant le
développement.

## Tests

```powershell
python -m pytest
```

## Structure

```text
Flask_project_Moubarak_LASSISSI.py  Application Flask
data_base.example.json              Exemple de données à copier localement
data_base.json                      Données locales ignorées par Git
templates/                          Pages HTML Jinja
tests/                              Tests de routes locales
requirements.txt                    Dépendances d'exécution
requirements-dev.txt                Dépendances de test
```
