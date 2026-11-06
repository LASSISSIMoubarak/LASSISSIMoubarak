get_project_dir <- function() {
  file_argument <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
  if (length(file_argument) > 0L) {
    script_path <- sub("^--file=", "", file_argument[[1L]])
    return(normalizePath(dirname(script_path), winslash = "/", mustWork = TRUE))
  }
  normalizePath(getwd(), winslash = "/", mustWork = TRUE)
}

PROJECT_DIR <- get_project_dir()

parse_args <- function(args) {
  options <- list(
    output_dir = file.path(PROJECT_DIR, "results"),
    iter = 2000L,
    warmup = 1000L,
    seed = 2026L
  )
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (!key %in% c("--output-dir", "--iter", "--warmup", "--seed")) {
      stop("Option inconnue : ", key)
    }
    if (i == length(args)) {
      stop("Valeur manquante pour ", key)
    }
    value <- args[[i + 1L]]
    name <- switch(
      key,
      "--output-dir" = "output_dir",
      "--iter" = "iter",
      "--warmup" = "warmup",
      "--seed" = "seed"
    )
    if (name != "output_dir") {
      number <- suppressWarnings(as.integer(value))
      minimum <- if (name == "warmup") 0L else 1L
      if (is.na(number) || number < minimum) {
        stop("Valeur invalide pour ", key, " : ", value)
      }
      options[[name]] <- number
    } else {
      options[[name]] <- value
    }
    i <- i + 2L
  }
  if (options$warmup >= options$iter) {
    stop("--warmup doit être inférieur à --iter.")
  }
  options
}

prepare_pbc_data <- function() {
  if (!requireNamespace("survival", quietly = TRUE)) {
    stop("Le package R 'survival' est requis. Installe-le avec install.packages('survival').")
  }
  data("pbc", package = "survival", envir = environment())
  randomized <- pbc[pbc$id <= 312, ]
  required <- c("time", "status", "trt", "age", "bili", "albumin")
  if (!all(required %in% names(randomized))) {
    stop("Le jeu survival::pbc ne contient pas les variables attendues.")
  }
  randomized <- randomized[complete.cases(randomized[, required]), ]
  randomized$event <- as.integer(randomized$status %in% c(1L, 2L))
  randomized$log_bili <- log(randomized$bili)
  randomized$dpenicillamine <- as.integer(randomized$trt == 1L)

  continuous <- c("age", "log_bili", "albumin")
  centers <- vapply(randomized[, continuous, drop = FALSE], mean, numeric(1))
  scales <- vapply(randomized[, continuous, drop = FALSE], sd, numeric(1))
  if (any(!is.finite(scales)) || any(scales <= 0)) {
    stop("Une variable continue ne peut pas être standardisée.")
  }
  for (variable in continuous) {
    randomized[[paste0(variable, "_z")]] <-
      (randomized[[variable]] - centers[[variable]]) / scales[[variable]]
  }

  randomized <- randomized[order(randomized$id), ]
  list(
    frame = randomized,
    stan_data = list(
      N = nrow(randomized),
      K = 4L,
      X = cbind(
        age_z = randomized$age_z,
        log_bili_z = randomized$log_bili_z,
        albumin_z = randomized$albumin_z,
        dpenicillamine = randomized$dpenicillamine
      ),
      time_days = as.numeric(randomized$time),
      event = randomized$event
    ),
    centers = centers,
    scales = scales
  )
}

posterior_summary <- function(fit) {
  raw <- rstan::summary(
    fit,
    pars = c("alpha", "beta", "shape", "time_ratio_dpenicillamine"),
    probs = c(0.025, 0.5, 0.975)
  )$summary
  terms <- c(
    "alpha",
    "beta[1]",
    "beta[2]",
    "beta[3]",
    "beta[4]",
    "shape",
    "time_ratio_dpenicillamine"
  )
  labels <- c(
    "Intercept (échelle log, covariables moyennes, D-pénicillamine)",
    "Âge (par écart-type)",
    "Log-bilirubine (par écart-type)",
    "Albumine (par écart-type)",
    "D-pénicillamine vs placebo (rapport de temps)",
    "Paramètre de forme Weibull",
    "D-pénicillamine vs placebo (rapport de temps)"
  )
  missing <- setdiff(terms, rownames(raw))
  if (length(missing)) {
    stop("Paramètres absents du résumé Stan : ", paste(missing, collapse = ", "))
  }
  result <- data.frame(
    parameter = terms,
    interpretation = labels,
    mean = raw[terms, "mean"],
    sd = raw[terms, "sd"],
    median = raw[terms, "50%"],
    lower_95 = raw[terms, "2.5%"],
    upper_95 = raw[terms, "97.5%"],
    rhat = raw[terms, "Rhat"],
    effective_sample_size = raw[terms, "n_eff"],
    row.names = NULL,
    check.names = FALSE
  )
  result
}

