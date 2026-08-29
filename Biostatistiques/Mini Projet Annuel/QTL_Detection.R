library(mc2d)
library(stats)
library(knitr)
library(kableExtra)

#TO DO: comments in english please(Already done)!
##----------------------Begin general parameters----------------------##

GetDmark <- function(T, nbmarkers) {
  T / (nbmarkers - 1)
}

lambda <- 1      # intensity of Poisson process (Haldane)
mu     <- 0
sigma  <- 1
T      <- 1      # chromosome length in Morgan

# QTL position (must not coincide with a marker)
posQTL <- 0.6123

# Haldane recombination function
Recombfunction <- function(t1, t2) {
  d <- abs(t1 - t2)
  0.5 * (1 - exp(-2 * d))
}

# Correlation p(t1,t2) = exp(-2|t1 - t2|)
rho <- function(t1, t2) {
  exp(-2 * abs(t1 - t2))
}




##---------------------- Simulation du génome ----------------------##

myGenomeSimul <- function(n, allLocations, lambda = 1, T = 1) {
  K <- length(allLocations)
  myGenome <- matrix(0, nrow = n, ncol = K)
  numberOfRecombinations <- numeric(n)
  
  for (i in 1:n) {
    alleleFirstMarker <- ifelse(rbern(1, 0.5) == 1, 1, -1)
    myGenome[i, ] <- alleleFirstMarker
    
    numberOfRecombinations[i] <- 0
    tRecomb <- rexp(1, lambda)
    
    currentAllele <- alleleFirstMarker
    lowerBound <- 0
    upperBound <- tRecomb
    
    while (tRecomb < T) {
      numberOfRecombinations[i] <- numberOfRecombinations[i] + 1
      
      IndicesOfInterest <- which(allLocations > lowerBound & allLocations <= upperBound)
      if (length(IndicesOfInterest) > 0) {
        myGenome[i, IndicesOfInterest] <- currentAllele
      }
      
      lowerBound <- tRecomb
      tRecomb <- tRecomb + rexp(1, lambda)
      upperBound <- tRecomb
      currentAllele <- ifelse(currentAllele == 1, -1, 1)
    }
    
    # Bottom interest of recombination
    IndicesOfInterest <- which(allLocations > lowerBound & allLocations <= T)
    if (length(IndicesOfInterest) > 0) {
      myGenome[i, IndicesOfInterest] <- currentAllele
    }
  }
  myGenome
}





##----------------------Phénotypes ----------------------##

myPhenotypeLaw <- function(mu, q, sigma, X, nobs, allLocations, posQTL, law = "gauss") {
  Y <- numeric(nobs)
  qtlIdx <- which(allLocations %in% posQTL)
  for (i in seq_len(nobs)) {
    bruit <- switch(law,
                    gauss   = sigma * rnorm(1),
                    khi2    = sigma * (rchisq(1, df = 3) - 3) / sqrt(6),
                    student = sigma * rt(1, df = 5) ,
                    beta    = sigma * (rbeta(1, 2, 5) - 2 / 7) / sqrt(10 / 392)
                    # sigma * rnorm(1)
    )
    Y[i] <- mu + sum(X[i, qtlIdx] * q) + bruit
  }
  Y
}



##---------------------- Find : Q, alpha, beta ----------------------##

computeQs <- function(t1, t, t2, Haldane = Recombfunction) {
  rt1t2 <- Haldane(t1, t2)
  rtt1  <- Haldane(t1, t)
  rtt2  <- Haldane(t, t2)
  
  Qp1p1 <- (1 - rtt1) * (1 - rtt2) / (1 - rt1t2)
  Qp1m1 <- (1 - rtt1) * rtt2 / rt1t2
  Qm1p1 <- rtt1 * (1 - rtt2) / rt1t2
  Qm1m1 <- 1 - Qp1p1
  
  list(Qp1p1 = Qp1p1, Qm1p1 = Qm1p1, Qp1m1 = Qp1m1, Qm1m1 = Qm1m1)
}

