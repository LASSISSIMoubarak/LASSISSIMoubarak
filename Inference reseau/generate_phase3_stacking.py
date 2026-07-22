#!/usr/bin/env python3
"""
PHASE 3: STACKING avec Meta-Learner

Problème Phase 2: Vote pondéré sur 7 modèles n'a pas amélioré
Raison: Poids fixes mauvais, ou modèles mal combinés

Solution Phase 3: Stacking
  1. Train 4 "base learners" (Phase 1)
  2. Générer features de meta-learner (predictions du Step 1)
  3. Train meta-learner (Ridge) sur ces features
  4. Meta-learner apprend les POIDS optimaux automatiquement!

Avantage:
  • Poids sont appris, pas hardcodés
  • Meta-learner = Ridge (simple, régularisé, stable)
  • Devrait découvrir meilleure combinaison
  
Espoir: 0.32 → 0.38-0.45+
"""

import pandas as pd
import numpy as np
import os
import zipfile
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.model_selection import cross_val_predict
import warnings
warnings.filterwarnings('ignore')

os.chdir(r"c:/Users/lassi/projet/Inference reseau")

def preprocess(df):
    """Impute + Standardize"""
    imp = SimpleImputer(strategy='median')
    X = imp.fit_transform(df)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    return pd.DataFrame(X, columns=df.columns)

def train_stacking_model(df, n_splits=3):
    """
    Train stacking model with cross-validation
    
    Base learners: ExtraTrees, GB, Ridge, Lasso
    Meta learner: Ridge
    """
    
    base_scores_by_target = {}
    
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        
        if len(y) < n_splits:
            n_splits = max(2, len(y) - 1)
        
        try:
            # Get base learner predictions via cross-validation
            predictions_et = cross_val_predict(
                ExtraTreesRegressor(n_estimators=400, max_features='log2', random_state=42, n_jobs=-1),
                X, y, cv=n_splits
            )
            
            predictions_gb = cross_val_predict(
                GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42),
                X, y, cv=n_splits
            )
            
            predictions_ridge = cross_val_predict(
                Ridge(alpha=1.0),
                X, y, cv=n_splits
            )
            
            predictions_lasso = cross_val_predict(
                Lasso(alpha=0.01, max_iter=10000),
                X, y, cv=n_splits
            )
            
            # Meta features: stack predictions as features
            meta_features = np.column_stack([
                predictions_et,
                predictions_gb,
                predictions_ridge,
                predictions_lasso
            ])
            
            # Train meta learner on meta features
            meta_learner = Ridge(alpha=0.1)  # Light regularization
            meta_learner.fit(meta_features, y)
            
            # Get final predictions by training base learners on full data and applying meta learner
            et = ExtraTreesRegressor(n_estimators=400, max_features='log2', random_state=42, n_jobs=-1)
            et.fit(X, y)
            et_scores = et.feature_importances_
            
            gb = GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42)
            gb.fit(X, y)
            gb_scores = gb.feature_importances_
            
            ridge = Ridge(alpha=1.0)
            ridge.fit(X, y)
            ridge_scores = np.abs(ridge.coef_)
            
            lasso = Lasso(alpha=0.01, max_iter=10000)
            lasso.fit(X, y)
            lasso_scores = np.abs(lasso.coef_)
            
            # Combine base scores using learned meta weights
            # But for feature importance, we need to combine appropriately
            meta_coef = meta_learner.coef_  # [w_et, w_gb, w_ridge, w_lasso]
            
            # Normalize coefficients to be positive weights
            meta_coef_abs = np.abs(meta_coef)
            meta_weights = meta_coef_abs / (meta_coef_abs.sum() + 1e-10)
            
            # Combine scores with learned weights
            combined_scores = (
                meta_weights[0] * et_scores +
                meta_weights[1] * gb_scores +
                meta_weights[2] * ridge_scores +
                meta_weights[3] * lasso_scores
            )
            
            base_scores_by_target[target] = {
                'combined': combined_scores,
                'features': X.columns.tolist(),
                'weights': meta_weights
            }
            
        except Exception as e:
            print(f"  Error for target {target}: {e}")
            continue
    
    return base_scores_by_target

