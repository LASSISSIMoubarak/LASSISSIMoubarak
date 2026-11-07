script_args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", script_args, value = TRUE)
project_dir <- if (length(file_arg)) {
  dirname(normalizePath(sub("^--file=", "", file_arg[[1]])))
} else {
  getwd()
}

source(file.path(project_dir, "gasoline_nir_analysis.R"))

data <- load_gasoline_data()
analysis <- fit_gasoline_model(
  data,
  model_type = "PCR",
  train_fraction = 0.8,
  seed = 4433,
  ncomp = 6
)

cat(
  sprintf(
    "%s — %d samples, %d wavelengths, %d for calibration and %d for testing.\n",
    analysis$model_type,
    nrow(data$X),
    ncol(data$X),
    length(analysis$train_indices),
    length(analysis$test_indices)
  )
)
cat(
  sprintf(
    "Components fitted: %d | Test RMSE: %.3f | Test R²: %.3f\n",
    analysis$ncomp,
    analysis$rmse,
    analysis$r_squared
  )
)

graphics::par(mfrow = c(2, 2), mar = c(4, 4, 2, 1))

graphics::matplot(
  data$wavelengths,
  t(data$X[analysis$train_indices[seq_len(min(12, length(analysis$train_indices)))], , drop = FALSE]),
  type = "l",
  lty = 1,
  col = grDevices::adjustcolor("#246B8E", alpha.f = 0.45),
  xlab = "Wavelength (nm)",
  ylab = "Absorbance",
  main = "Example NIR spectra"
)

graphics::plot(
  analysis$cv$components,
  analysis$cv$rmsep,
  type = "b",
  pch = 16,
  col = "#246B8E",
  xlab = "Number of components",
  ylab = "RMSEP (LOO cross-validation)",
  main = "Cross-validation error"
)
graphics::abline(v = analysis$ncomp, lty = 2, col = "#C4543D")

graphics::plot(
  analysis$predictions$observed,
  analysis$predictions$predicted,
  pch = 19,
  col = "#246B8E",
  xlab = "Observed octane rating",
  ylab = "Predicted octane rating",
  main = "External test set"
)
graphics::abline(0, 1, lty = 2, col = "#C4543D")

pca <- stats::prcomp(data$X, center = TRUE, scale. = FALSE)
explained_variance <- pca$sdev^2 / sum(pca$sdev^2)
visible_components <- seq_len(min(30, length(explained_variance)))
graphics::plot(
  visible_components,
  explained_variance[visible_components],
  type = "b",
  pch = 16,
  col = "#246B8E",
  xlab = "Principal component",
  ylab = "Proportion of variance explained",
  main = "Descriptive PCA of spectra"
)
