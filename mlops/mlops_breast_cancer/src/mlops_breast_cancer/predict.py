import argparse
from pathlib import Path

import joblib

from mlops_breast_cancer.data_utils import load_test_data

MODEL_DIR = Path(__file__).resolve().parents[2] / "models"


def predict_example(index: int = 0):
    # charger les données de puis data/
    X, y, target_names = load_test_data()
    # charger le modèle et le scaler
    model_path = MODEL_DIR / "logistic_regression_model.pkl"
    scaler_path = MODEL_DIR / "standard_scaler.pkl"

    if not model_path.exists() or not scaler_path.exists():
        raise FileNotFoundError(
            f"Model or scaler not found in {MODEL_DIR}. Run train.py first."
        )

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    # vérifier l'index
    if index < 0 or index >= len(X):
        raise IndexError(f"Index {index} out of range (0..{len(X)-1})")

    # sélectionner et standardiser l'exemple
    x_example = X.iloc[[index]]
    x_scaled = scaler.transform(x_example)

    # prédiction
    pred = model.predict(x_scaled)[0]
    pred_proba = model.predict_proba(x_scaled)[0]
    true_label = int(y.iloc[index]) if hasattr(y, 'iloc') else int(y[index])

    # affichage des résultats
    print(f"Example index: {index}")
    print(f"True label: {true_label} ({target_names[true_label]})")
    print(f"Predicted label: {pred} ({target_names[pred]})")
    print("Class probabilities:")
    for i, p in enumerate(pred_proba):
        print(f" - {target_names[i]}: {p:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--index", type=int, default=0, help="Index de l'exemple pour la prédiction"
    )
    args = parser.parse_args()
    predict_example(index=args.index)
