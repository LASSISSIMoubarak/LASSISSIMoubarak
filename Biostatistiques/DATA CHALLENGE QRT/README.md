## Structure du projet
- `notebooks/01_Analyse_Exploratoire.ipynb` : analyse exploratoire.
- `notebooks/02_Feature_Engineering.ipynb` : préparation et transformation des variables.
- `notebooks/03_Modelisation.ipynb` : entraînement, optimisation et création de soumissions.
- `data/` : données brutes et transformées utilisées par les notebooks.
- `src/utils.py` : fonctions utilitaires pour les métriques et les soumissions.
- `submissions/` : fichiers de soumission produits localement.

## Exécution du code

Ouvre les notebooks dans l'ordre indiqué avec Jupyter. Les chemins de données
et les bibliothèques nécessaires sont définis dans les cellules des notebooks;
exécute-les depuis le dossier du projet pour que les chemins relatifs soient
résolus correctement.

Les jeux de données du challenge et les résultats CSV ne sont pas versionnés.
Obtiens les données selon les conditions du challenge avant d'exécuter les
notebooks. Les fichiers de soumission sont écrits dans `submissions/` lorsqu'ils
sont générés. Les scores mentionnés dans les anciens noms de fichiers ne sont
pas reproduits ici comme résultats garantis.
