transition_ou <- function(x, dt, mu, theta, sigma) {
  if (length(dt) != 1L || !is.finite(dt) || dt <= 0 ||
      length(mu) != 1L || !is.finite(mu) ||
      length(theta) != 1L || !is.finite(theta) || theta <= 0 ||
      length(sigma) != 1L || !is.finite(sigma) || sigma <= 0 ||
      any(!is.finite(x))) {
    stop("Parametres invalides pour le processus d'Ornstein-Uhlenbeck.")
  }
  decay <- exp(-theta * dt)
  variance <- sigma^2 * (-expm1(-2 * theta * dt)) / (2 * theta)
  list(mean = mu + (x - mu) * decay, sd = sqrt(variance))
}

simuler_ou <- function(n_individus, n_temps, dt, mu, theta, sigma, seed) {
  if (length(n_individus) != 1L || !is.finite(n_individus) ||
      n_individus < 1 || n_individus != floor(n_individus) ||
      length(n_temps) != 1L || !is.finite(n_temps) ||
      n_temps < 2 || n_temps != floor(n_temps) ||
      length(seed) != 1L || !is.finite(seed) ||
      seed < 0 || seed != floor(seed) || seed > .Machine$integer.max) {
    stop("Nombre d'individus, nombre de mesures ou graine invalide.")
  }
  transition_ou(0, dt, mu, theta, sigma)
  set.seed(seed)
  values <- matrix(NA_real_, nrow = n_individus, ncol = n_temps)
  values[, 1L] <- rnorm(n_individus, mu, sigma / sqrt(2 * theta))
  for (j in 2:n_temps) {
    transition <- transition_ou(values[, j - 1L], dt, mu, theta, sigma)
    values[, j] <- rnorm(n_individus, transition$mean, transition$sd)
  }
  values
}

estimer_ou <- function(values, dt) {
  if (!is.matrix(values) || !is.numeric(values) || nrow(values) < 1L ||
      ncol(values) < 2L || any(!is.finite(values)) ||
      length(dt) != 1L || !is.finite(dt) || dt <= 0 ||
      sd(as.vector(values)) <= 0) {
    stop("Les donnees doivent etre une matrice numerique finie et variable, avec au moins deux temps et dt > 0.")
  }
  previous <- as.vector(values[, -ncol(values), drop = FALSE])
  current <- as.vector(values[, -1L, drop = FALSE])
  initial_mu <- mean(values)
  initial_sigma <- sd(as.vector(values))

  neg_log_likelihood <- function(par) {
    mu <- par[1L]
    theta <- exp(par[2L])
    sigma <- exp(par[3L])
    decay <- exp(-theta * dt)
    variance <- sigma^2 * (-expm1(-2 * theta * dt)) / (2 * theta)
    if (!is.finite(variance) || variance <= 0) return(Inf)
    residuals <- current - (mu + (previous - mu) * decay)
    sum(log(2 * pi * variance) + residuals^2 / variance) / 2
  }
  fit <- optim(
    c(initial_mu, log(1), log(initial_sigma)),
    neg_log_likelihood,
    method = "BFGS",
    control = list(maxit = 2000, reltol = 1e-10)
  )
  if (fit$convergence != 0L || !is.finite(fit$value) ||
      any(!is.finite(fit$par)) || any(!is.finite(exp(fit$par[2:3])))) {
    stop("L'estimation n'a pas converge vers des parametres finis.")
  }
  c(mu = fit$par[1L], theta = exp(fit$par[2L]), sigma = exp(fit$par[3L]))
}
