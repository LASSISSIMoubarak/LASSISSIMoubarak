# Traitement d'image

Ce dossier regroupe plusieurs travaux autour du filtrage et de l'analyse
d'images :

- `pythonTraitement_d'image.py` — démonstration d'un filtre de Wiener.
- `Traitement_d'image_TP_Moubarak_LASSISSI.py` — script de travaux pratiques.
- `Signale_filtrage/` — exemples de filtrage dans le domaine fréquentiel.
- `Image_folder/` — images d'entrée d'exercices.
- `analyse_scores_nettete.ipynb` et `rapport_nettete.tex` — analyse de mesures
  de netteté et rapport associé.

Pour le script de filtre de Wiener, installe `numpy`, `opencv-python` et
`matplotlib`, puis lance depuis la racine du dépôt :

```powershell
python "Traitement d'image\pythonTraitement_d'image.py"
```

Le script utilise par défaut `Image_folder/testna_slika1a.bmp`. Une autre image
peut être indiquée avec `--image "chemin\vers\image.bmp"`. Il compare trois
valeurs fixes du paramètre K afin d'éviter un long calcul aléatoire. Les autres
scripts et notebooks peuvent avoir des dépendances supplémentaires ; vérifie
leurs imports avant exécution.
