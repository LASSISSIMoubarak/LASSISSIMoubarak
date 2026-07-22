# Rapport de Progression - Gene Network Inference

## Status Actuel

**Score Meilleur:** 0.33 ✅
**Fichier:** `prediction_phase9_v2_etsqrt_subsamp_top320.zip`
**Date:** 2026-07-13 09:35

---

## Progression

```
Baseline (Phase 1):           0.32
Phase 2 (7 modèles):          0.31-0.32  ❌
Phase 7 (ExtraTrees only):    0.25       ❌
Phase 8 (data_train/):        0.08       ❌
Phase 9 V1 (ET:600, LR:0.05): 0.31       ❌
Phase 9 V2 (ET:sqrt):         0.33       ✅ BEST
```

**Amélioration:** +0.01 (0.32 → 0.33)

---

## Ce Qui a Marché

### 1. ExtraTrees max_features='sqrt'
- **Before:** max_features='log2' → 0.32
- **After:** max_features='sqrt' → 0.33
- **Conclusion:** sqrt est mieux pour ce problème!

### 2. GradientBoosting subsample=0.8
- Ajouter de la régularisation aide
- Réduit l'overfitting

### 3. Ridge alpha=5.0 (plus élevé)
- Régularisation plus forte
- Pénalise plus les coefficients

### 4. Lasso alpha=0.005 (plus bas)
- Moins de sparsité
- Permet plus de features

### 5. K=320 est optimal
- K=300: 0.32
- K=320: 0.33 ✅
- K=350: 0.32
- Sweet spot = 320

---

## Ce Qui N'a Pas Marché

1. **Augmenter ExtraTrees trees (600 au lieu de 400):** Pire (0.31)
2. **Réduire learning_rate (0.05):** Pire (0.31)
3. **Ajouter 7 modèles au lieu de 4:** Pas d'amélioration
4. **Utiliser data_train/ pour training:** Catastrophique (0.08)

---

## Prochaines Étapes Recommandées

### High Priority (Likely to improve)
1. **Fine-tune alpha values:**
   - Ridge: test 3.0, 4.0, 6.0, 7.0, 10.0
   - Lasso: test 0.003, 0.004, 0.006, 0.007

2. **Optimize K further:**
   - Test 310, 312, 314, 316, 318, 322, 324, 326, 328, 330
   - Find exact peak in 310-330 range

3. **Combine sqrt with other features:**
   - max_features='sqrt' seems critical
   - Try max_features=0.5 (50% of features)

4. **GradientBoosting subsample tuning:**
   - Current: 0.8
   - Test: 0.7, 0.75, 0.85, 0.9, 0.95

### Medium Priority
5. **Ensemble weights fine-tuning:**
   - Current: ET:0.4, GB:0.3, Ridge:0.2, Lasso:0.1
   - Try: ET:0.5, GB:0.2, Ridge:0.2, Lasso:0.1
   - Try: ET:0.35, GB:0.35, Ridge:0.2, Lasso:0.1

6. **Feature engineering:**
   - Normalize differently?
   - Log-transform data?
   - Polynomial features?

### Low Priority (Unlikely to help much)
7. Add new models (already tried, didn't help)
8. Different preprocessing

---

## Budget Check

- **Total:** 100 submissions
- **Used:** ~73 (Phase 1, 2, 7, 8, 9)
- **Remaining:** ~27
- **Recommended for Phase 10:** 10-15 submissions

---

## Phase 10 Plan

**Objective:** Reach 0.35+

**Strategy:** Fine-tune hyperparameters systematically

```python
# Pseudocode for Phase 10
ridge_alphas = [3.0, 4.0, 5.5, 6.0, 7.0]  # Current: 5.0
lasso_alphas = [0.003, 0.004, 0.006]      # Current: 0.005
k_values = [310, 315, 320, 325, 330]       # Current: 320

# Grid search best combination
# Expect: 0.33 → 0.34 → 0.35
```

---

## Archive Files Created

1. **ARCHIVE_MODELS.md** - Cette documentation
2. **generate_best_model_0.33.py** - Code exact du meilleur modèle
3. **generate_phase9_hyperparams.py** - Code pour reproduire Phase 9

---

## Key Learnings

1. **Small hyperparameter changes matter:** sqrt vs log2 = +0.01
2. **K-cutoff has a sweet spot:** Not always "more is better"
3. **Regularization is important:** subsample, alpha tuning
4. **More models ≠ better:** Diversity doesn't help here
5. **Right training data critical:** test_data/ not data_train/
6. **Ensemble approach works:** Simple weighted vote is effective

