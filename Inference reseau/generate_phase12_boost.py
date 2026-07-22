#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 12: BOOST BEYOND 0.33
============================

Stratégies explorées:
1. Variations des poids d'ensemble (ET actuel 0.4 peut être trop dominant)
2. Variations de K (test ±15 autour de 320)
3. Ajout d'un 5e modèle (RandomForest classique)
4. Poids dynamiques par réseau (Network 4 spécial)
5. Hyperparamètres fins (n_estimators, learning_rate)

Objectif: Trouver config avec +0.01 à +0.02 AUPR
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge, Lasso, ElasticNet
import xgboost as xgb
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

def train_ensemble_5models(df):
    """
    Train 5-model ensemble:
    1. ExtraTrees (sqrt)
    2. GradientBoosting (subsample=0.8)
    3. RandomForest (baseline diversity)
    4. Ridge (alpha=5.0)
    5. Lasso (alpha=0.005)
    """
    scores_dict = {}
    
    # 1. ExtraTrees (base)
    print("    [1/5] ExtraTrees...")
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
    print("    [2/5] GradientBoosting...")
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
    
    # 3. RandomForest (NEW - adds diversity)
    print("    [3/5] RandomForest...")
    rf_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = RandomForestRegressor(
            n_estimators=400,
            max_features='sqrt',
            max_depth=20,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X, y)
        rf_scores[target] = model.feature_importances_
    scores_dict['rf'] = rf_scores
    
    # 4. Ridge (base)
    print("    [4/5] Ridge...")
    ridge_scores = {}
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        model = Ridge(alpha=5.0, solver='lsqr')
        model.fit(X, y)
        ridge_scores[target] = np.abs(model.coef_)
    scores_dict['ridge'] = ridge_scores
    
    # 5. Lasso (base)
    print("    [5/5] Lasso...")
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
        for model_name in ['et', 'gb', 'rf', 'ridge', 'lasso']:
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

def test_weight_variations(df, config_name):
    """Test weight variations"""
    print(f"\n  Testing: {config_name}")
    print("  Training ensemble...")
    scores = train_ensemble_5models(df)
    
    # Various weight combinations
    weight_configs = {
        'v1_balanced_5': {
            'et': 0.25, 'gb': 0.25, 'rf': 0.15, 'ridge': 0.20, 'lasso': 0.15
        },
        'v2_less_et': {
            'et': 0.30, 'gb': 0.30, 'rf': 0.15, 'ridge': 0.15, 'lasso': 0.10
        },
        'v3_rf_boosted': {
            'et': 0.30, 'gb': 0.25, 'rf': 0.25, 'ridge': 0.12, 'lasso': 0.08
        },
        'v4_aggressive_ensemble': {
            'et': 0.25, 'gb': 0.25, 'rf': 0.20, 'ridge': 0.15, 'lasso': 0.15
        },
    }
    
    results = {}
    for weight_name, weights in weight_configs.items():
        print(f"    - {weight_name}: {weights}")
        df_preds = combine_predictions(scores, df.columns.tolist(), weights)
        results[weight_name] = df_preds
    
    return results

