import logging
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np

from .io import load_npy

logger = logging.getLogger(__name__)


def make_video(image_folder: Path, output_path: Path, fps: int = 1):
    """Create an MP4 video from .npz image files in a folder.

    Args:
        image_folder (Path): Directory containing .npz files with an "rgb" key.
        output_path (Path): Output path for the MP4 video file.
        fps (int): Frames per second for the output video (default: 1).
    """
    image_files = sorted(image_folder.glob("*.npz"))
    if not image_files:
        logger.warning(f"No images found in {image_folder}. Skipping video creation.")
        return

    height, width, _ = load_npy(image_files[0])["rgb"].shape

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    for image_file in image_files:
        logger.info(f"Adding image {image_file} to video...")
        img = load_npy(image_file)["rgb"]
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        video.write(img_bgr)

    video.release()
    logger.info(f"Video saved to {output_path}")


def plot_function(raw, aligned, bbox=None):
    """Plot raw and aligned images side by side with cloud mask contours.

    Creates a two-row figure showing the raw image on top and the aligned image
    below. Yellow contours indicate cloud coverage from the CLM mask. If a
    bounding box is provided, axes are labelled with geographic coordinates.

    Args:
        raw (dict): Dictionary with keys "rgb" (np.ndarray) and "clm" (np.ndarray)
            for the raw (unaligned) image.
        aligned (dict): Dictionary with keys "rgb" and "clm" for the aligned image.
        bbox (list[float] | None): Optional bounding box [west, south, east, north]
            used to set axis extents and labels.
    """
    extent = None
    if bbox is not None:
        # bbox: [west, south, east, north] -> extent: [left, right, bottom, top]
        extent = [bbox[0], bbox[2], bbox[1], bbox[3]]

    def plot_rgb_clm(data, ax):
        ax.imshow(data["rgb"], extent=extent)
        # draw contour around clouds
        ax.contour(
            data["clm"],
            levels=[0.5],
            colors="yellow",
            linewidths=0.5,
            alpha=1,
            extent=extent,
            origin="upper",
        )

    dpi = 120
    margin_w = 1.5  # y-label + ytick labels on the left
    margin_h = 0.8  # title on top + x-label/xtick labels on bottom
    if bbox is not None:
        lon_span = bbox[2] - bbox[0]
        lat_span = bbox[3] - bbox[1]
        # Correct longitude for latitude: 1° lon = cos(lat) * 1° lat in distance
        mean_lat = (bbox[1] + bbox[3]) / 2
        effective_lon_span = lon_span * np.cos(np.radians(mean_lat))
        scale = 150.0  # inches per degree of latitude
        figsize = (
            lon_span * scale,
            2 * lat_span * scale,
        )
    else:
        h, w = raw["rgb"].shape[:2]
        figsize = (w / dpi + margin_w, 2 * h / dpi)
    _, axes = plt.subplots(2, 1, figsize=figsize, sharey=True, sharex=True, dpi=dpi)
    plot_rgb_clm(raw, axes[0])
    axes[0].set_title("Raw Image")
    plot_rgb_clm(aligned, axes[1])
    axes[1].set_title("Aligned Image")

    if bbox is not None:
        axes[1].set_xlabel("Longitude (°)")
        for ax in axes:
            ax.set_ylabel("Latitude (°)")

    plt.tight_layout()
