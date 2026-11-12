# Glycémie simulée : séries temporelles et processus stochastiques en R

**Statut : projet en cours.**

Ce projet pédagogique étudie des trajectoires **simulées** inspirées de la
glycémie. Il vise à comprendre les fluctuations aléatoires, puis à étudier
des approches de prévision individualisée. Aucune donnée réelle de patient
n'est utilisée et le projet n'est pas un outil clinique.

## Avancement et objectifs

Déjà réalisés :

- simulation reproductible et exploration descriptive de 40 trajectoires ;
- représentation de trois trajectoires et tests exploratoires KPSS et ADF ;
- estimation des paramètres du processus générateur par vraisemblance
  conditionnelle, avec des tests du code.

À étudier par la suite :

- comparer les caractéristiques individuelles, les valeurs atypiques et les
  autocorrélations, puis examiner si des transformations sont justifiées ;
- comparer une référence de persistance, une dynamique commune utilisant
  l'historique individuel et des modèles individuels ou par profils ;
- évaluer plusieurs horizons de prévision sur des observations futures et
  sur des individus non utilisés pour l'apprentissage ;
- explorer des simulations avec des profils différents, puis éventuellement
  des données réelles si leur accès et leurs conditions d'utilisation le
  permettent.

Les méthodes de prévision et leur évaluation ne sont pas encore implémentées.
La moyenne du groupe décrit l'ensemble, mais ne suffit pas à prévoir chaque
individu. Les différences des trajectoires actuelles proviennent de l'aléa :
elles partagent les mêmes paramètres de simulation.

## Organisation des fichiers

| Fichier | Rôle |
| --- | --- |
| `configuration.R` | Paramètres et graine de la simulation |
| `modele.R` | Fonctions de simulation et d'estimation |
| `explorer.R` | Statistiques descriptives et graphiques |
| `Analyse-stochastiques-Modelisation.R` | Graphique de trois trajectoires et tests KPSS et ADF |
| `analyser.R` | Estimation des paramètres du processus simulé |
| `test_exploration.R`, `test_modele.R` | Tests reproductibles du code |

Les résultats générés sont conservés dans `outputs/`, ignoré par Git.

## Modèle

On utilise un processus d'Ornstein-Uhlenbeck :

```text
dX(t) = theta * (mu - X(t)) dt + sigma dW(t)
```

`mu` est le niveau moyen, `theta` la vitesse de retour vers ce niveau et
`sigma` l'intensité du bruit. Le temps est exprimé en heures et les valeurs
simulées en mg/dL. Les valeurs choisies sont illustratives, pas calibrées sur
des patients. Le processus gaussien peut même produire des valeurs négatives :
il ne garantit donc pas des concentrations biologiquement plausibles.

Le script simule 40 trajectoires indépendantes avec les mêmes paramètres,
mesurées toutes les 15 minutes pendant 30 heures. Le premier état est tiré de
la distribution stationnaire. La simulation utilise la transition exacte,
pas une approximation d'Euler. Une graine fixe permet la reproduction.

Les paramètres sont estimés conjointement par maximum de vraisemblance
conditionnelle : la vraisemblance utilise toutes les transitions, mais pas la
densité des observations initiales. L'optimisation impose `theta > 0` et
`sigma > 0`. Les valeurs simulées et estimées peuvent différer à cause de
l'aléa ; ce projet ne calcule pas d'intervalles de confiance.

## Exécution

Il faut R et `Rscript`. L'exploration descriptive et l'estimation utilisent R
de base ; les tests KPSS et ADF nécessitent le package `tseries`. Depuis ce
dossier, commence par l'exploration descriptive :

```powershell
Rscript explorer.R
Rscript test_exploration.R
```

Cette première étape affiche le nombre d'individus, la durée, la fréquence des
mesures, les valeurs manquantes et des statistiques descriptives. Elle produit
un tableau par individu et quatre graphiques : trajectoires, moyenne à chaque
temps, histogramme global et boîtes à moustaches par individu.

La moyenne à chaque temps résume les individus entre eux ; elle ne décrit pas
la trajectoire d'un individu. L'histogramme rassemble toutes les mesures,
dont celles d'une même trajectoire sont dépendantes. Une observation atypique
n'est pas forcément une erreur. La stationnarité et la propriété de Markov ne
peuvent pas être établies par ces seuls graphiques.

### Explorer la stationnarité de trois trajectoires

Le script suivant nécessite le package `tseries`. Si nécessaire, installe-le
une fois dans la console R avec `install.packages("tseries")`, puis lance :

```powershell
Rscript Analyse-stochastiques-Modelisation.R
```

Il choisit trois individus de façon reproductible, enregistre leur graphique
dans `outputs/stationnarite_trajectoires.png` et affiche les tests KPSS et ADF.
Le test KPSS utilisé a pour hypothèse nulle la stationnarité autour d'une
constante, tandis que l'ADF teste une hypothèse nulle de racine unitaire.
Ils ne prouvent pas à eux seuls la stationnarité ; ici les trajectoires sont
stationnaires par construction. Les séries ne sont ni transformées ni
différenciées.

Pour revenir plus tard à l'estimation des paramètres :

```powershell
Rscript analyser.R
Rscript test_modele.R
```

Sous Windows, si `Rscript` n'est pas dans le PATH, utiliser son chemin complet,
par exemple `& "C:\Program Files\R\R-4.4.0\bin\Rscript.exe" analyser.R`.
Les scripts fonctionnent également depuis un autre dossier en donnant leur
chemin. Les tests vérifient la transition, la reproductibilité, les entrées
invalides et la récupération approximative des paramètres simulés.

Les scripts utilisent les paramètres communs de `configuration.R` pour
recréer les mêmes données. Ils écrivent leurs résultats dans `outputs/`, ignoré
par Git ; relancer un script remplace ses propres fichiers.

## Limites et suites possibles

Ce modèle simplifié ne représente ni repas, ni traitements, ni rythme circadien,
ni variabilité entre individus, ni erreur de mesure. Les mesures sont
complètes et régulières. Une extension pourrait comparer les estimations sur
plusieurs simulations, puis étudier des données réelles autorisées et leurs
valeurs manquantes, sans supposer que ce modèle leur convient.

Pour approfondir progressivement les séries temporelles avant l'estimation :
étudier d'abord la tendance et la saisonnalité, puis la stationnarité et
l'autocorrélation. Les données actuelles sont générées sans tendance ni
saisonnalité et avec une dynamique markovienne : elles ne suffisent donc pas
à illustrer toute la variété des séries biologiques.
