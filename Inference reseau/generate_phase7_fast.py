#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 7 FAST: ExtraTrees Only on TEST_DATA
==========================================
Ultra-fast version using only ExtraTrees (weight 0.4 dominant).
This is the critical model for this problem.
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor
from zipfile import ZipFile

def preprocess(df):
    """Impute median + StandardScaler"""
    imputer = SimpleImputer(strategy='median')
    df_imputed = pd.DataFrame(imputer.fit_transform(df), columns=df.columns)
    
    scaler = StandardScaler()
    df_scaled = pd.DataFrame(scaler.fit_transform(df_imputed), columns=df.columns)
    
    return df_scaled

def train_extratrees(df):
    """Train ExtraTrees and extract feature importances for all targets"""
    print(f"  Training on {df.shape[0]} rows × {df.shape[1]} columns")
    
    scores_dict = {}
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
        scores_dict[target] = model.feature_importances_
    
    return scores_dict

def generate_predictions(scores_dict, targets):
    """Generate edge predictions from feature importances"""
    results = []
    
    for target in targets:
        imp = scores_dict[target]
        imp_norm = imp / (imp.max() + 1e-10)
        
        X_cols_idx = [i for i in range(len(targets)) if targets[i] != target]
        X_cols = [targets[i] for i in X_cols_idx]
        
        for cause_idx, cause in enumerate(X_cols):
            results.append({
                'Cause': cause,
                'Effect': target,
                'Score': imp_norm[cause_idx]
            })
    
    df_results = pd.DataFrame(results)
    return df_results.sort_values('Score', ascending=False).reset_index(drop=True)

def main():
    print("\n" + "="*70)
    print("PHASE 7 FAST: ExtraTrees on test_data/ (Ultra-Fast)")
    print("="*70)
    
    all_predictions = {}
    
    for network_id in range(1, 6):
        print(f"\n[Network {network_id}]")
        
        data_path = f"test_data/data{network_id}.csv"
        print(f"  Loading {data_path}...")
        df = pd.read_csv(data_path, index_col=0)
        print(f"  Shape: {df.shape}")
        
        print(f"  Preprocessing...")
        df_clean = preprocess(df)
        
        print(f"  Training ExtraTrees...")
        scores = train_extratrees(df_clean)
        
        print(f"  Generating predictions...")
        df_preds = generate_predictions(scores, df.columns.tolist())
        
        print(f"  Generated {len(df_preds)} edges")
        print(f"  Top 5 scores: {df_preds['Score'].head().values}")
        
        all_predictions[network_id] = df_preds
    
    print(f"\n" + "-"*70)
    print("Creating submissions...")
    print("-"*70)
    
    variants = [
        ('top300', 300),
        ('top320', 320),
        ('top350', 350)
    ]
    
    for variant_name, k_cutoff in variants:
        print(f"\nVariant: {variant_name} (K={k_cutoff})")
        
        zip_name = f"prediction_phase7_fast_{variant_name}.zip"
        
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
    print("✓ Phase 7 Fast complete! Ready to submit.")
    print("="*70)

if __name__ == '__main__':
    main()
