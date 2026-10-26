from __future__ import annotations

import pandas as pd

IRRADIANCE_THRESHOLD = 0.1
MIN_PEER_POWER = 10.0
SHARED_ZERO_FRACTION = 0.8
STOP_RATIO = 0.05
UNDERPERFORMANCE_RATIO = 0.7


def diagnose_snapshot(snapshot: pd.DataFrame) -> pd.DataFrame:
    """Return operational hypotheses for one plant and timestamp."""
    required = {"PLANT_ID", "SOURCE_KEY", "AC_POWER", "IRRADIATION"}
    if "DATE_TIME" in snapshot:
        required.add("DATE_TIME")
    missing = required - set(snapshot.columns)
    if missing:
        raise ValueError(f"Snapshot columns missing: {', '.join(sorted(missing))}")
    if snapshot.empty:
        return pd.DataFrame(
            columns=[
                "SOURCE_KEY",
                "performance_ratio",
                "zero_fraction",
                "diagnosis",
                "priority",
                "confidence",
            ]
        )
    if "DATE_TIME" in snapshot and snapshot["DATE_TIME"].nunique() > 1:
        raise ValueError("diagnose_snapshot expects one timestamp.")
    if snapshot["PLANT_ID"].nunique() > 1:
        raise ValueError("diagnose_snapshot expects one plant.")

    rows = snapshot.copy()
    peer_median = rows.groupby("PLANT_ID")["AC_POWER"].transform("median")
    zero_fraction = rows.groupby("PLANT_ID")["AC_POWER"].transform(
        lambda values: (values <= 1.0).mean()
    )
    rows["performance_ratio"] = rows["AC_POWER"] / peer_median.where(peer_median > 0)
    rows["zero_fraction"] = zero_fraction
    irradiance = rows.groupby("PLANT_ID")["IRRADIATION"].transform("median")
    enough_peers = rows.groupby("PLANT_ID")["SOURCE_KEY"].transform("nunique") >= 5
    monitorable = (irradiance >= IRRADIANCE_THRESHOLD) & (
        peer_median >= MIN_PEER_POWER
    ) & enough_peers

    rows["diagnosis"] = "non_surveille"
    rows.loc[monitorable, "diagnosis"] = "normal"
    rows["priority"] = "AUCUNE"
    rows["confidence"] = "faible"

    grid_candidate = (
        (irradiance >= IRRADIANCE_THRESHOLD)
        & enough_peers
        & (zero_fraction >= SHARED_ZERO_FRACTION)
    )
    rows.loc[grid_candidate, "diagnosis"] = "interruption_commune_a_verifier"
    rows.loc[grid_candidate, "priority"] = "CRITIQUE"
    rows.loc[grid_candidate, "confidence"] = "moyenne"

    inverter_stop = (
        monitorable
        & ~grid_candidate
        & (rows["AC_POWER"] <= 1.0)
        & (rows["performance_ratio"] <= STOP_RATIO)
    )
    rows.loc[inverter_stop, "diagnosis"] = "arret_onduleur_a_verifier"
    rows.loc[inverter_stop, "priority"] = "CRITIQUE"
    rows.loc[inverter_stop, "confidence"] = "moyenne"

    underperformance = (
        monitorable
        & ~grid_candidate
        & ~inverter_stop
        & (rows["performance_ratio"] < UNDERPERFORMANCE_RATIO)
    )
    rows.loc[underperformance, "diagnosis"] = "sous_performance_cause_inconnue"
    rows.loc[underperformance, "priority"] = "HAUTE"
    rows.loc[underperformance, "confidence"] = "faible"
    return rows[
        [
            "SOURCE_KEY",
            "performance_ratio",
            "zero_fraction",
            "diagnosis",
            "priority",
            "confidence",
        ]
    ]


