import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def sobel_numpy(image):
    image = image.astype(np.float64)

    Kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])

    Ky = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])

    padded = np.pad(image, 1, mode="reflect")

    windows = sliding_window_view(padded, (3, 3))  # (H, W, 3, 3)

    gx = np.tensordot(windows, Kx, axes=((2, 3), (0, 1)))
    gy = np.tensordot(windows, Ky, axes=((2, 3), (0, 1)))

    magnitude = np.sqrt(gx**2 + gy**2)

    return magnitude


def match_histogram(source, reference, n_bins=256):
    """
    Adjust the pixel values of a grayscale source image
    so that its histogram matches that of the reference image.

    Parameters:
        source (np.ndarray): Input image to transform.
        reference (np.ndarray): Reference image.
        n_bins (int): Number of bins (default 256).

    Returns:
        matched (np.ndarray): Histogram-matched image.
    """
    # Flatten images
    src = source.ravel()
    ref = reference.ravel()

    # Compute histogram and CDF for source
    src_hist, src_bins = np.histogram(src, bins=n_bins, range=(src.min(), src.max()))
    src_cdf = src_hist.cumsum()
    src_cdf = src_cdf / src_cdf[-1]

    # Compute histogram and CDF for reference
    ref_hist, ref_bins = np.histogram(ref, bins=n_bins, range=(ref.min(), ref.max()))
    ref_cdf = ref_hist.cumsum()
    ref_cdf = ref_cdf / ref_cdf[-1]

    # Map source pixels to reference
    interp_values = np.interp(src_cdf, ref_cdf, ref_bins[:-1])

    matched = np.interp(src, src_bins[:-1], interp_values)

    return matched.reshape(source.shape)
