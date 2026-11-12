script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(script_arg) != 1L) stop("Lancer ce script avec Rscript.")
project_dir <- dirname(normalizePath(sub("^--file=", "", script_arg[[1L]]), mustWork = TRUE))
source(file.path(project_dir, "modele.R"), encoding = "UTF-8")
source(file.path(project_dir, "configuration.R"), encoding = "UTF-8")

values <- simuler_ou(n_individus, n_temps, dt, mu, theta, sigma, seed)
estimated <- estimer_ou(values, dt)
truth <- c(mu = mu, theta = theta, sigma = sigma)
comparison <- data.frame(
  parametre = names(truth),
  valeur_simulee = unname(truth),
  estimation = unname(estimated)
)
print(comparison, row.names = FALSE)

output_dir <- file.path(project_dir, "outputs")
if (!dir.exists(output_dir) && !dir.create(output_dir, recursive = TRUE)) {
  stop("Impossible de creer le dossier de resultats : ", output_dir)
}
times <- (seq_len(n_temps) - 1L) * dt
observations <- data.frame(
  individu = rep(seq_len(n_individus), times = n_temps),
  temps_heures = rep(times, each = n_individus),
  glycemie_simulee_mg_dl = as.vector(values)
)
write.csv(observations, file.path(output_dir, "observations_simulees.csv"), row.names = FALSE)
write.csv(comparison, file.path(output_dir, "parametres.csv"), row.names = FALSE)

png(file.path(output_dir, "trajectoires.png"), width = 1100, height = 650)
matplot(times, t(values[1:5, , drop = FALSE]), type = "l", lty = 1,
        xlab = "Temps (heures)", ylab = "Glycemie simulee (mg/dL)",
        main = "Cinq trajectoires simulees")
abline(h = mu, lty = 2)
legend("topright", legend = c(paste("Individu", 1:5), "Moyenne simulee"),
       col = c(1:5, 1), lty = c(rep(1, 5), 2), bty = "n")
dev.off()
cat("Resultats ecrits dans :", output_dir, "\n")
