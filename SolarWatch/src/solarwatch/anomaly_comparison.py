from __future__ import annotations

from typing import Any

import pandas as pd


def compare_anomaly_signals(
    measurements: pd.DataFrame,
    forecasts: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Compare Isolation Forest and LSTM anomaly flags on the same test samples."""
    measurement_columns = {
        "PLANT_ID",
        "SOURCE_KEY",
        "DATE_TIME",
        "IFOREST_ANOMALY_SCORE",
        "IS_IFOREST_ANOMALY",
    }
    forecast_columns = {
        "plant_id",
        "inverter_id",
        "timestamp",
        "is_lstm_forecast_anomaly",
        "lstm_absolute_error",
        "lstm_anomaly_threshold",
    }
    missing_measurements = measurement_columns - set(measurements.columns)
    missing_forecasts = forecast_columns - set(forecasts.columns)
    if missing_measurements or missing_forecasts:
        missing = sorted(missing_measurements | missing_forecasts)
        raise ValueError(f"Anomaly comparison columns missing: {', '.join(missing)}")

    scored_measurements = measurements.loc[
        measurements["IFOREST_ANOMALY_SCORE"].notna(),
        [
            "PLANT_ID",
            "SOURCE_KEY",
            "DATE_TIME",
            "IS_IFOREST_ANOMALY",
            "IFOREST_ANOMALY_SCORE",
        ],
    ]
    comparison = scored_measurements.merge(
        forecasts[
            [
                "plant_id",
                "inverter_id",
                "timestamp",
                "is_lstm_forecast_anomaly",
                "lstm_absolute_error",
                "lstm_anomaly_threshold",
            ]
        ],
        left_on=["PLANT_ID", "SOURCE_KEY", "DATE_TIME"],
        right_on=["plant_id", "inverter_id", "timestamp"],
        how="inner",
        validate="one_to_one",
    )
    if comparison.empty:
        raise ValueError(
            "Isolation Forest and LSTM have no common scored test measurements."
        )

    iforest_flag = comparison["IS_IFOREST_ANOMALY"].astype(bool)
    lstm_flag = comparison["is_lstm_forecast_anomaly"].astype(bool)
    both = iforest_flag & lstm_flag
    only_iforest = iforest_flag & ~lstm_flag
    only_lstm = ~iforest_flag & lstm_flag
    neither = ~iforest_flag & ~lstm_flag
    union = iforest_flag | lstm_flag

    comparison["signal_comparison"] = "aucun modèle"
    comparison.loc[only_iforest, "signal_comparison"] = "Isolation Forest seulement"
    comparison.loc[only_lstm, "signal_comparison"] = "LSTM seulement"
    comparison.loc[both, "signal_comparison"] = "deux modèles"

    metrics: dict[str, Any] = {
        "common_test_measurements": int(len(comparison)),
        "isolation_forest_flags": int(iforest_flag.sum()),
        "lstm_forecast_residual_flags": int(lstm_flag.sum()),
        "both_flagged": int(both.sum()),
        "iforest_only": int(only_iforest.sum()),
        "lstm_only": int(only_lstm.sum()),
        "neither_flagged": int(neither.sum()),
        "agreement_rate": round(float((iforest_flag == lstm_flag).mean()), 4),
        "jaccard_similarity": round(
            float(both.sum() / union.sum()) if union.any() else 1.0,
            4,
        ),
        "interpretation": (
            "Accord entre deux signaux différents sur les mêmes mesures de test. "
            "Ce n'est ni une précision ni un rappel : aucune panne réelle étiquetée "
            "ne permet de déterminer quel signal est correct."
        ),
    }
    return comparison, metrics
