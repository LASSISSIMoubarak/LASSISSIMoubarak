from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import IsolationForest

from solarwatch.anomaly_comparison import compare_anomaly_signals
from solarwatch.diagnostics import build_synthetic_benchmark, diagnose_measurements
from solarwatch.forecasting import train_lstm_forecast

GENERATION_COLUMNS = {
    "DATE_TIME",
    "PLANT_ID",
    "SOURCE_KEY",
    "AC_POWER",
}
WEATHER_COLUMNS = {
    "DATE_TIME",
    "PLANT_ID",
    "AMBIENT_TEMPERATURE",
    "MODULE_TEMPERATURE",
    "IRRADIATION",
}
INTERVAL_MINUTES = 15
DAYLIGHT_IRRADIATION = 0.1
MIN_PEER_POWER = 10.0
UNDERPERFORMANCE_RATIO = 0.7
MIN_CONSECUTIVE_READINGS = 3
ISOLATION_FOREST_FEATURES = [
    "PERFORMANCE_RATIO",
    "IRRADIATION",
    "AMBIENT_TEMPERATURE",
    "MODULE_TEMPERATURE",
]


def _read_csv(path: Path, required_columns: set[str]) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(
            f"Fichier absent : {path}. Téléchargez les CSV Kaggle et placez-les dans data/raw/."
        )

    data = pd.read_csv(path)
    missing = required_columns - set(data.columns)
    if missing:
        raise ValueError(f"Colonnes absentes de {path.name} : {', '.join(sorted(missing))}")

    data["DATE_TIME"] = pd.to_datetime(
        data["DATE_TIME"], format="mixed", dayfirst=True, errors="raise"
    )
    return data


def load_plant_data(raw_dir: Path, plant_number: int) -> pd.DataFrame:
    """Charge les mesures d'une centrale et ajoute les mesures météo synchronisées."""
    generation_path = raw_dir / f"Plant_{plant_number}_Generation_Data.csv"
    weather_path = raw_dir / f"Plant_{plant_number}_Weather_Sensor_Data.csv"
    generation = _read_csv(generation_path, GENERATION_COLUMNS)
    weather = _read_csv(weather_path, WEATHER_COLUMNS)

    if generation["PLANT_ID"].nunique() != 1 or weather["PLANT_ID"].nunique() != 1:
        raise ValueError(f"Plant_ID incohérent dans les fichiers de la centrale {plant_number}.")
    if set(generation["PLANT_ID"]) != set(weather["PLANT_ID"]):
        raise ValueError(f"Les identifiants de centrale ne correspondent pas ({plant_number}).")

    duplicate_keys = generation.duplicated(["DATE_TIME", "SOURCE_KEY"])
    if duplicate_keys.any():
        raise ValueError(
            f"{int(duplicate_keys.sum())} doublon(s) horodatage/onduleur dans {generation_path.name}."
        )

    weather = (
        weather.groupby(["DATE_TIME", "PLANT_ID"], as_index=False)
        .agg(
            AMBIENT_TEMPERATURE=("AMBIENT_TEMPERATURE", "mean"),
            MODULE_TEMPERATURE=("MODULE_TEMPERATURE", "mean"),
            IRRADIATION=("IRRADIATION", "mean"),
        )
    )
    data = generation.merge(
        weather,
        on=["DATE_TIME", "PLANT_ID"],
        how="left",
        validate="many_to_one",
    )
    data["PEER_MEDIAN_AC_POWER"] = data.groupby("DATE_TIME")["AC_POWER"].transform(
        "median"
    )
    data["PEER_COUNT"] = data.groupby("DATE_TIME")["SOURCE_KEY"].transform("count")
    data["PERFORMANCE_RATIO"] = (
        data["AC_POWER"] / data["PEER_MEDIAN_AC_POWER"].where(
            data["PEER_MEDIAN_AC_POWER"] > 0
        )
    )
    data["IS_MONITORABLE"] = (
        (data["IRRADIATION"] >= DAYLIGHT_IRRADIATION)
        & (data["PEER_MEDIAN_AC_POWER"] >= MIN_PEER_POWER)
        & (data["PEER_COUNT"] >= 5)
    )
    return data.sort_values(["SOURCE_KEY", "DATE_TIME"]).reset_index(drop=True)


