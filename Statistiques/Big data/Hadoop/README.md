# Hadoop & PySpark — documentation du dossier

Ce dossier contient des exercices et notebooks pédagogiques pour apprendre MapReduce (Hadoop Streaming) et PySpark, appliqués à l'analyse de jeux de données (ex. Amazon Movie Reviews).

Objectifs
- Fournir des exemples concrets d'utilisation de MapReduce (Python streaming) pour des tâches d'analyse de logs / reviews.
- Montrer comment préparer et exécuter des jobs Hadoop en mode local (ou pseudo‑distributed) pour des petits jeux de données.
- Fournir un notebook PySpark pour explorer des données en mémoire et comparer approches.

Contenu du dossier
- `Moubarak_LASSISSI__02_Exe_MapReduce.ipynb` : notebook didactique détaillant un mini‑projet MapReduce — téléchargement du dataset, scripts de mappers/reducers, exécution en local, et analyses finales (count, moyenne, mots fréquents, jointure des résultats).
- `04_pyspark_movie_exercises (1).ipynb` : notebook PySpark contenant exercices d'analyse (chargement, transformations, aggregations) sur le même jeu de données.

Prérequis (local)
- Java 8+ (JDK). Assurez‑vous que `JAVA_HOME` est défini.
- Hadoop 3.x (pour exécuter des jobs MapReduce en local ou pseudo‑distributed). Pour des tests rapides on peut utiliser Hadoop en mode `local` (pas besoin de cluster).
- Python 3.8+ avec : `pyspark`, `numpy`, `pandas`, `matplotlib` (pour le notebook). Le notebook peut aussi effectuer l'installation et extraction de Hadoop dans un environnement Linux (ex : Google Colab). 

Remarques :
- Sur Windows, l'installation de Hadoop n'est pas toujours triviale. Pour expérimenter rapidement, utilisez une machine virtuelle Linux, WSL2 (Windows Subsystem for Linux) ou Google Colab/Dataproc.

Exécution — résumé des étapes (MapReduce en local)
1. Télécharger et préparer le dataset (extrait du notebook) :

```bash
# Exemple (depuis le notebook) :
wget -O Movies_and_TV_small.json.gz https://jmcauley.ucsd.edu/data/amazon_v2/categoryFilesSmall/Movies_and_TV_5.json.gz
gunzip Movies_and_TV_small.json.gz
```

2. Préparer des scripts `mapper.py` / `reducer.py` (exemples présents ou à créer depuis le notebook). Exemple simple (compter reviews par `asin`) :

mapper.py
```python
#!/usr/bin/env python3
import sys, json
for line in sys.stdin:
	obj = json.loads(line)
	asin = obj.get('asin')
	if asin:
		print(f"{asin}\t1")
```

reducer.py
```python
#!/usr/bin/env python3
import sys
current = None
count = 0
for line in sys.stdin:
	key, val = line.strip().split('\t')
	val = int(val)
	if key == current:
		count += val
	else:
		if current is not None:
			print(f"{current}\t{count}")
		current = key
		count = val
if current is not None:
	print(f"{current}\t{count}")
```

3. Lancer le job Hadoop en streaming (mode local) :

```bash
$HADOOP_HOME/bin/hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -input /path/to/Movies_and_TV_small.json \
  -output /path/to/out_count_by_movie \
  -mapper mapper.py \
  -reducer reducer.py \
  -file mapper.py \
  -file reducer.py
```

Remarque : en environnement non‑Hadoop (ex : notebook local), le notebook montre comment exécuter les mêmes étapes en mode simulé (ex. tri local des paires key/value) pour vérification.

Exécution — PySpark (notebook)
- Ouvrir `04_pyspark_movie_exercises (1).ipynb` dans Jupyter / JupyterLab ou exécuter dans Google Colab avec `pyspark` installé.
- Exemple PySpark (depuis le notebook) :

```python
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName('movies').master('local[*]').getOrCreate()
df = spark.read.json('Movies_and_TV_small.json')
df.select('asin','overall').groupBy('asin').agg({'overall':'avg','overall':'count'}).show()
```

Bonnes pratiques et conseils
- Versionnez vos scripts `mapper.py` et `reducer.py` dans ce dossier pour garder trace des transformations.
- Pour de gros jeux de données, testez d'abord sur un échantillon (`head -n 1000`) avant de lancer le job complet.
- Documentez le format d'entrée attendu (ici JSON ligne par ligne) et toute préproc (extraction de champs, nettoyage texte) dans le README ou dans un fichier `NOTES.md`.
- Si vous voulez exécuter sur un vrai cluster (YARN), adaptez les chemins HDFS et les paramètres du job (replication, partitions, mémoire).

Propositions d'amélioration (si vous voulez que je m'en occupe)
- Extraire et ajouter dans le dossier des scripts `mapper/reducer` prêts à l'emploi pour les quatre tâches du notebook (count, average rating, frequent keywords, join results).
- Fournir un script `run_local.sh` qui exécute automatiquement les étapes de préparation et teste les mappers/reducers en local (sans Hadoop) pour développement rapide.
- Ajouter un petit README avec instructions pour exécuter les notebooks dans Google Colab (install JDK/Hadoop, config env vars) — le notebook `Moubarak_LASSISSI__02_Exe_MapReduce.ipynb` contient déjà des cellules pour installer Hadoop sur Colab.

