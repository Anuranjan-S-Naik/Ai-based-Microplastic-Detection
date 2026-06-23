"""Estimate microns-per-pixel from the spiked dataset.

The spiked images contain reference particles of known size (HDPE ~500 um,
PET ~120 um). We use the ground-truth spiked masks: the largest particles
correspond to the 500 um HDPE pieces, so

    um_per_pixel = HDPE_REF_UM / (median major-axis of the largest particles)

This is magnification-specific (it is valid for images taken at the spiked
set's magnification). For other magnifications pass --um-per-pixel explicitly.
"""
from __future__ import annotations

import glob
import os
from typing import Optional

import cv2
import numpy as np

from . import config


def _foreground_from_mask(mask_gray: np.ndarray) -> np.ndarray:
    """Return a uint8 binary image where plastic == 255.

    Ground-truth spiked/clam masks store plastic as the MINORITY colour
    (black on white). Detect whichever colour is the minority as foreground.
    """
    white = int((mask_gray > 127).sum())
    black = int((mask_gray <= 127).sum())
    if white <= black:
        fg = (mask_gray > 127)
    else:
        fg = (mask_gray <= 127)
    return (fg.astype(np.uint8)) * 255


def _major_axes(binary: np.ndarray) -> list[float]:
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    axes = []
    for cnt in contours:
        if cv2.contourArea(cnt) < config.MIN_PARTICLE_AREA_PX:
            continue
        if len(cnt) >= 5:
            (_, _), (a1, a2), _ = cv2.fitEllipse(cnt)
            axes.append(max(a1, a2))
        else:
            x, y, w, h = cv2.boundingRect(cnt)
            axes.append(float(max(w, h)))
    return axes


def estimate_um_per_pixel(
    mask_dir: str = config.SPIKED_MASK_DIR,
    ref_um: float = config.HDPE_REF_UM,
    top_n: int = 3,
) -> Optional[float]:
    """Estimate um/pixel by matching the largest particles to ref_um.

    The HDPE reference pieces (~500 um) are the largest objects in the spiked
    set, so we take the median major-axis of the top_n largest particles found
    across all spiked masks and equate it to ref_um. Using a small group of the
    biggest particles (rather than a percentile of all of them) keeps the
    estimate from being dragged down by the many small PET/noise specks.

    Returns None if no usable particles are found.
    """
    paths = sorted(glob.glob(os.path.join(mask_dir, "*")))
    all_axes: list[float] = []
    for p in paths:
        m = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
        if m is None:
            continue
        all_axes.extend(_major_axes(_foreground_from_mask(m)))

    if not all_axes:
        return None

    axes = sorted(all_axes, reverse=True)
    n_top = max(1, min(top_n, len(axes)))
    largest_median_px = float(np.median(axes[:n_top]))
    if largest_median_px <= 0:
        return None
    return ref_um / largest_median_px


def resolve_um_per_pixel(cli_value: Optional[float], auto: bool) -> Optional[float]:
    """Pick the calibration value to use.

    Precedence: explicit CLI value > auto-estimate from spiked set >
    config default (may be None -> report in pixels).
    """
    if cli_value is not None:
        return cli_value
    if auto:
        est = estimate_um_per_pixel()
        if est is not None:
            return est
    return config.DEFAULT_UM_PER_PIXEL


if __name__ == "__main__":
    val = estimate_um_per_pixel()
    if val is None:
        print("Could not estimate calibration.")
    else:
        print(f"Estimated um_per_pixel = {val:.4f}  "
              f"(=> 1 px = {val:.2f} um, HDPE ref = {config.HDPE_REF_UM} um)")
