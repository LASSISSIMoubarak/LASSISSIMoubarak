"""
STRATÉGIE ULTRA-OPTIMISÉE: CONSENSUS PONDÉRÉ INTELLIGENT

Combine les forces de chaque approche:
- Correlation pour stabilité
- Mutual Info pour patterns cachés  
- ExtraTrees pour patterns complexes

Avec pondération adaptée par confiance de chaque stratégie
"""
import pandas as pd
import numpy as np
import os
import zipfile
from sklearn.preprocessing import StandardScaler, MinMaxScaler
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

def normalize_scores(scores_array, method='minmax'):
    """Normalize scores to [0, 1]"""
    if len(scores_array) == 0:
        return scores_array
    if method == 'minmax':
        min_val = np.min(scores_array)
        max_val = np.max(scores_array)
        if max_val - min_val < 1e-9:
            return np.ones_like(scores_array) * 0.5
        return (scores_array - min_val) / (max_val - min_val)
    else:  # sigmoid
        return 1 / (1 + np.exp(-scores_array))

def get_correlation_scores(df):
    """Correlation simple"""
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
    return pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score']) if rows else pd.DataFrame(columns=['Cause', 'Effect', 'Score'])

def get_mutual_info_scores(df):
    """Mutual Information"""
    rows = []
    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values
        try:
            mi = mutual_info_regression(X, y, random_state=42, n_neighbors=3)
            for col, score in zip(X.columns, mi):
                if score > 1e-6:
                    rows.append((col, target, float(score)))
        except:
            pass
    return pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score']) if rows else pd.DataFrame(columns=['Cause', 'Effect', 'Score'])

def get_extratrees_scores(df):
    """ExtraTrees"""
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
        except:
            pass
    return pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score']) if rows else pd.DataFrame(columns=['Cause', 'Effect', 'Score'])

def get_consensus_optimized(df):
    """
    ULTRA-OPTIMISÉ: Consensus intelligent pondéré
    
    Logique:
    1. Corrélation = base stable (poids 0.35)
    2. Mutual Info = capture patterns cachés (poids 0.35)
    3. ExtraTrees = patterns complexes (poids 0.30)
    
    Astuce: Garder seulement edges votés par ≥2 stratégies
    (réduit faux positifs tout en gardant patterns forts)
    """
    
    # Récupérer scores
    corr = get_correlation_scores(df)
    mi = get_mutual_info_scores(df)
    et = get_extratrees_scores(df)
    
    if len(corr) == 0 and len(mi) == 0 and len(et) == 0:
        return pd.DataFrame(columns=['Cause', 'Effect', 'Score'])
    
    # Créer dictionnaires {(cause, effect): score}
    scores = {}
    votes = {}
    
    for _, row in corr.iterrows():
        key = (row['Cause'], row['Effect'])
        scores[key] = scores.get(key, 0) + 0.35 * normalize_scores(corr['Score'].values)[list(corr.index).index(_)]
        votes[key] = votes.get(key, 0) + 1
    
    for _, row in mi.iterrows():
        key = (row['Cause'], row['Effect'])
        norm_mi = normalize_scores(mi['Score'].values)
        scores[key] = scores.get(key, 0) + 0.35 * norm_mi[list(mi.index).index(_)]
        votes[key] = votes.get(key, 0) + 1
    
    for _, row in et.iterrows():
        key = (row['Cause'], row['Effect'])
        norm_et = normalize_scores(et['Score'].values)
        scores[key] = scores.get(key, 0) + 0.30 * norm_et[list(et.index).index(_)]
        votes[key] = votes.get(key, 0) + 1
    
    # Filtrer: garder seulement edges avec ≥2 votes (consensus)
    consensus_edges = []
    for (cause, effect), score in scores.items():
        if votes[(cause, effect)] >= 2:  # Consensus
            consensus_edges.append((cause, effect, score / votes[(cause, effect)]))
    
    result = pd.DataFrame(consensus_edges, columns=['Cause', 'Effect', 'Score'])
    return result if len(result) > 0 else pd.DataFrame(columns=['Cause', 'Effect', 'Score'])

def get_consensus_majority(df):
    """
    Alternative: Majority Vote (2+ approches votent pour l'edge)
    """
    corr = get_correlation_scores(df)
    mi = get_mutual_info_scores(df)
    et = get_extratrees_scores(df)
    
    corr_edges = set(zip(corr['Cause'], corr['Effect']))
    mi_edges = set(zip(mi['Cause'], mi['Effect']))
    et_edges = set(zip(et['Cause'], et['Effect']))
    
    # Edges votés par ≥2 stratégies
    all_edges = list(corr_edges | mi_edges | et_edges)
    consensus = []
    
    for edge in all_edges:
        votes = 0
        scores = []
        
        if edge in corr_edges:
            votes += 1
            score = corr[(corr['Cause'] == edge[0]) & (corr['Effect'] == edge[1])]['Score'].values
            if len(score) > 0:
                scores.append(float(score[0]))
        
        if edge in mi_edges:
            votes += 1
            score = mi[(mi['Cause'] == edge[0]) & (mi['Effect'] == edge[1])]['Score'].values
            if len(score) > 0:
                scores.append(float(score[0]))
        
        if edge in et_edges:
            votes += 1
            score = et[(et['Cause'] == edge[0]) & (et['Effect'] == edge[1])]['Score'].values
            if len(score) > 0:
                scores.append(float(score[0]))
        
        if votes >= 2:  # Garder seulement consensus
            avg_score = np.mean(scores) if scores else 0
            consensus.append((edge[0], edge[1], avg_score, votes))
    
    result = pd.DataFrame(consensus, columns=['Cause', 'Effect', 'Score', 'Votes'])
    result = result.drop('Votes', axis=1)
    return result if len(result) > 0 else pd.DataFrame(columns=['Cause', 'Effect', 'Score'])

# ============================================================
# GÉNÉRER STRATÉGIES ULTRA-OPTIMISÉES
# ============================================================

print("="*70)
print("STRATÉGIES ULTRA-OPTIMISÉES: CONSENSUS INTELLIGENT")
print("="*70)

strategies = {
    'consensus_optimized': ('Consensus Pondéré', get_consensus_optimized),
    'consensus_majority': ('Majority Vote (≥2)', get_consensus_majority),
}

test_files = [f'test_data/data{i}.csv' for i in range(1, 6)]

for strategy_key, (strategy_name, strategy_func) in strategies.items():
    print(f"\n{'='*70}")
    print(f"STRATÉGIE: {strategy_name}")
    print(f"{'='*70}")
    
    for top_k in [50, 75, 100]:
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

print("\n" + "="*70)
print("RÉSUMÉ FINAL")
print("="*70)
print("""
✓ NOUVELLES STRATÉGIES (Ultra-Optimisées):
  - prediction_consensus_optimized_top50.zip   ← TESTE CELUI-CI!
  - prediction_consensus_optimized_top75.zip   (couverture intermédiaire)
  - prediction_consensus_optimized_top100.zip  (couverture maximale)
  
  - prediction_consensus_majority_top50.zip    (alternative)
  - prediction_consensus_majority_top75.zip
  - prediction_consensus_majority_top100.zip

LOGIQUE du Consensus:
✓ Garder seulement edges votés par ≥2 stratégies
✓ Éliminer les prédictions d'une seule approche
✓ Réduire faux positifs tout en gardant patterns forts
✓ Résultat: Très conservateur et très robuste

ESPÉRANCE: 0.21 → 0.28-0.35

ACTION: Tester prediction_consensus_optimized_top50.zip en priorité!
""")

print("Done!")
