#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gene Network Inference - Final Production Model
===============================================

**Title:** Ensemble-Based Gene Network Inference using Regression Feature Importance

**Authors:** Machine Learning Project Team
**Date:** July 2026
**Challenge:** Codalab Gene Network Inference Competition

**Method:** 
Ensemble of ExtraTrees, GradientBoosting, Ridge, and Lasso regressors
using feature importance-based edge scoring.

**Performance:** AUPR = 0.33 (average across 5 networks)

**Reference Implementation:** Phase 9 V2 Hyperparameters

This script implements the complete pipeline from raw data to final predictions
and generates a submission-ready ZIP file.
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from zipfile import ZipFile

# Machine Learning Libraries
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso


class DataPreprocessor:
    """
    Handles data loading and preprocessing.
    
    Pipeline:
    1. Load CSV data
    2. Impute missing values (median strategy)
    3. Normalize with StandardScaler
    """
    
    def __init__(self, strategy='median'):
        """
        Initialize preprocessor.
        
        Args:
            strategy (str): Imputation strategy. Default: 'median'
        """
        self.imputer = SimpleImputer(strategy=strategy)
        self.scaler = StandardScaler()
    
    def load_and_preprocess(self, filepath):
        """
        Load CSV and apply preprocessing pipeline.
        
        Args:
            filepath (str): Path to data CSV file
            
        Returns:
            pd.DataFrame: Preprocessed data (normalized, no missing values)
        """
        # Load data
        df = pd.read_csv(filepath, index_col=0)
        
        # Impute missing values
        df_imputed = pd.DataFrame(
            self.imputer.fit_transform(df),
            columns=df.columns,
            index=df.index
        )
        
        # Normalize
        df_scaled = pd.DataFrame(
            self.scaler.fit_transform(df_imputed),
            columns=df.columns,
            index=df.index
        )
        
        return df_scaled


class EnsembleModel:
    """
    Ensemble model combining 4 regression models for edge inference.
    
    Models:
    - ExtraTrees: Captures complex non-linearities
    - GradientBoosting: Sequential boosting with regularization
    - Ridge: L2 regularization, stable on multicollinearity
    - Lasso: Feature selection via L1 penalty
    
    Combination: Weighted average of normalized feature importances
    """
    
    def __init__(self):
        """Initialize ensemble with optimized hyperparameters."""
        self.models = {}
        self._setup_models()
    
    def _setup_models(self):
        """Setup models with optimal hyperparameters (Phase 9 V2)."""
        
        # ExtraTrees: max_features='sqrt' critical improvement vs 'log2'
        self.models['et'] = ExtraTreesRegressor(
            n_estimators=400,
            max_features='sqrt',  # Key finding: sqrt > log2
            random_state=42,
            n_jobs=-1
        )
        
        # GradientBoosting: subsample=0.8 provides regularization
        self.models['gb'] = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            subsample=0.8,  # Regularization via subsampling
            random_state=42
        )
        
        # Ridge: Higher alpha for stronger regularization
        self.models['ridge'] = Ridge(alpha=5.0)  # vs 1.0 in baseline
        
        # Lasso: Lower alpha for less sparsity
        self.models['lasso'] = Lasso(
            alpha=0.005,  # vs 0.01 in baseline
            max_iter=10000
        )
    
    def train_for_target(self, X, y, model_name):
        """
        Train a single model for predicting target y.
        
        Args:
            X (pd.DataFrame): Features (other genes)
            y (np.array): Target variable (one gene)
            model_name (str): Name of model ('et', 'gb', 'ridge', 'lasso')
            
        Returns:
            Trained model instance
        """
        model = self.models[model_name]
        model.fit(X, y)
        return model
    
    def extract_importances(self, df):
        """
        Extract feature importances for all target genes.
        
        For each gene as target, train all 4 models and extract their
        importance scores. This creates an importance matrix for edge scoring.
        
        Args:
            df (pd.DataFrame): Preprocessed gene expression data
                              (samples x genes)
            
        Returns:
            dict: {model_name: {target_gene: importances_array}}
        """
        importances_dict = {}
        targets = df.columns.tolist()
        n_targets = len(targets)
        
        print(f"  Extracting feature importances for {n_targets} target genes...")
        
        for model_name in self.models.keys():
            importances_dict[model_name] = {}
            
            for target in targets:
                # Prepare X, y
                X = df.drop(columns=[target])
                y = df[target].values
                
                # Train and extract importances
                model = self.train_for_target(X, y, model_name)
                
                if hasattr(model, 'feature_importances_'):
                    # Tree-based models: ExtraTrees, GradientBoosting
                    importances = model.feature_importances_
                else:
                    # Linear models: Ridge, Lasso - use absolute coefficients
                    importances = np.abs(model.coef_)
                
                importances_dict[model_name][target] = importances
        
        return importances_dict
    
    def combine_predictions(self, importances_dict, targets, weights):
        """
        Combine predictions from 4 models using weighted averaging.
        
        Process:
        1. Normalize each model's importances per target (0-1 scale)
        2. Weighted combination: 40% ET, 30% GB, 20% Ridge, 10% Lasso
        3. Sort by score descending
        4. Format as (Cause, Effect, Score)
        
        Args:
            importances_dict (dict): Output from extract_importances()
            targets (list): Gene names (same order as used in training)
            weights (dict): Model weights {model_name: weight}
            
        Returns:
            pd.DataFrame: Edge scores (columns: Cause, Effect, Score)
        """
        results = []
        
        for target in targets:
            # Get importances from each model
            et_imp = importances_dict['et'][target]
            gb_imp = importances_dict['gb'][target]
            ridge_imp = importances_dict['ridge'][target]
            lasso_imp = importances_dict['lasso'][target]
            
            # Normalize per model to [0,1] range
            et_norm = et_imp / (et_imp.max() + 1e-10)
            gb_norm = gb_imp / (gb_imp.max() + 1e-10)
            ridge_norm = ridge_imp / (ridge_imp.max() + 1e-10)
            lasso_norm = lasso_imp / (lasso_imp.max() + 1e-10)
            
            # Weighted combination
            combined = (
                weights['et'] * et_norm +
                weights['gb'] * gb_norm +
                weights['ridge'] * ridge_norm +
                weights['lasso'] * lasso_norm
            )
            
            # Create edges: every other gene i as source to target
            source_genes = [t for t in targets if t != target]
            for source_idx, source in enumerate(source_genes):
                results.append({
                    'Cause': source,
                    'Effect': target,
                    'Score': combined[source_idx]
                })
        
        # Sort by score descending
        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values('Score', ascending=False).reset_index(drop=True)
        
        return df_results


