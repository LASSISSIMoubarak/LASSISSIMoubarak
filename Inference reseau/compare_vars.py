import pandas as pd

print("="*60)
print("COMPARING TRAIN vs TEST VARIABLES")
print("="*60)

for g in range(1, 6):
    train = pd.read_csv(f'data_train/data{g}.csv')
    test = pd.read_csv(f'test_data/data{g}.csv')
    
    train_vars = set(train.columns)
    test_vars = set(test.columns)
    common = train_vars & test_vars
    
    print(f"\nGraph {g}:")
    print(f"  Train shape: {train.shape}")
    print(f"  Test shape:  {test.shape}")
    print(f"  Train variables: {sorted(list(train.columns))}")
    print(f"  Test variables (first 20): {sorted(list(test.columns))[:20]}")
    print(f"  Common: {len(common)}/{len(test_vars)}")
    print(f"  In test but not train: {len(test_vars - train_vars)}")
    if len(test_vars - train_vars) > 0:
        print(f"    Examples: {sorted(list(test_vars - train_vars))[:5]}")
