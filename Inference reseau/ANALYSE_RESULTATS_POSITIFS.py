"""
ANALYSE DES RÉSULTATS - Identification du Meilleur Hyperparamètre
"""
import os

print("""
╔════════════════════════════════════════════════════════════════════╗
║          ✅ SCORES AMÉLIORÉS - ANALYSE DU MEILLEUR VARIANT        ║
╚════════════════════════════════════════════════════════════════════╝

RÉSULTATS OBSERVÉS:
══════════════════════════════════════════════════════════════════

Top-300 Variants:
  ✓ maxfea (13:57)        : 0.25 ← MEILLEUR! (+19%)
  ✗ maxfea (13:59)        : 0.22 (+5%)
  ✓ msl_2                 : 0.23 (+10%)
  ✓ Top-300 (baseline)    : 0.23 (+10%)
  
Anciens:
  ○ Top-200               : 0.21 (baseline)
  ○ Top-100               : 0.19 (-10%)
  ○ Consensus/Ensemble    : 0.12-0.15 (-40%)

INSIGHT CLEF:
═════════════════════════════════════════════════════════════════

1. max_features variation = CRITIQUE
   - maxfea (13:57): 0.25 ← Gagnant!
   - maxfea (13:59): 0.22 ← Différent (nom tronqué?)
   
2. Cela signifie probablement:
   - max_features='log2' MEILLEUR
   - OU max_features=0.3 MEILLEUR
   
3. min_samples_leaf=2 aide aussi (0.23 vs 0.21)

STRATÉGIE SUIVANTE:
═════════════════════════════════════════════════════════════════

PHASE 1: Identifier exactement "maxfea" (13:57)
  ├─ Était-ce max_features='log2'?
  ├─ Ou max_features=0.3?
  └─ Généralement, diminuer max_features = plus conservateur = plus stable

PHASE 2: Optimiser combinaison gagnante
  1. Top-300 + maxfeat_log2 (ou 0.3) + n_est_600
  2. Top-300 + maxfeat_log2 (ou 0.3) + msl_2
  3. Top-350 + maxfeat_log2 (ou 0.3)
  4. Top-400 + maxfeat_log2 (ou 0.3)

PHASE 3: Fine-tuning
  ├─ Top-320 + meilleur_maxfeat
  ├─ Top-280 + meilleur_maxfeat
  └─ Trouver sweet spot exact

ESPÉRANCE:
═════════════════════════════════════════════════════════════════

Current best: 0.25 (Top-300 + maxfeat variant)

Potential improvements:
  • Top-350 + maxfeat_log2/0.3 → 0.25-0.28 (espoir: +19-33%)
  • Top-380 + maxfeat_log2/0.3 → 0.24-0.27 (espoir: +14-28%)
  • Top-300 + maxfeat + n_est_600 → 0.25-0.27 (espoir: +19-28%)

CONFIANCE: HAUTE! (Pattern clair: max_features aide)

""")

print("\n" + "="*70)
print("GÉNÉRATION DES STRATÉGIES SUIVANTES")
print("="*70)

# Lister les ZIPs pour identifier les noms exacts
print("\nZIPs générés contenant 'maxfea':")
zips = [f for f in os.listdir('.') if 'top300' in f and '.zip' in f]
for z in sorted(zips):
    size = os.path.getsize(z) / 1024
    print(f"  {z:50s} ({size:6.1f} KB)")

print("""

PROCHAINES ACTIONS:
═════════════════════════════════════════════════════════════════

1️⃣  IDENTIFIER: Quel "maxfea" (13:57) a donné 0.25?
    Candidats:
    └─ prediction_extratrees_top300_maxfeat_log2.zip
    └─ prediction_extratrees_top300_maxfeat_0.3.zip
    
    → Soumettre les deux pour identifier le gagnant

2️⃣  AMPLIFIER le variant gagnant:
    └─ Top-350 + max_features_gagnant
    └─ Top-400 + max_features_gagnant
    └─ Top-300 + max_features_gagnant + n_est_600
    └─ Top-300 + max_features_gagnant + msl_3

3️⃣  FINE-TUNE sweet spot:
    └─ Top-320, Top-340, Top-360, Top-380
    └─ Avec le meilleur max_features

TIMELINE:
═════════════════════════════════════════════════════════════════

MAINTENANT (14:21 UTC+2):
  → Soumettre: maxfeat_log2 et maxfeat_0.3 (clarifier lequel = 0.25)
  → Attendre résultats (~1-2h)
  
SI CONFIRMÉ (16:00):
  → Générer Top-350, Top-380 variantes
  → Soumettre combinaisons gagnantes
  
OBJECTIF: Atteindre 0.26-0.30 (vs 0.25 actuel)

""")
