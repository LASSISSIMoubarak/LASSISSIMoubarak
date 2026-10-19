import argparse
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
from numpy.fft import fft2, ifft2

# ---------------------------------------------------------
# Création de la PSF (flou gaussien)
# ---------------------------------------------------------
def gaussian_psf(size, sigma):
    ax = np.arange(-size//2 + 1., size//2 + 1.)
    xx, yy = np.meshgrid(ax, ax)
    psf = np.exp(-(xx**2 + yy**2) / (2. * sigma**2))
    psf /= psf.sum()
    return psf

# ---------------------------------------------------------
# Filtre de Wiener dans le domaine fréquentiel
# ---------------------------------------------------------
def wiener_filter(blurred, psf, K):
    H = fft2(psf, s=blurred.shape)
    G = fft2(blurred)

    H_conj = np.conj(H)
    W = H_conj / (np.abs(H)**2 + K)

    F_hat = W * G
    f_hat = np.real(ifft2(F_hat))
    return f_hat

def main():
    default_image = Path(__file__).resolve().parent / "Image_folder" / "testna_slika1a.bmp"
    parser = argparse.ArgumentParser(description="Restauration d'image par filtre de Wiener.")
    parser.add_argument(
        "--image",
        type=Path,
        default=default_image,
        help="Image en niveaux de gris (par défaut : Image_folder/testna_slika1a.bmp)",
    )
    args = parser.parse_args()

    image = cv2.imread(str(args.image), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Impossible de lire l'image : {args.image}")
    image = image.astype(np.float32) / 255.0

    psf = gaussian_psf(size=31, sigma=1.5)
    k_values = (0.01, 0.05, 0.1)
    results = [wiener_filter(image, psf, k) for k in k_values]

    plt.figure(figsize=(12, 6))
    plt.subplot(1, 4, 1)
    plt.title("Image d'entrée")
    plt.imshow(image, cmap="gray")
    plt.axis("off")

    for i, (k, result) in enumerate(zip(k_values, results), start=2):
        plt.subplot(1, 4, i)
        plt.title(f"K = {k}")
        plt.imshow(result, cmap="gray")
        plt.axis("off")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
