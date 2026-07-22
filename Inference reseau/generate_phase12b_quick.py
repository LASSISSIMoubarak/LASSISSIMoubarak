#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 12B: QUICK OPTIMIZATION (Faster Version)
================================================

Version optimisée pour rapidité:
- Teste uniquement les 3 meilleures configurations de poids
- Variations de K seulement pour la meilleure config
- Pas de RandomForest (coûteux en temps)

Temps d'exécution: ~30 min vs ~2h pour v1
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso, ElasticNet
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

def train_ensemble_4models_fast(df):
    """Train 4-model ensemble (current + ElasticNet variant)"""
    scores_dict = {}
    
    # 1. ExtraTrees (base)
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
    
    # 2. GradientBoosting (base)
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
    
    # 3. Ridge (base)
    ridge_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = Ridge(alpha=5.0, solver='lsqr')
        model.fit(X, y)
        ridge_scores[target] = np.abs(model.coef_)
    scores_dict['ridge'] = ridge_scores
    
    # 4. Lasso (base)
    lasso_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        try:
            model = Lasso(alpha=0.005, max_iter=10000)
            model.fit(X, y)
            lasso_scores[target] = np.abs(model.coef_)
        except:
            lasso_scores[target] = np.zeros(len(X.columns))
    scores_dict['lasso'] = lasso_scores
    
    return scores_dict

def combine_predictions(scores_dict, targets, weights):
    """Weighted combination"""
    results = []
    
    for target in targets:
        # Get normalized importances
        scores = {}
        for model_name in ['et', 'gb', 'ridge', 'lasso']:
            imp = scores_dict[model_name][target]
            imp_norm = imp / (imp.max() + 1e-10)
            scores[model_name] = imp_norm
        
        # Weighted combination
        combined = np.zeros(len(scores['et']))
        for model_name, weight in weights.items():
            if model_name in scores:
                combined += weight * scores[model_name]
        
        X_cols = [t for t in targets if t != target]
        for cause_idx, cause in enumerate(X_cols):
            results.append({
                'Cause': cause,
                'Effect': target,
                'Score': combined[cause_idx]
            })
    
    return pd.DataFrame(results).sort_values('Score', ascending=False).reset_index(drop=True)

def generate_submission_fast(all_predictions, k_value, config_name):
    """Generate submission ZIP"""
    zip_name = f"prediction_phase12b_{config_name}_top{k_value}.zip"
    
    with ZipFile(zip_name, 'w') as zf:
        for network_id in range(1, 6):
            if network_id in all_predictions:
                df_preds = all_predictions[network_id]
                df_top_k = df_preds.head(k_value)[['Cause', 'Effect', 'Score']]
                csv_name = f"predictions_network{network_id}.csv"
                df_top_k.to_csv(csv_name, index=False)
                zf.write(csv_name)
                os.remove(csv_name)
    
    return zip_name

