from __future__ import annotations

import argparse
import json
from pathlib import Path

from solarwatch.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyse les performances d'onduleurs à partir des CSV Kaggle."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/raw"),
        help="Dossier contenant les quatre CSV du jeu Kaggle (défaut : data/raw).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Dossier de sortie (défaut : outputs).",
    )
    args = parser.parse_args()
    print(json.dumps(run_pipeline(args.data_dir, args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
