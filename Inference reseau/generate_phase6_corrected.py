"""
PHASE 6 CORRECTED: Proper Regression-Based Ensemble

Correct approach (from Phase 1):
  For each target node j:
    - Train models to predict node j's values from all other nodes
    - Extract feature importances as edge scores (i → j)
    - These scores represent causal importance

Key insight:
  - Train on 20 dimensions (data_train/)
  - Apply to 100 dimensions (test_data/)
  - This explains why Phase 1 got 0.32
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

# ============================================================================
# PREPROCESSING
# ============================================================================

def preprocess(df):
    """Impute and standardize - handle headers properly"""
    # Convert to numeric
    df_numeric = df.apply(pd.to_numeric, errors='coerce')
    
    imp = SimpleImputer(strategy='median')
    X_imputed = imp.fit_transform(df_numeric)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_imputed)
    
    # Return DataFrame with column names preserved
    return pd.DataFrame(X_scaled, columns=df_numeric.columns)

# ============================================================================
# CORE: Train-Predict for regression-based edge scoring
# ============================================================================

def get_extratrees_scores(df):
    """ExtraTrees: Feature importance per target column"""
    rows = []
    
    # Convert column names to indices
    col_to_idx = {col: idx for idx, col in enumerate(df.columns)}
    
    for target_col_idx, target_col in enumerate(df.columns):
        X = df.drop(columns=[target_col])
        y = df[target_col].values
        
        try:
            model = ExtraTreesRegressor(n_estimators=400, max_features='log2', random_state=42, n_jobs=-1)
            model.fit(X, y)
            
            # X.columns are in same order as feature_importances_
            cause_idx = 0
            for cause_col_idx, cause_col in enumerate(X.columns):
                importance = model.feature_importances_[cause_idx]
                if importance > 0:
                    # Map back to original indices
                    original_cause_idx = col_to_idx[cause_col]
                    rows.append((original_cause_idx, target_col_idx, float(importance)))
                cause_idx += 1
        except:
            pass
    
    if rows:
        result_df = pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
        result_df['Score'] = result_df['Score'] / result_df['Score'].sum()
        return result_df
    return pd.DataFrame(columns=['Cause', 'Effect', 'Score'])

def get_gradient_scores(df):
    """GradientBoosting: Feature importance per target"""
    rows = []
    col_to_idx = {col: idx for idx, col in enumerate(df.columns)}
    
    for target_col_idx, target_col in enumerate(df.columns):
        X = df.drop(columns=[target_col])
        y = df[target_col].values
        
        try:
            model = GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42)
            model.fit(X, y)
            
            cause_idx = 0
            for cause_col_idx, cause_col in enumerate(X.columns):
                importance = model.feature_importances_[cause_idx]
                if importance > 0:
                    original_cause_idx = col_to_idx[cause_col]
                    rows.append((original_cause_idx, target_col_idx, float(importance)))
                cause_idx += 1
        except:
            pass
    
    if rows:
        result_df = pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
        result_df['Score'] = result_df['Score'] / result_df['Score'].sum()
        return result_df
    return pd.DataFrame(columns=['Cause', 'Effect', 'Score'])

def get_ridge_scores(df):
    """Ridge: Absolute coefficients per target"""
    rows = []
    col_to_idx = {col: idx for idx, col in enumerate(df.columns)}
    
    for target_col_idx, target_col in enumerate(df.columns):
        X = df.drop(columns=[target_col])
        y = df[target_col].values
        
        try:
            model = Ridge(alpha=1.0)
            model.fit(X, y)
            
            for cause_idx, cause_col in enumerate(X.columns):
                coef = np.abs(model.coef_[cause_idx])
                if coef > 0:
                    original_cause_idx = col_to_idx[cause_col]
                    rows.append((original_cause_idx, target_col_idx, float(coef)))
        except:
            pass
    
    if rows:
        result_df = pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
        result_df['Score'] = result_df['Score'] / result_df['Score'].sum()
        return result_df
    return pd.DataFrame(columns=['Cause', 'Effect', 'Score'])

def get_lasso_scores(df):
    """Lasso: Absolute coefficients per target"""
    rows = []
    col_to_idx = {col: idx for idx, col in enumerate(df.columns)}
    
    for target_col_idx, target_col in enumerate(df.columns):
        X = df.drop(columns=[target_col])
        y = df[target_col].values
        
        try:
            model = Lasso(alpha=0.01, max_iter=10000, random_state=42)
            model.fit(X, y)
            
            for cause_idx, cause_col in enumerate(X.columns):
                coef = np.abs(model.coef_[cause_idx])
                if coef > 0:
                    original_cause_idx = col_to_idx[cause_col]
                    rows.append((original_cause_idx, target_col_idx, float(coef)))
        except:
            pass
    
    if rows:
        result_df = pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
        result_df['Score'] = result_df['Score'] / result_df['Score'].sum()
        return result_df
    return pd.DataFrame(columns=['Cause', 'Effect', 'Score'])

# ============================================================================
# ENSEMBLE COMBINATIONS
# ============================================================================

def combine_ensemble_predictions(dfs_dict, weights):
    """Combine predictions from 4 models using weighted vote"""
    combined = []
    
    # Get all unique edges
    all_edges = set()
    for model_name, df in dfs_dict.items():
        if df is not None and len(df) > 0:
            for _, row in df.iterrows():
                all_edges.add((int(row['Cause']), int(row['Effect'])))
    
    # Combine scores
    for cause, effect in all_edges:
        total_score = 0
        for model_name, weight in weights.items():
            df = dfs_dict[model_name]
            if df is not None and len(df) > 0:
                matching = df[(df['Cause'] == cause) & (df['Effect'] == effect)]
                if len(matching) > 0:
                    total_score += weight * matching['Score'].values[0]
        
        combined.append({'Cause': cause, 'Effect': effect, 'Score': total_score})
    
    return pd.DataFrame(combined)

# ============================================================================
# GENERATE VARIANTS
# ============================================================================

def generate_phase6_variants():
    """Generate 3 Phase 6 variants with different weights"""
    
    print("=" * 70)
    print("PHASE 6: CORRECTED REGRESSION-BASED ENSEMBLE")
    print("=" * 70)
    
    variants = [
        ('extratrees_heavy', {'extratrees': 0.5, 'gradient': 0.25, 'ridge': 0.15, 'lasso': 0.1}, 300),
        ('regularized', {'extratrees': 0.3, 'gradient': 0.2, 'ridge': 0.25, 'lasso': 0.25}, 320),
        ('gb_focus', {'extratrees': 0.3, 'gradient': 0.4, 'ridge': 0.15, 'lasso': 0.15}, 310),
    ]
    
    for variant_name, weights, k_value in variants:
        print(f"\n--- Variant: {variant_name} (K={k_value}) ---")
        
        all_predictions = []
        
        for net_id in range(1, 6):
            print(f"  Network {net_id}...", end="", flush=True)
            
            # Load test data - has headers V0-V99
            test_df = pd.read_csv(f"test_data/data{net_id}.csv")
            test_preprocessed = preprocess(test_df)
            
            # Get scores from 4 models
            et_scores = get_extratrees_scores(test_preprocessed)
            gb_scores = get_gradient_scores(test_preprocessed)
            ridge_scores = get_ridge_scores(test_preprocessed)
            lasso_scores = get_lasso_scores(test_preprocessed)
            
            # Combine
            combined = combine_ensemble_predictions(
                {
                    'extratrees': et_scores,
                    'gradient': gb_scores,
                    'ridge': ridge_scores,
                    'lasso': lasso_scores
                },
                weights
            )
            
            # Sort and take top-K
            combined_sorted = combined.sort_values('Score', ascending=False).head(k_value)
            all_predictions.append(combined_sorted)
            
            print(f" {len(combined_sorted)} predictions")
        
        # Combine all networks
        final_predictions = pd.concat(all_predictions, ignore_index=True)
        
        # Create ZIP
        zip_path = f"prediction_corrected_p6_{variant_name}_top{k_value}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            csv_data = final_predictions.to_csv(index=False)
            zf.writestr("predictions.csv", csv_data)
        
        zip_size = Path(zip_path).stat().st_size
        print(f"  ✓ Created {zip_path} ({zip_size:,} bytes, {len(final_predictions)} total predictions)")
    
    print("\n" + "=" * 70)
    print("✓ PHASE 6 CORRECTED: Ready for submission!")
    print("=" * 70)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    generate_phase6_variants()
