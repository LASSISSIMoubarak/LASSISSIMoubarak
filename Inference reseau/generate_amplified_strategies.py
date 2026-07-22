"""
AMPLIFICATION DE LA STRATÉGIE GAGNANTE
Générer Top-350, 380, 320 avec les meilleurs hyperparamètres
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
print("AMPLIFICATION: Top-K + Meilleur max_features")
print("="*70)

test_files = [f'test_data/data{i}.csv' for i in range(1, 6)]

# Stratégies amplifiées
strategies = [
    # Top-K variations avec max_features optimisé
    (320, 'log2', 'top320_maxfeat_log2'),
    (350, 'log2', 'top350_maxfeat_log2'),
    (380, 'log2', 'top380_maxfeat_log2'),
    (320, 0.3, 'top320_maxfeat_0.3'),
    (350, 0.3, 'top350_maxfeat_0.3'),
    (380, 0.3, 'top380_maxfeat_0.3'),
    
    # Combinaisons: Top-300 + meilleur maxfeat + autres paramètres
    (300, 'log2', 'top300_maxfeat_log2_nest_800', {'n_estimators': 800}),
    (300, 'log2', 'top300_maxfeat_log2_msl_2', {'min_samples_leaf': 2}),
    (300, 0.3, 'top300_maxfeat_0.3_nest_800', {'n_estimators': 800}),
    (300, 0.3, 'top300_maxfeat_0.3_msl_2', {'min_samples_leaf': 2}),
]

for strat in strategies:
    if len(strat) == 3:
        top_k, max_feat, name = strat
        extra_params = {}
    else:
        top_k, max_feat, name, extra_params = strat
    
    print(f"\n--- {name} ---")
    
    all_predictions = []
    
    for g in range(1, 6):
        test_file = test_files[g-1]
        
        try:
            df = pd.read_csv(test_file)
            df_proc = preprocess(df)
            
            preds = get_extratrees_scores(df_proc, max_features=max_feat, **extra_params)
            preds = preds.sort_values('Score', ascending=False).head(top_k)
            
            out_csv = f'predictions_network{g}.csv'
            preds.to_csv(out_csv, index=False)
            all_predictions.append(len(preds))
            
            print(f"  Network {g}: {len(preds)} predictions")
            
        except Exception as e:
            print(f"  Network {g}: ERROR - {e}")
            all_predictions.append(0)
    
    # Créer ZIP
    zip_path = f'prediction_extratrees_{name}.zip'
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for g in range(1, 6):
            csv_file = f'predictions_network{g}.csv'
            if os.path.exists(csv_file):
                zf.write(csv_file, arcname=os.path.basename(csv_file))
    
    total = sum(all_predictions)
    print(f"  ✓ Created {zip_path} ({total} total predictions)")

print("\n" + "="*70)
print("RÉSUMÉ - PROCHAINES STRATÉGIES")
print("="*70)

print("""
TESTER (Prochaines Soumissions):
═════════════════════════════════════════════════════════════════

Tier 1 (PRIORITÉ) - Amplifier le variant gagnant (0.25):
  1. prediction_extratrees_top350_maxfeat_log2.zip   (Espoir: 0.25-0.28)
  2. prediction_extratrees_top380_maxfeat_log2.zip   (Espoir: 0.24-0.27)
  3. prediction_extratrees_top320_maxfeat_log2.zip   (Espoir: 0.24-0.26)

Tier 2 - Variante alternative (0.3):
  4. prediction_extratrees_top350_maxfeat_0.3.zip    (Espoir: 0.24-0.27)
  5. prediction_extratrees_top380_maxfeat_0.3.zip    (Espoir: 0.23-0.26)

Tier 3 - Combinaisons gagnantes (Top-300 + meilleur):
  6. prediction_extratrees_top300_maxfeat_log2_nest_800.zip
  7. prediction_extratrees_top300_maxfeat_log2_msl_2.zip

SCORE ACTUEL: 0.25 (meilleur)
OBJECTIF: 0.26-0.30 (amélioration progressive)

ACTION: Commencer par Tier 1!
""")

# Compter ZIPs générés
new_zips = [f for f in os.listdir('.') if 'top32' in f or 'top35' in f or 'top38' in f]
print(f"\n✓ {len(new_zips)} nouveaux ZIPs générés pour test")

print("\nDone!")
