# SolarWatch — surveillance de performance photovoltaïque

Mini-projet de data science appliquée à la maintenance solaire. À partir des
mesures d'onduleurs et de météo d'un jeu Kaggle, le pipeline compare la
production de chaque onduleur à la médiane de ses pairs dans la même centrale,
repère des arrêts et sous-performances persistantes, propose des hypothèses
d'incident, compare une prévision LSTM à un baseline et produit des alertes
hiérarchisées.

> **Limite importante :** les données ne contiennent pas de labels de panne.
> Une alerte est un écart statistique à examiner.
> Les données sont historiques, limitées à 34 jours et proviennent de centrales
> en Inde. Elles ne permettent pas d'évaluer un cycle saisonnier annuel.
> Les injections de scénarios sont synthétiques et séparées des observations
> réelles.

## Données et provenance

Jeu utilisé : [Solar Power Generation Data — Kaggle, Ani Kannal, version 1](https://www.kaggle.com/datasets/anikannal/solar-power-generation-data).
La page Kaggle décrit des données issues de deux centrales en Inde sur 34 jours,
avec production mesurée au niveau des onduleurs et météo mesurée au niveau de
chaque centrale. Les données du jeu ne sont pas recopiées dans ce dépôt : la
page Kaggle indique « Data files © Original Authors ». Vérifiez ses conditions
d'utilisation avant toute redistribution ou réutilisation publique.

Télécharge l'archive depuis Kaggle, puis place les quatre CSV extraits dans
`data/raw/` :

```text
data/raw/
├── Plant_1_Generation_Data.csv
├── Plant_1_Weather_Sensor_Data.csv
├── Plant_2_Generation_Data.csv
└── Plant_2_Weather_Sensor_Data.csv
```

## Lancer le projet

Depuis ce dossier, avec Python 3.10 ou supérieur :

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,deep-learning]"
python -m pytest
python -m solarwatch
```

Les options `--data-dir` et `--output-dir` permettent de choisir les chemins
des données et des résultats :

```powershell
python -m solarwatch --data-dir data/raw --output-dir outputs
```

## Méthode

1. Vérification des colonnes, des identifiants et des doublons, puis jointure
   temporelle des mesures météo et de production.
2. Calcul, à chaque horodatage, de la médiane de puissance AC des onduleurs de
   la centrale et du ratio `puissance de l'onduleur / médiane des pairs`.
3. Surveillance seulement en journée (`irradiation >= 0,1`) et lorsque la
   référence des pairs atteint au moins 10 unités de puissance.
4. En complément, entraînement d'une `IsolationForest` par centrale sur les
   premiers 70 % des horodatages surveillables, puis scoring des 30 % suivants.
   Les variables utilisées sont le ratio de performance, l'irradiation et les
   températures ambiante et module.
5. Entraînement d'un LSTM PyTorch pour prévoir le prochain relevé de puissance
   à partir des huit relevés précédents. Le découpage est chronologique : 70 %
   pour développement, avec une période de calibration interne, puis 30 % de
   test final. La MAE/RMSE est comparée à une référence de persistance basée sur
   la médiane des pairs au relevé précédent.
6. Comparaison directe des alertes Isolation Forest et LSTM sur les mesures
   communes du test temporel. On mesure leur taux d'accord et leur Jaccard,
   mais pas leur précision : aucune vérité terrain de panne n'est disponible.
7. Classification de situations à l'échelle de l'onduleur : arrêt individuel
   sous irradiation, sous-performance locale de cause inconnue, ou baisse
   simultanée de la centrale. Les périodes insuffisamment éclairées ou sans
   référence exploitable sont marquées **non surveillées**, et non « normales ».
   Une baisse commune est une interruption.
8. Détection d'une sous-performance si le ratio reste sous 0,70 pendant au
   moins trois relevés consécutifs, soit 45 minutes pour cet échantillonnage.
   Un épisode commun de production nulle en journée est aussi remonté après
   trois relevés.
