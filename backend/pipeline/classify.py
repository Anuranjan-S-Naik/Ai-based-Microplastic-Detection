"""Rule-based morphology classification: fibre / fragment / film / bead.

Transparent, training-free rules driven by the per-particle features computed
in analyzer.py. Thresholds live in config.py. A simple confidence is the
normalized margin by which the deciding rule was satisfied.
"""
from __future__ import annotations

from typing import List

from . import config
from .analyzer import Particle


def _clamp01(v: float) -> float:
    return float(max(0.0, min(1.0, v)))


def classify_particle(p: Particle) -> tuple[str, float]:
    """Return (class_name, confidence) for a single particle."""
    ar = p.aspect_ratio
    circ = p.circularity
    ext = p.extent
    area = p.area_px

    # 1. fibre: long & thin.
    if ar >= config.FIBRE_ASPECT_RATIO:
        conf = _clamp01((ar - config.FIBRE_ASPECT_RATIO) / config.FIBRE_ASPECT_RATIO + 0.5)
        return "fibre", conf

    # 2. bead: round and roughly equiaxed.
    if circ >= config.BEAD_CIRCULARITY and ar < config.BEAD_MAX_ASPECT_RATIO:
        conf = _clamp01((circ - config.BEAD_CIRCULARITY) / (1.0 - config.BEAD_CIRCULARITY))
        return "bead", conf

    # 3. film: large, flat sheet that fills its bounding box.
    if (ext >= config.FILM_MIN_EXTENT and area >= config.FILM_MIN_AREA_PX
            and circ >= config.FILM_MIN_CIRCULARITY):
        conf = _clamp01((ext - config.FILM_MIN_EXTENT) / (1.0 - config.FILM_MIN_EXTENT))
        return "film", conf

    # 4. fragment: default (irregular, angular). Confidence grows as the
    #    particle sits further from the bead/fibre boundaries.
    conf = _clamp01(0.5 * (
        (config.FIBRE_ASPECT_RATIO - ar) / config.FIBRE_ASPECT_RATIO
        + (config.BEAD_CIRCULARITY - circ) / config.BEAD_CIRCULARITY
    ))
    return "fragment", conf


def classify_all(particles: List[Particle]) -> List[Particle]:
    """Annotate each particle in place with cls + confidence."""
    for p in particles:
        p.cls, p.confidence = classify_particle(p)
    return particles
