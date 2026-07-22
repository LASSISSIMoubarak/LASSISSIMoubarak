"""
ANALYSE CRITIQUE DES RÉSULTATS - Diagnostic Corrigé
====================================================

Résultats observés:
  • Top-200: 0.21 (MEILLEUR)
  • Top-150: 0.20 (-5%)
  • ExtraTrees Top-100: 0.19 (-10%)
  • Correlation/Ensemble/Consensus: 0.12-0.15 (-40% à -45%)

CONCLUSION: Le diagnostic initial était FAUX!

❌ HYPOTHÈSE REJETÉE: "Réduire prédictions (Top-50) améliore généralisation"
   → Résultats: DÉGRADATION massive (-40% à -45%)

✓ NOUVELLE HYPOTHÈSE: "Qualité des prédictions TopK > Nombre"
   → Top-200 ExtraTrees = meilleur équilibre
   → Corrélation/Ensemble = capturent mal les patterns
   → Consensus = trop restrictif (perd vrais positifs)

STRATÉGIE CORRECTIVE:
========================

1. REVENIR À EXTRATREES Top-200 (0.21) = ligne de base
2. TESTER AUGMENTATION: Top-250, Top-300, Top-400
3. IGNORER les stratégies alternatives (correlation, MI, ensemble)
4. OPTIMISER LES HYPERPARAMÈTRES d'ExtraTrees

Rationale:
- Top-200 donne 0.21 (pas mauvais!)
- Réduction → dégradation (-40%)
- Donc augmentation peut améliorer?
- Ou ajuster modèle plutôt que K?
"""

print(__doc__)

import pandas as pd
import numpy as np

# Résumé des résultats
results = pd.DataFrame({
    'Stratégie': [
        'ExtraTrees Top-200 (original)',
        'ExtraTrees Top-150',
        'ExtraTrees Top-100',
        'Correlation Top-100',
        'Ensemble Top-50',
        'Consensus Majority Top-50',
        'Consensus Optimized Top-50'
    ],
    'Score': [0.21, 0.20, 0.19, 0.13, 0.13, 0.12, np.nan],  # Last not tested yet
    'Changement': ['', '-5%', '-10%', '-38%', '-38%', '-43%', '?']
})

print("\n" + "="*70)
print("RÉSUMÉ DES TESTS")
print("="*70)
print(results.to_string(index=False))

print("\n" + "="*70)
print("INSIGHTS CRITIQUES")
print("="*70)
print("""
1. ExtraTrees Top-200 DOMINE (-0.21 = meilleur)
   └─ Donc le modèle ML est bon
   └─ Donc le K=200 est bon pour ce dataset
   
2. Corrélation / Ensemble / Consensus = MAUVAIS (-38 à -43%)
   └─ Hypothesis: Patterns sont fortement non-linéaires
   └─ Hypothesis: Patterns nécessitent interactions (Trees)
   └─ Hypothesis: Données test_data/ ≠ données réelles du site
   
3. Réduire à Top-100 déjà -10%
   └─ Donc perte de prédictions = perte d'informations
   └─ Pas de surentraînement à réduire!
   
4. VRAIE CAUSE du problème initial?
   └─ Probablement: données test_data/ ne généralisent pas
   └─ Probablement: site utilise graphes différents
   └─ Probablement: patterns complexes que seul Trees capturent

CONCLUSION:
===========
❌ Arrêter l'approche de réduction (Top-50, Top-75, etc.)
✓ REVENIR à ExtraTrees
✓ TESTER Top-250, Top-300 (augmenter au lieu de réduire)
✓ AJUSTER hyperparamètres du modèle plutôt que K
""")

print("\n" + "="*70)
print("NOUVELLE STRATÉGIE - À FAIRE MAINTENANT")
print("="*70)
print("""
PHASE 1: Tester augmentation de K
─────────────────────────────────
• Générer prediction_extratrees_top250.zip (0.21 → 0.22-0.25?)
• Générer prediction_extratrees_top300.zip (0.21 → 0.22-0.25?)
• Générer prediction_extratrees_top400.zip (0.21 → 0.21-0.24?)
• Générer prediction_extratrees_top500.zip (0.21 → 0.20-0.23?)

PHASE 2: Si augmentation n'aide pas
───────────────────────────────────
• Ajuster hyperparamètres ExtraTrees:
  ├─ n_estimators: 400 → 250, 600, 1000
  ├─ max_features: 'sqrt' → 'log2', 0.5, 0.3
  ├─ min_samples_leaf: 1 → 2, 3, 5
  ├─ max_depth: None → 10, 15, 20
  └─ random_state: 0 → 42, 123 (randomization)

PHASE 3: Si toujours < 0.25
──────────────────────────
• Tester GradientBoosting instead of ExtraTrees
• Tester XGBoost ou LightGBM
• Tester Lasso ou Ridge Regression
• Investiguer structure données site

ABANDON (stratégies qui ont échoué):
════════════════════════════════════
❌ Corrélation simple
❌ Mutual Information
❌ Ensemble Vote
❌ Consensus ≥2
❌ Réduction agressif (Top-50, Top-75, Top-100)
""")
