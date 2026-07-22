"""
PHASE 6 FIXED: Correct regression-based ensemble with training data

Correct approach:
  1. Train on data_train/data*.csv (20-dim)
  2. Extract feature importances per target
  3. These importances are edge scores (i → j)
  4. Combine with different weights
  5. Apply to test data

Key fix: Train on TRAINING data, not test data!
"""

import pandas as pd
import numpy as np
from pathlib import Path
import zipfile
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

def preprocess(df):
    """Impute and standardize"""
    imp = SimpleImputer(strategy='median')
    X = imp.fit_transform(df)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    return X

def train_and_score_network(train_df, weights):
    """
    Train 4 models on training data, extract edge scores.
    
    For each target column j:
      - Train models to predict column j from other columns
      - Extract feature importances = scores for edges i→j
    """
    
    edge_scores = {}  # (cause, effect) → combined_score
    
    # Train 4 models per target column
    for target_idx in range(len(train_df.columns)):
        X_train = train_df.drop(columns=train_df.columns[target_idx])
        y_train = train_df.iloc[:, target_idx].values
        X_train_preprocessed = preprocess(X_train)
        
        scores_by_model = {}
        
        # ExtraTrees
        try:
            model_et = ExtraTreesRegressor(n_estimators=400, max_features='log2', random_state=42, n_jobs=-1)
            model_et.fit(X_train_preprocessed, y_train)
            scores_by_model['et'] = model_et.feature_importances_
        except:
            scores_by_model['et'] = np.zeros(len(X_train.columns))
        
        # GradientBoosting
        try:
            model_gb = GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42)
            model_gb.fit(X_train_preprocessed, y_train)
            scores_by_model['gb'] = model_gb.feature_importances_
        except:
            scores_by_model['gb'] = np.zeros(len(X_train.columns))
        
        # Ridge
        try:
            model_ridge = Ridge(alpha=1.0)
            model_ridge.fit(X_train_preprocessed, y_train)
            scores_by_model['ridge'] = np.abs(model_ridge.coef_)
        except:
            scores_by_model['ridge'] = np.zeros(len(X_train.columns))
        
        # Lasso
        try:
            model_lasso = Lasso(alpha=0.01, max_iter=10000, random_state=42)
            model_lasso.fit(X_train_preprocessed, y_train)
            scores_by_model['lasso'] = np.abs(model_lasso.coef_)
        except:
            scores_by_model['lasso'] = np.zeros(len(X_train.columns))
        
        # Combine scores with weights
        cause_idx = 0
        for cause_col_idx in range(len(train_df.columns)):
            if cause_col_idx != target_idx:
                combined_score = (
                    weights['et'] * scores_by_model['et'][cause_idx] +
                    weights['gb'] * scores_by_model['gb'][cause_idx] +
                    weights['ridge'] * scores_by_model['ridge'][cause_idx] +
                    weights['lasso'] * scores_by_model['lasso'][cause_idx]
                )
                edge_scores[(cause_col_idx, target_idx)] = combined_score
                cause_idx += 1
    
    return edge_scores

def generate_phase6_fixed():
    """Generate 3 Phase 6 variants with correct training"""
    
    print("=" * 70)
    print("PHASE 6 FIXED: Correct Regression-Based Ensemble")
    print("=" * 70)
    print("\nCritical Fix:")
    print("  ✓ Train on data_train/ (NOT test_data/)")
    print("  ✓ Extract edge scores from feature importances")
    print("  ✓ Apply different weight combinations")
    
    variants = [
        ('et_heavy_300', {'et': 0.5, 'gb': 0.25, 'ridge': 0.15, 'lasso': 0.1}, 300),
        ('regularized_320', {'et': 0.3, 'gb': 0.2, 'ridge': 0.25, 'lasso': 0.25}, 320),
        ('gb_boost_310', {'et': 0.3, 'gb': 0.4, 'ridge': 0.15, 'lasso': 0.15}, 310),
    ]
    
    for var_name, weights, k_val in variants:
        print(f"\n--- {var_name} (K={k_val}) ---")
        print(f"    Weights: ET={weights['et']}, GB={weights['gb']}, Ridge={weights['ridge']}, Lasso={weights['lasso']}")
        
        all_edges_by_net = {}
        
        for net_id in range(1, 6):
            print(f"    Network {net_id}...", end="", flush=True)
            
            # Load TRAINING data
            train_df = pd.read_csv(f"data_train/data{net_id}.csv")
            
            # Train and extract edge scores
            edge_scores = train_and_score_network(train_df, weights)
            
            # Convert to list and sort by score
            edges_list = [
                {'Cause': cause, 'Effect': effect, 'Score': score}
                for (cause, effect), score in edge_scores.items()
            ]
            edges_df = pd.DataFrame(edges_list)
            edges_df = edges_df.nlargest(k_val, 'Score')
            
            all_edges_by_net[net_id] = edges_df
            print(f" {len(edges_df)} predictions")
        
        # Combine all networks
        final_df = pd.concat([all_edges_by_net[n] for n in range(1, 6)], ignore_index=True)
        
        # Create ZIP with 5 network files
        zip_path = f"prediction_fixed_p6_{var_name}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for net_id in range(1, 6):
                net_df = all_edges_by_net[net_id]
                csv_data = net_df.to_csv(index=False)
                zf.writestr(f"predictions_network{net_id}.csv", csv_data)
        
        zip_size = Path(zip_path).stat().st_size
        print(f"    ✓ Created {zip_path} ({zip_size:,} bytes, {len(final_df)} total)")
    
    print("\n" + "=" * 70)
    print("✓ PHASE 6 FIXED: Ready for submission!")
    print("=" * 70)
    print("\nExpected: Back to 0.32+ (correct training)")

if __name__ == "__main__":
    generate_phase6_fixed()
