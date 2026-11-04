"""Compare les mots-clés d'une offre avec ce que le dossier du candidat documente."""
import re
import unicodedata
from urllib.parse import quote_plus

# Terme affiché -> variantes reconnues (comparées sans accents ni casse).
SKILL_VOCABULARY = {
    "Python": ["python"],
    "R": ["langage r", "rstudio", "r studio", "tidyverse", "ggplot2"],
    "SQL": ["sql", "postgresql", "mysql", "sql server", "t-sql"],
    "NoSQL": ["nosql", "mongodb"],
    "Excel": ["excel"],
    "VBA": ["vba"],
    "Power BI": ["power bi", "powerbi"],
    "DAX": ["dax"],
    "Power Query": ["power query"],
    "Power Automate": ["power automate"],
    "Tableau": ["tableau"],
    "Looker": ["looker"],
    "Qlik": ["qlik"],
    "SAS": ["sas"],
    "SPSS": ["spss"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "scikit-learn": ["scikit-learn", "scikit learn", "sklearn"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "Keras": ["keras"],
    "XGBoost": ["xgboost"],
    "Spark": ["spark", "pyspark"],
    "Hadoop": ["hadoop"],
    "Kafka": ["kafka"],
    "Airflow": ["airflow"],
    "dbt": ["dbt"],
    "ETL": ["etl", "extract transform load"],
    "Data warehouse": ["data warehouse", "entrepot de donnees"],
    "Snowflake": ["snowflake"],
    "Databricks": ["databricks"],
    "BigQuery": ["bigquery"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure"],
    "Azure DevOps": ["azure devops"],
    "GCP": ["gcp", "google cloud"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Git": ["git", "github", "gitlab"],
    "CI/CD": ["ci/cd", "ci cd", "integration continue"],
    "MLOps": ["mlops"],
    "MLflow": ["mlflow"],
    "DVC": ["dvc"],
    "FastAPI": ["fastapi"],
    "Flask": ["flask"],
    "API": ["api", "apis", "api rest", "restful"],
    "Linux": ["linux"],
    "NLP": ["nlp", "traitement du langage", "natural language processing"],
    "LLM": ["llm", "llms", "grands modeles de langage", "large language model"],
    "Deep learning": ["deep learning", "apprentissage profond"],
    "Machine learning": ["machine learning", "apprentissage automatique"],
    "Computer vision": ["computer vision", "vision par ordinateur"],
    "Séries temporelles": ["serie temporelle", "series temporelles", "time series"],
    "Modélisation statistique": [
        "modelisation statistique", "statistical modeling", "statistical modelling",
    ],
    "Statistiques": ["statistique", "statistiques", "statistics"],
    "Tests A/B": ["test a/b", "tests a/b", "a/b testing", "ab testing"],
    "Régression": ["regression"],
    "Data visualisation": [
        "data visualisation", "data visualization", "dataviz", "visualisation de donnees",
    ],
    "Reporting": ["reporting"],
    "KPI": ["kpi", "indicateurs de performance"],
    "Tableaux de bord": ["tableau de bord", "tableaux de bord", "dashboard", "dashboards"],
    "Business intelligence": ["business intelligence"],
    "Agile": ["agile", "scrum", "kanban"],
    "Data engineering": ["data engineering", "data engineer", "ingenierie des donnees"],
    "Data quality": ["data quality", "qualite des donnees"],
    "Data governance": ["data governance", "gouvernance des donnees"],
    "Jupyter": ["jupyter"],
    "Matplotlib": ["matplotlib"],
    "Plotly": ["plotly"],
    "Streamlit": ["streamlit"],
    "Java": ["java"],
    "Scala": ["scala"],
    "C++": ["c++"],
    "Bash": ["bash", "shell"],
    "Optimisation": ["optimisation", "optimization", "recherche operationnelle"],
    "Bayésien": ["bayesien", "bayesian"],
    "Anglais": ["anglais", "english"],
}

# Sans lien direct avec une compétence à apprendre : on les ignore dans la détection libre.
ACRONYM_STOPLIST = {
    "CDI", "CDD", "RH", "ET", "OU", "LE", "LA", "LES", "UN", "UNE", "DE", "DU", "DES", "EN",
    "SA", "SAS", "SARL", "PME", "ETI", "USA", "UK", "FR", "EU", "TVA", "HT", "TTC", "BAC",
    "BTS", "DUT", "MBA", "CV", "RTT", "IT", "OK", "AM", "PM", "NB", "ETC", "AVEC", "POUR",
    "PARIS", "LYON", "NANTES", "ANGERS", "OF", "THE", "AND", "FOR", "TO", "IN", "ON",
}

LEARNING_SOURCES = (
    ("DataCamp", "https://www.datacamp.com/search?q={q}"),
    ("Coursera", "https://www.coursera.org/search?query={q}"),
    ("YouTube", "https://www.youtube.com/results?search_query={q}"),
)


def normalize(text):
    text = unicodedata.normalize("NFKD", (text or "").casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[’']", "'", text)


def contains_term(normalized_text, term):
    pattern = r"(?<![a-z0-9])" + re.escape(normalize(term)) + r"(?![a-z0-9])"
    return re.search(pattern, normalized_text) is not None


def _label_in(normalized_text, variants):
    return any(contains_term(normalized_text, variant) for variant in variants)


def detect_free_acronyms(offer_text, known_variants):
    found = []
    for match in re.finditer(r"\b[A-Z][A-Z0-9+#/.\-]{1,7}\b", offer_text or ""):
        token = match.group(0).strip(".-/")
        if len(token) < 2 or token in ACRONYM_STOPLIST or token.isdigit():
            continue
        if normalize(token) in known_variants or token in found:
            continue
        found.append(token)
    return found


def learning_links(term):
    query = quote_plus(f"{term} tutorial")
    return [(name, url.format(q=query)) for name, url in LEARNING_SOURCES]


def analyze_keyword_gap(offer_text, candidate_text):
    """Retourne les mots-clés de l'offre déjà documentés et ceux qui manquent."""
    normalized_offer = normalize(offer_text)
    normalized_candidate = normalize(candidate_text)
    known_variants = {
        normalize(variant) for variants in SKILL_VOCABULARY.values() for variant in variants
    }
    known_words = {word for variant in known_variants for word in re.split(r"[^a-z0-9+#]+", variant)}
    wanted = []
    for label, variants in SKILL_VOCABULARY.items():
        if _label_in(normalized_offer, variants):
            wanted.append((label, variants))
    for token in detect_free_acronyms(offer_text, known_variants | known_words):
        wanted.append((token, [token]))

    covered, missing = [], []
    for label, variants in wanted:
        (covered if _label_in(normalized_candidate, variants) else missing).append(label)

    total = len(wanted)
    return _result(total, covered, missing)


def ungrounded_labels(text, candidate_text):
    """Compétences citées dans `text` qui ne figurent nulle part dans les sources du candidat."""
    normalized_text = normalize(text)
    normalized_candidate = normalize(candidate_text)
    return [
        label
        for label, variants in SKILL_VOCABULARY.items()
        if label != "Tableau"
        and _label_in(normalized_text, variants)
        and not _label_in(normalized_candidate, variants)
    ]


def _result(total, covered, missing):
    return {
        "total": total,
        "covered": covered,
        "missing": [{"term": term, "links": learning_links(term)} for term in missing],
        "score": round(100 * len(covered) / total) if total else None,
    }
