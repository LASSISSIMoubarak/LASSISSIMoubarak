import json
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests

app = Flask(__name__)

DATA_FILE = "data_base.json"
LOG_FILE = "client_logs.txt"
mon_URL= "http://22i008.stud.mua"

def log_client_info():
    """Log les informations du client (IP, URL)"""
    client_info = f"URL: {request.url} | IP: {request.remote_addr}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(client_info)
    except Exception as e:
        print(f"Erreur lors du logging client: {e}")

def load_data():
    """Charge les données locales"""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    """Sauvegarde les données locales"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.route("/", methods=["GET"])
def home():
    """Page d'accueil"""
    log_client_info()
    return render_template("welcome.html")


@app.route("/ws/topics")
def topics_list():
    """Liste les topics locaux"""
    log_client_info()
    data = load_data()
    topics_stats = {
        topic: {
            "items_count": len(items),
            "total_urls": sum(len(urls if isinstance(urls, list) else [urls]) for urls in items.values())
        }
        for topic, items in data.items()
    }
    return render_template("topics.html", topics=data.keys(), stats=topics_stats)


@app.route("/ws/topic/<topic_name>")
def topic_items(topic_name):
    """Liste les items d'un topic"""
    log_client_info()
    data = load_data()
    if topic_name not in data:
        return "Topic non trouvé", 404
    return render_template("topic_items.html", topic_name=topic_name, items=data[topic_name])


@app.route("/ws/topic/<topic_name>/<item_name>")
def item_urls(topic_name, item_name):
    """Liste les URLs d’un item"""
    log_client_info()
    data = load_data()
    if topic_name not in data or item_name not in data[topic_name]:
        return "Item non trouvé", 404
    urls = data[topic_name][item_name]
    if isinstance(urls, str):
        urls = [urls]
    return render_template("item_urls.html", topic_name=topic_name, item_name=item_name, urls=urls)


# Les autres serveurs

@app.route("/ws/annuaire")
def voir_annuaire():
    log_client_info()
    try:
        response = requests.get(ANNUAIRE_URL, timeout=5)
        response.raise_for_status()
        serveurs = response.json()
    except Exception as e:
        return f"Impossible d’accéder à l’annuaire : {e}"
    return render_template("annuaire.html", serveurs=serveurs)


@app.route("/ws/serveur/<path:server_url>")
def voir_contenu_serveur(server_url):
    """Affiche les topics d’un autre serveur Pythonpédia"""
    log_client_info()
    server_url = server_url.replace("|", "/") 
    try:
        resp = requests.get(f"{server_url}/ws/topics", timeout=5)
        resp.raise_for_status()
        data = resp.json() if resp.headers.get("Content-Type", "").startswith("application/json") else None
    except Exception as e:
        return f"Erreur en contactant {server_url} : {e}"

    if not data:
        return f"Le serveur {server_url} n’a pas renvoyé de données JSON valides."

    return render_template("serveur_topics.html", server_url=server_url, data=data)


@app.route("/ws/fusion")
def fusionner_serveurs():
    """Récupère tous les contenus des serveurs et fusionne dans ta base locale"""
    log_client_info()
    data_local = load_data()
    try:
        annuaire = requests.get(mon_URL, timeout=5).json()
    except Exception as e:
        return f"Erreur d’accès à l’annuaire : {e}"

    for serveur in annuaire:
        try:
            resp = requests.get(f"{serveur}/ws/topics", timeout=5)
            resp.raise_for_status()
            contenu = resp.json()
            # fusion 
            for topic, items in contenu.items():
                if topic not in data_local:
                    data_local[topic] = items
                else:
                    data_local[topic].update(items)
        except Exception as e:
            print(f"⚠️ Erreur {serveur}: {e}")
            continue

    save_data(data_local)
    return "Fusion terminée"


if __name__ == "__main__":
    app.run(debug=True, host='22i008.stud.mua', port=5000)
    
