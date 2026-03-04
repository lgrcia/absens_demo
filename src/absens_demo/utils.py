from datetime import datetime, timedelta
from skimage import filters
import numpy as np
import cv2


def monthly_iso_start_end(start_date: str, months: int) -> list[tuple[str, str]]:
    start_datetime: datetime = datetime.strptime(start_date, "%Y-%m-%d")

    iso_start_end = [
        (
            (start_datetime + timedelta(days=i * months)).isoformat() + "Z",
            (start_datetime + timedelta(days=(i + 1) * months)).isoformat() + "Z",
        )
        for i in range(months)
    ]
    return iso_start_end


def edge_detection(image):
    return filters.sobel(image)


def find_translation(im0, im1):
    # use findTransformECC from opencv
    # convert to float32
    im0 = im0.astype(np.float32)
    im1 = im1.astype(np.float32)
    # find translation
    warp_matrix = np.eye(2, 3, dtype=np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-6)
    cc, warp_matrix = cv2.findTransformECC(
        im0, im1, warp_matrix, cv2.MOTION_TRANSLATION, criteria
    )
    return warp_matrix[:2, 2]


def wrap_image(im, translation):
    import cv2

    # convert to float32
    im = im.astype(np.float32)
    # wrap image
    warp_matrix = np.eye(2, 3, dtype=np.float32)
    warp_matrix[:2, 2] = translation
    wrapped_im = cv2.warpAffine(
        im,
        warp_matrix,
        (im.shape[1], im.shape[0]),
        flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
    )
    return wrapped_im
