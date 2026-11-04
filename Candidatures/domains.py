"""Domaines proposés pour une candidature spontanée (sans offre publiée)."""

SPONTANEOUS_MARKER = "[Candidature spontanée"

# Mots-clés attendus en général dans le domaine : ils servent à classer les projets
# et à repérer les compétences à acquérir, jamais comme preuve d'expérience.
DOMAINS = {
    "biostatistique": (
        "Biostatistique",
        "biostatistique, statistiques, modélisation statistique, analyse de survie, survival, "
        "essais cliniques, données cliniques, régression, régression logistique, modèle de Cox, "
        "modèles mixtes, statistiques en grande dimension, omics, génomique, bioinformatique, "
        "QTL, inférence bayésienne, R, SAS, Python, reporting, rapport statistique",
    ),
    "data-science": (
        "Data science / Machine learning",
        "data science, machine learning, apprentissage automatique, deep learning, Python, "
        "scikit-learn, pandas, PyTorch, modélisation statistique, séries temporelles, "
        "détection d'anomalies, classification, régression, feature engineering, SQL, Git",
    ),
    "data-analyst": (
        "Data analyst / BI",
        "data analyst, business intelligence, Power BI, DAX, SQL, Excel, tableaux de bord, "
        "reporting, KPI, data visualisation, Power Query, ETL, statistiques, Python",
    ),
    "mlops": (
        "MLOps / industrialisation",
        "MLOps, machine learning, industrialisation, pipeline, CI/CD, Docker, MLflow, Git, "
        "Azure DevOps, tests, déploiement, API, FastAPI, Python, cloud",
    ),
    "data-engineering": (
        "Data engineering / Big data",
        "data engineering, big data, Spark, PySpark, MapReduce, Hadoop, ETL, SQL, Python, "
        "pipeline de données, data warehouse, Docker, Airflow, cloud",
    ),
    "nlp": (
        "NLP / IA générative",
        "NLP, traitement du langage, Transformers, LLM, embeddings, recherche sémantique, "
        "classification de texte, RAG, fine-tuning, PyTorch, Python, deep learning",
    ),
    "vision": (
        "Vision par ordinateur / traitement d'image",
        "vision par ordinateur, computer vision, traitement d'image, segmentation, détection, "
        "CNN, deep learning, OpenCV, filtrage, Python, PyTorch",
    ),
    "quant": (
        "Finance quantitative / risque",
        "finance quantitative, risque, actuariat, séries temporelles, modélisation statistique, "
        "Python, statistiques, backtesting, tableau de bord, optimisation, probabilités",
    ),
}


def domain_choices():
    return [(key, label) for key, (label, _keywords) in DOMAINS.items()]


def build_spontaneous_description(domain_key, position):
    label, keywords = DOMAINS[domain_key]
    return (
        f"{SPONTANEOUS_MARKER} — aucune offre publiée]\n"
        f"Poste visé : {position}\n"
        f"Domaine visé : {label}\n"
        f"Sujets et compétences généralement attendus dans ce domaine : {keywords}."
    )


def is_spontaneous(job_description):
    return (job_description or "").lstrip().startswith(SPONTANEOUS_MARKER)
