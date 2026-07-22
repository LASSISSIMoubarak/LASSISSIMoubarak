#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE10_TRACKER.py - Help track Phase 10 submissions
=====================================================

After Phase 10 completes, use this to:
1. List all generated ZIP files
2. Show summary of combinations
3. Prepare submission list
"""

import os
import pandas as pd
from pathlib import Path

def list_phase10_files():
    """List all Phase 10 prediction files"""
    phase10_files = sorted(Path('.').glob('prediction_phase10*.zip'))
    
    print("\n" + "="*70)
    print("PHASE 10 GENERATED FILES")
    print("="*70)
    
    if not phase10_files:
        print("❌ No Phase 10 files found yet. Script still running?")
        return None
    
    print(f"\n✓ Found {len(phase10_files)} submission files\n")
    
    results = []
    for i, fp in enumerate(phase10_files, 1):
        size_kb = fp.stat().st_size / 1024
        filename = fp.name
        
        # Extract hyperparams from filename
        # Format: prediction_phase10_ridge{R}_lasso{L}_top{K}.zip
        parts = filename.replace('prediction_phase10_', '').replace('.zip', '')
        
        print(f"{i:2d}. {filename} ({size_kb:.1f} KB)")
        results.append({
            'index': i,
            'filename': filename,
            'size_kb': size_kb
        })
    
    return pd.DataFrame(results)

def show_submission_template():
    """Show template for recording scores"""
    print("\n" + "="*70)
    print("CODALAB SUBMISSION TRACKING TEMPLATE")
    print("="*70)
    print("""
After submitting each ZIP to Codalab, record the score here:

| File | Ridge Alpha | Lasso Alpha | K | Score |
|------|-------------|-------------|---|-------|
| prediction_phase10_ridge4.0_lasso0.004_top320.zip | 4.0 | 0.004 | 320 | ? |
| prediction_phase10_ridge4.0_lasso0.005_top320.zip | 4.0 | 0.005 | 320 | ? |
| prediction_phase10_ridge4.0_lasso0.006_top320.zip | 4.0 | 0.006 | 320 | ? |
| ... | ... | ... | ... | ... |

Once scores are recorded, analyze to find best combination!
""")

def main():
    print("\n" + "="*70)
    print("PHASE 10 TRACKER")
    print("="*70)
    
    # Check if PHASE10_SUBMISSIONS.csv exists
    if os.path.exists('PHASE10_SUBMISSIONS.csv'):
        print("\n✓ Found PHASE10_SUBMISSIONS.csv")
        df = pd.read_csv('PHASE10_SUBMISSIONS.csv')
        print(f"  Expected submissions: {len(df)}")
        print(f"  Ridge alphas: {df['Ridge_Alpha'].unique().tolist()}")
        print(f"  Lasso alphas: {df['Lasso_Alpha'].unique().tolist()}")
    else:
        print("\n⏳ PHASE10_SUBMISSIONS.csv not found yet (script running)")
    
    # List generated files
    df_files = list_phase10_files()
    
    if df_files is not None:
        print("\n" + "="*70)
        print("READY TO SUBMIT")
        print("="*70)
        print(f"\n✓ {len(df_files)} files ready to submit to Codalab")
    else:
        print("\n⏳ Waiting for Phase 10 to complete...")
    
    show_submission_template()

if __name__ == '__main__':
    main()
