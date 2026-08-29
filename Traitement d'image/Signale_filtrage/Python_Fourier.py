import numpy as np
from collections import Counter
import math
import heapq
import itertools
from PIL import Image
#Exercice1
# FONCTION ENTROPIE
def entropy(array):
    values, counts = np.unique(array.flatten(), return_counts=True) #Vectorise les données et calcul le nombre d'occurence
    probs = counts / counts.sum()
    return -np.sum(probs * np.log2(probs))
# -----------------------------Exercice2---------------------------------------------------
###Partie 1-----------------------------------
# Implémentation du linear predictive ----------------------------------------
def linear_predictive(image):
    pred = np.zeros_like(image, dtype=np.int32)  
    rows, cols = image.shape
    for i in range(rows):
        pred[i, 0] = image[i, 0]  # on garde le premier pixel de chaque ligne
        for j in range(1, cols):
            predicted = image[i, j-1]
            pred[i, j] = np.int32(image[i, j]) - np.int32(predicted)
    return pred
##Fin de partie 1--------------------------------
#Partie 2-----------------------------------
#-----------------------------------------------------------------------------Code de Huffman-------------------------------
class Huffman:
    def __init__(self, symbol=None, freq=0, left=None, right=None):
        self.symbol = symbol
        self.freq = freq
        self.left = left
        self.right = right
    def __lt__(self, other):
        return self.freq < other.freq
def huffman_code(array):
    # Compter la fréquence de chaque symbole (pixel ou résidu)
    #    `array.flatten()` transforme l'image 2D en un vecteur 1D
    freq = Counter(array.flatten())  # compte la fréquence de chaque symbole

    # Construire la forêt initiale : un tas (min-heap) de nœuds feuilles
    # Chaque entrée du heap est un tuple (frequency, tie_id, node)
    # - frequency : nombre d'occurrences du symbole
    # - tie_id   : identifiant unique (next(counter)) utilisé pour départager
    #              deux symboles ayant la même fréquence (évite les erreurs
    #              de comparaison entre objets node)
    # - node     : instance de Huffman pour ce symbole
    counter = itertools.count()
    heap = [(count, next(counter), Huffman(symbol, count)) for symbol, count in freq.items()]
    heapq.heapify(heap)  # transforme la liste en un min-heap en place

    # Fusionner les deux nœuds de plus faible fréquence jusqu'à obtenir un seul arbre (la racine) : algorithme classique de Huffman
    while len(heap) > 1:
        # Extraire les deux nœuds avec les plus petites fréquences
        _, _, left = heapq.heappop(heap)
        _, _, right = heapq.heappop(heap)
        # Créer un nouveau nœud interne (sans symbole) avec la fréquence égale à la somme des fréquences des deux nœuds extraits
        merged = Huffman(None, left.freq + right.freq, left, right)
        # Réinsérer le nœud fusionné dans le heap
        heapq.heappush(heap, (merged.freq, next(counter), merged))

    #À la fin, le heap contient un seul élément : la racine de l'arbre
    root = heap[0][2]

    # Parcourir l'arbre pour générer les codes binaires :
    #    - aller à gauche ajoute '0' au préfixe
    #    - aller à droite ajoute '1' au préfixe
    #    Lorsqu'on atteint une feuille, on enregistre le code pour ce symbole
    codes = {}
    def build_codes(node, prefix=""):
        if node.symbol is not None:
            # feuille : associer le symbole au code (chaîne de '0'/'1')
            #si l'arbre ne contient qu'un seul symbole, on lui donne le code '0' pour éviter la chaîne vide
            codes[node.symbol] = prefix or "0"
        else:
            build_codes(node.left, prefix + "0")
            build_codes(node.right, prefix + "1")

    build_codes(root)
    return codes # dictionnaire {symbole: code binaire} Constituant le code de Huffman
##Fin de partie 2--------------------------------

if __name__=="__main__":   
    #Chargement de données 
    img = Image.open("C:/Users/lassi/Downloads/meteo.webp").convert("L")
    data = np.array(img)
    #EXO1
    # Tous les pixels ont la même valeur donc entropie va valoir 0
    img_min_entropy = np.zeros((100, 100), dtype=np.uint8)
    entropy_min = entropy(img_min_entropy)
    # Pixels uniformément distribués entre 0 et 255 pour avoir une diversité de pixel
    img_max_entropy = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
    entropy_max = entropy(img_max_entropy)

    # RÉSULTATS
    print("\n---------- CALCUL D'ENTROPIE EXO1 -----------------------")
    print(f"Entropie minimale EXO1   : {entropy_min:.6f} bits")
    print(f"Entropie maximale Aléatoire EXO1 : {entropy_max:.6f} bits")
    ##Fin Exercice1-  ----------------------------------------

    predicted = linear_predictive(data)
    ## calcul d'entrpoie et codage de Huffman
    # -----------------------------
    #Exo2 Partie 1
    Entropie_brute = entropy(data)
    Entropie_predite = entropy(predicted)
    print("Entropie image originale EXO2 :", Entropie_brute)
    print("Entropie image prédite   EXO2 :", Entropie_predite)
    #Exo2 Partie 2
    codes_brute = huffman_code(data)
    codes_predicted = huffman_code(predicted)
    print("Le nombre moyenne de bite de chaque pixel pour l'image brute EXO2 :", np.mean([len(codes_brute[val]) for val in data.flatten()]))
    print("Le nombre moyenne de bite de chaque pixel pour l'image prédite EXO2 :", np.mean([len(codes_predicted[val]) for val in predicted.flatten()]))
    # print(codes_brute)