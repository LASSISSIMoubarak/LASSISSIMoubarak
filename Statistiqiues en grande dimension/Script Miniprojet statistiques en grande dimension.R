library(pls)
library(ggplot2)
library(gridExtra)
set.seed(4433)
# Chargement des données
data(gasoline)
Y <- gasoline[,1]
X <- gasoline[,2]
n <- nrow(X)
p <- ncol(X)
plot(seq(900, 1700, 2), X[1, ], type="l", lwd=2, xlab="nm", ylab="NIR", main="")
grid()
# ACP Normée
pca <- prcomp(X, center = TRUE, scale. = FALSE)
summary(pca)
# Screeplot avec ggplot
Inertie_ex<- pca$sdev^2 / sum(pca$sdev^2) #Inertie_ex signifie Inertie Explquée par chaque composante
data_p <- data.frame(Cp = 1:60, Variance = Inertie_ex[1:60])

ggplot(data_p, aes(x = factor(Cp), y = Variance)) +
  geom_bar(stat = "identity", fill = "steelblue") +
  geom_line(aes(group = 1), color = "red", linewidth = 1) +
  geom_point(color = "red", size = 3) +
  labs(x = "Composante Principale", y = "Inertie Explquée par chaque composante",
       title = "Screeplot de l'ACP") +
  theme_minimal()

#Tirage   au sort de 50 observation , on le fait sans remise
tirage_in <- sample(1:n, 50) #Tirage sur des indices de 50
XTrain <- X[tirage_in, ]
YTrain <- Y[tirage_in]
XVal <- X[-tirage_in, ]
YVal <- Y[-tirage_in]

# PCR avec validation croisée LOO
PCR <- pcr(YTrain ~ XTrain, validation = "LOO", scale = TRUE)

validationplot(PCR, val.type="RMSEP", type="b", pch=16)
 grid()
 #Extraction des loading et visualisation
 par(mar=c(2, 2, 2, 2))  # Réglage des marges
 par(mfrow=c(3, 2))  # Diviser la fenêtre graphique en 3 lignes et deux colonnes
 
 # Premier composante
 plot(PCR$loadings[,1], type="l", col="blue", main="Loading 1", xlab="Index", ylab="Value")
 grid()
 
 # Deuxième composante
 plot(PCR$loadings[,2], type="l", col="red", main="Loading 2", xlab="Index", ylab="Value")
 grid()
 
 # Troisième composante
 plot(PCR$loadings[,3], type="l", col="green", main="Loading 3", xlab="Index", ylab="Value")
 grid()
 #Quatrième composante
 plot(PCR$loadings[,4], type="l", col="blue", main="Loading 4", xlab="Index", ylab="Value")
 grid()
 #Cinquième composante
 plot(PCR$loadings[,5], type="l", col="black", main="Loading 5", xlab="Index", ylab="Value")
 grid()
 #Sixième composante
 plot(PCR$loadings[,6], type="l", col="gray", main="Loading 6", xlab="Index", ylab="Value")
 grid()
 #Calcul de RMSE de validation , il faut calculer la prediction sur les données test
 predictions <- predict(PCR, XVal,ncomp = 6)
 
 RMSE <- sqrt(mean((predictions - YVal)^2))
 print(RMSE)
 
 