#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import re
import asyncio
from typing import List, Optional

# ---------- Logging ----------
logf = None

class Logable:
    def __init__(self, name: str, verbose: bool):
        self.name = name
        self.verbose = verbose

    def log(self, msg: str):
        if self.verbose and logf is not None:
            print(f"[{self.name}] {msg}", file=logf, flush=True)

# ---------- Clients ----------
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
                    consommations = [c.strip() for c in what.split(",") if c.strip()]
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
            await asyncio.sleep(delay)
        self.commandes.pop()
        if not self.commandes:
            self._done = True
        return cons

    def done(self) -> bool:
        return self._done

# ---------- Accessoires ----------
class Accessoire(Logable):
    def __init__(self, name: str, verbose: bool):
        super().__init__(name, verbose)
        self._q = asyncio.Queue()

    async def put(self, item):
        await self._q.put(item)

    async def get(self):
        return await self._q.get()

    def empty(self):
        return self._q.empty()

    def qsize(self):
        return self._q.qsize()

class Pic(Accessoire):
    async def embrocher(self, postit: List[str]):
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

# ---------- Employés ----------
class Employe(Logable):
    def __init__(self, pic: Pic, bar: Bar, clients: Clients, name: str, verbose: bool, productivity: float = 1.0):
        super().__init__(name, verbose)
        self.pic = pic
        self.bar = bar
        self.clients = clients
        self.productivity = float(productivity) if productivity > 0 else 1.0
        self.lock = asyncio.Lock()
        self.log("prêt pour le service")

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
                await asyncio.sleep(0.05 * self.productivity)
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

            async with self.lock:
                self.log(f"j'apporte la commande '{commande}'")
                for conso in commande:
                    self.log(f"je sers '{conso}'")
                    await asyncio.sleep(0.1 * self.productivity)
                await asyncio.sleep(0)
        return

    async def run(self):
        t1 = asyncio.create_task(self.prendre_commandes_loop())
        t2 = asyncio.create_task(self.servir_loop())
        await asyncio.gather(t1, t2)

class Bariste(Employe):
    async def servir_direct(self, commande: List[str]):
        self.log(f"je dépanne et je sers moi-même {commande}")
        for boisson in commande:
            self.log(f"je sers '{boisson}' (dépannage)")
            await asyncio.sleep(0.08 * self.productivity)

    async def preparer_loop(self):
        while True:
            # aider serveurs si pic vide
            if self.pic.empty() and not self.bar.empty():
                commande = await self.bar.evacuer()
                if commande:
                    await self.servir_direct(commande)
                    await asyncio.sleep(0)
                    continue

            if not self.pic.empty():
                postit = await self.pic.liberer()
            else:
                if self.clients.done() and self.pic.empty():
                    break
                await asyncio.sleep(0.05)
                continue

            if postit is None:
                await asyncio.sleep(0.01)
                continue

            async with self.lock:
                self.log(f"je commence la fabrication de '{postit}'")
                for conso in postit:
                    self.log(f"je prépare '{conso}'")
                    await asyncio.sleep(0.12 * self.productivity)
                await self.bar.recevoir(postit)
                self.log(f"la commande {postit} est prête")
                await asyncio.sleep(0)
        return

    async def run(self):
        await self.preparer_loop()

# ---------- main async ----------
async def main_async(fcommandes_path: str):
    les_clients = Clients(fcommandes_path)

    le_pic = Pic(name="le_pic", verbose=False)
    le_bar = Bar(name="le_bar", verbose=False)

    bob = Bariste(le_pic, le_bar, les_clients, name="bob", verbose=False, productivity=1.0)
    alice = Serveur(le_pic, le_bar, les_clients, name="alice", verbose=True, productivity=0.9)
    marc  = Serveur(le_pic, le_bar, les_clients, name="marc",  verbose=True, productivity=1.2)

    await asyncio.gather(
        bob.run(),
        alice.run(),
        marc.run()
    )

# ---------- usage ----------
def usage():
    print(f"usage: {sys.argv[0]} fichier_commandes")
    sys.exit(1)

def main():
    global logf
    if len(sys.argv) != 2:
        usage()

    fcommandes = sys.argv[1]

    if not os.path.exists(fcommandes):
        with open(fcommandes, "w", encoding="utf-8") as f:
            f.write("0 tequila sunrise,margarita\n0 daiquiri,ti-punch\n")

    logfile = os.path.join(os.getcwd(), "borabora.log")
    print(f"log in {logfile} ...")
    logf = open(logfile, "w", encoding="utf-8")
    print("\n---", file=logf, flush=True)

    try:
        asyncio.run(main_async(fcommandes))
    finally:
        if logf:
            logf.close()

if __name__ == "__main__":
    main()
