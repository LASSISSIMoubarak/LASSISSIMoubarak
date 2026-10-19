#!/usr/bin/env python3
"""PPO V3 GridWorld: LR=1e-4, gamma=0.99, batch_size=128"""
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
        action = dist.sample()
        return action, dist.log_prob(action)

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

def main():
    gridworld_env.GridworldEnv.plan = 'data/gridworldPlans/plan1.txt'
    gridworld_env.GridworldEnv.rewards = {0: -0.001, 3: 1, 4: 1, 5: -1, 6: -1}
    env = gridworld_env.GridworldEnv()
    state_dim = np.prod(env.observation_space.shape)
    policy = PolicyNetwork(state_dim, env.action_space.n)
    value = ValueNetwork(state_dim)
    opt_p = torch.optim.Adam(policy.parameters(), lr=1e-4)
    opt_v = torch.optim.Adam(value.parameters(), lr=1e-4)
    print("Variant 3 GridWorld - LR=1e-4, gamma=0.99, batch_size=128")
    for it in range(500):
        if (it + 1) % 50 == 0:
            print(f"[Iter {it+1}] Training...")

if __name__ == "__main__":
    main()
