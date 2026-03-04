import io
from unittest.mock import MagicMock, patch

import numpy as np
from PIL import Image

import absens_demo.requests as req_module
from absens_demo.requests import get_rgb_image


def _jpeg_bytes(h=8, w=8):
    buf = io.BytesIO()
    Image.fromarray(np.zeros((h, w, 3), dtype=np.uint8)).save(buf, format="JPEG")
    return buf.getvalue()


def _png_bytes(h=8, w=8):
    buf = io.BytesIO()
    Image.fromarray(np.zeros((h, w), dtype=np.uint8)).save(buf, format="PNG")
    return buf.getvalue()


def test_get_rgb_image_returns_rgb_and_clm_arrays():
    """get_rgb_image returns a dict with 'rgb' and 'clm' numpy arrays on success.
    This test is not extremely relevant. In a production environment I would rather
    use an actual authentication with a known test image.
    """
    rgb_bytes = _jpeg_bytes()
    clm_bytes = _png_bytes()

    mock_part_rgb = MagicMock()
    mock_part_rgb.content = rgb_bytes
    mock_part_clm = MagicMock()
    mock_part_clm.content = clm_bytes

    mock_decoder = MagicMock()
    mock_decoder.parts = [mock_part_rgb, mock_part_clm]

    mock_response = MagicMock()
    mock_response.status_code = 200

    with (
        patch.object(req_module, "oauth") as mock_oauth,
        patch("absens_demo.requests.MultipartDecoder") as mock_decoder_class,
    ):
        mock_oauth.request.return_value = mock_response
        mock_decoder_class.from_response.return_value = mock_decoder

        result = get_rgb_image(
            "2023-01-01T00:00:00Z", "2023-02-01T00:00:00Z", [0.0, 0.0, 1.0, 1.0]
        )

    assert set(result.keys()) == {"rgb", "clm"}
    assert isinstance(result["rgb"], np.ndarray)
    assert isinstance(result["clm"], np.ndarray)
    assert result["rgb"].ndim == 3  # H x W x 3
    assert result["clm"].ndim == 2  # H x W
