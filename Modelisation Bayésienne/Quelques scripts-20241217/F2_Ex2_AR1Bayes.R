# Récupération et conversion en vecteur numérique
Data = read.table("Mettre l'adresse de ARmodel.txt", header=FALSE)
Data = Data[[1]]

# Simule un échantillon de taille npred selon la loi prédictive sachant XObs
SimuPred = function(XObs, npred){
	nobs = length(XObs)
	Q = sum(XObs^2)
	P = sum(X[1:(nobs-1)]*X[2:nobs])
	V = (1 + Q - XObs[nobs]**2)/(1 + Q)
	XPred = rnorm(npred, XObs[nobs]*P/((1 + Q)*V), sqrt(1/V))
	return(XPred)
}

n = 50
X = Data[1:n]

# Large simulation selon la loi prédictive à partir des 50 premières valeurs de X
XPred = SimuPred(X, 10000)

# Graphique de la densité estimée
hist(XPred, breaks=sqrt(10000), col="gray", freq=FALSE, main="Densité estimée de X(n+1) | X(n), ..., X(1)")
lines(density(XPred), col="red")
grid()

# Recherche du plus court IC à 95%
Eps = seq(0.001, 0.049, by=0.001)
LongIC = c()
for (e in Eps){
	Quant = quantile(XPred, c(e, 0.95+e))
	LongIC = c(LongIC, Quant[2]-Quant[1])
}
QOpt = min(LongIC)
EpsOpt = Eps[which.min(LongIC)] # Sans surprise vu la taille de l'échantillon : environ 2.5% - 97.5%

# Pour le coût L2
EstPred = mean(XPred)
Data[51] # Il faut voir avec les IC

# Pour n=50, ..., 54, on estime la loi prédictive de X(n+1) sachant X(n), ..., X(1)
# On récupère les bornes à 95% et l'estimateur ponctuel
BInf = rep(0, 5)
BSup = rep(0, 5)
Est = rep(0, 5)
for (n in 50:54){
	X = Data[1:n]
	XPred = SimuPred(X, 10000)
	Quant = quantile(XPred, c(0.025, 0.975)) # On ne fait plus de recherche optimale, pour simplifier
	BInf[n-49] = Quant[1]
	BSup[n-49] = Quant[2]
	Est[n-49] = mean(XPred)
}

# Représentation graphique
plot(Data, type="l", main="", xlab="t", ylab="X(t)")
polygon(c(51:55, 55:51), c(BInf, rev(BSup)), col=rgb(1, 0.5, 0, 0.1), border=NA)
lines(51:55, Est, type="l", col="red", lwd=2, lty=2)
lines(51:55, Data[51:55], type="l", col="black")
grid()
legend("topright", col=c("orange", "red"), lwd=2, lty=c(1, 2), legend=c("IC 95%", "Pred")) 












 
