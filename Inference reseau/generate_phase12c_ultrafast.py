#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 12C: ULTRA-FAST TEST
===========================

⚡ VERSION LA PLUS RAPIDE POSSIBLE
Teste UNIQUEMENT les 2 meilleurs configs attendues

Temps: ~15-20 min seulement

BUT: Vérifier rapidement si amélioration possible
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
    imputer = SimpleImputer(strategy='median')
    df_imputed = pd.DataFrame(imputer.fit_transform(df), columns=df.columns)
    scaler = StandardScaler()
    df_scaled = pd.DataFrame(scaler.fit_transform(df_imputed), columns=df.columns)
    return df_scaled

def main():
    print("\n" + "="*80)
    print("PHASE 12C: ULTRA-FAST TEST (15-20 min)")
    print("="*80)
    print("""
TESTS:
1. Config: ET=0.35, GB=0.35, Ridge=0.20, Lasso=0.10, K=320
   - Reduction legere ET (0.40 vs 0.35)
   - Boost GB (0.30 vs 0.35)
   - Esperance: +0.005-0.015 AUPR

2. Config: ET=0.30, GB=0.30, Ridge=0.25, Lasso=0.15, K=320
   - Poids equilibres (chaque modele ~25-30%)
   - Esperance: +0.000-0.015 AUPR
    """)
    
    configs = {
        'test1_reduced_et': {
            'et': 0.35, 'gb': 0.35, 'ridge': 0.20, 'lasso': 0.10, 'k': 320
        },
        'test2_balanced': {
            'et': 0.30, 'gb': 0.30, 'ridge': 0.25, 'lasso': 0.15, 'k': 320
        },
    }
    
    for config_name, params in configs.items():
        print(f"\n{'='*80}")
        print(f"Testing: {config_name}")
        print(f"Weights: ET={params['et']}, GB={params['gb']}, Ridge={params['ridge']}, Lasso={params['lasso']}")
        print(f"{'='*80}")
        
        all_preds = {}
        
        for network_id in range(1, 6):
            print(f"\n[Network {network_id}]", end=' ')
            data_path = f"test_data/data{network_id}.csv"
            df = pd.read_csv(data_path, index_col=0)
            df_clean = preprocess(df)
            
            results = []
            for target in df_clean.columns:
                X = df_clean.drop(columns=[target])
                y = df_clean[target].values
                
                # ET
                model_et = ExtraTreesRegressor(n_estimators=400, max_features='sqrt', random_state=42, n_jobs=-1)
                model_et.fit(X, y)
                imp_et = model_et.feature_importances_
                imp_et_norm = imp_et / (imp_et.max() + 1e-10)
                
                # GB
                model_gb = GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, max_depth=5, subsample=0.8, random_state=42)
                model_gb.fit(X, y)
                imp_gb = model_gb.feature_importances_
                imp_gb_norm = imp_gb / (imp_gb.max() + 1e-10)
                
                # Ridge
                model_ridge = Ridge(alpha=5.0)
                model_ridge.fit(X, y)
                imp_ridge = np.abs(model_ridge.coef_)
                imp_ridge_norm = imp_ridge / (imp_ridge.max() + 1e-10)
                
                # Lasso
                try:
                    model_lasso = Lasso(alpha=0.005, max_iter=10000)
                    model_lasso.fit(X, y)
                    imp_lasso = np.abs(model_lasso.coef_)
                    imp_lasso_norm = imp_lasso / (imp_lasso.max() + 1e-10)
                except:
                    imp_lasso_norm = np.zeros(len(X.columns))
                
                # Combine
                combined = (params['et']*imp_et_norm + params['gb']*imp_gb_norm + 
                           params['ridge']*imp_ridge_norm + params['lasso']*imp_lasso_norm)
                
                X_cols = [c for c in df_clean.columns if c != target]
                for idx, cause in enumerate(X_cols):
                    results.append({'Cause': cause, 'Effect': target, 'Score': combined[idx]})
            
            df_preds = pd.DataFrame(results).sort_values('Score', ascending=False)
            all_preds[network_id] = df_preds.head(params['k'])
            print(f"✓ {len(df_preds)} edges → top {params['k']}")
        
        # Generate ZIP
        zip_name = f"prediction_phase12c_{config_name}.zip"
        with ZipFile(zip_name, 'w') as zf:
            for network_id in range(1, 6):
                df_top = all_preds[network_id][['Cause', 'Effect', 'Score']]
                csv_name = f"predictions_network{network_id}.csv"
                df_top.to_csv(csv_name, index=False)
                zf.write(csv_name)
                os.remove(csv_name)
        
        file_size = os.path.getsize(zip_name) / 1024
        print(f"\n✓ Generated: {zip_name} ({file_size:.1f} KB)")
        print(f"  Submit this to CodaLab!")
    
    print("\n" + "="*80)
    print("✓ Phase 12C Complete - 2 configurations generees")
    print("="*80)
    print("""
NEXT STEPS:
1. Submit: prediction_phase12c_test1_reduced_et.zip
2. Wait for score
3. If >0.335: Continue with K variations
4. If ~0.33: Try test2_balanced
5. If <0.33: Revert to 0.33 baseline
    """)

if __name__ == '__main__':
    main()
