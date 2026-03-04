import numpy as np
from skimage.filters import gaussian

from absens_demo.utils import monthly_iso_start_end
from absens_demo.alignment import edge_detection, find_translation, wrap_image


def _sinusoidal_image(size=200):
    """Return a structured float32 image with strong gradients suitable for ECC.

    ECC needs coherent gradient signal — sinusoidal patterns work well.
    We return a larger canvas so tests can extract overlapping patches without
    introducing zero borders from warpAffine.
    """
    y, x = np.mgrid[0:size, 0:size]
    return (np.sin(x * 0.2) * np.cos(y * 0.15)).astype(np.float32)


# ---------------------------------------------------------------------------
# monthly_iso_start_end
# ---------------------------------------------------------------------------


def test_monthly_iso_start_end_length():
    """Output list has exactly `months` entries."""
    for months in (1, 3, 12):
        result = monthly_iso_start_end("2023-01-01", months)
        assert len(result) == months


def test_monthly_iso_start_end_iso_format():
    """Every interval string is an ISO datetime ending with 'Z'."""
    result = monthly_iso_start_end("2023-06-15", 3)
    for start, end in result:
        assert start.endswith("Z"), f"{start!r} should end with 'Z'"
        assert end.endswith("Z"), f"{end!r} should end with 'Z'"
        assert "T" in start
        assert "T" in end
        assert end > start  # end is after start


# ---------------------------------------------------------------------------
# edge_detection
# ---------------------------------------------------------------------------


def test_edge_detection_preserves_shape():
    """Sobel edge detection returns an array with the same spatial shape."""
    image = np.random.default_rng(0).random((64, 64))
    result = edge_detection(image)
    assert result.shape == image.shape


# ---------------------------------------------------------------------------
# wrap_image
# ---------------------------------------------------------------------------


def test_wrap_image_preserves_shape():
    """wrap_image returns an array with the same shape as the input."""
    rng = np.random.default_rng(1)
    image = rng.random((50, 50)).astype(np.float32)
    wrapped = wrap_image(image, translation=np.array([5.0, 3.0]))
    assert wrapped.shape == image.shape


# ---------------------------------------------------------------------------
# find_translation
# ---------------------------------------------------------------------------


def test_find_translation_recovers_known_shift():
    """find_translation recovers a known pixel shift to within 0.1 px.

    ECC needs coherent gradient signal. We use a sinusoidal image and extract
    overlapping patches from a larger canvas to avoid zero-border artifacts.
    ECC returns the *negative* of the applied shift (it finds the inverse warp).
    """
    large = _sinusoidal_image()
    sz, tx, ty = 128, 5, 3
    im0 = large[:sz, :sz].copy()
    im1 = large[ty : sz + ty, tx : sz + tx].copy()  # shifted right/down by (tx,ty)

    translation = find_translation(im0, im1)

    np.testing.assert_allclose(translation, [-tx, -ty], atol=0.1)


def test_wrap_then_find_translation_roundtrip():
    """Applying find_translation + wrap_image realigns a shifted image to the original.

    Workflow: shift im0 → get translation → wrap im1 by that translation → compare.
    The interior of the corrected image should match im0 (borders are excluded since
    warpAffine fills out-of-bounds pixels with zeros).
    """
    large = _sinusoidal_image()
    sz, tx, ty = 128, 4, 3
    im0 = large[:sz, :sz].copy()
    im1 = large[ty : sz + ty, tx : sz + tx].copy()

    translation = find_translation(im0, im1)       # ≈ [-tx, -ty]
    im1_corrected = wrap_image(im1, translation)   # shift im1 back toward im0

    # Compare the interior, away from the zero-padded border introduced by warpAffine
    pad = max(tx, ty) + 2
    np.testing.assert_allclose(
        im1_corrected[pad:-pad, pad:-pad],
        im0[pad:-pad, pad:-pad],
        atol=0.05,
    )
