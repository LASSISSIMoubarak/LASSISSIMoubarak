
# Densités a priori
B = seq(0.05, 0.65, 0.1)
P = c(0.03, 0.18, 0.28, 0.25, 0.16, 0.07, 0.03)
plot(B, P, type="h", xlim=c(0, 1), ylim=c(0, 3), lwd=2, col="blue",
	main="Densités a priori", xlab="p", ylab="")
lines(B, P, type="p", lwd=2, col="blue", pch=16)
curve(dbeta(x, 3.4, 7.4), lwd=2, col="red", add=TRUE)
curve(dbeta(x, 0.5, 0.5), lwd=2, col="forestgreen", add=TRUE)
grid()
legend("topright", legend=c("Mod A", "Mod B", "Mod C"),
	col=c("blue", "red", "forestgreen"), lwd=2)


# Marginales de S
MA = rep(0, 28)
MB = rep(0, 28)
MC = rep(0, 28)
for (k in 0:27){
	MA[k+1] = choose(27, k)*sum(B**k*(1-B)**(27-k)*P)
	MB[k+1] = choose(27, k)*beta(k+3.4, 34.4-k)/beta(3.4, 7.4)
	MC[k+1] = choose(27, k)*beta(k+1/2, 27.5-k)/beta(1/2, 1/2)
}
plot(0:27, MA, lwd=2, type="o", col="blue",
	main="Densités marginales", xlab="S", ylab="")
lines(0:27, MB, lwd=2, type="o", col="red",
	main="Densités marginales", xlab="S", ylab="")
lines(0:27, MC, lwd=2, type="o", col="forestgreen",
	main="Densités marginales", xlab="S", ylab="")
grid()
legend("topright", legend=c("Mod A", "Mod B", "Mod C"),
	col=c("blue", "red", "forestgreen"), lwd=2)


# Facteurs de Bayes
BAB = MA[12]/MB[12]
BAC = MA[12]/MC[12]
BBC = MB[12]/MC[12]
# B > A >> C


# Superpositions a priori/a posteriori
B = seq(0.05, 0.65, 0.1)
P = c(0.03, 0.18, 0.28, 0.25, 0.16, 0.07, 0.03)
S = 11
PosA = B**S*(1-B)**(27-S)*P
PosA = PosA/sum(PosA)
plot(B, P, type="h", xlim=c(0, 1), ylim=c(0, 5), lty=2, col="blue",
	main="Densités a priori/a posteriori", xlab="p", ylab="")
lines(B, P, type="p", col="blue", pch=1)
lines(B, PosA, type="h", lwd=2, col="blue")
lines(B, PosA, type="p", lwd=2, col="blue", pch=16)
curve(dbeta(x, 3.4, 7.4), lty=2, col="red", add=TRUE)
curve(dbeta(x, 3.4+S, 34.4-S), lwd=2, col="red", add=TRUE)
curve(dbeta(x, 0.5, 0.5), lty=2, col="forestgreen", add=TRUE)
curve(dbeta(x, 0.5+S, 27.5-S), lwd=2, col="forestgreen", add=TRUE)
grid()
legend("topright", legend=c("Pri A", "Pos A", "Pri B", "Pos B", "Pri C", "Pos C"),
	col=c("blue", "blue", "red", "red", "forestgreen", "forestgreen"),
	lwd=c(1, 2, 1, 2, 1, 2), lty=c(2, 1, 2, 1, 2, 1))


# Régions HPD
PosA[3]+PosA[4]+PosA[5]
PosA[2]+PosA[3]+PosA[4]+PosA[5]
PosA[3]+PosA[4]+PosA[5]+PosA[6] # HPD Mod A

# Version approximative : rechercher sur tous les IC de taille 95%...
qbeta(c(0.025, 0.975), S+3.4, 34.4-11) # HPD Mod B -> plus court que Mod C
qbeta(c(0.025, 0.975), S+1/2, 27.5-11) # HPD Mod C


# Loi prédictive pour Mod B
SPredThB = rep(0, 21)
for (k in 0:20){
	SPredThB[k+1] = choose(20, k)*beta(k+14.4, 43.4-k)/beta(14.4, 23.4)
}

