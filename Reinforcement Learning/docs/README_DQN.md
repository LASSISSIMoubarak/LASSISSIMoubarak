# DQN Implementation - TP Master M2 DataScience

## 📋 Overview

Complete implementation of Deep Q-Network (DQN) algorithm for the TP assignment, supporting:
- **Standard DQN** with Experience Replay
- **Prioritized Experience Replay** (PER) with SumTree
- **Double DQN** variant
- **Target Network** with configurable update frequency

## ✅ Components Implemented

### Files
- **`src/dqn.py`** - Main DQN agent class with training loop
- **`src/memory.py`** - Replay buffer with prioritized sampling using SumTree
- **`src/core.py`** - Neural network definitions (NN class)
- **`configs/`** - Training configurations for each environment

### Key Features
- ✅ Epsilon-greedy exploration with configurable decay
- ✅ Huber loss (SmoothL1Loss) for stable Q-learning
- ✅ Separate target and main Q-networks
- ✅ Double Q-learning for action selection bias reduction
- ✅ Prioritized Experience Replay with importance sampling
- ✅ TensorBoard integration for monitoring
- ✅ Model checkpointing (save/load)

## 🚀 Quick Start

### Run Default Training (CartPole)
```bash
python src/dqn.py
```

### Run on Other Environments
**GridWorld:**
```python
python src/dqn.py --config configs/config_dqn_gridworld.yaml
```

**LunarLander:**
```python
python src/dqn.py --config configs/config_dqn_lunar.yaml
```

### Monitor Training
TensorBoard launches automatically. View at: **http://localhost:6006/**

Tracked metrics:
- `reward` - Episode cumulative reward
- `qvalue_mean` - Mean Q-value estimates
- `epsilon` - Exploration parameter
- `rewardTest` - Validation episode rewards

## ⚙️ Configuration

### CartPole (Default) - `configs/config_dqn_cartpole.yaml`
```yaml
env: CartPole-v1
nbEpisodes: 1000000
explo: 0.1              # Initial epsilon
edecay: 0.99999         # Epsilon decay per step
gamma: 0.999            # Discount factor
batchsize: 100
capacity: 10000         # Replay buffer size
lr: 0.003               # Learning rate
ctarget: 1000           # Target network update frequency
prioritizedReplay: true # Enable PER
doubleQ: false          # Standard DQN
maxLengthTrain: 300     # Max episode length (training)
maxLengthTest: 500      # Max episode length (testing)
```

### Hyperparameter Tuning
Modify config files to experiment:
- **Exploration**: `explo`, `edecay`, `freqOptim`
- **Learning**: `lr`, `gamma`, `batchsize`
- **Capacity**: `capacity` (replay buffer size)
- **Updates**: `ctarget` (target network update interval)
- **Variants**: `doubleQ`, `prioritizedReplay`

## 📊 Expected Results

### CartPole
- Converges to max reward (~500) within 2000 episodes
- Final training rewards stabilize at 300-500
- Test rewards typically 400-500 after 500+ episodes

### GridWorld
- Learns to navigate mazes progressively
- Reward accumulation improves with training
- Optimal rewards depend on map complexity

### LunarLander
- Reaches successful landing (positive reward) after ~1000+ episodes
- Requires larger buffer (capacity: 100000)
- Best results with Double DQN + PER

## 🔧 Advanced Usage

### Enabling Double DQN
In config file:
```yaml
doubleQ: true
```
Reduces overestimation of Q-values by using main network for action selection and target network for evaluation.

### Disabling Prioritized Replay
In config file:
```yaml
prioritizedReplay: false
```
Uses uniform random sampling instead of priority-weighted sampling.

### Loading Checkpoints
Set `fromFile` in config:
```yaml
fromFile: ./XP/CartPole-v1/DQN_<timestamp>/save_5000
```

## 📈 Monitoring

### Training Output Format
```
  <episode> | rsum=<reward> | <steps> actions | eps=<epsilon> | buffer=<size>
```

Example:
```
   50 | rsum= 245.3 | 245 actions | eps=0.09950 | buffer= 5113
```

### TensorBoard Metrics
- Smooth curves indicate stable learning
- Q-value growth suggests improving estimates
- Epsilon decay should follow configured schedule

## 🐛 Troubleshooting

### Error: "cannot find 'NothingToDo' in module '__main__'"
**Cause**: YAML loader can't find feature extractors
**Fix**: Feature extractors must be imported in dqn.py (already done)

### Slow Training
**Possible causes**:
- Large batch size (`batchsize`)
- Slow environment rendering
- GPU not available (if `device >= 0`)

**Solutions**:
- Increase `freqOptim` (update less often)
- Set `device: -1` to use CPU if GPU unavailable
- Reduce `nbEpisodes` for testing

### Memory Issues
- Reduce `capacity` parameter
- Decrease `batchsize`
- Check available RAM

## 📚 Algorithm Details

### DQN Update Rule
```
Q(s,a) <- Q(s,a) + lr * (r + γ * max_a' Q_target(s',a') - Q(s,a))
```

### Double DQN Variant
```
max_a' Q_target(s',a') <- Q_target(s', argmax_a' Q_main(s',a'))
```
Reduces overestimation bias.

### Prioritized Experience Replay
Samples transitions proportional to TD-error magnitude, weighted by importance sampling for unbiased estimates.

## 📝 Notes

- All updates happen synchronously (full batch) every `freqOptim` events when episode ends
- Target network updated every `ctarget` learning updates
- Episodes may be truncated at `maxLengthTrain` (flag `done=False` to avoid artificial terminal)
- Test episodes use `maxLengthTest` and no exploration (`epsilon=0`)

## 🎯 Deliverables for TP

For the assignment, produce:
1. ✅ Learning curves comparing:
   - DQN vs Random Agent
   - With/without Experience Replay
   - With/without Target Network
   - Standard vs Prioritized Replay
   - Standard vs Double DQN
2. ✅ Test performance scores
3. ✅ Mean Q-value evolution plots
4. ✅ Implementation code (this repo)

---

**Status**: ✅ Complete and tested
**Last Modified**: March 13, 2026
