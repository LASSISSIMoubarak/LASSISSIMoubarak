
# Echantillon N(0, 1)
n = 10
X = rnorm(n)
m = mean(X)

# Echantillonnage selon la loi a posteriori
tau2 = 2
N = 10**4
T = rnorm(N, m/(1+tau2/n), sqrt(1/(n+tau2)))
hist(T, main="Loi empirique a posteriori", freq=FALSE, ylim=c(0, 1.5))
lines(density(T), col="red", lty=2) # Empirique
curve(dnorm(x, m/(1+tau2/n), sqrt(1/(n+tau2))), col="forestgreen", lwd=2, add=TRUE) # Théorique
grid()

# Densité a posteriori sur L
L = dnorm(T, m/(1+tau2/n), sqrt(1/(n+tau2)))
Lt = sort(L)

a = 0.05
i = floor(N*a)
K = Lt[i]
H = T[L > K]

# HPD empirique
l = min(H)
u = max(H)

plot(T, L, xlab="", ylab="Posterior", main="A posteriori et HPD empirique")
LH = L[L > K]
lines(H, LH, type="p", col="red", pch=2)
abline(h=0, col="black")
lines(H, 0*H, type="p", col="red", pch=4)
lines(c(min(H), min(H)), c(0, LH[which.min(H)]), col="red")
lines(c(max(H), max(H)), c(0, LH[which.max(H)]), col="red")
text(mean(H), 0.1, paste("HPD à", (1-a)*100, "%"), col="red")
grid()

# HPD théorique
lth = m/(1+tau2/n) - qnorm(1-a/2)/sqrt(n+tau2)
uth = m/(1+tau2/n) + qnorm(1-a/2)/sqrt(n+tau2)

# Intervalles de crédibilité pour différents b (a=5%)
a = 0.05
pas = 1/1000
B = seq(pas, a-pas, pas)

UTH = qnorm(1-a+B, m/(1+tau2/n), sqrt(1/(n+tau2)))
LTH = qnorm(B, m/(1+tau2/n), sqrt(1/(n+tau2)))

plot(B, UTH, col="magenta", type="l", lwd=2, ylim=c(min(LTH), max(UTH)),
	xlab=expression(beta), ylab="", main="Evolution des IC à 95% avec b")
lines(B, LTH, col="blue", type="l", lwd=2)
grid()
legend("right", legend=c("Upper", "Lower"), col=c("magenta", "blue"), lwd=2)

# Beta optimal
ilopt = which.min(UTH-LTH)
B[ilopt] # a/2 : résultat attendu par symétrie de la densité

# Longueur des IC avec b (a=5%)
plot(B, UTH-LTH, col="forestgreen", lwd=2, type="l",
	main="Longueur des IC à 95% avec b", ylab="Longueur des IC", xlab=expression(beta))
points(B[ilopt], UTH[ilopt]-LTH[ilopt], col="red", pch=4, lwd=3)
grid()

