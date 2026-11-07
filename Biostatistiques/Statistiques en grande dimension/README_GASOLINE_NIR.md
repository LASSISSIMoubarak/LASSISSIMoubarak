# NIR Spectra Analysis: PCR, PLS, and Shiny Demo

This mini-project uses the `gasoline` dataset included in the R package `pls`.
It explores near-infrared (NIR) spectra and predicts octane rating. The analysis
compares principal component regression (PCR) and partial least squares (PLS),
using leave-one-out cross-validation on the calibration set and a separate test
set for evaluation.

## Installation

In R, install the required packages:

```r
install.packages(c("pls", "shiny"))
```

The example dataset is included with `pls`; no external data files are needed.

## Run the R analysis

From this directory, run:

```powershell
Rscript "Projet_statistiques en grande dimension.R"
```

The script reports RMSE and R² on the test set, then plots example spectra,
cross-validation error, test predictions, and a descriptive PCA of the spectra.

## Run the Shiny demo

In R or RStudio, set this directory as the working directory and run:

```r
shiny::runApp()
```

Choose PCR or PLS, the number of components, the calibration set size, and the
random seed. Cross-validation helps assess the number of components; the
displayed performance metrics are calculated on the held-out test samples.

## Scope and limitations

This is a methodological demonstration using gasoline spectra and octane
ratings. It does not use digestate samples, reproduce INRAE instruments or
protocols, or constitute field or instrument validation. Calibration and test
sets come from one reproducible random split, so performance should be
interpreted as illustrative rather than as a guarantee of generalization.
