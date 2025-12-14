# Observations
X = c(125, 18, 20, 34)

# Paramètres de la chaîne
N = 100000
x = rep(0, N)
s2 = 1
s = sqrt(s2)

# Valeur initiale
x[1] = rnorm(1)

for (i in 2:N){
	# Marche aléatoire de bruit N(0, s2)
	eta = x[i-1] + rnorm(1, 0, s)

	# Taux d'acceptation calculé en plusieurs étapes (pour des aspects numériques)
	t11 = 2 + exp(eta)/(1+exp(eta))
	t12 = 2 + exp(x[i-1])/(1+exp(x[i-1]))
	t1 = (t11/t12)**X[1]
	t21 = exp((1+X[4])*(eta - x[i-1]))
	t22 = ((1+exp(eta))/(1+exp(x[i-1])))**(-(X[2]+X[3]+X[4]+2))
	t2 = t21*t22
	rho = min(1, t1*t2)

	# Nouvelle valeur adoptée avec proba rho
	# Ancienne valeur dupliquée avec proba 1-rho
	u = runif(1)
	if (u < rho){
		x[i] = eta
	} else{
		x[i] = x[i-1]
	}
}

# Loi stationnaire estimée de la chaîne de Markov en eta
hist(x, breaks=sqrt(N), col="gray", freq=FALSE, main="Loi stationnaire estimée (pour eta)")
lines(density(x), col="red", lwd=2)
grid()

t = exp(x)/(1+exp(x))
# Loi stationnaire estimée de la chaîne de Markov en theta
hist(t, breaks=sqrt(N), col="gray", freq=FALSE, xlim=c(0, 1), main="Loi stationnaire estimée (pour theta)")
lines(density(t), col="red", lwd=2)
grid()

# Estimateur de Bayes (coût L2)
mean(t)

# Recherche du plus court IC à 95%
Eps = seq(0.001, 0.049, by=0.001)
LongIC = c()
for (e in Eps){
	Quant = quantile(t, c(e, 0.95+e))
	LongIC = c(LongIC, Quant[2]-Quant[1])
}
EpsOpt = Eps[which.min(LongIC)]

# Plus cours IC à 95% :
quantile(t, c(EpsOpt, 0.95+EpsOpt))



