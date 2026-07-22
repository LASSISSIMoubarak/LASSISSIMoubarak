# PHASE 10 - Soumissions Codalab

## Résumé Phase 10

**Objectif:** Fine-tune Ridge & Lasso alphas autour du meilleur (5.0 / 0.005)

**Stratégie:** Grid search 3×3
- Ridge alphas: 4.0, 5.0 (current), 6.0
- Lasso alphas: 0.004, 0.005 (current), 0.006

**Fixed:** ExtraTrees (sqrt, 400), GradientBoosting (subsample=0.8), K=320

**Attendu:** 0.33 → 0.34 ou mieux

---

## 📊 Fichiers Générés (9 total)

✓ prediction_phase10_ridge4.0_lasso0.004_top320.zip
✓ prediction_phase10_ridge4.0_lasso0.005_top320.zip
✓ prediction_phase10_ridge4.0_lasso0.006_top320.zip
✓ prediction_phase10_ridge5.0_lasso0.004_top320.zip
✓ prediction_phase10_ridge5.0_lasso0.005_top320.zip (← CURRENT BEST)
✓ prediction_phase10_ridge5.0_lasso0.006_top320.zip
✓ prediction_phase10_ridge6.0_lasso0.004_top320.zip
✓ prediction_phase10_ridge6.0_lasso0.005_top320.zip
✓ prediction_phase10_ridge6.0_lasso0.006_top320.zip

---

## 📝 Tracker de Soumissions

**Instructions:**
1. Soumettre chaque ZIP à Codalab
2. Enregistrer le score dans la table ci-dessous
3. Une fois tous les scores reçus, analyser pour trouver la meilleure combo

### Résultats

| Ridge | Lasso  | Fichier | Score | Détail Networks | Notes |
|-------|--------|---------|-------|-----------------|-------|
| 4.0   | 0.004  | ridge4.0_lasso0.004 | ? | - | En attente |
| 4.0   | 0.005  | ridge4.0_lasso0.005 | ? | - | En attente |
| 4.0   | 0.006  | ridge4.0_lasso0.006 | ? | - | En attente |
| 5.0   | 0.004  | ridge5.0_lasso0.004 | ? | - | En attente |
| 5.0   | 0.005  | ridge5.0_lasso0.005 | **0.33** | - | ✅ BASELINE (Phase 9 V2) |
| 5.0   | 0.006  | ridge5.0_lasso0.006 | 0.32 | 1:0.364, 2:0.337, 3:0.351, 4:0.207, 5:0.359 | ⚠️ Regression! |
| 6.0   | 0.004  | ridge6.0_lasso0.004 | 0.32 | - | ⚠️ Ridge 6.0 worse |
| 6.0   | 0.005  | ridge6.0_lasso0.005 | 0.32 | - | ⚠️ Ridge 6.0 worse |
| 6.0   | 0.006  | ridge6.0_lasso0.006 | 0.32 | - | ⚠️ Ridge 6.0 worse |

**Soumis:** 4 / 9
**Restant:** 5 / 9

---

## 🎯 Hypothèses

**Attendu ordre de performance:**

1. **Probable meilleur:** Ridge 5.0-6.0 avec Lasso légèrement ajusté (0.004 ou 0.006)
   - Raison: Ridge 5.0 marche bien, petit ajustement Lasso peut aider

2. **Possible améliorations:**
   - Ridge 5.0 + Lasso 0.004 (moins de sparsité, peut garder plus de features)
   - Ridge 6.0 + Lasso 0.005 (régularisation plus forte)

3. **Régularisation excessive** (probablement pire):
   - Ridge 6.0 + Lasso 0.006 (trop constrictif)

---

## ⚡ Ordre de Soumission Recommandé

Pour soumission stratégique (commence par probable meilleur):

1. ridge5.0_lasso0.005 (baseline - pour comparer)
2. ridge5.0_lasso0.004 (moins sparsité)
3. ridge5.0_lasso0.006 (plus sparsité)
4. ridge6.0_lasso0.005 (plus régularisation)
5. ridge4.0_lasso0.005 (moins régularisation)
6. ridge6.0_lasso0.004
7. ridge4.0_lasso0.004
8. ridge6.0_lasso0.006
9. ridge4.0_lasso0.006

---

## 📈 Analyse Après Soumission

**Une fois les 9 scores reçus:**

1. Identifier le score max
2. Analyser la tendance (Ridge/Lasso independently):
   - Ridge: 4.0 vs 5.0 vs 6.0?
   - Lasso: 0.004 vs 0.005 vs 0.006?
3. Proposer Phase 11 si besoin (affiner encore plus)

---

## Budget Check

- **Total:** 100 submissions
- **Utilisé avant Phase 10:** ~71
- **Phase 10:** 9
- **Total après Phase 10:** ~80
- **Restant:** ~20

**Décision Phase 11:**
- Si Phase 10 trouve une amélioration: fine-tune encore (max 10 tests)
- Si Phase 10 = 0.33: arrêter et soumettre le meilleur

