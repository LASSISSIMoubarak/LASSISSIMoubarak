"""
CORRECTED: Train and apply on the SAME TEST data
Since train and test have completely different variables,
we must train the models directly on test_data/
"""
import pandas as pd
import numpy as np
import os
import zipfile
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor

print("="*70)
print("CORRECTED APPROACH: Train and apply on TEST data")
print("(Because train/test have different variables)")
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
# GENERATE PREDICTIONS DIRECTLY ON TEST DATA
# ============================================================
print("\nGenerating predictions on test_data/ (train + test on same data)")
print("="*70)

final_predictions = []

for g in range(1, 6):
    print(f"\nGraphe {g}:")
    
    # Load TEST data
    test_file = f'test_data/data{g}.csv'
    df_test = load_data(test_file)
    print(f"  Shape: {df_test.shape}")
    
    # Process
    df_test_proc = impute_and_scale(df_test)
    
    # Train models on test data and extract importances
    rows = []
    for target in df_test_proc.columns:
        X_df = df_test_proc.drop(columns=[target])
        X = X_df.values
        y = df_test_proc[target].values
        
        # Train ExtraTrees on TEST data
        model = ExtraTreesRegressor(
            n_estimators=400,
            max_features='sqrt',
            random_state=0,
            n_jobs=-1
        )
        model.fit(X, y)
        
        # Extract importances
        importances = np.abs(model.feature_importances_)
        imp_sum = importances.sum()
        if imp_sum > 0:
            importances = importances / imp_sum
        
        # Add to predictions
        for feat_name, score in zip(X_df.columns, importances):
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
    
    print(f"  ✓ Saved {len(pred)} predictions")
    print(f"    Top 3: {pred.head(3)[['Cause', 'Effect', 'Score']].to_dict('records')}")

# ============================================================
# Create submission ZIP
# ============================================================
print("\n" + "="*70)
print("CREATING SUBMISSION ZIP")
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
print("KEY INSIGHT:")
print("="*70)
print("Train and Test data have COMPLETELY DIFFERENT variables:")
print("  - Graph 1: Train V0-V19, Test V0-V99 (only 20% overlap)")
print("  - Graph 3: Train (genes), Test (V0-V19) (0% overlap)")
print("  - Graph 4: Train (genes), Test (V0-V99) (0% overlap)")
print("  - Graph 5: Train (G1-G100), Test (V0-V19) (0% overlap)")
print("\nTherefore: Must train and apply on TEST data only")
print("Cannot transfer models from training to test")
print("="*70)
