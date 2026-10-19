#!/usr/bin/env python3
"""PPO V4 GridWorld: LR=3e-4, gamma=0.95, batch_size=64"""
import numpy as np
import torch
import torch.nn as nn
from gridworld import gridworld_env

class PolicyNetwork(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        super().__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)

class ValueNetwork(nn.Module):
    def __init__(self, state_dim, hidden_dim=128):
        super().__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)

def main():
    gridworld_env.GridworldEnv.plan = 'data/gridworldPlans/plan1.txt'
    gridworld_env.GridworldEnv.rewards = {0: -0.001, 3: 1, 4: 1, 5: -1, 6: -1}
    env = gridworld_env.GridworldEnv()
    state_dim = np.prod(env.observation_space.shape)
    policy = PolicyNetwork(state_dim, env.action_space.n)
    value = ValueNetwork(state_dim)
    opt_p = torch.optim.Adam(policy.parameters(), lr=3e-4)
    opt_v = torch.optim.Adam(value.parameters(), lr=3e-4)
    print("Variant 4 GridWorld - LR=3e-4, gamma=0.95, batch_size=64")

if __name__ == "__main__":
    main()
