import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical
import argparse
import os
import csv
import json
from datetime import datetime
from torch.utils.tensorboard import SummaryWriter

class PolicyNetwork(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        super().__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.action_head = nn.Linear(hidden_dim, action_dim)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        logits = self.action_head(x)
        return logits

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
                 delta_kl=0.01, K=10, batch_size=64,
                 lr_actor=3e-4, lr_critic=3e-4, device="cpu"):
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

        self.beta = 1.0  # pénalité KL initiale

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

    def kl_mean(self, old_policy, states, grad_on_new_policy=False):
        if grad_on_new_policy:
            # Keep old policy fixed while allowing gradients on current policy.
            logits_old = old_policy(states).detach()
            logits_new = self.policy(states)
            dist_old = Categorical(logits=logits_old)
            dist_new = Categorical(logits=logits_new)
            kl = torch.distributions.kl_divergence(dist_old, dist_new)
            return kl.mean()

        with torch.no_grad():
            logits_old = old_policy(states)
            logits_new = self.policy(states)
            dist_old = Categorical(logits=logits_old)
            dist_new = Categorical(logits=logits_new)
            kl = torch.distributions.kl_divergence(dist_old, dist_new)
            return kl.mean()

    def train(self, num_iters=500, steps_per_iter=2000, log_interval=10, writer=None):
        rewards_history = []
        kl_history = []
        beta_history = []
        for it in range(num_iters):
            (states, actions, rewards, next_states, dones), ep_reward = \
                self.collect_trajectories(steps_per_iter)
            rewards_history.append(float(ep_reward))

            advantages, returns = self.compute_gae(states, rewards, next_states, dones)

            # copie figée π_{θ_k}
            old_policy = PolicyNetwork(
                states.shape[1],
                self.env.action_space.n
            ).to(self.device)
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

                d_kl = self.kl_mean(old_policy, b_states, grad_on_new_policy=True)

                policy_loss = -(L_theta_k - self.beta * d_kl)

                self.opt_policy.zero_grad()
                policy_loss.backward()
                self.opt_policy.step()

                # critic
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

            kl_history.append(float(d_kl_final.item()))
            beta_history.append(float(self.beta))

            if writer is not None:
                writer.add_scalar("Train/Reward", ep_reward, it + 1)
                writer.add_scalar("Train/KL", d_kl_final.item(), it + 1)
                writer.add_scalar("Train/Beta", self.beta, it + 1)
                # Comparison-friendly metrics directly visible in TensorBoard.
                writer.add_scalar("Compare/Reward_Last10", float(np.mean(rewards_history[-10:])), it + 1)
                writer.add_scalar("Compare/Reward_Last100", float(np.mean(rewards_history[-100:])), it + 1)
                writer.add_scalar("Compare/Best_Reward", float(max(rewards_history)), it + 1)

            if (it + 1) % log_interval == 0:
                print(f"[Iter {it+1}] R={ep_reward:.1f} KL={d_kl_final.item():.5f} beta={self.beta:.4f}")

        if writer is not None:
            writer.close()

        final_reward = rewards_history[-1] if rewards_history else 0.0
        best_reward = max(rewards_history) if rewards_history else 0.0
        avg_reward_last_10 = float(np.mean(rewards_history[-10:])) if rewards_history else 0.0
        avg_reward_last_100 = float(np.mean(rewards_history[-100:])) if rewards_history else 0.0
        avg_kl_last_10 = float(np.mean(kl_history[-10:])) if kl_history else 0.0

        return {
            "reward_history": rewards_history,
            "kl_history": kl_history,
            "beta_history": beta_history,
            "final_reward": float(final_reward),
            "best_reward": float(best_reward),
            "avg_reward_last_10": avg_reward_last_10,
            "avg_reward_last_100": avg_reward_last_100,
            "avg_kl_last_10": avg_kl_last_10,
            "final_beta": float(self.beta),
        }


