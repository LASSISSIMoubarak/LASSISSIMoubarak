# Prévision bayésienne de production solaire

Expérience pédagogique indépendante du projet de survie PBC. Deux scripts
reproduisent la même régression linéaire bayésienne : le script Python et sa
version R, avec échantillonnage de Gibbs sous un modèle Normal-Inverse-Gamma.

## Données

Les scripts réutilisent les CSV déjà présents dans
[`SolarWatch/data/raw`](../../SolarWatch/data/raw/). Ils ne copient ni ne
redistribuent le jeu de données. Pour les sources, la préparation et les
limites du jeu Kaggle, consulter le [README SolarWatch](../../SolarWatch/README.md).

La cible est la puissance agrégée de chaque centrale au relevé de 15 minutes
suivant, pendant la journée. Le modèle apprend la variation de
`log1p(AC_POWER)` à partir de la puissance et des variables météo disponibles
au moment de la prédiction. Le découpage est chronologique (70 % entraînement,
30 % test) et commun aux deux centrales. Les résultats sont comparés à la
persistance, c'est-à-dire la dernière puissance observée.

## Exécution en Python

Depuis ce dossier, avec les dépendances Python de SolarWatch installées :

```powershell
python .\bayesian_forecasting.py
```

Le dossier de données est résolu vers `SolarWatch/data/raw` depuis la racine
du dépôt. Les résultats sont enregistrés dans `results/python/`. Tu peux
fournir `--data-dir` ou `--output-dir` pour utiliser d'autres chemins.

## Exécution en R

Depuis ce dossier :

```powershell
Rscript .\bayesian_forecasting.R
```

Les résultats sont écrits dans `results/r/`. Le script utilise uniquement R
de base. Il accepte les options `--data-dir`, `--output-dir`, `--draws`,
`--burn-in` et `--seed`.

## Résultats de référence

Sur les fichiers locaux, le split de jour contient 826 observations de test.
La MAE de la version Python est de 2 420,75, contre 2 495,88 pour la
persistance ; sa couverture prédictive à 95 % est de 96,0 %, avec des
intervalles très larges (largeur moyenne 22 633 unités). Pour la version R,
la MAE observée est de 2 425,35, contre 2 495,88 pour la persistance ; la
couverture est de 95,9 %, avec une largeur moyenne de 22 627 unités. Le gain
est modeste et ne démontre pas une amélioration opérationnelle.

Les CSV et graphiques reproductibles sont conservés dans le dossier `results/`.
Le jeu ne couvre qu'environ 34 jours et deux centrales en Inde. Cette étude
n'est ni une prévision à long horizon ni une validation d'usage industriel.
Acceptation-rejet et Metropolis-Hastings ne sont pas ajoutés artificiellement :
Gibbs est utilisé pour le modèle conjugué choisi.

## Tests Python

```powershell
python -m pytest .\tests
```
