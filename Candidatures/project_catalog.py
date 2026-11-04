from __future__ import annotations

import re
import unicodedata


PROJECT_SEEDS = (
    {
        "slug": "solarwatch",
        "title": "SolarWatch — surveillance de performance photovoltaïque",
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
        "title": "Tableau de bord Power BI — transactions en Inde",
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
        "title": "QuantDashboard — tableau de bord quantitatif multi-actifs",
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
        "title": "Pipeline MLOps — classification du cancer du sein",
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
        "title": "Apprentissage par renforcement — DQN et PPO",
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
        "title": "NLP — classification, Transformers et recherche sémantique",
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
        "title": "Challenge QRT — analyse de survie et modélisation",
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
        "title": "Inférence de réseau — notebooks et scripts d'analyse",
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
        "title": "Détection de QTL en R — mini-projet annuel",
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
        "title": "Statistiques en grande dimension — analyses en R",
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
        "title": "Dashboard CATPCA — application Shiny en R",
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
        "title": "Étude de cas en R — ANOVA multivariée et analyse bayésienne",
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
        "title": "Modélisation bayésienne — scripts R",
        "summary": (
            "Exercices R de modélisation bayésienne : lois a priori, modèles autorégressifs "
            "et méthodes de simulation."
        ),
        "description": (
            "Scripts R d'étude portant sur les lois a priori, les modèles autorégressifs et "
            "les méthodes de simulation en statistique bayésienne."
        ),
        "skills": "R, statistique bayésienne, modèles autorégressifs, méthodes de simulation",
        "keywords": (
            "bayésien, bayésienne, bayesian, inférence bayésienne, loi a priori, prior, MCMC, "
            "autorégressif, séries temporelles, time series"
        ),
        "highlights": (
            "Lois a priori et modèles autorégressifs en R",
            "Méthodes de simulation pour l'inférence bayésienne",
        ),
        "public_url": "",
    },
    {
        "slug": "machine-deep-learning-notebooks",
        "title": "Machine learning et deep learning — notebooks de travaux pratiques",
        "summary": (
            "Collection de notebooks : arbres, forêts aléatoires, réseaux de neurones, CNN, "
            "segmentation, détection d'images et classification d'activité humaine."
        ),
        "description": (
            "Notebooks d'étude couvrant CART et bagging, forêts aléatoires, approximation par "
            "noyaux, classification par réseau de neurones, CNN, détection et segmentation "
            "d'images, classification d'activités humaines, données NetCDF et "
            "physics-informed machine learning. Ce sont des travaux pratiques, pas un projet "
            "logiciel unique."
        ),
        "skills": (
            "Python, scikit-learn, réseaux de neurones, CNN, forêts aléatoires, "
            "segmentation d'images, classification"
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
        ),
        "public_url": "",
    },
    {
        "slug": "spark-mapreduce",
        "title": "Spark et MapReduce — traitement de données volumineuses",
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
        "title": "Programmation concurrente et calcul en Python",
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
        "title": "Traitement d'image — filtre de Wiener et mesures de netteté",
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
        "title": "Application Flask de partage de topics",
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
