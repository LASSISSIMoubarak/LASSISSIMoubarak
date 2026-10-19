#!/usr/bin/env python3
"""
Compare PPO runs saved under XP/PPO_KL by reading summary.json files.
"""

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_summaries(root: Path):
    rows = []
    if not root.exists():
        return rows

    for run_dir in root.iterdir():
        if not run_dir.is_dir():
            continue
        summary_path = run_dir / "summary.json"
        if not summary_path.exists():
            continue
        try:
            with summary_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            data["_path"] = str(summary_path)
            rows.append(data)
        except Exception:
            continue

    return rows


def print_table(rows):
    if not rows:
        print("Aucun summary.json trouve dans XP/PPO_KL")
        return

    rows_sorted = sorted(rows, key=lambda r: r.get("avg_reward_last_100", -1e9), reverse=True)

    print("\nClassement PPO (tri: avg_reward_last_100 desc)\n")
    print(f"{'#':>2} {'run_name':45} {'env':15} {'avg100':>10} {'best':>10} {'final':>10}")
    print("-" * 100)
    for i, row in enumerate(rows_sorted, start=1):
        run_name = row.get("run_name", "-")[:45]
        env = row.get("env", "-")[:15]
        avg100 = row.get("avg_reward_last_100", 0.0)
        best = row.get("best_reward", 0.0)
        final = row.get("final_reward", 0.0)
        print(f"{i:>2} {run_name:45} {env:15} {avg100:10.2f} {best:10.2f} {final:10.2f}")

    best_row = rows_sorted[0]
    print("\nMeilleur run:")
    print(f"  run_name : {best_row.get('run_name', '-')}")
    print(f"  env      : {best_row.get('env', '-')}")
    print(f"  avg100   : {best_row.get('avg_reward_last_100', 0.0):.2f}")
    print(f"  summary  : {best_row.get('_path', '-')}")


def main():
    parser = argparse.ArgumentParser(description="Compare PPO runs using summary.json files")
    parser.add_argument(
        "--root",
        type=str,
        default=str(PROJECT_ROOT / "XP" / "PPO_KL"),
        help="Directory containing run folders",
    )
    args = parser.parse_args()

    root = Path(args.root)
    rows = load_summaries(root)
    print_table(rows)


if __name__ == "__main__":
    main()