save_survival_plot <- function(fit, stan_data, output_path) {
  draws <- rstan::extract(fit, pars = c("alpha", "beta", "shape"))
  time_grid <- seq(0, max(stan_data$time_days), length.out = 250)
  treatment <- c(0, 1)
  curves <- lapply(treatment, function(active) {
    log_scale <- draws$alpha + draws$beta[, 4] * active
    survival <- vapply(time_grid, function(time) {
      exp(-((time / exp(log_scale)) ^ draws$shape))
    }, numeric(nrow(draws$beta)))
    data.frame(
      days = time_grid,
      median = apply(survival, 2L, median),
      lower_95 = apply(survival, 2L, quantile, probs = 0.025, names = FALSE),
      upper_95 = apply(survival, 2L, quantile, probs = 0.975, names = FALSE),
      treatment = if (active == 1) "D-pénicillamine" else "Placebo"
    )
  })
  curves <- do.call(rbind, curves)

  png(output_path, width = 1400, height = 850, res = 140)
  on.exit(dev.off(), add = TRUE)
  plot(
    NA,
    xlim = range(time_grid),
    ylim = c(0, 1),
    xlab = "Jours depuis l'inclusion",
    ylab = "Probabilité de rester sans transplantation ni décès",
    main = "Courbes de survie postérieures (covariables à leur moyenne)"
  )
  colors <- c("Placebo" = "darkorange3", "D-pénicillamine" = "steelblue4")
  for (group in names(colors)) {
    values <- curves[curves$treatment == group, ]
    polygon(
      c(values$days, rev(values$days)),
      c(values$lower_95, rev(values$upper_95)),
      col = grDevices::adjustcolor(colors[[group]], alpha.f = 0.14),
      border = NA
    )
    lines(values$days, values$median, col = colors[[group]], lwd = 2)
  }
  legend(
    "bottomleft",
    legend = c("Placebo", "D-pénicillamine", "Intervalle crédible 95 %"),
    col = c(colors, "grey60"),
    lty = c(1, 1, 1),
    lwd = c(2, 2, 8),
    bty = "n"
  )
}

run_analysis <- function(output_dir = file.path(PROJECT_DIR, "results"), iter = 2000L,
                         warmup = 1000L, seed = 2026L) {
  if (!requireNamespace("rstan", quietly = TRUE)) {
    stop("Le package R 'rstan' est requis. Installe-le selon le README.")
  }
  prepared <- prepare_pbc_data()
  frame <- prepared$frame
  data <- prepared$stan_data
  stan_file <- file.path(PROJECT_DIR, "stan", "pbc_weibull_aft.stan")
  if (!file.exists(stan_file)) {
    stop("Fichier Stan introuvable : ", stan_file,
         ". Lance le script depuis la racine du projet.")
  }

  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  rstan::rstan_options(auto_write = TRUE)
  options(mc.cores = min(4L, parallel::detectCores(logical = FALSE)))
  model <- rstan::stan_model(file = stan_file)
  fit <- rstan::sampling(
    object = model,
    data = data,
    chains = 4L,
    iter = iter,
    warmup = warmup,
    seed = seed,
    cores = min(4L, parallel::detectCores(logical = FALSE)),
    control = list(adapt_delta = 0.95, max_treedepth = 12L),
    refresh = 0L
  )

  estimates <- posterior_summary(fit)
  write.csv(
    estimates,
    file.path(output_dir, "posterior_parameter_estimates.csv"),
    row.names = FALSE
  )

  sampler_params <- rstan::get_sampler_params(fit, inc_warmup = FALSE)
  divergences <- sum(vapply(
    sampler_params,
    function(chain) sum(chain[, "divergent__"]),
    numeric(1)
  ))
  treedepth_hits <- sum(vapply(
    sampler_params,
    function(chain) sum(chain[, "treedepth__"] >= 12),
    numeric(1)
  ))
  diagnostics <- data.frame(
    chains = 4L,
    iterations_per_chain = iter,
    warmup_per_chain = warmup,
    divergent_transitions = divergences,
    max_treedepth_hits = treedepth_hits,
    max_rhat = max(estimates$rhat, na.rm = TRUE),
    min_effective_sample_size = min(estimates$effective_sample_size, na.rm = TRUE),
    events_composite = sum(data$event),
    censored = sum(data$event == 0L),
    randomized_participants = nrow(frame)
  )
  write.csv(
    diagnostics,
    file.path(output_dir, "model_diagnostics.csv"),
    row.names = FALSE
  )
  metadata <- data.frame(
    key = c(
      "R_version",
      "rstan_version",
      "survival_version",
      "seed",
      "chains",
      "iterations_per_chain",
      "warmup_per_chain",
      "randomized_participants",
      "composite_events",
      "right_censored",
      "data_source"
    ),
    value = c(
      R.version.string,
      as.character(utils::packageVersion("rstan")),
      as.character(utils::packageVersion("survival")),
      seed,
      4L,
      iter,
      warmup,
      nrow(frame),
      sum(data$event),
      sum(data$event == 0L),
      "survival::pbc; randomized trial subset id <= 312"
    ),
    stringsAsFactors = FALSE
  )
  write.csv(
    metadata,
    file.path(output_dir, "analysis_metadata.csv"),
    row.names = FALSE
  )
  save_survival_plot(
    fit,
    data,
    file.path(output_dir, "posterior_survival_curves.png")
  )
  saveRDS(fit, file.path(output_dir, "pbc_weibull_fit.rds"))

  cat("Participants randomisés :", nrow(frame), "\n")
  cat("Événements (transplantation ou décès) :", sum(data$event), "\n")
  cat("Observations censurées :", sum(data$event == 0L), "\n\n")
  print(estimates, row.names = FALSE)
  cat("\nDiagnostics MCMC :\n")
  print(diagnostics, row.names = FALSE)
  cat("\nFichiers enregistrés dans :", normalizePath(output_dir), "\n")
  invisible(list(fit = fit, estimates = estimates, diagnostics = diagnostics))
}

if (sys.nframe() == 0L) {
  arguments <- parse_args(commandArgs(trailingOnly = TRUE))
  run_analysis(
    output_dir = arguments$output_dir,
    iter = arguments$iter,
    warmup = arguments$warmup,
    seed = arguments$seed
  )
}
