
import cv2
import numpy as np
import glob
import os

window_size = 7 # Taille de la fenêtre locale c'est à dire la carte de fenetre . A default on met 7


#-----------------------------------------------------------------------------------------
def laplacian(img, window_size=window_size):
    """
    LAP2: Modified Laplacian focus measure d'arprès l'article
    """
    kernel_x = np.array([[1, -2, 1]])
    kernel_y = kernel_x.T
    Ix = cv2.filter2D(img, cv2.CV_64F, kernel_x)
    Iy = cv2.filter2D(img, cv2.CV_64F, kernel_y)
    FM = np.abs(Ix) + np.abs(Iy)
    focus_map = cv2.blur(FM, (window_size, window_size))
    return focus_map




#-----------------------------------------------------------------------------------------

def variance_of_laplacian(img, window_size=window_size):
    """
    LAP4: Variance of Laplacian focus measure d'après l'article
    """
    lap = cv2.Laplacian(img, cv2.CV_64F)
    # Moyenne locale de la variance
    mean = cv2.blur(lap, (window_size, window_size))
    var = cv2.blur((lap - mean) ** 2, (window_size, window_size))
    return var

#-----------------------------------------------------------------------------------------

def graylevel_variance(img, window_size=window_size):
    """
    STA3:de l'artcile 
    pour ce faire on a besoin de la variance locale des niveaux de gris
    donc forcement besoin de la moyenne locale.
    """
    mean = cv2.blur(img.astype(np.float64), (window_size, window_size))
    var = cv2.blur((img.astype(np.float64) - mean) ** 2, (window_size, window_size))
    return var



#-----------------------------------------------------------------------------------------





# Fonction principale pour traiter deux images et comparer leur netteté
def Traitement_images(img_path1, img_path2, window_size=window_size, results_list=None):
    # Charger les deux images (nette et floue) en niveaux de gris
    img1 = cv2.imread(img_path1, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(img_path2, cv2.IMREAD_GRAYSCALE)
    base1 = os.path.splitext(os.path.basename(img_path1))[0]
    base2 = os.path.splitext(os.path.basename(img_path2))[0]
    if img1 is None or img2 is None:
        raise ValueError("Erreur de chargement d'image.")

    # Dictionnaire des métriques qu'il faut utiliser dans notre cas
    metrics = {
        'Laplacian (LAP2)': laplacian,
        'Variance of Laplacian (LAP4)': variance_of_laplacian,
        'Gray-level Variance (STA3)': graylevel_variance
    }

    for name, func in metrics.items():
        # Calcul de la carte de netteté pour chaque image
        map1 = func(img1, window_size)
        map2 = func(img2, window_size)

        # On recupère la carte des maximale entre les deux cartes de netteté
        max_map = np.maximum(map1, map2) # Mais ce n'est pas suffisant pour determiner l'image la plus nette
        # Moyenne globale de chaque carte de netteté (score global de netteté)
        score1 = np.mean(map1)
        score2 = np.mean(map2)
        # Détermination automatique de l'image la plus nette
        if score1 > score2:
            print(" Image 1 est la plus nette selon cette métrique.\n")
        elif score2 > score1:
            print(" Image 2 est la plus nette selon cette métrique.\n")
        else:
            print(" Les deux images ont la même netteté selon cette métrique.\n")

        #Il faut maintenant reconstruire l'image en utilisant la carte de netteté maximale
        mask_img1 = map1 >= map2  # masque booléen : True si img1 est plus nette
        mask_img2 = ~mask_img1    # complémentaire : True si img2 est plus nette
        reconstructed = np.zeros_like(img1)
        reconstructed[mask_img1] = img1[mask_img1]
        reconstructed[mask_img2] = img2[mask_img2]

        # Sauvegarde de l'image reconstruite pour chaque métrique
        # Nom unique pour chaque image reconstruite
        out_name = f'image_reconstructed/reconstructed_{name.split()[0].lower()}_{base1}_vs_{base2}_w{window_size}.png'
        cv2.imwrite(out_name, reconstructed)
        print(f"  Image reconstruite sauvegardée sous : {out_name}\n")
        # 
        if results_list is not None:
            results_list.append({
                'image1': base1,
                'image2': base2,
                'metrique': name,
                'window_size': window_size,
                'score1': score1,
                'score2': score2
            })
if __name__ == "__main__":
    import csv
    # Récupère tous les fichiers jpg et bmp du dossier
    image_files = glob.glob("C:\\Users\\lassi\\projet\\TestingImageDataset\\Image_folder\\*.jpg")
    image_files += glob.glob("C:\\Users\\lassi\\projet\\TestingImageDataset\\Image_folder\\*.bmp")
    image_files.sort()

    used_files = set()
    pairs = []
    results = []
    for file1 in image_files:
        base, ext = os.path.splitext(file1)
        if base.endswith('a'):
            file2 = base[:-1] + 'b' + ext
            if file2 in image_files:
                pairs.append((file1, file2))
                used_files.add(file1)
                used_files.add(file2)
    print("Paires trouvées :")
    for file1, file2 in pairs:
        print(f"  {os.path.basename(file1)} {os.path.basename(file2)}")
        # Teste plusieurs tailles de fenêtre pour analyse
        for wsize in [5, 7, 9, 13, 17, 21]:
            Traitement_images(file1, file2, window_size=wsize, results_list=results)
    orphelins = [f for f in image_files if f not in used_files]
    if orphelins:
        print("\nFichiers sans paire correspondante :")
        for f in orphelins:
            print(f"  {os.path.basename(f)}")

    # Sauvegarde des sorties dans un fichiers csv poiur plus de statistiques
    with open('resultats_scores_nettete.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['image1', 'image2', 'metrique', 'window_size', 'score1', 'score2']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    print("\nTous les scores de comparaison ont été enregistrés dans resultats_scores_nettete.csv")

