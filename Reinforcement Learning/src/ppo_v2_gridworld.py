#!/usr/bin/env python3
"""
PPO-AdaptiveKL Variant 2 - GridWorld-v0
Hyperparamètres: LR=5e-4, gamma 0.99, batch_size 32
"""
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical
from gridworld import gridworld_env

class PolicyNetwork(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        super().__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.action_head = nn.Linear(hidden_dim, action_dim)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.action_head(x)

    def get_action(self, state):
        logits = self.forward(state)
        dist = Categorical(logits=logits)
        return dist.sample(), dist.log_prob(dist.sample())

class ValueNetwork(nn.Module):
    def __init__(self, state_dim, hidden_dim=128):
        super().__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.v = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.v(x)

class PPOAdaptiveKL:
    def __init__(self, env, gamma=0.99, batch_size=32, lr_actor=5e-4, **kwargs):
        self.env = env
        self.gamma = gamma
        self.batch_size = batch_size
        state_dim = np.prod(env.observation_space.shape)
        action_dim = env.action_space.n
        self.policy = PolicyNetwork(state_dim, action_dim)
        self.value = ValueNetwork(state_dim)
        self.opt_policy = torch.optim.Adam(self.policy.parameters(), lr=lr_actor)
        self.opt_value = torch.optim.Adam(self.value.parameters(), lr=lr_actor)
        self.beta = 1.0

    def collect_trajectories(self, max_steps):
        states, actions, rewards, next_states, dones = [], [], [], [], []
        state, _ = self.env.reset()
        total_reward = 0

        for _ in range(max_steps):
            s = torch.FloatTensor(state.flatten()).unsqueeze(0)
            action, _ = self.policy.get_action(s)
            next_state, reward, terminated, truncated, _ = self.env.step(action.item())
            done = terminated or truncated
            states.append(state.flatten())
            actions.append(action.item())
            rewards.append(reward)
            next_states.append(next_state.flatten())
            dones.append(float(done))
            total_reward += reward
            state = next_state
            if done:
                state, _ = self.env.reset()

        return (torch.FloatTensor(np.array(states)), torch.LongTensor(actions),
                torch.FloatTensor(rewards), torch.FloatTensor(np.array(next_states)),
                torch.FloatTensor(dones)), total_reward

    def compute_gae(self, states, rewards, next_states, dones):
        with torch.no_grad():
            values = self.value(states).squeeze(-1)
            next_values = self.value(next_states).squeeze(-1)
        deltas = rewards + self.gamma * next_values * (1 - dones) - values
        advantages = torch.zeros_like(rewards)
        gae = 0.0
        for t in reversed(range(len(rewards))):
            gae = deltas[t] + self.gamma * 0.95 * (1 - dones[t]) * gae
            advantages[t] = gae
        return advantages, advantages + values

    def train(self, num_iters=500, steps_per_iter=500):
        print(f"\nVariant 2 GridWorld - LR=5e-4, gamma=0.99, batch_size=32")
        for it in range(num_iters):
            (states, actions, rewards, next_states, dones), ep_reward = self.collect_trajectories(steps_per_iter)
            advantages, returns = self.compute_gae(states, rewards, next_states, dones)
            if (it + 1) % 50 == 0:
                print(f"[Iter {it+1}] R={ep_reward:.1f}")

def main():
    gridworld_env.GridworldEnv.plan = 'data/gridworldPlans/plan1.txt'
    gridworld_env.GridworldEnv.rewards = {0: -0.001, 3: 1, 4: 1, 5: -1, 6: -1}
    env = gridworld_env.GridworldEnv()
    agent = PPOAdaptiveKL(env, gamma=0.99, batch_size=32, lr_actor=5e-4)
    agent.train(num_iters=500, steps_per_iter=500)

if __name__ == "__main__":
    main()
