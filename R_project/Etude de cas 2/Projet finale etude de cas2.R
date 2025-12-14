library(readxl)
library(tidyverse)
data_COVID = read_excel("data_COVID.xlsx")
data = as.data.frame(data_COVID)
data2 = na.omit(data)
data2$niv_etude = replace(data2$niv_etude, data2$niv_etude %in% c("Diplôme du 1er cycle universitaire, BTS, DEUST, DUT, diplôme des professions sociales ou de la santé, ou équivalent BAC + 2","CAP, BEP ou diplôme de même niveau"),"BAC+2")
data2$niv_etude = replace(data2$niv_etude, data2$niv_etude %in% "Diplôme du 3ème cycle universitaire, doctorat","BAC+8")
data2$niv_etude = replace(data2$niv_etude, data2$niv_etude %in% "Diplôme du 2nd cycle universitaire, Master, ingénieur","BAC+5")
data2$niv_etude = replace(data2$niv_etude, data2$niv_etude %in% "Baccalauréat général, technologique, professionnel ou équivalent","BAC")
data2 <- data2 %>%
  filter(sexe != "Ne souhaite pas répondre")
data2$logement = replace(data2$logement, !data2$logement %in% c("En maison isolée","En maison mitoyenne"), "Autre")
data2$logement = replace(data2$logement, data2$logement %in% c("En maison isolée","En maison mitoyenne"),"Maison")
data2$activite = replace(data2$activite, !data2$activite %in% "Oui","Non")
options(contrasts=c("contr.sum","contr.sum"))
data2$semaine = factor(data2$semaine)
data2$ID = factor(data2$ID)
data2$sexe = factor(data2$sexe)
data2$niv_etude = factor(data2$niv_etude)
data2$logement = factor(data2$logement)
data2$activite = factor(data2$activite)
freq_sex_week <- data2 %>% 
  filter(semaine == 2) 
data2<-data2[,c(1,2,7,11,12,13)]
data2[,c(2,4,5,6)]<-scale(data2[,c(2,4,5,6)],center = TRUE,scale=TRUE)
data2$semaine<-as.numeric(data2$semaine)
data2$semaine_C <- data2$semaine**2

# Fonction pour calculer le facteur de Bayes (approximation de Laplace)
BFLM <- function(y, X1, X2, g1 = length(y), g2 = length(y)) {
  n <- length(y)
  p1 <- ncol(X1)
  p2 <- ncol(X2)
  
  # Estimation des coefficients pour chaque modèle
  beta1 <- solve(t(X1) %*% X1) %*% t(X1) %*% y
  beta2 <- solve(t(X2) %*% X2) %*% t(X2) %*% y
  
  # Calcul des résidus pour chaque modèle
  S1 <- sum((y - X1 %*% beta1)^2)
  S2 <- sum((y - X2 %*% beta2)^2)
  
  # Calcul du numérateur et du dénominateur
  num <- (g1 + 1)^(-p1 / 2) * (S1 + (t(beta1) %*% t(X1) %*% X1 %*% beta1) / (g1 + 1))^(-(n - 1) / 2)
  den <- (g2 + 1)^(-p2 / 2) * (S2 + (t(beta2) %*% t(X2) %*% X2 %*% beta2) / (g2 + 1))^(-(n - 1) / 2)
  
  return(as.numeric(num / den))
}

#
model<-'
data{
int<lower=1> n;
int<lower=1> p;
vector[n] x;
matrix[n,p] w;
vector[n] y;
vector[n] m;
vector[p+2] betah;
real g;
vector[p+1] alphah;
}
transformed data{
matrix[n,p+1] w1;
matrix[n,p+2] w2;
matrix[p+1,p+1] v1;
matrix[p+2,p+2] v2;
for(i in 1:n){
w1[i,1]=x[i];
w2[i,1]=m[i];
w2[i,2]=x[i];
}
w1[,2:(p+1)]=w;
w2[,3:(p+2)]=w;
v1=inverse(transpose(w1)*w1);
v2=inverse(transpose(w2)*w2);
}
parameters{
real alpha0;
real beta0;
real <lower=0> sigma1;
real <lower=0> sigma2;
vector[p+2] beta;
vector[p+1] alpha;
}

