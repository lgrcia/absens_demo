import cv2
import numpy as np
from skimage import filters


def edge_detection(image):
    """Detect edges in a grayscale image using the Sobel filter.

    Args:
        image (np.ndarray): 2D grayscale image array.

    Returns:
        np.ndarray: Edge magnitude image of the same shape.
    """
    return filters.sobel(image)


def find_translation(im0, im1):
    """Estimate the translation vector between two grayscale images using ECC.

    Uses OpenCV's findTransformECC with a translation motion model to compute
    the pixel-level shift that aligns im1 to im0.

    Args:
        im0 (np.ndarray): Reference grayscale image.
        im1 (np.ndarray): Target grayscale image to align.

    Returns:
        np.ndarray: 1D array [tx, ty] representing the translation in pixels.
    """
    # use findTransformECC from opencv
    # convert to float32
    im0 = im0.astype(np.float32)
    im1 = im1.astype(np.float32)
    # find translation
    warp_matrix = np.eye(2, 3, dtype=np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-6)
    cc, warp_matrix = cv2.findTransformECC(
        im0, im1, warp_matrix, cv2.MOTION_TRANSLATION, criteria
    )
    return warp_matrix[:2, 2]


def wrap_image(im, translation):
    """Apply a translation to an image using affine warping.

    Args:
        im (np.ndarray): Image array to warp (any number of channels).
        translation (np.ndarray): 1D array [tx, ty] representing the translation in pixels.

    Returns:
        np.ndarray: Warped image as a float32 array of the same shape.
    """
    # convert to float32
    im = im.astype(np.float32)
    # wrap image
    warp_matrix = np.eye(2, 3, dtype=np.float32)
    warp_matrix[:2, 2] = translation
    wrapped_im = cv2.warpAffine(
        im,
        warp_matrix,
        (im.shape[1], im.shape[0]),
        flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
    )
    return wrapped_im