def generate_stacking_predictions(k_value=300, stacking_name="stacking", verbose=True):
    """Generate stacking predictions"""
    
    if verbose:
        print(f"\n--- Top-{k_value} ({stacking_name}) ---")
    
    test_files = [f'test_data/data{i}.csv' for i in range(1, 6)]
    all_predictions = []
    
    for g in range(1, 6):
        test_file = test_files[g-1]
        
        try:
            df = pd.read_csv(test_file)
            df_proc = preprocess(df)
            
            # Train stacking model
            scores_by_target = train_stacking_model(df_proc)
            
            # Combine all predictions
            all_pairs = []
            for target, score_info in scores_by_target.items():
                combined_scores = score_info['combined']
                features = score_info['features']
                
                for feat, score in zip(features, combined_scores):
                    if score > 0:
                        all_pairs.append((feat, target, float(score)))
            
            preds_df = pd.DataFrame(all_pairs, columns=['Cause', 'Effect', 'Score'])
            
            if len(preds_df) > 0:
                preds_df = preds_df.sort_values('Score', ascending=False).head(k_value)
                preds_df['Score'] = preds_df['Score'] / preds_df['Score'].sum()
            
            out_csv = f'predictions_network{g}.csv'
            preds_df.to_csv(out_csv, index=False)
            all_predictions.append(len(preds_df))
            
            if verbose:
                print(f"  Network {g}: {len(preds_df)} predictions")
        
        except Exception as e:
            print(f"  Network {g}: ERROR - {e}")
            import traceback
            traceback.print_exc()
            all_predictions.append(0)
    
    # Create ZIP
    zip_path = f'prediction_stacking_{stacking_name}_top{k_value}.zip'
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for g in range(1, 6):
            csv_file = f'predictions_network{g}.csv'
            if os.path.exists(csv_file):
                zf.write(csv_file, arcname=os.path.basename(csv_file))
    
    total = sum(all_predictions)
    if verbose:
        print(f"  ✓ Created {zip_path} ({total} total predictions)")
    
    return zip_path

# MAIN EXECUTION
print("\n" + "="*70)
print("PHASE 3: STACKING avec Meta-Learner")
print("="*70)

print("""
ARCHITECTURE:
═════════════════════════════════════════════════════════════════

Base Learners (4 modèles Phase 1):
  1. ExtraTreesRegressor (400 trees)
  2. GradientBoostingRegressor (200 est.)
  3. Ridge Regression
  4. Lasso Regression

Meta-Learner:
  Ridge Regression (alpha=0.1)
  └─ Apprend les poids optimaux automatiquement!

Processus:
  1. Cross-validation: Get base learner predictions
  2. Stack predictions as meta-features
  3. Train Ridge on meta-features to learn optimal weights
  4. Apply learned combination to new data

Avantage vs Phase 2:
  • Poids optimaux = APPRIS (pas hardcodés)
  • Régularisation Ridge = Stabilité
  • Devrait découvrir meilleure combinaison
  
Espoir: 0.32 → 0.38-0.45+ (possiblement 0.50+!)
""")

# Generate stacking variants
stacking_configs = [
    {'k': 300, 'name': 'v1_balanced'},
    {'k': 320, 'name': 'v2_tuned'},
    {'k': 350, 'name': 'v3_aggressive'},
]

generated_files = []
for config in stacking_configs:
    try:
        zip_file = generate_stacking_predictions(
            k_value=config['k'],
            stacking_name=config['name'],
            verbose=True
        )
        generated_files.append((config['name'], zip_file))
    except Exception as e:
        print(f"✗ Error generating {config['name']}: {e}")

print("\n" + "="*70)
print("SUMMARY - PHASE 3 STACKING")
print("="*70)
print(f"\n✓ Generated {len(generated_files)} Stacking ZIP files:\n")

for name, filepath in generated_files:
    from pathlib import Path
    if os.path.exists(filepath):
        file_size = Path(filepath).stat().st_size
        print(f"  • prediction_stacking_{name}_top*.zip ({file_size} bytes)")

print("\n" + "="*70)
print("SUBMISSION PRIORITY - PHASE 3")
print("="*70)
print("""
TIER 1 (Start here):
  1. prediction_stacking_v1_balanced_top300.zip
  2. prediction_stacking_v2_tuned_top320.zip
  3. prediction_stacking_v3_aggressive_top350.zip

EXPECTED: 
  • Phase 1 (Simple Ensemble): 0.32
  • Phase 2 (Vote Pondéré 7 modèles): 0.31-0.32 (no improvement)
  • Phase 3 (Stacking): 0.38-0.45+ (espoir!)
  
  If ≥ 0.40: Excellent! Very close to 0.60, continue Phase 4
  If 0.35-0.40: Good improvement! Could be limit, try Phase 4
  If < 0.35: Unexpected, might need different approach

NEXT PHASE (if needed):
  - Phase 4: Feature engineering using data_train/
  - Target: Eventually 0.50+ toward 0.60

Budget: ~40 submissions remaining
""")

print("\n✓ All Phase 3 stacking files ready for submission!")
print("\nRECOMMENDATION: Soumettez les 3 fichiers Phase 3 maintenant!")
