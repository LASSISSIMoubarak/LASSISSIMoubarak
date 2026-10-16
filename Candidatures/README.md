# Cap Candidatures

Application locale pour suivre les offres, preparer des brouillons de CV et de lettres avec Qwen via Ollama, puis exporter le suivi en Excel.

## Lancer sous Windows

Dans PowerShell, depuis ce dossier :

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Ouvre ensuite http://127.0.0.1:5000. L'application n'ecoute que sur l'ordinateur local.

Pour generer les brouillons, Ollama doit etre ouvert et le modele doit etre present :

```powershell
ollama pull qwen2.5:3b
```

Si tu utilises un autre modele Ollama, definis `OLLAMA_MODEL` avant de lancer l'application.

## Contenu de cette premiere version

- Profil candidat et CV de reference conserves dans une base SQLite locale.
- Import de PDF texte avec extraction locale ; les PDF scannes sans texte selectionnable demandent un OCR externe, non inclus ici.
- Saisie manuelle d'une offre ou collage de sa description.
- Statuts, notes et suivi manuel des reponses.
- Brouillons de CV et de lettres generes localement par Ollama, telechargeables en DOCX ou en PDF.
- Lettre de motivation mise en page par l'application avec objet, date, coordonnees et formule d'appel ; le modele ne fournit que le corps du texte.
- Export du tableau de suivi en XLSX.

La recherche automatique sur les sites d'emploi, la connexion a une boite mail et l'envoi de candidatures ne sont pas inclus. Aucun document n'est envoye automatiquement. Verifie chaque brouillon : le modele peut se tromper et ne doit pas inventer d'informations.

Les donnees sont stockees dans `instance/candidatures.sqlite3` et ne sont pas ajoutees a Git. Le serveur Ollama recoit le profil et la description de l'offre uniquement sur demande de generation ; le traitement du modele reste local.
