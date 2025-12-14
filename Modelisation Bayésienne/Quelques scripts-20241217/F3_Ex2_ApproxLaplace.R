
# Superposition a priori/a posteriori
curve(dexp(x, 1), col="blue", lty=2, xlim=c(0, 2), ylim=c(0, 3),
	xlab=expression(theta), ylab="Densités")
curve(dgamma(x, shape=11, rate=22), col="red", lwd=2, add=TRUE)
legend("topright", legend=c(expression(pi(theta)), expression(pi(theta~"|"~y))),
	col=c("blue", "red"), lwd=c(1, 2), lty=c(2, 1))
grid()

# A posteriori de ln(theta) et approximation de Laplace
curve(exp(11*x)*exp(-22*exp(x))/(22**(-11)*gamma(11)), col="red", lwd=2, xlim=c(-2, 1),
	xlab=expression(ln(theta)), ylab="Densités")
curve(dnorm(x, log(11/22), sqrt(1/11)), col="blue", lty=2, add=TRUE)
legend("topright", legend=c(expression(pi(ln(theta)~"|"~y)), "Approx Laplace"),
	col=c("red", "blue"), lwd=c(2, 1), lty=c(1, 2))
grid()

# A posteriori de theta et approximation de Laplace
curve(dgamma(x, shape=11, rate=22), col="red", lwd=2, xlim=c(0, 2), ylim=c(0, 3),
	xlab=expression(theta), ylab="Densités")
curve(dlnorm(x, log(11/22), sqrt(1/11)), col="blue", lty=2, add=TRUE)
legend("topright", legend=c(expression(pi(theta~"|"~y)), "Approx Laplace"),
	col=c("red", "blue"), lwd=c(2, 1), lty=c(1, 2))
grid()


# Algorithme de Metropolis-Hastings pour estimer la loi a posteriori de ln(theta)
# Loi instrumentale : approximation de Laplace
N = 10000
x = rep(0, N)
x[1] = rexp(1)
for (t in 2:N){
	e = rnorm(1, log(11/22), sqrt(1/11))
	rf = exp(11*(e-x[t-1]))*exp(-22*(exp(e)-exp(x[t-1])))
	rq = dnorm(x[t-1], log(11/22), sqrt(1/11))/dnorm(e, log(11/22), sqrt(1/11))
	rho = min(1, rf*rq)
	u = runif(1)
	if (u < rho){
		x[t] = e
	} else{
		x[t] = x[t-1]
	}
}

# Graphique de la densité a posteriori estimée de ln(theta)
hist(x, breaks=sqrt(N), col="gray", freq=FALSE, main="Densité a posteriori estimée",
	xlab=expression(ln(theta)), ylab="Densités")
lines(density(x), col="black")
curve(exp(11*x)*exp(-22*exp(x))/(22**(-11)*gamma(11)), col="red", lwd=2, xlim=c(-2, 1),
	xlab=expression(ln(theta)), ylab="Densités", add=TRUE)

# Graphique de la densité a posteriori estimée de theta
y = exp(x)
hist(y, breaks=sqrt(N), col="gray", freq=FALSE, main="Densité a posteriori estimée",
	xlab=expression(theta), ylab="Densités")
lines(density(y), col="black")
curve(dgamma(x, shape=11, rate=22), col="red", lwd=2, xlim=c(0, 2), ylim=c(0, 3), add=TRUE)


# Algorithme de Metropolis-Hastings pour estimer la loi a posteriori de ln(theta)
# Loi instrumentale : marche aléatoire gaussienne de variance issue de l'approximation de Laplace
N = 10000
x = rep(0, N)
x[1] = rexp(1)
for (t in 2:N){
	e = x[t-1] + rnorm(1, 0, sqrt(1/11))
	rf = exp(11*(e-x[t-1]))*exp(-22*(exp(e)-exp(x[t-1])))
	rho = min(1, rf)
	u = runif(1)
	if (u < rho){
		x[t] = e
	} else{
		x[t] = x[t-1]
	}
}

# Graphique de la densité a posteriori estimée de ln(theta)
hist(x, breaks=sqrt(N), col="gray", freq=FALSE, main="Densité a posteriori estimée",
	xlab=expression(ln(theta)), ylab="Densités")
lines(density(x), col="black")
curve(exp(11*x)*exp(-22*exp(x))/(22**(-11)*gamma(11)), col="red", lwd=2, xlim=c(-2, 1), add=TRUE)

# Graphique de la densité a posteriori estimée de theta
y = exp(x)
hist(y, breaks=sqrt(N), col="gray", freq=FALSE, main="Densité a posteriori estimée",
	xlab=expression(theta), ylab="Densités")
lines(density(y), col="black")
curve(dgamma(x, shape=11, rate=22), col="red", lwd=2, xlim=c(0, 2), ylim=c(0, 3),
	xlab=expression(theta), ylab="Densités", add=TRUE)


