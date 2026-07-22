import pandas as pd
import os

os.chdir(r'c:/Users/lassi/projet/Inference reseau')

print('=== BENCHMARK ===')
for g in range(1,6):
    df = pd.read_csv(f'starting_kit_2_extracted/predictions_network{g}.csv')
    print(f'graph {g}: {len(df)} rows, score range {df["Score"].min():.4f} -> {df["Score"].max():.4f}')

print()
print('=== MY PREDICTIONS ===')
for g in range(1,6):
    df = pd.read_csv(f'predictions_network{g}.csv')
    print(f'graph {g}: {len(df)} rows, score range {df["Score"].min():.4f} -> {df["Score"].max():.4f}')

print()
print('=== LOCAL EVALUATION (BENCHMARK) ===')
from sklearn.metrics import average_precision_score

for g in range(1,6):
    pred = pd.read_csv(f'starting_kit_2_extracted/predictions_network{g}.csv')
    target = pd.read_csv(f'data_train/target{g}.csv')
    true = {(r.Cause, r.Effect) for _,r in target.iterrows()}
    y_true = [1 if (r.Cause,r.Effect) in true else 0 for _,r in pred.iterrows()]
    y_score = [float(r.Score) for _,r in pred.iterrows()]
    ap = average_precision_score(y_true, y_score)
    print(f'graph {g}: AP={ap:.4f}')

print()
print('=== LOCAL EVALUATION (MY PREDICTIONS) ===')
for g in range(1,6):
    pred = pd.read_csv(f'predictions_network{g}.csv')
    target = pd.read_csv(f'data_train/target{g}.csv')
    true = {(r.Cause, r.Effect) for _,r in target.iterrows()}
    y_true = [1 if (r.Cause,r.Effect) in true else 0 for _,r in pred.iterrows()]
    y_score = [float(r.Score) for _,r in pred.iterrows()]
    ap = average_precision_score(y_true, y_score)
    print(f'graph {g}: AP={ap:.4f}')
