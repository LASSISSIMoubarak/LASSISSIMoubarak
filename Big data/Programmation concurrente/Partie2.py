#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import time
import re
import asyncio
from typing import List, Optional

# ---------------- Entrée du script ----------------
def main():
    global logf

    if len(sys.argv) != 2:
        usage()
    fcommandes = sys.argv[1]

    # --- préparer le fichier de commandes s
    dossier = os.path.dirname(fcommandes)
    if dossier:
        os.makedirs(dossier, exist_ok=True)

    # --- préparer log 
    logfile = os.path.join(os.getcwd(), "borabora.log")
    print(f"log in {logfile} ...")
    logf = open(logfile, "w", encoding="utf-8")
    print("\n---", file=logf, flush=True)
    try:
        asyncio.run(main_async(fcommandes))
    finally:
        if logf:
            logf.close()









# ---------------- Logable ----------------
logf = None  
class Logable:
    def __init__(self, name: str, verbose: bool):
        self.name = name
        self.verbose = verbose
    def log(self, msg: str):
        if self.verbose and logf is not None:
            print(f"[{self.name}] {msg}", file=logf, flush=True)



# ---------------- Clients ----------------
class Clients:
    def __init__(self, fname: str):
        commandes = []
        start = time.time()
        fmt = re.compile(r"^\s*(\d+)\s+(.*\S)\s*$")
        with open(fname, "r", encoding="utf-8") as f:
            for line in f:
                found = fmt.search(line)
                if found:
                    when = int(found.group(1))
                    what = found.group(2)
                    consommations = [c.strip() for c in what.split(",") if c.strip()!=""]
                    commandes.append((start + when, consommations))
        self.commandes = commandes[::-1]
        self._done = False

    async def commande(self) -> Optional[List[str]]:
        if not self.commandes:
            self._done = True
            return None
        next_time, cons = self.commandes[-1]
        now = time.time()
        delay = next_time - now
        if delay > 0:
            # Attendre le délai (coopératif)
            await asyncio.sleep(delay)
        # pop et retourner
        self.commandes.pop()
        if not self.commandes:
            self._done = True
        return cons
    def done(self) -> bool:
        return self._done
    

# ---------------- Accessoire (Pic / Bar) ----------------
class Accessoire(Logable):
    """
    Wrapper autour d'une asyncio.Queue pour loguer opérations.
    On utilise une queue interne (asyncio.Queue)
    """
    def __init__(self, name: str, verbose: bool):
        Logable.__init__(self, name, verbose)
        # queue sans limite (maxsize=0)
        self._q = asyncio.Queue()
    # pour debug / inspection
    def qsize(self) -> int:
        return self._q.qsize()

    async def put(self, item):
        await self._q.put(item)

    async def get(self):
        item = await self._q.get()
        return item

    def empty(self) -> bool:
        return self._q.empty()

# Pic et Bar utilisent Accessoire mais ont méthodes sémantiques
class Pic(Accessoire):
    async def embrocher(self, postit: List[str]):
        # log avant ajout : on affiche la taille après ajout 
        taille_apres = self.qsize() + 1
        self.log(f"post-it '{postit}' embroché, {taille_apres} post-it(s) à traiter")
        await self.put(postit)

    async def liberer(self) -> Optional[List[str]]:
        if self._q.empty():
            return None
        postit = await self.get()
        taille_apres = self.qsize()
        self.log(f"post-it '{postit}' libéré, {taille_apres} post-it(s) à traiter")
        return postit

class Bar(Accessoire):
    async def recevoir(self, commande: List[str]):
        await self.put(commande)
        self.log(f"'{commande}' posée, {self.qsize()} commande(s) à servir")

    async def evacuer(self) -> Optional[List[str]]:
        if self._q.empty():
            return None
        commande = await self.get()
        self.log(f"'{commande}' évacuée, {self.qsize()} commande(s) à servir")
        return commande




# ---------------- Employe (Serveur / Bariste) ----------------
class Employe(Logable):
    def __init__(self, pic: Pic, bar: Bar, clients: Clients, name: str, verbose: bool):
        Logable.__init__(self, name, verbose)
        self.pic = pic
        self.bar = bar
        self.clients = clients
        self.step = 0
        self.lock = asyncio.Lock() #pour protéger les sections critiques
        self.log('prêt pour le service')
class Serveur(Employe):
    async def prendre_commandes_loop(self):
        while True:
            commande = await self.clients.commande()
            if commande is None:
                break
            async with self.lock:
                self.log("prêt pour prendre une nouvelle commande...'")
                self.log(f"j'ai la commande '{commande}'")
                self.log(f"j'écris sur le post-it '{commande}'")
                await self.pic.embrocher(commande)
                await asyncio.sleep(0)
        return
    async def servir_loop(self):
        while True:
            commande = None
            if not self.bar.empty():
                commande = await self.bar.evacuer()
            else:
                if self.clients.done() and self.pic.empty() and self.bar.empty():
                    break
                await asyncio.sleep(0.05)
                continue

            if commande is None:
                await asyncio.sleep(0.01)
                continue

            # servir la commande (une par une) en protégeant l'intégralité du service
            async with self.lock:
                self.log(f"j'apporte la commande '{commande}'")
                for conso in commande:
                    self.log(f"je sers '{conso}'")
                    #  un petit temps de service et coopératif
                    await asyncio.sleep(0.02)
                # fin de la commande ; courte pause coopérative
                await asyncio.sleep(0)

        return

    async def run(self):
        # lancer les deux boucles concurrentes
        t1 = asyncio.create_task(self.prendre_commandes_loop())
        t2 = asyncio.create_task(self.servir_loop())
        # attendre que les deux se terminent
        await asyncio.gather(t1, t2)

# Bariste prépare les commandes depuis Pic et les poste au Bar.
class Bariste(Employe):
    async def preparer_loop(self):
        while True:
            # tenter de liberer un post-it
            if not self.pic.empty():
                postit = await self.pic.liberer()
            else:
                # si plus rien à venir (clients done) et pic vide => on peut terminer
                if self.clients.done() and self.pic.empty():
                    break
                await asyncio.sleep(0.05)
                continue

            if postit is None:
                await asyncio.sleep(0.01)
                continue

            # préparer la commande (une seule à la fois)
            async with self.lock:
                self.log(f"je commence la fabrication de '{postit}'")
                for conso in postit:
                    self.log(f"je prépare '{conso}'")
                    # simuler temps de préparation et coopérer
                    await asyncio.sleep(0.03)
                # une fois prête, poser au bar
                await self.bar.recevoir(postit)
                self.log(f"la commande {postit} est prête")
                await asyncio.sleep(0)

        return

    async def run(self):
        await self.preparer_loop()

# ---------------- Main asynchrone ----------------
async def main_async(fcommandes_path: str):
    # Créer Clients (lecture déjà synchrone dans __init__)
    les_clients = Clients(fcommandes_path)

    # Créer accessoires (Pic/Bar)
    le_pic = Pic(name="le_pic", verbose=False)
    le_bar = Bar(name="le_bar", verbose=False)

    # Créer employés
    bob = Bariste(le_pic, le_bar, les_clients, name="bob", verbose=False)
    alice = Serveur(le_pic, le_bar, les_clients, name="alice", verbose=True)

    # Lancer les tâches concurrentes
    await asyncio.gather(
        bob.run(),
        alice.run()
    )


# ---------------- Utilitaires/usage ----------------
def usage():
    print(f"usage: {sys.argv[0]} fichier_commandes")
    sys.exit(1)




if __name__ == "__main__":
    main()
