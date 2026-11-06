get_script_dir <- function() {
  file_argument <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
  if (length(file_argument) > 0L) {
    script_path <- sub("^--file=", "", file_argument[[1L]])
    return(normalizePath(dirname(script_path), winslash = "/", mustWork = TRUE))
  }
  normalizePath(getwd(), winslash = "/", mustWork = TRUE)
}

SCRIPT_DIR <- get_script_dir()
REPOSITORY_ROOT <- normalizePath(
  file.path(SCRIPT_DIR, "..", ".."),
  winslash = "/",
  mustWork = TRUE
)

parse_args <- function(args) {
  options <- list(
    data_dir = file.path(REPOSITORY_ROOT, "SolarWatch", "data", "raw"),
    output_dir = file.path(SCRIPT_DIR, "results", "r"),
    draws = 2000L,
    burn_in = 1000L,
    seed = 42L
  )
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (!key %in% c("--data-dir", "--output-dir", "--draws", "--burn-in", "--seed")) {
      stop("Option inconnue : ", key)
    }
    if (i == length(args)) {
      stop("Valeur manquante pour ", key)
    }
    value <- args[[i + 1L]]
    name <- switch(
      key,
      "--data-dir" = "data_dir",
      "--output-dir" = "output_dir",
      "--draws" = "draws",
      "--burn-in" = "burn_in",
      "--seed" = "seed"
    )
    if (name %in% c("draws", "burn_in", "seed")) {
      number <- suppressWarnings(as.integer(value))
      if (is.na(number) || (name == "draws" && number < 1L) ||
          (name != "draws" && number < 0L)) {
        stop("Valeur entière invalide pour ", key, " : ", value)
      }
      options[[name]] <- number
    } else {
      options[[name]] <- value
    }
    i <- i + 2L
  }
  options
}

parse_timestamp <- function(values, formats) {
  result <- as.POSIXct(rep(NA_real_, length(values)), origin = "1970-01-01",
                       tz = "UTC")
  for (format in formats) {
    missing <- is.na(result)
    if (!any(missing)) {
      break
    }
    parsed <- as.POSIXct(
      strptime(values[missing], format, tz = "UTC"),
      tz = "UTC"
    )
    result[missing] <- parsed
  }
  result
}

read_plant_data <- function(data_dir, plant_number) {
  generation_path <- file.path(
    data_dir, paste0("Plant_", plant_number, "_Generation_Data.csv")
  )
  weather_path <- file.path(
    data_dir, paste0("Plant_", plant_number, "_Weather_Sensor_Data.csv")
  )
  if (!file.exists(generation_path) || !file.exists(weather_path)) {
    stop("Fichier de production ou de météo absent pour la centrale ", plant_number)
  }

  generation <- read.csv(generation_path, stringsAsFactors = FALSE)
  weather <- read.csv(weather_path, stringsAsFactors = FALSE)
  required_generation <- c("DATE_TIME", "PLANT_ID", "AC_POWER")
  required_weather <- c(
    "DATE_TIME", "PLANT_ID", "IRRADIATION",
    "AMBIENT_TEMPERATURE", "MODULE_TEMPERATURE"
  )
  if (!all(required_generation %in% names(generation))) {
    stop("Colonnes de production requises absentes : ", generation_path)
  }
  if (!all(required_weather %in% names(weather))) {
    stop("Colonnes météo requises absentes : ", weather_path)
  }

  generation$DATE_TIME <- parse_timestamp(
    generation$DATE_TIME,
    c("%d-%m-%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M")
  )
  weather$DATE_TIME <- parse_timestamp(
    weather$DATE_TIME,
    c("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M")
  )
  if (anyNA(generation$DATE_TIME) || anyNA(weather$DATE_TIME)) {
    stop("Impossible de lire certains horodatages pour la centrale ", plant_number)
  }

  power <- aggregate(
    AC_POWER ~ PLANT_ID + DATE_TIME,
    data = generation,
    FUN = sum
  )
  meteo <- aggregate(
    cbind(IRRADIATION, AMBIENT_TEMPERATURE, MODULE_TEMPERATURE) ~
      PLANT_ID + DATE_TIME,
    data = weather,
    FUN = mean
  )
  merged <- merge(power, meteo, by = c("PLANT_ID", "DATE_TIME"), all.x = TRUE)
  merged[order(merged$PLANT_ID, merged$DATE_TIME), , drop = FALSE]
}

load_aggregated_data <- function(data_dir) {
  files <- list.files(
    data_dir,
    pattern = "^Plant_[0-9]+_Generation_Data\\.csv$",
    full.names = FALSE
  )
  if (length(files) == 0L) {
    stop("Aucun fichier Plant_*_Generation_Data.csv dans ", data_dir)
  }
  plant_numbers <- sort(unique(as.integer(
    sub("^Plant_([0-9]+)_Generation_Data\\.csv$", "\\1", files)
  )))
  rows <- lapply(plant_numbers, function(plant_number) {
    read_plant_data(data_dir, plant_number)
  })
  result <- do.call(rbind, rows)
  result[order(result$PLANT_ID, result$DATE_TIME), , drop = FALSE]
}

