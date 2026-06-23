"""Reporting: per-particle CSV, summary JSON + console table, contamination
score, and annotated overlay image.
"""
from __future__ import annotations

import json
import os
from typing import List, Optional

import cv2
import numpy as np
import pandas as pd

from . import config
from .analyzer import Particle


# --------------------------------------------------------------------------
# Contamination scoring
# --------------------------------------------------------------------------
def contamination_score(n_particles: int, area_fraction: float) -> tuple[float, str]:
    """Return (index, level). area_fraction is plastic_px / total_px."""
    index = (config.CONTAM_COUNT_WEIGHT * n_particles
             + config.CONTAM_AREA_WEIGHT * (area_fraction * 100.0))
    for upper, label in config.CONTAM_BUCKETS:
        if index <= upper:
            return index, label
    return index, config.CONTAM_BUCKETS[-1][1]


# --------------------------------------------------------------------------
# CSV
# --------------------------------------------------------------------------
def to_dataframe(image_name: str, particles: List[Particle]) -> pd.DataFrame:
    rows = []
    for p in particles:
        rows.append({
            "image": image_name,
            "particle_id": p.pid,
            "class": p.cls,
            "confidence": round(p.confidence, 3),
            "area_px": round(p.area_px, 1),
            "area_um2": round(p.area_um2, 1) if p.area_um2 is not None else "",
            "length_px": round(p.major_axis_px, 1),
            "length_um": round(p.length_um, 1) if p.length_um is not None else "",
            "width_px": round(p.minor_axis_px, 1),
            "width_um": round(p.width_um, 1) if p.width_um is not None else "",
            "aspect_ratio": round(p.aspect_ratio, 2),
            "circularity": round(p.circularity, 3),
            "solidity": round(p.solidity, 3),
            "extent": round(p.extent, 3),
            "cx": round(p.centroid[0], 1),
            "cy": round(p.centroid[1], 1),
        })
    return pd.DataFrame(rows)


def save_csv(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, index=False)


# --------------------------------------------------------------------------
# Summary
# --------------------------------------------------------------------------
def build_summary(image_name: str, particles: List[Particle], mask: np.ndarray,
                  um_per_pixel: Optional[float]) -> dict:
    n = len(particles)
    total_px = mask.shape[0] * mask.shape[1]
    plastic_px = int((mask > 0).sum())
    area_fraction = plastic_px / total_px if total_px else 0.0
    index, level = contamination_score(n, area_fraction)

    class_counts = {c: 0 for c in config.CLASS_NAMES}
    for p in particles:
        class_counts[p.cls] = class_counts.get(p.cls, 0) + 1

    if um_per_pixel:
        sizes = [p.length_um for p in particles if p.length_um is not None]
        size_unit = "um"
    else:
        sizes = [p.major_axis_px for p in particles]
        size_unit = "px"
    sizes_arr = np.array(sizes) if sizes else np.array([0.0])

    return {
        "image": image_name,
        "particle_count": n,
        "class_counts": class_counts,
        "plastic_area_fraction": round(area_fraction, 5),
        "contamination_index": round(index, 2),
        "contamination_level": level,
        "calibration_um_per_pixel": round(um_per_pixel, 5) if um_per_pixel else None,
        "size_unit": size_unit,
        "size_median": round(float(np.median(sizes_arr)), 1),
        "size_min": round(float(sizes_arr.min()), 1),
        "size_max": round(float(sizes_arr.max()), 1),
    }


def save_summary(summary: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def summary_text(summary: dict) -> str:
    cc = summary["class_counts"]
    breakdown = ", ".join(f"{cc[c]} {c}s" for c in config.CLASS_NAMES)
    unit = summary["size_unit"]
    line = (f"{summary['particle_count']} particles: {breakdown} | "
            f"median size {summary['size_median']} {unit} | "
            f"contamination: {summary['contamination_level'].upper()} "
            f"(index {summary['contamination_index']}, "
            f"{summary['plastic_area_fraction']*100:.2f}% area)")
    return line


# --------------------------------------------------------------------------
# Annotated overlay
# --------------------------------------------------------------------------
def make_overlay(image_rgb: np.ndarray, particles: List[Particle],
                 summary: dict) -> np.ndarray:
    """Draw class-colored contours + IDs over the original image (BGR out)."""
    img = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR).copy()
    for p in particles:
        color = config.CLASS_COLORS.get(p.cls, (255, 255, 255))
        cv2.drawContours(img, [p.contour], -1, color, 2)
        x, y, _, _ = p.bbox
        cv2.putText(img, str(p.pid), (x, max(0, y - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

    _draw_banner(img, summary)
    _draw_legend(img)
    return img


def _draw_banner(img: np.ndarray, summary: dict) -> None:
    level = summary["contamination_level"].upper()
    color = {
        "LOW": (0, 180, 0), "MODERATE": (0, 200, 255),
        "HIGH": (0, 100, 255), "SEVERE": (0, 0, 255),
    }.get(level, (200, 200, 200))
    text = (f"{level}  |  {summary['particle_count']} particles  |  "
            f"{summary['plastic_area_fraction']*100:.2f}% area")
    cv2.rectangle(img, (0, 0), (img.shape[1], 40), (30, 30, 30), -1)
    cv2.putText(img, text, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                color, 2, cv2.LINE_AA)


def _draw_legend(img: np.ndarray) -> None:
    y0 = 55
    for i, c in enumerate(config.CLASS_NAMES):
        y = y0 + i * 22
        cv2.rectangle(img, (10, y - 12), (28, y + 4),
                      config.CLASS_COLORS[c], -1)
        cv2.putText(img, c, (34, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255, 255, 255), 1, cv2.LINE_AA)


def save_overlay(overlay_bgr: np.ndarray, path: str) -> None:
    cv2.imwrite(path, overlay_bgr)


def make_panel(image_rgb: np.ndarray, mask: np.ndarray,
               overlay_bgr: np.ndarray, path: str) -> None:
    """Optional 3-panel figure: original | binary mask | annotated."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    axes[0].imshow(image_rgb); axes[0].set_title("Original (FL)")
    axes[1].imshow(mask, cmap="gray"); axes[1].set_title("MP-Net mask")
    axes[2].imshow(cv2.cvtColor(overlay_bgr, cv2.COLOR_BGR2RGB))
    axes[2].set_title("Detected particles")
    for ax in axes:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
