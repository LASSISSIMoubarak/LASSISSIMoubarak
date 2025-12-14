# Partie 2 — Résumé court

- Fichier : `Partie2.py`
- Entrée : `commandes.txt` (format : `<délai_en_secondes> <boisson1>,<boisson2>,...`)
- Lancer :
```
python Partie2.py commandes.txt
```

- Logs : `borabora.log`

- Les méthodes `Pic.embrocher`, `Bar.recevoir`, etc  sont `asynchroniser` et doivent être appelées avec `await`.
- `Clients` renvoie chaque commande au moment demandé (cooperatif via `await asyncio.sleep`).
- `Serveur` exécute deux boucles concurrentes : prise de commandes et service; `Bariste` prépare et poste au `Bar`.
- Terminaison propre : le run s'arrête quand `clients.done()` et `pic.empty()` et `bar.empty()`.

Pour debugger rapidement :
- Ouvrez `borabora.log` après exécution pour lire les traces.
- Pour plus de détails en live, activez `verbose=True` lors de la création de `Pic`/`Bar`/employés dans `main_async()`.
