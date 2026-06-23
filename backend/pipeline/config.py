"""Central configuration: paths, model/inference constants, classification
thresholds, calibration and contamination scoring parameters.

Everything tunable lives here so the demo can be adjusted without touching
the pipeline code.
"""
from __future__ import annotations

import os

# --------------------------------------------------------------------------
# Paths (layout: <root>/{backend/pipeline, models, data}; this file is
# backend/pipeline/config.py, so PROJECT_ROOT is three levels up.)
# --------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))           # backend/pipeline
BACKEND_DIR = os.path.dirname(_THIS_DIR)                          # backend
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)                       # repo root

MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
WEIGHTS_DIR = MODELS_DIR
DEFAULT_WEIGHTS = os.path.join(MODELS_DIR, "unet4.pth")  # MP-Net best performer
OUTPUT_DIR = os.path.join(BACKEND_DIR, "outputs")

SPIKED_FL_DIR = os.path.join(DATA_DIR, "spiked", "spiked", "spiked_fl")
SPIKED_MASK_DIR = os.path.join(DATA_DIR, "spiked", "spiked", "spiked_mask")
CLAM_FL_DIR = os.path.join(DATA_DIR, "clam", "clam", "clam_fl")
CLAM_MASK_DIR = os.path.join(DATA_DIR, "clam", "clam", "clam_mask")

# --------------------------------------------------------------------------
# MP-Net segmentation model / inference (matches the upstream repo exactly)
# --------------------------------------------------------------------------
ENCODER = "resnet101"
PATCH_SIZE = 256
# The upstream UNet_prediction.py thresholds the RAW model output at 0.5
# (no sigmoid). We reproduce that by default for faithful results, but expose
# a flag in case sigmoid-then-threshold is preferred.
THRESHOLD = 0.5
APPLY_SIGMOID = False
NORM_MEAN = [0.1034, 0.0308, 0.0346]
NORM_STD = [0.0932, 0.0273, 0.0302]

# --------------------------------------------------------------------------
# Calibration (microns per pixel)
# --------------------------------------------------------------------------
# Known reference particle sizes in the spiked dataset (from the dataset README):
#   HDPE pieces ~500 um, PET pieces ~120 um.
# calibrate.py estimates um/pixel by matching the largest detected particles
# to HDPE_REF_UM. If calibration cannot run, sizes are reported in pixels.
HDPE_REF_UM = 500.0
PET_REF_UM = 120.0
# Fallback used when no calibration is available and the user passes none.
# None => report sizes in pixels (length_um/area_um2 columns left blank).
DEFAULT_UM_PER_PIXEL: float | None = None

# --------------------------------------------------------------------------
# Particle filtering
# --------------------------------------------------------------------------
MIN_PARTICLE_AREA_PX = 25       # drop blobs smaller than ~5x5 px (noise)
MIN_PARTICLE_BBOX_PX = 5        # drop blobs whose bbox side < 5 px

# --------------------------------------------------------------------------
# Shape classification thresholds (rule-based, evaluated in order)
# --------------------------------------------------------------------------
# fibre:    long & thin
FIBRE_ASPECT_RATIO = 3.0
# bead:     round
BEAD_CIRCULARITY = 0.85
BEAD_MAX_ASPECT_RATIO = 1.5
# film:     flat sheet that fills its bounding box
FILM_MIN_EXTENT = 0.60
FILM_MIN_AREA_PX = 800          # films are comparatively large
FILM_MIN_CIRCULARITY = 0.40
# fragment: everything else (default)

CLASS_NAMES = ["fibre", "fragment", "film", "bead"]
# BGR colors for the annotated overlay (OpenCV uses BGR).
CLASS_COLORS = {
    "fibre":    (0, 255, 255),   # yellow
    "fragment": (0, 165, 255),   # orange
    "film":     (255, 255, 0),   # cyan
    "bead":     (0, 0, 255),     # red
}

# --------------------------------------------------------------------------
# Contamination scoring
# --------------------------------------------------------------------------
# Index combines particle count and plastic area fraction. Buckets are applied
# to the resulting index. Tune freely for the demo.
# index = COUNT_WEIGHT * count + AREA_WEIGHT * (area_fraction * 100)
CONTAM_COUNT_WEIGHT = 1.0
CONTAM_AREA_WEIGHT = 20.0
CONTAM_BUCKETS = [   # (upper_bound_inclusive, label)
    (10,  "Low"),
    (40,  "Moderate"),
    (100, "High"),
    (float("inf"), "Severe"),
]
