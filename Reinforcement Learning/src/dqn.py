import argparse
import sys
from pathlib import Path
import matplotlib
matplotlib.use("TkAgg")
import torch
import torch.nn as nn
import numpy as np
from utils import *
from core import *
from memory import Memory
from torch.utils.tensorboard import SummaryWriter
from matplotlib import pyplot as plt
import yaml
from datetime import datetime
from gridworld import gridworld_env
import os


class DQNAgent(object):
    """Deep Q-Network Agent Implementation"""

    def __init__(self, env, opt):
        self.opt = opt
        self.env = env
        self.action_space = env.action_space
        self.nA = self.action_space.n
        self.featureExtractor = opt.featExtractor(env)

        # Device configuration
        self.device = torch.device("cuda:" + str(opt.device) if opt.device >= 0 else "cpu")

        # Build Q-networks
        self.qnet = self._build_network().to(self.device)
        self.target_qnet = self._build_network().to(self.device)
        self.target_qnet.load_state_dict(self.qnet.state_dict())
        self.target_qnet.eval()  # Target network in eval mode

        # Optimizer and loss
        self.optimizer = opt.optimizer(self.qnet.parameters(), lr=opt.lr)
        # Handle vloss if not defined in config
        if hasattr(opt, 'vloss') and opt.vloss is not None:
            self.loss_fn = opt.vloss(reduction='none')
        else:
            self.loss_fn = nn.SmoothL1Loss(reduction='none')

        # Replay buffer
        self.memory = Memory(opt.capacity, prior=opt.prioritizedReplay)

        # Hyperparameters
        self.gamma = opt.gamma
        self.epsilon = opt.explo
        self.epsilon_decay = opt.edecay
        self.epsilon_min = 0.01
        self.batchsize = opt.batchsize
        self.freqOptim = opt.freqOptim
        self.ctarget = opt.ctarget
        self.doubleQ = getattr(opt, "doubleQ", False)

        # Counters
        self.test = False
        self.nbEvents = 0
        self.nUpdates = 0
        self.timeToOPtim = False
        self.lastTransition = None
        self.qvalue_mean = 0.0

        if opt.fromFile is not None:
            self.load(opt.fromFile)

    def _build_network(self):
        """Build the Q-network using core.NN class"""
        # Use the NN class from core.py for consistency
        return NN(
            inSize=self.featureExtractor.outSize,
            outSize=self.nA,
            layers=self.opt.layers,
            finalActivation=None,
            activation=torch.tanh,
            dropout=0.0
        )

    def act(self, obs):
        """Epsilon-greedy action selection"""
        if self.test or (np.random.rand() > self.epsilon):
            with torch.no_grad():
                obs_tensor = torch.FloatTensor(obs).to(self.device)
                if obs_tensor.dim() == 1:
                    obs_tensor = obs_tensor.unsqueeze(0)
                q_values = self.qnet(obs_tensor)
                action = q_values.argmax(dim=1).item()
            return action
        else:
            return self.action_space.sample()

    def store(self, ob, action, new_ob, reward, done, it):
        """Store transition in replay buffer"""
        if self.test:
            return

        # Handle artificial episode termination
        if it == self.opt.maxLengthTrain:
            done = False

        tr = (ob, action, reward, new_ob, done)
        self.lastTransition = tr
        self.memory.store(tr)

    def learn(self):
        """Perform DQN learning update"""
        if self.test:
            return

        # Check if we have enough samples
        if self.memory.nentities < self.batchsize:
            return

        # Sample from replay buffer
        if self.opt.prioritizedReplay:
            batch_indices, weights_array, batch_transitions = self.memory.sample(self.batchsize)
            weights_batch = torch.FloatTensor(weights_array.flatten()).to(self.device)
        else:
            batch_indices, _, batch_transitions = self.memory.sample(self.batchsize)
            weights_batch = torch.ones(self.batchsize).to(self.device)

        # Prepare batch tensors
        obs_batch = torch.FloatTensor([np.array(t[0]).flatten() for t in batch_transitions]).to(self.device)
        action_batch = torch.LongTensor([t[1] for t in batch_transitions]).to(self.device)
        reward_batch = torch.FloatTensor([t[2] for t in batch_transitions]).to(self.device)
        next_obs_batch = torch.FloatTensor([np.array(t[3]).flatten() for t in batch_transitions]).to(self.device)
        done_batch = torch.FloatTensor([t[4] for t in batch_transitions]).to(self.device)

        # Compute target Q-values
        with torch.no_grad():
            if self.doubleQ:
                # Double DQN: use main network to select action
                next_actions = self.qnet(next_obs_batch).argmax(dim=1)
                next_q_values = self.target_qnet(next_obs_batch).gather(1, next_actions.unsqueeze(1)).squeeze(1)
            else:
                # Standard DQN: use target network to select and evaluate
                next_q_values = self.target_qnet(next_obs_batch).max(dim=1)[0]

            target_q_values = reward_batch + self.gamma * next_q_values * (1 - done_batch)

        # Compute current Q-values
        q_values_all = self.qnet(obs_batch)
        q_values = q_values_all.gather(1, action_batch.unsqueeze(1)).squeeze(1)

        # Compute TD error
        td_error = target_q_values - q_values

        # Weighted Huber loss
        per_sample_loss = self.loss_fn(q_values, target_q_values)
        loss = (weights_batch * per_sample_loss).mean()

        # Record mean Q-value
        self.qvalue_mean = q_values.detach().mean().item()

        # Backpropagation
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.qnet.parameters(), 1.0)
        self.optimizer.step()

        # Update priorities if using prioritized replay
        if self.opt.prioritizedReplay:
            self.memory.update(batch_indices, np.abs(td_error.detach().cpu().numpy()))

        # Update target network
        self.nUpdates += 1
        if self.nUpdates % self.ctarget == 0:
            self.target_qnet.load_state_dict(self.qnet.state_dict())

    def timeToLearn(self, done):
        """Check if it's time to perform learning"""
        if self.test:
            return False

        self.nbEvents += 1
        if self.nbEvents % self.freqOptim == 0:
            self.timeToOPtim = True

        if done and self.timeToOPtim:
            self.timeToOPtim = False
            return True
        return False

    def save(self, outputDir):
        """Save model checkpoint"""
        os.makedirs(outputDir, exist_ok=True)
        torch.save({
            'qnet': self.qnet.state_dict(),
            'target_qnet': self.target_qnet.state_dict(),
            'epsilon': self.epsilon,
            'nUpdates': self.nUpdates,
        }, os.path.join(outputDir, "dqn_model.pt"))

    def load(self, inputDir):
        """Load model checkpoint"""
        checkpoint = torch.load(os.path.join(inputDir, "dqn_model.pt"), map_location=self.device)
        self.qnet.load_state_dict(checkpoint['qnet'])
        self.target_qnet.load_state_dict(checkpoint['target_qnet'])
        self.epsilon = checkpoint['epsilon']
        self.nUpdates = checkpoint['nUpdates']


