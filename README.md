
# Projet: LASSISSI Moubarak

Ce dépôt rassemble plusieurs travaux et projets (Python, R, notebooks, prototypes MLOps) réalisés par LASSISSI Moubarak Ingénieur Statistcien & Data Scientist. Ce README donne une vue d'ensemble, des instructions pour lancer les éléments principaux et des repères pour retrouver les parties importantes du dépôt.

**Structure du dépôt**
- **`Big data/`** : scripts Python divers pour travaux Big Data et exercices. avec flask pour une création de site web puis l'utilisation de mapreducer puis spark

- **`Data challenge/`** : notebooks et scripts liés à un challenge de prédictions du traffic ferrovier sncf

- **`mlops/`** : projet MLOps, dont `mlops_breast_cancer/` contenant un petit projet Python avec `requirements.txt` et `pyproject.toml`. strutucturer un projet avec un modèle de regression logistique.

- **`R_project/`** : projets R; contient `CATPCA/` avec une application Shiny (`app.R`).
- **`Modelisation Bayésienne/`**, **`Etude de cas 2/`**, **`Mini Projet/`**, **`Statistiqiues en grande dimension/`** : scripts et analyses R.
- **`Projet Flask/`** : petite app Flask et templates HTML.
- Notebooks racine : `Kernel_approximation.ipynb`, `TP_CNN.ipynb`.

**Points d'entrée / éléments à lancer**
- `mlops/mlops_breast_cancer/requirements.txt` : dépendances Python du prototype MLOps.
- `R_project/CATPCA/app.R` : application Shiny CATPCA (R) — lancer depuis RStudio ou `shiny::runApp()`.
- Notebooks Jupyter : ouvrir avec JupyterLab/Jupyter Notebook.

**Installer l'environnement Python (exemple Windows PowerShell)**

```powershell
# Créer et activer un venv (depuis la racine du dépôt)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Installer dépendances pour le projet mlops si besoin
pip install -r .\mlops\mlops_breast_cancer\requirements.txt
```

**Lancer l'application Shiny (R)**

Ouvrir `R_project/CATPCA/app.R` dans RStudio puis cliquer sur "Run App", ou dans une session R :

```r
setwd("R_project/CATPCA")
shiny::runApp()
```

Packages R nécessaires (extraits de `app.R`) : `shiny`, `shinythemes`, `Gifi`, `ggplot2`, `dplyr`, `foreign`, `plotly`, `DT`, `corrplot`.

