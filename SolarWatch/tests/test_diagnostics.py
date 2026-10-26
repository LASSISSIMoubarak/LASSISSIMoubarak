import pandas as pd

from solarwatch.diagnostics import (
    build_synthetic_benchmark,
    diagnose_measurements,
    diagnose_snapshot,
)


def _snapshot(timestamp="2020-05-15 12:00"):
    return pd.DataFrame(
        {
            "PLANT_ID": [1] * 6,
            "SOURCE_KEY": [f"INV-{index}" for index in range(6)],
            "DATE_TIME": [pd.Timestamp(timestamp)] * 6,
            "AC_POWER": [100.0, 110.0, 120.0, 130.0, 140.0, 150.0],
            "PEER_MEDIAN_AC_POWER": [125.0] * 6,
            "IRRADIATION": [0.6] * 6,
        }
    )


def test_diagnose_snapshot_flags_inverter_stop_and_common_zero():
    inverter_stop = _snapshot()
    inverter_stop.loc[5, "AC_POWER"] = 0.0
    diagnoses = diagnose_snapshot(inverter_stop).set_index("SOURCE_KEY")
    assert diagnoses.loc["INV-5", "diagnosis"] == "arret_onduleur_a_verifier"
    assert diagnoses.loc["INV-5", "priority"] == "CRITIQUE"

    grid_interruption = _snapshot()
    grid_interruption["AC_POWER"] = 0.0
    diagnoses = diagnose_snapshot(grid_interruption)
    assert diagnoses["diagnosis"].eq("interruption_commune_a_verifier").all()


def test_vectorized_diagnoses_match_snapshot_diagnoses():
    data = _snapshot()
    data.loc[5, "AC_POWER"] = 0.0

    vectorized = diagnose_measurements(data)
    snapshot = diagnose_snapshot(data).set_index("SOURCE_KEY")

    assert vectorized["diagnosis"].tolist() == [
        snapshot.loc[key, "diagnosis"] for key in data["SOURCE_KEY"]
    ]


def test_nighttime_measurements_are_not_mislabeled_as_normal():
    data = _snapshot()
    data["IRRADIATION"] = 0.0

    vectorized = diagnose_measurements(data)
    snapshot = diagnose_snapshot(data)

    assert vectorized["diagnosis"].eq("non_surveille").all()
    assert snapshot["diagnosis"].eq("non_surveille").all()


def test_synthetic_benchmark_distinguishes_supported_alert_hypotheses():
    data = pd.concat(
        [_snapshot(f"2020-05-15 {hour:02}:00") for hour in range(10, 13)],
        ignore_index=True,
    )

    results, metrics = build_synthetic_benchmark(data)

    assert len(results) == 12
    assert metrics["accuracy_on_injected_scenarios"] == 1.0
    assert metrics["events_by_injection"] == {
        "normal": 3,
        "inverter_stop": 3,
        "localized_derating": 3,
        "grid_interruption": 3,
    }


def test_plant_wide_zero_production_becomes_a_common_interruption_alert():
    from solarwatch.pipeline import detect_plant_interruptions

    data = pd.concat(
        [
            _snapshot(timestamp.strftime("%Y-%m-%d %H:%M"))
            for timestamp in pd.date_range(
                "2020-05-15 10:00", periods=3, freq="15min"
            )
        ],
        ignore_index=True,
    )
    data["AC_POWER"] = 0.0

    alerts = detect_plant_interruptions(data)

    assert len(alerts) == 1
    assert alerts.iloc[0]["alert_type"] == "interruption_commune_a_verifier"
    assert alerts.iloc[0]["priority"] == "CRITIQUE"
