# Microplastic Detection 🔬

Drop a fluorescence microscopy image → get microplastics **detected, classified,
sized, and scored** for contamination, with a downloadable per-particle report.

The pipeline pairs the pretrained **MP-Net** binary segmentation model
(*Park et al., 2022 — segmentation_models_pytorch U-Net, ResNet101*) with a
custom **OpenCV particle-analysis layer** that the model itself lacks:
per-particle shape, size, circularity and aspect ratio → shape class
(**fibre / fragment / film / bead**) → contamination score → CSV.

## Project layout

```
anuBio/
├── backend/          FastAPI service + the Python pipeline
│   ├── main.py           API: /api/analyze, /api/config, /api/health
│   ├── pipeline/         segmenter · analyzer · classify · calibrate · report
│   ├── outputs/          generated per-request artifacts
│   └── requirements.txt
├── frontend/         Vite + React drop-image UI
│   └── src/              App + components (Dropzone, ResultView, …)
├── models/           pretrained weights (.pth) — unet4.pth is the default
├── data/             datasets (clam, spiked, nile-red images)
└── README.md
```

## Setup

**Python deps** (once):

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r backend/requirements.txt
```

**Frontend deps** (once):

```bash
cd frontend && npm install
```

## Run (two terminals)

**1 — Backend** (loads the model once at startup):

```bash
cd backend
uvicorn main:app --reload --port 8000
```

**2 — Frontend**:

```bash
cd frontend
npm run dev
```

Open the URL Vite prints (default http://localhost:5173), drag in an image
(try `data/spiked/spiked/spiked_fl/RR1.tiff`), and click **Analyze**.

> First analysis loads the 207 MB model and, on CPU, large images take
> ~30–60 s. The UI shows a loading state. Subsequent images are faster.

## The interface (AQUA-SCAN)

Three tabs:

- **Overview** — landing page: what the system does, the MP-Net + OpenCV
  architecture, and the scientific feature set.
- **Diagnostic Lab** — the workflow: pick an MP-Net checkpoint
  (`unet1–4.pth`), set the **detection threshold** (segmentation sensitivity),
  drop an image, and **Run Optical Inference**.
- **Awareness** — microplastic education: sources, the four shape classes,
  environmental + health impact, and what people can do.

Plus a dark/light theme toggle and a live **API: Online** status indicator.

## What you get per run

- **Annotated overlay** — class-colored particles + IDs (toggle Original / Mask)
- **Contamination banner** — Low / Moderate / High / Severe + count + area %
- **Summary cards** — totals, per-class counts, median size, calibration
- **Per-particle table** — sortable; id, class, size, circularity, aspect ratio…
- **CSV download** — the full per-particle report

## Calibration (microns)

`backend/pipeline/calibrate.py` estimates µm/pixel from the spiked reference
set (HDPE ≈ 500 µm) → ~6.83 µm/px. It is magnification-specific: for other
images, type a µm/pixel value in the UI, or untick calibration to report pixels.

## CLI (optional)

The pipeline still runs headless:

```bash
cd backend
python -m pipeline.run_demo --input ../data/spiked/spiked/spiked_fl --panel
```

Tunable thresholds (segmentation, noise filter, class rules, contamination
buckets) all live in `backend/pipeline/config.py`.
