"""
CORRECT SOLUTION: Train on data_train/ and apply to test_data/
"""
import pandas as pd
import numpy as np
import os
import zipfile
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor

print("="*70)
print("CORRECT APPROACH: Train on TRAINING data, apply to TEST data")
print("="*70)

def load_data(filepath):
    """Load data from CSV"""
    return pd.read_csv(filepath)

def impute_and_scale(df):
    """Impute missing values then standardize"""
    df_clean = df.copy()
    imputer = SimpleImputer(strategy='median')
    X_imp = imputer.fit_transform(df_clean.values)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X_imp)
    return pd.DataFrame(Xs, columns=df.columns, index=df.index)

# ============================================================
# STEP 1: TRAIN on data_train/
# ============================================================
print("\n" + "="*70)
print("STEP 1: TRAINING MODELS ON data_train/")
print("="*70)

trained_models = {}

for g in range(1, 6):
    print(f"\nGraphe {g}: Training...")
    
    # Load training data
    train_file = f'data_train/data{g}.csv'
    df_train = load_data(train_file)
    df_train_proc = impute_and_scale(df_train)
    
    trained_models[g] = {}
    
    # Train one model per target variable
    for target in df_train_proc.columns:
        X_df = df_train_proc.drop(columns=[target])
        X = X_df.values
        y = df_train_proc[target].values
        
        # Train ExtraTrees
        model = ExtraTreesRegressor(
            n_estimators=400,
            max_features='sqrt',
            random_state=0,
            n_jobs=-1
        )
        model.fit(X, y)
        
        # Store model and column names
        trained_models[g][target] = {
            'model': model,
            'features': X_df.columns.tolist(),
            'importances': np.abs(model.feature_importances_)
        }
    
    print(f"  ✓ Trained {len(df_train_proc.columns)} models for Graph {g}")

# ============================================================
# STEP 2: APPLY to test_data/ and generate predictions
# ============================================================
print("\n" + "="*70)
print("STEP 2: GENERATING PREDICTIONS ON test_data/")
print("="*70)

final_predictions = []

for g in range(1, 6):
    print(f"\nGraphe {g}: Generating predictions...")
    
    # Load test data
    test_file = f'test_data/data{g}.csv'
    df_test = load_data(test_file)
    df_test_proc = impute_and_scale(df_test)
    
    # For each target, extract feature importances from TRAINED models
    rows = []
    for target in df_test_proc.columns:
        if target not in trained_models[g]:
            print(f"  WARNING: Target {target} not in trained models")
            continue
        
        trained_info = trained_models[g][target]
        importances = trained_info['importances']
        features = trained_info['features']
        
        # Normalize importances
        imp_sum = importances.sum()
        if imp_sum > 0:
            importances_norm = importances / imp_sum
        else:
            importances_norm = importances
        
        # Add to predictions
        for feat_name, score in zip(features, importances_norm):
            if score > 0:
                rows.append((feat_name, target, float(score)))
    
    # Create prediction dataframe
    pred = pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
    pred = pred.sort_values('Score', ascending=False).head(50)  # Top-50
    
    # Save to CSV
    out_csv = f'predictions_network{g}.csv'
    pred.to_csv(out_csv, index=False)
    
    final_predictions.append({
        'Graph': g,
        'N_predictions': len(pred),
        'Top_score': pred['Score'].iloc[0] if len(pred) > 0 else 0
    })
    
    print(f"  ✓ Saved {len(pred)} predictions to {out_csv}")
    print(f"    Top 3: {pred.head(3)[['Cause', 'Effect', 'Score']].to_dict('records')}")

# ============================================================
# STEP 3: Create submission ZIP
# ============================================================
print("\n" + "="*70)
print("STEP 3: CREATING SUBMISSION ZIP")
print("="*70)

zip_path = 'prediction.zip'
with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    for g in range(1, 6):
        csv_file = f'predictions_network{g}.csv'
        if os.path.exists(csv_file):
            zf.write(csv_file, arcname=os.path.basename(csv_file))
            print(f"  ✓ Added {csv_file}")

print(f"\n✓ FINAL SUBMISSION: {zip_path}")
print(f"\nSummary:")
for item in final_predictions:
    print(f"  Network {item['Graph']}: {item['N_predictions']} predictions (top score: {item['Top_score']:.4f})")

print("\n" + "="*70)
print("KEY DIFFERENCE FROM BEFORE:")
print("="*70)
print("BEFORE (WRONG):")
print("  - Train on data_train/data1.csv")
print("  - Evaluate on data_train/data1.csv  ← SAME DATA = OVERFITTING")
print("  - Generate predictions on data_train/data1.csv")
print("")
print("NOW (CORRECT):")
print("  - Train on data_train/data1.csv")
print("  - Apply to test_data/data1.csv  ← DIFFERENT DATA = REAL TEST")
print("  - Generate predictions on test_data/data1.csv")
print("="*70)
