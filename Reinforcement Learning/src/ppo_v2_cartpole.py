#!/usr/bin/env python3
"""
PPO-AdaptiveKL Variant 2 - CartPole-v1
Hyperparamètres: LR augmenté (5e-4), gamma 0.99, batch_size 32 (plus de mises à jour)
"""
import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical

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
        log_prob = dist.log_prob(action)
        return action, log_prob

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
    def __init__(self, env, gamma=0.99, gae_lambda=0.95,
                 delta_kl=0.01, K=10, batch_size=32,
                 lr_actor=5e-4, lr_critic=5e-4, device="cpu"):
        self.env = env
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.delta_kl = delta_kl
        self.K = K
        self.batch_size = batch_size
        self.device = device

        state_dim = env.observation_space.shape[0]
        action_dim = env.action_space.n

        self.policy = PolicyNetwork(state_dim, action_dim).to(device)
        self.value = ValueNetwork(state_dim).to(device)

        self.opt_policy = torch.optim.Adam(self.policy.parameters(), lr=lr_actor)
        self.opt_value = torch.optim.Adam(self.value.parameters(), lr=lr_critic)
        self.beta = 1.0

    def collect_trajectories(self, max_steps):
        states, actions, rewards, next_states, dones = [], [], [], [], []
        state, _ = self.env.reset()
        total_reward = 0

        for _ in range(max_steps):
            s = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            with torch.no_grad():
                action, _ = self.policy.get_action(s)

            a_env = action.item()
            next_state, reward, terminated, truncated, _ = self.env.step(a_env)
            done = terminated or truncated

            states.append(state)
            actions.append(a_env)
            rewards.append(reward)
            next_states.append(next_state)
            dones.append(float(done))

            total_reward += reward
            state = next_state
            if done:
                state, _ = self.env.reset()

        states = torch.FloatTensor(np.array(states)).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)

        return (states, actions, rewards, next_states, dones), total_reward

    def compute_gae(self, states, rewards, next_states, dones):
        with torch.no_grad():
            values = self.value(states).squeeze(-1)
            next_values = self.value(next_states).squeeze(-1)

        deltas = rewards + self.gamma * next_values * (1 - dones) - values
        advantages = torch.zeros_like(rewards)
        gae = 0.0
        for t in reversed(range(len(rewards))):
            gae = deltas[t] + self.gamma * self.gae_lambda * (1 - dones[t]) * gae
            advantages[t] = gae

        returns = advantages + values
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        return advantages, returns

    def kl_mean(self, old_policy, states):
        with torch.no_grad():
            logits_old = old_policy(states)
            logits_new = self.policy(states)
            dist_old = Categorical(logits=logits_old)
            dist_new = Categorical(logits=logits_new)
            kl = torch.distributions.kl_divergence(dist_old, dist_new)
        return kl.mean()

    def train(self, num_iters=500, steps_per_iter=2000):
        print(f"\nVariant 2 CartPole - LR=5e-4, gamma=0.99, batch_size=32")
        for it in range(num_iters):
            (states, actions, rewards, next_states, dones), ep_reward = \
                self.collect_trajectories(steps_per_iter)

            advantages, returns = self.compute_gae(states, rewards, next_states, dones)

            old_policy = PolicyNetwork(states.shape[1], self.env.action_space.n).to(self.device)
            old_policy.load_state_dict(self.policy.state_dict())
            old_policy.eval()

            N = states.size(0)
            for _ in range(self.K):
                idx = np.random.choice(N, size=min(self.batch_size, N), replace=True)
                b_states = states[idx]
                b_actions = actions[idx]
                b_adv = advantages[idx]
                b_returns = returns[idx]

                with torch.no_grad():
                    logits_old = old_policy(b_states)
                    dist_old = Categorical(logits=logits_old)
                    old_log_probs = dist_old.log_prob(b_actions)

                logits_new = self.policy(b_states)
                dist_new = Categorical(logits=logits_new)
                new_log_probs = dist_new.log_prob(b_actions)

                ratio = torch.exp(new_log_probs - old_log_probs)
                L_theta_k = (ratio * b_adv).mean()
                d_kl = self.kl_mean(old_policy, b_states)
                policy_loss = -(L_theta_k - self.beta * d_kl)

                self.opt_policy.zero_grad()
                policy_loss.backward()
                self.opt_policy.step()

                v_pred = self.value(b_states).squeeze(-1)
                v_loss = F.smooth_l1_loss(v_pred, b_returns)
                self.opt_value.zero_grad()
                v_loss.backward()
                self.opt_value.step()

            d_kl_final = self.kl_mean(old_policy, states)
            if d_kl_final >= 1.5 * self.delta_kl:
                self.beta *= 2.0
            elif d_kl_final <= self.delta_kl / 1.5:
                self.beta *= 0.5

            if (it + 1) % 50 == 0:
                print(f"[Iter {it+1}] R={ep_reward:.1f} KL={d_kl_final.item():.5f} beta={self.beta:.4f}")

def main():
    env = gym.make("CartPole-v1")
    agent = PPOAdaptiveKL(env, gamma=0.99, gae_lambda=0.95, delta_kl=0.01,
                         K=10, batch_size=32, lr_actor=5e-4, lr_critic=5e-4, device="cpu")
    agent.train(num_iters=500, steps_per_iter=2000)

if __name__ == "__main__":
    main()
