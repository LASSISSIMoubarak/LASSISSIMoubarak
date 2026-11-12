script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(script_arg) != 1L) stop("Lancer ce script avec Rscript.")
project_dir <- dirname(normalizePath(sub("^--file=", "", script_arg[[1L]]), mustWork = TRUE))
source(file.path(project_dir, "modele.R"), encoding = "UTF-8")
source(file.path(project_dir, "configuration.R"), encoding = "UTF-8")

if (!requireNamespace("tseries", quietly = TRUE)) {
  stop("Le package 'tseries' est requis : installez-le avec install.packages('tseries').")
}

values <- simuler_ou(n_individus, n_temps, dt, mu, theta, sigma, seed)
set.seed(42)
indices <- sample(nrow(values), size = 3)
temps <- (seq_len(ncol(values)) - 1) * dt

output_dir <- file.path(project_dir, "outputs")
if (!dir.exists(output_dir) && !dir.create(output_dir, recursive = TRUE)) {
  stop("Impossible de creer le dossier de resultats : ", output_dir)
}
image_path <- file.path(output_dir, "stationnarite_trajectoires.png")
png(image_path, width = 1100, height = 650)
matplot(
  temps, t(values[indices, , drop = FALSE]),
  type = "l", lty = 1, col = 1:3,
  xlab = "Temps (heures)",
  ylab = "Glycémie simulée (mg/dL)",
  main = "Trois trajectoires choisies au hasard"
)
legend("topright", legend = paste("Individu", indices), col = 1:3, lty = 1)
dev.off()
cat("Graphique :", image_path, "\n")

for (i in indices) {
  val <- values[i, ]
  cat("\n--- Individu", i, "---\n")
  cat("\nTest KPSS (stationnarite autour d'une constante) :\n")
  print(tseries::kpss.test(val, null = "Level"))
  cat("\nTest ADF (hypothese nulle : racine unitaire) :\n")
  print(tseries::adf.test(val))
}
