import pandas as pd
import numpy as np

for g in range(1, 6):
    df = pd.read_csv(f'data_train/data{g}.csv')
    print(f"\nGraphe {g}:")
    print(f"  Shape: {df.shape}")
    print(f"  Missing values: {df.isnull().sum().sum()} ({100*df.isnull().sum().sum() / (df.shape[0]*df.shape[1]):.1f}%)")
    print(f"  Columns: {df.columns.tolist()}")
    
    target = pd.read_csv(f'data_train/target{g}.csv')
    print(f"  True edges: {len(target)}")
    
    # Vérifier si toutes les variables dans target sont dans data
    vars_in_data = set(df.columns)
    vars_in_target = set(target['Cause'].unique()) | set(target['Effect'].unique())
    missing_vars = vars_in_target - vars_in_data
    if missing_vars:
        print(f"  ⚠️ Variables in target but not in data: {missing_vars}")
    else:
        print(f"  ✓ All variables match")
