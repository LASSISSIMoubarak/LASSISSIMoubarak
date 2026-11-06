from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = PROJECT_DIR.parents[1]
SOLARWATCH_ROOT = REPOSITORY_ROOT / "SolarWatch"
SOLARWATCH_SOURCE = SOLARWATCH_ROOT / "src"
if str(SOLARWATCH_SOURCE) not in sys.path:
    sys.path.insert(0, str(SOLARWATCH_SOURCE))

from solarwatch.pipeline import load_plant_data

FEATURE_COLUMNS = (
    "log_current_power",
    "irradiation",
    "irradiation_change",
    "ambient_temperature",
    "module_temperature",
    "hour_sin",
    "hour_cos",
)
INTERVAL_MINUTES = 15


@dataclass(frozen=True)
class GibbsPosterior:
    feature_means: np.ndarray
    feature_scales: np.ndarray
    target_mean: float
    target_scale: float
    beta_draws: np.ndarray
    variance_draws: np.ndarray


def load_aggregated_data(raw_dir: Path) -> pd.DataFrame:
    """Load the available plant CSVs and aggregate inverter power by timestamp."""
    generation_files = sorted(raw_dir.glob("Plant_*_Generation_Data.csv"))
    plant_numbers = []
    for path in generation_files:
        match = re.fullmatch(r"Plant_(\d+)_Generation_Data\.csv", path.name)
        if match:
            plant_numbers.append(int(match.group(1)))
    if not plant_numbers:
        raise FileNotFoundError(
            f"Aucun fichier Plant_*_Generation_Data.csv trouvé dans {raw_dir}."
        )

    plants = [load_plant_data(raw_dir, number) for number in plant_numbers]
    data = pd.concat(plants, ignore_index=True)
    return (
        data.groupby(["PLANT_ID", "DATE_TIME"], as_index=False)
        .agg(
            AC_POWER=("AC_POWER", "sum"),
            IRRADIATION=("IRRADIATION", "mean"),
            AMBIENT_TEMPERATURE=("AMBIENT_TEMPERATURE", "mean"),
            MODULE_TEMPERATURE=("MODULE_TEMPERATURE", "mean"),
        )
        .sort_values(["PLANT_ID", "DATE_TIME"])
        .reset_index(drop=True)
    )


