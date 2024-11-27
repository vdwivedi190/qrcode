import numpy as np 
from PIL import Image
import matplotlib.pyplot as plt


# Function to display the QR code and mask
def qrdisplay(qrmat):
    fig, ax = plt.subplots(1, 1, figsize=(14, 6))
    ax.axis('off')
    fig.subplots_adjust(left=0.25, right=0.75, top=0.75, bottom=0.25)
    qr_image = Image.fromarray(np.uint8(~qrmat) * 255)

    # Pad the image with whitespace
    padding = 6
    padded_image = Image.new('L', (qr_image.size[0] + 2 * padding, qr_image.size[1] + 2 * padding), 255)
    padded_image.paste(qr_image, (padding, padding))

    ax.imshow(padded_image, cmap='gray', vmin=0, vmax=255)
    plt.show()


# Function to display the QR code and mask
def qrdisplay_all(qrmat, mask): 
    qrsize = qrmat.shape[0]

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(14, 6))
    plt.subplots_adjust(wspace=0.5)  # Increase the space between the two figures

    # Display the QR code
    qr_image = Image.fromarray(np.uint8(~qrmat) * 255)
    ax1.imshow(qr_image, cmap='gray', vmin=0, vmax=1)
    ax1.set_title("QR Code")
    ax1.set_xticks(np.arange(-.5, qrsize, 1), minor=True)
    ax1.set_yticks(np.arange(-.5, qrsize, 1), minor=True)
    ax1.grid(which='minor', color='gray', linestyle='-', linewidth=0.5)
    ax1.tick_params(which='minor', size=0)

    # Display the mask image
    mask_image = Image.fromarray(np.uint8(mask) * 255)
    ax2.imshow(mask_image, cmap='gray', vmin=0, vmax=255)
    ax2.set_title("Mask Image")
    ax2.grid(which='minor', color='gray', linestyle='-', linewidth=0.5)
    ax2.tick_params(which='minor', size=0)

    # Display the mask image
    combined_image = Image.fromarray(np.uint8(~qrmat) * 128 + np.uint8(mask) * 127)
    ax3.imshow(combined_image, cmap='gray', vmin=0, vmax=255)
    ax3.set_title("Combined Image")
    ax3.grid(which='minor', color='gray', linestyle='-', linewidth=0.5)
    ax3.tick_params(which='minor', size=0)

    plt.show()