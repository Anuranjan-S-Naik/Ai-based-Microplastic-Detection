"""OpenCV / scikit-image particle analysis layer.

Takes the binary mask from the segmenter and extracts per-particle morphology:
area, perimeter, major/minor axis, aspect ratio, circularity, solidity, extent
and equivalent diameter. This is the value-add on top of the binary MP-Net
model, which only says "plastic vs not plastic".
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

import cv2
import numpy as np

from . import config


@dataclass
class Particle:
    pid: int
    # geometry in pixels
    area_px: float
    perimeter_px: float
    major_axis_px: float
    minor_axis_px: float
    equiv_diameter_px: float
    aspect_ratio: float
    circularity: float
    solidity: float
    extent: float
    # bounding box (x, y, w, h) in pixels
    bbox: tuple
    centroid: tuple
    contour: np.ndarray
    # calibrated sizes (filled if um_per_pixel provided)
    area_um2: Optional[float] = None
    length_um: Optional[float] = None
    width_um: Optional[float] = None
    # classification (filled by classify.py)
    cls: str = ""
    confidence: float = 0.0


def _circularity(area: float, perimeter: float) -> float:
    if perimeter <= 0:
        return 0.0
    return float(min(1.0, 4.0 * math.pi * area / (perimeter * perimeter)))


def analyze(mask: np.ndarray, um_per_pixel: Optional[float] = None) -> List[Particle]:
    """Extract particles from a binary mask (plastic == 255)."""
    binary = (mask > 0).astype(np.uint8)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    particles: List[Particle] = []
    pid = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        x, y, bw, bh = cv2.boundingRect(cnt)

        # Noise filtering.
        if area < config.MIN_PARTICLE_AREA_PX:
            continue
        if bw < config.MIN_PARTICLE_BBOX_PX and bh < config.MIN_PARTICLE_BBOX_PX:
            continue

        perimeter = cv2.arcLength(cnt, True)

        # Major/minor axis via fitted ellipse (needs >= 5 points), else bbox.
        if len(cnt) >= 5:
            (_, _), (ax1, ax2), _ = cv2.fitEllipse(cnt)
            major = max(ax1, ax2)
            minor = min(ax1, ax2)
        else:
            major = float(max(bw, bh))
            minor = float(min(bw, bh))
        minor = max(minor, 1e-6)
        aspect_ratio = major / minor

        # Solidity = area / convex hull area.
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = float(area / hull_area) if hull_area > 0 else 0.0

        # Extent = area / bbox area.
        bbox_area = bw * bh
        extent = float(area / bbox_area) if bbox_area > 0 else 0.0

        equiv_diameter = math.sqrt(4.0 * area / math.pi)

        M = cv2.moments(cnt)
        cx = M["m10"] / M["m00"] if M["m00"] else x + bw / 2
        cy = M["m01"] / M["m00"] if M["m00"] else y + bh / 2

        pid += 1
        p = Particle(
            pid=pid,
            area_px=float(area),
            perimeter_px=float(perimeter),
            major_axis_px=float(major),
            minor_axis_px=float(minor),
            equiv_diameter_px=float(equiv_diameter),
            aspect_ratio=float(aspect_ratio),
            circularity=_circularity(area, perimeter),
            solidity=solidity,
            extent=extent,
            bbox=(int(x), int(y), int(bw), int(bh)),
            centroid=(float(cx), float(cy)),
            contour=cnt,
        )

        if um_per_pixel:
            p.area_um2 = p.area_px * (um_per_pixel ** 2)
            p.length_um = p.major_axis_px * um_per_pixel
            p.width_um = p.minor_axis_px * um_per_pixel

        particles.append(p)

    return particles
