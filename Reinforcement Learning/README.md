# Apprentissage par renforcement : DQN et PPO

Projet d'étude d'algorithmes d'apprentissage par renforcement profond sur
CartPole et un environnement GridWorld personnalisé. Le dépôt contient aussi
des expériences PPO sur CartPole et GridWorld, ainsi que des configurations DQN
pour CartPole, GridWorld et LunarLander.

## Structure

```text
Reinforcement Learning/
├── configs/       Configurations YAML DQN et PPO
├── data/          Cartes texte du GridWorld
├── docs/          Guides d'utilisation et d'ablation
├── reports/       Sources LaTeX du rapport et de ses sections
├── src/           Agents, environnement GridWorld et scripts
├── XP/            Résultats locaux (ignorés par Git)
└── README.md
```

Les checkpoints, historiques TensorBoard et fichiers intermédiaires sous
`XP/` sont des résultats locaux et ne sont pas versionnés. Les environnements
Python virtuels ne sont pas inclus. Le sujet PDF du TP est conservé localement
et n'est pas publié avec les sources.

## Installation (Windows PowerShell)

Depuis ce dossier :

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Lancer DQN

Depuis la racine du projet :

```powershell
python src\dqn.py --config configs\config_dqn_cartpole.yaml
```

Autres configurations disponibles dans `configs/`, notamment pour GridWorld et
LunarLander. Les entraînements complets peuvent être longs ; vérifie les
paramètres `nbEpisodes`, `freqTest` et `freqSave` avant de lancer une expérience.

## Lancer PPO

Un script PPO CartPole :

```powershell
python src\ppo_v1_cartpole.py
```

Un script PPO GridWorld :

```powershell
python src\ppo_v1_gridworld.py
```

PPO-AdaptiveKL :

```powershell
python src\ppo_adaptive_kl.py --env CartPole-v1 --episodes 500
```

Les lanceurs `src\run_ppo_variants.py` et `src\run_ppo_adaptive_kl.py` exécutent
plusieurs entraînements et peuvent prendre longtemps.

## Consulter les résultats

Les entraînements enregistrent leurs résultats dans `XP/`. Pour visualiser les
scalaires TensorBoard :

```powershell
tensorboard --logdir XP
```

Pour comparer les résumés PPO-AdaptiveKL :

```powershell
python src\compare_ppo_runs.py
```

## Rapports

Les sources LaTeX sont dans `reports/`. Certaines sections comportent encore
des figures ou valeurs à compléter ; vérifie les placeholders et les résultats
expérimentaux avant de présenter le rapport comme final.
