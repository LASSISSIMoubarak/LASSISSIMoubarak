# Récupération et conversion en vecteur numérique
Data = read.table("L'adresse de votre fichier duree-de-vie.txt", header=FALSE)
X = Data[[1]]

# Superposition de l'a priori avec les a posteriori pour plusieurs n
# On passe a et b (a priori de theta) en paramètres
GraphGamma = function(X, a, b){
	curve(dgamma(x, shape=a, rate=b), col="black", xlim=c(0, 5), ylim=c(0, 5))
	c = 1
	for (n in c(2, 5, 10, 100, 500, 1000)){
		M = mean(X[1:n])
		c = c+1
		curve(dgamma(x, shape=n+a, rate=n*M+b), col=c, add=TRUE)
	}
	grid()
	legend("topright", legend=c("n=0", "n=2", "n=5", "n=10", "n=100", "n=500", "n=1000"), col=1:7, lwd=1)
	# On voit que l'a posteriori se concentre sur 0.5 avec n
}

# Evolution de E[theta | X] et Var(theta | X) en fonction de n
# On passe a et b (a priori de theta) en paramètres
GraphEV = function(X, a, b){
	E = rep(0, 1001)
	V = rep(0, 1001)
	E[1] = a/b
	V[1] = a/b**2
	for (n in 1:1000){
		M = mean(X[1:n])
		E[n+1] = (n+a)/(n*M+b)
		V[n+1] = (n+a)/(n*M+b)**2
	}
	plot(0:n, E, type="p", pch="x", col="black", ylim=c(0, 1), main="", xlab="n", ylab="A posteriori")
	lines(0:n, V, type="p", pch="o", col="red")
	grid()
	legend("topright", legend=c("E[theta | X]", "V(theta | X)"), col=c("black", "red"), pch=c("x", "o"))
}

# Trace les bornes du plus court IC théorique à 95% en fonction de n
# Renvoie l'IC pour la dernière valeur de n
ICGamma = function(X, a, b){
	BI = rep(0, 1001)
	BS = rep(0, 1001)

	Eps = seq(0.001, 0.049, by=0.001)
	
	# Recherche "manuelle" du plus court IC
	LongIC = c()
	for (e in Eps){
		Quant = qgamma(c(e, 0.95+e), shape=a, rate=b)
		LongIC = c(LongIC, Quant[2]-Quant[1])
	}
	EpsOpt = Eps[which.min(LongIC)]
	BI[1] = qgamma(EpsOpt, shape=a, rate=b)
	BS[1] = qgamma(0.95+EpsOpt, shape=a, rate=b)

	for (n in 1:1000){
		M = mean(X[1:n])

		# Recherche "manuelle" du plus court IC
		LongIC = c()
		for (e in Eps){
			Quant = qgamma(c(e, 0.95+e), shape=n+a, rate=n*M+b)
			LongIC = c(LongIC, Quant[2]-Quant[1])
		}
		EpsOpt = Eps[which.min(LongIC)]
		BI[n+1] = qgamma(EpsOpt, shape=n+a, rate=n*M+b)
		BS[n+1] = qgamma(0.95+EpsOpt, shape=n+a, rate=n*M+b)
	}

	plot(0:n, BI, type="l", col="red", ylim=c(0, 1), main="", xlab="n", ylab="IC à 95%")
	lines(0:n, BS, type="l", col="red")
	grid()
	return(c(BI[1001], BS[1001]))
}

# Avec un a priori d'espérance 1/2 :

# Var(theta) = 1/2 : (a, b) = (1/2, 1)
GraphGamma(X, 1/2, 1)
GraphEV(X, 1/2, 1)
ICGamma(X, 1/2, 1)

# Var(theta) = 1/100 : (a, b) = (25, 50)
GraphGamma(X, 25, 50)
GraphEV(X, 25, 50)
ICGamma(X, 25, 50)

# Var(theta) = 1/10 : (a, b) = (2.5, 5)
GraphGamma(X, 2.5, 5)
GraphEV(X, 2.5, 5)
ICGamma(X, 2.5, 5)

# Var(theta) = 10 : (a, b) = (1/40, 1/20)
GraphGamma(X, 1/40, 1/20)
GraphEV(X, 1/40, 1/20)
ICGamma(X, 1/40, 1/20)

# Var(theta) = 100 : (a, b) = (1/400, 1/200)
GraphGamma(X, 1/400, 1/200)
GraphEV(X, 1/400, 1/200)
ICGamma(X, 1/400, 1/200)

# On observe que lorsque tau est petit, n n'a pas besoin d'être très grand pour qu'on se concentre sur 0.5 (ex : 1/100)
# Au contraire lorsque tau est grand (ex : 100), il faut n plus grand pour récupérer le centrage en 0.5


# Avec un a priori d'espérance 3 :

# Var(theta) = 1/2 : (a, b) = (18, 6)
GraphGamma(X, 18, 6)
GraphEV(X, 18, 6)
ICGamma(X, 18, 6)

# Var(theta) = 1/100 : (a, b) = (900, 300)
GraphGamma(X, 900, 300)
GraphEV(X, 900, 300)
ICGamma(X, 900, 300)
# Beaucoup plus long à se stabiliser autour de 0.5 : l'a priori est à la fois très concentré et très mauvais

# Var(theta) = 1/10 : (a, b) = (90, 30)
GraphGamma(X, 90, 30)
GraphEV(X, 90, 30)
ICGamma(X, 90, 30)

# Var(theta) = 10 : (a, b) = (0.9, 0.3)
GraphGamma(X, 0.9, 0.3)
GraphEV(X, 0.9, 0.3)
ICGamma(X, 0.9, 0.3)

# Var(theta) = 100 : (a, b) = (0.09, 0.03)
GraphGamma(X, 0.09, 0.03)
GraphEV(X, 0.09, 0.03)
ICGamma(X, 0.09, 0.03)




