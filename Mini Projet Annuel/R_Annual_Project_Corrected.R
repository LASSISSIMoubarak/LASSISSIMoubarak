#load essential packages
library(mc2d)
library(stats)
lambda<-1 #intensity of poisson processus
#TO DO: comments in english please(Already done)!

T=10 # chromosome length in Morgan

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
  Y <- numeric(nobs)
  qtl_idx <- which(allLocations %in% posQTL)
  for (i in seq_len(nobs)){
    Y[i] <- nu + sum(X[i, qtl_idx] * q) + sigma * rt(1, df = 5)
  }
  Y
}


#### Generating phenotypes under the alternative
mu<-1
sigma=3
#sigma standard deviation for the noise
# q<-c(2,4,-3,6,8)
# #q is a vector of QTL effects
# myPhenotypeUnderH1<-myPhenotype(mu,q,sigma,myGenome,n)


#### Now under H0, ie no QTL
q<-c(0,0,0,0,0)
#q is a vector of QTL effects
myPhenotypeUnderH0<-myPhenotype(mu,q,sigma,myGenome,n)




# Functions for recombination calculations
Recombfunction <- function(t1, t2) {
  d <- abs(t1 - t2)
  0.5 * (1 - exp(-2 * d))
}





#------------------------------------------------------------------
compute_Qs <- function(t1, t, t2, Haldane = Recombfunction) {
  rt1t2 <- Haldane(t1, t2) #between QTLs
  rtt1  <- Haldane(t1, t) #between QTL and left marker
  rtt2  <- Haldane(t, t2)#between QTL and right marker
  Q11<- (1- rtt1) * (1- rtt2) / (1- rt1t2)
  Q01 <- rtt1 * (1-rtt2) / (rt1t2)
  Q10 <- 1 - Q01
  Q00<- 1- Q11 
  Prob<- c(Q11, Q01, Q10, Q00)
  return(Prob)
}


#------------------------------------------------------------------ 

compute_alpha_beta <- function(t1, t, t2, dist = Recombfunction) {
  qs <- compute_Qs(t1, t, t2, Haldane = Recombfunction)
  alpha <- qs[1] - qs[2]
  beta  <- qs[1] - qs[3]
  list(alpha = alpha, beta = beta)
}

#------------------------------------------------------------------
#Compute Sn statistic

SnSta<-function(myPhenotype){
  Y <- myPhenotype(mu, q, sigma, myGenome, n)
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
# Update SnSta: smooth/update the statistic using neighbors (avoid boundaries)
updating_SnSta <- function(SnStat, allLocations, haldane = Recombfunction) {
  nloc <- length(allLocations)
  sn <- SnStat
  if (nloc < 3) return(sn)
  for (j in seq(2, nloc - 1)) {
    left_pos  <- allLocations[j - 1]
    mid_pos   <- allLocations[j]
    right_pos <- allLocations[j + 1]

    ab <- compute_alpha_beta(left_pos, mid_pos, right_pos, haldane)
    alpha <- ab$alpha
    beta  <- ab$beta

    num <- SnStat[j - 1] * alpha + SnStat[j + 1] * beta + SnStat[j]
    denom <- sqrt(alpha^2 + beta^2 + 4 * alpha * beta * haldane(left_pos, right_pos))
    if (!is.finite(denom) || denom == 0) denom <- .Machine$double.eps
    sn[j] <- num / denom
  }
  sn
}

#------------------------------------------------------------------
#Decision rule
decision<-0
decisionRule <- function(SnStat, threshold,numexperience) {
  for (i in 1:numexperience){
    SnStat <- SnSta(myPhenotype)
    SnStat <- updating_SnSta(SnStat, allLocations, haldane = Recombfunction)
    print(max(SnStat^2))
    exit()
    
  if (max(SnSta^2) > threshold){
    decision<-decision +1
  }
  }
  return(decision/numeperience)
}

##Application
decision_rule <- decisionRule(SnStat, threshold = 8.4,100)
print(decision_rule)

