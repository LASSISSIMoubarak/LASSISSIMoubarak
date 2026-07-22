#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 10: Fine-tune Ridge & Lasso Alphas
==========================================

Current best: 0.33 (Ridge:5.0, Lasso:0.005)

Strategy: Grid search Ridge/Lasso alphas
- Keep: ExtraTrees (sqrt), GradientBoosting (subsample=0.8), K=320
- Vary: Ridge alpha, Lasso alpha
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

def train_ensemble_with_alphas(df, ridge_alpha, lasso_alpha):
    """Train ensemble with given Ridge and Lasso alphas"""
    scores_dict = {}
    
    # ExtraTrees with sqrt (don't change)
    et_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = ExtraTreesRegressor(
            n_estimators=400,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1
        )
        model.fit(X, y)
        et_scores[target] = model.feature_importances_
    scores_dict['et'] = et_scores
    
    # GradientBoosting with subsample (don't change)
    gb_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            subsample=0.8,
            random_state=42
        )
        model.fit(X, y)
        gb_scores[target] = model.feature_importances_
    scores_dict['gb'] = gb_scores
    
    # Ridge with tuned alpha
    ridge_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = Ridge(alpha=ridge_alpha)
        model.fit(X, y)
        ridge_scores[target] = np.abs(model.coef_)
    scores_dict['ridge'] = ridge_scores
    
    # Lasso with tuned alpha
    lasso_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = Lasso(alpha=lasso_alpha, max_iter=10000)
        model.fit(X, y)
        lasso_scores[target] = np.abs(model.coef_)
    scores_dict['lasso'] = lasso_scores
    
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

def test_combination(ridge_alpha, lasso_alpha, k_cutoff=320):
    """Test one alpha combination"""
    print(f"\n  Testing Ridge:{ridge_alpha}, Lasso:{lasso_alpha}...", end=" ", flush=True)
    
    all_predictions = {}
    
    for network_id in range(1, 6):
        data_path = f"test_data/data{network_id}.csv"
        df = pd.read_csv(data_path, index_col=0)
        df_clean = preprocess(df)
        
        scores = train_ensemble_with_alphas(df_clean, ridge_alpha, lasso_alpha)
        
        weights = {'et': 0.4, 'gb': 0.3, 'ridge': 0.2, 'lasso': 0.1}
        df_preds = combine_predictions(scores, df.columns.tolist(), weights)
        all_predictions[network_id] = df_preds
    
    # Generate ZIP
    zip_name = f"prediction_phase10_ridge{ridge_alpha}_lasso{lasso_alpha}_top{k_cutoff}.zip"
    
    with ZipFile(zip_name, 'w') as zf:
        for network_id in range(1, 6):
            df_preds = all_predictions[network_id]
            df_top_k = df_preds.head(k_cutoff)[['Cause', 'Effect', 'Score']]
            
            csv_name = f"predictions_network{network_id}.csv"
            df_top_k.to_csv(csv_name, index=False)
            zf.write(csv_name)
            os.remove(csv_name)
    
    print(f"✓ {zip_name}")
    return zip_name

def main():
    print("\n" + "="*70)
    print("PHASE 10: Fine-tune Ridge & Lasso Alphas")
    print("="*70)
    print("""
FIXED (from best 0.33):
- ExtraTrees: n_estimators=400, max_features='sqrt'
- GradientBoosting: subsample=0.8, learning_rate=0.1, max_depth=5
- K-cutoff: 320
- Weights: ET:0.4, GB:0.3, Ridge:0.2, Lasso:0.1

VARYING:
- Ridge alpha: [4.0, 5.0 (current), 6.0]
- Lasso alpha: [0.004, 0.005 (current), 0.006]

Expected submissions: 9 (3x3 grid around current best)
""")
    
    # Optimized: test around current best (5.0 / 0.005)
    ridge_alphas = [4.0, 5.0, 6.0]
    lasso_alphas = [0.004, 0.005, 0.006]
    
    results_log = []
    
    print("\nGenerating predictions...")
    print("-" * 70)
    
    for ridge_alpha in ridge_alphas:
        for lasso_alpha in lasso_alphas:
            zip_file = test_combination(ridge_alpha, lasso_alpha, k_cutoff=320)
            results_log.append({
                'Ridge_Alpha': ridge_alpha,
                'Lasso_Alpha': lasso_alpha,
                'Zip_File': zip_file,
                'K': 320
            })
    
    # Save results log
    df_results = pd.DataFrame(results_log)
    df_results.to_csv('PHASE10_SUBMISSIONS.csv', index=False)
    
    print("\n" + "="*70)
    print(f"✓ Generated {len(results_log)} submissions")
    print(f"✓ Results logged in: PHASE10_SUBMISSIONS.csv")
    print("="*70)
    print("\nSubmissions summary:")
    print(df_results.to_string(index=False))
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("  1. Submit each ZIP to Codalab")
    print("  2. Record scores in ARCHIVE_MODELS.md")
    print("  3. Identify best combination")
    print("="*70)

if __name__ == '__main__':
    main()
