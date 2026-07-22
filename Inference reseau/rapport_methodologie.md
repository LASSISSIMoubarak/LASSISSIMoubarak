# Rapport méthodologique : classement des arêtes pour la soumission

## Objectif
L’objectif est de produire, pour chaque réseau, un classement d’arêtes de causalité fiable, où chaque paire (Cause, Effect) reçoit un score continu reflétant sa probabilité de pertinence. Ce classement est ensuite exporté sous forme de fichiers CSV puis regroupé dans une archive ZIP pour la soumission globale.

## Données utilisées
- Données d’entraînement disponibles dans le dossier data_train
- Un fichier cible par réseau contenant les arêtes attendues
- Les fichiers produits sont nommés predictions_network1.csv à predictions_network5.csv

## Pipeline utilisée
1. Prétraitement des données
   - imputation des valeurs manquantes par la médiane
   - normalisation des variables

2. Construction d’un score par arête
   - Lasso CV : sélection de variables par régularisation
   - Elastic Net CV : stabilité supplémentaire
   - Random Forest : importance des variables
   - Gradient Boosting : importance non linéaire
   - Mesures de dépendance complémentaires : corrélation de Pearson, corrélation de Spearman et information mutuelle

3. Agrégation du score
   - Chaque signal est normalisé entre 0 et 1
   - Les scores sont combinés dans un score composite
   - Les arêtes sont triées par score décroissant

4. Export
   - Chaque réseau donne un fichier CSV avec les colonnes Cause, Effect, Score
   - Les cinq fichiers sont regroupés dans prediction.zip

## Résultats observés
Les fichiers produits contiennent maintenant des scores continus et non binaires :
- Network 1 : 380 arêtes, score entre 0.0 et 1.0
- Network 2 : 380 arêtes, score entre 0.0 et 1.0
- Network 3 : 380 arêtes, score entre 0.0 et 1.0
- Network 4 : 9900 arêtes, score entre 0.0005 et 1.0
- Network 5 : 9900 arêtes, score entre 0.0001 et 0.5626

## Intérêt de la méthode
Cette approche fournit un vrai classement de confiance plutôt qu’un simple binaire. Cela est plus adapté à une soumission globale, car le système peut ensuite privilégier les arêtes les plus plausibles en haut du classement.

## Fichiers générés
- prediction.zip
- predictions_network1.csv
- predictions_network2.csv
- predictions_network3.csv
- predictions_network4.csv
- predictions_network5.csv
- generate_submission_predictions.py
