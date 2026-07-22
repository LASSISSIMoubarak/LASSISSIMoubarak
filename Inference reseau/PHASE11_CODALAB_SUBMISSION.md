# PHASE 11 - CODALAB SUBMISSION TRACKER

## 🎯 Mission: Reach 0.40 by fixing Network 4

**Current Baseline:** 0.33 (Phase 9 V2 with K=320 everywhere)
**Problem:** Network 4 scores only 0.207, dragging average down

**Solution:** Test different K values for Network 4 while keeping K=320 for networks 1,2,3,5

---

## 📤 7 Fichiers Prêts à Soumettre

| # | K Network4 | Fichier | Expected | Status |
|---|-----------|---------|----------|--------|
| 1 | 150 | prediction_phase11_k320_net1235_k150_net4_1.zip | Very aggressive (prob. worse) | ⏳ Ready |
| 2 | 200 | prediction_phase11_k320_net1235_k200_net4_2.zip | Aggressive | ⏳ Ready |
| 3 | 250 | prediction_phase11_k320_net1235_k250_net4_3.zip | Moderate aggressive | ⏳ Ready |
| 4 | 300 | prediction_phase11_k320_net1235_k300_net4_4.zip | Moderate | ⏳ Ready |
| 5 | 350 | prediction_phase11_k320_net1235_k350_net4_5.zip | **PROBABLE BEST** 👑 | ⏳ Ready |
| 6 | 400 | prediction_phase11_k320_net1235_k400_net4_6.zip | Conservative | ⏳ Ready |
| 7 | 500 | prediction_phase11_k320_net1235_k500_net4_7.zip | Very conservative | ⏳ Ready |

---

## 📊 Résultats Codalab

**INSTRUCTIONS:** Remplis ce tableau au fur et à mesure des soumissions

| K Net4 | AUPR Net1 | AUPR Net2 | AUPR Net3 | AUPR Net4 | AUPR Net5 | Average | Notes |
|--------|-----------|-----------|-----------|-----------|-----------|---------|-------|
| 150    | ? | ? | ? | ? | ? | ? | |
| 200    | ? | ? | ? | ? | ? | ? | |
| 250    | ? | ? | ? | ? | ? | ? | |
| 300    | ? | ? | ? | ? | ? | ? | |
| **350**| ? | ? | ? | ? | ? | ? | ← Probablement meilleur |
| 400    | ? | ? | ? | ? | ? | ? | |
| 500    | ? | ? | ? | ? | ? | ? | |

**Baseline (Phase 9 V2, K=320 everywhere):** 
- AUPR: 0.364 | 0.337 | 0.351 | 0.207 | 0.359 = **0.3242 avg**

---

## 💡 Analyse Attendue

### Best Case Scenario
- K=350 finds sweet spot
- Network 4: 0.207 → 0.32+
- Average: 0.3242 → 0.34+ ✅
- **Use for final submission!**

### Good Case Scenario  
- Multiple K values > 0.33
- Average: 0.33+ (tie with baseline)
- **Keep Phase 9 V2 as safety**

### Bad Case Scenario
- All scores ≤ 0.32 (regression)
- **Revert to Phase 9 V2 (0.33) for final**

---

## 🎬 Next Steps

1. **Submit each ZIP** to Codalab competition
2. **Record scores** in the table above
3. **Identify best K** for Network 4
4. **Decision:**
   - If best > 0.33: Use it!
   - If best = 0.33: Use Phase 9 V2
   - If best < 0.33: Use Phase 9 V2

---

## 📈 Budget Status

- **Total:** 100 submissions
- **Used before Phase 11:** 80 (Phase 1-10)
- **Phase 11:** 7 submissions
- **Total used:** 87/100
- **Remaining buffer:** 13 submissions

**Strategy:**
- If Phase 11 finds improvement → Prepare FINAL SUBMISSION
- If Phase 11 fails → Use Phase 9 V2, keep 13 as buffer
- **Reserve 2-3 for final edge case adjustments**

---

## 🎯 Goal Reminder

**Reach 0.40:** Very ambitious!
- Would need massive improvement in Network 4
- More realistic target: **0.35+** (better than baseline 0.33)

**Minimum Success:** > 0.33 (beat baseline)

