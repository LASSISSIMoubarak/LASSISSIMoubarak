library(rstan)
library(bayesplot)
library(bridgesampling)
library(BayesFactor)
set.seed(3344)

load("C:/Users/lass/Downloads/data.rda")


mediation_reg <- '
data {
int<lower = 1> n;
int<lower = 1> p;
vector[n] y;
vector[n] X;
vector[n] M;
matrix[n,p] W;
vector[p+2] betah;
vector[p+1] alphah;
real <lower = 0> g;
}
transformed data{
matrix[n,p+1] W1;
matrix[n,p+2] W2;
matrix[p+1,p+1] V1;
matrix[p+2,p+2] V2;
for (i in 1:n){
W1[i,1] = X[i];
W2[i,1] = M[i];
W2[i,2] = X[i];
}
W1[,2:(p+1)] = W;
W2[,3:(p+2)] = W;
V1 = inverse(transpose(W1)*W1);
V2 = inverse(transpose(W2)*W2);
}
parameters {
real<lower=0> sigma1;
real<lower=0> sigma2;
vector[p+1] alpha;
vector[p+2] beta;
real beta0;
real alpha0;
}
transformed parameters{
real indirect;
indirect = alpha[1]*beta[1];
}

model {
y ~ normal(beta0 + W2*beta,sigma2);
M ~ normal(alpha0 + W1*alpha,sigma1);
beta ~ multi_normal(betah,g*(sigma2^2)*V2);
alpha ~ multi_normal(alphah,g*(sigma1^2)*V1);
}
'
# Compilation et exécution du modèle
stanmediation <- stan_model(model_code = mediation_reg,model_name = "stanmodel")
W <- as.matrix(df[,c("X1","X2","X3","X4","X5")])
fit <- sampling(stanmediation,data = list(n = length(df$Y), p = 5,X = df$X,M = df$M,y = df$Y,betah = rep(0,7),alphah = rep(0,6),g = length(df$Y),W = W),iter = 5000)
res <- rstan::extract(fit)

# Calcul du facteur de Bayes associé aux paramètres
BFLM <- function(y,X1,X2,g1 = length(y),g2 = length(y),n = length(y),betah1,betah2){
  p1 <- ncol(X1)
  p2 <- ncol(X2)
  X1 <- scale(as.matrix(X1),center = T,scale = T)
  X2 <- scale(as.matrix(X2),center = T,scale = T)
  beta_hat1 <- solve(t(X1)%*%X1)%*%t(X1)%*%y
  beta_hat2 <- solve(t(X2)%*%X2)%*%t(X2)%*%y
  s2_1 <- sum((y - mean(y) - X1%*%beta_hat1)**2)
  s2_2 <- sum((y - mean(y) - X2%*%beta_hat2)**2)
  m <- ((g1+1)**(-p1/2))/((g2+1)**(-p2/2))
  k <- (s2_1 + (t(betah1 - beta_hat1)%*%(t(X1)%*%X1)%*%(betah1 - beta_hat1))/(g1 + 1))/(s2_2 + (t(betah2 - beta_hat2)%*%(t(X2)%*%X2)%*%(betah2 - beta_hat2))/(g2 + 1))
  return(as.numeric(m*k**(-(n-1)/2)))
}
#log10(BFLM(df$Y,df[-1],df[-c(1,3)],betah1 = rep(0,7),betah2 = rep(0,6)))
BFalpha_1 <- BFLM(df$M,df[-c(1,2)],df[-c(1,2,3)],betah1 = rep(0,6),betah2 = rep(0,5))
BFbeta_1 <- BFLM(df$Y,df[-1],df[-c(1,2)],betah1 = rep(0,7),betah2 = rep(0,6))
BFindirect <- (BFalpha_1*BFbeta_1)/(1+BFbeta_1+BFalpha_1)
log10(BFindirect)
