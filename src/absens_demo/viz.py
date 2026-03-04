import cv2
import logging
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from .io import load_npy

logger = logging.getLogger(__name__)


def make_video(image_folder: Path, output_path: Path, fps: int = 1):
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


def plot_function(raw, aligned):
    def plot_rgb_clm(data, ax):
        ax.imshow(data["rgb"])
        clm_alpha = np.where(data["clm"] > 0, 1, np.nan)
        # draw contour around clouds
        ax.contour(
            data["clm"],
            levels=[0.5],
            colors="yellow",
            linewidths=0.5,
            alpha=1,
        )

    _, axes = plt.subplots(1, 2, figsize=(10, 5), sharey=True, sharex=True)
    plot_rgb_clm(raw, axes[0])
    axes[0].set_title("Raw Image")
    plot_rgb_clm(aligned, axes[1])
    axes[1].set_title("Aligned Image")
    plt.tight_layout()
