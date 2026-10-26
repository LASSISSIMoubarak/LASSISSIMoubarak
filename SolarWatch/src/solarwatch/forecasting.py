from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler

SEQUENCE_LENGTH = 8
FORECAST_FEATURES = [
    "AC_POWER",
    "PEER_MEDIAN_AC_POWER",
    "IRRADIATION",
    "AMBIENT_TEMPERATURE",
    "MODULE_TEMPERATURE",
]


def train_lstm_forecast(
    data: pd.DataFrame,
    *,
    epochs: int = 8,
    batch_size: int = 512,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Train a next-step LSTM on earlier timestamps and evaluate a later holdout."""
    try:
        import torch
        from torch import nn
    except ImportError as exc:
        raise ImportError(
            "PyTorch is required for the LSTM component. Install it with "
            "`python -m pip install -e \".[dev,deep-learning]\"`."
        ) from exc

    torch.manual_seed(42)
    torch.set_num_threads(1)
    if data.empty:
        raise ValueError("Cannot train the LSTM on an empty dataset.")
    missing = set(FORECAST_FEATURES + ["PLANT_ID", "SOURCE_KEY", "DATE_TIME"]) - set(
        data.columns
    )
    if missing:
        raise ValueError(f"LSTM input columns missing: {', '.join(sorted(missing))}")

    sequences: list[np.ndarray] = []
    targets: list[float] = []
    peer_persistence: list[float] = []
    timestamps: list[pd.Timestamp] = []
    plants: list[int] = []
    inverters: list[str] = []

    for (plant_id, inverter_id), inverter_data in data.groupby(
        ["PLANT_ID", "SOURCE_KEY"], sort=True
    ):
        inverter_data = inverter_data.sort_values("DATE_TIME").reset_index(drop=True)
        values = inverter_data[FORECAST_FEATURES].to_numpy(dtype=np.float32)
        times = inverter_data["DATE_TIME"].to_numpy()
        for index in range(SEQUENCE_LENGTH, len(inverter_data)):
            if (
                pd.Timestamp(times[index]) - pd.Timestamp(times[index - 1])
            ).total_seconds() > 20 * 60:
                continue
            start = index - SEQUENCE_LENGTH
            if any(
                (pd.Timestamp(times[position]) - pd.Timestamp(times[position - 1])).total_seconds()
                > 20 * 60
                for position in range(start + 1, index + 1)
            ):
                continue
            if not np.isfinite(values[start : index + 1]).all():
                continue
            sequences.append(values[start:index])
            targets.append(float(values[index, 0]))
            peer_persistence.append(float(values[index - 1, 1]))
            timestamps.append(pd.Timestamp(times[index]))
            plants.append(int(plant_id))
            inverters.append(str(inverter_id))

    if not sequences:
        raise ValueError("No contiguous finite sequences are available for LSTM training.")
    x = np.stack(sequences)
    y = np.asarray(targets, dtype=np.float32)
    peer_baseline = np.asarray(peer_persistence, dtype=np.float32)
    time_index = pd.DatetimeIndex(timestamps)
    plant_ids = np.asarray(plants)

    fit_mask = np.zeros(len(y), dtype=bool)
    calibration_mask = np.zeros(len(y), dtype=bool)
    test_mask = np.zeros(len(y), dtype=bool)
    for plant_id in np.unique(plant_ids):
        plant_timestamps = time_index[plant_ids == plant_id].unique().sort_values()
        if len(plant_timestamps) < 10:
            raise ValueError(f"Not enough timestamps to split plant {plant_id}.")
        split = int(len(plant_timestamps) * 0.7)
        training_timestamps = plant_timestamps[:split]
        fit_split = max(1, int(len(training_timestamps) * 0.8))
        fit_cutoff = training_timestamps[fit_split - 1]
        training_cutoff = training_timestamps[-1]
        plant_mask = plant_ids == plant_id
        fit_mask |= plant_mask & (time_index <= fit_cutoff)
        calibration_mask |= (
            plant_mask
            & (time_index > fit_cutoff)
            & (time_index <= training_cutoff)
        )
        test_mask |= plant_mask & (time_index > training_cutoff)
    if not fit_mask.any() or not calibration_mask.any() or not test_mask.any():
        raise ValueError("The chronological LSTM fit/calibration/test split is empty.")

    x_scaler = StandardScaler().fit(x[fit_mask].reshape(-1, x.shape[-1]))
    y_scaler = StandardScaler().fit(y[fit_mask].reshape(-1, 1))
    x_scaled = x_scaler.transform(x.reshape(-1, x.shape[-1])).reshape(x.shape)
    y_scaled = y_scaler.transform(y.reshape(-1, 1)).ravel()

    class PowerLSTM(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.lstm = nn.LSTM(input_size=x.shape[-1], hidden_size=32, batch_first=True)
            self.output = nn.Linear(32, 1)

        def forward(self, sequence: torch.Tensor) -> torch.Tensor:
            encoded, _ = self.lstm(sequence)
            return self.output(encoded[:, -1, :]).squeeze(-1)

    model = PowerLSTM()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.003)
    loss_function = nn.MSELoss()
    train_x = torch.from_numpy(x_scaled[fit_mask].astype(np.float32))
    train_y = torch.from_numpy(y_scaled[fit_mask].astype(np.float32))
    generator = torch.Generator().manual_seed(42)

    model.train()
    for _ in range(epochs):
        order = torch.randperm(len(train_x), generator=generator)
        for batch_start in range(0, len(order), batch_size):
            indices = order[batch_start : batch_start + batch_size]
            optimizer.zero_grad()
            loss = loss_function(model(train_x[indices]), train_y[indices])
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        calibration_predictions_scaled = model(
            torch.from_numpy(x_scaled[calibration_mask].astype(np.float32))
        ).numpy()
        predictions_scaled = model(
            torch.from_numpy(x_scaled[test_mask].astype(np.float32))
        ).numpy()
    calibration_prediction = y_scaler.inverse_transform(
        calibration_predictions_scaled.reshape(-1, 1)
    ).ravel()
    prediction = y_scaler.inverse_transform(predictions_scaled.reshape(-1, 1)).ravel()
    y_test = y[test_mask]
    peer_test = peer_baseline[test_mask]
    lstm_mae = float(mean_absolute_error(y_test, prediction))
    peer_mae = float(mean_absolute_error(y_test, peer_test))
    residual_threshold = float(
        np.quantile(np.abs(y[calibration_mask] - calibration_prediction), 0.99)
    )
    test_absolute_error = np.abs(y_test - prediction)
    forecast_rows = pd.DataFrame(
        {
            "plant_id": plant_ids[test_mask],
            "inverter_id": np.asarray(inverters)[test_mask],
            "timestamp": time_index[test_mask],
            "actual_ac_power": y_test,
            "lstm_predicted_ac_power": prediction,
            "peer_persistence_baseline_ac_power": peer_test,
            "lstm_absolute_error": test_absolute_error,
            "lstm_anomaly_threshold": residual_threshold,
            "is_lstm_forecast_anomaly": test_absolute_error > residual_threshold,
            "peer_baseline_absolute_error": np.abs(y_test - peer_test),
        }
    )
    metrics: dict[str, Any] = {
        "model": "PyTorch LSTM (8 x 15-min history, 32 hidden units)",
        "train_fraction": 0.7,
        "sequence_length": SEQUENCE_LENGTH,
        "epochs": epochs,
        "fit_samples": int(fit_mask.sum()),
        "calibration_samples": int(calibration_mask.sum()),
        "test_samples": int(test_mask.sum()),
        "lstm_mae_ac_power": round(lstm_mae, 4),
        "lstm_rmse_ac_power": round(
            float(np.sqrt(mean_squared_error(y_test, prediction))), 4
        ),
        "calibration_residual_p99_threshold_ac_power": round(residual_threshold, 4),
        "anomalous_test_forecasts": int(
            (test_absolute_error > residual_threshold).sum()
        ),
        "peer_persistence_baseline_mae_ac_power": round(peer_mae, 4),
        "lstm_mae_improvement_vs_peer_baseline_pct": round(
            (peer_mae - lstm_mae) / peer_mae * 100 if peer_mae else 0.0,
            2,
        ),
        "evaluation": (
            "Chronological holdout. Forecast error measures power prediction only; "
            "it is not a fault-detection accuracy metric."
        ),
    }
    return forecast_rows, metrics
