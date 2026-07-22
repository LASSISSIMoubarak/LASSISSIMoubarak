#TP 11
proteins<-scale(proteins,center = TRUE,scale = TRUE)
p<-ncol(proteins)
cor_matrix <- cor(proteins,method="pearson")
AL <- matrix(0, p, p)
for (i in 1:(p-1)) {
  for (j in (i+1):p) {
    test_result <- cor.test(proteins[, i], proteins[, j],method="pearson")
    if (test_result$p.value < 0.05) { 
      AL[i, j] <- 1
      AL[j, i] <- 1
    }
  }
}
layout(matrix(1:2,1,2))
par(mar = c(1, 1, 1, 1))  

plot(G)
library(igraph)
library(glasso)
colnames(AL) <- colnames(proteins)
rownames(AL) <- colnames(proteins)
G <- graph_from_adjacency_matrix(AL, mode="undirected", diag=FALSE)
V(G)$name <- colnames(proteins)
plot(G)

find <- function(Cov,lam) {
  lambda <- seq(0.01, 1, by = 0.01)  
  for (lambda in lambda) {
    GraphLasso <- glasso(Cov, rho = lambda, penalize.diagonal = FALSE)

#EXO9