if __name__ == '__main__':
    # Support des arguments de ligne de commande
    parser = argparse.ArgumentParser(description='DQN Agent Training')
    parser.add_argument('--config', type=str,
                        default=str(Path(__file__).resolve().parents[1] / 'configs' / 'config_dqn_cartpole.yaml'),
                        help='Path to config file')
    parser.add_argument('--env', type=str,
                        default='CartPole',
                        help='Environment name (CartPole, GridWorld, LunarLander)')
    args = parser.parse_args()

    # Extraire le nom de la variante du chemin du config
    variant_name = Path(args.config).stem.replace('config_dqn_', '')

    # Formater le nom pour TensorBoard (ex: cartpole_baseline -> Baseline)
    parts = variant_name.split('_')
    if len(parts) > 1:
        variant_display = '_'.join(parts[1:]).replace('_', ' ').title().replace(' ', '')
    else:
        variant_display = 'Standard'

    env, config, outdir, logger = init(args.config, args.env)

    # Modifier le nom du dossier de sortie pour inclure la variante
    if "XP" in outdir:
        outdir_path = Path(outdir)
        env_folder = outdir_path.parent.name  # CartPole-v1 ou GridWorld-v0
        timestamp = outdir_path.name.split('_')[-1]  # Récupère le timestamp

        # Créer nouveau nom avec variante
        new_outdir = str(outdir_path.parent / f"{variant_display}_{env_folder}_{timestamp}")

        # Créer le nouveau dossier s'il n'existe pas
        os.makedirs(new_outdir, exist_ok=True)

        # Mettre à jour logger et outdir
        outdir = new_outdir
        logger = SummaryWriter(outdir)

    freqTest = config["freqTest"]
    freqSave = config["freqSave"]
    nbTest = config["nbTest"]
    episode_count = config["nbEpisodes"]

    agent = DQNAgent(env, config)

    rsum = 0
    mean = 0
    itest = 0
    reward = 0
    done = False
    test_episode_count = 0

    for i in range(episode_count):
        checkConfUpdate(outdir, config)

        rsum = 0
        agent.nbEvents = 0

        ob, _ = env.reset()

        # Mode test
        if i % freqTest == 0 and i > 0:
            print("Test time! ")
            mean = 0
            agent.test = True
            test_episode_count = 0

        if agent.test:
            test_episode_count += 1
            if test_episode_count >= nbTest:
                print("End of test, mean reward=", mean / nbTest)
                itest += 1
                logger.add_scalar("rewardTest", mean / nbTest, itest)
                agent.test = False

        # Sauvegarde
        if i % freqSave == 0:
            agent.save(outdir + "/save_" + str(i))

        j = 0
        new_ob = agent.featureExtractor.getFeatures(ob)
        while True:
            ob = new_ob
            action = agent.act(ob)
            new_ob, reward, done, _, _ = env.step(action)
            new_ob = agent.featureExtractor.getFeatures(new_ob)

            j += 1

            # Si on a atteint la longueur max définie dans le fichier de config
            if ((config["maxLengthTrain"] > 0) and (not agent.test) and (j == config["maxLengthTrain"])) or ( (agent.test) and (config["maxLengthTest"] > 0) and (j == config["maxLengthTest"])):
                done = True

            agent.store(ob, action, new_ob, reward, done, j)
            rsum += reward

            if agent.timeToLearn(done):
                agent.learn()
                # Log Q-value mean during training
                if agent.qvalue_mean != 0:
                    logger.add_scalar("qvalue_mean", agent.qvalue_mean, agent.nbEvents)

            if done:
                epsilon_val = agent.epsilon
                agent.epsilon = max(agent.epsilon_min, agent.epsilon * agent.epsilon_decay)

                print(f"{i:4d} | rsum={rsum:7.1f} | {j:3d} actions | eps={epsilon_val:.5f} | buffer={agent.memory.nentities:5d}")
                logger.add_scalar("reward", rsum, i)
                logger.add_scalar("epsilon", epsilon_val, i)
                mean += rsum
                rsum = 0

                break

    env.close()
