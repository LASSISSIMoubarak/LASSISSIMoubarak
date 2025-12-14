#!/bin/env python3
# -*- coding: utf-8 -*-
import sys, time, re
import os

# ---------------- Classe Logable ----------------

## Classe de base pour disposer d'une méthode log qui affiche des messages si verbose=True
class Logable:
    """Classe de base pour disposer d'une méthode log"""
    def __init__(self, name, verbose):
        self.name = name
        self.verbose = verbose

    def log(self, msg):
        if self.verbose:
            print(f"[{self.name}] {msg}", file=logf, flush=True)

##########################################################################################


####Accessoires : Pic (pile LIFO) et Bar (file FIFO)####
# ---------------- Classe Accessoire ----------------
class Accessoire(list, Logable):
    """Accessoire : base pour Pic et Bar"""
    def __init__(self, name, verbose):
        list.__init__(self)
        Logable.__init__(self, name, verbose)


###########################################################################



#------------------------------------------------------------------------------------------

##Pic : pile LIFO pour les post-it des commandes à fabriquer
##Bar : file FIFO pour les commandes prêtes à être servies
## sans oublier à enrichir l'ACCESSSOIRE de base pour la gestion des logs

# ---------------- Classe Pic ----------------
class Pic(Accessoire):
    """Pile LIFO contenant les commandes à fabriquer"""
    def embrocher(self, postit):
        self.log(f"post-it '{postit}' embrochée, {len(self)+1} post-it(s) à traiter")
        self.append(postit)

    def liberer(self):
        if len(self) > 0:
            postit = self.pop()
            self.log(f"post-it '{postit}' libéré, {len(self)} post-it(s) à traiter")
            return postit
        return None


############################################################################




####Bar : file FIFO pour les commandes prêtes à être servies
# ---------------- Classe Bar ----------------
class Bar(Accessoire):
    """File FIFO pour recevoir les commandes à servir"""
    def recevoir(self, commande):
        self.append(commande)
        self.log(f"'{commande}' posée, {len(self)} commande(s) à servir")

    def evacuer(self):
        if len(self) > 0:
            commande = self.pop(0)
            self.log(f"'{commande}' évacuée, {len(self)} commande(s) à servir")
            return commande
        return None




############################################################################


####Employe : base pour Serveur et Bariste
# ---------------- Classe Employe ----------------
class Employe(Logable):
    """Base pour Serveur et Bariste"""
    def __init__(self, pic, bar, clients, name, verbose):
        Logable.__init__(self, name, verbose)
        self.pic = pic
        self.bar = bar
        self.clients = clients
        self.step = 0
        self.log('prêt pour le service')

# ---------------- Classe Serveur ----------------
class Serveur(Employe):
    def prendre_commande(self):
        while True:
            commande = self.clients.commande()
            if not commande:
                break
            self.log("prêt pour prendre une nouvelle commande...'")
            self.log(f"j'ai la commande '{commande}'")
            self.log(f"j'écris sur le post-it '{commande}'")
            self.pic.embrocher(commande)

    def servir(self):
        while True:
            commande = self.bar.evacuer()
            if not commande:
                break
            self.log(f"j'apporte la commande '{commande}'")
            for conso in commande:
                self.log(f"je sers '{conso}'")

    def run(self):
        if self.step == 0:
            self.step += 1
            self.prendre_commande()
        elif self.step == 1:
            self.step += 1
            self.servir()

# ---------------- Classe Bariste ----------------
class Bariste(Employe):
    def preparer(self):
        while True:
            commande = self.pic.liberer()
            if not commande:
                break
            self.log(f"je commence la fabrication de '{commande}'")
            for conso in commande:
                self.log(f"je prépare '{conso}'")
            self.bar.recevoir(commande)
            self.log(f"la commande {commande} est prête")

    def run(self):
        self.preparer()



############################################################################

####Clients : simulation des clients à partir d'un fichier avec temporisation
# ---------------- Classe Clients ----------------
class Clients:
    """Simule les clients à partir d'un fichier avec temporisation"""
    def __init__(self, fname):
        commandes = []
        start = time.time()
        fmt = re.compile(r"(\d+)\s+(.*)")
        with open(fname, "r") as f:
            for line in f:
                found = fmt.search(line)
                if found:
                    when = int(found.group(1))
                    what = found.group(2)
                    commandes.append((start + when, what.split(",")))
        self.commandes = commandes[::-1]

####  Méthode commande : retourne la prochaine commande si son temps est écoulé
    def commande(self):
        if len(self.commandes) > 0:
            while True:
                if time.time() > self.commandes[-1][0]:
                    return self.commandes.pop()[1]
        else:
            return None



# ---------------- Fonction main ----------------
def main():
    alice.run()  # Serveur prend les commandes
    bob.run()    # Bariste prépare les commandes
    alice.run()  # Serveur sert les commandes

# ---------------- Fonction usage ----------------
def usage():
    print(f"usage: {sys.argv[0]} fichier")
    exit(1)


# ---------------- Exécution ----------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()
    fcommandes = sys.argv[1]

    if not os.path.exists(fcommandes):
        with open(fcommandes, "w", encoding="utf-8") as f:
            f.write("0 tequila sunrise,margarita\n0 daiquiri,ti-punch\n")


    logfile = "borabora.log"
    print(f"login in {logfile}...")
    logf = open(logfile, "w")
    print("\n---", file=logf, flush=True)

    les_clients = Clients(fcommandes)

    le_pic = Pic(name="le_pic", verbose=False)
    le_bar = Bar(name="le_bar", verbose=False)
    bob = Bariste(le_pic, le_bar, les_clients, name="bob", verbose=False)
    alice = Serveur(le_pic, le_bar, les_clients, name="alice", verbose=True)

    main()