computeAlphaBeta <- function(t1, t, t2, dist = Recombfunction) {
  qs <- computeQs(t1, t, t2, Haldane = dist)
  alpha <- qs$Qp1p1 - qs$Qm1p1
  beta  <- qs$Qp1p1 - qs$Qp1m1
  list(alpha = alpha, beta = beta)
}






##---------------------- Azais interpolate statistic function ----------------------##

SnMarkers <- function(Y, myGenome, markerLocations, allLocations) {
  markerIdx <- which(allLocations %in% markerLocations)
  sn <- numeric(length(markerIdx))
  Ycenter <- Y - mean(Y)
  denomY <- sum(Ycenter^2)
  denom <- sqrt(denomY)
  
  for (j in seq_along(markerIdx)) {
    gcol <- myGenome[, markerIdx[j]]
    num <- as.numeric(t(Ycenter) %*% gcol)
    sn[j] <- num / denom
  }
  sn
}

SnInterpolated <- function(SnMarker, markerLocations, myGenome, haldane = Recombfunction,
                            rho = rho, by = 0.001) {
  nloc <- markerLocations
  Sta <- list()
  midPosall <- list()
  
  for (j in seq_along(nloc)[-length(nloc)]) {
    leftPos  <- nloc[j]
    rightPos <- nloc[j + 1]
    midPosseq <- seq(leftPos, rightPos, by = by)
    statsj <- numeric(length(midPosseq))
    
    for (i in seq_along(midPosseq)) {
      midPos <- midPosseq[i]
      qs <- computeAlphaBeta(leftPos, midPos, rightPos, dist = haldane)
      num <- SnMarker[j] * qs$alpha + SnMarker[j + 1] * qs$beta
      denom <- sqrt(qs$alpha^2 + qs$beta^2 + 2 * qs$alpha * qs$beta * rho(leftPos, rightPos))
      if (!is.finite(denom) || denom == 0) {
        statsj[i] <- NA
      } else {
        statsj[i] <- num / denom
      }
    }
    Sta[[j]] <- statsj
    midPosall[[j]] <- midPosseq
  }
  list(stats = Sta, midPos = midPosall)
}





##---------------------- calculate Decision under H0 / H1(Test decision) ----------------------##

decisionRuleLaw <- function(threshold, n, sampleSize, law,
                            T, nbmarkers, posQTL) {
  # select adequate qtl position
  dmark <- GetDmark(T, nbmarkers)
  posMarker <- seq(0, T, dmark)
  allLocations <- sort(c(posMarker, posQTL))
  
  decisionUnderH0 <- 0
  decisionUnderH1 <- 0
  staVecH0 <- numeric(sampleSize)
  staVecH1 <- numeric(sampleSize)
  argmaxH1 <- numeric(sampleSize)
  qUnderH0 <- 0
  qUnderH1 <- 4 / sqrt(n)
  
  firstStats <- NULL
  firstPositions <- NULL
  
  for (i in 1:sampleSize) {
    myGenome <- myGenomeSimul(n, allLocations, lambda = lambda, T = T)
    
    ## Under H0
    YH0 <- myPhenotypeLaw(mu, qUnderH0, sigma, myGenome, n, allLocations, posQTL, law)
    SnH0Markers <- SnMarkers(YH0, myGenome, posMarker, allLocations)
    SnH0Interp  <- SnInterpolated(SnH0Markers, posMarker, myGenome,
                                    haldane = Recombfunction, rho = rho, by = 0.001)
    staVecH0[i] <- max(unlist(SnH0Interp$stats)^2, na.rm = TRUE)
    if (staVecH0[i] > threshold) {
      decisionUnderH0 <- decisionUnderH0 + 1
    }
    
    ## Under H1
    YH1 <- myPhenotypeLaw(mu, qUnderH1, sigma, myGenome, n, allLocations, posQTL, law)
    SnH1Markers <- SnMarkers(YH1, myGenome, posMarker, allLocations)
    SnH1Interp  <- SnInterpolated(SnH1Markers, posMarker, myGenome,
                                    haldane = Recombfunction, rho = rho, by = 0.001)
    staVecH1[i] <- max(unlist(SnH1Interp$stats)^2, na.rm = TRUE)
    if (staVecH1[i] > threshold) {
      decisionUnderH1 <- decisionUnderH1 + 1
    }
    
    if (i == 1) {
      firstStats     <- unlist(SnH1Interp$stats)
      firstPositions <- unlist(SnH1Interp$midPos)
    }
    posH1 <- unlist(SnH1Interp$midPos)
    maxIdx <- which.max(staVecH1[i])
    argmaxH1[i] <- posH1[maxIdx]
  }
  
  list(
    decisionUnderH0 = decisionUnderH0 * 100 / sampleSize,
    decisionUnderH1 = decisionUnderH1 * 100 / sampleSize,
    firstStats     = firstStats,
    firstPositions = firstPositions,
    argmaxH1 = argmaxH1,
    meanArgmax= mean(argmaxH1)
  )
}






