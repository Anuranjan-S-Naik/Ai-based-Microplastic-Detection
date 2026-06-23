"""Microplastic detection + particle analysis demo.

Pipeline:
    image -> MP-Net binary segmentation -> OpenCV particle analysis
          -> per-particle morphology + class -> CSV / overlay / summary
"""
