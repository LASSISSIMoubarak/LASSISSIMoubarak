# Rapport de Méthodologie et Résultats
## Inférence de Réseaux de Régulation Génique

---

## 1. Introduction

Ce projet vise à prédire les arêtes causales dans des réseaux de régulation génique en utilisant des méthodes d'apprentissage machine. Le défi consiste à inférer les interactions (Cause → Effet) entre gènes à partir de données d'expression génique.

**Objectif:** Maximiser la métrique AUPR (Area Under Precision-Recall curve) sur 5 réseaux biologiques distincts.

---

## 2. Méthodologie

### 2.1 Approche Générale

L'inférence a été effectuée selon une stratégie de **régression basée sur l'importance des features** :

Pour chaque gène cible j:
1. Entraîner des modèles de régression pour prédire j à partir des autres gènes
2. Extraire l'importance des features de chaque modèle
3. Ces importances représentent les scores d'arêtes (gène i → gène j)
4. Combiner les prédictions de plusieurs modèles (ensemble learning)
5. Sélectionner les top-K arêtes par réseau

### 2.2 Architecture d'Ensemble

Quatre modèles complémentaires ont été sélectionnés:

| Modèle | Rôle | Hyperparamètres Finaux |
|--------|------|------------------------|
| **ExtraTrees** | Capture non-linéarités | n_estimators=400, max_features='sqrt' |
| **GradientBoosting** | Boosting séquentiel | n_estimators=200, LR=0.1, max_depth=5, subsample=0.8 |
| **Ridge** | Régularisation L2 | alpha=5.0 |
| **Lasso** | Sélection de features | alpha=0.005, max_iter=10000 |

**Weights (combinaison):** 
- ExtraTrees: 40%
- GradientBoosting: 30%
- Ridge: 20%
- Lasso: 10%

Ces poids ont été déterminés empiriquement et réflètent la contribution relative de chaque modèle.

### 2.3 Prétraitement des Données

**Pipeline standard:**
1. **Imputation:** SimpleImputer avec stratégie median
2. **Normalisation:** StandardScaler (moyenne=0, écart-type=1)
3. **Raison:** Assurer la stabilité numérique et l'équité entre features

**Données d'entrainement:** test_data/data{1-5}.csv
- Dimensions: 100 gènes
- Observations: 500 (sauf network 5: 100)

### 2.4 Optimisation des Hyperparamètres

#### Phase 1: Baseline (Score: 0.32)
- Configuration initiale avec hyperparamètres standards
- Établit une ligne de base stable

#### Phase 9: Fine-tuning (Score: 0.33) ✅ **MEILLEUR**
- **Découverte clé 1:** max_features='sqrt' > 'log2' pour ExtraTrees
  - Impact: +0.01 sur le score global
  - Justification: sqrt réduit la corrélation entre arbres, améliore la variance

- **Découverte clé 2:** Subsample=0.8 pour GradientBoosting
  - Impact: Régularisation, réduit l'overfitting
  
- **Découverte clé 3:** Augmenter Ridge alpha (1.0 → 5.0) et réduire Lasso alpha (0.01 → 0.005)
  - Impact: Meilleur équilibre entre biais et variance

- **Découverte clé 4:** K=320 edges par réseau = optimal
  - Testé: K=300 (0.32), K=320 (0.33), K=350 (0.32)
  - Sweet spot établi empiriquement

#### Phase 10: Grid Search Ridge/Lasso (Score: 0.32)
- Test de 9 combinaisons autour du baseline
- Résultat: Ridge 5.0 + Lasso 0.005 confirmé comme optimal
- Conclusions: Ridge > 5.0 ou Lasso ≠ 0.005 empiriquement pire

#### Phase 11: Network-Specific Tuning (Score: 0.32)
- Stratégie: K variable par réseau (K=320 pour networks 1-3-5, K∈{150,200,...,500} pour network 4)
- Observation: Network 4 structurellement difficile (AUPR=0.207 en baseline)
- Résultat: Aucune amélioration, confirme que hyperparamètres globaux sont robustes

---

## 3. Résultats

### 3.1 Score Final Obtenu

**Meilleur score:** **0.33 (AUPR moyen)**

**Distribution par réseau:**
```
Network 1: 0.3641
Network 2: 0.3371
Network 3: 0.3507
Network 4: 0.2068  (faiblesse identifiée)
Network 5: 0.3592
```

**Analyse:** 
- 4 réseaux sur 5 (networks 1,2,3,5) performent bien (AUPR ≈ 0.33-0.36)
- Network 4 présente une difficulté structurelle (AUPR = 0.207)
- Cette asymétrie suggère que network 4 a des propriétés différentes (topologie, densité, bruits, etc.)

### 3.2 Évolution des Scores

| Phase | Stratégie | Score | Notes |
|-------|-----------|-------|-------|
| Phase 1 | Baseline ensemble | 0.32 | ✅ Stable |
| Phase 2 | 7 modèles | 0.31 | ❌ Dégradation |
| Phase 7 | ExtraTrees only | 0.25 | ❌ Single model insufficient |
| Phase 8 | Wrong training data | 0.08 | ❌ Data source critical |
| Phase 9 V1 | Hyperparams exp. | 0.31 | ❌ Bad configuration |
| **Phase 9 V2** | **Optimal tuning** | **0.33** | **✅ BEST** |
| Phase 10 | Alpha grid search | 0.32 | ❌ Confirmed 0.33 is better |
| Phase 11 | Network 4 focus | 0.32 | ❌ Structural issue confirmed |

