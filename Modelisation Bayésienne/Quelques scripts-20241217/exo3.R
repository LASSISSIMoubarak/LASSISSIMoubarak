#Exo3
l<-rgamma(1000,shape=1/2,rate=1/2)
moy=0
var=1
 mu=1
for(i in seq_along(l)){
  y[i]<-rnorm(1,mean=0,sd=sqrt(1/l[i]))
}
#simulation nu
gibbs<-function(y,N){
  y<-numeric(1000)
  lamda<-numeric(1000)
  sigma2<-numeric(1000)
  nu<-numeric(1000)
  nu[1]<-moy
  sigma2[1]<-var
for(i in seq_along(y)){
  lamda[i]<-rgamma(1,shape=mu+1/2,rate=mu/2+(y[i]-moy)^2/2*var)
  sigma2[i]<-rinvgamma(1,shape=N/2,scale=sum(lamda*(y-nu)))
  nu[i]<-rnorm(1,mean=sum(lamda*y)/sum(lamda),sd=sqrt(sigma2[i]^2/sum(lamda)))
}
  result <- list(lamda = lamda, sigma2 = sigma2, nu = nu)
  return(result)
}
A<-gibbs(y,1000)

