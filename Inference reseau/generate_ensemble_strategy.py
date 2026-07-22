#!/usr/bin/env python3
"""
ENSEMBLE STRATEGY: Combiner 4 modèles pour atteindre 0.6

Modèles:
  1. ExtraTreesRegressor (ce qui fonctionne - 0.25)
  2. GradientBoostingRegressor (généralement très bon)
  3. Ridge Regression (stabilité)
  4. Lasso Regression (sélection features)

Stratégie: Vote pondéré avec poids adaptés aux performances attendues
Poids: ExtraTrees=0.4, GB=0.3, Ridge=0.2, Lasso=0.1
"""

import pandas as pd
import numpy as np
import os
import zipfile
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
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

def train_ensemble_models(df):
    """Entraîner 4 modèles sur toutes les paires (Cause, Effect)"""
    
    rows_by_model = {
        'extratrees': [],
        'gradient': [],
        'ridge': [],
        'lasso': []
    }
    
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        
        try:
            # 1. ExtraTreesRegressor (ce qui fonctionne)
            et = ExtraTreesRegressor(
                n_estimators=400,
                max_features='log2',
                random_state=42,
                n_jobs=-1
            )
            et.fit(X, y)
            for col, imp in zip(X.columns, et.feature_importances_):
                if imp > 0:
                    rows_by_model['extratrees'].append((col, target, float(imp)))
            
            # 2. GradientBoostingRegressor
            gb = GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
            gb.fit(X, y)
            for col, imp in zip(X.columns, gb.feature_importances_):
                if imp > 0:
                    rows_by_model['gradient'].append((col, target, float(imp)))
            
            # 3. Ridge
            ridge = Ridge(alpha=1.0)
            ridge.fit(X, y)
            coefs = np.abs(ridge.coef_)
            for col, coef in zip(X.columns, coefs):
                if coef > 0:
                    rows_by_model['ridge'].append((col, target, float(coef)))
            
            # 4. Lasso
            lasso = Lasso(alpha=0.01, max_iter=10000)
            lasso.fit(X, y)
            coefs = np.abs(lasso.coef_)
            for col, coef in zip(X.columns, coefs):
                if coef > 0:
                    rows_by_model['lasso'].append((col, target, float(coef)))
        
        except Exception as e:
            print(f"  Error for target {target}: {e}")
    
    # Convertir en DataFrames
    dfs = {}
    for model_name, rows in rows_by_model.items():
        if rows:
            dfs[model_name] = pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
            # Normaliser scores
            dfs[model_name]['Score'] = dfs[model_name]['Score'] / dfs[model_name]['Score'].sum()
        else:
            dfs[model_name] = pd.DataFrame(columns=['Cause', 'Effect', 'Score'])
    
    return dfs

def combine_ensemble_predictions(dfs_dict, weights=None):
    """
    Combiner les prédictions de tous les modèles avec vote pondéré
    
    weights: dict avec poids pour chaque modèle
    """
    
    if weights is None:
        weights = {
            'extratrees': 0.4,
            'gradient': 0.3,
            'ridge': 0.2,
            'lasso': 0.1
        }
    
    # Combiner toutes les paires (Cause, Effect)
    combined_scores = {}
    
    for model_name, df in dfs_dict.items():
        weight = weights.get(model_name, 0.25)
        
        for _, row in df.iterrows():
            pair = (row['Cause'], row['Effect'])
            if pair not in combined_scores:
                combined_scores[pair] = 0.0
            combined_scores[pair] += row['Score'] * weight
    
    # Convertir en DataFrame
    result = pd.DataFrame([
        {'Cause': c, 'Effect': e, 'Score': s}
        for (c, e), s in combined_scores.items()
    ])
    
    # Renormaliser
    if len(result) > 0:
        result['Score'] = result['Score'] / result['Score'].sum()
    
    return result

def generate_ensemble_predictions(k_value=300, ensemble_name="ensemble", verbose=True):
    """Générer prédictions ensemble pour un K donné"""
    
    if verbose:
        print(f"\n--- Top-{k_value} ({ensemble_name}) ---")
    
    test_files = [f'test_data/data{i}.csv' for i in range(1, 6)]
    all_predictions = []
    
    for g in range(1, 6):
        test_file = test_files[g-1]
        
        try:
            df = pd.read_csv(test_file)
            df_proc = preprocess(df)
            
            # Entraîner ensemble de 4 modèles
            dfs_models = train_ensemble_models(df_proc)
            
            # Combiner avec vote pondéré
            preds = combine_ensemble_predictions(dfs_models)
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
    zip_path = f'prediction_ensemble_{ensemble_name}_top{k_value}.zip'
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
print("ENSEMBLE STRATEGY: 4 Modèles Combinés")
print("="*70)

print("""
MODÈLES:
  1. ExtraTreesRegressor (400 trees, max_features='log2')  - Weight: 0.4
  2. GradientBoostingRegressor (200 est., depth=5)         - Weight: 0.3
  3. Ridge Regression (alpha=1.0)                          - Weight: 0.2
  4. Lasso Regression (alpha=0.01)                         - Weight: 0.1

STRATÉGIE: Vote pondéré (poids adapté à performance attendue)
K: 300 predictions par network
Espoir: 0.30-0.35 (ou plus si ensemble bien calibré!)
""")

# Générer plusieurs variantes ensemble
ensemble_configs = [
    {'k': 300, 'name': 'v1_balanced'},
    {'k': 320, 'name': 'v2_extratrees_boost'},
    {'k': 350, 'name': 'v3_aggressive'},
]

generated_files = []
for config in ensemble_configs:
    try:
        zip_file = generate_ensemble_predictions(
            k_value=config['k'],
            ensemble_name=config['name'],
            verbose=True
        )
        generated_files.append((config['name'], zip_file))
    except Exception as e:
        print(f"✗ Error generating {config['name']}: {e}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"\n✓ Generated {len(generated_files)} ensemble ZIP files:\n")

for name, filepath in generated_files:
    from pathlib import Path
    file_size = Path(filepath).stat().st_size
    print(f"  • prediction_ensemble_{name}_top*.zip ({file_size} bytes)")

print("\n" + "="*70)
print("SUBMISSION PRIORITY")
print("="*70)
print("""
TIER 1 (Start here):
  1. prediction_ensemble_v1_balanced_top300.zip
  2. prediction_ensemble_v2_extratrees_boost_top320.zip
  3. prediction_ensemble_v3_aggressive_top350.zip

EXPECTED: 
  • Should improve from 0.25 to 0.30-0.40 range
  • If ≥ 0.30: Excellent! Continue with more models or weights tuning
  • If 0.25-0.30: Good! Try weight adjustment or add 5th model

NEXT PHASE (if needed):
  - Add XGBoost
  - Tune weights more carefully
  - Try stacking or blending
  - Combine with domain-specific features

Budget: ~50 submissions remaining
""")

print("\n✓ All ensemble files ready for submission!")
