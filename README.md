
# Projet : Moubarak LASSISSI — Portfolio et travaux

Ce dépôt centralise les projets et travaux (Python, R, notebooks, prototypes MLOps) de Moubarak LASSISSI.

Dernières actions réalisées
- Réorganisation des projets par catégorie (dossiers créés automatiquement) :
	- `Biostatistiques/`, `Statistiques/`, `SparkBigData/`, `Flask/`, `Traitement d'image/`, `Reinforcement Learning/`, `NLP/`
- Génération d'un portfolio statique : `index.html` (généré depuis les classifications).

Fichiers utiles
- `projects_classification_final.csv` : résumé et catégorie détectée pour chaque projet.
- `scan_projects.py` / `scan_projects_quick.py` : scripts pour analyser le workspace et extraire des mots-clés.
- `finalize_classification.py` : post-traitement et attribution de badges.
- `generate_portfolio.py` + `portfolio_template.html` : génèrent `index.html` à partir des classifications.

Générer ou mettre à jour le portfolio
1. (option rapide) lancer le scanner top-level et finaliser :

```powershell
python .\scan_projects_quick.py --root . --out quick_projects.csv
python .\finalize_classification.py
```

2. Générer la page HTML :

```powershell
python .\generate_portfolio.py
# ouvre index.html dans le navigateur ou servez localement
python -m http.server 8000
# puis ouvrez http://localhost:8000/index.html
```

Contrôle Git (après réorganisation)
- Voir les fichiers staged et confirmer les renommages :

```bash
git status
git diff --staged
```

- Commit + push :

```bash
git commit -m "Réorganisation des projets par catégorie et génération du portfolio"
git push origin main
```

Notes et bonnes pratiques
- Vérifiez les dossiers marqués `Unknown` dans `projects_classification_final.csv` si certains projets doivent être classés différemment.
- Si vous voulez que j'ajoute des badges automatiquement dans les README de chaque projet, dites "Oui badge".

Contact
- Email : lassissimoubarak20@gmail.com

---
Fichier généré automatiquement par les outils du dépôt ; modifiez ce README si vous souhaitez une présentation différente.

