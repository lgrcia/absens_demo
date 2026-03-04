from absens_demo import requests, utils, viz, io as absens_io, alignment
from datetime import datetime, timedelta
from pathlib import Path
from tqdm import tqdm
import numpy as np
import cv2
import io
import imageio
import matplotlib.pyplot as plt


def download_and_align(bbox, start_date, months, destination: Path):
    start_date_datetime = datetime.strptime(start_date, "%Y-%m-%d")

    # add the number of months to the start date
    end_date_datetime = start_date_datetime + timedelta(days=30 * months)
    # iso datetimes to utc format
    iso_datetimes = (
        start_date_datetime.isoformat() + "Z",
        end_date_datetime.isoformat() + "Z",
    )

    bbox_string = "_".join(map(str, bbox))
    base_folder = destination / bbox_string
    base_folder.mkdir(exist_ok=True, parents=True)

    # collect images for each month
    iso_datetimes = utils.monthly_iso_start_end(start_date, months)
    # folder with joined bbox
    bbox_string = "_".join(map(str, bbox))
    raw_folder = base_folder / "raw"
    raw_folder.mkdir(exist_ok=True, parents=True)

    for start_iso, end_iso in tqdm(iso_datetimes, desc="Downloading images"):
        output_file = raw_folder / f"{start_iso}_{end_iso}.npz"

        if Path(output_file).exists():
            continue

        im_data = absens_io.get_rgb_image(start_iso, end_iso, bbox)
        absens_io.save_npy(im_data, output_file)

    reference_image = requests.get_rgb_image(
        "2020-01-01T00:00:00Z", "2024-01-01T00:00:00Z", bbox
    )

    ref_edges = alignment.edge_detection(reference_image["rgb"].mean(-1))
    aligned_folder = base_folder / "aligned"
    aligned_folder.mkdir(exist_ok=True, parents=True)

    images = sorted(raw_folder.glob("*.npz"))

    for im in tqdm(images, desc="Aligning images"):
        rgb = absens_io.load_npy(im)["rgb"]
        clm = absens_io.load_npy(im)["clm"]
        mean_rgb = rgb.mean(-1)
        edges = alignment.edge_detection(mean_rgb)
        try:
            translation = alignment.find_translation(ref_edges, edges)
            wrapped_rgb = alignment.wrap_image(rgb, translation)
            # convert to uint8
            wrapped_rgb = np.clip(wrapped_rgb, 0, 255).astype(np.uint8)
            wrapped_clm = alignment.wrap_image(clm, translation)
            wrapped_clm = np.clip(wrapped_clm, 0, 255).astype(np.uint8)

        except cv2.error as e:
            wrapped_rgb = rgb
            wrapped_clm = clm

        np.savez(
            aligned_folder / im.name,
            rgb=wrapped_rgb,
            clm=wrapped_clm,
        )

    return base_folder


def make_video(folder: Path, output):
    writer = imageio.get_writer(
        output,
        mode="I",
        fps=10,
    )

    raw_folder = folder / "raw"
    aligned_folder = folder / "aligned"

    images = sorted(raw_folder.glob("*.npz"))

    for im in tqdm(images, desc="Making video"):
        im_raw = absens_io.load_npy(im)
        im_aligned = absens_io.load_npy(aligned_folder / im.name)
        viz.plot_function(im_raw, im_aligned)
        buf = io.BytesIO()
        plt.savefig(buf)
        writer.append_data(imageio.imread(buf))
        plt.close()

    writer.close()
