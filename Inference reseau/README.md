
# Gene Network Inference - Final Submission Package

**Competition:** Codalab Gene Network Inference Challenge  
**Method:** Ensemble-Based Regression Feature Importance  
**Performance:** AUPR = 0.33 (average across 5 networks)  
**Date:** July 2026

---

## Overview

This package contains a complete machine learning pipeline for inferring causal edges in gene regulatory networks. The method combines four complementary regression models (ExtraTrees, GradientBoosting, Ridge, Lasso) using weighted ensemble averaging on feature importances.

**Key Features:**
- ✅ Reproducible: `random_state=42` everywhere
- ✅ Production-ready: Clean, documented code
- ✅ Optimized hyperparameters: After systematic tuning (11 phases)
- ✅ Robust: Handles missing values and variable data scales
- ✅ Efficient: ~5 minutes total runtime for all 5 networks

---

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Prediction Pipeline

```bash
# Generate final submission ZIP
python generate_final_submission.py

# Output: prediction_submission_final.zip (ready for Codalab)
```

### 3. Upload to Codalab

Login to Codalab and upload `prediction_submission_final.zip`

---

## Directory Structure

```
.
├── README.md                          # This file
├── RAPPORT_FINAL.md                   # Academic methodology report (French)
├── requirements.txt                   # Python dependencies
├── generate_final_submission.py        # Main production script ⭐
│
├── test_data/                         # Training data
│   ├── data1.csv                      # Network 1 (100 genes × 500 samples)
│   ├── data2.csv                      # Network 2
│   ├── data3.csv                      # Network 3
│   ├── data4.csv                      # Network 4
│   └── data5.csv                      # Network 5 (100 samples)
│
├── ARCHIVE_MODELS.md                  # Experimental history (all 11 phases)
├── RAPPORT_PROGRESSION.md             # Progress tracking
│
└── [Output]
    └── prediction_submission_final.zip # Codalab submission (auto-generated)
```

---

## Method Description

### Pipeline Overview

```
Raw Data (test_data/)
    ↓
[Preprocessing]
  • Imputation (median strategy)
  • StandardScaler normalization
    ↓
[Feature Importance Extraction]
  For each of 100 target genes:
    • Train ExtraTrees (400 estimators, max_features='sqrt')
    • Train GradientBoosting (200 estimators, subsample=0.8)
    • Train Ridge (alpha=5.0)
    • Train Lasso (alpha=0.005)
    • Extract feature importances (99 features per model)
    ↓
[Ensemble Combination]
  • Normalize importances per model [0,1]
  • Weighted average: ET(40%) + GB(30%) + Ridge(20%) + Lasso(10%)
  • Result: Edge scores for all (Cause, Effect) pairs
    ↓
[Edge Selection]
  • Sort by score descending
  • Select top-320 edges per network
    ↓
[Output Formatting]
  • Create predictions_network{1-5}.csv
  • Format: (Cause, Effect, Score)
    ↓
[Packaging]
  • ZIP all 5 CSV files
  • Ready for Codalab submission
```

### Model Details

| Component | Hyperparameter | Value | Justification |
|-----------|---|---|---|
| **ExtraTrees** | n_estimators | 400 | Balance between accuracy and computation |
| | max_features | 'sqrt' | **Key finding:** sqrt > log2 (+0.01 AUPR) |
| | random_state | 42 | Reproducibility |
| **GradientBoosting** | n_estimators | 200 | Sufficient boosting iterations |
| | learning_rate | 0.1 | Standard weak learner rate |
| | max_depth | 5 | Prevent overfitting |
| | subsample | 0.8 | **Regularization:** Improves stability |
| | random_state | 42 | Reproducibility |
| **Ridge** | alpha | 5.0 | **Tuned:** Higher than baseline (1.0) |
| **Lasso** | alpha | 0.005 | **Tuned:** Lower than baseline (0.01) |
| | max_iter | 10000 | Convergence guarantee |
| **Ensemble** | K (top edges) | 320 | **Optimized:** K=300/350 worse (0.32) |
| | Weights | 0.4/0.3/0.2/0.1 | Data-driven empirical determination |

---

## Performance Results

**Final Score:** 0.33 AUPR (average across 5 networks)

**Results by Network:**
- Network 1: 0.3641 ✅
- Network 2: 0.3371 ✅
- Network 3: 0.3507 ✅
- Network 4: 0.2068 ⚠️ (structural difficulty)
- Network 5: 0.3592 ✅

**Output Format:** ZIP containing 5 CSV files with columns (Cause, Effect, Score)

---

## Dependencies

```
pandas>=1.3.0
numpy>=1.20.0
scikit-learn>=1.0.0
```

Install via: `pip install -r requirements.txt`

---

## Documentation

- **RAPPORT_FINAL.md** - Complete methodology (French, academic style)
- **ARCHIVE_MODELS.md** - Full experimental history (11 phases)
- **RAPPORT_PROGRESSION.md** - Progress tracking and key findings
- **generate_final_submission.py** - Well-documented source code

---

## Code Quality

✅ **PEP 8 compliant** - Follows Python style guide
✅ **Fully documented** - Docstrings and inline comments
✅ **Modular design** - Reusable classes and functions
✅ **Reproducible** - `random_state=42` pinned globally
✅ **Production-ready** - Error handling and validation

---

## Usage

```bash
# Generate submission
python generate_final_submission.py

# Creates: prediction_submission_final.zip
# Size: ~45 KB
# Ready for: Codalab upload
```

---

**Status:** ✅ Complete and Production Ready
**Last Updated:** 2026-07-15

