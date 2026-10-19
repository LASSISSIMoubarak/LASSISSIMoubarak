import gymnasium as gym
from gridworld.gridworld_env import GridworldEnv

from gymnasium import register


print("Le module a été importé")

register(
    id='gridworld-v0',
    entry_point='gridworld:GridworldEnv',
)