def diagnose_measurements(data: pd.DataFrame) -> pd.DataFrame:
    """Add vectorized inverter-level diagnostic hypotheses to all measurements."""
    required = {"PLANT_ID", "DATE_TIME", "SOURCE_KEY", "AC_POWER", "IRRADIATION"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Measurement columns missing: {', '.join(sorted(missing))}")

    result = data.copy()
    group = result.groupby(["PLANT_ID", "DATE_TIME"], sort=False)
    peer_median = group["AC_POWER"].transform("median")
    zero_fraction = (result["AC_POWER"] <= 1.0).groupby(
        [result["PLANT_ID"], result["DATE_TIME"]], sort=False
    ).transform("mean")
    peer_count = group["SOURCE_KEY"].transform("nunique")
    irradiation = group["IRRADIATION"].transform("median")
    ratio = result["AC_POWER"] / peer_median.where(peer_median > 0)
    monitorable = (
        (irradiation >= IRRADIANCE_THRESHOLD)
        & (peer_median >= MIN_PEER_POWER)
        & (peer_count >= 5)
    )
    common_outage = (
        (irradiation >= IRRADIANCE_THRESHOLD)
        & (peer_count >= 5)
        & (zero_fraction >= SHARED_ZERO_FRACTION)
    )
    inverter_stop = (
        monitorable
        & ~common_outage
        & (result["AC_POWER"] <= 1.0)
        & (ratio <= STOP_RATIO)
    )
    underperformance = (
        monitorable
        & ~common_outage
        & ~inverter_stop
        & (ratio < UNDERPERFORMANCE_RATIO)
    )
    result["diagnosis"] = "non_surveille"
    result.loc[monitorable, "diagnosis"] = "normal"
    result.loc[common_outage, "diagnosis"] = "interruption_commune_a_verifier"
    result.loc[inverter_stop, "diagnosis"] = "arret_onduleur_a_verifier"
    result.loc[underperformance, "diagnosis"] = "sous_performance_cause_inconnue"
    result["priority"] = "AUCUNE"
    result.loc[common_outage | inverter_stop, "priority"] = "CRITIQUE"
    result.loc[underperformance, "priority"] = "HAUTE"
    result["confidence"] = "faible"
    result.loc[common_outage | inverter_stop, "confidence"] = "moyenne"
    result["diagnostic_performance_ratio"] = ratio
    result["zero_fraction"] = zero_fraction
    return result


def build_synthetic_benchmark(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    """Evaluate diagnostic rules on injected, explicitly synthetic snapshot cases."""
    cases: list[pd.DataFrame] = []
    for plant_id, plant_data in data.groupby("PLANT_ID"):
        snapshots = plant_data.loc[
            (plant_data["IRRADIATION"] >= 0.3)
            & (plant_data["PEER_MEDIAN_AC_POWER"] >= 100)
            & plant_data["IRRADIATION"].notna()
        ]
        timestamps = snapshots["DATE_TIME"].drop_duplicates().sort_values()
        if timestamps.empty:
            continue
        sample_indices = range(0, len(timestamps), max(1, len(timestamps) // 40))
        for timestamp_index in sample_indices:
            timestamp = timestamps.iloc[timestamp_index]
            base = snapshots.loc[snapshots["DATE_TIME"] == timestamp].copy()
            if len(base) < 5:
                continue
            target_index = base["AC_POWER"].idxmax()
            scenarios = [
                ("normal", None),
                ("inverter_stop", "stop"),
                ("localized_derating", "derating"),
                ("grid_interruption", "grid"),
            ]
            for scenario, injection in scenarios:
                event = base.copy()
                if injection == "stop":
                    event.loc[target_index, "AC_POWER"] = 0.0
                elif injection == "derating":
                    event.loc[target_index, "AC_POWER"] *= 0.5
                elif injection == "grid":
                    event["AC_POWER"] = 0.0
                diagnosed = diagnose_snapshot(event)
                target_diagnosis = diagnosed.loc[
                    diagnosed["SOURCE_KEY"] == event.loc[target_index, "SOURCE_KEY"]
                ].iloc[0]
                if scenario == "normal":
                    expected = "normal"
                elif scenario == "inverter_stop":
                    expected = "arret_onduleur_a_verifier"
                elif scenario == "localized_derating":
                    expected = "sous_performance_cause_inconnue"
                else:
                    expected = "interruption_commune_a_verifier"
                cases.append(
                    pd.DataFrame(
                        [
                            {
                                "plant_id": int(plant_id),
                                "timestamp": timestamp,
                                "scenario_injecte_synthetique": scenario,
                                "diagnostic_attendu": expected,
                                "diagnostic_observe": target_diagnosis["diagnosis"],
                                "priority": target_diagnosis["priority"],
                            }
                        ]
                    )
                )

    results = (
        pd.concat(cases, ignore_index=True)
        if cases
        else pd.DataFrame(
            columns=[
                "plant_id",
                "timestamp",
                "scenario_injecte_synthetique",
                "diagnostic_attendu",
                "diagnostic_observe",
                "priority",
            ]
        )
    )
    if results.empty:
        raise ValueError("No eligible snapshots available for the synthetic benchmark.")
    correct = results["diagnostic_attendu"] == results["diagnostic_observe"]
    metrics: dict[str, object] = {
        "data_type": "synthetic injections on real historical snapshots; not field faults",
        "events": int(len(results)),
        "accuracy_on_injected_scenarios": round(float(correct.mean()), 4),
        "events_by_injection": {
            str(name): int(count)
            for name, count in results["scenario_injecte_synthetique"]
            .value_counts()
            .items()
        },
        "accuracy_by_injection": {
            str(name): round(
                float(
                    correct.loc[
                        results["scenario_injecte_synthetique"] == name
                    ].mean()
                ),
                4,
            )
            for name in results["scenario_injecte_synthetique"].unique()
        },
        "confusion_matrix": {
            expected: {
                observed: int(
                    (
                        (results["diagnostic_attendu"] == expected)
                        & (results["diagnostic_observe"] == observed)
                    ).sum()
                )
                for observed in sorted(results["diagnostic_observe"].unique())
            }
            for expected in sorted(results["diagnostic_attendu"].unique())
        },
        "limitations": (
            "Les étiquettes décrivent les injections synthétiques. Une baisse locale "
            "ne permet pas de distinguer panne de chaîne, ombrage ou autre cause; "
            "une baisse commune n'établit pas une interruption réseau."
        ),
    }
    return results, metrics
