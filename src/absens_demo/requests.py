from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from requests_toolbelt.multipart.decoder import MultipartDecoder
from PIL import Image
import io
import numpy as np
import logging
import os
import json

logger = logging.getLogger(__name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
COLLECTION_ID = "sentinel-2-l2a"


def _base_json_request_with_clm(start_iso, end_iso, bbox):
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
            "width": 1024,
            "height": 1024,
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