build_next_step_frame <- function(data) {
  data <- data[order(data$PLANT_ID, data$DATE_TIME), , drop = FALSE]
  groups <- split(data, data$PLANT_ID, drop = TRUE)
  results <- lapply(groups, function(plant) {
    plant <- plant[order(plant$DATE_TIME), , drop = FALSE]
    n <- nrow(plant)
    if (n < 3L) {
      return(NULL)
    }
    rows <- vector("list", n - 2L)
    count <- 0L
    for (i in 2L:(n - 1L)) {
      if (difftime(plant$DATE_TIME[i], plant$DATE_TIME[i - 1L],
                   units = "secs") != 900 ||
          difftime(plant$DATE_TIME[i + 1L], plant$DATE_TIME[i],
                   units = "secs") != 900) {
        next
      }
      timestamp <- plant$DATE_TIME[i]
      hour <- as.POSIXlt(timestamp, tz = "UTC")$hour +
        as.POSIXlt(timestamp, tz = "UTC")$min / 60
      count <- count + 1L
      rows[[count]] <- data.frame(
        PLANT_ID = plant$PLANT_ID[i],
        DATE_TIME = timestamp,
        next_timestamp = plant$DATE_TIME[i + 1L],
        current_power = plant$AC_POWER[i],
        target_power = plant$AC_POWER[i + 1L],
        irradiation = plant$IRRADIATION[i],
        irradiation_change = plant$IRRADIATION[i] - plant$IRRADIATION[i - 1L],
        ambient_temperature = plant$AMBIENT_TEMPERATURE[i],
        module_temperature = plant$MODULE_TEMPERATURE[i],
        log_current_power = log1p(max(0, plant$AC_POWER[i])),
        hour_sin = sin(2 * pi * hour / 24),
        hour_cos = cos(2 * pi * hour / 24)
      )
    }
    if (count == 0L) {
      return(NULL)
    }
    do.call(rbind, rows[seq_len(count)])
  })
  results <- Filter(Negate(is.null), results)
  if (length(results) == 0L) {
    stop("Aucune paire de relevés consécutifs espacés de 15 minutes.")
  }
  frame <- do.call(rbind, results)
  frame <- frame[complete.cases(frame), , drop = FALSE]
  frame[order(frame$DATE_TIME, frame$PLANT_ID), , drop = FALSE]
}

chronological_split <- function(frame, train_fraction = 0.7) {
  if (train_fraction <= 0 || train_fraction >= 1) {
    stop("train_fraction doit être strictement compris entre 0 et 1.")
  }
  timestamps <- sort(unique(frame$DATE_TIME))
  split_index <- floor(length(timestamps) * train_fraction)
  if (split_index < 1L || split_index >= length(timestamps)) {
    stop("Pas assez d'horodatages pour séparer train et test.")
  }
  boundary <- timestamps[split_index + 1L]
  train <- frame[frame$DATE_TIME < boundary, , drop = FALSE]
  test <- frame[frame$DATE_TIME >= boundary, , drop = FALSE]
  if (nrow(train) == 0L || nrow(test) == 0L) {
    stop("Le découpage chronologique a produit un ensemble vide.")
  }
  list(train = train, test = test)
}

