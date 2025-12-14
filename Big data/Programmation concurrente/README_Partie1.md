# Partie 1 
Il simule un petit flux de travail de type "serveur / bariste" : prise de commandes, préparation et service.
- **Fichier principal** : `Partie1.py`
- **Entrée attendue** : un fichier de commandes (texte)
- **Fichier de log** : `borabora.log` (généré par le script)
## But / Description
Le script modélise :
- des clients qui envoient des commandes temporelles (`Clients`),
- une pile LIFO `Pic` (post-it) pour sauvegarder les commandes à préparer,
- une file FIFO `Bar` pour les commandes prêtes à être servies,
- un `Bariste` qui prépare les consommations et un `Serveur` qui prend et sert les commandes.
Les principales classes sont: `Logable`,`Accessoire`, `Pic`, `Bar`, `Clients`, `Employe`, `Serveur`, `Bariste`.

comment ça marche?
- **Classe `Serveur`** : récupère les commandes depuis `Clients` (en respectant les temporisations), écrit chaque commande sur un post-it (pile `Pic`) et, lors de la phase de service, récupère les commandes prêtes dans `Bar` pour servir chaque consommation. Les étapes et événements sont tracés dans `borabora.log`

- **Classe `Bariste`** : prend les post-it depuis `Pic`, prépare chaque boisson de la commande puis place la commande prête dans `Bar` pour que le `Serveur` la serve.

## Format du fichier de commandes
Chaque ligne du fichier de commandes respecte le format :
```
<délai_en_secondes> <consommation1>,<consommation2>,...
```

```Par exemple
0 tequila sunrise,margarita
0 daiquiri,ti-punch
```

## Usage
```
python Partie1.py commandes.txt
```
Si `commandes.txt` n'existe pas, le script en crée un avec deux commandes d'exemple.
Après exécution, un fichier `borabora.log` est créé contenant les traces de log (le script écrit les logs sur ce fichier via la variable `logf`).
## Personnalisation 
- Activer/désactiver l'affichage console (verbose) : dans `Partie1.py` les instances `le_pic`, `le_bar`, `bob`, `alice` sont créées avec un paramètre `verbose` (True/False). 
- Modifier les commandes de test : éditez le fichier de commandes (`commandes.txt`) ou changez la section qui écrit le fichier par défaut.
## Points d'entrée utiles dans le code
- `main()` : orchestre `alice.run()` et `bob.run()` (Serveur/Bariste)
- `Clients.commande()` : logique de temporisation des commandes
- `Pic.embrocher()` / `Pic.liberer()` : pile LIFO
- `Bar.recevoir()` / `Bar.evacuer()` : file FIFO
