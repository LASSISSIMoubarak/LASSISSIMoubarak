import argparse
import os

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler

from mlops_breast_cancer.data_utils import load_test_data, load_train_data


def train_model(random_state: int):
    # charger les données
    X_train, y_train, target_names = load_train_data()
    X_test, y_test, _ = load_test_data()
    # construire et entrainer le scaler
    scaler = StandardScaler()
    scaler.fit(X_train)

    X_train_scaled = scaler.transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # entrainer le modèle
    model = LogisticRegression(random_state=random_state, max_iter=1000)
    model.fit(X_train_scaled, y_train)

    # évaluer le modèle
    y_pred = model.predict(X_test_scaled)
    print("Classification report on test set:")
    print(classification_report(y_test, y_pred, target_names=target_names))

    # sauvegarder le modèle et le scaler
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/logistic_regression_model.pkl")
    joblib.dump(scaler, "models/standard_scaler.pkl")
    print("Model and scaler saved to models/ directory.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--random-state", type=int, default=42, help="Seed pour reproductibilité"
    )
    args = parser.parse_args()
    train_model(random_state=args.random_state)
