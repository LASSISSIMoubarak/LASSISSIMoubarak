# Archive de Modèles - Gene Network Inference Challenge

## Meilleur Score Actuel: **0.33**

### Modèle Gagnant
**File:** `prediction_phase9_v2_etsqrt_subsamp_top320.zip`
**Score:** 0.33
**Date:** 2026-07-13 09:35
**Configuration:** V2_etsqrt_subsample_top320

---

## Historique Complet des Submissions

| Rank | Score | Model | File | Hyperparameters | Date |
|------|-------|-------|------|-----------------|------|
| 1 | 0.33 | Phase 9 V2 K320 | prediction_phase9_v2_etsqrt_subsamp_top320.zip | ET:sqrt, GB:subsample0.8, Ridge:5.0, Lasso:0.005 | 2026-07-13 09:35 |
| 2 | 0.32 | Phase 9 V2 K350 | prediction_phase9_v2_etsqrt_subsamp_top350.zip | ET:sqrt, GB:subsample0.8, Ridge:5.0, Lasso:0.005 | 2026-07-13 09:36 |
| 3 | 0.32 | Phase 1 | prediction_ensemble_phase2_p2_xgb_boost_top320.zip | Phase 1 baseline | 2026-07-13 00:51 |
| 4 | 0.31 | Phase 9 V1 K320 | prediction_phase9_v1_etmore_lrlow_top320.zip | ET:600, GB:LR0.05, Ridge:2.0, Lasso:0.005 | 2026-07-13 09:38 |
| 5 | 0.31 | Phase 9 V1 K350 | prediction_phase9_v1_etmore_lrlow_top350.zip | ET:600, GB:LR0.05, Ridge:2.0, Lasso:0.005 | 2026-07-13 09:39 |
| 6 | 0.25 | Phase 7 | prediction_phase7_fast_top350.zip | ExtraTrees only, test_data/ | 2026-07-12 22:27 |

---

## Phases et Stratégies

### Phase 1: Baseline (0.32)
- **Code:** `generate_phase2_ensemble.py` (original)
- **Modèles:** ExtraTrees (0.25) + GradientBoosting (0.20) + Ridge (0.15) + Lasso (0.10)
- **Data:** test_data/ (100 dims)
- **Score:** 0.32 (stable)
- **Status:** ✅ Working baseline

### Phase 2: Expand with 7 Models (0.31-0.32)
- **Code:** `generate_phase2_ensemble.py`
- **Modèles:** Phase 1 + XGBoost + RandomForest + SVR
- **Score:** 0.31-0.32 (no improvement)
- **Status:** ❌ Not better

### Phase 7: ExtraTrees Only on test_data/ (0.25)
- **Code:** `generate_phase7_fast.py`
- **Modèles:** ExtraTrees only
- **Score:** 0.25 (worse)
- **Status:** ❌ Worse than baseline

### Phase 8: ExtraTrees on data_train/ (0.08)
- **Code:** `generate_phase8_correct.py`
- **Data:** data_train/ (WRONG - caused failure)
- **Score:** 0.08 (catastrophic)
- **Status:** ❌ Wrong training data

### Phase 9: Hyperparameter Tuning (0.31-0.33) ⭐
- **Code:** `generate_phase9_hyperparams.py`

#### Variant 1 (0.31)
- **Hyperparameters:**
  - ExtraTrees: 600 trees, max_features='log2'
  - GradientBoosting: 200 estimators, LR=0.05, max_depth=5
  - Ridge: alpha=2.0
  - Lasso: alpha=0.005, max_iter=10000
- **Weights:** ET:0.4, GB:0.3, Ridge:0.2, Lasso:0.1
- **Score:** 0.31 (worse)
- **Status:** ❌ LR too low

#### Variant 2 (0.33) ⭐ BEST
- **Hyperparameters:**
  - ExtraTrees: 400 trees, max_features='sqrt'
  - GradientBoosting: 200 estimators, LR=0.1, max_depth=5, subsample=0.8
  - Ridge: alpha=5.0
  - Lasso: alpha=0.005, max_iter=10000
- **Weights:** ET:0.4, GB:0.3, Ridge:0.2, Lasso:0.1
- **K-cutoffs tested:** 300 (0.32), 320 (0.33), 350 (0.32)
- **Score:** 0.33 with K=320 ⭐
- **Status:** ✅ BEST - ET:sqrt works better than log2!

---

## Key Findings

1. **ExtraTrees max_features:** 
   - `log2`: 0.32 (original baseline)
   - `sqrt`: 0.33 (better!) ✅
   
2. **K-cutoff sweet spot:** 320 (not 300, 350)

3. **Regularization matters:**
   - Ridge alpha=5.0 (higher) > alpha=1.0
   - Lasso alpha=0.005 (lower) > alpha=0.01
   - GB subsample=0.8 helps stability

4. **Data source critical:**
   - test_data/: 0.33 ✅
   - data_train/: 0.08 ❌

5. **More models ≠ Better:**
   - Phase 1 (4 models): 0.32
   - Phase 2 (7 models): 0.31-0.32 (not better)

---

## Next Experiments to Try

1. **Fine-tune K further:** 310-330 range
2. **Try max_features='log2' with sqrt regularization**
3. **Adjust Ridge alpha:** test 3.0, 4.0, 6.0, 7.0
4. **GradientBoosting:**
   - Lower max_depth: 3, 4
   - Higher subsample: 0.9, 0.95
5. **Feature engineering** on top of current best

---

## File Naming Convention

For easy tracking, files are named:
`prediction_phase{N}_{variant}_{hyperparams_shortcode}_top{K}.zip`

Example: 
- `prediction_phase9_v2_etsqrt_subsamp_top320.zip` 
  - Phase 9
  - Variant 2 
  - ET:sqrt + subsample
  - Top 320 edges per network

---

### Phase 10: Ridge & Lasso Alpha Tuning (✅ READY TO SUBMIT) 🎯
- **Code:** `generate_phase10_alphas.py`
- **Strategy:** 3×3 grid search around current best
  - Ridge alphas: [4.0, 5.0 (current), 6.0]
  - Lasso alphas: [0.004, 0.005 (current), 0.006]
- **Fixed:** ExtraTrees (sqrt, 400), GradientBoosting (subsample=0.8), K=320
- **Generated:** 9 submission files (all ~44 KB)
- **Expected:** 0.33 → 0.34+?
- **Status:** ✅ Complete - ready for Codalab submission
- **Tracker:** See PHASE10_CODALAB_TRACKER.md

---

## Submission Budget Status

- **Total:** 100 submissions
- **Used before Phase 10:** ~71
- **Phase 10:** 9 (✅ ready to submit)
- **Total after Phase 10:** ~80
- **Remaining:** ~20
- **Current best:** 0.33 (Phase 9 V2 K320)

**Next Decision:**
- If Phase 10 finds improvement: consider Phase 11 fine-tuning (max 10 more)
- If Phase 10 = 0.33: prepare final submission with best model

