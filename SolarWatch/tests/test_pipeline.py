import pandas as pd

from solarwatch.pipeline import detect_alerts, score_anomalies


def test_detect_alerts_requires_three_readings_and_ranks_severe_events():
    timestamps = pd.to_datetime(
        [
            "2020-05-15 10:00",
            "2020-05-15 10:15",
            "2020-05-15 10:30",
            "2020-05-15 12:00",
            "2020-05-15 12:15",
            "2020-05-15 12:30",
        ]
    )
    data = pd.DataFrame(
        {
            "PLANT_ID": [1] * 6,
            "SOURCE_KEY": ["INV-1"] * 6,
            "DATE_TIME": timestamps,
            "IS_MONITORABLE": [True] * 6,
            "PERFORMANCE_RATIO": [0.6, 0.6, 0.6, 0.05, 0.05, 0.05],
            "PEER_MEDIAN_AC_POWER": [100.0] * 6,
            "AC_POWER": [60.0, 60.0, 60.0, 5.0, 5.0, 5.0],
        }
    )

    alerts = detect_alerts(data)

    assert len(alerts) == 2
    assert alerts.iloc[0]["priority"] == "CRITIQUE"
    assert alerts.iloc[0]["duration_minutes"] == 45
    assert alerts.iloc[0]["estimated_energy_gap_kwh"] == 71.25
    assert alerts.iloc[1]["priority"] == "MOYENNE"


def test_detect_alerts_ignores_short_and_unmonitorable_dips():
    timestamps = pd.date_range("2020-05-15 10:00", periods=3, freq="15min")
    data = pd.DataFrame(
        {
            "PLANT_ID": [1] * 3,
            "SOURCE_KEY": ["INV-1"] * 3,
            "DATE_TIME": timestamps,
            "IS_MONITORABLE": [True, True, False],
            "PERFORMANCE_RATIO": [0.2, 0.2, 0.1],
            "PEER_MEDIAN_AC_POWER": [100.0] * 3,
            "AC_POWER": [20.0, 20.0, 10.0],
        }
    )

    assert detect_alerts(data).empty


def test_isolation_forest_is_trained_before_and_scores_temporal_holdout():
    data = pd.DataFrame(
        {
            "PLANT_ID": [1] * 101,
            "DATE_TIME": pd.date_range("2020-05-15", periods=101, freq="15min"),
            "IS_MONITORABLE": [True] * 101,
            "PERFORMANCE_RATIO": [0.95 + (i % 5) * 0.01 for i in range(100)] + [0.01],
            "IRRADIATION": [0.6 + (i % 4) * 0.02 for i in range(100)] + [0.9],
            "AMBIENT_TEMPERATURE": [25.0 + (i % 3) for i in range(100)] + [45.0],
            "MODULE_TEMPERATURE": [30.0 + (i % 5) for i in range(100)] + [65.0],
        }
    )

    scored, holdout_counts = score_anomalies(data)

    assert holdout_counts == {"1": 31}
    assert scored.iloc[:70]["IFOREST_ANOMALY_SCORE"].isna().all()
    assert scored.iloc[70:]["IFOREST_ANOMALY_SCORE"].notna().all()
    assert bool(scored.iloc[-1]["IS_IFOREST_ANOMALY"])