##---------------------- main----------------------##

# nValues <- c(50, 100, 200)
nValues<-c(50)
markersList <- list(
  "6"   = 6.76,
  "41"  = 8.16,
  "51"  = 8.27,
  "101" = 8.41
)
sampleSize <- 10000
# lois <- c("gauss", "khi2", "student", "beta")
lois<-c("student")
resultsList <- list()

for (law in lois) {
  results <- data.frame(
    n          = character(),
    nbmarkers = integer(),
    threshold  = numeric(),
    decisionH0 = numeric(),
    decisionH1 = numeric()
  )
  
  for (n in nValues) {
    for (nbMarkersName in names(markersList)) {
      nbmarkers <- as.numeric(nbMarkersName)
      threshold  <- markersList[[nbMarkersName]]
      
      cat(sprintf("Loi: %s, n: %d, nbmarkers: %d\n", law, n, nbmarkers))
      
      testLevel <- decisionRuleLaw(
        threshold = threshold,
        n         = n,
        sampleSize = sampleSize,
        law       = law,
        T         = T,
        nbmarkers = nbmarkers,
        posQTL    = posQTL
      )
      cat(sprintf("RateOfReject (H0): %.4f\n", testLevel$decisionUnderH0))
      cat(sprintf("RateOfReject (H1): %.4f\n", testLevel$decisionUnderH1))
      cat(sprintf("Position réelle QTL: %.4f\n", posQTL))
      cat(sprintf("Moyenne des argmax: %.4f\n", testLevel$meanArgmax))
      cat(sprintf("Écart-type des argmax: %.4f\n", testLevel$sdArgmax))
      cat(sprintf("Différence avec QTL: %.4f\n", abs(testLevel$meanArgmax - posQTL)))
      cat("\n")
      
      # Ajouter une ligne verticale pour la moyenne des argmax
      plot(testLevel$firstPositions, testLevel$firstStats, type = "l",
           main = sprintf("Statistique by position - Law %s, n=%d, markers=%d", law, n, nbmarkers),
           xlab = "Position", ylab = "Statistique")
      abline(v = posQTL, col = "red", lty = 2, lwd = 2, label = "QTL réel")
      abline(v = testLevel$meanArgmax, col = "blue", lty = 3, lwd = 2, label = "Moyenne argmax")
      legend("topright", legend = c("QTL réel", "Moyenne argmax"), 
             col = c("red", "blue"), lty = c(2, 3), lwd = 2)
      results <- rbind(results, data.frame(
        n           = paste0("n_", n),
        nbmarkers  = nbmarkers,
        threshold   = threshold,
        decisionH0 = testLevel$decisionUnderH0,
        decisionH1 = testLevel$decisionUnderH1
      ))
    }
  }
  resultsList[[law]] <- results
}









