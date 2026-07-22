import pandas as pd
import sqlite3
# Charger le CSV dans un DataFrame
df = pd.read_csv("ratSurvival.csv")

# Afficher les noms de colonnes pour aider à construire la requête SQL
print("Colonnes disponibles :", df.columns.tolist())

# Créer une base SQLite en mémoire et y charger le DataFrame
conn = sqlite3.connect(":memory:")
df.to_sql("ratSurvival", conn, index=False, if_exists="replace")

# Exemple de requête SQL (à adapter après avoir vu les colonnes)
# query = "SELECT * FROM ratSurvival WHERE colonne = 'valeur'"
# result = pd.read_sql_query(query, conn)
# print(result)

conn.close()