library(readr)
Rats <- read_delim("ratSurvival.csv", 
                          delim = ";", escape_double = FALSE, trim_ws = TRUE)
ngrp = 10
m = (ngrp*(ngrp-1)/2)
Ctrl = Rats[ Rats[, 2] == "control", 1 ]
NK1 = Rats[ Rats[, 2] == "NK603-11%", 1 ]
NK2 = Rats[ Rats[, 2] == "NK603-22%", 1 ]
NK3 = Rats[ Rats[, 2] == "NK603-33%", 1 ]
NK1R = Rats[ Rats[, 2] == "NK603-11%+R", 1 ]
NK2R = Rats[ Rats[, 2] == "NK603-22%+R", 1 ]
NK3R = Rats[ Rats[, 2] == "NK603-33%+R", 1 ]
RA = Rats[ Rats[, 2] == "RoundUp A", 1 ]
RB = Rats[ Rats[, 2] == "RoundUp B", 1 ]
RC = Rats[ Rats[, 2] == "RoundUp C", 1 ]
Data = cbind(Ctrl, NK1, NK2, NK3, NK1R, NK2R, NK3R, RA, RB, RC)
layout(matrix(1:2,1,2))

par(mar = rep(2, 4))
# Boxplot groupe par groupe
boxplot(Data, col="forestgreen")
grid()
# Des groupes se démarquent immédiatement

MatPVal<-matrix(0,nrow=10,ncol=10)
VecPVal=c()
a=0.05
for(i in 1:(ngrp-1)){
  for(j in (i+1):ngrp){
   p=wilcox.test(Data[,i],Data[,j])$p.value
   MatPVal[i,j]=p
   MatPVal[i,j]= MatPVal[i,j]
   VecPVal=c(VecPVal,p)
  }
}


VecPVal=sort(VecPVal)
Col=c("forestgreen","red")
RejAlpha=(VecPVal<a)
plot(VecPVal,type="p",pch=24,col=Col[RejAlpha+1])
grid()
#
Col=c("forestgreen","red")
RejBonf=(VecPVal<a/m)
plot(VecPVal,type="p",pch=24,col=Col[RejAlpha+1])
grid()

RejBH = (VecPVal<a*(1:m)/m)
plot(VecPVal,type ="p",pch=24),Col[RejBH+1])
lines(1:m,a*(1:m)/m,lty=2)

RejBY = (VecPVal<a*(1:m)/m)
plot(VecPVal,type ="p",pch=24)?COL+COL[RejBH+1])
lines(1:m,a*(1:m)/(m*sum(1/(1:m)),lty=2)