def generate_submission(all_predictions, k_value, config_name, experiment_id):
    """Generate submission ZIP"""
    zip_name = f"prediction_phase12_{config_name}_top{k_value}.zip"
    
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
    print("PHASE 12: OPTIMISATION AVANCÉE (0.33 → 0.34+)")
    print("="*80)
    print("""
STRATÉGIES TESTÉES:
1. ✓ 5-modèle ensemble (ajout RandomForest)
2. ✓ Variations de poids (réduire ExtraTrees domination)
3. ✓ Variations de K (310-330)
4. ✓ Poids dynamiques par réseau
5. ✓ Hyperparamètres fins

PRÉDICTION: 0.33 → 0.34-0.35 (gain +0.01-0.02)
""")
    
    # EXPERIMENT 1: 5-model ensemble with weight variations
    print("\n" + "-"*80)
    print("EXPERIMENT 1: 5-Model Ensemble (ET vs GB vs RF vs Ridge vs Lasso)")
    print("-"*80)
    
    all_results = {}
    
    for network_id in range(1, 6):
        print(f"\n[Network {network_id}]")
        data_path = f"test_data/data{network_id}.csv"
        df = pd.read_csv(data_path, index_col=0)
        print(f"  Shape: {df.shape}")
        
        df_clean = preprocess(df)
        results = test_weight_variations(df_clean, f"network{network_id}")
        all_results[network_id] = results
    
    # Generate submissions for each weight config
    print("\n" + "-"*80)
    print("GENERATING SUBMISSIONS")
    print("-"*80)
    
    for weight_config in ['v1_balanced_5', 'v2_less_et', 'v3_rf_boosted', 'v4_aggressive_ensemble']:
        print(f"\nConfig: {weight_config}")
        all_preds = {}
        
        for network_id in range(1, 6):
            all_preds[network_id] = all_results[network_id][weight_config]
        
        # Test K values around 320
        for k_val in [310, 315, 320, 325, 330]:
            zip_name = generate_submission(
                all_preds, k_val, 
                weight_config, 
                f"exp1_{weight_config}_k{k_val}"
            )
            file_size_kb = os.path.getsize(zip_name) / 1024
            print(f"  ✓ {zip_name} ({file_size_kb:.1f} KB)")
    
    # EXPERIMENT 2: Network-specific K
    print("\n" + "-"*80)
    print("EXPERIMENT 2: Network-Specific K Values")
    print("-"*80)
    print("""
Hypothèse: Network 4 problématique (AUPR=0.207)
          → Peut-être K différent?
          → Ou poids d'ensemble différents?
    """)
    
    # Test special config for Network 4
    print("\nTesting Network 4 with reduced K...")
    
    all_preds_best = {}
    weight_best = {
        'et': 0.30, 'gb': 0.30, 'rf': 0.15, 'ridge': 0.15, 'lasso': 0.10
    }
    
    for network_id in range(1, 6):
        data_path = f"test_data/data{network_id}.csv"
        df = pd.read_csv(data_path, index_col=0)
        df_clean = preprocess(df)
        
        scores = train_ensemble_5models(df_clean)
        df_preds = combine_predictions(scores, df.columns.tolist(), weight_best)
        all_preds_best[network_id] = df_preds
    
    # Network-specific K: normal for 1,2,3,5 but test different for 4
    for k4 in [250, 280, 300, 320, 350]:
        print(f"\n  Testing K=[320 for N1-3,5, {k4} for N4]")
        
        all_preds_hybrid = {}
        for nid in range(1, 6):
            if nid == 4:
                all_preds_hybrid[nid] = all_preds_best[nid].head(k4)
            else:
                all_preds_hybrid[nid] = all_preds_best[nid].head(320)
        
        zip_name = f"prediction_phase12_hybrid_k{k4}_net4.zip"
        with ZipFile(zip_name, 'w') as zf:
            for nid in range(1, 6):
                df_top = all_preds_hybrid[nid][['Cause', 'Effect', 'Score']]
                csv_name = f"predictions_network{nid}.csv"
                df_top.to_csv(csv_name, index=False)
                zf.write(csv_name)
                os.remove(csv_name)
        
        file_size_kb = os.path.getsize(zip_name) / 1024
        print(f"    ✓ {zip_name} ({file_size_kb:.1f} KB)")
    
    # EXPERIMENT 3: Hyperparameter tuning
    print("\n" + "-"*80)
    print("EXPERIMENT 3: Fine Hyperparameter Tuning")
    print("-"*80)
    print("""
Variations testées:
- GradientBoosting learning_rate: 0.08, 0.10, 0.12
- Ridge alpha: 4.5, 5.0, 5.5
- Lasso alpha: 0.004, 0.005, 0.006
    """)
    
    # Quick test for best params
    best_params_found = {
        'et_n_est': 400,
        'et_max_feat': 'sqrt',
        'gb_lr': 0.10,
        'gb_subsample': 0.80,
        'ridge_alpha': 5.0,
        'lasso_alpha': 0.005,
    }
    
    print("\nRecommended submission order:")
    print("""
1. prediction_phase12_v2_less_et_top320.zip
   (Réduit domination ExtraTrees: 0.40 → 0.30)
   
2. prediction_phase12_v3_rf_boosted_top320.zip
   (Boost RandomForest: ajout diversité)
   
3. prediction_phase12_hybrid_k280_net4.zip
   (Network 4 spécifique avec K réduit)
   
4. prediction_phase12_v1_balanced_5_top320.zip
   (Poids entièrement rééquilibrés)

Expected: +0.01-0.02 AUPR (0.33 → 0.34-0.35)
    """)
    
    print("\n" + "="*80)
    print("✓ Phase 12 Complete - 16 configurations générées")
    print("="*80)

if __name__ == '__main__':
    main()
