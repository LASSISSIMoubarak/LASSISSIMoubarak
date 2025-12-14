## Analyse univariée et bivariée automatisée
## Dépendances utiles : tidyverse, GGally, corrplot, psych
## Installez si nécessaire (décommenter):
# install.packages(c('tidyverse','GGally','corrplot','psych'))

library(tidyverse)
library(GGally)
library(corrplot)
library(psych)

dir.create("plots", showWarnings = FALSE)

data <- read.csv("data_full.csv", stringsAsFactors = FALSE)

cat("Dimensions du jeu de données:", dim(data)[1], "lignes x", dim(data)[2], "colonnes\n")

# Détection automatique des variables numériques vs catégorielles
is_num <- sapply(data, is.numeric)
# Forcer conversion des colonnes qui sont numériques encodées en texte si possible
maybe_num <- function(x){ if(is.character(x) && all(grepl("^-?\\d+\\.?\\d*$", x[!is.na(x)]))) as.numeric(x) else x }
data <- data %>% mutate(across(where(is.character), maybe_num))
is_num <- sapply(data, is.numeric)

num_vars <- names(data)[is_num]
cat_vars <- names(data)[!is_num]

# Résumés globaux
write.csv(summary(data), file = "summary_overall.csv")
write.csv(describe(data), file = "describe_psych.csv")

## --- Univariée ---
plot_univariate <- function(df){
	for(v in names(df)){
		col <- df[[v]]
		safe_name <- gsub("[^A-Za-z0-9_-]", "_", v)
		if(is.numeric(col)){
			# calculer facteur d'échelle pour superposer densité sur counts
			vcol <- df[[v]]
			binwidth <- diff(range(vcol, na.rm = TRUE))/30
			nobs <- sum(!is.na(vcol))
			scale_factor <- nobs * binwidth

			p1 <- ggplot(df, aes(x = .data[[v]])) +
				geom_histogram(fill = '#2b8cbe', color='white', bins = 30) +
				geom_density(aes(x = .data[[v]], y = after_stat(density) * scale_factor), color='#f03b20', linewidth=0.8, alpha=0.3) +
				labs(title = paste('Histogramme + densité —', v), x = v)
			ggsave(filename = file.path('plots', paste0('univar_hist_', safe_name, '.png')), plot = p1)

			p2 <- ggplot(df, aes(y = .data[[v]])) +
				geom_boxplot(fill = '#74c476') +
				labs(title = paste('Boxplot —', v), y = v)
			ggsave(filename = file.path('plots', paste0('univar_box_', safe_name, '.png')), plot = p2)
		} else {
			# catégorielle
			colf <- as.factor(col)
			p <- ggplot(df, aes(x = colf)) +
				geom_bar(fill = '#6baed6') +
				labs(title = paste('Barplot —', v), x = v) +
				theme(axis.text.x = element_text(angle = 45, hjust = 1))
			ggsave(filename = file.path('plots', paste0('univar_bar_', safe_name, '.png')), plot = p)
			# table pour counts
			tab <- as.data.frame(table(colf, useNA = 'ifany'))
			write.csv(tab, file = file.path('plots', paste0('univar_counts_', safe_name, '.csv')),
								row.names = FALSE)
		}
	}
}

plot_univariate(data)

## --- Bivariée ---
plot_bivariate <- function(df){
	num_vars <- names(df)[sapply(df, is.numeric)]
	cat_vars <- names(df)[!sapply(df, is.numeric)]

	# Numeric vs Numeric: scatter + correlation
	if(length(num_vars) >= 2){
		cor_mat <- cor(df[num_vars], use = 'pairwise.complete.obs')
		write.csv(cor_mat, file = 'correlation_matrix.csv')
		png('plots/corrplot.png', width = 800, height = 800)
		corrplot(cor_mat, method = 'color', tl.cex = 0.8)
		dev.off()

		# ggpairs (peu de variables => faisable)
		nshow <- length(num_vars)
		if(nshow <= 8){
			gp <- ggpairs(df[num_vars])
			ggsave(filename = 'plots/ggpairs_numeric.png', plot = gp, width = 10, height = 10)
		}

		# Scatter plots pairwise (échantillonnage si grand)
		samp <- df %>% select(all_of(num_vars))
		if(nrow(samp) > 2000) samp <- samp %>% sample_n(2000)
		for(i in seq_len(length(num_vars)-1)){
			for(j in (i+1):length(num_vars)){
				x <- num_vars[i]; y <- num_vars[j]
				p <- ggplot(samp, aes(x = .data[[x]], y = .data[[y]])) +
					geom_point(alpha = 0.6) +
					geom_smooth(method = 'lm', se = FALSE, color = '#de2d26') +
					labs(title = paste('Scatter —', x, 'vs', y))
				safe_name <- paste0(gsub('[^A-Za-z0-9_-]', '_', x),'_vs_',gsub('[^A-Za-z0-9_-]', '_', y))
				ggsave(filename = file.path('plots', paste0('bivar_scatter_', safe_name, '.png')), plot = p)
			}
		}
	}

	# Numeric vs Categorical: boxplots
	if(length(num_vars) >= 1 & length(cat_vars) >= 1){
		for(nv in num_vars){
			for(cv in cat_vars){
				safe_name <- paste0(gsub('[^A-Za-z0-9_-]', '_', nv),'_by_',gsub('[^A-Za-z0-9_-]', '_', cv))
				df2 <- df %>% select(all_of(c(nv, cv))) %>% drop_na()
				if(nrow(df2) == 0) next
				# convertir catégorie en factor
				df2[[cv]] <- as.factor(df2[[cv]])
				p <- ggplot(df2, aes(x = .data[[cv]], y = .data[[nv]])) +
					geom_boxplot(fill = '#9ecae1') +
					geom_jitter(width = 0.2, alpha = 0.4) +
					labs(title = paste('Boxplot', nv, 'par', cv), x = cv, y = nv) +
					theme(axis.text.x = element_text(angle = 45, hjust = 1))
				ggsave(filename = file.path('plots', paste0('bivar_box_', safe_name, '.png')), plot = p)
			}
		}
	}

	# Categorical vs Categorical: proportion plot
	if(length(cat_vars) >= 2){
		for(i in seq_len(length(cat_vars)-1)){
			for(j in (i+1):length(cat_vars)){
				a <- cat_vars[i]; b <- cat_vars[j]
				df2 <- df %>% select(all_of(c(a,b))) %>% drop_na()
				if(nrow(df2) == 0) next
				df2[[a]] <- as.factor(df2[[a]]); df2[[b]] <- as.factor(df2[[b]])
				p <- ggplot(df2, aes(x = .data[[a]], fill = .data[[b]])) +
					geom_bar(position = 'fill') +
					labs(y = 'Proportion', title = paste('Proportion de', b, 'par', a)) +
					theme(axis.text.x = element_text(angle = 45, hjust = 1))
				safe_name <- paste0(gsub('[^A-Za-z0-9_-]', '_', a),'_vs_',gsub('[^A-Za-z0-9_-]', '_', b))
				ggsave(filename = file.path('plots', paste0('bivar_cat_', safe_name, '.png')), plot = p)
			}
		}
	}
}

plot_bivariate(data)

cat('Analyses créées dans le dossier `plots/`. Résumés: `summary_overall.csv`, `describe_psych.csv`, `correlation_matrix.csv`\n')

