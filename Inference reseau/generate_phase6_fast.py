"""
PHASE 6 ULTRA-FAST: Test weight combinations on 20-dim baseline

Key insight: Phase 1 scored 0.32 likely using only first 20 columns.
Let's quickly test if different weights beat 0.32.

Variants (all on 20-dim):
  A. ET-heavy: (0.5, 0.25, 0.15, 0.1)
  B. Regularized: (0.3, 0.2, 0.25, 0.25)
  C. GB-boost: (0.3, 0.4, 0.15, 0.15)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import zipfile
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

def preprocess(df):
    imp = SimpleImputer(strategy='median')
    X = imp.fit_transform(df)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    return X

def extract_edge_scores(df, model, model_name):
    """Train model on each target column, extract feature importances"""
    rows = []
    
    for target_idx in range(len(df.columns)):
        X = df.drop(columns=df.columns[target_idx])
        y = df.iloc[:, target_idx].values
        
        X_preprocessed = preprocess(X)
        
        if model_name == 'et':
            m = ExtraTreesRegressor(n_estimators=400, max_features='log2', random_state=42, n_jobs=-1)
            m.fit(X_preprocessed, y)
            importances = m.feature_importances_
        elif model_name == 'gb':
            m = GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42)
            m.fit(X_preprocessed, y)
            importances = m.feature_importances_
        elif model_name == 'ridge':
            m = Ridge(alpha=1.0)
            m.fit(X_preprocessed, y)
            importances = np.abs(m.coef_)
        else:  # lasso
            m = Lasso(alpha=0.01, max_iter=10000, random_state=42)
            m.fit(X_preprocessed, y)
            importances = np.abs(m.coef_)
        
        # Map back to original column indices
        cause_idx = 0
        for orig_idx in range(len(df.columns)):
            if orig_idx != target_idx:
                score = importances[cause_idx]
                if score > 0:
                    rows.append((orig_idx, target_idx, float(score)))
                cause_idx += 1
    
    if rows:
        result = pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
        result['Score'] = result['Score'] / result['Score'].max()
        return result
    return pd.DataFrame(columns=['Cause', 'Effect', 'Score'])

def generate_variants():
    print("=" * 70)
    print("PHASE 6 ULTRA-FAST: Weight Tuning on 20-dim")
    print("=" * 70)
    
    variants = [
        ('et_heavy_300', [0.5, 0.25, 0.15, 0.1], 300),
        ('regularized_320', [0.3, 0.2, 0.25, 0.25], 320),
        ('gb_boost_310', [0.3, 0.4, 0.15, 0.15], 310),
    ]
    
    for var_name, (weight_et, weight_gb, weight_ridge, weight_lasso), k_val in [
        ('et_heavy_300', (0.5, 0.25, 0.15, 0.1), 300),
        ('regularized_320', (0.3, 0.2, 0.25, 0.25), 320),
        ('gb_boost_310', (0.3, 0.4, 0.15, 0.15), 310),
    ]:
        print(f"\n--- {var_name} (K={k_val}) ---")
        
        all_edges = {}
        
        for net_id in range(1, 6):
            print(f"  Network {net_id}...", end="", flush=True)
            
            # Load 20-dim data
            df = pd.read_csv(f"test_data/data{net_id}.csv").iloc[:, :20]
            
            # Get scores from 4 models
            et_scores = extract_edge_scores(df, None, 'et')
            gb_scores = extract_edge_scores(df, None, 'gb')
            ridge_scores = extract_edge_scores(df, None, 'ridge')
            lasso_scores = extract_edge_scores(df, None, 'lasso')
            
            # Combine all edges with scores
            all_edges_net = set()
            edge_to_scores = {}
            
            for _, row in et_scores.iterrows():
                key = (int(row['Cause']), int(row['Effect']))
                all_edges_net.add(key)
                edge_to_scores[key] = {'et': row['Score']}
            
            for _, row in gb_scores.iterrows():
                key = (int(row['Cause']), int(row['Effect']))
                all_edges_net.add(key)
                if key not in edge_to_scores:
                    edge_to_scores[key] = {}
                edge_to_scores[key]['gb'] = row['Score']
            
            for _, row in ridge_scores.iterrows():
                key = (int(row['Cause']), int(row['Effect']))
                all_edges_net.add(key)
                if key not in edge_to_scores:
                    edge_to_scores[key] = {}
                edge_to_scores[key]['ridge'] = row['Score']
            
            for _, row in lasso_scores.iterrows():
                key = (int(row['Cause']), int(row['Effect']))
                all_edges_net.add(key)
                if key not in edge_to_scores:
                    edge_to_scores[key] = {}
                edge_to_scores[key]['lasso'] = row['Score']
            
            # Weighted ensemble
            net_edges = []
            for cause, effect in all_edges_net:
                scores = edge_to_scores.get((cause, effect), {})
                combined = (
                    weight_et * scores.get('et', 0) +
                    weight_gb * scores.get('gb', 0) +
                    weight_ridge * scores.get('ridge', 0) +
                    weight_lasso * scores.get('lasso', 0)
                )
                net_edges.append({'Cause': cause, 'Effect': effect, 'Score': combined})
            
            # Sort and take top-K
            net_edges_df = pd.DataFrame(net_edges)
            net_edges_df = net_edges_df.nlargest(k_val, 'Score')
            all_edges[net_id] = net_edges_df
            
            print(f" {len(net_edges_df)} predictions")
        
        # Combine all networks
        final_df = pd.concat([all_edges[n] for n in range(1, 6)], ignore_index=True)
        
        # Create ZIP with 5 separate network files
        zip_path = f"prediction_fast_p6_{var_name}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for net_id in range(1, 6):
                net_df = all_edges[net_id]
                csv_data = net_df.to_csv(index=False)
                zf.writestr(f"predictions_network{net_id}.csv", csv_data)
        
        zip_size = Path(zip_path).stat().st_size
        print(f"  ✓ Created {zip_path} ({zip_size:,} bytes, {len(final_df)} total)")
    
    print("\n" + "=" * 70)
    print("✓ PHASE 6 COMPLETE: Ready for submission!")
    print("=" * 70)

if __name__ == "__main__":
    generate_variants()
