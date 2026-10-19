# Hadoop Streaming et PySpark

Ce dossier contient deux notebooks d'étude appliqués à l'analyse de données de
films :

- `Moubarak_LASSISSI__02_Exe_MapReduce.ipynb` — notebook MapReduce avec Hadoop
  Streaming.
- `04_pyspark_movie_exercises (1).ipynb` — exercices d'analyse PySpark.

## Prérequis

- Pour le notebook MapReduce : Java et Hadoop avec Hadoop Streaming disponible.
- Pour PySpark : Python, Java/JDK et `pyspark`. Les notebooks peuvent avoir
  d'autres dépendances déclarées dans leurs cellules.
- Les données utilisées dans les exemples sont à télécharger ou à préparer
  selon les cellules des notebooks ; elles ne sont pas incluses ici.

Sur Windows, Hadoop est généralement plus simple à utiliser dans WSL2, une
machine Linux ou Google Colab. Ouvre le notebook correspondant dans Jupyter,
exécute les cellules dans l'ordre et vérifie les chemins d'entrée avant de
lancer un traitement.

Les extraits mapper/reducer présentés dans les notebooks sont des exemples :
aucun fichier `mapper.py` ou `reducer.py` autonome n'est fourni dans ce
dossier. Des notebooks apparentés se trouvent aussi dans `SparkBigData/`.
