import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.feature_selection import mutual_info_regression
from scipy.stats import spearmanr, pearsonr
import warnings
warnings.filterwarnings('ignore')

# CHARGE LES DONNÉES
df_raw = pd.read_csv('data_train/data1.csv')
target_true = pd.read_csv('data_train/target1.csv')
true_edges = {(r.Cause, r.Effect) for _, r in target_true.iterrows()}

print("="*60)
print("DIAGNOSTIC: Pourquoi 0.08 partout?")
print("="*60)

# 1. Vérifier les données brutes
print("\n1. DONNÉES BRUTES:")
print(f"  Shape: {df_raw.shape}")
print(f"  Missing: {df_raw.isnull().sum().sum()}")
print(f"  True edges: {len(true_edges)}")
print(f"  Variables: {list(df_raw.columns[:5])}...")

# 2. Différentes stratégies
def strategy_correlation(df_raw):
    """Correlation simple (pas d'imputation)"""
    rows = []
    corr = df_raw.corr().abs()
    for i in corr.columns:
        for j in corr.columns:
            if i != j:
                rows.append((i, j, float(corr.loc[i, j])))
    pred = pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
    pred = pred.sort_values('Score', ascending=False).head(50)
    return pred

def strategy_spearman(df_raw):
    """Spearman correlation (robust to missing)"""
    rows = []
    for i in range(len(df_raw.columns)):
        for j in range(len(df_raw.columns)):
            if i != j:
                col_i = df_raw.iloc[:, i].dropna()
                col_j = df_raw.iloc[:, j].dropna()
                if len(col_i) > 0 and len(col_j) > 0:
                    # align both series
                    mask = df_raw.iloc[:, i].notna() & df_raw.iloc[:, j].notna()
                    if mask.sum() > 3:
                        coef, _ = spearmanr(df_raw.iloc[mask, i], df_raw.iloc[mask, j])
                        rows.append((df_raw.columns[i], df_raw.columns[j], abs(float(coef)) if not np.isnan(coef) else 0.0))
    pred = pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
    pred = pred.sort_values('Score', ascending=False).head(50)
    return pred

def strategy_mi(df_proc):
    """Information mutuelle (ne dépend pas de régression)"""
    rows = []
    for target in df_proc.columns:
        X_df = df_proc.drop(columns=[target])
        X = X_df.values
        y = df_proc[target].values
        mi = mutual_info_regression(X, y, random_state=0)
        for feat_name, score in zip(X_df.columns, mi):
            if score > 0:
                rows.append((feat_name, target, float(score)))
    pred = pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
    pred = pred.sort_values('Score', ascending=False).head(50)
    return pred

# Test stratégies
print("\n2. RÉSULTATS STRATÉGIES GRAPH 1:")

# Corrélation Pearson brute
print("\n  A) Corrélation Pearson (données brutes):")
pred_corr = strategy_correlation(df_raw)
pred_corr.to_csv('test_correlation.csv', index=False)
tp_corr = len(set(zip(pred_corr['Cause'], pred_corr['Effect'])) & true_edges)
print(f"     Top hits: {tp_corr}/50, Examples: {pred_corr.head(3)[['Cause', 'Effect', 'Score']].to_dict('records')}")

# Spearman (robuste aux NaN)
print("\n  B) Corrélation Spearman (robuste NaN):")
try:
    pred_spear = strategy_spearman(df_raw)
    pred_spear.to_csv('test_spearman.csv', index=False)
    tp_spear = len(set(zip(pred_spear['Cause'], pred_spear['Effect'])) & true_edges)
    print(f"     Top hits: {tp_spear}/50, Examples: {pred_spear.head(3)[['Cause', 'Effect', 'Score']].to_dict('records')}")
except Exception as e:
    print(f"     ERROR: {e}")

# Information mutuelle
print("\n  C) Information Mutuelle (imputation + MI):")
df_proc = pd.DataFrame(
    StandardScaler().fit_transform(SimpleImputer(strategy='median').fit_transform(df_raw)),
    columns=df_raw.columns
)
try:
    pred_mi = strategy_mi(df_proc)
    pred_mi.to_csv('test_mi.csv', index=False)
    tp_mi = len(set(zip(pred_mi['Cause'], pred_mi['Effect'])) & true_edges)
    print(f"     Top hits: {tp_mi}/50, Examples: {pred_mi.head(3)[['Cause', 'Effect', 'Score']].to_dict('records')}")
except Exception as e:
    print(f"     ERROR: {e}")

# ExtraTrees (notre approche)
print("\n  D) ExtraTrees (notre approche):")
rows = []
for target in df_proc.columns:
    X_df = df_proc.drop(columns=[target])
    X = X_df.values
    y = df_proc[target].values
    model = ExtraTreesRegressor(n_estimators=200, max_features='sqrt', random_state=0, n_jobs=-1)
    model.fit(X, y)
    importances = np.abs(model.feature_importances_)
    importances = importances / (importances.sum() + 1e-12)
    for feat_name, score in zip(X_df.columns, importances):
        if score > 0:
            rows.append((feat_name, target, float(score)))
pred_et = pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
pred_et = pred_et.sort_values('Score', ascending=False).head(50)
tp_et = len(set(zip(pred_et['Cause'], pred_et['Effect'])) & true_edges)
print(f"     Top hits: {tp_et}/50, Examples: {pred_et.head(3)[['Cause', 'Effect', 'Score']].to_dict('records')}")

print("\n" + "="*60)
print("RÉSUMÉ")
print("="*60)
print("Si corrélation/MI aussi mauvais que ExtraTrees,")
print("le problème est dans les DONNÉES ou la MÉTRIQUE du site.")
print("\nProblèmes possibles:")
print("1. Site a des graphes DIFFÉRENTS de data_train/")
print("2. Site utilise une MÉTRIQUE DIFFÉRENTE (pas AP)")
print("3. CSV ne correspondant pas au format attendu")
print("4. Prétraitement des données NaN différent")
