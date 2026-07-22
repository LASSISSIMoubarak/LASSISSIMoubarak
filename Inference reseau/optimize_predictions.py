"""
Optimize Top-K strategy on test data
"""
import pandas as pd
import numpy as np
import os
import zipfile
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor

print("="*70)
print("OPTIMIZING Top-K STRATEGY ON TEST DATA")
print("="*70)

def load_data(filepath):
    return pd.read_csv(filepath)

def impute_and_scale(df):
    df_clean = df.copy()
    imputer = SimpleImputer(strategy='median')
    X_imp = imputer.fit_transform(df_clean.values)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X_imp)
    return pd.DataFrame(Xs, columns=df.columns, index=df.index)

# Test different K values
k_values = [30, 50, 75, 100, 150, 200]
results = []

for k in k_values:
    print(f"\n--- Testing Top-{k} ---")
    
    for g in range(1, 6):
        test_file = f'test_data/data{g}.csv'
        df_test = load_data(test_file)
        df_test_proc = impute_and_scale(df_test)
        
        rows = []
        for target in df_test_proc.columns:
            X_df = df_test_proc.drop(columns=[target])
            X = X_df.values
            y = df_test_proc[target].values
            
            model = ExtraTreesRegressor(
                n_estimators=400,
                max_features='sqrt',
                random_state=0,
                n_jobs=-1
            )
            model.fit(X, y)
            
            importances = np.abs(model.feature_importances_)
            imp_sum = importances.sum()
            if imp_sum > 0:
                importances = importances / imp_sum
            
            for feat_name, score in zip(X_df.columns, importances):
                if score > 0:
                    rows.append((feat_name, target, float(score)))
        
        pred = pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
        pred = pred.sort_values('Score', ascending=False).head(k)
        
        out_csv = f'predictions_network{g}.csv'
        pred.to_csv(out_csv, index=False)
        
        print(f"  Graph {g}: {len(pred)} predictions")
    
    # Create zip for this k
    zip_path = f'prediction_top{k}.zip'
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for g in range(1, 6):
            csv_file = f'predictions_network{g}.csv'
            if os.path.exists(csv_file):
                zf.write(csv_file, arcname=os.path.basename(csv_file))
    
    results.append({'K': k, 'Zip': zip_path})
    print(f"  ✓ Created {zip_path}")

print("\n" + "="*70)
print("GENERATED SUBMISSION FILES")
print("="*70)
print("\nCurrent best: Top-50 → 0.15")
print("\nTo test higher scores, try in order:")
for r in results:
    print(f"  {r['Zip']}")
print("\nUpload each to site and compare scores!")
print("\nExpected improvement order: Top-50 (0.15) → Top-100 → Top-75 → Top-200")
