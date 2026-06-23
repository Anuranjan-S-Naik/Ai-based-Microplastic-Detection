# Microplastic Detection + Particle Analysis Demo

End-to-end microplastic screening pipeline:

```
fluorescence image
   -> MP-Net binary segmentation (pretrained U-Net, ResNet101)   [detection]
   -> OpenCV per-particle morphology analysis                     [our layer]
   -> rule-based shape classification (fibre/fragment/film/bead)
   -> per-particle CSV + annotated overlay + contamination summary
```

The pretrained MP-Net model only answers *"is this pixel plastic?"*. The value
added here is the OpenCV analysis layer that turns that binary mask into
per-particle measurements (size, shape, circularity, aspect ratio), a shape
class for each particle, and an overall contamination score.

## Install

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install segmentation-models-pytorch opencv-python numpy pandas pillow matplotlib scikit-image
```

Weights are already present in `../Dataset/pre-trained_weights/` (`unet4.pth`
is the MP-Net best performer and the default).

## Run

```bash
# single image, auto-calibrated from the spiked reference set, + 3-panel figure
python -m microplastic_demo.run_demo --input "../Dataset/spiked/spiked/spiked_fl/RR1.tiff" --panel

# a whole folder
python -m microplastic_demo.run_demo --input "../Dataset/spiked/spiked/spiked_fl"

# report sizes in pixels (no calibration)
python -m microplastic_demo.run_demo --input <img> --no-calibrate

# supply your own scale
python -m microplastic_demo.run_demo --input <img> --um-per-pixel 6.83
```

Outputs land in `../outputs/`:

| file | contents |
|------|----------|
| `<name>_overlay.png`   | original image with class-colored particles + IDs, contamination banner, legend |
| `<name>_particles.csv` | one row per particle (id, class, confidence, area, length/width, aspect ratio, circularity, solidity, extent, centroid) |
| `<name>_summary.json`  | counts, class breakdown, size stats, contamination index + level, calibration used |
| `<name>_panel.png`     | (with `--panel`) original \| MP-Net mask \| annotated |

## Calibration (size in microns)

`calibrate.py` estimates microns-per-pixel from the spiked ground-truth masks
by matching the largest particles to the known HDPE reference size (500 um).
For the bundled spiked set this gives ~6.83 um/pixel. It is **magnification
specific** — for images at another magnification pass `--um-per-pixel`, or use
`--no-calibrate` to report pixels.

## Shape classification rules

Transparent, training-free rules (thresholds in `config.py`):

| class | rule |
|-------|------|
| fibre    | aspect ratio >= 3 (long, thin) |
| bead     | circularity >= 0.85 and aspect ratio < 1.5 (round) |
| film     | extent >= 0.6 and large area and moderate circularity (flat sheet) |
| fragment | everything else (irregular, angular) — default |

## Contamination score

`index = count + 20 * (plastic_area_fraction * 100)`, bucketed into
Low / Moderate / High / Severe (see `config.py`). Shown with the raw count and
area fraction behind it.

## Notes

- Inference reproduces the upstream `UNet_prediction.py`: 256x256 patches,
  pad to multiples of 256, normalize, threshold raw output at 0.5, stitch.
- The clam samples are nearly clean (ground truth has only ~50-200 plastic px
  per image), so they legitimately yield few/zero particles after noise
  filtering. The spiked set is the showcase.
- Tune thresholds (segmentation, noise filter, class rules, contamination
  buckets) entirely in `config.py`.
```
