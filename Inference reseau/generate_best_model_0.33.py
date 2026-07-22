#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEILLEUR MODELE - 0.33
======================

Score: 0.33
File: prediction_phase9_v2_etsqrt_subsamp_top320.zip
Date: 2026-07-13 09:35
K-cutoff: 320

Hyperparameters clés qui font la différence:
- ExtraTrees: max_features='sqrt' (NOT 'log2')
- GradientBoosting: subsample=0.8 (regularization)
- Ridge: alpha=5.0 (higher than baseline 1.0)
- Lasso: alpha=0.005 (lower than baseline 0.01)
- K=320 (sweet spot)
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
from zipfile import ZipFile

def preprocess(df):
    """Impute median + StandardScaler"""
    imputer = SimpleImputer(strategy='median')
    df_imputed = pd.DataFrame(imputer.fit_transform(df), columns=df.columns)
    
    scaler = StandardScaler()
    df_scaled = pd.DataFrame(scaler.fit_transform(df_imputed), columns=df.columns)
    
    return df_scaled

def train_best_ensemble(df):
    """Train best ensemble configuration (Phase 9 V2 = 0.33)"""
    scores_dict = {}
    
    # ExtraTrees with sqrt (KEY DIFFERENCE from baseline log2)
    et_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = ExtraTreesRegressor(
            n_estimators=400,
            max_features='sqrt',  # ← CHANGED from 'log2'
            random_state=42,
            n_jobs=-1
        )
        model.fit(X, y)
        et_scores[target] = model.feature_importances_
    scores_dict['et'] = et_scores
    
    # GradientBoosting with subsample (regularization)
    gb_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            subsample=0.8,  # ← ADDED subsample
            random_state=42
        )
        model.fit(X, y)
        gb_scores[target] = model.feature_importances_
    scores_dict['gb'] = gb_scores
    
    # Ridge with higher alpha
    ridge_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = Ridge(alpha=5.0)  # ← INCREASED from 1.0
        model.fit(X, y)
        ridge_scores[target] = np.abs(model.coef_)
    scores_dict['ridge'] = ridge_scores
    
    # Lasso with lower alpha
    lasso_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = Lasso(
            alpha=0.005,  # ← DECREASED from 0.01
            max_iter=10000
        )
        model.fit(X, y)
        lasso_scores[target] = np.abs(model.coef_)
    scores_dict['lasso'] = lasso_scores
    
    return scores_dict

def combine_predictions(scores_dict, targets, weights):
    """Weighted combination with Phase 1 weights"""
    results = []
    
    for target in targets:
        et_imp = scores_dict['et'][target]
        gb_imp = scores_dict['gb'][target]
        ridge_imp = scores_dict['ridge'][target]
        lasso_imp = scores_dict['lasso'][target]
        
        # Normalize
        et_norm = et_imp / (et_imp.max() + 1e-10)
        gb_norm = gb_imp / (gb_imp.max() + 1e-10)
        ridge_norm = ridge_imp / (ridge_imp.max() + 1e-10)
        lasso_norm = lasso_imp / (lasso_imp.max() + 1e-10)
        
        # Weighted vote
        combined = (
            weights['et'] * et_norm + 
            weights['gb'] * gb_norm + 
            weights['ridge'] * ridge_norm + 
            weights['lasso'] * lasso_norm
        )
        
        X_cols = [t for t in targets if t != target]
        for cause_idx, cause in enumerate(X_cols):
            results.append({
                'Cause': cause,
                'Effect': target,
                'Score': combined[cause_idx]
            })
    
    return pd.DataFrame(results).sort_values('Score', ascending=False).reset_index(drop=True)

def main():
    print("\n" + "="*70)
    print("BEST MODEL: Phase 9 V2 (0.33)")
    print("="*70)
    print("""
KEY IMPROVEMENTS:
- ExtraTrees: max_features='sqrt' (was 'log2')
- GradientBoosting: subsample=0.8 (was 1.0)
- Ridge: alpha=5.0 (was 1.0)
- Lasso: alpha=0.005 (was 0.01)
- K=320 (optimal K-cutoff)

Data: test_data/ (100 dimensions)
Weights: ET:0.4, GB:0.3, Ridge:0.2, Lasso:0.1
""")
    
    all_predictions = {}
    
    for network_id in range(1, 6):
        print(f"\n[Network {network_id}]")
        
        data_path = f"test_data/data{network_id}.csv"
        print(f"  Loading {data_path}...")
        df = pd.read_csv(data_path, index_col=0)
        print(f"  Shape: {df.shape}")
        
        print(f"  Preprocessing...")
        df_clean = preprocess(df)
        
        print(f"  Training best ensemble...")
        scores = train_best_ensemble(df_clean)
        
        print(f"  Combining predictions...")
        weights = {'et': 0.4, 'gb': 0.3, 'ridge': 0.2, 'lasso': 0.1}
        df_preds = combine_predictions(scores, df.columns.tolist(), weights)
        
        print(f"  Generated {len(df_preds)} edges")
        print(f"  Top 5 scores: {df_preds['Score'].head().values}")
        
        all_predictions[network_id] = df_preds
    
    # Generate final submission (K=320 - optimal)
    print(f"\n" + "-"*70)
    print("Creating final submission...")
    print("-"*70)
    
    k_cutoff = 320
    zip_name = f"prediction_best_model_0.33_top{k_cutoff}.zip"
    
    print(f"\nSubmission: {zip_name}")
    
    with ZipFile(zip_name, 'w') as zf:
        for network_id in range(1, 6):
            df_preds = all_predictions[network_id]
            df_top_k = df_preds.head(k_cutoff)[['Cause', 'Effect', 'Score']]
            
            csv_name = f"predictions_network{network_id}.csv"
            df_top_k.to_csv(csv_name, index=False)
            zf.write(csv_name)
            os.remove(csv_name)
            
            print(f"  network{network_id}: {len(df_top_k)} edges")
    
    file_size_kb = os.path.getsize(zip_name) / 1024
    print(f"\n✓ Created: {zip_name} ({file_size_kb:.1f} KB)")
    
    print("\n" + "="*70)
    print("✓ Best model ready! Expected score: 0.33+")
    print("="*70)

if __name__ == '__main__':
    main()