def detect_alerts(data: pd.DataFrame) -> pd.DataFrame:
    """Regroupe les baisses relatives persistantes en alertes triées par priorité."""
    alert_columns = [
        "plant_id",
        "inverter_id",
        "start",
        "end",
        "duration_minutes",
        "min_performance_ratio",
        "median_performance_ratio",
        "estimated_energy_gap_kwh",
        "priority",
        "alert_type",
    ]
    alerts: list[dict[str, object]] = []
    candidates = data.loc[
        data["IS_MONITORABLE"]
        & (data["PERFORMANCE_RATIO"] < UNDERPERFORMANCE_RATIO)
    ]

    for (plant_id, inverter_id), inverter_data in candidates.groupby(
        ["PLANT_ID", "SOURCE_KEY"], sort=True
    ):
        inverter_data = inverter_data.sort_values("DATE_TIME")
        segment: list[pd.Series] = []
        previous_time: pd.Timestamp | None = None

        def save_segment(rows: list[pd.Series]) -> None:
            if len(rows) < MIN_CONSECUTIVE_READINGS:
                return
            ratios = pd.Series([row["PERFORMANCE_RATIO"] for row in rows])
            median_ratio = float(ratios.median())
            min_ratio = float(ratios.min())
            if median_ratio <= 0.1:
                priority = "CRITIQUE"
            elif median_ratio <= 0.4:
                priority = "HAUTE"
            else:
                priority = "MOYENNE"
            diagnoses = pd.Series(
                [row.get("diagnosis", "sous_performance_cause_inconnue") for row in rows]
            )
            diagnosis = str(diagnoses.mode().iloc[0])

            energy_gap = sum(
                max(
                    float(row["PEER_MEDIAN_AC_POWER"] - row["AC_POWER"]),
                    0.0,
                )
                * INTERVAL_MINUTES
                / 60
                for row in rows
            )
            alerts.append(
                {
                    "plant_id": int(plant_id),
                    "inverter_id": inverter_id,
                    "start": rows[0]["DATE_TIME"],
                    "end": rows[-1]["DATE_TIME"],
                    "duration_minutes": len(rows) * INTERVAL_MINUTES,
                    "min_performance_ratio": min_ratio,
                    "median_performance_ratio": median_ratio,
                    "estimated_energy_gap_kwh": energy_gap,
                    "priority": priority,
                    "alert_type": diagnosis,
                }
            )

        for _, row in inverter_data.iterrows():
            current_time = row["DATE_TIME"]
            if (
                previous_time is not None
                and (current_time - previous_time).total_seconds() > 20 * 60
            ):
                save_segment(segment)
                segment = []
            segment.append(row)
            previous_time = current_time
        save_segment(segment)

    result = pd.DataFrame(alerts, columns=alert_columns)
    if not result.empty:
        result = result.sort_values(
            ["priority", "estimated_energy_gap_kwh"],
            ascending=[True, False],
            key=lambda column: (
                column.map({"CRITIQUE": 0, "HAUTE": 1, "MOYENNE": 2})
                if column.name == "priority"
                else column
            ),
        ).reset_index(drop=True)
    return result


