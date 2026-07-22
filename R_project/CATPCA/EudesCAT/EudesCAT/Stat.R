#load essential packages
library(mc2d)
library(stats)
lambda<-1 #intensity of poisson processus
#TO DO: comments in english please(Already done)!

T=10 # chromosome length

dmark<-0.1
#distance between markers

posMarker<-seq(0,T,dmark)
#Location of markers 


m<-5
#m number of QTLs


posQTL<-c((2.91),(4.61),(5.31),(6.02),(9.03))
# Warning: the QTL location must not match a marker location !
 
allLocations<-sort(c(posMarker,posQTL))
#combining location of markers and QTLs, and we sort them

n<-1000
# n Individuals

K<-length(allLocations)

#simulate genome
myGenome<-matrix(data=0,nrow=n,ncol=K)#Initialize genome with zero dim=n*k


numberOfRecombinations<-numeric(n)
#numberOfRecombinations[i] will refer to the number of recombinations that happened for ind i


for(i in 1:n){
  # we start with first marker for individual i
  alleleFirstMarker<-ifelse(rbern(1, 0.5) == 1, 1, -1)#Ifelse respect condition and update others to -1
  myGenome[i, 1:K] <- alleleFirstMarker
  
  numberOfRecombinations[i] <-0#Initialize step to zero (Just look in A)
  tRecomb<-rexp(1,lambda)#parameters
  # the intensity of the Poisson process is 1 according to Haldane ...
  # tRecomb is the location of the first recombination event
  
  currentAllele<-alleleFirstMarker
  lowerBound<-0
  UpperBound<-tRecomb
  
   while (tRecomb < T) {   
     #One recombination happened !
     #so alleles at markers located between lowerBound and UpperBound receive current Allele
     
     numberOfRecombinations[i] <- numberOfRecombinations[i] + 1
     
     IndicesOfInterest<-which(allLocations < UpperBound & allLocations>lowerBound )
     
     myGenome[i, IndicesOfInterest]<-currentAllele
     
     lowerBound<-tRecomb
     tRecomb <-tRecomb+ rexp(1,lambda) #Actualise tRecomb
     UpperBound<-tRecomb
     
     currentAllele<-ifelse(currentAllele== 1, -1, 1)
     
   }
}

#phenotype
myPhenotype<-function(nu,q,sigma,X,nobs){
  Y<-numeric(nobs)
  for(i in 1:nobs){
    Y[i]<-mu + sum(X[i,which(allLocations %in% posQTL)]*q) + sigma*rt(1,df=5)} 
return(Y)}


#### Generating phenotypes under the alternative
mu<-1
sigma=3
#sigma standard deviation for the noise
q<-c(2,4,-3,6,8)
#q is a vector of QTL effects
myPhenotype(mu,q,sigma,myGenome,n)


#### Now under H0, ie no QTL
q<-c(0,0,0,0,0)
#q is a vector of QTL effects
myPhenotype(mu,q,sigma,myGenome,n)
#Generate test statistic under H0 and H1 and compare them to get power and type I error








haldane_dist <- function(t_a, t_b) {
  d <- abs(t_a - t_b)
  0.5 * (1 - exp(-2 * d))
}


compute_Qs <- function(t1, t, t2, r_fn = haldane_dist) {
  r_t1_t2 <- r_fn(t1, t2) #between QTLs
  r_t_t1  <- r_fn(t1, t) #between QTL and left marker
  r_t_t2  <- r_fn(t, t2)#between QTL and right marker
  br_t1_t2 <- 1 - r_t1_t2#without recombination between QTLs
  br_t_t1  <- 1 - r_t_t1#without recombination between QTL and left marker
  br_t_t2  <- 1 - r_t_t2#without recombination between QTL and right marker

  # Following the textual formulas provided:
  Q11<- br_t_t1 * br_t_t2 / max(br_t1_t2)
  Q01 <- r_t_t1 * br_t_t2 / max(r_t1_t2)
  Q10 <- 1 - Q01
  Q00<- 1- Q11 

  raw <- c(Q11, Q01, Q10, Q00)
  return(raw)
}



compute_alpha_beta_from_Qs <- function(t1, t, t2, r_fn = haldane_dist) {
  qs <- compute_Qs(t1, t, t2, r_fn)
  alpha <- qs[1] - qs[2]  # Q11 corresponds to the first element
  beta  <- qs[1] - qs[3]  # Q10 corresponds to the third element
  return(list(alpha = alpha, beta = beta))
}

SnSta<-function(myPhenotype){
  if (!exists("Y") || length(Y) != n) {
    Y <- myPhenotype(mu, q, sigma, myGenome, n)
  }
  sn <- numeric(length(allLocations))
  Ycenter <- Y - mean(Y)
  denomY <- sum(Ycenter^2)
  for (j in seq_along(allLocations)) {
    gcol <- myGenome[, j]
    num <- sum(Ycenter * gcol)
    denom <- sqrt(denomY * sum(gcol^2))
    sn[j] <- num / denom
  }
  return(sn)
}
#Update SnSta 
updating_SnSta<-function(SnStat,allLocations,haldane_dist){
  for (j in length(allLocations)) {
    left<-which(allLocations[j+1])
    right<-which(allLocations[j-1])
    alpha<- compute_alpha_beta_from_Qs(left,right,haldane_dist)$alpha
    beta<- compute_alpha_beta_from_Qs(left,right,haldane_dist)$beta
    num<-SnStat[j-1]*alpha  + SnStat[j+1]* beta + SnStat[j+1]
    denom<-sqrt(alpha^2 + beta^2 +4*alpha*beta*haldane_dist(allLocations[j-1],allLocations[j+1]))
    sn[j]<- num/denom
  return(sn)
}

#Decision rule
decision_rule<-function(SnStat,threshold,experiences_num){
  for (i in 1:experiences_num){
    qtl_position<-which(allLocations %in% posQTL)
    for (pos in qtl_position){
      sta<-Updating_SnSta[pos]^2
    }if((sta)>threshold){
      decisions[i]+<-1 }
  return(decisions)

} 
