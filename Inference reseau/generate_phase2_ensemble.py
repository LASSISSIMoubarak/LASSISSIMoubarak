#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 2: Enrichir l'ensemble Phase 1 avec 3 nouveaux modèles puissants

Phase 1 (0.32): ExtraTrees + GradientBoosting + Ridge + Lasso
Phase 2 (?) : + XGBoost + RandomForest + SVR

Stratégie: Ajouter des modèles diversifiés
  - XGBoost: Très puissant, souvent meilleur que GB
  - RandomForest: Régularité, sélection bootstrap
  - SVR: Non-linéaire, kernel RBF
  
Ensemble combiné (7 modèles):
  Weight ExtraTrees: 0.25   (bon performer)
  Weight GradientBoosting: 0.20
  Weight Ridge: 0.15
  Weight Lasso: 0.10
  Weight XGBoost: 0.15     (nouveau puissant)
  Weight RandomForest: 0.10  (nouveau)
  Weight SVR: 0.05          (nouveau exploration)
"""

import pandas as pd
import numpy as np
import os
import zipfile
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.svm import SVR
import warnings
warnings.filterwarnings('ignore')

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️  XGBoost not installed, trying to install...")
    os.system("pip install xgboost -q")
    try:
        from xgboost import XGBRegressor
        XGBOOST_AVAILABLE = True
    except:
        XGBOOST_AVAILABLE = False

os.chdir(r"c:/Users/lassi/projet/Inference reseau")

def preprocess(df):
    """Impute + Standardize"""
    imp = SimpleImputer(strategy='median')
    X = imp.fit_transform(df)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    return pd.DataFrame(X, columns=df.columns)

def train_phase2_ensemble(df):
    """Train 7 models (Phase 1 + Phase 2)"""
    
    rows_by_model = {
        'extratrees': [],
        'gradient': [],
        'ridge': [],
        'lasso': [],
        'xgboost': [],
        'randomforest': [],
        'svr': []
    }
    
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        
        try:
            # 1. ExtraTreesRegressor (Phase 1)
            et = ExtraTreesRegressor(n_estimators=400, max_features='log2', random_state=42, n_jobs=-1)
            et.fit(X, y)
            for col, imp in zip(X.columns, et.feature_importances_):
                if imp > 0:
                    rows_by_model['extratrees'].append((col, target, float(imp)))
            
            # 2. GradientBoostingRegressor (Phase 1)
            gb = GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42)
            gb.fit(X, y)
            for col, imp in zip(X.columns, gb.feature_importances_):
                if imp > 0:
                    rows_by_model['gradient'].append((col, target, float(imp)))
            
            # 3. Ridge (Phase 1)
            ridge = Ridge(alpha=1.0)
            ridge.fit(X, y)
            coefs = np.abs(ridge.coef_)
            for col, coef in zip(X.columns, coefs):
                if coef > 0:
                    rows_by_model['ridge'].append((col, target, float(coef)))
            
            # 4. Lasso (Phase 1)
            lasso = Lasso(alpha=0.01, max_iter=10000)
            lasso.fit(X, y)
            coefs = np.abs(lasso.coef_)
            for col, coef in zip(X.columns, coefs):
                if coef > 0:
                    rows_by_model['lasso'].append((col, target, float(coef)))
            
            # 5. XGBoost (Phase 2) - NEW
            if XGBOOST_AVAILABLE:
                try:
                    xgb = XGBRegressor(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42, verbosity=0)
                    xgb.fit(X, y)
                    for col, imp in zip(X.columns, xgb.feature_importances_):
                        if imp > 0:
                            rows_by_model['xgboost'].append((col, target, float(imp)))
                except:
                    pass
            
            # 6. RandomForestRegressor (Phase 2) - NEW
            rf = RandomForestRegressor(n_estimators=200, max_features='sqrt', random_state=42, n_jobs=-1)
            rf.fit(X, y)
            for col, imp in zip(X.columns, rf.feature_importances_):
                if imp > 0:
                    rows_by_model['randomforest'].append((col, target, float(imp)))
            
            # 7. SVR (Phase 2) - NEW
            try:
                svr = SVR(kernel='rbf', C=1.0, gamma='scale')
                svr.fit(X, y)
                coefs = np.abs(svr.coef_[0]) if hasattr(svr, 'coef_') else np.ones(len(X.columns))
                for col, coef in zip(X.columns, coefs):
                    if coef > 0:
                        rows_by_model['svr'].append((col, target, float(coef)))
            except:
                # SVR might fail on some data, skip
                pass
        
        except Exception as e:
            print(f"  Error for target {target}: {e}")
    
    # Convert to DataFrames
    dfs = {}
    for model_name, rows in rows_by_model.items():
        if rows:
            dfs[model_name] = pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
            dfs[model_name]['Score'] = dfs[model_name]['Score'] / dfs[model_name]['Score'].sum()
        else:
            dfs[model_name] = pd.DataFrame(columns=['Cause', 'Effect', 'Score'])
    
    return dfs

def combine_phase2_ensemble(dfs_dict, weights=None):
    """Combine 7 models with optimized weights"""
    
    if weights is None:
        weights = {
            'extratrees': 0.25,
            'gradient': 0.20,
            'ridge': 0.15,
            'lasso': 0.10,
            'xgboost': 0.15,
            'randomforest': 0.10,
            'svr': 0.05
        }
    
    combined_scores = {}
    
    for model_name, df in dfs_dict.items():
        weight = weights.get(model_name, 1.0/len(dfs_dict))
        
        for _, row in df.iterrows():
            pair = (row['Cause'], row['Effect'])
            if pair not in combined_scores:
                combined_scores[pair] = 0.0
            combined_scores[pair] += row['Score'] * weight
    
    result = pd.DataFrame([
        {'Cause': c, 'Effect': e, 'Score': s}
        for (c, e), s in combined_scores.items()
    ])
    
    if len(result) > 0:
        result['Score'] = result['Score'] / result['Score'].sum()
    
    return result

def generate_phase2_predictions(k_value=300, ensemble_name="phase2", verbose=True):
    """Generate Phase 2 ensemble predictions"""
    
    if verbose:
        print(f"\n--- Top-{k_value} ({ensemble_name}) ---")
    
    test_files = [f'test_data/data{i}.csv' for i in range(1, 6)]
    all_predictions = []
    
    for g in range(1, 6):
        test_file = test_files[g-1]
        
        try:
            df = pd.read_csv(test_file)
            df_proc = preprocess(df)
            
            # Train Phase 2 ensemble (7 models)
            dfs_models = train_phase2_ensemble(df_proc)
            
            # Combine with optimized weights
            preds = combine_phase2_ensemble(dfs_models)
            preds = preds.sort_values('Score', ascending=False).head(k_value)
            
            out_csv = f'predictions_network{g}.csv'
            preds.to_csv(out_csv, index=False)
            all_predictions.append(len(preds))
            
            if verbose:
                print(f"  Network {g}: {len(preds)} predictions")
        
        except Exception as e:
            print(f"  Network {g}: ERROR - {e}")
            all_predictions.append(0)
    
    # Create ZIP
    zip_path = f'prediction_ensemble_phase2_{ensemble_name}_top{k_value}.zip'
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
print("PHASE 2 ENSEMBLE: 7 Modèles Combinés")
print("="*70)

print("""
MODÈLES PHASE 1:
  1. ExtraTreesRegressor (400 trees, max_features='log2')  - Weight: 0.25
  2. GradientBoostingRegressor (200 est., depth=5)         - Weight: 0.20
  3. Ridge Regression (alpha=1.0)                          - Weight: 0.15
  4. Lasso Regression (alpha=0.01)                         - Weight: 0.10

