
#Exo8
library(glmnet)
library(readr)
omics <- read_csv("omics.csv")
X<-omics[,1:length(omics)-1]
Y<-omics[,length(omics)]
Y<-as.double(Y)
lasso = cv.glmnet(X, Y, alpha=1, nlambda=100, standardize=TRUE, nfolds=10)

str(Y)
#EXO9
library(gglasso)
library(glmnet)
load("Hopx_X.rda") 
load("Hopx_Y.rda")
ls()
data.X <- as.data.frame(data.X)  
data.Y.Hopx <- as.data.frame(data.Y.Hopx)
#2
group<-c(74, 67,63,60,39,45,52,43,31,51,21,26,33,22,15,27,18,30,34,19)
Grp<-rep(1:20, times=group)
#3
GLasso =cv.gglasso(as.matrix(data.X),data.Y.Hopx, group=Grp,loss="ls",pred.loss="L2",nfolds=20, intercept=TRUE)
plot(GLasso, lwd=2, group=TRUE)
grid()


#Exo10
library(fda)
data(CanadianWeather)

Temp <- CanadianWeather$dailyAv[, , 1]  
MaxPrecLog <- apply(CanadianWeather$dailyAv[, , 3], 2, max)  
X <- Temp  
y <- MaxPrecLog  
fit <- glmnet(t(X), y, alpha = 0) 
par(mar = c(4, 4, 2, 1))  
plot(fit, xvar = "lambda", label = TRUE)
plot(fit, xvar = "lambda", label = TRUE)


















#Exo5
lamda=seq(0,90,0.001)
fonc<-function(x){
  While(x>=sqrt(lamda)){
    H<-x
  }
  S<-if(x>0){max(c(abs(x)-lamda,0)) }
  else{S<-(-S)}
}





