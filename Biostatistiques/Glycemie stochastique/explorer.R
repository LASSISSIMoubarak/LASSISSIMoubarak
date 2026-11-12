resumer_trajectoires <- function(values) {
  if (!is.matrix(values) || !is.numeric(values) || nrow(values) < 1L ||
      ncol(values) < 2L || any(!is.finite(values))) {
    stop("Les donnees doivent etre une matrice numerique finie avec au moins deux temps.")
  }
  data.frame(
    individu = seq_len(nrow(values)),
    moyenne = rowMeans(values),
    ecart_type = apply(values, 1L, sd),
    minimum = apply(values, 1L, min),
    maximum = apply(values, 1L, max)
  )
}

explorer <- function(project_dir) {
  source(file.path(project_dir, "modele.R"), local = TRUE, encoding = "UTF-8")
  source(file.path(project_dir, "configuration.R"), local = TRUE, encoding = "UTF-8")
  values <- simuler_ou(n_individus, n_temps, dt, mu, theta, sigma, seed)
  times <- (seq_len(n_temps) - 1L) * dt
  resume <- resumer_trajectoires(values)

  cat("Nombre de trajectoires :", nrow(values), "\n")
  cat("Mesures par trajectoire :", ncol(values), "\n")
  cat("Duree (heures) :", tail(times, 1L), "\n")
  cat("Intervalle entre mesures (heures) :", dt, "\n")
  cat("Valeurs manquantes :", sum(is.na(values)), "\n")
  cat("Statistiques de toutes les valeurs simulees :\n")
  print(summary(as.vector(values)))
  cat("Resume par individu (5 premiers) :\n")
  print(head(resume, 5L), row.names = FALSE)

  output_dir <- file.path(project_dir, "outputs")
  if (!dir.exists(output_dir) && !dir.create(output_dir, recursive = TRUE)) {
    stop("Impossible de creer le dossier de resultats : ", output_dir)
  }
  write.csv(resume, file.path(output_dir, "exploration_resume_individus.csv"), row.names = FALSE)
  image_path <- file.path(output_dir, "exploration_graphiques.png")
  png(image_path, width = 1400, height = 1000)
  on.exit(dev.off(), add = TRUE)
  par(mfrow = c(2, 2), mar = c(4, 4, 3, 1))
  n_display <- min(5L, nrow(values))
  matplot(times, t(values[seq_len(n_display), , drop = FALSE]), type = "l", lty = 1,
          xlab = "Temps (heures)", ylab = "Glycemie simulee (mg/dL)",
          main = "Trajectoires individuelles")
  plot(times, colMeans(values), type = "l", lwd = 2,
       xlab = "Temps (heures)", ylab = "Glycemie moyenne (mg/dL)",
       main = "Moyenne des individus a chaque temps")
  hist(as.vector(values), breaks = 30, col = "lightblue", border = "white",
       xlab = "Glycemie simulee (mg/dL)", main = "Distribution des observations")
  boxplot(as.data.frame(t(values[seq_len(n_display), , drop = FALSE])),
          names = paste("Individu", seq_len(n_display)), las = 2,
          ylab = "Glycemie simulee (mg/dL)", main = "Distribution par individu")
  cat("Resultats ecrits dans :", output_dir, "\n")
}

if (sys.nframe() == 0L) {
  script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
  if (length(script_arg) != 1L) stop("Lancer ce script avec Rscript.")
  project_dir <- dirname(normalizePath(sub("^--file=", "", script_arg[[1L]]), mustWork = TRUE))
  explorer(project_dir)
}
