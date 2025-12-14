import argparse
import json
import os

import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split


def create_data(test_size: float, random_state: int):
    # charger les données
    bc = load_breast_cancer()
    X = pd.DataFrame(bc.data, columns=bc.feature_names)
    y = pd.Series(bc.target)
    target_names = bc.target_names.tolist()

    # construire les datasets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # sauvegarder les datasets dans data/
    os.makedirs("data", exist_ok=True)

    X_train.to_csv("data/X_train.csv", index=False)
    y_train.to_csv("data/y_train.csv", index=False, header=True)

    X_test.to_csv("data/X_test.csv", index=False)
    y_test.to_csv("data/y_test.csv", index=False, header=True)

    metadata = {"target_names": target_names}
    with open("data/metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)

    print("Datasets saved to data/ directory.")


def load_target_names():
    with open("data/metadata.json", "r") as f:
        metadata = json.load(f)
    return metadata["target_names"]


def load_train_data():
    X_train = pd.read_csv("data/X_train.csv")
    y_train = pd.read_csv("data/y_train.csv").squeeze()
    target_names = load_target_names()
    return X_train, y_train, target_names


def load_test_data():
    X_test = pd.read_csv("data/X_test.csv")
    y_test = pd.read_csv("data/y_test.csv").squeeze()
    target_names = load_target_names()
    return X_test, y_test, target_names


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test-size", type=float, default=0.2, help="Proportion du jeu de test"
    )
    parser.add_argument(
        "--random-state", type=int, default=42, help="Seed pour reproductibilité"
    )
    args = parser.parse_args()
    create_data(test_size=args.test_size, random_state=args.random_state)
