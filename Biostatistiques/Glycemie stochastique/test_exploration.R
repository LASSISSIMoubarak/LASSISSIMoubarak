script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(script_arg) != 1L) stop("Lancer ce test avec Rscript.")
project_dir <- dirname(normalizePath(sub("^--file=", "", script_arg[[1L]]), mustWork = TRUE))
source(file.path(project_dir, "explorer.R"), encoding = "UTF-8")

values <- matrix(c(1, 2, 3, 4, 5, 6), nrow = 2, byrow = TRUE)
resume <- resumer_trajectoires(values)
stopifnot(
  nrow(resume) == 2L,
  identical(resume$individu, 1:2),
  isTRUE(all.equal(resume$moyenne, c(2, 5))),
  isTRUE(all.equal(resume$ecart_type, c(1, 1))),
  isTRUE(all.equal(resume$minimum, c(1, 4))),
  isTRUE(all.equal(resume$maximum, c(3, 6))),
  inherits(try(resumer_trajectoires(matrix(c(1, NA), nrow = 1)), silent = TRUE), "try-error")
)
cat("Tous les tests de l'exploration ont reussi.\n")
