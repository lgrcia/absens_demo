import io
import json
import logging
import os

import numpy as np
from oauthlib.oauth2 import BackendApplicationClient
from PIL import Image
from requests_oauthlib import OAuth2Session
from requests_toolbelt.multipart.decoder import MultipartDecoder

import io
from datetime import datetime
from pathlib import Path

import numpy as np
from tqdm import tqdm

from absens_demo import utils, io as absens_io
from dateutil.relativedelta import relativedelta


logger = logging.getLogger(__name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
COLLECTION_ID = "sentinel-2-l2a"


def _base_json_request_with_clm(start_iso, end_iso, bbox):
    """Build the base JSON request body for Sentinel Hub Process API with CLM output.

    Args:
        start_iso (str): Start datetime in ISO 8601 format (e.g. "2020-01-01T00:00:00Z").
        end_iso (str): End datetime in ISO 8601 format.
        bbox (list[float]): Bounding box as [west, south, east, north] in WGS84.

    Returns:
        dict: JSON request body with bounds, data filter, and dual output (image + cloud mask).
    """
    return {
        "input": {
            "bounds": {
                "bbox": bbox,
                "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"},
            },
            "data": [
                {
                    "type": "S2L2A",
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{start_iso}",
                            "to": f"{end_iso}",
                        },
                        "mosaickingOrder": "leastCC",
                    },
                }
            ],
        },
        "output": {
            "width": (bbox[2] - bbox[0]) * 10000,
            "height": (bbox[3] - bbox[1]) * 10000,
            "responses": [
                {
                    "identifier": "default",
                    "format": {
                        "type": "image/jpeg",
                    },
                },
                {
                    "identifier": "clm",
                    "format": {
                        "type": "image/png",
                    },
                },
            ],
        },
        "evalscript": None,
    }


client = BackendApplicationClient(client_id=CLIENT_ID)
oauth = OAuth2Session(client=client)

token = oauth.fetch_token(
    token_url="https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token",
    client_secret=CLIENT_SECRET,
    include_client_id=True,
)

headers_request = {"Authorization": "Bearer %s" % token["access_token"]}


def get_datetimes(start_date: str, end_date: str, bbox: list[float]) -> list[str]:
    """Query the Sentinel Hub Catalog API for available scene datetimes.

    Args:
        start_date (str): Start date in YYYY-MM-DD format.
        end_date (str): End date in YYYY-MM-DD format.
        bbox (list[float]): Bounding box as [west, south, east, north] in WGS84.

    Returns:
        list[str]: ISO 8601 datetime strings for each available scene.
    """
    CATALOG_URL = "https://services.sentinel-hub.com/api/v1/catalog/1.0.0/search"

    json_request = {
        "collections": [COLLECTION_ID],
        "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
        "bbox": bbox,
        "limit": 100,
    }

    response = oauth.request(
        "POST", CATALOG_URL, headers=headers_request, json=json_request
    )
    response_json = json.loads(response.content)
    datetimes = [f["properties"]["datetime"] for f in response_json["features"]]
    return datetimes


def get_rgb_image(start_iso, end_iso, bbox):
    """
    Get an image for a given datetime and bounding box.

    Handles repsonse status 429 (Too Many Requests) by retrying the request after a 1 min delay.

    Args:
        iso_datetime (datetime): The datetime for which to get the image.
        bbox (list): The bounding box for which to get the image.

    Returns:
        tuple[np.array, np.array]: The RGB image and cloud mask as numpy arrays.

    Raises:
        Exception: If the request fails with a status code other than 200 or 429.
    """
    evalscript = """
    //VERSION=3

    function setup() {
    return {
        input: ["B02", "B03", "B04", "CLM"],
        output: [{ id: 'default', bands: 3 }, {id:'clm', bands: 1, sampleType: "UINT8" }]
    };
    }

    function evaluatePixel(sample) {
    return {
        default: [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02],
        clm: [sample.CLM]
        };
    }
    """

    if isinstance(bbox, np.ndarray):
        bbox = bbox.tolist()

    json_request = _base_json_request_with_clm(start_iso, end_iso, bbox)
    json_request["evalscript"] = evalscript

    url_request = "https://services.sentinel-hub.com/api/v1/process"
    headers = {
        "Authorization": "Bearer %s" % token["access_token"],
        "Content-Type": "application/json",
        "Accept": "multipart/mixed",
    }

    response = oauth.request("POST", url_request, headers=headers, json=json_request)

    decoder = MultipartDecoder.from_response(response)

    return {
        "rgb": np.array(Image.open(io.BytesIO(decoder.parts[0].content))),
        "clm": np.array(Image.open(io.BytesIO(decoder.parts[1].content))),
    }


