# Charger le package
library(invgamma)
library(ggplot2)
# Définir les paramètres
alpha <- 3  # Shape
beta <- 2   # Scale

# Simuler à partir de la distribution Gamma inverse
n <- 1000
X <- rinvgamma(n, shape = alpha, scale = beta)
data<-data.frame(x=X)
# Visualiser les résultats
ggplot(data,aes(x=x))+
geom_histogram(aes(y=..density..),bins = 30,color="black")+
geom_density(color="red",size=1)+
theme_minimal()
