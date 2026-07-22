#!/usr/bin/env python3
"""
PHASE 4 V2: Validation-Guided Ensemble

NEW INSIGHT:
  target*.csv = TRUE CAUSAL RELATIONSHIPS (edge lists)
  Not numeric targets for regression!

Strategy:
  1. Load true edges from data_train/target*.csv
  2. Train Phase 1 ensemble (4 modèles) on data_train/
  3. Compare ensemble predictions with true edges
  4. Learn which model is BEST for each type of edge
  5. Apply learned weighting to test set
  
Example:
  true_edges_network1 = [(V0,V2), (V0,V3), ...]
  predictions_network1 = [all predictions with scores]
  
  Measure: Which model predicts true edges highest?
  → Adjust weights accordingly!
  → Apply to test set

Objective: 0.32 → 0.40-0.50+
"""

import pandas as pd
import numpy as np
import os
import zipfile
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
import warnings
warnings.filterwarnings('ignore')

os.chdir(r"c:/Users/lassi/projet/Inference reseau")

def preprocess(df):
    """Impute + Standardize"""
    imp = SimpleImputer(strategy='median')
    X = imp.fit_transform(df)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    return pd.DataFrame(X, columns=df.columns)

def get_ensemble_scores(df, target_col):
    """Get scores from 4 base models"""
    X = df.drop(columns=[target_col])
    y = df[target_col].values
    
    scores_by_model = {
        'extratrees': np.zeros(len(X.columns)),
        'gradient': np.zeros(len(X.columns)),
        'ridge': np.zeros(len(X.columns)),
        'lasso': np.zeros(len(X.columns))
    }
    
    try:
        # ExtraTrees
        et = ExtraTreesRegressor(n_estimators=400, max_features='log2', random_state=42, n_jobs=-1)
        et.fit(X, y)
        scores_by_model['extratrees'] = et.feature_importances_
    except:
        pass
    
    try:
        # GradientBoosting
        gb = GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42)
        gb.fit(X, y)
        scores_by_model['gradient'] = gb.feature_importances_
    except:
        pass
    
    try:
        # Ridge
        ridge = Ridge(alpha=1.0)
        ridge.fit(X, y)
        scores_by_model['ridge'] = np.abs(ridge.coef_)
    except:
        pass
    
    try:
        # Lasso
        lasso = Lasso(alpha=0.01, max_iter=10000)
        lasso.fit(X, y)
        scores_by_model['lasso'] = np.abs(lasso.coef_)
    except:
        pass
    
    return scores_by_model

def evaluate_model_weights_on_training(network_id):
    """
    Evaluate optimal weights by testing on training data with true edges
    
    Returns adjusted weights based on what works best for this network
    """
    
    try:
        # Load training data and true edges
        data = pd.read_csv(f'data_train/data{network_id}.csv')
        true_edges = pd.read_csv(f'data_train/target{network_id}.csv')
        
        data_proc = preprocess(data)
        
        # Convert true edges to set for fast lookup
        true_edges_set = set(zip(true_edges['Cause'], true_edges['Effect']))
        
        # Get scores from all 4 models for first target
        first_target = data_proc.columns[0]
        scores_by_model = get_ensemble_scores(data_proc, first_target)
        
        # Evaluate each model: what fraction of top predictions are true edges?
        model_accuracies = {}
        
        for model_name, scores in scores_by_model.items():
            if np.sum(scores) == 0:
                model_accuracies[model_name] = 0
                continue
            
            # Get top 50 predictions
            top_indices = np.argsort(scores)[-50:]
            top_features = [data_proc.columns[i] for i in top_indices]
            
            # Check how many match true edges with this target
            matches = sum(1 for feat in top_features if (feat, first_target) in true_edges_set)
            model_accuracies[model_name] = matches / len(top_indices) if len(top_indices) > 0 else 0
        
        # Convert accuracies to weights (normalized)
        total_acc = sum(model_accuracies.values())
        if total_acc > 0:
            weights = {k: v/total_acc for k, v in model_accuracies.items()}
        else:
            weights = {'extratrees': 0.4, 'gradient': 0.3, 'ridge': 0.2, 'lasso': 0.1}
        
        return weights, model_accuracies
        
    except Exception as e:
        print(f"  Error evaluating network {network_id}: {e}")
        # Default weights
        return {'extratrees': 0.4, 'gradient': 0.3, 'ridge': 0.2, 'lasso': 0.1}, {}

