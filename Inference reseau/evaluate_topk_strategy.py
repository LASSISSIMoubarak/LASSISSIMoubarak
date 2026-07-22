import os
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

ROOT = r"c:/Users/lassi/projet/Inference reseau"
os.chdir(ROOT)


def ap_for_k(pred_df, true_edges, k):
    p = pred_df.head(k)
    y_true = [1 if (r.Cause, r.Effect) in true_edges else 0 for _, r in p.iterrows()]
    y_score = [float(r.Score) for _, r in p.iterrows()]
    if len(set(y_true)) < 2:
        return 0.0
    return float(average_precision_score(y_true, y_score))


grid = [4, 8, 12, 20, 30, 50, 80, 120, 200, 400, 800, 1500, 3000]
results = []

for k in grid:
    aps = []
    for g in range(1, 6):
        pred = pd.read_csv(f"predictions_network{g}.csv").sort_values(["Score", "Cause", "Effect"], ascending=[False, True, True]).reset_index(drop=True)
        target = pd.read_csv(f"data_train/target{g}.csv")
        true_edges = {(r.Cause, r.Effect) for _, r in target.iterrows()}
        kk = min(k, len(pred))
        aps.append(ap_for_k(pred, true_edges, kk))
    results.append((k, float(np.mean(aps)), [float(x) for x in aps]))

for k, mean_ap, aps in results:
    print(f"k={k:4d} mean_ap={mean_ap:.4f} per_graph={[round(x,4) for x in aps]}")

best = max(results, key=lambda x: x[1])
print("BEST", best[0], round(best[1], 4))
