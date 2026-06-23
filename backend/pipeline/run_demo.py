"""End-to-end CLI for the microplastic detection + analysis demo.

    python -m microplastic_demo.run_demo --input <image-or-folder> \
        [--weights PATH] [--um-per-pixel FLOAT | --no-calibrate] \
        [--out outputs/] [--panel]

For each image it writes:
    <name>_overlay.png    annotated image (class-colored particles + IDs)
    <name>_particles.csv  one row per particle
    <name>_summary.json   counts, sizes, contamination level
    <name>_panel.png      (optional) original | mask | annotated
and prints a one-line summary per image.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

import cv2
import numpy as np

from . import config, calibrate, segmenter, analyzer, classify, report

IMAGE_EXTS = (".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp")


def _load_rgb(path: str) -> np.ndarray:
    """Load any supported image as HxWx3 RGB uint8."""
    img = cv2.imread(path, cv2.IMREAD_COLOR)  # BGR, drops alpha, handles tiff
    if img is None:
        raise ValueError(f"Could not read image: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def _gather_inputs(input_path: str) -> list[str]:
    if os.path.isdir(input_path):
        files = []
        for ext in IMAGE_EXTS:
            files.extend(glob.glob(os.path.join(input_path, f"*{ext}")))
            files.extend(glob.glob(os.path.join(input_path, f"*{ext.upper()}")))
        return sorted(set(files))
    return [input_path]


def process_image(path: str, model, device, um_per_pixel, out_dir: str,
                  make_panel: bool) -> dict:
    name = os.path.splitext(os.path.basename(path))[0]
    rgb = _load_rgb(path)

    mask = segmenter.segment(model, device, rgb)
    particles = analyzer.analyze(mask, um_per_pixel=um_per_pixel)
    classify.classify_all(particles)

    summary = report.build_summary(name, particles, mask, um_per_pixel)
    df = report.to_dataframe(name, particles)
    overlay = report.make_overlay(rgb, particles, summary)

    report.save_csv(df, os.path.join(out_dir, f"{name}_particles.csv"))
    report.save_summary(summary, os.path.join(out_dir, f"{name}_summary.json"))
    report.save_overlay(overlay, os.path.join(out_dir, f"{name}_overlay.png"))
    if make_panel:
        report.make_panel(rgb, mask, overlay,
                          os.path.join(out_dir, f"{name}_panel.png"))

    print(f"[{name}] {report.summary_text(summary)}")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="Microplastic detection demo")
    parser.add_argument("--input", required=True,
                        help="Image file or folder of images")
    parser.add_argument("--weights", default=config.DEFAULT_WEIGHTS,
                        help="MP-Net .pth weights (default: unet4.pth)")
    parser.add_argument("--out", default=config.OUTPUT_DIR,
                        help="Output directory")
    parser.add_argument("--um-per-pixel", type=float, default=None,
                        help="Explicit calibration (overrides auto-estimate)")
    parser.add_argument("--no-calibrate", action="store_true",
                        help="Disable spiked auto-calibration (report pixels)")
    parser.add_argument("--panel", action="store_true",
                        help="Also save a 3-panel figure per image")
    args = parser.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)

    um_per_pixel = calibrate.resolve_um_per_pixel(
        args.um_per_pixel, auto=not args.no_calibrate)
    if um_per_pixel:
        print(f"Calibration: {um_per_pixel:.4f} um/pixel "
              f"(1 px = {um_per_pixel:.2f} um)")
    else:
        print("Calibration: none -> sizes reported in pixels")

    print(f"Loading MP-Net weights: {args.weights}")
    model, device = segmenter.load_model(args.weights)
    print(f"Model ready on {device}")

    inputs = _gather_inputs(args.input)
    if not inputs:
        print(f"No images found at {args.input}", file=sys.stderr)
        return 1

    for path in inputs:
        try:
            process_image(path, model, device, um_per_pixel, args.out, args.panel)
        except Exception as exc:  # keep going on a bad image
            print(f"[{os.path.basename(path)}] ERROR: {exc}", file=sys.stderr)

    print(f"\nDone. Outputs written to: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