9. Priorité **critique** pour un arrêt ou une interruption commune, sinon
   **critique** si le ratio médian d'un épisode individuel est inférieur ou
   égal à 0,10, **haute** jusqu'à 0,40, sinon **moyenne**.
10. Injection reproductible d'arrêts, de baisses locales et de baisses communes
   dans des copies de snapshots réels. La précision de diagnostic rapportée
   dans ce benchmark concerne uniquement ces scénarios fabriqués.


**Les deux méthodes d'anomalie ont des rôles différents.** Isolation Forest
recherche des observations inhabituelles dans les variables d'entrée. Le LSTM
prévoit la puissance suivante ; un résidu élevé (écart entre mesure et
prévision) devient un signal d'anomalie. Le pipeline compare ces deux signaux
sur exactement les mêmes mesures de test, indique leurs alertes communes et
leurs désaccords. Cette comparaison mesure leur concordance, pas leur
exactitude : sans pannes labellisées, on ne sait pas lequel a raison. Les alertes
par seuil de sous-performance décrites plus haut constituent encore un
troisième signal, basé sur la médiane des pairs.

### Correspondance avec l'offre et limites du jeu

| Besoin métier | Dans le mini-projet | Limite à garder en tête |
|---|---|---|
| Analyser les données solaires | Contrôles qualité, jointure météo/production, CSV et graphiques | Jeu court, deux centrales |
| Suivre production et sous-performance | Ratio par rapport aux pairs, alertes persistantes et estimation indicative | Seuils de démonstration |
| Arrêts d'onduleurs | Détection de puissance nulle en journée, si les pairs produisent | Hypothèse à vérifier, pas de journal d'état d'onduleur |
| Interruptions réseau | Repérage d'une baisse simultanée de la centrale | Données seules ne distinguent pas réseau, arrêt commun, communication ou capteur |
| Défauts de chaînes | Sous-performance locale remontée pour inspection | Les mesures sont au niveau onduleur, pas chaîne/string : diagnostic direct impossible |
| Ombrage | Signalement d'une sous-performance locale | Pas de capteur d'ombrage ni de mesure par chaîne ; cause non identifiable |
| Hiérarchiser les alertes | Niveaux critique/haut/moyen et tri des épisodes | Les règles doivent être validées avec des équipes de maintenance |
| IA / LSTM | Prévision un pas à l'avance; MAE/RMSE contre un baseline de persistance; résidus élevés signalés | Prévision n'égale pas diagnostic de cause; aucun label de panne réel |
| Comparaison des détections | Accord Isolation Forest / résidus LSTM sur le même test temporel | Accord entre modèles n'est pas une précision de détection |
| Interpréter et valider | Split temporel, baseline, tests, comparaison de signaux et benchmark synthétique transparent | L'injection ne remplace pas une validation sur incidents réels |
| Visualisation | Courbes PNG et tables CSV réutilisables | Une intégration Grafana/QuickSight nécessiterait une source de données exploitable et un service de déploiement |
| Saisonnalité et allocation aux clients | Piste d'évolution, non implémentée | 34 jours de données et aucune donnée de demande, stockage ou réseau |

Les seuils sont des paramètres de démonstration définis dans
`src/solarwatch/pipeline.py` et `src/solarwatch/diagnostics.py`, à faire valider
par des spécialistes avant tout usage opérationnel. L'estimation d'énergie
suppose des relevés espacés de 15 minutes et des valeurs de puissance en kW ;
elle n'est pas une mesure contractuelle de pertes.

## Résultats reproductibles observés

Exécution locale sur la version 1 du jeu Kaggle :

