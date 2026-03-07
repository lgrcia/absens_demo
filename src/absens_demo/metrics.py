import numpy as np


def normalized_cross_correlation(img1, img2):
    img1_mean = np.mean(img1)
    img2_mean = np.mean(img2)

    numerator = np.sum((img1 - img1_mean) * (img2 - img2_mean))
    denominator = np.sqrt(
        np.sum((img1 - img1_mean) ** 2) * np.sum((img2 - img2_mean) ** 2)
    )

    return numerator / denominator


def nanncc(img1, img2):
    img1_mean = np.nanmean(img1)
    img2_mean = np.nanmean(img2)

    numerator = np.nansum((img1 - img1_mean) * (img2 - img2_mean))
    denominator = np.sqrt(
        np.nansum((img1 - img1_mean) ** 2) * np.nansum((img2 - img2_mean) ** 2)
    )

    return numerator / denominator


def mutual_information(img1, img2, bins=256, normalize=True):
    img1 = img1.ravel()
    img2 = img2.ravel()

    # Joint histogram
    joint_hist, _, _ = np.histogram2d(img1, img2, bins=bins)

    # Convert to probability
    joint_prob = joint_hist / np.sum(joint_hist)

    # Marginalisartion
    px = np.sum(joint_prob, axis=1)
    py = np.sum(joint_prob, axis=0)

    # Avoid log(0)
    nz = joint_prob > 0

    mi = np.sum(
        joint_prob[nz] * np.log(joint_prob[nz] / (px[:, None] * py[None, :])[nz])
    )

    if normalize:
        nz_x = px > 0
        nz_y = py > 0
        hx = -np.sum(px[nz_x] * np.log(px[nz_x]))
        hy = -np.sum(py[nz_y] * np.log(py[nz_y]))
        denom = hx + hy
        return mi / (denom / 2) if denom > 0 else 0.0

    return mi


def subpixel_peak(corr, peak):
    """
    Estimate subpixel shift using parabolic interpolation.

    corr: 2D cross-correlation array
    peak: (y, x) integer peak
    """

    y, x = peak
    h, w = corr.shape

    # wrap edges
    y0 = (y - 1) % h
    y1 = y
    y2 = (y + 1) % h

    x0 = (x - 1) % w
    x1 = x
    x2 = (x + 1) % w

    # 3x3 neighborhood
    window = corr[[y0, y1, y2]][:, [x0, x1, x2]]

    # subpixel formula: delta = (f(x-1)-f(x+1)) / (2*(f(x-1)-2f(x)+f(x+1)))
    def parabolic_offset(f):
        return 0.5 * (f[0] - f[2]) / (f[0] - 2 * f[1] + f[2] + 1e-12)

    dx = parabolic_offset(window[1, :])
    dy = parabolic_offset(window[:, 1])

    return y + dy, x + dx


def phase_correlation(img1, img2, subpixel=True):
    f1 = np.fft.fft2(img1 - img1.mean())
    f2 = np.fft.fft2(img2 - img2.mean())

    cps = f1 * np.conj(f2)
    cps /= np.abs(cps) + 1e-12

    corr = np.fft.ifft2(cps)
    corr = np.abs(corr)

    peak = np.unravel_index(np.argmax(corr), corr.shape)
    if subpixel:
        y_sub, x_sub = subpixel_peak(corr, peak)
    else:
        y_sub, x_sub = peak

    h, w = img1.shape

    # wrap around
    dy = y_sub if y_sub <= h // 2 else y_sub - h
    dx = x_sub if x_sub <= w // 2 else x_sub - w

    return np.linalg.norm([dy, dx])


# import numpy as np


# def _rank_normalize(img):
#     """Convert pixel values to rank positions, giving the image a uniform distribution.
#     Makes NCC invariant to any monotonic intensity transformation."""
#     flat = img.ravel().astype(float)
#     order = flat.argsort()
#     ranks = np.empty_like(order, dtype=float)
#     ranks[order] = np.arange(len(flat))
#     return ranks.reshape(img.shape)


# def _nan_rank_normalize(img):
#     """Rank-normalize ignoring NaNs; NaN positions remain NaN."""
#     flat = img.ravel().astype(float)
#     mask = ~np.isnan(flat)
#     order = flat[mask].argsort()
#     ranks_valid = np.empty_like(order, dtype=float)
#     ranks_valid[order] = np.arange(len(order))
#     ranked = np.full(len(flat), np.nan)
#     ranked[mask] = ranks_valid
#     return ranked.reshape(img.shape)