fit_gibbs_regression <- function(train, draws = 2000L, burn_in = 1000L,
                                 seed = 42L) {
  feature_names <- c(
    "log_current_power", "irradiation", "irradiation_change",
    "ambient_temperature", "module_temperature", "hour_sin", "hour_cos"
  )
  if (draws < 1L || burn_in < 0L) {
    stop("draws doit être positif et burn_in ne peut pas être négatif.")
  }
  if (nrow(train) <= length(feature_names) + 1L) {
    stop("Il faut davantage d'observations d'entraînement.")
  }

  features <- as.matrix(train[, feature_names, drop = FALSE])
  target <- log1p(pmax(0, train$target_power)) -
    log1p(pmax(0, train$current_power))
  if (any(!is.finite(features)) || any(!is.finite(target))) {
    stop("Les données d'entraînement contiennent des valeurs non finies.")
  }

  feature_means <- colMeans(features)
  feature_scales <- apply(features, 2L, sd)
  feature_scales[!is.finite(feature_scales) | feature_scales == 0] <- 1
  target_mean <- mean(target)
  target_scale <- sd(target)
  if (!is.finite(target_scale) || target_scale == 0) {
    target_scale <- 1
  }
  standardized_features <- sweep(
    sweep(features, 2L, feature_means, "-"), 2L, feature_scales, "/"
  )
  standardized_target <- (target - target_mean) / target_scale
  design <- cbind(Intercept = 1, standardized_features)

  parameter_count <- ncol(design)
  prior_precision <- diag(1 / 25, parameter_count)
  posterior_precision <- crossprod(design) + prior_precision
  posterior_covariance <- solve(posterior_precision)
  posterior_mean <- drop(
    posterior_covariance %*% crossprod(design, standardized_target)
  )
  prior_shape <- 2
  prior_scale <- 1
  posterior_shape <- prior_shape + nrow(train) / 2
  posterior_scale <- prior_scale + 0.5 * (
    sum(standardized_target^2) -
      drop(crossprod(posterior_mean, posterior_precision %*% posterior_mean))
  )
  posterior_scale <- max(posterior_scale, .Machine$double.xmin)

  set.seed(seed)
  cholesky <- chol(posterior_covariance)
  beta_draws <- matrix(NA_real_, nrow = draws, ncol = parameter_count)
  variance_draws <- numeric(draws)
  beta <- posterior_mean
  variance <- posterior_scale / max(posterior_shape - 1, 1)
  conditional_shape <- prior_shape + (nrow(train) + parameter_count) / 2

  for (iteration in seq_len(draws + burn_in)) {
    beta <- drop(
      posterior_mean +
        sqrt(variance) * t(cholesky) %*% rnorm(parameter_count)
    )
    residual <- standardized_target - drop(design %*% beta)
    conditional_scale <- prior_scale + 0.5 * (
      sum(residual^2) + drop(crossprod(beta, prior_precision %*% beta))
    )
    variance <- 1 / rgamma(1L, shape = conditional_shape,
                           rate = conditional_scale)
    if (iteration > burn_in) {
      sample_index <- iteration - burn_in
      beta_draws[sample_index, ] <- beta
      variance_draws[sample_index] <- variance
    }
  }

  list(
    feature_names = feature_names,
    feature_means = feature_means,
    feature_scales = feature_scales,
    target_mean = target_mean,
    target_scale = target_scale,
    beta_draws = beta_draws,
    variance_draws = variance_draws
  )
}

predict_posterior <- function(posterior, rows, seed = 142L) {
  if (nrow(rows) == 0L) {
    return(data.frame(
      prediction = numeric(), lower_95 = numeric(), upper_95 = numeric()
    ))
  }
  features <- as.matrix(rows[, posterior$feature_names, drop = FALSE])
  standardized_features <- sweep(
    sweep(features, 2L, posterior$feature_means, "-"),
    2L, posterior$feature_scales, "/"
  )
  design <- cbind(Intercept = 1, standardized_features)
  predictive_mean <- design %*% t(posterior$beta_draws)
  set.seed(seed)
  noise <- matrix(
    rnorm(length(predictive_mean)),
    nrow = nrow(rows),
    ncol = ncol(predictive_mean)
  )
  predictive <- predictive_mean +
    sweep(noise, 2L, sqrt(posterior$variance_draws), "*")
  log_power <- matrix(
    log1p(pmax(0, rows$current_power)),
    nrow = nrow(rows),
    ncol = ncol(predictive)
  ) + posterior$target_mean + posterior$target_scale * predictive
  log_power[log_power > 50] <- 50
  log_power[log_power < -50] <- -50
  power <- expm1(log_power)
  power[power < 0] <- 0
  data.frame(
    prediction = apply(power, 1L, median),
    lower_95 = apply(power, 1L, quantile, probs = 0.025, names = FALSE),
    upper_95 = apply(power, 1L, quantile, probs = 0.975, names = FALSE)
  )
}

regression_metrics <- function(rows) {
  actual <- rows$actual_power
  prediction <- rows$bayesian_prediction
  persistence <- rows$persistence_prediction
  errors <- actual - prediction
  persistence_errors <- actual - persistence
  data.frame(
    samples = length(actual),
    bayesian_mae = mean(abs(errors)),
    bayesian_rmse = sqrt(mean(errors^2)),
    bayesian_95_interval_coverage = mean(
      actual >= rows$lower_95 & actual <= rows$upper_95
    ),
    bayesian_95_interval_mean_width = mean(rows$upper_95 - rows$lower_95),
    persistence_mae = mean(abs(persistence_errors)),
    persistence_rmse = sqrt(mean(persistence_errors^2))
  )
}

