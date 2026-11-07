load_gasoline_data <- function() {
  dataset_environment <- new.env(parent = emptyenv())
  utils::data("gasoline", package = "pls", envir = dataset_environment)
  gasoline <- dataset_environment$gasoline

  if (is.list(gasoline) && !is.null(gasoline$octane) && !is.null(gasoline$NIR)) {
    response <- as.numeric(gasoline$octane)
    spectra <- as.matrix(gasoline$NIR)
  } else {
    gasoline_matrix <- as.matrix(gasoline)
    if (ncol(gasoline_matrix) < 2L) {
      stop("The gasoline dataset must contain octane values and spectral columns.")
    }
    response <- as.numeric(gasoline_matrix[, 1L])
    spectra <- gasoline_matrix[, -1L, drop = FALSE]
  }

  storage.mode(spectra) <- "double"
  if (
    nrow(spectra) != length(response) ||
      any(!is.finite(spectra)) ||
      any(!is.finite(response))
  ) {
    stop("The gasoline dataset has inconsistent dimensions or non-finite values.")
  }

  wavelength_names <- colnames(spectra)
  wavelengths <- suppressWarnings(as.numeric(wavelength_names))
  if (is.null(wavelength_names) || anyNA(wavelengths)) {
    wavelengths <- seq(900, 1700, length.out = ncol(spectra))
  }

  list(X = spectra, Y = response, wavelengths = wavelengths)
}

fit_gasoline_model <- function(
  data,
  model_type = "PCR",
  train_fraction = 0.8,
  seed = 4433,
  ncomp = 6
) {
  model_type <- match.arg(model_type, c("PCR", "PLS"))
  sample_count <- nrow(data$X)
  if (sample_count < 6L) {
    stop("At least six samples are required to split calibration and test sets.")
  }
  if (
    !is.numeric(train_fraction) ||
      length(train_fraction) != 1L ||
      !is.finite(train_fraction) ||
      train_fraction <= 0 ||
      train_fraction >= 1
  ) {
    stop("The calibration fraction must be between 0 and 1.")
  }
  if (
    !is.numeric(seed) ||
      length(seed) != 1L ||
      !is.finite(seed) ||
      seed < 0 ||
      seed > .Machine$integer.max ||
      seed != as.integer(seed)
  ) {
    stop("The seed must be an integer between 0 and R's maximum integer value.")
  }
  if (
    !is.numeric(ncomp) ||
      length(ncomp) != 1L ||
      !is.finite(ncomp) ||
      ncomp < 1 ||
      ncomp > .Machine$integer.max ||
      ncomp != as.integer(ncomp)
  ) {
    stop("The number of components must be a positive integer.")
  }

  train_count <- max(2L, min(sample_count - 1L, floor(sample_count * train_fraction)))
  set.seed(as.integer(seed))
  train_indices <- sample(seq_len(sample_count), size = train_count)
  test_indices <- setdiff(seq_len(sample_count), train_indices)
  component_count <- max(
    1L,
    min(as.integer(ncomp), ncol(data$X), train_count - 1L)
  )

  training_data <- data.frame(
    octane = data$Y[train_indices],
    NIR = I(data$X[train_indices, , drop = FALSE])
  )

  model_function <- if (model_type == "PCR") pls::pcr else pls::plsr
  model <- model_function(
    octane ~ NIR,
    data = training_data,
    ncomp = component_count,
    validation = "LOO",
    scale = TRUE
  )

  test_data <- data.frame(
    NIR = I(data$X[test_indices, , drop = FALSE])
  )
  predicted <- as.numeric(
    stats::predict(model, newdata = test_data, ncomp = component_count)
  )
  observed <- data$Y[test_indices]
  rmse <- sqrt(mean((predicted - observed)^2))
  total_sum_squares <- sum((observed - mean(observed))^2)
  r_squared <- if (total_sum_squares > 0) {
    1 - sum((predicted - observed)^2) / total_sum_squares
  } else {
    NA_real_
  }
  cv_press <- model$validation$PRESS
  cv_rmsep <- sqrt(as.numeric(cv_press[1L, ]) / train_count)

  list(
    model_type = model_type,
    model = model,
    ncomp = component_count,
    train_indices = train_indices,
    test_indices = test_indices,
    rmse = rmse,
    r_squared = r_squared,
    cv = data.frame(
      components = seq_along(cv_rmsep),
      rmsep = cv_rmsep
    ),
    predictions = data.frame(
      sample = test_indices,
      observed = observed,
      predicted = predicted
    )
  )
}
