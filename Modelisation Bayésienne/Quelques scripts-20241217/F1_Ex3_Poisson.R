# Superposition prior/posterior pour Y=5
X = 0:18
plot(X, dpois(X, 5), type="h", col="blue", lwd=2, ylim=c(0, 0.22),
     xlab="Nombre de clients", ylab="Proba")
lines(X, dpois(X, 5), type="p", col="blue", pch=16)
lines(X+5, dpois(X, 4), type="h", col="magenta", lwd=2)
lines(X+5, dpois(X, 4), type="p", col="magenta", pch=16)
legend("topright", legend=c(expression(pi(N)), expression(pi(N~"|"~Y~"="~5))),
       col=c("blue", "magenta"), lwd=2)
grid()

m = 10**3
N = 5+rpois(m, 4)
mean(N) # valeur théorique : 9
median(N) # environ 9
quantile(N, c(0.025, 0.975))