# Simulation
M = 1000
SPred = rep(0, M)
for (k in 1:M){
	p = rbeta(1, 14.4, 23.4)
	SPred[k] = rbinom(1, 20, p)
}
DensSPred = rep(0, 21)
for (i in 0:20){
	DensSPred[i+1] = sum(SPred == i)/M
}

# Densité de la loi prédictive
plot(0:20, DensSPred, col="gray", type="h", main="Densité de S* | S",
	xlab="S*", ylab="", ylim=c(0, 0.2))
lines(0:20, DensSPred, col="gray", type="p", pch=16)
lines(0:20, SPredThB, col="red", type="h", lty=2)
lines(0:20, SPredThB, col="red", type="p", pch=16)
grid()
legend("topright", legend=c("Théorique", "Estimée"),
	col=c("red", "gray"), lwd=2, lty=c(2, 1))


# Loi prédictive pour Mod C
SPredThC = rep(0, 21)
for (k in 0:20){
	SPredThC[k+1] = choose(20, k)*beta(k+11.5, 36.5-k)/beta(11.5, 16.5)
}

# Simulation
M = 1000
SPred = rep(0, M)
for (k in 1:M){
	p = rbeta(1, 11.5, 16.5)
	SPred[k] = rbinom(1, 20, p)
}
DensSPred = rep(0, 21)
for (i in 0:20){
	DensSPred[i+1] = sum(SPred == i)/M
}

# Densité de la loi prédictive
plot(0:20, DensSPred, col="gray", type="h", main="Densité de S* | S",
	xlab="S*", ylab="", ylim=c(0, 0.2))
lines(0:20, DensSPred, col="gray", type="p", pch=16)
lines(0:20, SPredThC, col="red", type="h", lty=2)
lines(0:20, SPredThC, col="red", type="p", pch=16)
grid()
legend("topright", legend=c("Théorique", "Estimée"),
	col=c("red", "gray"), lwd=2, lty=c(2, 1))


# Loi prédictive pour Mod A
SPredThA = rep(0, 21)
for (k in 0:20){
	SPredThA[k+1] = choose(20, k)*sum( B**(11+k)*(1-B)**(36-k)*P )
}
SPredThA = SPredThA/sum(SPredThA)

PPred = P*B**11*(1-B)**16
PPred = PPred/sum(PPred)

# Simulation
M = 1000
SPred = rep(0, M)
for (k in 1:M){
	p = sample(B, 1, prob=PPred)
	SPred[k] = rbinom(1, 20, p)
}

DensSPred = rep(0, 21)
for (i in 0:20){
	DensSPred[i+1] = sum(SPred == i)/M
}

# Densité de la loi prédictive
plot(0:20, DensSPred, col="gray", type="h", main="Densité de S* | S",
	xlab="S*", ylab="", ylim=c(0, 0.2))
lines(0:20, DensSPred, col="gray", type="p", pch=16)
lines(0:20, SPredThA, col="red", type="h", lty=2)
lines(0:20, SPredThA, col="red", type="p", pch=16)
grid()
legend("topright", legend=c("Théorique", "Estimée"),
	col=c("red", "gray"), lwd=2, lty=c(2, 1))


# Superposition des lois prédictives
plot(0:20, SPredThA, col="blue", type="h", main="Densité de S* | S",
	xlab="S*", ylab="", ylim=c(0, 0.2))
lines(0:20, SPredThA, col="blue", type="p", pch=16)
lines(0:20, SPredThB, col="red", type="h", main="Densité de S* | S",
	xlab="S*", ylab="", ylim=c(0, 0.2))
lines(0:20, SPredThB, col="red", type="p", pch=16)
lines(0:20, SPredThC, col="forestgreen", type="h", main="Densité de S* | S",
	xlab="S*", ylab="", ylim=c(0, 0.2))
lines(0:20, SPredThC, col="forestgreen", type="p", pch=16)
grid()
legend("topright", legend=c("Mod A", "Mod B", "Mod C"),
	col=c("blue", "red", "forestgreen"), lwd=2)




