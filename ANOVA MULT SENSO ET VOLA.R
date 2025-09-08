library(tidyverse)
library(FactoMineR)
library(factoextra)
library(pls)
library(limpca)
library(MBAnalysis)

#Pretraitement des données 

only <- function(col) {
  all(col == 0)
}
more <- function(col) {
  sum(col == 0) / length(col) > 0.5
}
dV1 <- DV %>%
  select(-which(sapply(., only))) %>%
  select(-which(sapply(., more)))
dm1 <- DM_CLR %>%
  select(-which(sapply(., only))) %>%
  select(-which(sapply(., more)))
print(dV1)
dv2<-dV1[,-c(1,2,3,4)]
ACP<-PCA(dv2, scale.unit = TRUE, ncp = 5)
summary(ACP)
fviz_pca_var(ACP, col.var = "cos2", gradient.cols = c("blue", "yellow", "red"), repel = TRUE)
cos2 <- ACP$var$cos2
print(cos2)
ds1<-DS[,-c(1,2,4,5)]
ACP2<-PCA(ds1, scale.unit = TRUE, ncp = 5)


###Anova multivariée

# Volatilome

outcomes =as.matrix(scale(dV1[,-c(1,2,3,4,5)]))
formula = "outcomes ~ Time + Lactate + Atm + Lactate:Atm + Time:Lactate "


################################################################"

#Pour les sensoriels il suffit de remplacer formula par formula 2
# **
outcomes2 =as.matrix(scale(ds1[,-c(1)]))
formula2 = "outcomes2 ~ Time + Lactate + Atm  + Lot + Atm:Lactate + Time:Lactate"


design2 = DS[,c(2,3,4,5)]
design2$Time<-as.factor(design2$Time)
rownames(outcomes2) <- paste0("", seq_len(nrow(outcomes2)))

##***

##################################################################

design = dV1[,c(2,3,4,5)]
design$Time<-as.factor(design$Time)

UCH <- data2LmpDataList(
  se=NULL,outcomes=outcomes2 ,
  design=design2, 
  formula=formula2
)




# design
plotDesign(
  design = UCH$design, x = "Atm",
  y = "Lactate", rows = "Time",
  title = "Design of the UCH dataset"
)
UCH$design
UCH$formula
UCH$outcomes

# Visualisation sur une variable (la variable de 2.6092056 ppm)
plotMeans(Y = UCH$outcomes, design = UCH$design, cols = c(15),
          x = c("Lactate"), w = c("Atm"), z = c("Time"), ylab = "Intensity",
          title = c("Mean reponse for main Citrate peak"))

#ACP simple sur tout le jeu de données
res.lim = pcaBySvd(UCH$outcomes, nPC = min(dim(UCH$outcomes)))
pcaScreePlot(res.lim)

#plan factoriel en colorant selon certaines variables
pcaScorePlot(res.lim, design=UCH$design, color="Lactate", shape="Atm")
pcaScorePlot(res.lim, design=UCH$design, color="Time", shape="Lactate")
pcaScorePlot(res.lim, design=UCH$design, color="Time", shape="Atm")

pcaLoading2dPlot(res.lim,axes=c(1,2), title="PCA loadings", addRownames = TRUE)


# Génération du modèle
resMM <- lmpModelMatrix(UCH)

# Estimation des effets et décomposition des matrices
resEM <- lmpEffectMatrices(resMM, SS = TRUE, contrastList = NA)

# Importance des effets
resEM$varPercentagesPlot
resEM$variationPercentages

#Significativité : test de bootstrap
res.lmpBootstrapTests = lmpBootstrapTests(resEM)
res.lmpBootstrapTests

pander::pander(t(res.lmpBootstrapTests$resultsTable))

#Réaliser l'ASCA pour visualiser les effets
resASCAE <- lmpPcaEffects(resLmpEffectMatrices = resEM, method = "ASCA-E")                                                                                            

# Contributions des composantes
resLmpContributions <- lmpContributions(resASCAE)
pander::pander(resLmpContributions$totalContribTable)
pander::pander(resLmpContributions$effectTable)
pander::pander(resLmpContributions$combinedEffectTable)
pander::pander("Ordered contributions per effect:")
resLmpContributions$plotTotal

pander::pander("For each PC of the different effects:")
resLmpContributions$plotContrib


# Scores plot des facteurs significatifs 
# Time , Atm ou Lot
lmpScorePlot(resASCAE, effectNames = "Time",
             color = "Time", shape = "Time", drawShapes = "ellipse")

lmpLoading2dPlot(resLmpPcaEffects = resASCAE, effectNames = c("Atm"),
                 axes = c(1, 2), addRownames = TRUE, pl_n = 10)






