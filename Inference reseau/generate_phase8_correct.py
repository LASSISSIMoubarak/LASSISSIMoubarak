#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 8 FAST: Correct Training Data (data_train/)
==================================================
Train ExtraTrees only on data_train/ (20 dims) - CORRECT training source.
Ultra-fast version using dominant model only.
This should return to ~0.32 baseline.
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
    """Train ExtraTrees on 20-dim data"""
    print(f"  Training on {df.shape[0]} rows × {df.shape[1]} columns")
    
    et_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = ExtraTreesRegressor(n_estimators=400, max_features='log2', random_state=42, n_jobs=-1)
        model.fit(X, y)
        et_scores[target] = model.feature_importances_
    
    return et_scores

def generate_predictions(scores_dict, targets):
    """Generate edge predictions from feature importances"""
    results = []
    
    for target in targets:
        imp = scores_dict[target]
        imp_norm = imp / (imp.max() + 1e-10)
        
        X_cols = [t for t in targets if t != target]
        for cause_idx, cause in enumerate(X_cols):
            results.append({'Cause': cause, 'Effect': target, 'Score': imp_norm[cause_idx]})
    
    return pd.DataFrame(results).sort_values('Score', ascending=False).reset_index(drop=True)

def main():
    print("\n" + "="*70)
    print("PHASE 8 FAST: Correct Training Data (data_train/ - 20 dims)")
    print("="*70)
    
    all_predictions = {}
    
    for network_id in range(1, 6):
        print(f"\n[Network {network_id}]")
        
        data_path = f"data_train/data{network_id}.csv"
        
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
    
    variants = [('top300', 300), ('top320', 320), ('top350', 350)]
    
    for variant_name, k_cutoff in variants:
        print(f"\nVariant: {variant_name} (K={k_cutoff})")
        
        zip_name = f"prediction_phase8_fast_{variant_name}.zip"
        
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
    print("✓ Phase 8 Fast complete! Ready for submission (~0.32).")
    print("="*70)

if __name__ == '__main__':
    main()
