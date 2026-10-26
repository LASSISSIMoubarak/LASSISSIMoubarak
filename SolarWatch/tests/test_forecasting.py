import pandas as pd
import pytest

from solarwatch.forecasting import train_lstm_forecast


def test_lstm_uses_a_chronological_holdout_and_reports_baseline():
    pytest.importorskip("torch")
    rows = []
    for index, timestamp in enumerate(
        pd.date_range("2020-05-15", periods=50, freq="15min")
    ):
        power = 100 + (index % 10) * 3
        rows.append(
            {
                "PLANT_ID": 1,
                "SOURCE_KEY": "INV-1",
                "DATE_TIME": timestamp,
                "AC_POWER": power,
                "PEER_MEDIAN_AC_POWER": power + 5,
                "IRRADIATION": 0.5 + (index % 4) * 0.05,
                "AMBIENT_TEMPERATURE": 25 + index % 3,
                "MODULE_TEMPERATURE": 30 + index % 5,
            }
        )

    forecasts, metrics = train_lstm_forecast(pd.DataFrame(rows), epochs=1, batch_size=16)

    assert metrics["fit_samples"] > 0
    assert metrics["calibration_samples"] > 0
    assert metrics["test_samples"] > 0
    assert forecasts["timestamp"].min() > pd.Timestamp("2020-05-15 08:00")
    assert metrics["peer_persistence_baseline_mae_ac_power"] > 0
    assert "anomalous_test_forecasts" in metrics
