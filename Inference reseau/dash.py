import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import pandas as pd

# Jeu de données exemple
df = px.data.gapminder().query("year == 2007")

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Dashboard interactif avec barre de recherche"),

    # Barre de recherche
    dcc.Input(
        id="search-bar",
        type="text",
        placeholder="Rechercher un pays...",
        style={"width": "40%", "padding": "10px"}
    ),

    # Filtre dropdown
    dcc.Dropdown(
        id="continent-filter",
        options=[{"label": c, "value": c} for c in df["continent"].unique()],
        placeholder="Filtrer par continent",
        style={"width": "40%", "margin-top": "10px"}
    ),

    # Graphique
    dcc.Graph(id="graph"),

    # Tableau
    dash_table.DataTable(
        id="table",
        columns=[{"name": col, "id": col} for col in df.columns],
        page_size=10,
        style_table={"overflowX": "auto"}
    )
])

@app.callback(
    [Output("graph", "figure"),
     Output("table", "data")],
    [Input("search-bar", "value"),
     Input("continent-filter", "value")]
)
def update_dashboard(search_value, continent_value):
    filtered_df = df.copy()

    # Filtre texte
    if search_value:
        filtered_df = filtered_df[filtered_df["country"].str.contains(search_value, case=False)]

    # Filtre dropdown
    if continent_value:
        filtered_df = filtered_df[filtered_df["continent"] == continent_value]

    # Graphique
    fig = px.scatter(
        filtered_df,
        x="gdpPercap",
        y="lifeExp",
        size="pop",
        color="continent",
        hover_name="country",
        title="Relation PIB / Espérance de vie"
    )

    return fig, filtered_df.to_dict("records")

if __name__ == "__main__":
    app.run_server(debug=True)
