import numpy as np
import cv2
import matplotlib.pyplot as plt
from scipy.signal import fftconvolve
from numpy.fft import fft2, ifft2, fftshift

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

# --------------------------------------------------------- UTILISATION D'image réelle ---------------------------------------------------------
image = cv2.imread("C:\\Users\\lassi\\projet\\R_project\\CATPCA\\WhatsApp Image 2025-10-20 at 23.06.46.jpeg", cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0

# PSF gaussienne
sigma = 1.5
psf = gaussian_psf(size=31, sigma=sigma)

# Différentes valeurs de K
Ks = np.random.uniform(0.01, 0.1, 1000)
results = [wiener_filter(image, psf, K) for K in Ks]

# ---------------------------------------------------------
plt.figure(figsize=(12, 6))
plt.subplot(1, 4, 1)
plt.title("Image floutée")
plt.imshow(image, cmap='gray')
plt.axis('off')

for i, K in enumerate(Ks[:3]):
    plt.subplot(1, 4, i+2)
    plt.title(f"K = {K}")
    plt.imshow(results[i], cmap='gray')
    plt.axis('off')

plt.tight_layout()
plt.show()
