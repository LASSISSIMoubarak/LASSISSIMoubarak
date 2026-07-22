## Structure du projet
- `notebooks/03_Modelisation.ipynb` : Notebook principal pour l'entraînement, l'optimisation et la soumission des modèles.
-`notebooks/02_Feature_Engineering.ipynb`:Notebook pour le data engineering et le preprocessing.
-`notebooks/01_Analyse_Exploratoire.ipynb` pour l'analyse global du jeu de données.
- `data/processed/Train_transformed_data.csv` : Données d'entraînement transformées.
- `data/processed/Test_transformed_data.csv` : Données de test transformées.
- `src/utils.py` : Fonctions utilitaires (wrappers, métriques, sauvegarde de soumission) importer pour utiliser dans les notebooks.

## Exécution du code

1. **Ouvrir le notebook**

    -`notebooks/01_Analyse_Exploratoire.ipynb`.:Pour visualiser les données

    - `notebooks/02_Feature_Engineering.ipynb.ipynb`.:Transformation des données.

    - `notebooks/03_Modelisation.ipynb`. voir les modèles et soumissions.

3. **Résultats**
   - Les fichiers de soumission sont créés dans `submissions/` :
     - `submission_combinaison_3_model.csv` avec 0.7403 d'IPCW_C_index de score 

     -`submission_combinaison_3_model2.csv`  O.73 et 

     - `submission_rsf_optimized.csv` avec 0.73 d'IPCW_C_index
