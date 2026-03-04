import argparse
import tempfile
from pathlib import Path

from absens_demo import main


def parse_args():
    """Parse command-line arguments for the absens-demo CLI.

    Returns:
        argparse.Namespace: Parsed arguments with attributes:
            - bbox (list[float]): Bounding box [min_lon, min_lat, max_lon, max_lat].
            - start_date (str): Start date in YYYY-MM-DD format.
            - months (int): Number of months to cover.
            - folder (Path | None): Directory to store downloaded data.
            - output (str): Output GIF/video file path.
    """
    parser = argparse.ArgumentParser(
        description="Download satellite imagery for a bounding box and create a video."
    )
    parser.add_argument(
        "--bbox",
        type=float,
        nargs=4,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        required=True,
        help="Bounding box as: min_lon min_lat max_lon max_lat",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2020-01-01",
        help="Start date in YYYY-MM-DD format (default: 2020-01-01)",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=30,
        help="Number of months to cover (default: 30)",
    )
    parser.add_argument(
        "--folder",
        type=Path,
        default=None,
        help="Directory to store downloaded data (default: a temporary folder)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output.gif",
        help="Output video/gif file path (default: output.gif)",
    )
    return parser.parse_args()


def run():
    """Entry point for the absens-demo CLI.

    Parses arguments, downloads and aligns monthly satellite images for the
    specified bounding box, then renders the output GIF/video.
    """
    args = parse_args()
    if args.folder is None:
        folder = Path(tempfile.mkdtemp())
        print(f"No folder specified, using temporary folder: {folder}")
    else:
        folder = args.folder
    data_folder = main.download_and_align(
        args.bbox, args.start_date, args.months, folder
    )
    main.make_video(data_folder, args.output, bbox=args.bbox)
    print(f"Video saved to {args.output}")


if __name__ == "__main__":
    run()