def detect_plant_interruptions(data: pd.DataFrame) -> pd.DataFrame:
    """Flag persistent, daylight plant-wide zero production as an interruption hypothesis."""
    events: list[dict[str, object]] = []
    plant_rows = data.loc[
        data["IRRADIATION"].notna()
        & (data["IRRADIATION"] >= DAYLIGHT_IRRADIATION)
    ]
    for plant_id, plant_data in plant_rows.groupby("PLANT_ID", sort=True):
        snapshots = (
            plant_data.groupby("DATE_TIME")
            .agg(
                zero_fraction=("AC_POWER", lambda values: (values <= 1.0).mean()),
                peer_count=("SOURCE_KEY", "nunique"),
                irradiation=("IRRADIATION", "median"),
            )
            .reset_index()
            .sort_values("DATE_TIME")
        )
        candidates = snapshots.loc[
            (snapshots["zero_fraction"] >= 0.8) & (snapshots["peer_count"] >= 5)
        ]
        segment: list[pd.Series] = []
        previous_time: pd.Timestamp | None = None

        def save_segment(rows: list[pd.Series]) -> None:
            if len(rows) < MIN_CONSECUTIVE_READINGS:
                return
            events.append(
                {
                    "plant_id": int(plant_id),
                    "inverter_id": "ENSEMBLE_CENTRALE",
                    "start": rows[0]["DATE_TIME"],
                    "end": rows[-1]["DATE_TIME"],
                    "duration_minutes": len(rows) * INTERVAL_MINUTES,
                    "min_performance_ratio": float("nan"),
                    "median_performance_ratio": float("nan"),
                    "estimated_energy_gap_kwh": float("nan"),
                    "priority": "CRITIQUE",
                    "alert_type": "interruption_commune_a_verifier",
                }
            )

        for _, row in candidates.iterrows():
            timestamp = row["DATE_TIME"]
            if (
                previous_time is not None
                and (timestamp - previous_time).total_seconds() > 20 * 60
            ):
                save_segment(segment)
                segment = []
            segment.append(row)
            previous_time = timestamp
        save_segment(segment)
    return pd.DataFrame(
        events,
        columns=[
            "plant_id",
            "inverter_id",
            "start",
            "end",
            "duration_minutes",
            "min_performance_ratio",
            "median_performance_ratio",
            "estimated_energy_gap_kwh",
            "priority",
            "alert_type",
        ],
    )


