import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor

# Charger données
df_raw = pd.read_csv('data_train/data1.csv')
target_true = pd.read_csv('data_train/target1.csv')
true_edges = {(r.Cause, r.Effect) for _, r in target_true.iterrows()}

def compute_pr_curve(pred_df, true_edges, var_names):
    """Calcule la Precision-Recall curve"""
    pred_set = {(r.Cause, r.Effect) for _, r in pred_df.iterrows()}
    tp = len(pred_set & true_edges)
    fp = len(pred_set - true_edges)
    fn = len(true_edges - pred_set)
    
    if tp + fp > 0:
        precision = tp / (tp + fp)
    else:
        precision = 0.0
    
    if tp + fn > 0:
        recall = tp / (tp + fn)
    else:
        recall = 0.0
    
    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0
    
    # AP approximation: moyenne de precision aux rappels
    ap = (precision * recall) if (tp + fn) > 0 else 0
    return recall, precision, ap

def test_imputation_strategy(df_raw, strategy_name, **kwargs):
    """Test une stratégie d'imputation donnée"""
    df_clean = df_raw.copy()
    
    if strategy_name == "median":
        imputer = SimpleImputer(strategy='median')
        X_imp = imputer.fit_transform(df_clean.values)
    elif strategy_name == "zero":
        X_imp = df_clean.fillna(0).values
    elif strategy_name == "mean":
        imputer = SimpleImputer(strategy='mean')
        X_imp = imputer.fit_transform(df_clean.values)
    elif strategy_name == "drop_rows":
        df_clean = df_clean.dropna()
        X_imp = df_clean.values
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X_imp)
    df_proc = pd.DataFrame(Xs, columns=df_clean.columns)
    
    # Entraîner ExtraTrees
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
    
    pred = pd.DataFrame(rows, columns=['Cause', 'Effect', 'Score'])
    pred = pred.sort_values('Score', ascending=False).head(300)
    
    var_names = df_proc.columns.tolist()
    _, _, ap = compute_pr_curve(pred, true_edges, var_names)
    
    return ap, len(pred)

print("Testing different imputation strategies on Graph 1:")
print("=" * 60)

strategies = ["median", "mean", "zero", "drop_rows"]
results = {}

for strat in strategies:
    try:
        ap, n_pred = test_imputation_strategy(df_raw, strat)
        results[strat] = ap
        print(f"{strat:15} -> AP = {ap:.4f} ({n_pred} predictions)")
    except Exception as e:
        print(f"{strat:15} -> ERROR: {e}")

print("\n" + "=" * 60)
best_strat = max(results, key=results.get)
print(f"Best strategy: {best_strat} (AP={results[best_strat]:.4f})")
print(f"Local (median): AP=0.3139 (from Q18)")
print(f"Site score:    AP=0.0239 (Network 1)")
