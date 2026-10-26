import pandas as pd
import pytest

from solarwatch.anomaly_comparison import compare_anomaly_signals


def test_compares_iforest_and_lstm_flags_on_common_rows_only():
    measurements = pd.DataFrame(
        {
            "PLANT_ID": [1, 1, 1, 1],
            "SOURCE_KEY": ["A", "A", "A", "A"],
            "DATE_TIME": pd.date_range("2020-05-15", periods=4, freq="15min"),
            "IFOREST_ANOMALY_SCORE": [-0.2, -0.1, -0.05, float("nan")],
            "IS_IFOREST_ANOMALY": [True, True, False, False],
        }
    )
    forecasts = pd.DataFrame(
        {
            "plant_id": [1, 1, 1],
            "inverter_id": ["A", "A", "A"],
            "timestamp": pd.date_range("2020-05-15", periods=3, freq="15min"),
            "is_lstm_forecast_anomaly": [True, False, True],
            "lstm_absolute_error": [10.0, 2.0, 20.0],
            "lstm_anomaly_threshold": [8.0, 8.0, 8.0],
        }
    )

    comparison, metrics = compare_anomaly_signals(measurements, forecasts)

    assert len(comparison) == 3
    assert metrics["both_flagged"] == 1
    assert metrics["iforest_only"] == 1
    assert metrics["lstm_only"] == 1
    assert metrics["neither_flagged"] == 0
    assert metrics["agreement_rate"] == pytest.approx(0.3333)
    assert metrics["jaccard_similarity"] == pytest.approx(0.3333)
    assert "ni une précision ni un rappel" in metrics["interpretation"]
