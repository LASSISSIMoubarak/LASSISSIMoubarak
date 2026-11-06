from __future__ import annotations

import re
import unicodedata


PROJECT_SEEDS = (
    {
        "slug": "solarwatch",
        "title": "SolarWatch - surveillance de performance photovoltaïque",
        "summary": (
            "Mini-pipeline de surveillance de deux centrales photovoltaïques : "
            "sous-performance, alertes candidates et prévision de production."
        ),
        "description": (
            "Projet personnel réalisé sur le jeu public Solar Power Generation Data "
            "(Kaggle, deux centrales en Inde, 34 jours). Le pipeline joint les mesures "
            "météo et la production de 44 onduleurs, compare leur puissance à la médiane "
            "de leurs pairs, puis évalue Isolation Forest et un LSTM sur des périodes "
            "chronologiques distinctes. Les incidents injectés dans des scénarios de "
            "test sont synthétiques. Le jeu ne contient pas de pannes labellisées et "
            "ne permet pas d'identifier les causes terrain."
        ),
        "skills": "Python, pandas, scikit-learn, PyTorch, LSTM, Isolation Forest, séries temporelles, énergie solaire, détection d'anomalies, Git",
        "keywords": (
            "solaire, photovoltaïque, photovoltaic, solar, renewable, énergie, energy, "
            "centrale, production, onduleur, inverter, maintenance, fiabilité, "
            "anomalie, anomaly, détection, prédiction, forecast, prévision, LSTM, "
            "séries temporelles, time series, météo, irradiation, performance, "
            "machine learning, machine learning, IA, AI"
        ),
        "highlights": (
            "136 476 mesures de production analysées sur 34 jours",
            "Comparaison d'un LSTM de prévision à une référence de persistance sur test chronologique",
            "Alertes candidates hiérarchisées et scénarios synthétiques documentés",
        ),
        "public_url": "",
    },
    {
        "slug": "power-bi-transactions-india",
        "title": "Tableau de bord Power BI - transactions en Inde",
        "summary": (
            "Rapport interactif orienté métier pour explorer les montants de "
            "transactions par secteur, genre, État, année et âge."
        ),
        "description": (
            "Projet BI réalisé avec Power BI à partir d'un rapport d'analyse "
            "de transactions en Inde. Le tableau de bord présente le montant "
            "agrégé, une répartition par secteur d'activité et par genre, une "
            "visualisation géographique par État ainsi qu'une analyse par année "
            "et par âge. Le projet inclut également l'automatisation de "
            "l'actualisation du rapport avec Power Automate."
        ),
        "skills": (
            "Power BI, conception de tableaux de bord, visualisation de données, "
            "analyse métier, Power Automate, automatisation de l'actualisation"
        ),
        "keywords": (
            "BI, business intelligence, Power BI, Power Automate, tableau de bord, "
            "dashboard, visualisation, visualisation de données, data visualization, "
            "analyse métier, business analysis, transactions, transaction, "
            "secteur d'activité, industry, Inde, India, reporting, rapport, "
            "actualisation de données, data refresh, automatisation, automation"
        ),
        "highlights": (
            "Analyse interactive des montants par secteur d'activité et par genre",
            "Visualisation géographique des transactions par État indien",
            "Exploration des montants par année et par âge",
            "Automatisation de l'actualisation du rapport avec Power Automate",
        ),
        "public_url": "",
    },
    {
        "slug": "quantdashboard",
        "title": "QuantDashboard - tableau de bord quantitatif multi-actifs",
        "summary": (
            "Application interactive R Shiny de suivi des cours, des rendements "
            "et des indicateurs de risque pour plusieurs classes d'actifs."
        ),
        "description": (
            "Tableau de bord développé avec R Shiny pour consulter les cours "
            "historiques de paires de devises, cryptoactifs, de l'indice S&P 500 "
            "et d'Apple. Les données sont récupérées avec tidyquant, synchronisées "
            "dans PostgreSQL hébergé sur Neon, puis utilisées pour calculer les "
            "rendements logarithmiques, les moyennes mobiles à 20, 50 et 200 jours, "
            "la performance sur 30 jours, la volatilité annualisée, la VaR à 95 % "
            "sur un jour et le drawdown maximal. L'interface présente les tendances, "
            "la distribution des rendements et les indicateurs clés."
        ),
        "skills": (
            "R, Shiny, bslib, tidyquant, PostgreSQL, Neon, DBI, RPostgres, dplyr, "
            "ggplot2, zoo, analyse quantitative, séries temporelles, gestion du risque"
        ),
        "keywords": (
            "QuantDashboard, R, R Shiny, Shiny, bslib, tidyquant, PostgreSQL, Neon, "
            "DBI, RPostgres, dplyr, ggplot2, zoo, tableau de bord, dashboard, "
            "finance quantitative, quantitative finance, analyse quantitative, "
            "quantitative analysis, trading algorithmique, algorithmic trading, "
            "marchés financiers, financial markets, actifs, assets, devises, forex, "
            "crypto, cryptocurrency, cryptoactifs, actions, equities, S&P 500, "
            "rendements, returns, volatilité, volatility, VaR, value at risk, "
            "drawdown, gestion du risque, risk management, moyennes mobiles, "
            "moving averages, séries temporelles, time series, visualisation, "
            "data visualization, ETL, PostgreSQL database"
        ),
        "highlights": (
            "Suivi interactif de paires de devises, cryptoactifs, du S&P 500 et d'Apple",
            "Calcul des moyennes mobiles à 20, 50 et 200 jours et des rendements logarithmiques",
            "Affichage de la performance sur 30 jours, de la volatilité annualisée, de la VaR à 95 % sur un jour et du drawdown maximal",
            "Synchronisation des données de marché avec une base PostgreSQL hébergée sur Neon",
        ),
        "public_url": "",
    },
    {
        "slug": "mlops-breast-cancer",
        "title": "Pipeline MLOps - classification du cancer du sein",
        "summary": (
            "Pipeline reproductible de préparation, entraînement et prédiction "
            "avec le jeu Wisconsin intégré à scikit-learn."
        ),
        "description": (
            "Projet pédagogique reproductible séparant la préparation des données, "
            "l'entraînement d'une régression logistique et la prédiction. Le scaler est "
            "appris uniquement sur les données d'entraînement et les artefacts sont "
            "générés localement."
        ),
        "skills": "Python, pandas, scikit-learn, régression logistique, StandardScaler, pipeline reproductible, tests",
        "keywords": (
            "classification, classifier, machine learning, apprentissage automatique, "
            "scikit-learn, sklearn, régression logistique, logistic regression, "
            "préparation données, data preparation, pipeline, MLOps, modèle, "
            "évaluation, prédiction, prediction, santé, medical, reproductible"
        ),
        "highlights": (
            "Séparation des étapes de préparation, entraînement et prédiction",
            "Prévention de la fuite de données par apprentissage du scaler sur le seul jeu d'entraînement",
            "Tests de bout en bout du pipeline local",
        ),
        "public_url": "",
    },
    {
        "slug": "reinforcement-learning",
        "title": "Apprentissage par renforcement - DQN et PPO",
        "summary": (
            "Étude comparative de DQN et PPO sur CartPole et un environnement "
            "GridWorld personnel, avec configurations DQN pour LunarLander."
        ),
        "description": (
            "Travaux personnels d'apprentissage par renforcement comprenant la "
            "comparaison de DQN et PPO sur CartPole et un environnement GridWorld créé "
            "pour le projet, ainsi que l'exploration de variantes et paramètres DQN "
            "pour LunarLander."
        ),
        "skills": "Python, apprentissage par renforcement, DQN, PPO, PyTorch, CartPole, GridWorld, LunarLander, expérimentation",
        "keywords": (
            "reinforcement learning, apprentissage par renforcement, DQN, PPO, "
            "deep learning, apprentissage profond, PyTorch, torch, neural network, "
            "réseau neuronal, agent, simulation, optimisation, optimisation"
        ),
        "highlights": (
            "Comparaison de DQN et PPO sur CartPole et GridWorld",
            "Création d'un environnement GridWorld",
            "Exploration de variantes et paramètres DQN sur LunarLander",
        ),
        "public_url": "",
    },
    {
        "slug": "nlp-transformers",
        "title": "NLP - classification, Transformers et recherche sémantique",
        "summary": (
            "Ensemble de travaux pratiques sur la classification de fake news, "
            "la génération de titres, les embeddings et les Transformers."
        ),
        "description": (
            "Projets et notebooks d'étude couvrant la classification de fake news, "
            "la génération de titres avec T5, la recherche sémantique par embeddings, "
            "les Transformers, une introduction au RAG, et le suivi d'expériences "
            "avec MLflow."
        ),
        "skills": "Python, NLP, Transformers, T5, embeddings, recherche sémantique, RAG, MLflow, classification de texte",
        "keywords": (
            "NLP, traitement du langage, natural language processing, langage, "
            "Transformers, transformer, LLM, RAG, embeddings, recherche sémantique, "
            "semantic search, T5, fake news, classification de texte, text classification, "
            "génération de texte, text generation, MLflow, machine learning"
        ),
        "highlights": (
            "Classification de fake news et génération de titres avec T5",
            "Recherche sémantique avec embeddings et travaux sur les Transformers",
            "Introduction au RAG et suivi d'expériences avec MLflow",
        ),
        "public_url": "",
    },
    {
        "slug": "challenge-qrt",
        "title": "Challenge QRT - analyse de survie et modélisation",
        "summary": (
            "Analyse de survie et modélisation statistique réalisées dans le cadre "
            "d'un challenge de données."
        ),
        "description": (
            "Projet de challenge documenté dans le portfolio, centré sur l'analyse "
            "de survie et la modélisation statistique."
        ),
        "skills": "Statistiques, analyse de survie, modélisation, analyse de données",
        "keywords": (
            "statistique, statistics, survival, survie, actuariat, risque, risk, "
            "modélisation, modeling, data science, challenge, biostatistique, "
            "probabilité, probability"
        ),
        "highlights": (
            "Analyse de survie dans le cadre d'un challenge de données",
            "Modélisation statistique appliquée",
        ),
        "public_url": "",
    },
    {
        "slug": "inference-reseau",
        "title": "Inférence de réseau - notebooks et scripts d'analyse",
        "summary": (
            "Travaux d'étude sur un problème d'inférence de réseau : analyse, diagnostic "
            "et génération de prédictions avec CatBoost."
        ),
        "description": (
            "Projet d'étude en biostatistique composé de notebooks et de scripts d'analyse "
            "critique des résultats, de diagnostic, de comparaison de variables, de génération "
            "et d'optimisation de prédictions, avec CatBoost et une interface exploratoire. "
            "Ce sont des itérations de travail, sans point d'entrée final unique."
        ),
        "skills": "Python, CatBoost, inférence de réseau, analyse de données, diagnostic de modèles",
        "keywords": (
            "inférence de réseau, network inference, réseau, réseaux, graphe, biostatistique, "
            "bioinformatique, catboost, machine learning, prédiction"
        ),
        "highlights": (
            "Scripts d'analyse critique et de diagnostic des prédictions",
            "Optimisation de prédictions avec CatBoost",
        ),
        "public_url": "",
    },
    {
        "slug": "detection-qtl-r",
        "title": "Détection de QTL en R",
        "summary": "Projet de détection de QTL (loci de caractères quantitatifs) réalisé en R.",
        "description": (
            "Mini-projet annuel de biostatistique consacré à la détection de QTL, réalisé "
            "avec des scripts R et des résultats exportés au format CSV."
        ),
        "skills": "R, détection de QTL, statistique, biostatistique, génétique",
        "keywords": (
            "QTL, génétique, génomique, biostatistique, bioinformatique, cartographie de QTL"
        ),
        "highlights": (
            "Détection de QTL avec des scripts R",
            "Résultats exportés au format CSV",
        ),
        "public_url": "",
    },
    {
        "slug": "statistiques-grande-dimension",
        "title": "Statistiques en grande dimension en R",
        "summary": (
            "Analyses statistiques en grande dimension en R sur des jeux de données omiques, "
            "protéiques et de survie."
        ),
        "description": (
            "Travaux d'étude en R sur des données de grande dimension (jeux omics, protéines "
            "et survie de rats) réalisés dans le cadre d'un projet de statistiques en grande "
            "dimension."
        ),
        "skills": "R, statistiques en grande dimension, omics, analyse de survie, biostatistique",
        "keywords": (
            "grande dimension, high dimension, omics, protéomique, protéines, survie, survival, "
            "biostatistique, génomique, bioinformatique"
        ),
        "highlights": (
            "Analyses en R sur des jeux de données omiques et de survie",
        ),
        "public_url": "",
    },
    {
        "slug": "catpca-shiny",
        "title": "Dashboard CATPCA - application Shiny en R",
        "summary": (
            "Application Shiny interactive pour l'analyse en composantes principales "
            "catégorielles."
        ),
        "description": (
            "Application R Shiny permettant d'importer un fichier CSV ou ARFF et d'explorer "
            "une analyse en composantes principales catégorielles (CATPCA) avec des "
            "graphiques interactifs, des tableaux et des corrélations."
        ),
        "skills": "R, Shiny, Gifi, ggplot2, plotly, dplyr, CATPCA, visualisation de données",
        "keywords": (
            "shiny, catpca, acp, analyse en composantes principales, statistique multivariée, "
            "analyse multivariée, plotly, ggplot2"
        ),
        "highlights": (
            "Import de fichiers CSV et ARFF dans une interface interactive",
            "Visualisations interactives avec plotly et corrélations avec corrplot",
        ),
        "public_url": "",
    },
    {
        "slug": "etude-de-cas-r-multivariee",
        "title": "Étude de cas en R - ANOVA multivariée et analyse bayésienne",
        "summary": (
            "Scripts R d'analyse statistique multivariée et bayésienne avec jeux de données "
            "de travail."
        ),
        "description": (
            "Étude de cas en R rassemblant des scripts d'ANOVA multivariée, d'AOV-PLS et "
            "d'analyse statistique et bayésienne, avec des graphiques d'effets indirects."
        ),
        "skills": "R, ANOVA multivariée, AOV-PLS, statistique bayésienne, analyse multivariée",
        "keywords": (
            "anova, anova multivariée, analyse multivariée, statistique multivariée, bayésien, "
            "bayésienne, bayesian, effet indirect, médiation"
        ),
        "highlights": (
            "Analyses ANOVA multivariée et AOV-PLS en R",
            "Graphiques d'effets indirects",
        ),
        "public_url": "",
    },
    {
        "slug": "modelisation-bayesienne",
        "title": "Modélisation bayésienne en R",
        "summary": (
            "Modélisation statistique bayésienne en R, des lois a priori à l'inférence "
            "a posteriori, avec modèles autorégressifs et simulation Monte-Carlo."
        ),
        "description": (
            "Développer des modèles statistiques bayésiens en R en formulant des lois a "
            "priori et en étudiant l'inférence a posteriori. Étudier des modèles "
            "autorégressifs et mettre en œuvre des méthodes de simulation de type "
            "Monte-Carlo pour explorer les distributions et estimer les paramètres."
        ),
        "skills": (
            "Statistique bayésienne, inférence bayésienne, lois a priori, inférence "
            "a posteriori, modèles autorégressifs, Monte-Carlo, simulation MCMC, R"
        ),
        "keywords": (
            "bayésien, bayésienne, bayesian, inférence bayésienne, loi a priori, prior, "
            "inférence a posteriori, posterior, Monte-Carlo, Monte Carlo, simulation, MCMC, "
            "Gibbs, Metropolis-Hastings, acceptation-rejet, autorégressif, séries temporelles, "
            "time series, R, statistique, statistiques, modélisation statistique"
        ),
        "highlights": (
            "Formulation de modèles bayésiens à partir de lois a priori et étude de l'inférence a posteriori",
            "Étude de modèles autorégressifs en R",
            "Mise en œuvre de méthodes de simulation Monte-Carlo pour l'inférence bayésienne",
        ),
        "public_url": "",
    },
    {
        "slug": "pbc-rstan-survival",
        "title": "Survie clinique bayésienne - modèle Weibull avec RStan",
        "summary": (
            "Modèle Weibull AFT avec censure à droite pour étudier la survie "
            "dans l'essai historique PBC."
        ),
        "description": (
            "Analyse reproductible en R et Stan du sous-ensemble randomisé de "
            "312 participants du jeu survival::pbc. Le modèle Weibull AFT prend "
            "en compte la censure à droite et ajuste l'association du traitement "
            "par D-pénicillamine, de l'âge, de la log-bilirubine et de l'albumine "
            "avec le temps avant transplantation ou décès. Quatre chaînes de "
            "2 000 itérations (1 000 de warmup) ont donné zéro divergence et un "
            "R-hat maximal de 1,0008. Le rapport de temps médian du traitement "
            "est 1,06 (intervalle crédible à 95 % : 0,85–1,31) ; l'intervalle "
            "inclut 1, et l'analyse ne permet pas de conclusion thérapeutique."
        ),
        "skills": (
            "R, RStan, Stan, statistique bayésienne, survie, analyse de survie, "
            "modèle Weibull, modèle AFT, données censurées, MCMC, diagnostic "
            "de convergence, biostatistique"
        ),
        "keywords": (
            "bayésien, bayésienne, bayesian, RStan, Stan, biostatistique, "
            "biostatistics, survie, survival analysis, analyse de survie, "
            "modèle de survie, Weibull, AFT, accelerated failure time, "
            "censure, censored data, données censurées, essai clinique, "
            "clinical trial, MCMC, convergence, R-hat, santé, médical"
        ),
        "highlights": (
            "Modèle Weibull AFT avec vraisemblance adaptée à la censure à droite",
            "Analyse de 312 participants randomisés du jeu survival::pbc",
            "Quatre chaînes : zéro divergence et R-hat maximal de 1,0008",
            "Rapport de temps médian de 1,06, IC crédible à 95 % [0,85 ; 1,31]",
        ),
        "public_url": "",
    },
    {
        "slug": "prevision-solaire-bayesienne",
        "title": "Prévision solaire bayésienne - régression et Gibbs en R/Python",
        "summary": (
            "Régression linéaire bayésienne conjuguée pour prévoir la production "
            "solaire à 15 minutes avec incertitude prédictive."
        ),
        "description": (
            "Deux implémentations reproductibles en Python et R d'une régression "
            "linéaire bayésienne Normal-Inverse-Gamma échantillonnée par Gibbs. "
            "Le modèle prédit la puissance agrégée des centrales pendant la "
            "journée, à partir de la puissance et des variables météorologiques "
            "disponibles au moment de la prédiction. Sur un test chronologique "
            "commun de 826 observations, la MAE est de 2 420,75 en Python et "
            "2 425,35 en R, contre 2 495,88 pour la persistance ; les intervalles "
            "prédictifs à 95 % couvrent respectivement 96,0 % et 95,9 % des "
            "observations. Il s'agit d'une expérience sur environ 34 jours et "
            "deux centrales, pas d'un modèle opérationnel ni d'une prévision à "
            "long horizon."
        ),
        "skills": (
            "Python, R, statistique bayésienne, régression linéaire, "
            "Normal-Inverse-Gamma, échantillonnage de Gibbs, MCMC, "
            "prévision probabiliste, intervalles prédictifs, séries temporelles, "
            "énergie solaire, pandas, NumPy"
        ),
        "keywords": (
            "bayésien, bayésienne, bayesian, Gibbs, MCMC, régression bayésienne, "
            "bayesian regression, régression linéaire, prédiction, prévision, "
            "forecast, forecasting, énergie solaire, solaire, photovoltaïque, "
            "solar, renewable energy, météo, time series, séries "
            "temporelles, incertitude, probabiliste, intervalle prédictif, "
            "Normal-Inverse-Gamma, production énergétique"
        ),
        "highlights": (
            "Implémentations cohérentes en R et Python avec échantillonnage de Gibbs",
            "Prévision à 15 minutes évaluée sur un test chronologique de 826 observations",
            "MAE Python/R inférieure à la référence de persistance sur ce test",
            "Couverture des intervalles prédictifs à 95 % proche de 96 %",
        ),
        "public_url": "",
    },
    {
        "slug": "machine-deep-learning-notebooks",
        "title": "Machine learning et deep learning (arbres, CNN, segmentation)",
        "summary": (
            "Collection de notebooks : arbres, forêts aléatoires, réseaux de neurones, CNN, "
            "segmentation, détection d'images et classification d'activité humaine."
        ),
        "description": (
            "Notebooks d'étude couvrant CART et bagging, forêts aléatoires, approximation par "
            "noyaux, classification par réseau de neurones, CNN, détection et segmentation "
            "d'images, classification d'activités humaines, ainsi que l'ouverture et "
            "l'inspection de fichiers NetCDF avec xarray dans un notebook d'étude. "
            "Le dépôt comprend aussi un notebook de physics-informed machine learning. "
            "Ce sont des travaux pratiques, pas un projet logiciel unique."
        ),
        "skills": (
            "Python, scikit-learn, réseaux de neurones, CNN, forêts aléatoires, "
            "segmentation d'images, classification, NetCDF, xarray"
        ),
        "keywords": (
            "machine learning, apprentissage automatique, deep learning, réseau de neurones, "
            "CNN, random forest, forêt aléatoire, arbre de décision, "
            "segmentation, vision par ordinateur, computer vision, capteurs, "
            "scikit-learn, PIML"
        ),
        "highlights": (
            "Notebooks sur les arbres, les forêts aléatoires et les réseaux de neurones",
            "Classification d'activités physiques à partir de capteurs de smartphone",
            "Ouverture et inspection de fichiers NetCDF avec xarray dans un notebook d'étude",
        ),
        "public_url": "",
    },
    {
        "slug": "spark-mapreduce",
        "title": "Spark et MapReduce - traitement de données volumineuses",
        "summary": "Exercices MapReduce (mapper/reducer) et PySpark avec Spark SQL.",
        "description": (
            "Deux notebooks d'exercices : un traitement de type mapper/reducer et des "
            "exercices PySpark de chargement, transformation et agrégation avec Spark SQL, "
            "accompagnés de rapports."
        ),
        "skills": "PySpark, Spark SQL, MapReduce, Hadoop, Python, big data",
        "keywords": (
            "big data, spark, pyspark, spark sql, mapreduce, hadoop, data engineering, "
            "pipeline de données, agrégation"
        ),
        "highlights": (
            "Traitements mapper/reducer et agrégations avec Spark SQL",
            "Rapports associés aux exercices MapReduce et PySpark",
        ),
        "public_url": "",
    },
    {
        "slug": "programmation-concurrente-python",
        "title": "Calcul parallèle en Python",
        "summary": (
            "Exercices sur les threads, le multiprocessing, asyncio et la communication "
            "entre processus."
        ),
        "description": (
            "Exercices Python sur les threads et les verrous, le multiprocessing avec Pipe et "
            "Queue, la programmation asynchrone avec asyncio, le motif producteur/consommateur, "
            "un benchmark numérique et une régression avec PyTorch."
        ),
        "skills": "Python, threads, multiprocessing, asyncio, PyTorch, NumPy",
        "keywords": (
            "concurrence, programmation concurrente, multithreading, multiprocessing, "
            "asyncio, calcul scientifique"
        ),
        "highlights": (
            "Verrous, conditions de course et motif producteur/consommateur",
            "Comparaison threads, processus et asyncio",
        ),
        "public_url": "",
    },
    {
        "slug": "traitement-image-wiener",
        "title": "Traitement d'image - filtre de Wiener et mesures de netteté",
        "summary": (
            "Filtrage d'images (filtre de Wiener, domaine fréquentiel) et analyse de scores "
            "de netteté."
        ),
        "description": (
            "Scripts et notebook de traitement d'image : démonstration d'un filtre de Wiener "
            "avec NumPy, OpenCV et Matplotlib, filtrage dans le domaine fréquentiel et analyse "
            "de mesures de netteté avec un rapport LaTeX."
        ),
        "skills": "Python, NumPy, OpenCV, Matplotlib, filtrage, traitement du signal",
        "keywords": (
            "traitement d'image, traitement du signal, filtre de wiener, filtrage, "
            "opencv, netteté, vision par ordinateur, computer vision"
        ),
        "highlights": (
            "Filtre de Wiener comparé pour plusieurs valeurs du paramètre K",
            "Analyse de scores de netteté documentée dans un rapport LaTeX",
        ),
        "public_url": "",
    },
    {
        "slug": "flask-partage-topics",
        "title": "Application web Flask - topics et liens (JSON, pytest)",
        "summary": (
            "Application Flask qui affiche des topics et des liens depuis un fichier JSON "
            "local, avec tests de routes."
        ),
        "description": (
            "Petite application web Flask avec pages Jinja, données JSON locales, routes "
            "expérimentales vers un annuaire distant configurable par variable d'environnement "
            "et tests pytest des routes locales."
        ),
        "skills": "Python, Flask, Jinja, JSON, pytest, API",
        "keywords": (
            "flask, application web, jinja, pytest"
        ),
        "highlights": (
            "Application web Flask avec tests pytest des routes",
            "Configuration par variables d'environnement, exécution locale par défaut",
        ),
        "public_url": "",
    },
    {
        "slug": "prevision-ventes-multi-sites",
        "title": "Prévision des ventes multi-sites - Parker Aerospace",
        "summary": (
            "Analyse et prévision des ventes de six sites, avec tableau de bord interactif "
            "et déploiement."
        ),
        "description": (
            "Participation à l'extraction et au traitement par lots des données DB2, à la "
            "création d'un tableau de bord interactif Python/Dash, aux tests et au déploiement "
            "avec Azure DevOps et Azure. Comparaison d'un réseau de neurones, de Gradient "
            "Boosting et d'une régression pénalisée. Résultats détaillés confidentiels."
        ),
        "skills": "SQL, DB2, Python, Dash, machine learning, Azure DevOps, Azure",
        "keywords": (
            "prévision des ventes, forecasting, séries temporelles, tableau de bord, dash, "
            "db2, gradient boosting, régression pénalisée, azure, déploiement"
        ),
        "highlights": (
            "Extraction et traitement par lots des données DB2",
            "Tableau de bord interactif avec prévisions téléchargeables",
        ),
        "public_url": "",
    },
    {
        "slug": "challenge-sncf-trafic",
        "title": "Challenge SNCF - prévision du trafic ferroviaire",
        "summary": (
            "Analyse exploratoire et prévision du trafic ferroviaire avec SARIMA et XGBoost "
            "(MAE de 0,8)."
        ),
        "description": (
            "Analyse exploratoire et modélisation prédictive du trafic ferroviaire avec "
            "SARIMA et XGBoost, sur les données disponibles sur le site du challenge."
        ),
        "skills": "Python, SARIMA, XGBoost, séries temporelles",
        "keywords": (
            "séries temporelles, time series, sarima, xgboost, prévision, forecasting, "
            "transport, trafic ferroviaire"
        ),
        "highlights": (
            "Comparaison d'un modèle SARIMA et d'un modèle XGBoost",
            "MAE de 0,8 sur les données du challenge",
        ),
        "public_url": "",
    },
    {
        "slug": "agent-candidatures-llm",
        "title": "Agent de candidatures basé sur LLM - génération de CV et de lettres",
        "summary": (
            "Application Flask qui génère des CV et des lettres adaptés aux offres "
            "avec des modèles de langage locaux ou via API."
        ),
        "description": (
            "Application personnelle qui analyse une offre d'emploi et génère un CV et une "
            "lettre de motivation à partir de faits vérifiés. Intégration de modèles de "
            "langage locaux (Ollama, Qwen) et d'une API (OpenRouter), ingénierie de prompts "
            "avec contraintes de véracité, sélection de projets pertinents, score de "
            "correspondance et export PDF compatible ATS. Tests automatisés avec pytest."
        ),
        "skills": "Python, Flask, LLM, ingénierie de prompts, Ollama, OpenRouter, NLP, SQLite, pytest",
        "keywords": (
            "LLM, large language model, grand modèle de langage, IA générative, generative AI, "
            "GenAI, prompt engineering, RAG, retrieval augmented generation, NLP, Ollama, "
            "OpenRouter, intelligence artificielle"
        ),
        "highlights": (
            "Intégration de LLM locaux (Ollama) et d'une API (OpenRouter)",
            "Prompts contraints pour limiter les inventions et respecter les faits fournis",
            "Score de correspondance offre/profil et sélection des projets pertinents",
            "Tests automatisés avec pytest",
        ),
        "public_url": "",
    },
)


def project_slug(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title.casefold())
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return slug[:80] or "projet"


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9+#]+", " ", ascii_text)


def rank_projects(offer_text: str, projects: list[dict]) -> list[dict]:
    """Rank projects by exact normalized keyword phrases present in the offer."""
    normalized_offer = f" {_normalize(offer_text)} "
    ranked = []
    for project in projects:
        keywords = [
            keyword.strip()
            for keyword in project["keywords"].replace("\n", ",").split(",")
            if keyword.strip()
        ]
        matched = []
        for keyword in keywords:
            normalized_keyword = _normalize(keyword).strip()
            if normalized_keyword and f" {normalized_keyword} " in normalized_offer:
                matched.append(keyword)
        unique_matches = list(dict.fromkeys(matched))
        score = min(100, len(unique_matches) * 20)
        ranked.append(
            {
                **dict(project),
                "match_score": score,
                "matched_keywords": unique_matches[:5],
                "match_reason": (
                    "Correspondances : " + ", ".join(unique_matches[:5])
                    if unique_matches
                    else "Aucun mot-clé direct trouvé dans l'offre"
                ),
            }
        )
    return sorted(
        ranked,
        key=lambda item: (-item["match_score"], item["title"].casefold()),
    )
