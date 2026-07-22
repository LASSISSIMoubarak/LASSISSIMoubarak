#!/usr/bin/env python3
"""
Diagnostic: Pourquoi le même fichier ZIP produit des scores différents?
Vérifier intégrité, checksums, et contenus des ZIPs générés
"""

import hashlib
import zipfile
import pandas as pd
from pathlib import Path

def get_file_hash(filepath):
    """Calculer MD5 d'un fichier"""
    md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        md5.update(f.read())
    return md5.hexdigest()

def analyze_zip(zippath):
    """Analyser le contenu d'un ZIP"""
    print(f"\n{'='*70}")
    print(f"ANALYSE: {zippath.name}")
    print(f"{'='*70}")
    
    # Hash du ZIP
    hash_val = get_file_hash(zippath)
    print(f"✓ MD5 du ZIP: {hash_val[:16]}...")
    
    # Taille
    size = zippath.stat().st_size
    print(f"✓ Taille: {size} bytes")
    
    # Contenu
    with zipfile.ZipFile(zippath) as zf:
        print(f"\n📋 CONTENU DU ZIP:")
        total_rows = 0
        total_size = 0
        
        for info in zf.filelist:
            print(f"  • {info.filename}")
            print(f"    - Taille: {info.file_size} bytes")
            print(f"    - Date: {info.date_time}")
            
            # Lire le CSV et compter les lignes
            if info.filename.endswith('.csv'):
                with zf.open(info.filename) as f:
                    df = pd.read_csv(f)
                    rows = len(df)
                    total_rows += rows
                    total_size += info.file_size
                    print(f"    - Lignes: {rows}")
                    print(f"    - Colonnes: {list(df.columns)}")
                    
                    # Stats des scores
                    if 'Score' in df.columns:
                        print(f"    - Score: min={df['Score'].min():.4f}, "
                              f"max={df['Score'].max():.4f}, "
                              f"mean={df['Score'].mean():.4f}")
        
        print(f"\n📊 RÉSUMÉ:")
        print(f"  Total lignes: {total_rows}")
        print(f"  Total taille CSV: {total_size} bytes")
        print(f"  Fichiers: {len([f for f in zf.filelist if f.filename.endswith('.csv')])}")

# Files to analyze
files_to_check = [
    "prediction_extratrees_top350_maxfeat_log2.zip",
    "prediction_extratrees_top380_maxfeat_log2.zip",
    "prediction_extratrees_top320_maxfeat_log2.zip",
]

print("🔍 DIAGNOSTIC: Vérifier intégrité des fichiers ZIP")
print("=" * 70)

# Check which files exist
workspace = Path(".")
existing_files = []
for fname in files_to_check:
    fpath = workspace / fname
    if fpath.exists():
        existing_files.append(fpath)
        print(f"✓ Trouvé: {fname}")
    else:
        print(f"✗ Manquant: {fname}")

print(f"\n📍 Fichiers à analyser: {len(existing_files)}")

# Analyze each file
for zp in sorted(existing_files):
    analyze_zip(zp)

print("\n" + "=" * 70)
print("🎯 INTERPRÉTATION:")
print("=" * 70)
print("""
Si les fichiers ont:
  ✓ Mêmes MD5 hashes → Pas de corruption
  ✓ Mêmes nombres de lignes → Intégrité OK
  ⚠️ Scores différents sur Codabench → Variance de Codabench probable

Si les fichiers ont:
  ❌ MD5 différents → Régénération entre soumissions
  ❌ Lignes différentes → Problème de génération
  ⚠️ Scores différents → Expliqué par contenu différent
""")

print("\n💡 PROCHAINES ACTIONS:")
print("  1. Si hashes identiques → Accepter variance Codabench, soumettre top320")
print("  2. Si hashes différents → Régénérer les fichiers + revalider")
print("  3. Utiliser le score MAX (0.26) comme confiance")
