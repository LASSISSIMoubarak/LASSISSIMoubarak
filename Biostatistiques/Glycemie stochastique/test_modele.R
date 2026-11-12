script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(script_arg) != 1L) stop("Lancer ce test avec Rscript.")
project_dir <- dirname(normalizePath(sub("^--file=", "", script_arg[[1L]]), mustWork = TRUE))
source(file.path(project_dir, "modele.R"), encoding = "UTF-8")

transition <- transition_ou(110, 0.25, 100, 0.8, 12)
stopifnot(
  isTRUE(all.equal(transition$mean, 100 + 10 * exp(-0.2))),
  isTRUE(all.equal(transition$sd^2, 12^2 * (1 - exp(-0.4)) / (2 * 0.8)))
)
values <- simuler_ou(40, 121, 0.25, 100, 0.8, 12, 2026)
stopifnot(
  identical(dim(values), c(40L, 121L)),
  identical(values, simuler_ou(40, 121, 0.25, 100, 0.8, 12, 2026)),
  all(is.finite(values))
)
fit <- estimer_ou(values, 0.25)
stopifnot(abs(fit["mu"] - 100) < 3,
          abs(fit["theta"] - 0.8) < 0.2,
          abs(fit["sigma"] - 12) < 1)
stopifnot(inherits(try(estimer_ou(matrix(1, 2, 2), 0.25), silent = TRUE), "try-error"))
stopifnot(inherits(try(transition_ou(1, 0, 100, 0.8, 12), silent = TRUE), "try-error"))
cat("Tous les tests du modele ont reussi.\n")