def get_b8_image(start_iso, end_iso, bbox):
    """Fetch the near-infrared (B08) band image and cloud mask from Sentinel Hub.

    Args:
        start_iso (str): Start datetime in ISO 8601 format.
        end_iso (str): End datetime in ISO 8601 format.
        bbox (list[float]): Bounding box as [west, south, east, north] in WGS84.

    Returns:
        dict: A dictionary with keys:
            - "b8" (np.ndarray): Near-infrared band image as a numpy array.
            - "clm" (np.ndarray): Cloud mask as a numpy array.
    """
    evalscript = """
    //VERSION=3

    function setup() {
    return {
        input: ["B08", "CLM"],
        output: [{ id: 'default', bands: 1 }, {id:'clm', bands: 1, sampleType: "UINT8" }]
    };
    }

    function evaluatePixel(sample) {
    return {
        default: [2.5 * sample.B08, 2.5],
        clm: [sample.CLM]
        };
    }
    """

    json_request = _base_json_request_with_clm(start_iso, end_iso, bbox)
    json_request["evalscript"] = evalscript

    url_request = "https://services.sentinel-hub.com/api/v1/process"
    headers = {
        "Authorization": "Bearer %s" % token["access_token"],
        "Content-Type": "application/json",
        "Accept": "multipart/mixed",
    }

    response = oauth.request("POST", url_request, headers=headers, json=json_request)

    decoder = MultipartDecoder.from_response(response)

    return {
        "b8": np.array(Image.open(io.BytesIO(decoder.parts[0].content))),
        "clm": np.array(Image.open(io.BytesIO(decoder.parts[1].content))),
    }


def download_monthly_images(
    bbox: list[float], start_date: str, months: int, destination: Path
):
    """Download monthly satellite images for a given bounding box and time range.

    For each monthly interval, fetches RGB + cloud mask (CLM) data from Sentinel Hub
    and saves the raw images as .npz files in the specified destination folder.

    Args:
        bbox (list[float]): Bounding box as [west, south, east, north] in WGS84.
        start_date (str): Start date in YYYY-MM-DD format.
        months (int): Number of monthly intervals to process.
        destination (Path): Output directory where "raw/" subfolder will be created.

    Returns:
        Path: Path to the destination folder
    """
    start_date_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_datetime = start_date_datetime + relativedelta(months=months)
    iso_datetimes = (
        start_date_datetime.isoformat() + "Z",
        end_date_datetime.isoformat() + "Z",
    )

    bbox_string = "_".join(map(str, bbox))
    base_folder = destination / bbox_string
    raw_folder = base_folder / "raw"
    raw_folder.mkdir(exist_ok=True, parents=True)

    iso_datetimes = utils.monthly_iso_start_end(start_date, months)

    for start_iso, end_iso in tqdm(iso_datetimes, desc="Downloading images"):
        output_file = raw_folder / f"{start_iso}_{end_iso}.npz"

        if Path(output_file).exists():
            continue

        im_data = absens_io.get_rgb_image(start_iso, end_iso, bbox)
        absens_io.save_npy(im_data, output_file)

    return raw_folder
