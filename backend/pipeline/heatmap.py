"""Spatial density heatmap via kernel density estimation (KDE).

Given the list of detected particles (with centroids), this module uses
scipy's Gaussian KDE to estimate a continuous density surface, then renders
it as a color-mapped overlay blended onto the original microscope image.

The result highlights *where* contamination clusters — going beyond simple
counts into spatial ecology-grade analysis.
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

import cv2
import numpy as np

from .analyzer import Particle

# ---------------------------------------------------------------------------
# Attempt scipy import; fall back gracefully so the rest of the pipeline
# still works if scipy is missing (heatmap just won't be generated).
# ---------------------------------------------------------------------------
try:
    from scipy.stats import gaussian_kde
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def can_generate(particles: List[Particle]) -> bool:
    """Return True if we have enough particles to build a meaningful KDE.

    KDE needs at least 3 non-coincident points; with fewer we'd just get
    a single blob or a degenerate bandwidth.
    """
    if not HAS_SCIPY:
        return False
    if len(particles) < 3:
        return False
    # Check that centroids aren't all identical (would crash KDE).
    xs = {round(p.centroid[0], 1) for p in particles}
    ys = {round(p.centroid[1], 1) for p in particles}
    return len(xs) > 1 and len(ys) > 1


def generate(
    image_rgb: np.ndarray,
    particles: List[Particle],
    *,
    colormap: int = cv2.COLORMAP_JET,
    alpha: float = 0.55,
    grid_resolution: int = 300,
) -> Tuple[np.ndarray, dict]:
    """Build a KDE heatmap and blend it onto the original image.

    Parameters
    ----------
    image_rgb : HxWx3 uint8 RGB image (the original microscope input).
    particles : list of Particle dataclasses (must have .centroid).
    colormap  : OpenCV colormap constant (default JET — blue→green→red).
    alpha     : blending weight for the heatmap layer (0 = invisible, 1 = opaque).
    grid_resolution : number of points along the longer axis for KDE eval grid.
                      Higher = smoother but slower. 300 is a good balance.

    Returns
    -------
    (overlay_bgr, hotspot_stats)

    overlay_bgr : HxWx3 uint8 BGR image (the blended heatmap).
    hotspot_stats : dict with keys:
        - peak_x, peak_y : pixel coords of the highest-density point
        - peak_density   : the density value at the peak (arbitrary units)
        - n_clusters     : rough cluster count (local maxima in the density)
    """
    h, w = image_rgb.shape[:2]

    # Collect centroids.
    xs = np.array([p.centroid[0] for p in particles], dtype=np.float64)
    ys = np.array([p.centroid[1] for p in particles], dtype=np.float64)

    # Fit KDE on the (x, y) centroid cloud.
    data = np.vstack([xs, ys])   # shape (2, N)
    kde = gaussian_kde(data, bw_method="scott")

    # Evaluate on a grid that spans the image.
    aspect = w / h
    if w >= h:
        nx = grid_resolution
        ny = max(2, int(grid_resolution / aspect))
    else:
        ny = grid_resolution
        nx = max(2, int(grid_resolution * aspect))

    gx = np.linspace(0, w, nx)
    gy = np.linspace(0, h, ny)
    gxx, gyy = np.meshgrid(gx, gy)
    grid_points = np.vstack([gxx.ravel(), gyy.ravel()])   # (2, nx*ny)
    density = kde(grid_points).reshape(ny, nx)             # (ny, nx)

    # Normalize to 0-255.
    d_min, d_max = density.min(), density.max()
    if d_max - d_min < 1e-12:
        normed = np.zeros_like(density, dtype=np.uint8)
    else:
        normed = ((density - d_min) / (d_max - d_min) * 255).astype(np.uint8)

    # Resize to full image dimensions.
    heat_gray = cv2.resize(normed, (w, h), interpolation=cv2.INTER_CUBIC)

    # Apply colormap → BGR.
    heat_color = cv2.applyColorMap(heat_gray, colormap)

    # Build an alpha mask: areas with very low density are nearly transparent,
    # so the original image shows through in empty regions.
    # We use the normalized gray as the per-pixel alpha channel.
    alpha_mask = heat_gray.astype(np.float32) / 255.0
    # Apply a power curve to push low values further toward transparent.
    alpha_mask = np.power(alpha_mask, 1.5) * alpha
    alpha_3ch = np.stack([alpha_mask] * 3, axis=-1)

    # Blend: result = heat * alpha + original * (1 - alpha).
    original_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR).astype(np.float32)
    blended = heat_color.astype(np.float32) * alpha_3ch + original_bgr * (1.0 - alpha_3ch)
    blended = np.clip(blended, 0, 255).astype(np.uint8)

    # Draw a banner.
    _draw_heatmap_banner(blended)

    # Draw a simple color bar legend.
    _draw_colorbar(blended, colormap)

    # Compute hotspot stats.
    peak_idx = np.unravel_index(np.argmax(density), density.shape)
    peak_y_grid = gy[peak_idx[0]]
    peak_x_grid = gx[peak_idx[1]]

    n_clusters = _count_local_maxima(density)

    hotspot_stats = {
        "peak_x": round(float(peak_x_grid), 1),
        "peak_y": round(float(peak_y_grid), 1),
        "peak_density": round(float(density[peak_idx]), 6),
        "n_clusters": n_clusters,
    }

    return blended, hotspot_stats


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _draw_heatmap_banner(img: np.ndarray) -> None:
    """Draw a title banner at the top of the heatmap image."""
    h, w = img.shape[:2]
    cv2.rectangle(img, (0, 0), (w, 40), (20, 20, 20), -1)
    cv2.putText(img, "SPATIAL DENSITY HEATMAP", (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 220, 255), 2, cv2.LINE_AA)


def _draw_colorbar(img: np.ndarray, colormap: int, bar_width: int = 20,
                   margin: int = 15) -> None:
    """Draw a vertical color bar on the right edge of the image."""
    h, w = img.shape[:2]
    bar_height = min(200, h - 100)
    if bar_height < 40:
        return

    x0 = w - margin - bar_width
    y0 = 50
    y1 = y0 + bar_height

    # Build the gradient strip.
    grad = np.linspace(255, 0, bar_height).astype(np.uint8).reshape(-1, 1)
    grad = np.repeat(grad, bar_width, axis=1)
    grad_color = cv2.applyColorMap(grad, colormap)

    # Paste into the image.
    img[y0:y1, x0:x0 + bar_width] = grad_color

    # Border.
    cv2.rectangle(img, (x0 - 1, y0 - 1), (x0 + bar_width, y1), (200, 200, 200), 1)

    # Labels.
    cv2.putText(img, "High", (x0 - 4, y0 - 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1, cv2.LINE_AA)
    cv2.putText(img, "Low", (x0, y1 + 16),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1, cv2.LINE_AA)


def _count_local_maxima(density: np.ndarray, threshold_frac: float = 0.3) -> int:
    """Count approximate cluster centres as local maxima in the density grid.

    Uses OpenCV dilation to find local peaks, then filters by a threshold
    fraction of the global maximum.
    """
    d_max = density.max()
    if d_max < 1e-12:
        return 0

    # Normalize to uint8 for morphological ops.
    normed = ((density / d_max) * 255).astype(np.uint8)

    # Dilate to find local maxima.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    dilated = cv2.dilate(normed, kernel)
    local_max_mask = (normed == dilated) & (normed > int(threshold_frac * 255))

    # Count connected components as clusters.
    n_labels, _ = cv2.connectedComponents(local_max_mask.astype(np.uint8))
    return max(0, n_labels - 1)  # subtract the background label
