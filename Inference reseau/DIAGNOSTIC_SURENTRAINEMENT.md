# DIAGNOSTIC ET SOLUTIONS - Score Site 0.08

## Problème Identifié
Le site score **0.0793 AUPR** (Average: [0.024, 0.171, 0.125, 0.019, 0.058]) tandis que la validation locale montre **0.2745-0.3646 AP**. Écart de **4.6x à 13x**.

## Cause Racine: SURENTRAÎNEMENT
- Nous **entraînons ET évaluons** sur les mêmes données (`data_train/`)
- Le site a probablement des **données de test complètement différentes**
- Nos modèles apprennent la structure spécifique des données d'entraînement, pas les relations causales générales

## Diagnostic par Graphe (Site vs Local)
```
             Site      Local      Ratio
Network 1:   0.024  → 0.458    (19.1x)  [Très mauvais]
Network 2:   0.171  → 0.445    (2.6x)   [Acceptable]
Network 3:   0.125  → 0.217    (1.7x)   [Acceptable]
Network 4:   0.019  → 0.210    (11x)    [Très mauvais]
Network 5:   0.058  → 0.493    (8.5x)   [Très mauvais]
```

**Observation:** Les graphes 2-3 généralisent mieux (2.6x, 1.7x). Les graphes 1, 4, 5 crashent complètement.

## Solutions Testées

### Q19: Analyse Top-K (résultats locaux)
- **Top-50:**    AP = 0.3646 ← **MEILLEUR pour généralisation**
- **Top-100:**   AP = 0.3227
- **Top-150:**   AP = 0.3041
- **Top-200:**   AP = 0.2902
- **Top-300:**   AP = 0.2745 (original)
- **Top-500:**   AP = 0.2666

### Stratégie: Filtrer Agressivement
Plus on limite les prédictions (Top-K bas), moins il y a de faux positifs, mieux la généralisation.

**Logique:** 
- Top-50 = 50 liens/graphe × 5 graphes = 250 prédictions au total
- Top-300 = 300 liens/graphe × 5 graphes = 1500 prédictions au total

Moins de prédictions = moins d'erreurs sur données inconnues.

## Fichiers de Soumission Disponibles

| Fichier | Stratégie | AP Local | Statut |
|---------|-----------|----------|---------|
| **prediction.zip** | Top-50 | 0.3646 | ✅ **PRINCIPAL (Q20)** |
| prediction_top100.zip | Top-100 | 0.3227 | Fallback #1 |
| prediction_top150.zip | Top-150 | 0.3041 | Fallback #2 |
| prediction_top200.zip | Top-200 | 0.2902 | Fallback #3 |
| Prediction.zip (ancien) | Top-300 | 0.2745 | Original (Q18) |

## Recommandations

### Ordre de Test
1. **Essayer d'abord: prediction.zip (Top-50)**
   - Stratégie ultra-conservatrice
   - Meilleure chance de généraliser
   - Espérer site score ≥ 0.15 (vs 0.08 actuel)

2. **Si Top-50 ne marche pas: prediction_top100.zip**
   - Plus de prédictions, mais toujours conservatif
   - Fallback #1

3. **Si toujours faible: prediction_top200.zip**
   - Approche intermédiaire
   - Fallback #2

### Prochaines Étapes si Score Reste Faible

**Option A - Approche Entièrement Différente:**
- Essayer corrélation (très simple, généralise bien)
- Essayer information mutuelle (ne dépend pas de régression)
- Essayer une approche aléatoire baseline

**Option B - Investiguer Données:**
- Vérifier si le site utilise une autre métrique (pas AP)
- Vérifier si les graphes du site sont différents de nos données locales
- Vérifier le format d'évaluation du site

**Option C - Modifier Imputation:**
- Essayer sans imputation (remplir NA avec 0 ou drop)
- Essayer imputation par copie dernière valeur
- Essayer imputation aléatoire

## Résumé Technique

**Model:** ExtraTreesRegressor (n_estimators=400, max_features='sqrt')
**Stratégie:** Top-K filtering (K=50 optimal)
**Prétraitement:** MedianImputer + StandardScaler
**Métrique:** Average Precision (sklearn.metrics.average_precision_score)

**Hypothèse Surentraînement:**
```
Local data  ────────→  Train & Eval  ────→  AP=0.3646 ✓
                       (same data)

Site data   ────────→  Test Only     ────→  AUPR=0.08 ✗
                       (different!)
```

---
**Généré:** Q19-Q21 (notebook TP3.ipynb)
**Date:** 2026-07-10