def generate_validation_guided_predictions(k_value=300, variant_name="v1", verbose=True):
    """Generate predictions using validation-guided weights"""
    
    if verbose:
        print(f"\n--- Top-{k_value} ({variant_name}) ---")
    
    test_files = [f'test_data/data{i}.csv' for i in range(1, 6)]
    all_predictions = []
    
    for g in range(1, 6):
        test_file = test_files[g-1]
        
        try:
            # Evaluate optimal weights on training data
            weights, accuracies = evaluate_model_weights_on_training(g)
            if verbose and accuracies:
                print(f"  Network {g} model accuracies: {accuracies}")
                print(f"  Network {g} learned weights: {weights}")
            
            # Load test data
            df = pd.read_csv(test_file)
            df_proc = preprocess(df)
            
            # Get predictions from all targets
            all_pairs = []
            for target_col in df_proc.columns:
                scores_by_model = get_ensemble_scores(df_proc, target_col)
                
                # Combine with learned weights
                combined_scores = np.zeros(len(df_proc.columns) - 1)
                
                for model_name, weight in weights.items():
                    if model_name in scores_by_model:
                        combined_scores += weight * scores_by_model[model_name]
                
                # Create predictions
                features = [col for col in df_proc.columns if col != target_col]
                for feat, score in zip(features, combined_scores):
                    if score > 0:
                        all_pairs.append((feat, target_col, float(score)))
            
            # Create dataframe and sort
            preds_df = pd.DataFrame(all_pairs, columns=['Cause', 'Effect', 'Score'])
            
            if len(preds_df) > 0:
                preds_df = preds_df.sort_values('Score', ascending=False).head(k_value)
                preds_df['Score'] = preds_df['Score'] / preds_df['Score'].sum()
            
            out_csv = f'predictions_network{g}.csv'
            preds_df.to_csv(out_csv, index=False)
            all_predictions.append(len(preds_df))
            
            if verbose:
                print(f"  Network {g}: {len(preds_df)} predictions")
        
        except Exception as e:
            print(f"  Network {g}: ERROR - {e}")
            all_predictions.append(0)
    
    # Create ZIP
    zip_path = f'prediction_valguided_{variant_name}_top{k_value}.zip'
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for g in range(1, 6):
            csv_file = f'predictions_network{g}.csv'
            if os.path.exists(csv_file):
                zf.write(csv_file, arcname=os.path.basename(csv_file))
    
    total = sum(all_predictions)
    if verbose:
        print(f"  ✓ Created {zip_path} ({total} total predictions)")
    
    return zip_path

# MAIN EXECUTION
print("\n" + "="*70)
print("PHASE 4 V2: Validation-Guided Ensemble")
print("="*70)

print("""
NEW INSIGHT:
═════════════════════════════════════════════════════════════════

data_train/target*.csv contains TRUE CAUSAL EDGES!

Strategy:
  1. Load true edges from training data
  2. Evaluate 4 models on training data
  3. Measure: Which model ranks true edges highest?
  4. Learn optimal weights from validation
  5. Apply to test set
  
Example:
  Model A: True edges rank 1-50 high  → weight = 0.5
  Model B: True edges rank 100+ low   → weight = 0.1
  Model C: True edges rank 20-40 high → weight = 0.3
  Model D: True edges rank 60-80      → weight = 0.1
  
Result: Optimized ensemble = 0.32 → 0.40+?

OBJECTIVE: Learn from ground truth edges!
""")

# Generate validation-guided variants
vg_configs = [
    {'k': 300, 'name': 'p4v2_balanced'},
    {'k': 320, 'name': 'p4v2_tuned'},
    {'k': 350, 'name': 'p4v2_aggressive'},
]

generated_files = []
for config in vg_configs:
    try:
        zip_file = generate_validation_guided_predictions(
            k_value=config['k'],
            variant_name=config['name'],
            verbose=True
        )
        generated_files.append((config['name'], zip_file))
    except Exception as e:
        print(f"✗ Error generating {config['name']}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*70)
print("SUMMARY - PHASE 4 V2")
print("="*70)
print(f"\n✓ Generated {len(generated_files)} Validation-Guided ZIP files:\n")

for name, filepath in generated_files:
    from pathlib import Path
    if os.path.exists(filepath):
        file_size = Path(filepath).stat().st_size
        print(f"  • prediction_valguided_{name}_top*.zip ({file_size} bytes)")

print("\n" + "="*70)
print("SUBMISSION PRIORITY - PHASE 4 V2")
print("="*70)
print("""
TIER 1 (BREAKTHROUGH POTENTIAL):
  1. prediction_valguided_p4v2_balanced_top300.zip
  2. prediction_valguided_p4v2_tuned_top320.zip
  3. prediction_valguided_p4v2_aggressive_top350.zip

RATIONALE: 
  Using ground truth edges from training data
  Should provide major improvement
  
EXPECTED: 
  • Phase 1 (Simple Ensemble): 0.32
  • Phase 4 V2 (Validation-Guided): 0.35-0.50+???
  
  This is a new approach with ground truth signal!
  
  If ≥ 0.40: Massive breakthrough! Approaching 0.60 goal
  If 0.35-0.40: Good! Ground truth approach works
  If < 0.32: Validation approach needs refinement

Budget: ~34 submissions remaining
""")

print("\n✓ All Phase 4 V2 validation-guided files ready for submission!")
print("\nRECOMMENDATION: Soumettez les 3 fichiers Phase 4 V2 maintenant!")