MODÈLES PHASE 2 (NOUVEAU):
  5. XGBoost (200 est., depth=5)                           - Weight: 0.15
  6. RandomForestRegressor (200 trees)                     - Weight: 0.10
  7. SVR (kernel='rbf')                                    - Weight: 0.05

STRATÉGIE: Vote pondéré avec 7 modèles diversifiés
OBJECTIF: 0.32 -> 0.40-0.50 (ou plus!)
""")

# Generate Phase 2 ensemble
phase2_configs = [
    {'k': 300, 'name': 'p2_balanced'},
    {'k': 320, 'name': 'p2_xgb_boost'},
    {'k': 350, 'name': 'p2_aggressive'},
]

generated_files = []
for config in phase2_configs:
    try:
        zip_file = generate_phase2_predictions(
            k_value=config['k'],
            ensemble_name=config['name'],
            verbose=True
        )
        generated_files.append((config['name'], zip_file))
    except Exception as e:
        print(f"✗ Error generating {config['name']}: {e}")

print("\n" + "="*70)
print("SUMMARY - PHASE 2")
print("="*70)
print(f"\n✓ Generated {len(generated_files)} Phase 2 ZIP files:\n")

for name, filepath in generated_files:
    from pathlib import Path
    file_size = Path(filepath).stat().st_size
    print(f"  • prediction_ensemble_phase2_{name}_top*.zip ({file_size} bytes)")

print("\n" + "="*70)
print("SUBMISSION PRIORITY - PHASE 2")
print("="*70)
print("""
TIER 1 (Start here):
  1. prediction_ensemble_phase2_p2_balanced_top300.zip
  2. prediction_ensemble_phase2_p2_xgb_boost_top320.zip
  3. prediction_ensemble_phase2_p2_aggressive_top350.zip

EXPECTED: 
  • Phase 1: 0.32 (Ensemble 4 modèles)
  • Phase 2: 0.40-0.50+ (Ensemble 7 modèles with XGBoost/RF/SVR)
  
  If ≥ 0.40: Excellent! Continue to Phase 3 (Stacking)
  If 0.35-0.40: Good! Try weight tuning or add more models
  If < 0.35: Try increasing K or adjusting model parameters

NEXT PHASE (if needed):
  - Phase 3: Stacking with meta-learner
  - Phase 4: Feature engineering with data_train/
  - Target: 0.50+ eventually reaching 0.60

Budget: ~43 submissions remaining (plenty!)
""")

print("\n✓ All Phase 2 ensemble files ready for submission!")
print("\nRECOMMENDATION: Soumettez les 3 fichiers Phase 2 maintenant!")
