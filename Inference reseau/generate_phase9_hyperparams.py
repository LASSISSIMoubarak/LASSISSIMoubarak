#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 9: Ajuster les Hyperparamètres
====================================
Phase 1 = 0.32 stable
Phase 2 = 0.31-0.32 (pas d'amélioration)

Phase 9: Optimiser les hyperparamètres de Phase 1

Stratégies:
1. ExtraTrees: augmenter trees, essayer sqrt
2. GradientBoosting: réduire learning_rate, subsample
3. Ridge: augmenter alpha
4. Lasso: réduire alpha
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

def preprocess(df):
    """Impute median + StandardScaler"""
    imputer = SimpleImputer(strategy='median')
    df_imputed = pd.DataFrame(imputer.fit_transform(df), columns=df.columns)
    
    scaler = StandardScaler()
    df_scaled = pd.DataFrame(scaler.fit_transform(df_imputed), columns=df.columns)
    
    return df_scaled

def train_ensemble_v1(df):
    """VARIANT 1: Augment ExtraTrees, reduce LR"""
    print(f"  Training V1 (ET:600, GB:LR0.05)...", end='', flush=True)
    
    scores_dict = {}
    
    # ExtraTrees with more trees
    et_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = ExtraTreesRegressor(n_estimators=600, max_features='log2', random_state=42, n_jobs=-1)
        model.fit(X, y)
        et_scores[target] = model.feature_importances_
    scores_dict['et'] = et_scores
    
    # GradientBoosting with lower learning rate
    gb_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, max_depth=5, random_state=42)
        model.fit(X, y)
        gb_scores[target] = model.feature_importances_
    scores_dict['gb'] = gb_scores
    
    # Ridge with higher alpha
    ridge_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = Ridge(alpha=2.0)
        model.fit(X, y)
        ridge_scores[target] = np.abs(model.coef_)
    scores_dict['ridge'] = ridge_scores
    
    # Lasso with lower alpha
    lasso_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = Lasso(alpha=0.005, max_iter=10000)
        model.fit(X, y)
        lasso_scores[target] = np.abs(model.coef_)
    scores_dict['lasso'] = lasso_scores
    
    print(" ✓")
    return scores_dict

def train_ensemble_v2(df):
    """VARIANT 2: ET with sqrt, GB with subsample"""
    print(f"  Training V2 (ET:sqrt, GB:subsample)...", end='', flush=True)
    
    scores_dict = {}
    
    # ExtraTrees with sqrt
    et_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = ExtraTreesRegressor(n_estimators=400, max_features='sqrt', random_state=42, n_jobs=-1)
        model.fit(X, y)
        et_scores[target] = model.feature_importances_
    scores_dict['et'] = et_scores
    
    # GradientBoosting with subsample
    gb_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, max_depth=5, subsample=0.8, random_state=42)
        model.fit(X, y)
        gb_scores[target] = model.feature_importances_
    scores_dict['gb'] = gb_scores
    
    # Ridge with higher alpha
    ridge_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = Ridge(alpha=5.0)
        model.fit(X, y)
        ridge_scores[target] = np.abs(model.coef_)
    scores_dict['ridge'] = ridge_scores
    
    # Lasso with reduced alpha
    lasso_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = Lasso(alpha=0.005, max_iter=10000)
        model.fit(X, y)
        lasso_scores[target] = np.abs(model.coef_)
    scores_dict['lasso'] = lasso_scores
    
    print(" ✓")
    return scores_dict

def combine_predictions(scores_dict, targets, weights):
    """Weighted combination"""
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
        combined = weights['et'] * et_norm + weights['gb'] * gb_norm + weights['ridge'] * ridge_norm + weights['lasso'] * lasso_norm
        
        X_cols = [t for t in targets if t != target]
        for cause_idx, cause in enumerate(X_cols):
            results.append({'Cause': cause, 'Effect': target, 'Score': combined[cause_idx]})
    
    return pd.DataFrame(results).sort_values('Score', ascending=False).reset_index(drop=True)

def main():
    print("\n" + "="*70)
    print("PHASE 9: Hyperparameter Tuning")
    print("="*70)
    
    variants = [
        {
            'name': 'v1_etmore_lrlow',
            'train_fn': train_ensemble_v1,
            'weights': {'et': 0.4, 'gb': 0.3, 'ridge': 0.2, 'lasso': 0.1},
            'description': 'ET:600, GB:LR0.05, Ridge:2.0, Lasso:0.005'
        },
        {
            'name': 'v2_etsqrt_subsample',
            'train_fn': train_ensemble_v2,
            'weights': {'et': 0.4, 'gb': 0.3, 'ridge': 0.2, 'lasso': 0.1},
            'description': 'ET:sqrt, GB:subsample0.8, Ridge:5.0, Lasso:0.005'
        }
    ]
    
    for variant in variants:
        print(f"\n[{variant['name']}]")
        print(f"  Config: {variant['description']}")
        
        all_predictions = {}
        
        for network_id in range(1, 6):
            data_path = f"test_data/data{network_id}.csv"
            df = pd.read_csv(data_path, index_col=0)
            df_clean = preprocess(df)
            
            scores = variant['train_fn'](df_clean)
            df_preds = combine_predictions(scores, df.columns.tolist(), variant['weights'])
            
            print(f"  Network {network_id}: {len(df_preds)} edges")
            all_predictions[network_id] = df_preds
        
        # Generate 3 K-cutoffs
        for k_cutoff in [300, 320, 350]:
            zip_name = f"prediction_phase9_{variant['name']}_top{k_cutoff}.zip"
            
            with ZipFile(zip_name, 'w') as zf:
                for network_id in range(1, 6):
                    df_preds = all_predictions[network_id]
                    df_top_k = df_preds.head(k_cutoff)[['Cause', 'Effect', 'Score']]
                    
                    csv_name = f"predictions_network{network_id}.csv"
                    df_top_k.to_csv(csv_name, index=False)
                    zf.write(csv_name)
                    os.remove(csv_name)
            
            file_size_kb = os.path.getsize(zip_name) / 1024
            print(f"  Created: {zip_name} ({file_size_kb:.1f} KB)")
    
    print("\n" + "="*70)
    print("✓ Phase 9 complete! 6 submission files ready.")
    print("="*70)

if __name__ == '__main__':
    main()
