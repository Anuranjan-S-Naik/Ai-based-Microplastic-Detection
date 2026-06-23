"""FastAPI backend for the microplastic detection web app.

Endpoints
---------
GET  /api/health          -> liveness + whether the model is loaded
GET  /api/config          -> calibration default + class names (for the UI)
POST /api/analyze         -> multipart image upload, runs the full pipeline,
                             returns summary + particles + artifact URLs
Static
------
/outputs/<id>/...         -> generated original/mask/overlay/csv per request

The MP-Net model is loaded ONCE at startup (it is ~207 MB); requests reuse it.
"""
from __future__ import annotations

import io
import os
import uuid

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from pipeline import config, segmenter, analyzer, classify, report, calibrate, heatmap

app = FastAPI(title="Microplastic Detection API", version="1.0")

# Vite dev server origins. "*" is fine for a local demo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# Lazy singletons: one model per checkpoint (cached), + spiked calibration.
# --------------------------------------------------------------------------
DEFAULT_CHECKPOINT = os.path.basename(config.DEFAULT_WEIGHTS)
_MODELS: dict = {}                       # checkpoint name -> (model, device)
_STATE: dict = {"spiked_um_per_px": None}


def list_checkpoints() -> list[str]:
    """Compatible U-Net checkpoints (all smp.Unet/ResNet101, same size)."""
    try:
        names = [f for f in os.listdir(config.MODELS_DIR)
                 if f.startswith("unet") and f.endswith(".pth")
                 and "_tta" not in f]
    except FileNotFoundError:
        names = []
    names = sorted(names)
    if DEFAULT_CHECKPOINT in names:  # default first
        names.remove(DEFAULT_CHECKPOINT)
        names.insert(0, DEFAULT_CHECKPOINT)
    return names or [DEFAULT_CHECKPOINT]


def get_model(checkpoint: str | None = None):
    name = checkpoint or DEFAULT_CHECKPOINT
    if name not in list_checkpoints():
        raise HTTPException(status_code=400, detail=f"Unknown checkpoint: {name}")
    if name not in _MODELS:
        _MODELS[name] = segmenter.load_model(os.path.join(config.MODELS_DIR, name))
    return _MODELS[name]


def get_spiked_calibration():
    if _STATE["spiked_um_per_px"] is None:
        _STATE["spiked_um_per_px"] = calibrate.estimate_um_per_pixel()
    return _STATE["spiked_um_per_px"]


os.makedirs(config.OUTPUT_DIR, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=config.OUTPUT_DIR), name="outputs")


@app.on_event("startup")
def _warmup():
    # Load the model and compute calibration up front so the first upload is fast.
    get_model()
    get_spiked_calibration()


@app.get("/api/health")
def health():
    return {"status": "ok", "model_loaded": bool(_MODELS),
            "device": str(next(iter(_MODELS.values()))[1]) if _MODELS else "cpu"}


@app.get("/api/config")
def get_config():
    return {
        "class_names": config.CLASS_NAMES,
        "class_colors": config.CLASS_COLORS,
        "checkpoints": list_checkpoints(),
        "default_checkpoint": DEFAULT_CHECKPOINT,
        "default_threshold": config.THRESHOLD,
        "architecture": f"MP-Net (U-Net, {config.ENCODER})",
        "spiked_um_per_pixel": round(get_spiked_calibration(), 4)
        if get_spiked_calibration() else None,
        "hdpe_ref_um": config.HDPE_REF_UM,
    }


def _read_upload_as_rgb(raw: bytes) -> np.ndarray:
    """Decode uploaded bytes (incl. .tif/.tiff) to HxWx3 RGB uint8."""
    try:
        pil = Image.open(io.BytesIO(raw)).convert("RGB")
        return np.array(pil)
    except Exception:
        arr = np.frombuffer(raw, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Unsupported or corrupt image")
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


@app.post("/api/analyze")
async def analyze(
    file: UploadFile = File(...),
    um_per_pixel: float | None = Form(None),
    calibrate_flag: bool = Form(True),
    threshold: float | None = Form(None),
    weights: str | None = Form(None),
):
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")
    rgb = _read_upload_as_rgb(raw)

    # Resolve calibration: explicit value > spiked estimate (if enabled) > none.
    if um_per_pixel and um_per_pixel > 0:
        upp = float(um_per_pixel)
    elif calibrate_flag:
        upp = get_spiked_calibration()
    else:
        upp = None

    model, device = get_model(weights)
    mask = segmenter.segment(model, device, rgb, threshold=threshold)
    particles = analyzer.analyze(mask, um_per_pixel=upp)
    classify.classify_all(particles)

    name = os.path.splitext(os.path.basename(file.filename or "upload"))[0]
    summary = report.build_summary(name, particles, mask, upp)
    df = report.to_dataframe(name, particles)
    overlay = report.make_overlay(rgb, particles, summary)

    # Generate spatial density heatmap (if enough particles exist).
    heatmap_bgr = None
    hotspot_stats = None
    if heatmap.can_generate(particles):
        heatmap_bgr, hotspot_stats = heatmap.generate(rgb, particles)

    # Persist artifacts under a unique id so the frontend can fetch them.
    rid = uuid.uuid4().hex[:12]
    out_dir = os.path.join(config.OUTPUT_DIR, rid)
    os.makedirs(out_dir, exist_ok=True)
    cv2.imwrite(os.path.join(out_dir, "original.png"),
                cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    cv2.imwrite(os.path.join(out_dir, "mask.png"), mask)
    report.save_overlay(overlay, os.path.join(out_dir, "overlay.png"))
    report.save_csv(df, os.path.join(out_dir, "particles.csv"))
    if heatmap_bgr is not None:
        cv2.imwrite(os.path.join(out_dir, "heatmap.png"), heatmap_bgr)

    base = f"/outputs/{rid}"
    response = {
        "id": rid,
        "checkpoint": weights or DEFAULT_CHECKPOINT,
        "threshold": config.THRESHOLD if threshold is None else float(threshold),
        "summary": summary,
        "particles": df.to_dict("records"),
        "original_url": f"{base}/original.png",
        "mask_url": f"{base}/mask.png",
        "overlay_url": f"{base}/overlay.png",
        "csv_url": f"{base}/particles.csv",
    }
    if heatmap_bgr is not None:
        response["heatmap_url"] = f"{base}/heatmap.png"
        response["hotspot_stats"] = hotspot_stats
    return JSONResponse(response)
