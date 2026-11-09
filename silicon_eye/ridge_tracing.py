"""Fixed CPU ridge tracer used by the metal extent batch; requires scipy."""

import numpy as np
from scipy.ndimage import gaussian_filter, maximum_filter1d

DEFAULTS = dict(
    step_x=4,
    sigma_y=1.0,
    sigma_x=3.0,
    background_sigma_y=6.0,
    max_dy=3,
    movement_penalty=0.3,
    unknown_ridge_threshold=0.12,
)


def trace(gray, seeds, x_start, x_end):
    """Trace fixed bright-ridge paths; unsupported gaps fail instead of being bridged."""
    if (gray.ndim != 2 or not seeds or not 0 <= x_start < x_end < gray.shape[1]
            or any(type(s) is not int or not 0 <= s < gray.shape[0] for s in seeds)):
        raise ValueError("Invalid ridge image, seeds or x range")
    smooth = gaussian_filter(gray.astype(float), (DEFAULTS["sigma_y"], DEFAULTS["sigma_x"]))
    ridge = smooth - gaussian_filter(smooth, (DEFAULTS["background_sigma_y"], 0))
    scale = max(float(np.percentile(np.abs(ridge), 95)), 1.0)
    ridge = ridge / scale
    xs = np.arange(x_start, x_end + 1, DEFAULTS["step_x"])
    if xs[-1] != x_end:
        xs = np.append(xs, x_end)
    height = gray.shape[0]
    peaks = (ridge == maximum_filter1d(ridge, size=5, axis=0)) & (ridge > 0.12)
    allowed = maximum_filter1d(peaks.astype(int), size=3, axis=0).astype(bool)
    tracks = []
    for sy in seeds:
        score = np.full(height, -1e20)
        score[sy] = 0
        parents = np.zeros((len(xs), height), dtype=np.int16)
        ys_all = np.arange(height)
        for k, x in enumerate(xs[1:], 1):
            offsets = np.arange(-DEFAULTS["max_dy"], DEFAULTS["max_dy"] + 1)
            choices = np.full((len(offsets), height), -1e20)
            for j, delta in enumerate(offsets):
                prev = ys_all + delta
                valid = (prev >= 0) & (prev < height)
                choices[j, valid] = score[prev[valid]] - DEFAULTS["movement_penalty"] * abs(delta)
            best = np.argmax(choices, axis=0)
            parents[k] = np.clip(ys_all + offsets[best], 0, height - 1)
            score = choices[best, ys_all] + ridge[:, x]
            score[~allowed[:, x]] = -1e20
            if score.max() < -1e10:
                raise RuntimeError(f"No supported ridge path for seed {sy}, x={x}")
        ys = np.zeros(len(xs), dtype=int)
        ys[-1] = np.argmax(score)
        for k in range(len(xs) - 1, 0, -1):
            ys[k - 1] = parents[k, ys[k]]
        values = ridge[ys, xs]
        low = values < DEFAULTS["unknown_ridge_threshold"]
        spans = []
        start = None
        for k, bad in enumerate(np.r_[low, False]):
            if bad and start is None:
                start = k
            if not bad and start is not None:
                spans.append([int(xs[start]), int(xs[k - 1])])
                start = None
        tracks.append(
            dict(
                points=np.column_stack((xs, ys)).tolist(),
                unknown_spans=spans,
                ridge_min=float(values.min()),
                ridge_median=float(np.median(values)),
            )
        )
    return tracks

