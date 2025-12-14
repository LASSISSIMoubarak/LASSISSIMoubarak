# Récupération et conversion en vecteur numérique
Data = read.table("L'adresse de votre fichier data-gauss.txt", header=FALSE)
X = Data[[1]]
n = length(X)

M = mean(X)
Q = sum(X**2)
n = length(X)
N = 10000

# Majoration du ratio f_tilde/g_tilde (f_tilde et g_tilde obtenues par proportionnalité)
Cst = exp(n/2*M**2-Q/2)

# On simule N variables par acceptation/rejet
# On compte le nombre d'itérations nécessaires pour obtenir une simulation valable
T = rep(0, N)
Nb = rep(0, N)
for (i in 1:N){
	cont = TRUE
	cpt = 0
	
	# On simule tant que la condition u <= f_tilde(z) n'est pas satisfaite
	# Avec z simulée selon la loi instrumentale
	while (cont){
		cpt = cpt+1
		z = rnorm(1, M, sqrt(1/n)) # Loi instrumentale
		u = runif(1, 0, Cst*exp(-n/2*(z-M)**2)) # Uniforme sur [0, Cst g_tilde(z)]
		if (u <= exp(-sum((X-z)**2)/2)/(1+z**2)){ # Acceptation
			T[i] = z
			Nb[i] = cpt
			cont = FALSE
		}
	}
}

# Graphique de la densité estimée
hist(T, breaks=sqrt(N), col="gray", freq=FALSE, main="Densité a posteriori estimée")
lines(density(T), col="red")

# Nombre de tirages nécessaires pour l'acceptation
boxplot(Nb, col="forestgreen", main="Nombre de tirages avant acceptation")
grid()
mean(Nb)
quantile(Nb)