def main():
    print("\n" + "="*80)
    print("PHASE 12B: QUICK OPTIMIZATION (0.33 → 0.34+) - FAST VERSION")
    print("="*80)
    print("""
STRATÉGIES TESTÉES (VERSION RAPIDE):
1. ✓ Réduction domination ExtraTrees (0.40 → 0.35)
2. ✓ Augmentation Ridge/Lasso (contre-poids)
3. ✓ Variations de K (310-335)

Configurations de poids:
- baseline_optimized: ET:0.4, GB:0.3, Ridge:0.2, Lasso:0.1 (current 0.33)
- reduced_et: ET:0.35, GB:0.35, Ridge:0.2, Lasso:0.1 (réduction légère)
- balanced_linear: ET:0.30, GB:0.30, Ridge:0.25, Lasso:0.15 (poids linéaires)
- aggressive_regularization: ET:0.30, GB:0.25, Ridge:0.30, Lasso:0.15 (boost Ridge/Lasso)
- ensemble_conservative: ET:0.25, GB:0.25, Ridge:0.35, Lasso:0.15 (conservatif)
    """)
    
    # Generate ensemble for all networks
    print("\nTraining ensemble for all networks...")
    all_scores = {}
    
    for network_id in range(1, 6):
        print(f"\n[Network {network_id}]")
        data_path = f"test_data/data{network_id}.csv"
        df = pd.read_csv(data_path, index_col=0)
        print(f"  Shape: {df.shape}")
        print(f"  Preprocessing...")
        df_clean = preprocess(df)
        print(f"  Training ensemble...")
        scores = train_ensemble_4models_fast(df_clean)
        all_scores[network_id] = {
            'scores': scores,
            'targets': df.columns.tolist()
        }
    
    # Test weight configurations
    weight_configs = {
        'baseline': {
            'et': 0.40, 'gb': 0.30, 'ridge': 0.20, 'lasso': 0.10
        },
        'reduced_et': {
            'et': 0.35, 'gb': 0.35, 'ridge': 0.20, 'lasso': 0.10
        },
        'balanced': {
            'et': 0.30, 'gb': 0.30, 'ridge': 0.25, 'lasso': 0.15
        },
        'aggressive_reg': {
            'et': 0.30, 'gb': 0.25, 'ridge': 0.30, 'lasso': 0.15
        },
        'conservative': {
            'et': 0.25, 'gb': 0.25, 'ridge': 0.35, 'lasso': 0.15
        },
    }
    
    print("\n" + "-"*80)
    print("GENERATING SUBMISSIONS")
    print("-"*80)
    
    for config_name, weights in weight_configs.items():
        print(f"\n>>> Config: {config_name}")
        print(f"    Weights: ET={weights['et']}, GB={weights['gb']}, Ridge={weights['ridge']}, Lasso={weights['lasso']}")
        
        all_preds = {}
        for network_id in range(1, 6):
            data = all_scores[network_id]
            df_preds = combine_predictions(data['scores'], data['targets'], weights)
            all_preds[network_id] = df_preds
        
        # Test K values
        for k_val in [310, 315, 320, 325, 330, 335]:
            zip_name = generate_submission_fast(all_preds, k_val, f"{config_name}_k{k_val}")
            file_size_kb = os.path.getsize(zip_name) / 1024
            print(f"    ✓ {zip_name} ({file_size_kb:.1f} KB)")
    
    # ADDITIONAL: Test hyperparameter variations
    print("\n" + "-"*80)
    print("BONUS: Hyperparameter Variations")
    print("-"*80)
    print("""
Testing alternative hyperparams:
- Ridge alpha: 4.5, 5.5 (vs current 5.0)
- Lasso alpha: 0.004, 0.006 (vs current 0.005)
- GB subsample: 0.7, 0.9 (vs current 0.8)
    """)
    
    # Test Ridge variation
    print("\nTesting Ridge alpha variations...")
    for ridge_alpha in [4.5, 5.5]:
        print(f"\n  Ridge alpha = {ridge_alpha}")
        all_preds_ridge = {}
        
        for network_id in range(1, 6):
            targets = all_scores[network_id]['targets']
            X_id = [t for t in targets]
            
            # Recompute Ridge only
            ridge_scores = {}
            data_path = f"test_data/data{network_id}.csv"
            df = pd.read_csv(data_path, index_col=0)
            df_clean = preprocess(df)
            
            for target in df_clean.columns:
                X = df_clean.drop(columns=[target])
                y = df_clean[target].values
                model = Ridge(alpha=ridge_alpha, solver='lsqr')
                model.fit(X, y)
                ridge_scores[target] = np.abs(model.coef_)
            
            # Combine with best weights (reduced_et)
            scores_dict = all_scores[network_id]['scores'].copy()
            scores_dict['ridge'] = ridge_scores
            
            weights_best = {
                'et': 0.35, 'gb': 0.35, 'ridge': 0.20, 'lasso': 0.10
            }
            df_preds = combine_predictions(scores_dict, targets, weights_best)
            all_preds_ridge[network_id] = df_preds
        
        zip_name = generate_submission_fast(
            all_preds_ridge, 320, f"reduced_et_ridge{ridge_alpha}"
        )
        file_size_kb = os.path.getsize(zip_name) / 1024
        print(f"    ✓ {zip_name} ({file_size_kb:.1f} KB)")
    
    print("\n" + "="*80)
    print("✓ Phase 12B Complete - 30 configurations générées")
    print("="*80)
    print("""
RECOMMENDED SUBMISSION ORDER:

1️⃣  prediction_phase12b_reduced_et_k320.zip
    (Léger réduction ExtraTrees: 0.40 → 0.35)
    Espérance: 0.33 → 0.335-0.340

2️⃣  prediction_phase12b_balanced_k320.zip
    (Poids plus balancés)
    Espérance: 0.33 → 0.330-0.338

3️⃣  prediction_phase12b_aggressive_reg_k320.zip
    (Boost Ridge/Lasso pour régularisation)
    Espérance: 0.33 → 0.330-0.337

4️⃣  prediction_phase12b_reduced_et_ridge5.5_top320.zip
    (Combo: moins ET + Ridge plus fort)
    Espérance: 0.33 → 0.331-0.336

Si tous ~0.33: continuer Phase 12A (avec RandomForest)
    """)

if __name__ == '__main__':
    main()
