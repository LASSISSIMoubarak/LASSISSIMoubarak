import time
import subprocess
from collections import namedtuple,defaultdict
import logging
import json
import os
import yaml
import gymnasium as gym
import sys
import threading
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from torch.utils.tensorboard import SummaryWriter
import torch
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def loadTensorBoard(outdir):
    t = threading.Thread(target=launchTensorBoard, args=([outdir]))
    t.start()

def launchTensorBoard(tensorBoardPath):
    command = ["tensorboard", "--logdir", str(tensorBoardPath)]
    print("Starting TensorBoard for " + str(tensorBoardPath))
    try:
        subprocess.run(command, check=False, cwd=PROJECT_ROOT)
    except FileNotFoundError:
        executable_name = "tensorboard.exe" if os.name == "nt" else "tensorboard"
        executable = Path(sys.executable).parent / executable_name
        if not executable.is_file():
            raise
        subprocess.run([str(executable), "--logdir", str(tensorBoardPath)],
                       check=False, cwd=PROJECT_ROOT)



class LogMe(dict):
    def __init__(self,writer,term=True):
        self.writer = writer
        self.dic = defaultdict(list)
        self.term = term
    def write(self,i):
        if len(self.dic)==0: return
        s=f"Epoch {i} : "
        for k,v in self.dic.items():
            self.writer.add_scalar(k,sum(v)*1./len(v),i)
            s+=f"{k}:{sum(v)*1./len(v)} -- "
        self.dic.clear()
        if self.term: logging.info(s)
    def update(self,l):
        for k,v in l:
            self.add(k,v)
    def direct_write(self,k,v,i):
        self.writer.add_scalar(k,v,i)
    def add(self,k,v):
        self.dic[k].append(v)

def save_src(path):
    output_dir = Path(path)
    source_files = [
        *PROJECT_ROOT.joinpath("src").rglob("*.py"),
        *PROJECT_ROOT.joinpath("configs").rglob("*.yaml"),
    ]
    with ZipFile(output_dir / "source.zip", "w", compression=ZIP_DEFLATED) as archive:
        for source_file in source_files:
            archive.write(source_file, source_file.relative_to(PROJECT_ROOT))

def prs(*args):
    st = ""
    for s in args:
        st += str(s)
    print(st)


class DotDict(dict):
    """dot.notation access to dictionary attributes (Thomas Robert)"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def load_yaml(path):
    path = Path(path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    with open(path, 'r') as stream:
        opt = yaml.load(stream,Loader=yaml.Loader)
    return DotDict(opt)

def write_yaml(file,dotdict):
    d=dict(dotdict)
    with open(file, 'w', encoding='utf8') as outfile:
        yaml.dump(d, outfile, default_flow_style=False, allow_unicode=True)

global verbose
verbose=2

def printv(*o,p=0):
    if p<verbose:
        print(*o)

def checkConfUpdate(outdir,config):
    if os.path.exists(os.path.join(outdir, 'update.yaml')):
        try:
            config2 = load_yaml(os.path.join(outdir, 'update.yaml'))
            print("update conf with:",config2)
            for k in config2:
                config[k] = config2[k]
            if config2.get("execute") is not None:
                exec(config2["execute"])
            now = datetime.now()
            date_time = now.strftime("%d-%m-%Y-%HH%M-%SS")
            write_yaml(os.path.join(outdir, 'newConfig_' + date_time + '.yaml'), config)
            os.remove(os.path.join(outdir, 'update.yaml'))
        except yaml.scanner.ScannerError:
            print("update config failed, yaml error")
        except SyntaxError:
            print("pb with exec code in config")

def logConfig(logger,config):
    print(str(yaml.dump(dict(config))))
    st = ""
    for i, v in dict(config).items():
        st += "\t \t \t \n" + str(i) + ":" + str(v)
    logger.writer.add_text("config", st, 1)

def logRun(name,config,agent_object):
    global agent
    agent=agent_object
    now = datetime.now()
    date_time = now.strftime("%d-%m-%Y-%HH%M-%SS")
    outdir = PROJECT_ROOT / "XP" / config["env"] / (name + "_" + date_time)
    print("Saving in " + str(outdir))
    os.makedirs(outdir, exist_ok=True)
    save_src(outdir)
    config["commit"] = subprocess.check_output(
        ['git', 'show-ref'], cwd=PROJECT_ROOT
    ).decode('utf-8')
    write_yaml(os.path.join(outdir, 'config.yaml'), config)
    logger = LogMe(SummaryWriter(str(outdir)))
    loadTensorBoard(str(outdir))
    logConfig(logger, config)
    return logger,str(outdir)


# Wrapper personnalisé pour activer/désactiver le rendu: pas d'autre solution que d'avoir deux env
class DualEnvWrapper(gym.Wrapper):
    def __init__(self, config):
        try:
            self.silent_env= gym.make(config["env"])
            self.human_env =  gym.make(config["env"], render_mode="human")
        except gym.error.Error:
            self.silent_env=config["env_maker"](config["env"])
            self.human_env =config["env_maker"](config["env"], render_mode="human")
        super(DualEnvWrapper, self).__init__(self.silent_env)
        self.nb_episodes=0
        self.config=config
        self.seed=config["seed"]
        #self.env=self.silent_env

    #def _make_env


    def reset(self,  *args, **kwargs):
        if (self.nb_episodes >= 0 and self.nb_episodes % int(self.config["freqVerbose"]) == 0):
            self.env=self.human_env
        else:
            self.env = self.silent_env
        self.seed+=1
        self.nb_episodes+=1

        return self.env.reset(seed=self.seed,*args, **kwargs)

    def setPlan(self, map, rewards):
        self.silent_env.unwrapped.setPlan(map, rewards)
        self.human_env.unwrapped.setPlan(map, rewards)

def init(config_file, algoName):
    #print("envs registered :", gym.envs.registry)
    config = load_yaml(config_file)
    if config.get("map"):
        map_path = Path(config["map"])
        if not map_path.is_absolute():
            config["map"] = str(PROJECT_ROOT / map_path)
    #config["commit"] = subprocess.check_output(['git', 'show-ref']).decode('utf-8')
    if config.get("import") is not None:
        exec(config["import"])
    #render_mode = "human"
    env=DualEnvWrapper(config)
    #try:
    #    env = gym.make(config["env"],render_mode=render_mode)
    #except gym.error.Error:
    #    env=config["env_maker"](config["env"],render_mode=render_mode)




    if config.get("execute") is not None:
        exec(config["execute"])



    np.random.seed(config["seed"])
    #a=np.random.get_state()
    #print(a)
    #print(np.random.rand())
    #np.random.set_state(a)
    #ss = env.seed(config["seed"])
    #print(ss)
    #print(np.random.rand())

    torch.manual_seed(config["seed"])
    if config.device > -1:
        torch.cuda.manual_seed_all(config["seed"])

    if config.get("determninistic_opt") is not None:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    now = datetime.now()
    date_time = now.strftime("%d-%m-%Y-%HH%M-%SS")
    outdir = PROJECT_ROOT / "XP" / config["env"] / (algoName + "_" + date_time)

    print("Saving in " + str(outdir))
    os.makedirs(outdir, exist_ok=True)
    save_src(outdir)
    write_yaml(os.path.join(outdir, 'config.yaml'), config)
    logger = LogMe(SummaryWriter(str(outdir)))
    loadTensorBoard(str(outdir))

    return env, config, str(outdir), logger
