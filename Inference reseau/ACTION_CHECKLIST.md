# ✅ CHECKLIST: AMÉLIORATION 0.33 → 0.34+

## 📋 FICHIERS GÉNÉRÉS

Une fois Phase 12C terminée, vous aurez:

### IMMÉDIATEMENT UTILISABLE (Phase 12C - 20-25 min):
- [ ] `prediction_phase12c_test1_reduced_et.zip` ← **TESTER D'ABORD**
  - Config: ET:0.35, GB:0.35, Ridge:0.20, Lasso:0.10
  - Espérance: 0.335-0.340
  
- [ ] `prediction_phase12c_test2_balanced.zip` ← **TESTER EN SECOND**
  - Config: ET:0.30, GB:0.30, Ridge:0.25, Lasso:0.15
  - Espérance: 0.330-0.338

### À VENIR (Phase 12B - 45-60 min):
- [ ] `prediction_phase12b_reduced_et_k310.zip`
- [ ] `prediction_phase12b_reduced_et_k315.zip`
- [ ] `prediction_phase12b_reduced_et_k320.zip`
- [ ] `prediction_phase12b_reduced_et_k325.zip`
- [ ] `prediction_phase12b_reduced_et_k330.zip`
- [ ] (+ 25 autres configs)

### BONUS (Phase 12A - 1-2h):
- [ ] `prediction_phase12_v3_rf_boosted_top320.zip` (avec RandomForest)
- [ ] `prediction_phase12_v2_less_et_top320.zip`
- [ ] (+ 14 autres configs)

---

## 🎯 PLAN SUBMISSION CODALAB

### ÉTAPE 1: Tests Rapides (30 min après Phase 12C)
```
1. Soumettre: prediction_phase12c_test1_reduced_et.zip
   Attendre score...
   
   SI score ≥ 0.335:   ✓ Amélioration confirmée!
   SI score = 0.33:    → Essayer TEST 2
   SI score < 0.33:    → Revert à baseline 0.33
```

### ÉTAPE 2: Variations K (si Phase 1 ≥ 0.335)
```
2. Soumettre: prediction_phase12b_reduced_et_k310.zip
3. Soumettre: prediction_phase12b_reduced_et_k315.zip
4. Soumettre: prediction_phase12b_reduced_et_k320.zip (déjà testé)
5. Soumettre: prediction_phase12b_reduced_et_k325.zip
6. Soumettre: prediction_phase12b_reduced_et_k330.zip

Objectif: Trouver K optimal pour +0.001-0.005 supplémentaires
```

### ÉTAPE 3: 5e Modèle (si Phase 1-2 ~ 0.33)
```
7. Soumettre: prediction_phase12_v3_rf_boosted_top320.zip
   Ajoute RandomForest pour diversité
   Espérance: +0.005-0.015
```

### ÉTAPE 4: Spécialisé Network 4 (si Phase 1-3 ~ 0.33)
```
8. Soumettre: prediction_phase12_hybrid_k280_net4.zip
   K réduit pour Network 4 (problématique)
```

---

## 🔍 CRITÈRES DE SUCCÈS

| Étape | Score Cible | Status | Action |
|-------|-----------|--------|--------|
| Étape 1 (TEST 1) | ≥0.335 | ✓ SUCCESS | Continuer Étape 2 |
| Étape 1 (TEST 1) | 0.330-0.334 | ⚠ MARGINAL | Essayer TEST 2 + Étape 2 |
| Étape 1 (TEST 1) | <0.330 | ✗ FAIL | Revert + analyser |
| Étape 2 (K var.) | ≥0.338 | ✓ SUCCESS | Arrêter, soumis meilleur |
| Étape 3 (RF) | ≥0.340 | ✓ EXCELLENT | Arrêter |

---

## 💡 POINTS CLÉS À RETENIR

1. **ExtraTrees 0.40 est trop dominant**
   - Solution: Réduire à 0.35, boost GB à 0.35

2. **Diversité d'ensemble crucial**
   - 4 modèles > 1 modèle
   - 5 modèles > 4 modèles

3. **Network 4 est le bottleneck**
   - Reste faible (0.207) même après optimisation
   - Nécessite approche spécifique si temps

4. **K=320 proche du sweet spot**
   - Variations ±10-15 probablement peu utiles
   - Plus utile après rééquilibrage poids

---

## 🚀 ACTIONS IMMÉDIATES

```
FAIRE MAINTENANT:
□ Lire QUICK_SUMMARY_FR.md (2 min)
□ Attendre Phase 12C (20-25 min)

DÈS QUE 12C FINI:
□ Soumettre prediction_phase12c_test1_reduced_et.zip
□ Noter le score obtenu
□ Attendre feedback CodaLab

SI SCORE ≥ 0.335:
□ Procéder Étape 2 (variations K)
□ Tester K=310, 315, 320, 325, 330

SI SCORE ~0.33:
□ Attendre Phase 12B complet
□ Tester autre config de poids

SI SCORE <0.33:
□ Analyser: pourquoi baisse?
□ Revert baseline 0.33
□ Chercher erreur
```

---

## 📞 SUPPORT

Questions fréquentes:

**Q: Pourquoi réduire ET de 0.40 à 0.35?**
A: Parce que ExtraTrees capture bruit sur données génomiques bruyantes. 
   GB + Ridge regularisent mieux.

**Q: Peut-on aller au-delà de 0.35?**
A: Probablement 0.34-0.35 réaliste. 
   Pour 0.36+: besoin Network 4 spécifique ou feature engineering.

**Q: Combien de temps Phase 12C?**
A: ~20-25 min (5 networks × 4 modèles × 99 targets)

**Q: Et si Phase 12C génère erreur?**
A: Réessayer. Si persiste: network 4 ou données corrompues.

