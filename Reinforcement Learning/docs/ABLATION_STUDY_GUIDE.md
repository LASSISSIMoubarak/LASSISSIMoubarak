# 📊 DQN Ablation Study - Guide pour le Rapport

## 📁 Structure des résultats

Après l'entraînement, les résultats seront organisés dans `./XP/` comme suit :

```
XP/
├── CartPole-v1/
│   ├── runs/Baseline_<timestamp>/           [Baseline]
│   ├── runs/ReplayOnly_<timestamp>/         [Replay seul]
│   ├── runs/TargetOnly_<timestamp>/         [Target Network seul]
│   ├── runs/Standard_<timestamp>/           [Replay + Target]
│   └── runs/BONUS_DoublePrioritized_<timestamp>/  [Double DQN + PER]
├── GridWorld-v0/
│   ├── runs/Baseline_<timestamp>/
│   ├── runs/ReplayOnly_<timestamp>/
│   ├── runs/TargetOnly_<timestamp>/
│   ├── runs/Standard_<timestamp>/
│   └── runs/BONUS_DoublePrioritized_<timestamp>/
└── LunarLander-v2/
    ├── runs/Baseline_<timestamp>/
    ├── runs/ReplayOnly_<timestamp>/
    ├── runs/TargetOnly_<timestamp>/
    ├── runs/Standard_<timestamp>/
    └── runs/BONUS_DoublePrioritized_<timestamp>/
```

## 🚀 Comment lancer l'étude complète

Lancer une configuration à la fois depuis la racine du projet. Les entraînements
longs ne sont pas lancés automatiquement et les scripts historiques de
comparaison mentionnés ci-dessous ne sont pas présents dans cette version.

**Exemple :**
```bash
python src/dqn.py --config configs/config_dqn_cartpole_baseline.yaml
```

Remplace le nom du fichier par la variante voulue, par exemple
`config_dqn_gridworld_standard.yaml` ou `config_dqn_lunar_bonus.yaml`.
Les fichiers YAML disponibles sont dans `configs/`.

**Un lancement PPO-AdaptiveKL :**
```bash
python src/ppo_adaptive_kl.py --env CartPole-v1 --episodes 500
```

## 📈 Métriques à extraire pour le rapport

### Courbes principales (TensorBoard)

Pour chaque jeu et chaque variante, extraire :

| Métrique | Description | Section rapport |
|----------|-------------|-----------------|
| `reward` | Récompense cumulative par épisode (entraînement) | Convergence |
| `rewardTest` | Récompense de test (tous les freqTest épisodes) | Performance |
| `qvalue_mean` | Estimation Q-value moyenne | Stabilité |
| `epsilon` | Taux d'exploration (decay) | Exploration |
| `tdError_mean` | Erreur TD (stabilité d'apprentissage) | Stabilité |

### Scores finaux à calculer

Pour chaque variante (moyennes des 100 derniers épisodes) :
- **Reward moyen** : (voir `rewardTest`)
- **Reward max** : meilleur score atteint
- **Stabilité** : écart-type des 100 derniers tests
- **Temps de convergence** : quand reward > seuil (par jeu)

## 🎯 Variantes expliquées

| Variante | Composants | Objectif |
|----------|-----------|----------|
| **Baseline** | ❌ No replay, ❌ No target | Mesurer importance combinée |
| **ReplayOnly** | ✅ Replay, ❌ No target | Mesurer impact replay seul |
| **TargetOnly** | ❌ No replay, ✅ Target | Mesurer impact target seul |
| **Standard** | ✅ Replay, ✅ Target | DQN classique (Mnih et al. 2015) |
| **BONUS** | ✅ Double DQN, ✅ PER, ✅ Target | État de l'art |

## 📊 Noms pour le rapport

Utiliser ces noms exactement pour la clarté :

```python
VARIANT_NAMES_REPORT = {
    "Baseline": "Q-learning (baseline)",
    "ReplayOnly": "DQN + Experience Replay",
    "TargetOnly": "DQN + Target Network",
    "Standard": "DQN Standard (Replay + Target)",
    "BONUS_DoublePrioritized": "Advanced DQN (Double + PER)"
}
```

## 📋 Checklist pour le rapport

- [ ] 5 courbes de `reward` par jeu (convergence)
- [ ] 5 courbes de `rewardTest` par jeu (performance)
- [ ] Tableau comparatif : scores finaux par variante
- [ ] Analyse de la contribution de Replay vs Target Network
- [ ] Analyse du Double DQN + PER vs Standard
- [ ] Graphique : Temps de convergence vs complexité tâche
- [ ] Graphique : Stabilité (variance) par classe de tâche

## 🔍 TensorBoard - Commandes utiles

**Lancer le serveur :**
```bash
tensorboard --logdir=./XP/
```
Puis ouvrir : http://localhost:6006/

**Comparer les 5 variants d'un même jeu :**
- Aller dans l'onglet "SCALARS"
- Sélectionner la métrique (ex: reward)
- Cocher tous les runs du même jeu
- Exporter en PNG pour le rapport

## 📝 Section "Ablation Study" type

```markdown
### Résultats Ablation Study

Nous avons mesuré l'impact de chaque composant DQN :

#### CartPole (tâche simple)
- Baseline:           reward = XXX
- + Replay Buffer:    reward = XXX (+XX%)
- + Target Network:   reward = XXX (+XX%)
- Replay + Target:    reward = XXX (+XX%)
- Double DQN + PER:   reward = XXX (+XX%)

#### GridWorld (navigation)
[similaire]

#### LunarLander (tâche complexe)
[similaire]

**Conclusion :** [analyse des résultats]
```

## 🎓 Points importants à documenter

1. **Hyperparamètres constants** across all variants:
   - Learning rate: 0.0001
   - Discount factor (gamma): 0.99
   - Batch size: 100
   - Buffer capacities: variant by env

2. **Hyperparamètres variables**:
   - `ctarget`: 999999999 (disabled) ou 1000 (active)
   - `prioritizedReplay`: false ou true
   - `doubleQ`: false ou true

3. **Contrôles scientifiques**:
   - Même seed pour toutes les variants (seed: 5)
   - Menus `nbTest: 5` pour stabilité statistique
   - Même nombre d'épisodes (1000000)
   - Même architecture neuronale

---

**Questions pour le rapport ?**
Voir les configs dans `./configs/config_dqn_*_*.yaml` pour tous les détails.