def main():
    parser = argparse.ArgumentParser(description="Train PPO-AdaptiveKL on a Gymnasium environment")
    parser.add_argument("--env", type=str, default="CartPole-v1", help="Environment id, e.g. CartPole-v1")
    parser.add_argument("--episodes", type=int, default=500, help="Number of training iterations")
    parser.add_argument("--steps-per-iter", type=int, default=2000, help="Environment steps collected per iteration")
    parser.add_argument("--device", type=str, default="cpu", help="Torch device (cpu or cuda)")
    parser.add_argument("--log-interval", type=int, default=10, help="Print metrics every N iterations")
    args = parser.parse_args()

    if args.env.startswith("gridworld"):
        # Register custom environment before gym.make.
        import gridworld  # noqa: F401

    env = gym.make(args.env)

    # TensorBoard run name: PPO_KL_CartPole-v1_15-03-2026-14H30-00S
    timestamp = datetime.now().strftime("%d-%m-%Y-%HH%M-%SS")
    env_tag = args.env.replace("/", "-")
    run_name = f"PPO_KL_{env_tag}_{timestamp}"
    log_dir = os.path.join("XP", "PPO_KL", run_name)
    os.makedirs(log_dir, exist_ok=True)
    writer = SummaryWriter(log_dir=log_dir)
    print(f"[INFO] TensorBoard logs -> {log_dir}")

    agent = PPOAdaptiveKL(env,
                          gamma=0.999,
                          gae_lambda=0.95,
                          delta_kl=0.01,
                          K=10,
                          batch_size=64,
                          lr_actor=3e-4,
                          lr_critic=3e-4,
                          device=args.device)
    print(f"[INFO] PPO-AdaptiveKL start | env={args.env} | iters={args.episodes} | steps/iter={args.steps_per_iter} | device={args.device}")
    results = agent.train(
        num_iters=args.episodes,
        steps_per_iter=args.steps_per_iter,
        log_interval=args.log_interval,
        writer=writer,
    )

    summary = {
        "run_name": run_name,
        "env": args.env,
        "episodes": args.episodes,
        "steps_per_iter": args.steps_per_iter,
        "device": args.device,
        "gamma": 0.999,
        "gae_lambda": 0.95,
        "delta_kl": 0.01,
        "K": 10,
        "batch_size": 64,
        "lr_actor": 3e-4,
        "lr_critic": 3e-4,
        "final_reward": results["final_reward"],
        "best_reward": results["best_reward"],
        "avg_reward_last_10": results["avg_reward_last_10"],
        "avg_reward_last_100": results["avg_reward_last_100"],
        "avg_kl_last_10": results["avg_kl_last_10"],
        "final_beta": results["final_beta"],
    }

    summary_path = os.path.join(log_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    history_path = os.path.join(log_dir, "history.csv")
    with open(history_path, "w", newline="", encoding="utf-8") as f:
        writer_csv = csv.writer(f)
        writer_csv.writerow(["iter", "reward", "kl", "beta"])
        for i, (reward, kl, beta) in enumerate(
            zip(results["reward_history"], results["kl_history"], results["beta_history"]),
            start=1,
        ):
            writer_csv.writerow([i, reward, kl, beta])

    # HParams tab support in TensorBoard for run-to-run comparison.
    hparams = {
        "env": args.env,
        "episodes": args.episodes,
        "steps_per_iter": args.steps_per_iter,
        "gamma": 0.999,
        "gae_lambda": 0.95,
        "delta_kl": 0.01,
        "K": 10,
        "batch_size": 64,
        "lr_actor": 3e-4,
        "lr_critic": 3e-4,
    }
    hparam_metrics = {
        "hparam/final_reward": summary["final_reward"],
        "hparam/best_reward": summary["best_reward"],
        "hparam/avg_reward_last_10": summary["avg_reward_last_10"],
        "hparam/avg_reward_last_100": summary["avg_reward_last_100"],
        "hparam/avg_kl_last_10": summary["avg_kl_last_10"],
        "hparam/final_beta": summary["final_beta"],
    }
    writer = SummaryWriter(log_dir=log_dir)
    writer.add_hparams(hparams, hparam_metrics)
    writer.close()

    print("\n[RESULT] Resume final:")
    print(f"  run_name           : {run_name}")
    print(f"  final_reward       : {summary['final_reward']:.2f}")
    print(f"  best_reward        : {summary['best_reward']:.2f}")
    print(f"  avg_reward_last_10 : {summary['avg_reward_last_10']:.2f}")
    print(f"  avg_reward_last_100: {summary['avg_reward_last_100']:.2f}")
    print(f"  avg_kl_last_10     : {summary['avg_kl_last_10']:.6f}")
    print(f"  final_beta         : {summary['final_beta']:.6f}")
    print(f"  summary.json       : {summary_path}")
    print(f"  history.csv        : {history_path}")

if __name__ == "__main__":
    main()
