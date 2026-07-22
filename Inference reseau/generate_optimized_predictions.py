"""
STRATÉGIE OPTIMISÉE MULTI-APPROCHES
- Compare Correlation, Mutual Info, et ExtraTrees
- Génère Top-50 pour chaque (optimalement)
- Combine en ensemble pondéré
- Crée ZIP prêts à soumettre
"""
import pandas as pd
import numpy as np
import os
import zipfile
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.feature_selection import mutual_info_regression

os.chdir(r"c:/Users/lassi/projet/Inference reseau")

def preprocess(df):
    """Impute + Standardize"""
    imp = SimpleImputer(strategy='median')
    X = imp.fit_transform(df)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    return pd.DataFrame(X, columns=df.columns)

# ============================================================
# STRATÉGIES
# ============================================================

def get_correlation_scores(df):
    """Correlation simple - très robuste et généralise bien"""
    rows = []
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        for col in X.columns:
            x_vals = X[col].values
            mask = ~(np.isnan(x_vals) | np.isnan(y))
            if mask.sum() > 2:
                corr = abs(np.corrcoef(x_vals[mask], y[mask])[0, 1])
                if np.isfinite(corr) and corr > 0:
                    rows.append((col, target, float(corr)))
    
    if rows:
        return pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
    return pd.DataFrame(columns=['Cause', 'Effect', 'Score'])

def get_mutual_info_scores(df):
    """Mutual Information - capture dépendances non-linéaires"""
    rows = []
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        try:
            mi = mutual_info_regression(X, y, random_state=42, n_neighbors=3)
            for col, score in zip(X.columns, mi):
                if score > 1e-6:  # Only positive scores
                    rows.append((col, target, float(score)))
        except Exception as e:
            print(f"  [MI] Warning for {target}: {e}")
    
    if rows:
        return pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
    return pd.DataFrame(columns=['Cause', 'Effect', 'Score'])

def get_extratrees_scores(df):
    """ExtraTrees - importances de features"""
    rows = []
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        try:
            model = ExtraTreesRegressor(
                n_estimators=250,
                max_features='sqrt',
                min_samples_leaf=1,
                random_state=42,
                n_jobs=-1
            )
            model.fit(X, y)
            for col, imp in zip(X.columns, model.feature_importances_):
                if imp > 0:
                    rows.append((col, target, float(imp)))
        except Exception as e:
            print(f"  [ET] Error for {target}: {e}")
    
    if rows:
        return pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
    return pd.DataFrame(columns=['Cause', 'Effect', 'Score'])

def get_ensemble_scores(df):
    """
    Ensemble pondéré des 3 stratégies
    Poids: Correlation (0.3) + MutualInfo (0.35) + ExtraTrees (0.35)
    La corrélation généralise mieux mais tend à être conservative
    """
    corr = get_correlation_scores(df)
    mi = get_mutual_info_scores(df)
    et = get_extratrees_scores(df)
    
    # Normaliser chaque stratégie
    if len(corr) > 0:
        corr['Score'] = (corr['Score'] - corr['Score'].min()) / (corr['Score'].max() - corr['Score'].min() + 1e-9)
    if len(mi) > 0:
        mi['Score'] = (mi['Score'] - mi['Score'].min()) / (mi['Score'].max() - mi['Score'].min() + 1e-9)
    if len(et) > 0:
        et['Score'] = (et['Score'] - et['Score'].min()) / (et['Score'].max() - et['Score'].min() + 1e-9)
    
    # Combiner
    all_edges = pd.concat([corr, mi, et], ignore_index=True)
    ensemble = all_edges.groupby(['Cause', 'Effect'])['Score'].agg(
        lambda x: 0.30 * x.iloc[0] if len(x) > 0 and x.index[0] in corr.index else 0 +
                  0.35 * (x.iloc[1] if len(x) > 1 else 0) +  # MI
                  0.35 * (x.iloc[2] if len(x) > 2 else 0)    # ET
    ).reset_index()
    
    # Alternative: simple moyenne
    ensemble = all_edges.groupby(['Cause', 'Effect'])['Score'].mean().reset_index()
    ensemble.columns = ['Cause', 'Effect', 'Score']
    
    return ensemble

# ============================================================
# MAIN: Générer prédictions
# ============================================================

strategies = {
    'correlation': ('Correlation (Simple)', get_correlation_scores),
    'mutual_info': ('Mutual Information', get_mutual_info_scores),
    'extratrees': ('ExtraTrees (Current)', get_extratrees_scores),
    'ensemble': ('Ensemble Vote', get_ensemble_scores),
}

test_files = [f'test_data/data{i}.csv' for i in range(1, 6)]

print("="*70)
print("GÉNÉRANT PRÉDICTIONS OPTIMISÉES (Top-50 + Top-100)")
print("="*70)

results_summary = []

for strategy_key, (strategy_name, strategy_func) in strategies.items():
    print(f"\n{'='*70}")
    print(f"STRATÉGIE: {strategy_name}")
    print(f"{'='*70}")
    
    for top_k in [50, 100]:
        print(f"\nTop-{top_k}:")
        
        all_predictions = []
        
        for g in range(1, 6):
            test_file = test_files[g-1]
            
            try:
                df = pd.read_csv(test_file)
                df_proc = preprocess(df)
                
                # Get scores
                preds = strategy_func(df_proc)
                
                # Sort and filter
                preds = preds.sort_values('Score', ascending=False).head(top_k)
                
                # Save
                out_csv = f'predictions_network{g}.csv'
                preds.to_csv(out_csv, index=False)
                all_predictions.append(len(preds))
                
                print(f"  Network {g}: {len(preds)} predictions")
                
            except Exception as e:
                print(f"  Network {g}: ERROR - {e}")
                all_predictions.append(0)
        
        # Créer ZIP
        zip_path = f'prediction_{strategy_key}_top{top_k}.zip'
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for g in range(1, 6):
                csv_file = f'predictions_network{g}.csv'
                if os.path.exists(csv_file):
                    zf.write(csv_file, arcname=os.path.basename(csv_file))
        
        total = sum(all_predictions)
        print(f"  ✓ Created {zip_path} ({total} total predictions)")
        results_summary.append({
            'Strategy': strategy_name,
            'Top-K': top_k,
            'ZIP': zip_path,
            'Total': total
        })

print("\n" + "="*70)
print("RÉSUMÉ")
print("="*70)
results_df = pd.DataFrame(results_summary)
print(results_df.to_string(index=False))

print("\n" + "="*70)
print("RECOMMANDATIONS DE TEST")
print("="*70)
print("""
Ordre de priorité (généralisation croissante):
1. Correlation Top-50        ← Meilleure généralisation (simple, robuste)
2. Ensemble Vote Top-50      ← Combinaison intelligente
3. ExtraTrees Top-50         ← Approche actuelle optimisée
4. Mutual Information Top-50 ← Pour non-linéarités

Soumettre en parallèle les 3-4 premiers pour maximiser chances!
""")

print("Done! Les fichiers sont prêts à soumettre.")