| Indicateur | Résultat |
|---|---:|
| Période couverte | 15 mai – 17 juin 2020 |
| Centrales / onduleurs | 2 / 44 |
| Mesures de production | 136 476 |
| Mesures sans donnée météo associée | 4 |
| Mesures retenues pour la surveillance | 58 980 |
| Relevés sous le seuil de performance | 4 121 |
| Épisodes d'alerte regroupés | 355 |
| Alertes critiques / hautes / moyennes | 334 / 12 / 9 |
| Anomalies Isolation Forest dans le test temporel | 2 569 / 18 216 |
| LSTM : MAE / RMSE sur le test chronologique | 56,06 / 111,25 unités de `AC_POWER` |
| Baseline de persistance des pairs : MAE | 75,57 unités de `AC_POWER` |
| Amélioration LSTM de la MAE par rapport au baseline | 25,82 % |
| Prévisions LSTM signalées par le seuil calibré | 134 / 41 470 |
| Mesures de test comparées entre les deux modèles | 17 908 |
| Isolation Forest / résidus LSTM signalés sur ces mesures | 2 501 / 99 |
| Anomalies signalées par les deux modèles | 39 |
| Accord / Jaccard des signaux | 85,92 % / 1,52 % |
| Benchmark de scénarios synthétiques | 97,89 % (332 événements injectés) |
| Baisse locale correctement signalée dans ce benchmark | 76 / 83 (91,57 %) |
| Écart d'énergie estimé sur les épisodes | 858 157,49 kWh* |

L'écart d'énergie est une estimation indicative calculée en comparant chaque
onduleur à la médiane de ses pairs ; plusieurs alertes peuvent couvrir le même
intervalle. Le calcul suppose que la puissance est exprimée en kW et les
relevés espacés de 15 minutes. Il ne s'agit pas d'une perte confirmée : vérifier
les unités du jeu avant toute interprétation physique. L'absence de labels de
panne interdit de calculer une précision, un rappel ou un score d'exactitude honnête.
Les 2 569 observations signalées par Isolation Forest sont également des
candidates non validées, pas un taux d'erreur mesuré.
L'accord de 85,92 % entre l'Isolation Forest et le LSTM est dominé par les
mesures où aucun des deux ne déclenche d'alerte ; le Jaccard de 1,52 % montre
que leurs alertes positives se recouvrent peu. Ce sont des comportements
différents des modèles, pas une comparaison de leur justesse.
Les métriques de forecast et de scénarios sont recalculées à chaque exécution :
elles ne doivent pas être comparées sans conserver les paramètres et les
versions de dépendances.

Les unités de puissance des fichiers sont reprises telles quelles dans les
métriques MAE/RMSE.

## Livrables générés

Le pipeline crée `outputs/` (non versionné) :

- `results.json` — période, volumes, seuils et comptage des alertes ;
- `alerts.csv` — épisodes, priorité, ratios et écart d'énergie estimé ;
- `monitoring_samples.csv` — données jointes, indicateurs et scores du modèle ;
- `lstm_forecasts.csv` — prévisions du jeu test, baseline et résidus LSTM ;
- `anomaly_signal_comparison.csv` — résultats côte à côte d'Isolation Forest et
  du signal de résidu LSTM pour chaque mesure de test commune ;
- `synthetic_scenario_benchmark.csv` et `synthetic_scenario_metrics.json` —
  diagnostics comparés aux étiquettes d'injection simulées, avec matrice de
  confusion pour analyser les baisses locales non signalées ;
- `plant_1_monitoring.png` et `plant_2_monitoring.png` — production réelle
  comparée à la médiane des pairs, avec les relevés candidats surlignés et
  les anomalies Isolation Forest du jeu de test.
- `plant_1_lstm_forecast.png` et `plant_2_lstm_forecast.png` — vérité test,
  prévision LSTM et baseline des pairs.

Les tests unitaires vérifient le regroupement des épisodes, la durée minimale,
la hiérarchisation, le rejet des relevés non surveillables, la cohérence des
diagnostics vectorisés, la séparation temporelle des modèles et les cas
synthétiques. Le pipeline fonctionne en batch ; il ne se connecte pas à une
centrale en temps réel.
