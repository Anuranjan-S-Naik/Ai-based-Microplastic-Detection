import React from "react";

const FEATURES = [
  {
    icon: "🧠",
    title: "MP-Net Segmentation",
    body: "A pretrained U-Net with a ResNet-101 encoder (segmentation_models_pytorch) produces a pixel-level binary mask of every microplastic particle in the frame.",
  },
  {
    icon: "📐",
    title: "Per-Particle Morphology",
    body: "An OpenCV analysis layer measures area, length, width, circularity, aspect ratio and solidity for each detected particle — not just a yes/no answer.",
  },
  {
    icon: "🏷️",
    title: "Shape Classification",
    body: "Transparent rules sort every particle into fibre, fragment, film or bead — the standard microplastic morphology categories used in the literature.",
  },
  {
    icon: "📏",
    title: "Micron Calibration",
    body: "Sizes are reported in microns, calibrated against the spiked reference set (HDPE ≈ 500 µm) — or override with your own µm/pixel scale.",
  },
  {
    icon: "⚠️",
    title: "Contamination Scoring",
    body: "Particle count and plastic-area fraction combine into a single contamination index, bucketed Low / Moderate / High / Severe for quick triage.",
  },
  {
    icon: "📄",
    title: "Exportable Reports",
    body: "Every run yields an annotated overlay, a binary mask, and a downloadable per-particle CSV ready for lab record-keeping.",
  },
];

export default function Overview({ cfg, onLaunch }) {
  const arch = cfg?.architecture || "MP-Net (U-Net, ResNet101)";
  return (
    <div className="overview">
      <section className="hero">
        <div className="hero-text">
          <span className="badge-pill">
            <span className="badge-dot" /> Deep Learning AI Integration
          </span>
          <h1 className="hero-title">
            Microplastic Detection in <span className="accent">Water Samples</span>{" "}
            using AI
          </h1>
          <p className="hero-desc">
            Aqua-Scan pairs a pretrained <strong>MP-Net U-Net (ResNet-101)</strong>{" "}
            segmentation model with a custom OpenCV particle-analysis layer to
            automatically detect, classify, size and quantify microplastics in
            fluorescence microscopy images — turning a raw scan into a
            quantitative water-quality report.
          </p>
          <div className="hero-actions">
            <button className="btn-primary" onClick={onLaunch}>
              Open Diagnostic Lab →
            </button>
            <a
              className="btn-ghost"
              href="https://doi.org/10.1371/journal.pone.0269449"
              target="_blank"
              rel="noreferrer"
            >
              Learn More
            </a>
          </div>
        </div>

        <div className="hero-card">
          <div className="hero-card-head">
            <span className="mono-accent">⚕ Sample Segmentation Output</span>
            <span className="acc-pill">Nile-Red FL</span>
          </div>
          <div className="hero-scan">
            <div className="scan-grid" />
            <div className="scan-blob blob-a">
              <span className="scan-tag">bead · 0.86</span>
            </div>
            <div className="scan-blob blob-b">
              <span className="scan-tag">fragment</span>
            </div>
            <div className="scan-blob blob-c">
              <span className="scan-tag">fibre</span>
            </div>
            <div className="scan-caption">SEGMENTING WATER CORE SAMPLE</div>
            <div className="scan-sub">
              Class map: fibre · fragment · film · bead
            </div>
          </div>
          <div className="hero-stats">
            <div className="hstat">
              <div className="hstat-label">FRAMEWORK</div>
              <div className="hstat-value">PyTorch</div>
            </div>
            <div className="hstat">
              <div className="hstat-label">ARCHITECTURE</div>
              <div className="hstat-value">{arch.replace("MP-Net (", "").replace(")", "") || "U-Net"}</div>
            </div>
            <div className="hstat">
              <div className="hstat-label">INTERFACE</div>
              <div className="hstat-value">FastAPI</div>
            </div>
          </div>
        </div>
      </section>

      <h2 className="features-title">Advanced Scientific Features</h2>
      <div className="features-grid">
        {FEATURES.map((f) => (
          <div className="feature-card" key={f.title}>
            <div className="feature-icon">{f.icon}</div>
            <h3>{f.title}</h3>
            <p>{f.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
