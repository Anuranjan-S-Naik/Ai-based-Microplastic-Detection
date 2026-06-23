"""MP-Net binary segmentation.

Loads the pretrained `segmentation_models_pytorch` U-Net (ResNet101 encoder)
and runs the patch-based inference used by the upstream
Microplastics-Annotation-Package repo, returning a full-resolution binary
mask where plastic == 255.

The patch/pad/stitch logic mirrors UNet_prediction.py from that repo so the
results match the published MP-Net behaviour.
"""
from __future__ import annotations

import numpy as np
import torch
from PIL import Image
from torchvision.transforms import transforms
from torchvision.transforms.functional import crop
import segmentation_models_pytorch as smp

from . import config


def _size_adjustment(pil_img: Image.Image, patch_size: int):
    """Pad image (black) so width & height are multiples of patch_size.

    Returns (padded_image, added_w, added_h).
    """
    w, h = pil_img.size
    added_w = (patch_size - (w % patch_size)) % patch_size
    added_h = (patch_size - (h % patch_size)) % patch_size
    if added_w == 0 and added_h == 0:
        return pil_img, 0, 0
    new_img = Image.new(pil_img.mode, (w + added_w, h + added_h), (0, 0, 0))
    new_img.paste(pil_img, (0, 0))
    return new_img, added_w, added_h


def load_model(weights_path: str = config.DEFAULT_WEIGHTS, device: str | None = None):
    """Build the smp U-Net and load MP-Net weights. Returns (model, device)."""
    dev = torch.device(device) if device else torch.device(
        "cuda" if torch.cuda.is_available() else "cpu")
    # encoder_weights=None: we overwrite all weights with the .pth state_dict,
    # so there is no need to download ImageNet init.
    model = smp.Unet(config.ENCODER, in_channels=3, classes=1, encoder_weights=None)
    try:
        model.load_state_dict(torch.load(weights_path, map_location=str(dev)))
    except RuntimeError:
        # Fall back to CPU if a CUDA-saved checkpoint can't map to this device.
        dev = torch.device("cpu")
        model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.to(dev)
    model.eval()
    return model, dev


@torch.no_grad()
def segment(model, device, image_rgb: np.ndarray, threshold: float | None = None) -> np.ndarray:
    """Run patch-based inference on an HxWx3 RGB uint8 array.

    threshold overrides config.THRESHOLD for this call (the "detection
    threshold" exposed in the UI). Returns an HxW uint8 mask,
    plastic == 255, background == 0.
    """
    thr = config.THRESHOLD if threshold is None else float(threshold)
    pil = Image.fromarray(image_rgb).convert("RGB")
    padded, added_w, added_h = _size_adjustment(pil, config.PATCH_SIZE)
    w, h = padded.size
    ps = config.PATCH_SIZE

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=config.NORM_MEAN, std=config.NORM_STD),
    ])

    prediction = None
    for y in range(0, h, ps):
        row = None
        for x in range(0, w, ps):
            patch = crop(padded, y, x, ps, ps)
            tensor = transform(patch).unsqueeze(0).to(device, dtype=torch.float32)
            out = model(tensor)
            if config.APPLY_SIGMOID:
                out = torch.sigmoid(out)
            # plastic == output > threshold (matches upstream, foreground == 1)
            p_patch = (out > thr).float().squeeze(0)  # (1, ps, ps)

            # Trim the black padding from the last column/row of patches.
            if x + ps == w and y + ps == h:
                p_patch = p_patch[:, :ps - added_h, :ps - added_w]
            elif x + ps == w:
                p_patch = p_patch[:, :, :ps - added_w]
            elif y + ps == h:
                p_patch = p_patch[:, :ps - added_h, :]

            row = p_patch if row is None else torch.cat((row, p_patch), dim=2)
        prediction = row if prediction is None else torch.cat((prediction, row), dim=1)

    mask = prediction.squeeze(0).cpu().numpy().astype(np.uint8) * 255
    return mask
