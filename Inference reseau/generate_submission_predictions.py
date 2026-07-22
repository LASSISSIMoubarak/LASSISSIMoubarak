import os
import zipfile
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LassoCV, ElasticNetCV
from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
)
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.feature_selection import mutual_info_regression
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from scipy.spatial.distance import pdist, squareform
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor

ROOT = r"c:/Users/lassi/projet/Inference reseau"
os.chdir(ROOT)


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    imp = SimpleImputer(strategy="median")
    X = imp.fit_transform(df)
    X = StandardScaler().fit_transform(X)
    return pd.DataFrame(X, columns=df.columns, index=df.index)


def normalize(values: np.ndarray) -> np.ndarray:
    values = np.nan_to_num(np.asarray(values, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
    if values.size == 0:
        return values
    if values.max() <= values.min():
        return np.zeros_like(values)
    return (values - values.min()) / (values.max() - values.min())


def partial_correlation(x: np.ndarray, y: np.ndarray, controls: pd.DataFrame) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = ~(np.isnan(x) | np.isnan(y))
    if controls is not None:
        controls = controls.loc[~np.isnan(x) & ~np.isnan(y)]
        x = x[mask]
        y = y[mask]
        if len(controls) == 0 or controls.shape[1] == 0:
            return 0.0
        Z = np.column_stack([np.ones(len(x)), controls.to_numpy(dtype=float)])
        beta_x = np.linalg.lstsq(Z, x, rcond=None)[0]
        beta_y = np.linalg.lstsq(Z, y, rcond=None)[0]
        rx = x - Z @ beta_x
        ry = y - Z @ beta_y
        if np.std(rx) < 1e-12 or np.std(ry) < 1e-12:
            return 0.0
        corr = np.corrcoef(rx, ry)[0, 1]
        return 0.0 if not np.isfinite(corr) else abs(float(corr))
    if np.std(x) < 1e-12 or np.std(y) < 1e-12:
        return 0.0
    corr = np.corrcoef(x, y)[0, 1]
    return 0.0 if not np.isfinite(corr) else abs(float(corr))


def distance_correlation(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = ~(np.isnan(x) | np.isnan(y))
    x = x[mask]
    y = y[mask]
    if len(x) < 4 or np.std(x) < 1e-12 or np.std(y) < 1e-12:
        return 0.0
    A = squareform(pdist(x.reshape(-1, 1)))
    B = squareform(pdist(y.reshape(-1, 1)))
    A = A - A.mean(axis=0)[None, :] - A.mean(axis=1)[:, None] + A.mean()
    B = B - B.mean(axis=0)[None, :] - B.mean(axis=1)[:, None] + B.mean()
    numerator = np.sqrt(np.sum(A * B))
    denominator = np.sqrt(np.sum(A * A) * np.sum(B * B))
    if denominator < 1e-12:
        return 0.0
    return float(numerator / denominator)


def build_models():
    return [
        ("lasso", LassoCV(cv=3, alphas=np.logspace(-4, 1, 40), random_state=0, n_jobs=-1, max_iter=50000)),
        ("elastic", ElasticNetCV(cv=3, l1_ratio=[0.1, 0.3, 0.5, 0.7, 0.9], random_state=0, n_jobs=-1, max_iter=50000)),
        (
            "rf",
            RandomForestRegressor(
                n_estimators=250,
                max_features="sqrt",
                min_samples_leaf=2,
                random_state=0,
                n_jobs=-1,
            ),
        ),
        (
            "extra",
            ExtraTreesRegressor(
                n_estimators=300,
                max_features="sqrt",
                min_samples_leaf=1,
                random_state=0,
                n_jobs=-1,
            ),
        ),
        (
            "gbm",
            GradientBoostingRegressor(
                n_estimators=180,
                learning_rate=0.05,
                max_depth=3,
                random_state=0,
            ),
        ),
        (
            "hgb",
            HistGradientBoostingRegressor(
                learning_rate=0.05,
                max_depth=4,
                max_iter=250,
                random_state=0,
            ),
        ),
        (
            "xgb",
            XGBRegressor(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=4,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_lambda=1.0,
                random_state=0,
                n_jobs=-1,
                eval_metric="rmse",
            ),
        ),
        (
            "lgbm",
            LGBMRegressor(
                n_estimators=250,
                learning_rate=0.05,
                num_leaves=31,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=0,
                n_jobs=-1,
                verbosity=-1,
            ),
        ),
        (
            "catboost",
            CatBoostRegressor(
                iterations=250,
                learning_rate=0.05,
                depth=5,
                loss_function="RMSE",
                random_seed=0,
                verbose=False,
            ),
        ),
        ("knn", KNeighborsRegressor(n_neighbors=5, weights="distance")),
        (
            "mlp",
            MLPRegressor(
                hidden_layer_sizes=(64, 32),
                activation="relu",
                alpha=1e-4,
                learning_rate_init=0.001,
                max_iter=800,
                random_state=0,
            ),
        ),
    ]


def get_importance(model, X: pd.DataFrame, y: np.ndarray) -> np.ndarray:
    if hasattr(model, "coef_"):
        importance = np.abs(model.coef_)
    elif hasattr(model, "feature_importances_"):
        importance = np.abs(model.feature_importances_)
    else:
        perm = permutation_importance(
            model,
            X,
            y,
            n_repeats=8,
            random_state=0,
            scoring="r2",
            n_jobs=-1,
        )
        importance = perm.importances_mean
    return normalize(np.nan_to_num(np.asarray(importance, dtype=float), nan=0.0, posinf=0.0, neginf=0.0))


def model_weight(model, X: pd.DataFrame, y: np.ndarray) -> float:
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.25, random_state=0)
    model.fit(X_train, y_train)
    pred = model.predict(X_val)
    score = r2_score(y_val, pred)
    if not np.isfinite(score):
        return 0.0
    return max(0.0, float(score))


def make_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = preprocess(df)
    rows = []

    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].to_numpy(dtype=float)

        weights = []
        importances = []

        for name, model in build_models():
            weight = model_weight(model, X, y)
            if weight <= 0.0:
                continue
            model.fit(X, y)
            imp = get_importance(model, X, y)
            weights.append(max(0.05, weight))
            importances.append(imp)

        if importances:
            combined_model_scores = np.zeros(X.shape[1], dtype=float)
            total_weight = 0.0
            for weight, imp in zip(weights, importances):
                combined_model_scores += weight * imp
                total_weight += weight
            combined_model_scores = normalize(combined_model_scores / total_weight if total_weight > 0 else np.ones(X.shape[1]))
        else:
            combined_model_scores = np.ones(X.shape[1], dtype=float)
            combined_model_scores = normalize(combined_model_scores)

        stability_scores = np.zeros(X.shape[1], dtype=float)
        if importances:
            top_k = max(2, int(np.ceil(0.25 * X.shape[1])))
            for imp in importances:
                top_idx = np.argsort(imp)[-top_k:]
                stability_scores[top_idx] += 1.0
            stability_scores = normalize(stability_scores / max(1, len(importances)))

        pair_scores = []
        for source in X.columns:
            x = df[source].to_numpy(dtype=float)
            mask = ~(np.isnan(x) | np.isnan(y))
            if mask.sum() < 4:
                corr = 0.0
                spearman = 0.0
                mi = 0.0
                partial = 0.0
                dcor = 0.0
            else:
                xr = x[mask]
                yr = y[mask]
                corr = abs(np.corrcoef(xr, yr)[0, 1]) if np.std(xr) > 0 and np.std(yr) > 0 else 0.0
                xr_rank = pd.Series(xr).rank(method="average").to_numpy(dtype=float)
                yr_rank = pd.Series(yr).rank(method="average").to_numpy(dtype=float)
                spearman = abs(np.corrcoef(xr_rank, yr_rank)[0, 1]) if np.std(xr_rank) > 0 and np.std(yr_rank) > 0 else 0.0
                mi = mutual_info_regression(xr.reshape(-1, 1), yr, random_state=0)[0]
                mi = min(1.0, float(mi / (np.log(len(yr)) + 1e-12)))
                control_df = X.drop(columns=[source]).loc[mask]
                partial = partial_correlation(xr, yr, control_df)
                dcor = distance_correlation(xr, yr)
            pair_scores.append(0.25 * corr + 0.15 * spearman + 0.15 * mi + 0.2 * partial + 0.25 * dcor)

        pair_scores = normalize(np.array(pair_scores))
        combined = 0.55 * combined_model_scores + 0.25 * pair_scores + 0.2 * stability_scores
        combined = normalize(combined)

        for name, score in zip(X.columns, combined):
            rows.append((name, target, float(score)))

    pred = pd.DataFrame(rows, columns=["Cause", "Effect", "Score"])
    pred = pred.sort_values(["Score", "Cause", "Effect"], ascending=[False, True, True])
    pred = pred.reset_index(drop=True)
    return pred


csv_paths = []

for g in range(1, 6):
    data = pd.read_csv(f"data_train/data{g}.csv")
    pred = make_scores(data)
    csv_name = f"predictions_network{g}.csv"
    pred.to_csv(csv_name, index=False)
    csv_paths.append(csv_name)
    print(f"generated {csv_name} with {len(pred)} rows")

archive_path = os.path.join(ROOT, "prediction.zip")
with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for csv_name in csv_paths:
        full_path = os.path.join(ROOT, csv_name)
        zf.write(full_path, arcname=csv_name)

print(f"created {archive_path}")
