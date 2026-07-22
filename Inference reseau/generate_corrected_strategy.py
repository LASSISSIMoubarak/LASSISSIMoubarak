"""
STRATÉGIE CORRECTIVE: Augmentation de K + Optimisation Hyperparamètres
"""
import pandas as pd
import numpy as np
import os
import zipfile
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor

os.chdir(r"c:/Users/lassi/projet/Inference reseau")

def preprocess(df):
    """Impute + Standardize"""
    imp = SimpleImputer(strategy='median')
    X = imp.fit_transform(df)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    return pd.DataFrame(X, columns=df.columns)

def get_extratrees_scores(df, n_estimators=400, max_features='sqrt', min_samples_leaf=1, max_depth=None):
    """ExtraTrees avec hyperparamètres personnalisés"""
    rows = []
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        try:
            model = ExtraTreesRegressor(
                n_estimators=n_estimators,
                max_features=max_features,
                min_samples_leaf=min_samples_leaf,
                max_depth=max_depth,
                random_state=42,
                n_jobs=-1
            )
            model.fit(X, y)
            for col, imp in zip(X.columns, model.feature_importances_):
                if imp > 0:
                    rows.append((col, target, float(imp)))
        except Exception as e:
            print(f"  Error for {target}: {e}")
    
    if rows:
        return pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
    return pd.DataFrame(columns=['Cause', 'Effect', 'Score'])

print("="*70)
print("PHASE 1: Augmentation de K (250, 300, 400, 500)")
print("="*70)

test_files = [f'test_data/data{i}.csv' for i in range(1, 6)]
k_values = [250, 300, 400, 500]

for top_k in k_values:
    print(f"\n--- Top-{top_k} ---")
    
    all_predictions = []
    
    for g in range(1, 6):
        test_file = test_files[g-1]
        
        try:
            df = pd.read_csv(test_file)
            df_proc = preprocess(df)
            
            preds = get_extratrees_scores(df_proc, n_estimators=400, max_features='sqrt')
            preds = preds.sort_values('Score', ascending=False).head(top_k)
            
            out_csv = f'predictions_network{g}.csv'
            preds.to_csv(out_csv, index=False)
            all_predictions.append(len(preds))
            
            print(f"  Network {g}: {len(preds)} predictions")
            
        except Exception as e:
            print(f"  Network {g}: ERROR - {e}")
            all_predictions.append(0)
    
    # Créer ZIP
    zip_path = f'prediction_extratrees_top{top_k}.zip'
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for g in range(1, 6):
            csv_file = f'predictions_network{g}.csv'
            if os.path.exists(csv_file):
                zf.write(csv_file, arcname=os.path.basename(csv_file))
    
    total = sum(all_predictions)
    print(f"  ✓ Created {zip_path} ({total} total predictions)")

print("\n" + "="*70)
print("PHASE 2: Optimisation Hyperparamètres (Top-300)")
print("="*70)

# Tester différentes configurations pour Top-300
configs = [
    {'n_estimators': 250, 'max_features': 'sqrt', 'name': 'n_est_250'},
    {'n_estimators': 600, 'max_features': 'sqrt', 'name': 'n_est_600'},
    {'n_estimators': 1000, 'max_features': 'sqrt', 'name': 'n_est_1000'},
    {'n_estimators': 400, 'max_features': 'log2', 'name': 'maxfeat_log2'},
    {'n_estimators': 400, 'max_features': 0.3, 'name': 'maxfeat_0.3'},
    {'n_estimators': 400, 'max_features': 'sqrt', 'min_samples_leaf': 2, 'name': 'msl_2'},
    {'n_estimators': 400, 'max_features': 'sqrt', 'min_samples_leaf': 3, 'name': 'msl_3'},
]

for config in configs:
    print(f"\n--- Top-300 {config['name']} ---")
    
    name = config.pop('name')
    all_predictions = []
    
    for g in range(1, 6):
        test_file = test_files[g-1]
        
        try:
            df = pd.read_csv(test_file)
            df_proc = preprocess(df)
            
            preds = get_extratrees_scores(df_proc, **config)
            preds = preds.sort_values('Score', ascending=False).head(300)
            
            out_csv = f'predictions_network{g}.csv'
            preds.to_csv(out_csv, index=False)
            all_predictions.append(len(preds))
            
            print(f"  Network {g}: {len(preds)} predictions")
            
        except Exception as e:
            print(f"  Network {g}: ERROR - {e}")
            all_predictions.append(0)
    
    # Créer ZIP
    zip_path = f'prediction_extratrees_top300_{name}.zip'
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for g in range(1, 6):
            csv_file = f'predictions_network{g}.csv'
            if os.path.exists(csv_file):
                zf.write(csv_file, arcname=os.path.basename(csv_file))
    
    total = sum(all_predictions)
    print(f"  ✓ Created {zip_path} ({total} total predictions)")

print("\n" + "="*70)
print("RÉSUMÉ - ZIPs Générés")
print("="*70)

zips = sorted([f for f in os.listdir('.') if f.startswith('prediction_extratrees_top') and 'n_est' not in f and 'maxfeat' not in f and 'msl' not in f])
print("\nStratégies d'augmentation K (Top-250, 300, 400, 500):")
for z in zips[-4:] if len(zips) >= 4 else zips:
    size = os.path.getsize(z) / 1024
    print(f"  ✓ {z:45s} ({size:5.1f} KB)")

print("\nStratégies d'optimisation hyperparamètres (Top-300):")
hyperparam_zips = sorted([f for f in os.listdir('.') if 'top300_' in f])
for z in hyperparam_zips:
    size = os.path.getsize(z) / 1024
    print(f"  ✓ {z:45s} ({size:5.1f} KB)")

print("\n" + "="*70)
print("PRIORITÉ DE TEST")
print("="*70)
print("""
PHASE 1 (Augmentation K):
  1. prediction_extratrees_top250.zip  (0.21 → 0.22-0.25?)
  2. prediction_extratrees_top300.zip  (0.21 → 0.23-0.26?)
  3. prediction_extratrees_top400.zip  (0.21 → 0.22-0.25?)
  
PHASE 2 (Si Phase 1 ≤ 0.25, tester hyperparamètres):
  5. prediction_extratrees_top300_n_est_600.zip
  6. prediction_extratrees_top300_n_est_1000.zip
  7. prediction_extratrees_top300_maxfeat_log2.zip
  8. prediction_extratrees_top300_maxfeat_0.3.zip

ACTION: Soumettre Top-300 en priorité!
""")

print("Done!")