def score_anomalies(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Entraîne une Isolation Forest par centrale et score son holdout temporel."""
    scored = data.copy()
    scored["IFOREST_ANOMALY_SCORE"] = float("nan")
    scored["IS_IFOREST_ANOMALY"] = False
    holdout_counts: dict[str, int] = {}

    for plant_id, plant_data in scored.groupby("PLANT_ID"):
        eligible = plant_data.loc[plant_data["IS_MONITORABLE"]].sort_values(
            "DATE_TIME"
        )
        timestamps = eligible["DATE_TIME"].drop_duplicates().sort_values()
        if len(timestamps) < 10:
            raise ValueError(
                f"Pas assez d'horodatages surveillables pour entraîner le modèle "
                f"(centrale {int(plant_id)})."
            )

        split_index = int(len(timestamps) * 0.7)
        cutoff = timestamps.iloc[split_index - 1]
        training = eligible.loc[eligible["DATE_TIME"] <= cutoff]
        holdout = eligible.loc[eligible["DATE_TIME"] > cutoff]
        if holdout.empty:
            raise ValueError(f"Jeu de test chronologique vide (centrale {int(plant_id)}).")

        model = IsolationForest(
            n_estimators=200,
            contamination="auto",
            random_state=42,
            n_jobs=-1,
        )
        model.fit(training[ISOLATION_FOREST_FEATURES])
        scores = model.decision_function(holdout[ISOLATION_FOREST_FEATURES])
        predictions = model.predict(holdout[ISOLATION_FOREST_FEATURES]) == -1
        scored.loc[holdout.index, "IFOREST_ANOMALY_SCORE"] = scores
        scored.loc[holdout.index, "IS_IFOREST_ANOMALY"] = predictions
        holdout_counts[str(int(plant_id))] = int(len(holdout))

    return scored, holdout_counts


def _save_plot(data: pd.DataFrame, alerts: pd.DataFrame, output_dir: Path, plant_number: int) -> None:
    if alerts.empty:
        inverter_id = str(data["SOURCE_KEY"].iloc[0])
    else:
        inverter_id = str(alerts.iloc[0]["inverter_id"])
    inverter_data = data.loc[data["SOURCE_KEY"] == inverter_id].sort_values(
        "DATE_TIME"
    )

    figure, axis = plt.subplots(figsize=(12, 4.5))
    axis.plot(
        inverter_data["DATE_TIME"],
        inverter_data["AC_POWER"],
        label="Production mesurée",
        linewidth=1,
    )
    axis.plot(
        inverter_data["DATE_TIME"],
        inverter_data["PEER_MEDIAN_AC_POWER"],
        label="Référence : médiane des onduleurs",
        linewidth=1,
        alpha=0.8,
    )
    flagged = inverter_data.loc[
        inverter_data["IS_MONITORABLE"]
        & (inverter_data["PERFORMANCE_RATIO"] < UNDERPERFORMANCE_RATIO)
    ]
    axis.scatter(
        flagged["DATE_TIME"],
        flagged["AC_POWER"],
        color="red",
        s=12,
        label="Sous-performance candidate",
        zorder=3,
    )
    ml_flagged = inverter_data.loc[inverter_data["IS_IFOREST_ANOMALY"]]
    axis.scatter(
        ml_flagged["DATE_TIME"],
        ml_flagged["AC_POWER"],
        color="darkorange",
        marker="x",
        s=22,
        label="Anomalie Isolation Forest (test)",
        zorder=4,
    )
    axis.set(
        title=f"Centrale {plant_number} — onduleur {inverter_id}",
        xlabel="Date",
        ylabel="Puissance AC (unité du jeu de données)",
    )
    axis.legend()
    axis.grid(alpha=0.2)
    figure.tight_layout()
    figure.savefig(output_dir / f"plant_{plant_number}_monitoring.png", dpi=150)
    plt.close(figure)


def _save_forecast_plot(
    forecasts: pd.DataFrame,
    output_dir: Path,
    plant_id: int,
    plant_number: int,
) -> None:
    plant_forecasts = forecasts.loc[forecasts["plant_id"] == plant_id]
    if plant_forecasts.empty:
        return
    inverter_id = (
        plant_forecasts.groupby("inverter_id")["lstm_absolute_error"]
        .mean()
        .idxmax()
    )
    inverter_forecasts = plant_forecasts.loc[
        plant_forecasts["inverter_id"] == inverter_id
    ].sort_values("timestamp")
    figure, axis = plt.subplots(figsize=(12, 4.5))
    axis.plot(
        inverter_forecasts["timestamp"],
        inverter_forecasts["actual_ac_power"],
        label="Production mesurée",
        linewidth=1,
    )
    axis.plot(
        inverter_forecasts["timestamp"],
        inverter_forecasts["lstm_predicted_ac_power"],
        label="Prévision LSTM",
        linewidth=1,
    )
    axis.plot(
        inverter_forecasts["timestamp"],
        inverter_forecasts["peer_persistence_baseline_ac_power"],
        label="Persistance médiane des pairs (t-1)",
        linewidth=1,
        alpha=0.75,
    )
    axis.set(
        title=f"Centrale {plant_number} — test chronologique, onduleur {inverter_id}",
        xlabel="Date",
        ylabel="Puissance AC (unité du jeu de données)",
    )
    axis.legend()
    axis.grid(alpha=0.2)
    figure.tight_layout()
    figure.savefig(output_dir / f"plant_{plant_number}_lstm_forecast.png", dpi=150)
    plt.close(figure)


def run_pipeline(raw_dir: Path, output_dir: Path) -> dict[str, object]:
    """Exécute la surveillance des deux centrales et écrit les livrables."""
    output_dir.mkdir(parents=True, exist_ok=True)
    all_data = []
    for plant_number in (1, 2):
        data = load_plant_data(raw_dir, plant_number)
        all_data.append(data)

    data = pd.concat(all_data, ignore_index=True)
    data, holdout_counts = score_anomalies(data)
    data = diagnose_measurements(data)
    inverter_alerts = detect_alerts(data)
    plant_alerts = detect_plant_interruptions(data)
    alerts = (
        pd.concat(
            [result for result in (inverter_alerts, plant_alerts) if not result.empty],
            ignore_index=True,
        )
        if not inverter_alerts.empty or not plant_alerts.empty
        else inverter_alerts
    )
    if not alerts.empty:
        priority_order = {"CRITIQUE": 0, "HAUTE": 1, "MOYENNE": 2}
        alerts = alerts.sort_values(
            ["priority", "estimated_energy_gap_kwh"],
            ascending=[True, False],
            key=lambda column: (
                column.map(priority_order)
                if column.name == "priority"
                else column
            ),
            na_position="last",
        ).reset_index(drop=True)
    synthetic_cases, synthetic_metrics = build_synthetic_benchmark(data)
    forecasts, lstm_metrics = train_lstm_forecast(data)
    anomaly_comparison_rows, anomaly_comparison_metrics = compare_anomaly_signals(
        data, forecasts
    )
    monitorable = data.loc[data["IS_MONITORABLE"]]
    flagged_rows = monitorable.loc[
        monitorable["PERFORMANCE_RATIO"] < UNDERPERFORMANCE_RATIO
    ]

    data.to_csv(output_dir / "monitoring_samples.csv", index=False)
    alerts.to_csv(output_dir / "alerts.csv", index=False)
    synthetic_cases.to_csv(output_dir / "synthetic_scenario_benchmark.csv", index=False)
    forecasts.to_csv(output_dir / "lstm_forecasts.csv", index=False)
    anomaly_comparison_rows.to_csv(
        output_dir / "anomaly_signal_comparison.csv", index=False
    )
    (output_dir / "synthetic_scenario_metrics.json").write_text(
        json.dumps(synthetic_metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary: dict[str, object] = {
        "dataset": "Solar Power Generation Data (Kaggle, version 1)",
        "period_start": str(data["DATE_TIME"].min()),
        "period_end": str(data["DATE_TIME"].max()),
        "plants": int(data["PLANT_ID"].nunique()),
        "inverters": int(data["SOURCE_KEY"].nunique()),
        "measurements": int(len(data)),
        "measurements_without_weather": int(data["IRRADIATION"].isna().sum()),
        "monitorable_measurements": int(len(monitorable)),
        "candidate_underperformance_readings": int(len(flagged_rows)),
        "alerts": int(len(alerts)),
        "alerts_by_priority": {
            priority: int(alerts["priority"].eq(priority).sum())
            for priority in ("CRITIQUE", "HAUTE", "MOYENNE")
        },
        "alerts_by_plant": {
            str(int(plant_id)): int(count)
            for plant_id, count in alerts.groupby("plant_id").size().items()
        },
        "isolation_forest": {
            "training_fraction": 0.7,
            "test_samples": int(sum(holdout_counts.values())),
            "anomalous_test_samples": int(data["IS_IFOREST_ANOMALY"].sum()),
            "test_samples_by_plant": holdout_counts,
            "model": "IsolationForest",
            "contamination": "auto",
            "random_state": 42,
        },
        "lstm_forecast": lstm_metrics,
        "anomaly_signal_comparison": anomaly_comparison_metrics,
        "diagnostic_hypotheses": {
            "scope": (
                "Inverter-level telemetry only; interruption and stop labels are "
                "hypotheses, string-level diagnosis is not observable."
            ),
            "hypothesis_counts": {
                str(name): int(count)
                for name, count in data["diagnosis"].value_counts().items()
            },
            "priorities": {
                str(name): int(count)
                for name, count in data["priority"].value_counts().items()
            },
        },
        "synthetic_scenario_benchmark": synthetic_metrics,
        "total_estimated_energy_gap_kwh": round(
            float(alerts["estimated_energy_gap_kwh"].sum()), 2
        ),
        "detection_parameters": {
            "daylight_irradiation_minimum": DAYLIGHT_IRRADIATION,
            "peer_power_minimum": MIN_PEER_POWER,
            "underperformance_ratio_maximum": UNDERPERFORMANCE_RATIO,
            "minimum_consecutive_readings": MIN_CONSECUTIVE_READINGS,
            "interval_minutes": INTERVAL_MINUTES,
        },
        "interpretation": (
            "L'Isolation Forest repère des mesures atypiques et le LSTM signale "
            "des écarts de prévision; leur accord est calculé sur des mesures de "
            "test communes, mais ce n'est pas une mesure de précision. Les alertes "
            "règles restent des anomalies candidates, pas des pannes confirmées "
            "(aucun label de panne dans le jeu). Les écarts d'énergie sont estimés."
        ),
    }
    (output_dir / "results.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for plant_number in (1, 2):
        plant_id = all_data[plant_number - 1]["PLANT_ID"].iloc[0]
        plant_data = data.loc[data["PLANT_ID"] == plant_id]
        plant_alerts = alerts.loc[alerts["plant_id"] == plant_id]
        _save_plot(plant_data, plant_alerts, output_dir, plant_number)
        _save_forecast_plot(forecasts, output_dir, int(plant_id), plant_number)
    return summary
