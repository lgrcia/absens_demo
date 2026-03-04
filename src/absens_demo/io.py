import numpy as np
import logging
from pathlib import Path

from .requests import get_rgb_image
from .utils import monthly_iso_start_end

logger = logging.getLogger(__name__)


def save_npy(data: dict, path: Path) -> None:
    """
    Save a numpy array as a .npy file.

    Args:
        image (np.array): The image to save.
        path (Path): The path to save the image to.
    """
    np.savez(
        path,
        rgb=data["rgb"],
        clm=data["clm"],
    )


def load_npy(path: Path) -> dict:
    """
    Load a .npy file as a numpy array.

    Args:
        path (Path): The path to the .npy file to load.
    Returns:
        dict: A dictionary containing the RGB image and cloud mask as numpy arrays.
    """
    data = np.load(path, allow_pickle=True)
    return {
        "rgb": data["rgb"],
        "clm": data["clm"],
    }


def download_monthly_images(
    start_date: str, months: int, bbox: list[float], output_folder: Path
) -> int:
    output_folder.mkdir(parents=True, exist_ok=True)
    iso_start_end = monthly_iso_start_end(start_date, months=months)
    count = 0
    for start, end in iso_start_end:
        file_stem = f"{start}-{end}"
        if (output_folder / f"{file_stem}").exists():
            logger.info(f"Image for datetime: {file_stem} already exists. Skipping...")
            continue

        logger.info(f"Getting image for datetime: {file_stem}...")
        im = get_rgb_image(start, end, bbox)
        save_npy(im, output_folder / f"{file_stem}")
        count += 1
    return count
