#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 7: Correct Training Source
================================
Train ensemble on TEST_DATA (100 dims) - NOT data_train (20 dims)
This is the working methodology that achieved 0.32.

Models: ExtraTrees, GradientBoosting, Ridge, Lasso
Weights: (0.4, 0.3, 0.2, 0.1)
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
from zipfile import ZipFile
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# PREPROCESSING
# ============================================================================

def preprocess(df):
    """Impute median + StandardScaler"""
    imputer = SimpleImputer(strategy='median')
    df_imputed = pd.DataFrame(imputer.fit_transform(df), columns=df.columns)
    
    scaler = StandardScaler()
    df_scaled = pd.DataFrame(scaler.fit_transform(df_imputed), columns=df.columns)
    
    return df_scaled

# ============================================================================
# TRAINING
# ============================================================================

def train_ensemble_models(df):
    """
    Train 4 models on df (each model predicts each column from others).
    Returns dict: {model_name: {target_col: feature_importances}}
    """
    print(f"  Training on {df.shape[0]} rows × {df.shape[1]} columns")
    
    scores_dict = {}
    
    # 1. ExtraTrees
    print("  - ExtraTrees...", end='', flush=True)
    et_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = ExtraTreesRegressor(
            n_estimators=400,
            max_features='log2',
            random_state=42,
            n_jobs=-1
        )
        model.fit(X, y)
        et_scores[target] = model.feature_importances_
    scores_dict['extratrees'] = et_scores
    print(" ✓")
    
    # 2. GradientBoosting (optimized for speed)
    print("  - GradientBoosting...", end='', flush=True)
    gb_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=3,
            subsample=0.8,
            random_state=42
        )
        model.fit(X, y)
        gb_scores[target] = model.feature_importances_
    scores_dict['gradient'] = gb_scores
    print(" ✓")
    
    # 3. Ridge
    print("  - Ridge...", end='', flush=True)
    ridge_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = Ridge(alpha=1.0)
        model.fit(X, y)
        ridge_scores[target] = np.abs(model.coef_)
    scores_dict['ridge'] = ridge_scores
    print(" ✓")
    
    # 4. Lasso
    print("  - Lasso...", end='', flush=True)
    lasso_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = Lasso(alpha=0.01, max_iter=10000)
        model.fit(X, y)
        lasso_scores[target] = np.abs(model.coef_)
    scores_dict['lasso'] = lasso_scores
    print(" ✓")
    
    return scores_dict

# ============================================================================
# COMBINATION & PREDICTION
# ============================================================================

def combine_ensemble_predictions(dfs_dict, weights):
    """
    Combine predictions from 4 models via weighted vote.
    
    Args:
        dfs_dict: {model_name: {target_col: feature_importances}}
        weights: {'extratrees': 0.4, 'gradient': 0.3, 'ridge': 0.2, 'lasso': 0.1}
    
    Returns:
        DataFrame with columns [Cause, Effect, Score]
    """
    
    results = []
    
    # Get all possible edges (all models have same targets)
    targets = list(dfs_dict['extratrees'].keys())
    
    for target in targets:
        # Collect feature importances from all 4 models
        et_imp = dfs_dict['extratrees'][target]
        gb_imp = dfs_dict['gradient'][target]
        ridge_imp = dfs_dict['ridge'][target]
        lasso_imp = dfs_dict['lasso'][target]
        
        # Normalize each model's importances to [0, 1]
        et_imp_norm = et_imp / (et_imp.max() + 1e-10)
        gb_imp_norm = gb_imp / (gb_imp.max() + 1e-10)
        ridge_imp_norm = ridge_imp / (ridge_imp.max() + 1e-10)
        lasso_imp_norm = lasso_imp / (lasso_imp.max() + 1e-10)
        
        # Weighted combination
        combined = (
            weights['extratrees'] * et_imp_norm +
            weights['gradient'] * gb_imp_norm +
            weights['ridge'] * ridge_imp_norm +
            weights['lasso'] * lasso_imp_norm
        )
        
        # Create edges (cause → effect)
        # Get column indices of X (all except target)
        X_cols_idx = [i for i in range(len(targets)) if targets[i] != target]
        X_cols = [targets[i] for i in X_cols_idx]
        
        for cause_idx, cause in enumerate(X_cols):
            results.append({
                'Cause': cause,
                'Effect': target,
                'Score': combined[cause_idx]
            })
    
    df_results = pd.DataFrame(results)
    return df_results

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*70)
    print("PHASE 7: Correct Training Source (test_data/)")
    print("="*70)
    
    # Load and process test_data for 5 networks
    all_predictions = {}
    
    for network_id in range(1, 6):
        print(f"\n[Network {network_id}]")
        
        # Load TEST DATA (100 dimensions)
        data_path = f"test_data/data{network_id}.csv"
        print(f"  Loading {data_path}...")
        df = pd.read_csv(data_path, index_col=0)
        print(f"  Shape: {df.shape}")
        
        # Preprocess
        print(f"  Preprocessing...")
        df_clean = preprocess(df)
        
        # Train ensemble
        print(f"  Training ensemble...")
        scores_dict = train_ensemble_models(df_clean)
        
        # Combine predictions
        print(f"  Combining predictions...")
        weights = {'extratrees': 0.4, 'gradient': 0.3, 'ridge': 0.2, 'lasso': 0.1}
        df_preds = combine_ensemble_predictions(scores_dict, weights)
        
        # Sort by score descending
        df_preds = df_preds.sort_values('Score', ascending=False).reset_index(drop=True)
        print(f"  Generated {len(df_preds)} edges")
        print(f"  Top 5 scores: {df_preds['Score'].head().values}")
        
        all_predictions[network_id] = df_preds
    
    # Generate 3 variants (different K cutoffs)
    variants = [
        ('top300', 300),
        ('top320', 320),
        ('top350', 350)
    ]
    
    print(f"\n" + "-"*70)
    print("Generating submissions...")
    print("-"*70)
    
    for variant_name, k_cutoff in variants:
        print(f"\nVariant: {variant_name} (K={k_cutoff})")
        
        zip_name = f"prediction_phase7_correct_source_{variant_name}.zip"
        
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
        print(f"  Created: {zip_name} ({file_size_kb:.1f} KB)")
    
    print("\n" + "="*70)
    print("✓ Phase 7 complete! Ready to submit.")
    print("="*70)

if __name__ == '__main__':
    main()
