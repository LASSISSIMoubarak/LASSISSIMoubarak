import os
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LassoCV, ElasticNetCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

ROOT = r"c:/Users/lassi/projet/Inference reseau"
os.chdir(ROOT)


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    imp = SimpleImputer(strategy="median")
    X = imp.fit_transform(df)
    X = StandardScaler().fit_transform(X)
    return pd.DataFrame(X, columns=df.columns, index=df.index)


def build_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = preprocess(df)
    rows = []

    for target in df.columns:
        X = df.drop(columns=[target])
        y = df[target].values

        # Lasso CV
        lasso = LassoCV(cv=5, alphas=np.logspace(-4, 1, 80), random_state=0, n_jobs=-1, max_iter=50000)
        lasso.fit(X, y)
        lasso_scores = np.abs(lasso.coef_)
        lasso_scores = lasso_scores / (lasso_scores.max() + 1e-12)

        # Elastic Net CV
        enet = ElasticNetCV(cv=5, l1_ratio=[0.1, 0.3, 0.5, 0.7, 0.9], random_state=0, n_jobs=-1, max_iter=50000)
        enet.fit(X, y)
        enet_scores = np.abs(enet.coef_)
        enet_scores = enet_scores / (enet_scores.max() + 1e-12)

        # Random Forest importance
        rf = RandomForestRegressor(
            n_estimators=400,
            max_features="sqrt",
            min_samples_leaf=2,
            random_state=0,
            n_jobs=-1,
        )
        rf.fit(X, y)
        rf_scores = np.abs(rf.feature_importances_)
        rf_scores = rf_scores / (rf_scores.max() + 1e-12)

        # Gradient Boosting importance
        gbm = GradientBoostingRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=3,
            random_state=0,
        )
        gbm.fit(X, y)
        gbm_scores = np.abs(gbm.feature_importances_)
        gbm_scores = gbm_scores / (gbm_scores.max() + 1e-12)

        # Weighted ensemble
        ensemble = 0.45 * lasso_scores + 0.25 * enet_scores + 0.20 * rf_scores + 0.10 * gbm_scores

        for name, score in zip(X.columns, ensemble):
            rows.append((name, target, float(score)))

    pred = pd.DataFrame(rows, columns=["Cause", "Effect", "Score"])
    pred = pred.sort_values("Score", ascending=False)
    pred = pred.reset_index(drop=True)
    return pred


for g in range(1, 6):
    data = pd.read_csv(f"data_train/data{g}.csv")
    pred = build_scores(data)
    pred.to_csv(f"predictions_network{g}.csv", index=False)
    print(f"generated predictions_network{g}.csv with {len(pred)} rows")
