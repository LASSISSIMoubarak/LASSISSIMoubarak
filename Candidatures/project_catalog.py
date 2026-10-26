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
)


def project_slug(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title.casefold())
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return slug[:80] or "projet"


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


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