transformed parameters{
real Indirect ;
Indirect=alpha[1]*beta[1];
}
model{
beta~multi_normal(betah,g*(sigma2^2)*v2);
alpha~multi_normal(alphah,g*(sigma1^2)*v1);
y~normal(beta0+w2*beta,sigma2);
m~normal(alpha0+w1*alpha,sigma1);
}
'
library(rstan)
modelOneSample<-stan_model(model_code=model)
set.seed(14)

data2$sexe <- ifelse(data2$sexe == "Femme", 0, 1)


# 3. Boucle sur les semaines et estimation du modèle
resultats <- list()
BF_indirects <- numeric(12)
indirect_distributions <- list()

for (i in 1:12) {
  don <- data2 %>% filter(semaine == i)
  w <- as.matrix(don[, c("sexe", "age")])
  p <- ncol(w)
  
  data_list <- list(
    n = nrow(don),
    p = p,
    x = don$APA,
    y = don$Confiance,
    m = don$Perc_risq,
    w = w,
    g = nrow(don) ,
    betah = numeric(p + 2),
    alphah = numeric(p + 1)
  )
  
  modele <- sampling(modelOneSample, data = data_list, iter = 5000, chains = 1)
  resultats[[i]] <- modele
  
  # Extraction des échantillons de l'effet indirect
  indirect_samples <- extract(modele, "Indirect")$Indirect
  indirect_distributions[[i]] <- indirect_samples
  
  # 4. Calcul du facteur de Bayes pour chaque semaine
  # Modèle 1: Effet indirect présent
  X1 <- cbind(don$Perc_risq,don$sexe,don$age)
  # Modèle 2: Effet indirect absent
  X2 <- cbind(don$APA,don$Perc_risq,don$sexe, don$age) 
  
  BFalpha_1 <- BFLM(don$APA, X1, X1[,-c(1)])
  BFbeta_1 <- BFLM(don$Confiance, X2,X2[,-1])
  BF_indirect <- (BFalpha_1 * BFbeta_1) / (1 + BFbeta_1 + BFalpha_1)
  BF_indirects[i] <- BF_indirect
}


# Calcul de la moyenne et de l'intervalle de crédibilité pour chaque semaine
indirect_means <- sapply(indirect_distributions, mean)
indirect_cis <- t(sapply(indirect_distributions, function(x) quantile(x, c(0.025, 0.975))))
library(ggplot2)

# Création du dataframe pour ggplot
df_plot <- data.frame(
  Semaine = 1:12,
  Indirect_mean = indirect_means,
  IC_lower = indirect_cis[,1],  
  IC_upper = indirect_cis[,2]  
)

# Graphique de l'évolution de l'effet indirect avec intervalle de crédibilité
ggplot(df_plot, aes(x = Semaine, y = Indirect_mean)) +
  geom_line(color = "blue", size = 1.2) +  # Courbe de la moyenne
  geom_point(color = "black", size = 2) +  # Points pour chaque semaine
  geom_ribbon(aes(ymin = IC_lower, ymax = IC_upper), alpha = 0.2, fill = "blue") +  # Intervalle de crédibilité
  labs(title = "Évolution de l'effet indirect avec IC 95%",
       x = "Semaine",
       y = "Effet Indirect (Moyenne)") +
  theme_minimal()

# 5. Analyses supplémentaires

par(mfrow = c(3, 4), mar = c(2, 2, 2, 2))  # Marges plus petites
for (i in 1:12) {
  hist(indirect_distributions[[i]], main = paste("Semaine", i), xlab = "Effet Indirect")
}
par(mfrow = c(1, 1), mar = c(5, 4, 4, 2))  

# 5.2. Tableau des facteurs de Bayes
BF_table <- data.frame(Semaine = 1:12, BF_Indirect = BF_indirects)
# Création du tableau des facteurs de Bayes
BF_table <- data.frame(Semaine = 1:12, BF_Indirect = BF_indirects)
BF_table$Significativite <- cut(
  BF_table$BF_Indirect,
  breaks = c(0, 1, 3, 10, Inf),
  labels = c("Aucune", "Faible", "Modérée", "Forte")
)

