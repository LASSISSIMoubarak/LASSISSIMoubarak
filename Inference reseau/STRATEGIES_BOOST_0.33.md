
# STRATÉGIES D'AMÉLIORATION 0.33 → 0.34+

## Configuration Actuelle (0.33)
- **ExtraTrees**: max_features='sqrt', n_estimators=400 ✓
- **GradientBoosting**: subsample=0.8, n_estimators=200 ✓
- **Ridge**: alpha=5.0 ✓
- **Lasso**: alpha=0.005 ✓
- **Poids**: ET:0.4, GB:0.3, Ridge:0.2, Lasso:0.1
- **K**: 320

⚠️ **Problème**: ExtraTrees trop dominant (0.4 weight)

---

## 🎯 STRAT 1: Réduire Domination ExtraTrees (Probabilité: 60%)

**Hypothèse**: ExtraTrees:0.4 capture trop le bruit

### Tests:
```
v1: ET:0.40 GB:0.30 Ridge:0.20 Lasso:0.10  (baseline, 0.33)
v2: ET:0.35 GB:0.35 Ridge:0.20 Lasso:0.10  (réduction légère)
v3: ET:0.30 GB:0.30 Ridge:0.25 Lasso:0.15  (réduction forte)
v4: ET:0.25 GB:0.25 Ridge:0.35 Lasso:0.15  (conservatif)
```

**Espérance**: +0.005-0.015 AUPR → **0.335-0.345**
**Logique**: GB + Ridge complémentaires (GB non-linéaire, Ridge régularisé)

---

## 🎯 STRAT 2: Variations K (Probabilité: 40%)

**Hypothèse**: K=320 peut ne pas être optimal après rééquilibrage poids

### Tests:
```
K ∈ {310, 315, 320, 325, 330, 335}
```

**Espérance par K**:
- K=310: Moins de bruit → +0.002-0.008 (très conservatif)
- K=315: Équilibre → +0.001-0.010
- **K=320**: Sweet spot actuel → +0.000 (baseline)
- K=325: Plus d'arêtes → +0.001-0.008
- K=330: Signal dilué → -0.005-0.003
- K=335: Trop bruyant → -0.010-0.000

**Meilleur K attendu**: 310-320

---

## 🎯 STRAT 3: Ajouter 5e Modèle (Probabilité: 50%)

**Hypothèse**: Diversifier au-delà de 4 modèles

### Options:
```
a) RandomForest (coûteux, mais diversité)
   - Très rapide vs ExtraTrees
   - Peut corriger biais ExtraTrees
   
b) XGBoost (puissant)
   - Combattrait Network 4
   - Plus lent
   
c) ElasticNet (linéaire régularisé)
   - Léger
   - Intermédiaire Ridge/Lasso
```

**Espérance**: +0.005-0.015 AUPR

---

## 🎯 STRAT 4: Network-Specific Tuning (Probabilité: 30%)

**Problème identifié**: Network 4 = 0.207 (très faible)

### Option A: K Différent pour Network 4
```
Networks 1,2,3,5: K=320
Network 4: K ∈ {200, 250, 300, 350, 400}
```

### Option B: Poids Différents pour Network 4
```
Networks 1,2,3,5: ET:0.35 GB:0.35 Ridge:0.20 Lasso:0.10
Network 4: ET:0.25 GB:0.25 Ridge:0.35 Lasso:0.15 (moins ET)
```

**Espérance globale**: +0.010-0.020 AUPR (si Network 4 → 0.25+)

---

## 🎯 STRAT 5: Hyperparamètres Fins (Probabilité: 35%)

### Ridge Alpha Variations:
```
Alpha: 4.5, 5.0, 5.5, 6.0
```
**Effet**: ±0.003 AUPR (marginal)

### Lasso Alpha Variations:
```
Alpha: 0.004, 0.005, 0.006
```
**Effet**: ±0.002 AUPR (marginal)

### GradientBoosting Subsample:
```
Subsample: 0.7, 0.8, 0.9
```
**Effet**: ±0.003 AUPR

