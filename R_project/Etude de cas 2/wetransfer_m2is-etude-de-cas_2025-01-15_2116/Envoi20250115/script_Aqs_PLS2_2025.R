###########################################
#      LIGNES DE CODES PRELIMINAIRES      #
###########################################


library(FactoMineR)
library(MASS)
library(RODBC)
library(stringr)
library(car)
library(corrplot)
library(rstatix)
library(factoextra)
library(pls)

#Fonctions VIP et VIPjh
## VIP returns all VIP values for all variables and all number of components,
## as a ncomp x nvars matrix.
VIP <- function(object) {
  if (object$method != "oscorespls")
    stop("Only implemented for orthogonal scores algorithm.  Refit with 'method = \"oscorespls\"'")
  if (nrow(object$Yloadings) > 1)
    stop("Only implemented for single-response models")
  
  SS <- c(object$Yloadings)^2 * colSums(object$scores^2)
  Wnorm2 <- colSums(object$loading.weights^2)
  SSW <- sweep(object$loading.weights^2, 2, SS / Wnorm2, "*")
  sqrt(nrow(SSW) * apply(SSW, 1, cumsum) / cumsum(SS))
}


## VIPjh returns the VIP of variable j with h components
VIPjh <- function(object, j, h) {
  if (object$method != "oscorespls")
    stop("Only implemented for orthogonal scores algorithm.  Refit with 'method = \"oscorespls\"'")
  if (nrow(object$Yloadings) > 1)
    stop("Only implemented for single-response models")
  
  b <- c(object$Yloadings)[1:h]
  T <- object$scores[,1:h, drop = FALSE]
  SS <- b^2 * colSums(T^2)
  W <- object$loading.weights[,1:h, drop = FALSE]
  Wnorm2 <- colSums(W^2)
  sqrt(nrow(W) * sum(SS * W[j,]^2 / Wnorm2) / sum(SS))
}


#Definition de l'environnement de travail
setwd("C:/Users/veronique.cariou/Documents/Cours/ING3/FOODS/Sensometrie/TD/ProduitsMer")

##Lecture des donnees
channel1 <- odbcConnectExcel2007("ProduitsMer.xls") #nom de fichier
sqlTables(channel1)
Y<-sqlQuery(channel = channel1,  "select * from [senso$]") #dataSenso
X<-sqlQuery(channel = channel1,  "select * from [physico$]") #dataSpectro
odbcCloseAll() #fermer la connexion
rownames(X) <- X[,1]
X <- X[,-1]
rownames(Y) <- Y[,1]
Y <- Y[,-1]
#attention var tma présente dans ins et senso
colnames(Y)[2]<-"tmas"
XY <- cbind(X,Y)#concatenation des variables senso et inst

##################
#      PIQU      #
##################

#Construire la formule !
fmla <- paste(colnames(X),collapse = " + ")
fmla <- paste("piqu ~",fmla)
fmla <- as.formula(fmla)
res.lm=lm(fmla ,data=XY)
summary(res.lm)
vif(res.lm) 


###########################################
#      PLS1      sur piqu                 #
###########################################


res.PLS1 <- plsr(fmla,data=XY, ncomp = 7, method="oscorespls",validation = "LOO",jackknife=TRUE)
summary(res.PLS1) 
round(explvar(res.PLS1),2) # % d'inertie de X expliquée par les variables latentes (les composantes de la PLS1)

# Représentation graphique : ce graphique représente le RMSEP (root Mean Squared Errors of Prediction) en fonction du nombre de composantes introduites dans le modèle. 
validationplot(res.PLS1, val.type="RMSEP",estimate = c("train","CV"), legendpos = "topright",main="RMSEP en fonction du nombre de composantes")

##
#### Qualité du modèle
# choix du nb de composantes par l'erreur minimum en CV avec + 1 sigma vs en randomisation
ncomp.onesigma <- selectNcomp(res.PLS1, method = "onesigma", plot = TRUE) #3
ncomp.graph <- 2 ## pour les représentations graphiques


# Visualisation des R2 associés
validationplot(res.PLS1, val.type="R2",estimate = c("train","CV"))
abline(v=ncomp.onesigma,lty=2,col="blue")
R2(res.PLS1,estimate=c("train","CV"))
# Visualisation des Pourcentages d'inertie de X expliqués
plot(cumsum(explvar(res.PLS1)), type="l", main="% d'inertie de X restituée", xlab="composantes", ylab="% d'inertie")
abline(v=ncomp.onesigma,lty=2,col="blue")


# Représentation graphique : Représentation graphiques des composantes PLS
plot(res.PLS1, plottype = "scores", labels="names", type="p", pch=20,comps = 1:2,main="1er plan factoriel")
abline(h=0,lty=2)
abline(v=0,lty=2)


# cercle des corrélations associés 
X11()
corrplot(res.PLS1,labels=colnames(X),cex=1)
coord.y <- cor(scores(res.PLS1),Y$piqu)
text(coord.y[1],coord.y[2],"piqu",col="red")


## pour interpréter les variables latentes (ici, composantes principales)
barplot(t(res.PLS1$loadings[,1:2]),  beside=T,  names.arg=colnames(X),las=2,legend.text=c("Comp.1","Comp.2"))
title("Loadings")


## check vip
res.VIP <- VIP(res.PLS1)
plage.keep <- which(res.VIP[ncomp.onesigma,]>1)

par(mfrow=c(1,1))
vip <- res.VIP[ncomp.onesigma,]
barplot(vip,names.arg=colnames(X),
        legend=paste("Cp",ncomp.onesigma),las=1)
abline(h=1,col="red",lty=2)
abline(h=0.8,col="blue",lty=2)

res.jack <- jack.test(res.PLS1, ncomp = ncomp.onesigma)
res.jack.mat <- data.frame(name=colnames(X),value=res.jack$coefficients[,1,1],sd=res.jack$sd[,1,1],tvalue=res.jack$tvalues[,1,1])

# Most basic error bar
ggplot(res.jack.mat) +
  geom_bar( aes(x=name, y=value), stat="identity", fill="skyblue", alpha=0.7) + theme_bw() +
  geom_errorbar( aes(x=name, ymin=value-sd, ymax=value+sd), width=0.4, colour="orange", alpha=0.9, size=0.5)


################################
#    ANALYSE GLOBALE     #
################################

#PLS2 
#faire validation plot / R2

#Choix du nombre de composantes par variables sensorielles et détermination des variables chimiques contributives (VIP)
# ne fonctionne pas en PLS2 donc à reproduire en faisant des PLS1 partielles

## scoreplot et correlation plot


