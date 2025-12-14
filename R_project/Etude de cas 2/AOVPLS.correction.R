source("~/TIRAC/TIRAC 2023-2024/CIMMAP/R/AoVPLS/AOVPLS.R")
AOVPLS.correction<-function(formula,design,rem,data,alpha=0.05) {
   for (j in 1:ncol(design)) 
   design[,j] <- factor(design[,j])
  for (j in 1:length(rem))
    if (length(grep(rem[j],formula))==0)
      stop(paste("Erreur : le facteur",rem[j],"n est pas présent"))
  data.lim <- list(design=design,outcomes=as.matrix(data),formula=formula)
  var.sel=selvar(formula,data.frame(design,data),rem,alpha=alpha)
  res.lmpModelMatrix <- lmpModelMatrix(data.lim)
  res.lmpEffectMatrices <- lmpEffectMatrices(res.lmpModelMatrix, SS = TRUE, contrastList = NA)
  data.correction = data
  for (j in 1:length(rem)) {
    data.correction=data.correction-res.lmpEffectMatrices$effectMatrices[[rem[j]]]
  }
  res=list(var.sel=var.sel,data.correction=data.correction)
  return (res)
}

