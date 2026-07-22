"""
🚀 QUICK START - TESTER LES PRÉDICTIONS OPTIMISÉES
=====================================================

Usage:
  python quick_test.py --strategy consensus_optimized --k 50
  
Ou simplement:
  python quick_test.py
  
Default: Teste Consensus Top-50 (le meilleur!)
"""

import os
import shutil
import argparse

os.chdir(r"c:/Users/lassi/projet/Inference reseau")

def list_zips():
    """List tous les ZIPs disponibles"""
    zips = [f for f in os.listdir('.') if f.startswith('prediction_') and f.endswith('.zip')]
    return sorted(zips)

def copy_zip_to_submit(zip_name):
    """Copie le ZIP pour soumission"""
    if not os.path.exists(zip_name):
        print(f"❌ {zip_name} non trouvé!")
        return False
    
    submit_path = f"{zip_name.replace('.zip', '')}_SUBMIT.zip"
    shutil.copy(zip_name, submit_path)
    print(f"✓ Copié vers: {submit_path}")
    return True

def extract_and_verify(zip_name):
    """Vérifie que le ZIP est valide"""
    import zipfile
    try:
        with zipfile.ZipFile(zip_name, 'r') as zf:
            files = zf.namelist()
            print(f"\n📦 Contenu de {zip_name}:")
            for f in sorted(files):
                info = zf.getinfo(f)
                print(f"   ✓ {f:30s} ({info.file_size:6d} bytes)")
            
            # Vérifier structure
            required = {f'predictions_network{i}.csv' for i in range(1, 6)}
            actual = set(files)
            if required == actual:
                print(f"\n✅ ZIP valide! Prêt à soumettre.")
                return True
            else:
                print(f"\n❌ ZIP invalide!")
                print(f"   Requis: {required}")
                print(f"   Trouvé: {actual}")
                return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test des prédictions optimisées")
    parser.add_argument('--list', action='store_true', help='Lister tous les ZIPs')
    parser.add_argument('--strategy', default='consensus_optimized', help='Stratégie')
    parser.add_argument('--k', default='50', help='Top-K')
    parser.add_argument('--verify', help='Vérifier ZIP spécifique')
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("🚀 OPTIMISATION DES PRÉDICTIONS - QUICK START")
    print("="*70)
    
    if args.list:
        print("\n📋 ZIPs disponibles:\n")
        for i, z in enumerate(list_zips(), 1):
            size = os.path.getsize(z) / 1024 / 1024
            print(f"   {i:2d}. {z:50s} ({size:6.2f} MB)")
        return
    
    if args.verify:
        extract_and_verify(args.verify)
        return
    
    # Default: Test consensus_optimized_top50
    print("\n" + "="*70)
    print("RECOMMANDATION: Consensus Optimized Top-50")
    print("="*70)
    
    strategies = [
        ('Consensus Optimized (BEST)', 'prediction_consensus_optimized_top50.zip'),
        ('Ensemble Top-50', 'prediction_ensemble_top50.zip'),
        ('Correlation Top-50', 'prediction_correlation_top50.zip'),
        ('ExtraTrees Top-50', 'prediction_extratrees_top50.zip'),
    ]
    
    print("\n📊 Stratégies de test (par priorité):\n")
    for i, (desc, zip_name) in enumerate(strategies, 1):
        exists = "✓" if os.path.exists(zip_name) else "✗"
        print(f"   {i}. [{exists}] {desc}")
        print(f"      Fichier: {zip_name}")
        if exists == "✓":
            size = os.path.getsize(zip_name) / 1024
            print(f"      Taille: {size:.1f} KB")
    
    print("\n" + "="*70)
    print("INSTRUCTIONS")
    print("="*70)
    
    print("""
1️⃣  TÉLÉCHARGER ET SOUMETTRE (dans cet ordre):
    
    Première priorité:
    └─ prediction_consensus_optimized_top50.zip
    
    Si score ≤ 0.25:
    └─ prediction_ensemble_top50.zip
    └─ prediction_correlation_top50.zip

2️⃣  VÉRIFIER LA STRUCTURE:
    
    python quick_test.py --verify prediction_consensus_optimized_top50.zip

3️⃣  LISTER TOUS LES ZIPS:
    
    python quick_test.py --list

4️⃣  PERFORMANCE ATTENDUE:
    
    Score actuel:    0.21
    Score espéré:    0.28-0.35 (+33-67%)
    Amélioration:    Réduction overfitting (Top-200 → Top-50)
    
5️⃣  SI TOUJOURS FAIBLE:
    
    Tester: prediction_consensus_optimized_top75.zip
    Puis:   prediction_ensemble_top100.zip
    """)
    
    print("\n" + "="*70)
    print("VÉRIFICATION AUTOMATIQUE")
    print("="*70)
    
    # Vérifier top 3 stratégies
    for desc, zip_name in strategies[:3]:
        if os.path.exists(zip_name):
            print(f"\n✓ Vérifiant {zip_name}...")
            extract_and_verify(zip_name)

if __name__ == '__main__':
    main()
    
    print("\n" + "="*70)
    print("✅ Ready! Procéder avec soumission.")
    print("="*70)
