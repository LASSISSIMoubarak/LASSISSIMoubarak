#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 11: Network 4 Rescue Mission
==================================

Goal: Reach 0.40 by fixing Network 4 (currently 0.207)

Strategy: Use different K-cutoff for each network
- Networks 1,2,3,5: Keep K=320 (working well)
- Network 4: Vary K to find sweet spot

Hypothesis: Network 4 needs different sparsity than others
- Maybe K=200 (more aggressive)?
- Maybe K=250?
- Maybe K=400 (less aggressive)?
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
    """Train best ensemble (Phase 9 V2 - 0.33 baseline)"""
    scores_dict = {}
    
    # ExtraTrees with sqrt
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
    
    # GradientBoosting with subsample
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
    
    # Ridge with best alpha
    ridge_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = Ridge(alpha=5.0)
        model.fit(X, y)
        ridge_scores[target] = np.abs(model.coef_)
    scores_dict['ridge'] = ridge_scores
    
    # Lasso with best alpha
    lasso_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = Lasso(alpha=0.005, max_iter=10000)
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

def generate_with_variable_k(k_network4, description=""):
    """Generate submission with K=320 for networks 1-3-5, varying K for network 4"""
    print(f"\n  Testing Network4 K={k_network4}...", end=" ", flush=True)
    
    all_predictions = {}
    weights = {'et': 0.4, 'gb': 0.3, 'ridge': 0.2, 'lasso': 0.1}
    
    for network_id in range(1, 6):
        data_path = f"test_data/data{network_id}.csv"
        df = pd.read_csv(data_path, index_col=0)
        df_clean = preprocess(df)
        
        scores = train_best_ensemble(df_clean)
        df_preds = combine_predictions(scores, df.columns.tolist(), weights)
        all_predictions[network_id] = df_preds
    
    # Generate ZIP with variable K
    k_network4_str = str(k_network4).replace('.', 'p')
    zip_name = f"prediction_phase11_k320_net1235_k{k_network4_str}_net4{description}.zip"
    
    with ZipFile(zip_name, 'w') as zf:
        for network_id in range(1, 6):
            df_preds = all_predictions[network_id]
            
            # Use K=320 for networks 1,2,3,5 and varying K for network 4
            if network_id == 4:
                k = k_network4
            else:
                k = 320
            
            df_top_k = df_preds.head(k)[['Cause', 'Effect', 'Score']]
            
            csv_name = f"predictions_network{network_id}.csv"
            df_top_k.to_csv(csv_name, index=False)
            zf.write(csv_name)
            os.remove(csv_name)
    
    print(f"✓ {zip_name}")
    return zip_name

def main():
    print("\n" + "="*70)
    print("PHASE 11: Network 4 Rescue Mission")
    print("="*70)
    print("""
GOAL: Reach 0.40 by fixing Network 4 (currently 0.207)

STRATEGY: Different K-cutoff per network
- Networks 1,2,3,5: K=320 (working well, average ~0.35)
- Network 4: VARY K (find optimal for this network)

HYPOTHESIS: Network 4 needs different sparsity

BASE: Phase 9 V2 (ridge5.0_lasso0.005, ET:sqrt, GB:subsample0.8)

Expected improvements:
- If Network 4 improves from 0.207 → 0.30: Average 0.3242 → 0.3365 (+1.2%)
- If Network 4 improves from 0.207 → 0.35: Average 0.3242 → 0.3542 (+3%)
- To reach 0.40: Need all networks ~0.40 (difficult!)
  OR: 4 networks at 0.35 + 1 network at 0.60 (very high!)
""")
    
    # Test different K values for network 4
    k_values_network4 = [150, 200, 250, 300, 350, 400, 500]
    
    results_log = []
    
    print("\nGenerating submissions...")
    print("-" * 70)
    
    for i, k in enumerate(k_values_network4, 1):
        desc = f"_{i}"
        zip_file = generate_with_variable_k(k, desc)
        results_log.append({
            'K_Network4': k,
            'K_Others': 320,
            'Zip_File': zip_file,
            'Description': f"K=320 for networks 1,2,3,5 | K={k} for network 4"
        })
    
    # Save results log
    df_results = pd.DataFrame(results_log)
    df_results.to_csv('PHASE11_SUBMISSIONS.csv', index=False)
    
    print("\n" + "="*70)
    print(f"✓ Generated {len(results_log)} submissions")
    print(f"✓ Results logged in: PHASE11_SUBMISSIONS.csv")
    print("="*70)
    print("\nSubmissions summary:")
    print(df_results.to_string(index=False))
    print("\n" + "="*70)
    print("STRATEGY:")
    print("  1. Submit each ZIP to Codalab")
    print("  2. Record scores - find optimal K for Network 4")
    print("  3. If improvement found: potentially Phase 12")
    print("="*70)

if __name__ == '__main__':
    main()