def build_next_step_frame(plant_data: pd.DataFrame) -> pd.DataFrame:
    """Create one-step-ahead rows using only information available at time t."""
    required = {
        "PLANT_ID",
        "DATE_TIME",
        "AC_POWER",
        "IRRADIATION",
        "AMBIENT_TEMPERATURE",
        "MODULE_TEMPERATURE",
    }
    missing = required - set(plant_data.columns)
    if missing:
        raise ValueError(f"Colonnes requises absentes : {', '.join(sorted(missing))}")

    rows = plant_data.sort_values(["PLANT_ID", "DATE_TIME"]).copy()
    rows["previous_timestamp"] = rows.groupby("PLANT_ID")["DATE_TIME"].shift(1)
    rows["previous_irradiation"] = rows.groupby("PLANT_ID")["IRRADIATION"].shift(1)
    rows["next_timestamp"] = rows.groupby("PLANT_ID")["DATE_TIME"].shift(-1)
    rows["target_power"] = rows.groupby("PLANT_ID")["AC_POWER"].shift(-1)
    rows = rows.loc[
        (
            rows["next_timestamp"] - rows["DATE_TIME"]
            == pd.Timedelta(minutes=INTERVAL_MINUTES)
        )
        & (
            rows["DATE_TIME"] - rows["previous_timestamp"]
            == pd.Timedelta(minutes=INTERVAL_MINUTES)
        )
    ].copy()

    hour = rows["DATE_TIME"].dt.hour + rows["DATE_TIME"].dt.minute / 60
    rows["log_current_power"] = np.log1p(rows["AC_POWER"].clip(lower=0))
    rows["irradiation_change"] = (
        rows["IRRADIATION"] - rows["previous_irradiation"]
    )
    rows["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    rows["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    rows = rows.rename(
        columns={
            "IRRADIATION": "irradiation",
            "AMBIENT_TEMPERATURE": "ambient_temperature",
            "MODULE_TEMPERATURE": "module_temperature",
            "AC_POWER": "current_power",
        }
    )
    rows = rows.replace([np.inf, -np.inf], np.nan)
    return rows.dropna(subset=[*FEATURE_COLUMNS, "target_power"]).reset_index(drop=True)


def chronological_split(
    frame: pd.DataFrame, train_fraction: float = 0.7
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split on a shared timestamp boundary so no plant leaks into the test period."""
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction doit être strictement compris entre 0 et 1.")
    timestamps = np.sort(frame["DATE_TIME"].dropna().unique())
    split_index = int(len(timestamps) * train_fraction)
    if split_index < 1 or split_index >= len(timestamps):
        raise ValueError("Pas assez d'horodatages pour créer les ensembles train/test.")
    boundary = timestamps[split_index]
    train = frame.loc[frame["DATE_TIME"] < boundary].copy()
    test = frame.loc[frame["DATE_TIME"] >= boundary].copy()
    if train.empty or test.empty:
        raise ValueError("Le découpage chronologique a produit un ensemble vide.")
    return train, test


def fit_gibbs_regression(
    train: pd.DataFrame,
    *,
    draws: int = 2000,
    burn_in: int = 1000,
    seed: int = 42,
) -> GibbsPosterior:
    """Sample a Normal-Inverse-Gamma Bayesian linear regression with Gibbs."""
    if draws < 1 or burn_in < 0:
        raise ValueError("draws doit être positif et burn_in ne peut pas être négatif.")
    if len(train) <= len(FEATURE_COLUMNS) + 1:
        raise ValueError("Il faut davantage d'observations d'entraînement.")

    features = train.loc[:, FEATURE_COLUMNS].to_numpy(dtype=float)
    target = (
        np.log1p(train["target_power"].clip(lower=0).to_numpy(dtype=float))
        - np.log1p(train["current_power"].clip(lower=0).to_numpy(dtype=float))
    )
    if not np.isfinite(features).all() or not np.isfinite(target).all():
        raise ValueError("Les données d'entraînement contiennent des valeurs non finies.")

    feature_means = features.mean(axis=0)
    feature_scales = features.std(axis=0)
    feature_scales[feature_scales == 0] = 1.0
    target_mean = float(target.mean())
    target_scale = float(target.std())
    if target_scale == 0:
        target_scale = 1.0

    standardized_features = (features - feature_means) / feature_scales
    design = np.column_stack(
        [np.ones(len(train)), standardized_features]
    )
    standardized_target = (target - target_mean) / target_scale

    parameter_count = design.shape[1]
    prior_covariance = np.eye(parameter_count) * 25.0
    prior_precision = np.linalg.inv(prior_covariance)
    posterior_precision = prior_precision + design.T @ design
    posterior_covariance = np.linalg.inv(posterior_precision)
    posterior_mean = posterior_covariance @ (design.T @ standardized_target)

    prior_shape = 2.0
    prior_scale = 1.0
    posterior_shape = prior_shape + len(train) / 2
    posterior_scale = prior_scale + 0.5 * (
        standardized_target @ standardized_target
        - posterior_mean @ posterior_precision @ posterior_mean
    )
    posterior_scale = max(float(posterior_scale), np.finfo(float).tiny)

    covariance_cholesky = np.linalg.cholesky(posterior_covariance)
    rng = np.random.default_rng(seed)
    beta = posterior_mean.copy()
    variance = posterior_scale / max(posterior_shape - 1, 1)
    beta_draws = np.empty((draws, parameter_count))
    variance_draws = np.empty(draws)
    conditional_shape = prior_shape + (len(train) + parameter_count) / 2

    for iteration in range(draws + burn_in):
        beta = posterior_mean + (
            covariance_cholesky @ rng.standard_normal(parameter_count)
        ) * np.sqrt(variance)
        residual = standardized_target - design @ beta
        prior_deviation = beta
        conditional_scale = prior_scale + 0.5 * (
            residual @ residual
            + prior_deviation @ prior_precision @ prior_deviation
        )
        variance = 1 / rng.gamma(
            shape=conditional_shape, scale=1 / conditional_scale
        )
        if iteration >= burn_in:
            sample_index = iteration - burn_in
            beta_draws[sample_index] = beta
            variance_draws[sample_index] = variance

    return GibbsPosterior(
        feature_means=feature_means,
        feature_scales=feature_scales,
        target_mean=target_mean,
        target_scale=target_scale,
        beta_draws=beta_draws,
        variance_draws=variance_draws,
    )


def predict_posterior(
    posterior: GibbsPosterior,
    rows: pd.DataFrame,
    *,
    seed: int,
    chunk_size: int = 256,
) -> pd.DataFrame:
    """Return posterior predictive medians and 95% intervals in power units."""
    if rows.empty:
        return pd.DataFrame(
            columns=["prediction", "lower_95", "upper_95"], index=rows.index
        )
    features = rows.loc[:, FEATURE_COLUMNS].to_numpy(dtype=float)
    standardized_features = (
        features - posterior.feature_means
    ) / posterior.feature_scales
    design = np.column_stack([np.ones(len(rows)), standardized_features])
    rng = np.random.default_rng(seed)
    predictions = np.empty(len(rows))
    lower = np.empty(len(rows))
    upper = np.empty(len(rows))
    draw_scale = np.sqrt(posterior.variance_draws)

    for start in range(0, len(rows), chunk_size):
        stop = min(start + chunk_size, len(rows))
        mean = design[start:stop] @ posterior.beta_draws.T
        predictive = mean + rng.standard_normal(mean.shape) * draw_scale
        log_power = (
            np.log1p(rows["current_power"].iloc[start:stop].clip(lower=0).to_numpy())[
                :, None
            ]
            + posterior.target_mean
            + posterior.target_scale * predictive
        )
        power = np.maximum(0, np.expm1(np.clip(log_power, -50, 50)))
        predictions[start:stop] = np.median(power, axis=1)
        lower[start:stop] = np.quantile(power, 0.025, axis=1)
        upper[start:stop] = np.quantile(power, 0.975, axis=1)

    return pd.DataFrame(
        {"prediction": predictions, "lower_95": lower, "upper_95": upper},
        index=rows.index,
    )


def _regression_metrics(rows: pd.DataFrame) -> dict[str, float | int | None]:
    if rows.empty:
        return {
            "samples": 0,
            "bayesian_mae": None,
            "bayesian_rmse": None,
            "bayesian_95_interval_coverage": None,
            "bayesian_95_interval_mean_width": None,
            "persistence_mae": None,
            "persistence_rmse": None,
        }
    actual = rows["actual_power"].to_numpy()
    predicted = rows["bayesian_prediction"].to_numpy()
    persistence = rows["persistence_prediction"].to_numpy()
    errors = actual - predicted
    persistence_errors = actual - persistence
    return {
        "samples": int(len(rows)),
        "bayesian_mae": float(np.mean(np.abs(errors))),
        "bayesian_rmse": float(np.sqrt(np.mean(errors**2))),
        "bayesian_95_interval_coverage": float(
            np.mean(
                (actual >= rows["lower_95"].to_numpy())
                & (actual <= rows["upper_95"].to_numpy())
            )
        ),
        "bayesian_95_interval_mean_width": float(
            np.mean(rows["upper_95"] - rows["lower_95"])
        ),
        "persistence_mae": float(np.mean(np.abs(persistence_errors))),
        "persistence_rmse": float(np.sqrt(np.mean(persistence_errors**2))),
    }


def _save_forecast_plot(forecasts: pd.DataFrame, output_path: Path) -> None:
    figure, axis = plt.subplots(figsize=(12, 5))
    axis.plot(
        forecasts["next_timestamp"],
        forecasts["actual_power"],
        label="Production réelle à t+15 min",
        color="black",
        linewidth=1,
    )
    axis.plot(
        forecasts["next_timestamp"],
        forecasts["bayesian_prediction"],
        label="Médiane prédictive bayésienne",
        color="tab:blue",
        linewidth=1,
    )
    axis.fill_between(
        forecasts["next_timestamp"],
        forecasts["lower_95"],
        forecasts["upper_95"],
        label="Intervalle prédictif à 95 %",
        color="tab:blue",
        alpha=0.18,
    )
    axis.plot(
        forecasts["next_timestamp"],
        forecasts["persistence_prediction"],
        label="Baseline de persistance",
        color="tab:orange",
        alpha=0.7,
        linewidth=0.8,
    )
    axis.set(
        title=f"Prévision bayésienne de production - centrale {forecasts['plant_id'].iloc[0]}",
        xlabel="Horodatage de la production prévue",
        ylabel="AC_POWER (unité du jeu source)",
    )
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def run_forecast(
    raw_dir: Path,
    output_dir: Path,
    *,
    draws: int = 2000,
    burn_in: int = 1000,
    seed: int = 42,
) -> dict[str, object]:
    aggregate = load_aggregated_data(raw_dir)
    frame = build_next_step_frame(aggregate)
    train, test = chronological_split(frame)
    train_daylight = train.loc[train["irradiation"] >= 0.1]
    test_daylight = test.loc[test["irradiation"] >= 0.1]
    test_results = []

    for plant_id, plant_test in test_daylight.groupby("PLANT_ID", sort=True):
        plant_train = train_daylight.loc[train_daylight["PLANT_ID"] == plant_id]
        if plant_train.empty:
            raise ValueError(
                f"Aucune donnée d'entraînement de jour pour la centrale {plant_id}."
            )
        posterior = fit_gibbs_regression(
            plant_train,
            draws=draws,
            burn_in=burn_in,
            seed=seed + int(plant_id),
        )
        predicted = predict_posterior(
            posterior,
            plant_test,
            seed=seed + int(plant_id) + 100_000,
        )
        result = plant_test[
            [
                "PLANT_ID",
                "DATE_TIME",
                "next_timestamp",
                "current_power",
                "target_power",
                "irradiation",
            ]
        ].copy()
        result = result.rename(
            columns={
                "PLANT_ID": "plant_id",
                "target_power": "actual_power",
                "current_power": "persistence_prediction",
            }
        )
        result["bayesian_prediction"] = predicted["prediction"]
        result["lower_95"] = predicted["lower_95"]
        result["upper_95"] = predicted["upper_95"]
        result["split"] = "test"
        test_results.append(result)

    forecasts = pd.concat(test_results, ignore_index=True).sort_values(
        ["plant_id", "next_timestamp"]
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    forecasts.to_csv(output_dir / "bayesian_forecasts.csv", index=False)
    for plant_id, plant_forecasts in forecasts.groupby("plant_id", sort=True):
        _save_forecast_plot(
            plant_forecasts,
            output_dir / f"plant_{plant_id}_bayesian_forecast.png",
        )

    metrics: dict[str, object] = {
        "model": "Daylight Bayesian linear regression with Normal-Inverse-Gamma prior",
        "sampler": "Gibbs",
        "target": "daylight aggregate AC_POWER at t+15 minutes",
        "daylight_filter": "irradiation at prediction time >= 0.1",
        "features_at_prediction_time": list(FEATURE_COLUMNS),
        "train_samples_daylight": int(len(train_daylight)),
        "test_samples_daylight": int(len(test_daylight)),
        "train_end": train["DATE_TIME"].max().isoformat(),
        "test_start": test["DATE_TIME"].min().isoformat(),
        "test_end": test["next_timestamp"].max().isoformat(),
        "gibbs_draws_per_plant": draws,
        "burn_in_per_plant": burn_in,
        "daylight_test_metrics": _regression_metrics(forecasts),
        "limitations": [
            "The public source data covers about 34 days and two plants in India.",
            "This is a daylight one-step-ahead estimate using current weather, not a long-horizon forecast.",
            "A Gaussian regression on log-power changes is a simple baseline, not a validated operational model.",
            "Predictive interval coverage is measured on the held-out period and may be miscalibrated.",
        ],
    }
    with (output_dir / "bayesian_metrics.json").open("w", encoding="utf-8") as file:
        json.dump(metrics, file, ensure_ascii=False, indent=2)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prévision bayésienne de la production solaire à 15 minutes."
    )
    parser.add_argument(
        "--data-dir", type=Path, default=SOLARWATCH_ROOT / "data" / "raw"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=PROJECT_DIR / "results" / "python"
    )
    parser.add_argument("--draws", type=int, default=2000)
    parser.add_argument("--burn-in", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    result = run_forecast(
        args.data_dir,
        args.output_dir,
        draws=args.draws,
        burn_in=args.burn_in,
        seed=args.seed,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
