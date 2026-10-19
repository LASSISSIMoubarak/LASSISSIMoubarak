# MLOps - prédiction du cancer du sein

Petit pipeline reproductible de classification binaire avec le jeu de données
Breast Cancer Wisconsin fourni par scikit-learn. Le projet sépare la préparation
des données, l'entraînement et la prédiction d'un exemple.

## Prérequis et installation

Python 3.8 ou supérieur est requis. Depuis ce dossier, crée un environnement et
installe les dépendances :

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Exécuter le pipeline

Les commandes sont indépendantes du répertoire courant grâce aux chemins
résolus depuis le projet :

```powershell
python -m mlops_breast_cancer.data_utils
python -m mlops_breast_cancer.train --random-state 42
python -m mlops_breast_cancer.predict --index 0
```

La préparation crée les partitions d'entraînement et de test dans `data/`.
L'entraînement apprend un `StandardScaler` sur les seules données
d'entraînement, ajuste une régression logistique et affiche le rapport de
classification sur le jeu de test. Le modèle et le scaler sont écrits dans
`models/`. La prédiction charge ces artefacts et affiche les classes et
probabilités de l'exemple demandé.

Les fichiers CSV et modèles générés sont locaux et ignorés par Git. Les données
peuvent être régénérées à partir du jeu intégré à scikit-learn ; aucun fichier
de données téléchargé n'est nécessaire.

## Tests

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

## Structure

```text
src/mlops_breast_cancer/  Préparation, entraînement et prédiction
tests/                    Test de bout en bout du pipeline local
data/                     Partitions générées (non versionnées)
models/                   Modèle et scaler générés (non versionnés)
pyproject.toml            Métadonnées et configuration de paquet
requirements.txt          Dépendances d'exécution
requirements-dev.txt      Dépendances de test
```