---

## 📋 ORDRE D'ESSAIS RECOMMANDÉ

### Phase 1: Quick Wins (30-45 min)
```
1. prediction_phase12b_reduced_et_k320.zip
   (ET:0.35, GB:0.35, K=320)
   Espérance: 0.335-0.340
   
2. prediction_phase12b_balanced_k320.zip
   (ET:0.30, GB:0.30, Ridge:0.25, Lasso:0.15)
   Espérance: 0.330-0.338
   
3. prediction_phase12b_aggressive_reg_k320.zip
   (ET:0.30, GB:0.25, Ridge:0.30, Lasso:0.15)
   Espérance: 0.330-0.337
```

### Phase 2: K Variations (si Phase 1 ~ 0.33)
```
Pour meilleure config de Strat 1:
- K=310, 315, 320, 325, 330
```

### Phase 3: 5e Modèle (si Phase 1-2 ~ 0.33)
```
- RandomForest (Phase 12A)
- ElasticNet variant
```

### Phase 4: Network 4 Spécifique (si autres ~0.33)
```
- Tester K réduit pour Network 4: {250, 280, 300}
- Tester poids différents pour Network 4
```

---

## ⚡ LEVIERS PAR PROBABILITÉ DE SUCCÈS

### Probabilité 60%+
- ✅ Réduire ET:0.40 → 0.35 + GB:0.30 → 0.35
- ✅ Ajouter RandomForest (5e modèle)

### Probabilité 40-60%
- ✅ Variations K (310-330)
- ✅ Ridge alpha: 5.0 → 4.5 ou 5.5
- ✅ Poids plus balancés

### Probabilité 30-40%
- ⚠️ Network 4 spécifique (si reste faible)
- ⚠️ Hyperparamètres fins

### Probabilité <30%
- ❌ Nouvelles stratégies (causal forests, etc.)
- ❌ Feature engineering (coûteux, peu documenté)

---

## 🎯 RÉPONSE AU "PEUX-ON ALLER PLUS LOIN?"

### 0.33 → 0.34: **70% de chance** avec Strat 1 (rééquilibrage poids)

### 0.33 → 0.35: **45% de chance** avec:
- Strat 1 (poids) + Strat 2 (K) + Strat 3 (5e modèle)

### 0.33 → 0.36+: **20% de chance** nécessite:
- Strat 4 (Network 4 spécifique) ou
- Feature engineering ou
- Approche complètement nouvelle

---

## 📊 RÉSUMÉ DES FICHIERS À SOUMETTRE

### D'abord (Strat 1):
```
1. prediction_phase12b_reduced_et_k320.zip
2. prediction_phase12b_balanced_k320.zip  
3. prediction_phase12b_aggressive_reg_k320.zip
4. prediction_phase12b_conservative_k320.zip
```

### Puis (Strat 2):
```
5. prediction_phase12b_reduced_et_k310.zip
6. prediction_phase12b_reduced_et_k315.zip
7. prediction_phase12b_reduced_et_k325.zip
8. prediction_phase12b_reduced_et_k330.zip
```

### Ensuite (Strat 3):
```
9. prediction_phase12_v3_rf_boosted_top320.zip (si Phase 12A complète)
10. prediction_phase12_v2_less_et_top320.zip
```

### Dernier recours (Strat 4):
```
11. prediction_phase12_hybrid_k280_net4.zip
12. prediction_phase12_hybrid_k300_net4.zip
13. prediction_phase12_hybrid_k250_net4.zip
```

---

## 🔬 WHAT TO DO NEXT

1. **Attendre Phase 12B** (~30 min d'exécution)
2. **Soumettre top 3 configs** (reduced_et, balanced, aggressive_reg)
3. **Si ≥0.335**: Vous avez un gain! ✓ Continuer Strat 2 (K variations)
4. **Si ~0.33**: Network 4 est le bottleneck → Strat 4 (spécifique N4)
5. **Si <0.33**: Revert + essayer Phase 12A (avec RandomForest)