# def normalized_cross_correlation(img1, img2):
#     # Rank-normalize so the metric is invariant to any monotonic intensity
#     # transformation (gamma, contrast stretching, etc.), not just affine ones.
#     img1 = _rank_normalize(img1)
#     img2 = _rank_normalize(img2)

#     img1_mean = np.mean(img1)
#     img2_mean = np.mean(img2)

#     numerator = np.sum((img1 - img1_mean) * (img2 - img2_mean))
#     denominator = np.sqrt(
#         np.sum((img1 - img1_mean) ** 2) * np.sum((img2 - img2_mean) ** 2)
#     )

#     return np.clip(numerator / (denominator + 1e-12), -1.0, 1.0)


# def nanncc(img1, img2):
#     img1 = _nan_rank_normalize(img1)
#     img2 = _nan_rank_normalize(img2)

#     img1_mean = np.nanmean(img1)
#     img2_mean = np.nanmean(img2)

#     numerator = np.nansum((img1 - img1_mean) * (img2 - img2_mean))
#     denominator = np.sqrt(
#         np.nansum((img1 - img1_mean) ** 2) * np.nansum((img2 - img2_mean) ** 2)
#     )

#     return np.clip(numerator / (denominator + 1e-12), -1.0, 1.0)


# def mutual_information(img1, img2, bins=256, normalize=True):
#     img1 = img1.ravel()
#     img2 = img2.ravel()

#     # Joint histogram
#     joint_hist, _, _ = np.histogram2d(img1, img2, bins=bins)

#     # Convert to probability
#     joint_prob = joint_hist / np.sum(joint_hist)

#     # Marginalisartion
#     px = np.sum(joint_prob, axis=1)
#     py = np.sum(joint_prob, axis=0)

#     # Avoid log(0)
#     nz = joint_prob > 0

#     mi = np.sum(
#         joint_prob[nz] * np.log(joint_prob[nz] / (px[:, None] * py[None, :])[nz])
#     )

#     if normalize:
#         nz_x = px > 0
#         nz_y = py > 0
#         hx = -np.sum(px[nz_x] * np.log(px[nz_x]))
#         hy = -np.sum(py[nz_y] * np.log(py[nz_y]))
#         denom = hx + hy
#         return mi / (denom / 2) if denom > 0 else 0.0

#     return mi


# def subpixel_peak(corr, peak):
#     """
#     Estimate subpixel shift using parabolic interpolation.

#     corr: 2D cross-correlation array
#     peak: (y, x) integer peak
#     """

#     y, x = peak
#     h, w = corr.shape

#     # wrap edges
#     y0 = (y - 1) % h
#     y1 = y
#     y2 = (y + 1) % h

#     x0 = (x - 1) % w
#     x1 = x
#     x2 = (x + 1) % w

#     # 3x3 neighborhood
#     window = corr[[y0, y1, y2]][:, [x0, x1, x2]]

#     # subpixel formula: delta = (f(x-1)-f(x+1)) / (2*(f(x-1)-2f(x)+f(x+1)))
#     def parabolic_offset(f):
#         return 0.5 * (f[0] - f[2]) / (f[0] - 2 * f[1] + f[2] + 1e-12)

#     dx = parabolic_offset(window[1, :])
#     dy = parabolic_offset(window[:, 1])

#     return y + dy, x + dx


# def phase_correlation(img1, img2, subpixel=True):
#     f1 = np.fft.fft2(img1 - img1.mean())
#     f2 = np.fft.fft2(img2 - img2.mean())

#     cps = f1 * np.conj(f2)
#     cps /= np.abs(cps) + 1e-12

#     corr = np.fft.ifft2(cps)
#     corr = np.abs(corr)

#     peak = np.unravel_index(np.argmax(corr), corr.shape)
#     if subpixel:
#         y_sub, x_sub = subpixel_peak(corr, peak)
#     else:
#         y_sub, x_sub = peak

#     h, w = img1.shape

#     # wrap around
#     dy = y_sub if y_sub <= h // 2 else y_sub - h
#     dx = x_sub if x_sub <= w // 2 else x_sub - w

#     return np.linalg.norm([dy, dx])
