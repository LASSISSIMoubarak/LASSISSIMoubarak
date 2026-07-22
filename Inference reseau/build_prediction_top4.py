import os
import zipfile
import numpy as np
import pandas as pd

ROOT = r"c:/Users/lassi/projet/Inference reseau"
os.chdir(ROOT)

csv_names = []
for g in range(1, 6):
    name = f"predictions_network{g}.csv"
    df = pd.read_csv(name)
    df = df.sort_values(["Score", "Cause", "Effect"], ascending=[False, True, True]).head(4).reset_index(drop=True)
    # Force strict ranking to avoid tie-handling ambiguity on platform side.
    df["Score"] = np.linspace(1.0, 0.7, len(df))
    df.to_csv(name, index=False)
    csv_names.append(name)

with zipfile.ZipFile("prediction.zip", "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for name in csv_names:
        zf.write(name, arcname=name)

print("created prediction.zip")
for name in csv_names:
    d = pd.read_csv(name)
    print(name, "rows", len(d), "scores", d["Score"].tolist())