save_forecast_plot <- function(rows, output_path) {
  rows <- rows[order(rows$next_timestamp), , drop = FALSE]
  plant_id <- rows$PLANT_ID[1L]
  png(output_path, width = 1400, height = 700, res = 130)
  on.exit(dev.off(), add = TRUE)
  plot(
    rows$next_timestamp, rows$actual_power,
    type = "l", col = "black", lwd = 1,
    ylim = range(
      c(rows$actual_power, rows$bayesian_prediction,
        rows$lower_95, rows$upper_95, rows$persistence_prediction),
      finite = TRUE
    ),
    xlab = "Horodatage de la production prévue",
    ylab = "AC_POWER (unité du jeu source)",
    main = paste("Prévision bayésienne - centrale", plant_id)
  )
  polygon(
    c(rows$next_timestamp, rev(rows$next_timestamp)),
    c(rows$lower_95, rev(rows$upper_95)),
    col = adjustcolor("steelblue", alpha.f = 0.18),
    border = NA
  )
  lines(rows$next_timestamp, rows$actual_power, col = "black", lwd = 1)
  lines(rows$next_timestamp, rows$bayesian_prediction,
        col = "steelblue", lwd = 1)
  lines(rows$next_timestamp, rows$persistence_prediction,
        col = "darkorange", lwd = 1)
  legend(
    "topleft",
    legend = c("Réel", "Médiane bayésienne", "Intervalle prédictif 95 %",
               "Persistance"),
    col = c("black", "steelblue", "steelblue", "darkorange"),
    lty = c(1, 1, 1, 1), lwd = c(1, 1, 8, 1), bty = "n"
  )
}

run_forecast <- function(
                         data_dir = file.path(REPOSITORY_ROOT, "SolarWatch", "data", "raw"),
                         output_dir = file.path(SCRIPT_DIR, "results", "r"),
                         draws = 2000L, burn_in = 1000L, seed = 42L) {
  data <- load_aggregated_data(data_dir)
  frame <- build_next_step_frame(data)
  split <- chronological_split(frame)
  train <- split$train[split$train$irradiation >= 0.1, , drop = FALSE]
  test <- split$test[split$test$irradiation >= 0.1, , drop = FALSE]
  if (nrow(train) == 0L || nrow(test) == 0L) {
    stop("Pas assez d'observations de jour pour entraîner et tester.")
  }

  test_plants <- sort(unique(test$PLANT_ID))
  results <- lapply(test_plants, function(plant_id) {
    plant_train <- train[train$PLANT_ID == plant_id, , drop = FALSE]
    plant_test <- test[test$PLANT_ID == plant_id, , drop = FALSE]
    if (nrow(plant_train) == 0L) {
      stop("Aucune donnée d'entraînement de jour pour la centrale ", plant_id)
    }
    posterior <- fit_gibbs_regression(
      plant_train, draws = draws, burn_in = burn_in, seed = seed + plant_id
    )
    predictions <- predict_posterior(
      posterior, plant_test, seed = seed + plant_id + 100000L
    )
    cbind(
      plant_test[, c(
        "PLANT_ID", "DATE_TIME", "next_timestamp", "current_power",
        "target_power", "irradiation"
      )],
      persistence_prediction = plant_test$current_power,
      actual_power = plant_test$target_power,
      bayesian_prediction = predictions$prediction,
      lower_95 = predictions$lower_95,
      upper_95 = predictions$upper_95
    )
  })
  forecasts <- do.call(rbind, results)
  forecasts <- forecasts[order(forecasts$PLANT_ID, forecasts$next_timestamp), ]

  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  write.csv(
    forecasts, file.path(output_dir, "bayesian_forecasts.csv"),
    row.names = FALSE
  )
  metrics <- regression_metrics(forecasts)
  write.csv(
    metrics, file.path(output_dir, "bayesian_metrics.csv"),
    row.names = FALSE
  )
  for (plant_id in test_plants) {
    plant_forecasts <- forecasts[forecasts$PLANT_ID == plant_id, , drop = FALSE]
    save_forecast_plot(
      plant_forecasts,
      file.path(output_dir, paste0("plant_", plant_id, "_bayesian_forecast.png"))
    )
  }

  cat("Modèle : régression bayésienne de jour, posterior Normal-Inverse-Gamma\n")
  cat("Échantillonnage : Gibbs\n")
  cat("Observations entraînement jour :", nrow(train), "\n")
  cat("Observations test jour :", nrow(test), "\n")
  cat("Fin entraînement :", format(max(split$train$DATE_TIME), tz = "UTC"), "\n")
  cat("Début test :", format(min(split$test$DATE_TIME), tz = "UTC"), "\n\n")
  print(metrics, row.names = FALSE)
  cat("\nRésultats enregistrés dans :", normalizePath(output_dir), "\n")
  invisible(list(forecasts = forecasts, metrics = metrics))
}

if (sys.nframe() == 0L) {
  options <- parse_args(commandArgs(trailingOnly = TRUE))
  run_forecast(
    data_dir = options$data_dir,
    output_dir = options$output_dir,
    draws = options$draws,
    burn_in = options$burn_in,
    seed = options$seed
  )
}
