import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import make_scorer
from sksurv.metrics import concordance_index_censored, concordance_index_ipcw
from sksurv.util import Surv
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# CHARGEMENT DES DONNÉES
def load_processed_data(base_dir: Path):
    """Charge les données transformées"""
    data = pd.read_csv(base_dir / 'data' / 'processed' / 'Train_transformed_data.csv')
    # Séparer features et target
    target_cols = ['ID', 'OS_YEARS', 'OS_STATUS']
    feature_cols = [c for c in data.columns if c not in target_cols]
    X = data[feature_cols].values
    y_years = data['OS_YEARS'].values
    y_status = data['OS_STATUS'].values
    ids = data['ID'].values 
    return X, y_years, y_status, ids, feature_cols
#chargé les données de test
def load_test_data(base_dir: Path, feature_cols: list, imputer, scaler):
    """Charge et transforme les données de test"""
    clinical_test = pd.read_csv(base_dir / 'X_test_xzVefmA' / 'X_test' / 'clinical_test.csv')
    molecular_test = pd.read_csv(base_dir / 'X_test_xzVefmA' / 'X_test' / 'molecular_test.csv')
    return clinical_test, molecular_test

# =============================================================================
# MÉTRIQUES DE SURVIE
def concordance_index_ipcw_score(y_train_time, y_train_event, y_test_time, y_test_event, y_pred, tau=7):
    # Structured arrays pour sksurv
    y_train_surv = Surv.from_arrays(np.asarray(y_train_event).astype(bool), y_train_time)
    y_test_surv = Surv.from_arrays(np.asarray(y_test_event).astype(bool), y_test_time)
    return concordance_index_ipcw(y_train_surv, y_test_surv, y_pred, tau=tau)[0]
# =============================================================================
# VALIDATION CROISÉE PERSONNALISÉE
# =============================================================================

def cross_validate_survival(model, X, y_time, y_event, n_splits=5, random_state=42, use_ipcw=True, tau=7):
    """Validation croisée personnalisée pour les modèles de survie"""
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    scores = []
    
    for fold, (train_idx, val_idx) in enumerate(kf.split(X)):
        X_train, X_val = X[train_idx], X[val_idx]
        y_time_train, y_time_val = y_time[train_idx], y_time[val_idx]
        y_event_train, y_event_val = y_event[train_idx], y_event[val_idx]
        # Fit
        model.fit(X_train, y_time_train, y_event_train)
        
        # Predict risk scores
        y_pred = model.predict_risk(X_val)
    
        # Calculate IPCW ou classique
        if use_ipcw:
            c_idx = concordance_index_ipcw_score(
                y_time_train, y_event_train,
                y_time_val, y_event_val,
                y_pred, tau=tau
            )
        scores.append(c_idx)
    
    return {
        'scores': np.array(scores),
        'mean': np.mean(scores),
        'std': np.std(scores),
        'min': np.min(scores),
        'max': np.max(scores)
    }


# =============================================================================
# WRAPPERS POUR DIFFÉRENTS MODÈLES
class SurvivalModelWrapper:
    """Wrapper de base pour uniformiser l'interface des modèles"""
    
    def __init__(self, model, model_type='regression'):
        self.model = model
        self.model_type = model_type
        
    def fit(self, X, y_time, y_event):
        """Fit le modèle"""
        raise NotImplementedError
    def predict_risk(self, X):
        """Prédit le score de risque (plus élevé = plus de risque)"""
        raise NotImplementedError

# Regression Wrapper
class RegressionSurvivalWrapper(SurvivalModelWrapper):
    """Wrapper pour modèles de régression sklearn (Ridge, XGBoost, etc.)"""
    def fit(self, X, y_time, y_event):
        # Pour la régression, on prédit -OS_YEARS 
        self.model.fit(X, y_time)
        return self
        
    def predict_risk(self, X):
        # Risque = -temps prédit (temps court = risque élevé)
        return -self.model.predict(X)
# CoxPH Wrapper
class CoxWrapper(SurvivalModelWrapper):
    """Wrapper pour CoxPH de sksurv"""
    def fit(self, X, y_time, y_event):
        y = np.array([(bool(e), t) for e, t in zip(y_event, y_time)],
                     dtype=[('event', bool), ('time', float)])
        self.model.fit(X, y)
        return self
    def predict_risk(self, X):
        return self.model.predict(X)

#RSF Wrapper
class RSFWrapper(SurvivalModelWrapper):
    """Wrapper pour Random Survival Forest de sksurv"""
    
    def fit(self, X, y_time, y_event):
        y = np.array([(bool(e), t) for e, t in zip(y_event, y_time)],
                     dtype=[('event', bool), ('time', float)])
        self.model.fit(X, y)
        return self
        
    def predict_risk(self, X):
        return self.model.predict(X)

#GBSurvival Wrapper
class GBSurvivalWrapper(SurvivalModelWrapper):
    """Wrapper pour Gradient Boosting Survival de sksurv"""
    def fit(self, X, y_time, y_event):
        y = np.array([(bool(e), t) for e, t in zip(y_event, y_time)],
                     dtype=[('event', bool), ('time', float)])
        self.model.fit(X, y)
        return self
        
    def predict_risk(self, X):
        return self.model.predict(X)


# =============================================================================
# SAUVEGARDE DES RÉSULTATS

def save_submission(ids, risk_scores, output_path, filename='submission.csv'):
    """Sauvegarde les prédictions"""
    submission = pd.DataFrame({'ID': ids, 'risk_score': risk_scores})
    submission.to_csv(output_path / filename, index=False)
    print(f"Soumission sauvegardée: {output_path / filename}")
    return submission

def save_model_results(results_dict, output_path, filename='model_results.csv'):
    """Sauvegarde les résultats de tous les modèles"""
    df = pd.DataFrame(results_dict).T
    df.to_csv(output_path / filename)
    print(f"Résultats sauvegardés: {output_path / filename}")
    return df
# ==================================Fin===========================================