ggplot(BF_table, aes(x = factor(Semaine), y = BF_Indirect, fill = Significativite)) +
  geom_bar(stat = "identity") +
  scale_fill_manual(values = c("gray", "red", "yellow", "green")) +
  labs(title = "Facteur de Bayes pour l'effet indirect",
       x = "Semaine",
       y = "Facteur de Bayes") +
  theme_minimal()

library(bayesplot)
# 5.3. Vérification de la convergence MCMC (exemple pour la première semaine)
traceplot(resultats[[1]], pars = c("alpha0", "beta0","beta" ,"sigma1", "sigma2", "Indirect"))
print(summary(resultats[[1]], pars = c("alpha0", "beta0","alpha", "sigma1", "sigma2", "Indirect")))
# Vérification de la convergence pour la première semaine
mcmc_trace(resultats[[1]], pars = c("alpha0", "beta0", "beta", "sigma1", "sigma2", "Indirect"),
           facet_args = list(nrow = 2)) 
#valeur plus petite que 1.1 impliquent la convergence des chaines 
mcmc_dens_chains(resultats[[1]], pars = c("alpha0", "beta0", "beta[1]","beta[2]","beta[3]","beta[4]", "sigma1", "sigma2", "Indirect"),
          facet_args = list(nrow = 2))+
          facet_text(size=14)



#Deuxieme partie 

# Extraction des estimations initiales
initial_beta <- colMeans(extract(resultats[[1]], "beta")$beta)
initial_alpha <- colMeans(extract(resultats[[1]], "alpha")$alpha)

