"""
Script launcher pour executer toutes les 10 variantes PPO (CartPole + GridWorld)
Execution sequentielle avec timing et suivi du progres
"""

import subprocess
import time
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def run_variant(variant_file):
    """
    Execute une variante PPO et retourne les statistiques
    """
    try:
        print(f"\n{'='*70}")
        print(f">>> Execution: {variant_file}")
        print(f"{'='*70}")

        start_time = time.time()

        # Execution du script
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / variant_file)],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes max par variante
            cwd=PROJECT_ROOT,
        )

        elapsed = time.time() - start_time

        # Affichage des resultats
        print(result.stdout)
        if result.stderr:
            print("[WARNING] STDERR:", result.stderr)

        status = "[OK]" if result.returncode == 0 else f"[FAIL] code {result.returncode}"

        return {
            "variant": variant_file,
            "status": status,
            "time": elapsed,
            "returncode": result.returncode
        }

    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {variant_file} a depasse 10 minutes")
        return {
            "variant": variant_file,
            "status": "[TIMEOUT]",
            "time": 600,
            "returncode": -1
        }
    except Exception as e:
        print(f"[ERROR] Erreur lors de l'execution: {e}")
        return {
            "variant": variant_file,
            "status": f"[ERROR] {str(e)}",
            "time": 0,
            "returncode": -1
        }

def main():
    """
    Execute toutes les 10 variantes PPO en sequence
    """
    # Liste de toutes les variantes
    variants = [
        # CartPole variants
        "src/ppo_v1_cartpole.py",
        "src/ppo_v2_cartpole.py",
        "src/ppo_v3_cartpole.py",
        "src/ppo_v4_cartpole.py",
        "src/ppo_v5_cartpole.py",
        # GridWorld variants
        "src/ppo_v1_gridworld.py",
        "src/ppo_v2_gridworld.py",
        "src/ppo_v3_gridworld.py",
        "src/ppo_v4_gridworld.py",
        "src/ppo_v5_gridworld.py",
    ]

    # Verification que tous les fichiers existent
    print("[INFO] Verification des fichiers...")
    missing = []
    for v in variants:
        if not (PROJECT_ROOT / v).exists():
            missing.append(v)

    if missing:
        print(f"[FAIL] Fichiers manquants: {missing}")
        return

    print(f"[OK] Tous les {len(variants)} fichiers presents\n")

    # Execution
    print(f"[START] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Execution de {len(variants)} variantes...")

    start_total = time.time()
    results = []

    for i, variant in enumerate(variants, 1):
        print(f"\n[PROGRESS] [{i}/{len(variants)}]")
        result = run_variant(variant)
        results.append(result)

    total_time = time.time() - start_total

    # Rapport final
    print(f"\n\n{'='*70}")
    print(f"[REPORT] RAPPORT FINAL - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    cartpole_results = results[:5]
    gridworld_results = results[5:]

    print("[RESULTS] CartPole Variants:")
    for r in cartpole_results:
        print(f"  {r['variant']:30} {r['status']:20} ({r['time']:.1f}s)")

    print("\n[RESULTS] GridWorld Variants:")
    for r in gridworld_results:
        print(f"  {r['variant']:30} {r['status']:20} ({r['time']:.1f}s)")

    # Statistiques
    success_count = sum(1 for r in results if r["returncode"] == 0)
    failed_count = len(results) - success_count
    total_compute_time = sum(r["time"] for r in results)

    print(f"\n{'─'*70}")
    print(f"Resultats: {success_count} OK / {failed_count} FAIL (total: {len(results)})")
    print(f"Temps total (compute): {total_compute_time:.1f}s ({total_compute_time/60:.1f}m)")
    print(f"Temps total (elapsed): {total_time:.1f}s ({total_time/60:.1f}m)")
    print(f"{'='*70}\n")

    return success_count, failed_count

if __name__ == "__main__":
    success, failed = main()
    sys.exit(0 if failed == 0 else 1)