def generate_network_predictions(network_id, data_dir='test_data', k_cutoff=320):
    """
    Generate predictions for a single network.
    
    Args:
        network_id (int): Network ID (1-5)
        data_dir (str): Directory containing data CSV files
        k_cutoff (int): Number of top edges to select
        
    Returns:
        pd.DataFrame: Top-K edge predictions
    """
    print(f"\n[Network {network_id}] Processing...")
    
    # Load and preprocess
    data_path = f"{data_dir}/data{network_id}.csv"
    preprocessor = DataPreprocessor()
    df = preprocessor.load_and_preprocess(data_path)
    print(f"  Data shape: {df.shape}")
    
    # Train ensemble
    ensemble = EnsembleModel()
    importances = ensemble.extract_importances(df)
    
    # Combine predictions
    weights = {'et': 0.4, 'gb': 0.3, 'ridge': 0.2, 'lasso': 0.1}
    df_preds = ensemble.combine_predictions(importances, df.columns.tolist(), weights)
    
    # Select top-K
    df_top_k = df_preds.head(k_cutoff)[['Cause', 'Effect', 'Score']]
    print(f"  Selected {len(df_top_k)} edges (K={k_cutoff})")
    print(f"  Score range: [{df_top_k['Score'].min():.4f}, {df_top_k['Score'].max():.4f}]")
    
    return df_top_k


def create_submission_zip(all_predictions, output_zip='prediction_submission_final.zip'):
    """
    Package predictions into submission-ready ZIP file.
    
    Args:
        all_predictions (dict): {network_id: df_predictions}
        output_zip (str): Output ZIP filename
        
    Returns:
        str: Path to created ZIP file
    """
    print(f"\nCreating submission ZIP: {output_zip}")
    
    with ZipFile(output_zip, 'w') as zf:
        for network_id in range(1, 6):
            if network_id not in all_predictions:
                raise ValueError(f"Network {network_id} predictions missing!")
            
            df_preds = all_predictions[network_id]
            
            # Write to CSV in ZIP
            csv_name = f"predictions_network{network_id}.csv"
            df_preds.to_csv(csv_name, index=False)
            zf.write(csv_name)
            os.remove(csv_name)
            
            print(f"  ✓ {csv_name} ({len(df_preds)} edges)")
    
    file_size_kb = os.path.getsize(output_zip) / 1024
    print(f"\n✓ Submission ZIP created: {output_zip} ({file_size_kb:.1f} KB)")
    
    return output_zip


def main():
    """Main execution pipeline."""
    
    print("\n" + "="*70)
    print("GENE NETWORK INFERENCE - FINAL SUBMISSION")
    print("="*70)
    print(f"""
Method: Ensemble-based regression feature importance
Models: ExtraTrees (40%) + GradientBoosting (30%) + Ridge (20%) + Lasso (10%)
Hyperparameters: Phase 9 V2 (optimized)
Expected AUPR: 0.33 (average across 5 networks)

K-cutoff: 320 edges per network
Data source: test_data/

Pipeline:
  1. Load training data
  2. Impute & normalize
  3. Train 4 models per target gene
  4. Extract feature importances
  5. Combine & normalize scores
  6. Select top-K edges
  7. Package into ZIP
""")
    
    print("-"*70)
    print("PROCESSING NETWORKS")
    print("-"*70)
    
    # Generate predictions for all networks
    all_predictions = {}
    for network_id in range(1, 6):
        df_top_k = generate_network_predictions(network_id, k_cutoff=320)
        all_predictions[network_id] = df_top_k
    
    # Create submission ZIP
    output_zip = create_submission_zip(all_predictions)
    
    print("\n" + "="*70)
    print("✓ SUBMISSION READY")
    print("="*70)
    print(f"""
Output file: {output_zip}

This ZIP contains:
  - predictions_network1.csv
  - predictions_network2.csv
  - predictions_network3.csv
  - predictions_network4.csv
  - predictions_network5.csv

Each CSV has columns: Cause, Effect, Score
Format ready for Codalab submission.

Next step: Upload to Codalab competition platform
""")
    
    return output_zip


if __name__ == '__main__':
    main()
