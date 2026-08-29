# Partie 3 

- Entrée : `commandes.txt` (format : `<délai_en_secondes> <boisson1>,<boisson2>,...`).

- Logs : `borabora.log`
Points clés:
- `asyncio` et `asyncio.Queue` sont utilisés pour orchestrer plusieurs tâches coopératives.
- `Clients` lit le fichier et restitue chaque commande au bon moment (`await asyncio.sleep`).
- `Pic` : post‑it (LIFO logique via les méthodes `embrocher`/`liberer`) ; `Bar` : file de commandes prêtes (`recevoir`/`evacuer`).
- `Bariste` prépare les commandes et peut servir directement (dépannage) si besoin.
- `Serveur` exécute des boucles concurrentes pour prendre les commandes et servir celles du `Bar`.
- `productivity` : multiplicateur appliqué aux `await asyncio.sleep(...)` pour simuler vitesse différente des employés (par ex. `alice` 0.9, `marc` 1.2).

Debug rapide
- Ouvrez `borabora.log` après exécution pour lire les traces.
- Pour plus de détails activez `verbose=True` lors de la création des objets dans `main_async()`.
- Pour expérimenter la vitesse, changez les valeurs `productivity` dans `main_async()` et relancez.