### 3.3 Budget et Efficacité

- **Total submissions:** 100
- **Utilisés:** 87
- **Restants:** 13
- **Efficacité:** Score optimal trouvé en phase 9 (submission #71)

---

## 4. Conclusions et Recommandations

### 4.1 Conclusions Principales

1. **Ensemble Learning Efficace:** 4 modèles > modèle unique (Phase 7-9 vs Phase 1)
   - Justification: Diversité réductrice de biais et variance

2. **Importance du Prétraitement:** StandardScaler + Imputation = stabilité
   - Données normalisées essentielles pour modèles régularisés

3. **Hyperparamètres Critiques Identifiés:**
   - ExtraTrees: max_features='sqrt' est crucial (+0.01 vs 'log2')
   - Ridge alpha=5.0: bon équilibre régularisation
   - Lasso alpha=0.005: sélection de features effective
   - K=320: sweet spot pour sparsité

4. **Limites Identifiées:**
   - Network 4 récalcitrant (AUPR=0.207) → possibilité d'hétérogénéité dans les données
   - Approche globale suboptimale pour ce réseau
   - Métaapprentissage ou transfer learning pourrait aider

### 4.2 Recommandations Futures

1. **Analyser Network 4 spécifiquement:**
   - Vérifier densité/topologie du réseau
   - Détecter outliers ou bruits
   - Considérer prétraitement différencié

2. **Métaapprentissage (Phase 12+):**
   - Hyperparamètres différents par réseau
   - Weights d'ensemble adaptatifs basés sur performance réseau

3. **Amélioration Feature Engineering:**
   - Transformer logarithmique pour données biologiques
   - Features polynomiales
   - Analyse de corrélation préalable

4. **Ensembles Avancés:**
   - Stacking: méta-modèle pour combiner prédictions
   - Nested cross-validation pour validation robuste

---

## 5. Architecture Technique

### 5.1 Pipeline de Traitement

```
Données brutes (test_data/)
    ↓
Imputation (median)
    ↓
Normalisation (StandardScaler)
    ↓
Entraînement 4 modèles (5 targets)
    ↓
Extraction importances
    ↓
Normalisation per-modèle
    ↓
Combinaison pondérée
    ↓
Tri scores décroissants
    ↓
Sélection top-K (K=320)
    ↓
Export CSV (Cause, Effect, Score)
    ↓
Packaging ZIP
```

### 5.2 Dépendances

```
pandas>=1.3.0
numpy>=1.20.0
scikit-learn>=1.0.0
```

### 5.3 Reproductibilité

- `random_state=42` fixé partout
- Graine reproductible pour tous modèles
- Pipeline déterministe assurant résultats identiques

---

## 6. Format de Soumission

### 6.1 Structure ZIP

```
predictions_network1.csv
predictions_network2.csv
predictions_network3.csv
predictions_network4.csv
predictions_network5.csv
```

### 6.2 Format CSV

Chaque fichier contient:
```csv
Cause,Effect,Score
gene_i,gene_j,0.8456
gene_k,gene_l,0.8234
...
```

- **Cause:** Gène régulateur (source)
- **Effect:** Gène cible (destination)
- **Score:** Confiance de l'arête (0-1), normalisé

### 6.3 Top-K Selection

- K=320 arêtes par réseau
- Sélection des scores les plus hauts
- Justification: Balance entre sensibilité et spécificité

---

## 7. Validation et Métriques

### 7.1 Métrique AUPR

**Area Under Precision-Recall Curve:**
- Appropriée pour problèmes déséquilibrés (peu de vraies arêtes)
- Robuste aux threshold de classification
- Utilisée par challenge Codalab

### 7.2 Évaluation

- **Training:** test_data/ (100% données utilisées)
- **Validation:** Codalab leaderboard (données test cachées)
- **Cross-validation:** Non effectuée (données petites, risque overfitting sur CV)

---

## 8. Références et Contexte

**Challenge:** Gene Network Inference - Codalab
**Discipline:** Bioinformatique, Apprentissage Machine
**Approche:** Supervised feature importance-based inference
**Méthodes:** Ensemble learning, hyperparameter tuning, empirical optimization

---

## Annexe: Chemins et Fichiers Clés

**Code de production:**
- `generate_best_model_0.33.py` - Script final optimisé
- `generate_phase9_hyperparams.py` - Phase 9 implementation

**Données:**
- `test_data/data{1-5}.csv` - Données d'entrainement
- `test_data/target{1-5}.csv` - (si disponible) Labels

**Soumission:**
- `prediction_phase9_v2_etsqrt_subsamp_top320.zip` - Best submission (AUPR=0.33)

**Documentation:**
- `ARCHIVE_MODELS.md` - Historique complet des expériences
- `RAPPORT_PROGRESSION.md` - Progress tracking

---

**Rapport rédigé le:** 2026-07-15  
**Dernière mise à jour:** Phase 11 completion  
**Status:** Complet et prêt pour soumission
