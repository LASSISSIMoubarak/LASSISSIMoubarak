import os
import zipfile
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LassoCV, ElasticNetCV, Lasso
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.feature_selection import mutual_info_regression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

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


def safe_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    score = r2_score(y_true, y_pred)
    if not np.isfinite(score):
        return 0.0
    return max(0.0, float(score))


def importance_from_model(model, X: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "coef_"):
        raw = np.abs(np.asarray(model.coef_, dtype=float))
    else:
        raw = np.abs(np.asarray(model.feature_importances_, dtype=float))
    return normalize(np.nan_to_num(raw, nan=0.0, posinf=0.0, neginf=0.0))


def make_scores(df: pd.DataFrame, top_k: int = None) -> pd.DataFrame:
    df = preprocess(df)
    rows = []

    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].to_numpy(dtype=float)
        is_large_graph = X.shape[1] > 60

        if is_large_graph:
            models = [
                ("lasso_fast", Lasso(alpha=0.01, max_iter=50000, random_state=0), 0.35),
                ("extra_fast", ExtraTreesRegressor(n_estimators=90, max_features="sqrt", min_samples_leaf=1, random_state=0, n_jobs=1), 0.65),
            ]
        else:
            models = [
                ("lasso", LassoCV(cv=3, alphas=np.logspace(-4, 1, 40), random_state=0, n_jobs=1, max_iter=50000), None),
                ("elastic", ElasticNetCV(cv=3, l1_ratio=[0.2, 0.5, 0.8], random_state=0, n_jobs=1, max_iter=50000), None),
                ("rf", RandomForestRegressor(n_estimators=140, max_features="sqrt", min_samples_leaf=2, random_state=0, n_jobs=1), None),
                ("extra", ExtraTreesRegressor(n_estimators=180, max_features="sqrt", min_samples_leaf=1, random_state=0, n_jobs=1), None),
                ("gbm", GradientBoostingRegressor(n_estimators=120, learning_rate=0.05, max_depth=3, random_state=0), None),
            ]

        if not is_large_graph:
            X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.25, random_state=0)

        model_weights = []
        model_importances = []
        for _, model, fixed_weight in models:
            if is_large_graph:
                weight = fixed_weight
            else:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_val)
                weight = 0.05 + safe_r2(y_val, y_pred)
            model.fit(X, y)
            imp = importance_from_model(model, X)

            model_weights.append(weight)
            model_importances.append(imp)

        weighted_model_score = np.zeros(X.shape[1], dtype=float)
        total_weight = float(np.sum(model_weights))
        for w, imp in zip(model_weights, model_importances):
            weighted_model_score += w * imp
        weighted_model_score = normalize(weighted_model_score / (total_weight + 1e-12))

        top_q = max(2, int(np.ceil(0.2 * X.shape[1])))
        stability = np.zeros(X.shape[1], dtype=float)
        for imp in model_importances:
            idx = np.argsort(imp)[-top_q:]
            stability[idx] += 1.0
        stability = normalize(stability / len(model_importances))

        use_fast_pair = is_large_graph
        pair_scores = []
        for source in X.columns:
            x = df[source].to_numpy(dtype=float)
            mask = ~(np.isnan(x) | np.isnan(y))
            if mask.sum() < 4:
                corr = 0.0
                spearman = 0.0
                mi = 0.0
            else:
                xr = x[mask]
                yr = y[mask]
                corr = abs(np.corrcoef(xr, yr)[0, 1]) if np.std(xr) > 0 and np.std(yr) > 0 else 0.0
                xr_rank = pd.Series(xr).rank(method="average").to_numpy(dtype=float)
                yr_rank = pd.Series(yr).rank(method="average").to_numpy(dtype=float)
                spearman = abs(np.corrcoef(xr_rank, yr_rank)[0, 1]) if np.std(xr_rank) > 0 and np.std(yr_rank) > 0 else 0.0
                if use_fast_pair:
                    mi = 0.0
                else:
                    mi = mutual_info_regression(xr.reshape(-1, 1), yr, random_state=0)[0]
                    mi = min(1.0, float(mi / (np.log(len(yr)) + 1e-12)))
            if use_fast_pair:
                pair_scores.append(0.6 * corr + 0.4 * spearman)
            else:
                pair_scores.append(0.45 * corr + 0.25 * spearman + 0.30 * mi)

        pair_scores = normalize(np.array(pair_scores))
        combined = 0.6 * weighted_model_score + 0.25 * pair_scores + 0.15 * stability
        combined = normalize(combined)

        for name, score in zip(X.columns, combined):
            rows.append((name, target, float(score)))

    pred = pd.DataFrame(rows, columns=["Cause", "Effect", "Score"])
    pred = pred.sort_values(["Score", "Cause", "Effect"], ascending=[False, True, True])
    pred = pred.reset_index(drop=True)

    if top_k is not None:
        pred = pred.head(top_k)

    return pred


csv_paths = []

for g in range(1, 6):
    data = pd.read_csv(f"data_train/data{g}.csv")
    data = data.copy()
    data.columns = [f"V{i}" for i in range(data.shape[1])]
    pred = make_scores(data)
    pred = pred.sort_values(["Score", "Cause", "Effect"], ascending=[False, True, True]).reset_index(drop=True)
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
