import os, pandas as pd, numpy as np
from sklearn import metrics
os.chdir(r'c:/Users/lassi/projet/Inference reseau')

def compute_ap(pred_path, target_path):
    pred = pd.read_csv(pred_path)
    target = pd.read_csv(target_path)
    true_edges = {(r.Cause, r.Effect) for _, r in target.iterrows()}
    graph_id = int(''.join(ch for ch in os.path.basename(pred_path) if ch.isdigit()))
    var_names = list(pd.read_csv(f'data_train/data{graph_id}.csv').columns)
    rows = []
    for _, row in pred.iterrows():
        if row['Cause'] in var_names and row['Effect'] in var_names:
            rows.append((row['Cause'], row['Effect'], abs(float(row['Score']))))
    pred_df = pd.DataFrame(rows, columns=['Cause','Effect','Score'])
    if pred_df.empty:
        return 0.0
    y_true = [1 if (r.Cause, r.Effect) in true_edges else 0 for _, r in pred_df.iterrows()]
    if len(set(y_true)) < 2:
        return 0.0
    y_scores = pred_df['Score'].to_numpy()
    return metrics.average_precision_score(y_true, y_scores)

for g in range(1,6):
    ap = compute_ap(f'predictions_network{g}.csv', f'data_train/target{g}.csv')
    print(g, ap)