# Boucle pour les semaines suivantes
for (i in 2:12) {
  don <- data2 %>% filter(semaine == i)
  w <- as.matrix(don[, c("sexe", "age")])
  p <- ncol(w)
  
  data_list <- list(
    n = nrow(don),
    p = p,
    x = don$APA,
    y = don$Confiance,
    m = don$Perc_risq,
    w = w,
    g = nrow(don) ,
    betah = initial_beta,  # Utilisation des estimations précédentes
    alphah = initial_alpha  # Utilisation des estimations précédentes
  )
 
  modele <- sampling(modelOneSample, data = data_list, iter = 5000, chains = 1)
  resultats[[i]] <- modele
  # Extraction des échantillons de l'effet indirect
  indirect_samples <- extract(modele, "Indirect")$Indirect
  indirect_distributions[[i]] <- indirect_samples
  
  # 4. Calcul du facteur de Bayes pour chaque semaine
  # Modèle 1: Effet indirect présent
  X1 <- cbind(don$Perc_risq,don$sexe,don$age)
  # Modèle 2: Effet indirect absent
  X2 <- cbind(don$APA,don$Perc_risq,don$sexe, don$age) 
  
  BFalpha_1 <- BFLM(don$APA, X1, X1[,-c(1)])
  BFbeta_1 <- BFLM(don$Confiance, X2,X2[,-1])
  BF_indirect <- (BFalpha_1 * BFbeta_1) / (1 + BFbeta_1 + BFalpha_1)
  BF_indirects[i] <- BF_indirect
  # Mise à jour des estimations initiales pour la prochaine itération
  initial_beta <- colMeans(extract(modele, "beta")$beta)
  initial_alpha <- colMeans(extract(modele, "alpha")$alpha)
}
  
 
  # 5. Analyses supplémentaires
  
  par(mfrow = c(3, 4), mar = c(2, 2, 2, 2))  
  for (i in 2:12) {
    hist(indirect_distributions[[i]], main = paste("Semaine", i), xlab = "Effet Indirect")
  }
  
  # Calcul de la moyenne et de l'intervalle de crédibilité pour chaque semaine
  indirect_means <- sapply(indirect_distributions, mean)
  indirect_cis <- t(sapply(indirect_distributions, function(x) quantile(x, c(0.025, 0.975))))
  library(ggplot2)
  
  # Création du dataframe pour ggplot
  df_plot <- data.frame(
    Semaine = 1:12,
    Indirect_mean = indirect_means,
    IC_lower = indirect_cis[,1],  
    IC_upper = indirect_cis[,2]  
  )
  
  # Graphique de l'évolution de l'effet indirect avec intervalle de crédibilité
  ggplot(df_plot, aes(x = Semaine, y = Indirect_mean)) +
    geom_line(color = "blue", size = 1.2) +  # Courbe de la moyenne
    geom_point(color = "black", size = 2) +  # Points pour chaque semaine
    
    geom_ribbon(aes(ymin = IC_lower, ymax = IC_upper), alpha = 0.2, fill = "blue") +  # Intervalle de crédibilité
    labs(title = "Évolution de l'effet indirect avec IC 95%",
         x = "Semaine",
         y = "Effet Indirect (Moyenne)") +
    theme_minimal()
  
  # 5. Analyses supplémentaires
  
  par(mfrow = c(3, 4), mar = c(2, 2, 2, 2))  # Marges plus petites
  for (i in 1:12) {
    hist(indirect_distributions[[i]], main = paste("Semaine", i), xlab = "Effet Indirect")
  }
  par(mfrow = c(1, 1), mar = c(5, 4, 4, 2))  
  
  # 5.2. Tableau des facteurs de Bayes
  BF_table <- data.frame(Semaine = 1:12, BF_Indirect = BF_indirects)
  # Création du tableau des facteurs de Bayes
  BF_table <- data.frame(Semaine = 1:12, BF_Indirect = BF_indirects)
  BF_table$Significativite <- cut(
    BF_table$BF_Indirect,
    breaks = c(0, 1, 3, 10, Inf),
    labels = c("Aucune", "Faible", "Modérée", "Forte")
  )
  
  ggplot(BF_table, aes(x = factor(Semaine), y = BF_Indirect, fill = Significativite)) +
    geom_bar(stat = "identity") +
    scale_fill_manual(values = c("gray", "red", "yellow", "green")) +
    labs(title = "Facteur de Bayes pour l'effet indirect",
         x = "Semaine",
         y = "Facteur de Bayes") +
    theme_minimal()
  
  library(bayesplot)
  # 5.3. Vérification de la convergence MCMC (exemple pour la première semaine)
  traceplot(resultats[[1]], pars = c("alpha0", "beta0","beta" ,"sigma1", "sigma2", "Indirect"))
  print(summary(resultats[[1]], pars = c("alpha0", "beta0","alpha", "sigma1", "sigma2", "Indirect")))
  # Vérification de la convergence pour la première semaine
  mcmc_trace(resultats[[1]], pars = c("alpha0", "beta0", "beta", "sigma1", "sigma2", "Indirect"),
             facet_args = list(nrow = 2)) 
  #valeur plus petite que 1.1 impliquent la convergence des chaines 
  mcmc_dens_chains(resultats[[2]], pars = c("alpha0", "beta0", "beta[1]","beta[2]","beta[3]","beta[4]", "sigma1", "sigma2", "Indirect"),
                  )+
    facet_text(size=14)
  plot(mean_indirect_lineaire)
  
 df_linear<-data.frame(
   Semaine = 1:12,
   mean_indirect_lineaire = mean_indirect_lineaire)
  
  ggplot() +
    geom_line(data = df_plot, aes(x = Semaine, y = Indirect_mean, color = "Moyenne (Non-linéaire)"), size = 1.2) +
    geom_point(data = df_plot, aes(x = Semaine, y = Indirect_mean), color = "black", size = 2) +
    geom_line(data = df_linear, aes(x = Semaine, y = mean_indirect_lineaire, color = "Moyenne (Linéaire)"), size = 1.2, linetype = "dashed") +
    scale_color_manual(values = c("moyenne(simple)" = "blue", "Moyenne (Linéaire)" = "red")) + # Choose your colors
    labs(title = "Évolution de l'Effet Indirect",
         x = "Semaine",
         y = "Effet Indirect") +
    theme_minimal() +
    theme(legend.title = element_blank()) # Optional: Remove legend title