import numpy as np
import pandas as pd

from bayesian_forecasting import (
    FEATURE_COLUMNS,
    build_next_step_frame,
    chronological_split,
    fit_gibbs_regression,
    predict_posterior,
)


def _synthetic_plant_data(rows=120):
    timestamps = pd.date_range("2020-05-15", periods=rows, freq="15min")
    irradiation = np.maximum(0, np.sin(np.arange(rows) / 24 * 2 * np.pi))
    power = 100 + 50 * irradiation + np.arange(rows) % 7
    return pd.DataFrame(
        {
            "PLANT_ID": 1,
            "DATE_TIME": timestamps,
            "AC_POWER": power,
            "IRRADIATION": irradiation,
            "AMBIENT_TEMPERATURE": 20 + irradiation,
            "MODULE_TEMPERATURE": 25 + 2 * irradiation,
        }
    )


def test_next_step_frame_drops_missing_intervals_and_uses_next_power():
    data = _synthetic_plant_data()
    data = data.drop(index=10).reset_index(drop=True)

    frame = build_next_step_frame(data)

    assert len(frame) == len(data) - 4
    row = frame.loc[frame["DATE_TIME"] == pd.Timestamp("2020-05-15 02:00")].iloc[0]
    assert row["next_timestamp"] == pd.Timestamp("2020-05-15 02:15")
    assert row["target_power"] == data.loc[
        data["DATE_TIME"] == pd.Timestamp("2020-05-15 02:15"), "AC_POWER"
    ].iloc[0]
    assert set(FEATURE_COLUMNS).issubset(frame.columns)


def test_chronological_split_keeps_all_plants_on_each_side_of_boundary():
    data = _synthetic_plant_data()
    second_plant = data.assign(PLANT_ID=2)
    frame = build_next_step_frame(pd.concat([data, second_plant], ignore_index=True))

    train, test = chronological_split(frame, train_fraction=0.7)

    assert train["DATE_TIME"].max() < test["DATE_TIME"].min()
    assert set(train["PLANT_ID"]) == {1, 2}
    assert set(test["PLANT_ID"]) == {1, 2}


def test_gibbs_sampler_produces_finite_predictions_and_intervals():
    frame = build_next_step_frame(_synthetic_plant_data())
    train, test = chronological_split(frame)
    posterior = fit_gibbs_regression(
        train, draws=80, burn_in=30, seed=7
    )

    predictions = predict_posterior(posterior, test, seed=8, chunk_size=16)

    assert posterior.beta_draws.shape[0] == 80
    assert np.isfinite(posterior.beta_draws).all()
    assert np.isfinite(posterior.variance_draws).all()
    assert (predictions["prediction"] >= 0).all()
    assert (predictions["lower_95"] <= predictions["prediction"]).all()
    assert (predictions["prediction"] <= predictions["upper_95"]).all()
