model<-'
data{
int<lower=1> n;
int<lower=1> p;
vector[n] x;
matrix[n,p] w;
vector[n] y;
vector[n] m;
vector[p+2] betah;
real g;
vector[p+1] alphah;
}
transformed data{
matrix[n,p+1] w1;
matrix[n,p+2] w2;
matrix[p+1,p+2] v1;
matrix[p+2,p+2] v2;
for(i in 1:n){
w1[i,1]=x[i];
w2[i,1]=m[i];
w2[i,2]=x[i];
}
w1[,2:(p+1)]=w;
w2[,3:(p+2)]=w;
v1=inverse(transpose(w1)*w1);
v2=inverse(transpose(w2)*w2);
}
parameters{
real alpha0;
real beta0;
real <lower=0> sigma1;
real <lower=0> sigma2;
vector[p+2] beta;
vector[p+1] alpha;
}

transformed parameters{
real Indirect ;
Indirect=alpha[1]*beta[1];
}

model{
beta~multi_normal(betah,g*sigma2^2*v2);
alpha~multi_normal(alphah,g*sigma1^2*v1);
y~normal(beta0+w2*beta,sigma2);
m~normal(alpha0+w1*alpha,sigma1);
}
'
library(rstan)
modelOneSample<-stan_model(model_code=model)
set.seed(14)


y = df$Y
w <- as.matrix(df[, c("X1", "X2", "X3", "X4", "X5")])  
dim(w)
p <- ncol(w)

data_list <- list(
  n = nrow(df),
  p = p,  
  x = df$X,
  y = y,
  m = df$M,
  w = w,  
  bh = rep(0, p + 2),
  ah = rep(0, p + 1),
  g = length(y) 
)

fit<-sampling(modelOneSample,
              data=data_list,iter=5000)
BFLM <- function(y, X1, X2, g1 = length(y), g2 = length(y)) {
  n=length(y)
  # Estimation des coefficients pour chaque modèle
  beta1 <- solve(t(X1) %% X1) %% t(X1) %% y
  beta2 <- solve(t(X2) %% X2) %% t(X2) %% y
  
  Calcul des résidus pour chaque modèle
  S1 <- sum((y - mean(y) - X1 %% beta1)^2)
  S2 <- sum((y - mean(y) - X2 %% beta2)^2)
  
  Calcul du numérateur et du dénominateur
  num <- (g1 + 1)^(-p1 / 2) * (S1 + (t(beta1) %% t(X1) %% X1 %% beta1) / (g1 + 1))^(-(n - 1) / 2)
  den <- (g2 + 1)^(-p2 / 2) (S2 + (t(beta2) %% t(X2) %% X2 %*% beta2) / (g2 + 1))^(-(n - 1) / 2)
  
  return(as.numeric(num / den))
}

Calculer le facteur de Bayes entre les deux modèles
BFLM_result <- BFLM(y, X1=scale(as.matrix(X)), X2=scale(as.matrix(X2)), g1 = length(y), g2 = length(y))
print(BFLM_result)

