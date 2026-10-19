#!/usr/bin/env python3
"""
Script de lancement pour entraîner PPO-AdaptiveKL sur plusieurs environnements.

Ce script lance des sessions d'entraînement séquentielles pour chaque environnement
et collecte les résultats.
"""

import subprocess
import time
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Configuration des environnements à entraîner
ENVIRONMENTS = [
    {
        "name": "CartPole-v1",
        "episodes": 500,
        "description": "Environnement CartPole avec PPO-AdaptiveKL"
    },
    {
        "name": "gridworld-v0",
        "episodes": 500,
        "description": "Environnement GridWorld custom avec PPO-AdaptiveKL"
    }
]


def main():
    """Lance l'entraînement PPO-AdaptiveKL sur tous les environnements"""

    print("\n" + "="*90)
    print("PPO-AdaptiveKL - Entraînement sur plusieurs environnements")
    print("="*90 + "\n")

    print("Environnements à entraîner:")
    for i, env in enumerate(ENVIRONMENTS, 1):
        print(f"  {i}. {env['name']:20s} | Episodes: {env['episodes']:4d} | {env['description']}")

    print(f"\nDémarrage: {datetime.now().strftime('%H:%M:%S')}")
    print("="*90 + "\n")

    results = []

    for i, env in enumerate(ENVIRONMENTS, 1):
        env_name = env['name']
        episodes = env['episodes']

        print(f"\n[{i}/{len(ENVIRONMENTS)}] Entraînement: {env_name}")
        print(f"     Episodes: {episodes}")
        print(f"     Heure: {datetime.now().strftime('%H:%M:%S')}")
        print("-"*90)

        try:
            # Construit la commande Python
            cmd = [
                sys.executable,
                str(PROJECT_ROOT / 'src' / 'ppo_adaptive_kl.py'),
                '--env', env_name,
                '--episodes', str(episodes),
                '--steps-per-iter', '1000'
            ]

            # Lance le sous-processus
            result = subprocess.run(cmd, capture_output=False, text=True, cwd=PROJECT_ROOT)

            if result.returncode == 0:
                print(f"\n[✓] {env_name} - SUCCESS (Code: {result.returncode})")
                results.append((env_name, "SUCCESS"))
            else:
                print(f"\n[✗] {env_name} - FAILED (Code: {result.returncode})")
                results.append((env_name, "FAILED"))

        except Exception as e:
            print(f"\n[✗] {env_name} - ERROR: {e}")
            results.append((env_name, "ERROR"))

        print("\n" + "="*90)

        # Pause entre les entraînements
        if i < len(ENVIRONMENTS):
            print("\n[...] Attente 5 secondes avant environnement suivant...")
            time.sleep(5)

    # Affiche le résumé final
    print("\n" + "="*90)
    print("RESUME DE L'EXECUTION")
    print("="*90)
    for env_name, status in results:
        status_symbol = "✓" if status == "SUCCESS" else "✗"
        print(f"  [{status_symbol}] {env_name:25s} | {status}")

    print(f"\n{'='*90}")
    print("Informations importantes:")
    print("  Résultats stockés dans: ./XP/PPO_KL/")
    print("  Chaque entraînement crée un dossier avec timestamp")
    print("\nPour visualiser les courbes d'entraînement:")
    print("  $ tensorboard --logdir=./XP/PPO_KL/")
    print(f"{'='*90}\n")


if __name__ == '__main__':
    main()
