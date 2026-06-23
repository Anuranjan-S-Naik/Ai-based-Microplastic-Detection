import React, { useState } from "react";
import ContaminationBanner from "./ContaminationBanner.jsx";
import SummaryCards from "./SummaryCards.jsx";
import ParticleTable from "./ParticleTable.jsx";

const BASE_VIEWS = [
  { key: "overlay_url", label: "Detected" },
  { key: "original_url", label: "Original" },
  { key: "mask_url", label: "Mask" },
];

export default function ResultView({ result }) {
  const [view, setView] = useState("overlay_url");
  const { summary } = result;
  const calibrated = summary.calibration_um_per_pixel != null;

  // Build the view list dynamically — add Heatmap only if the backend
  // generated one (requires >= 3 particles with distinct centroids).
  const views = [...BASE_VIEWS];
  if (result.heatmap_url) {
    views.push({ key: "heatmap_url", label: "🔥 Heatmap" });
  }

  const hotspot = result.hotspot_stats;

  return (
    <section className="results">
      {(result.checkpoint || result.threshold != null) && (
        <div className="result-meta">
          {result.checkpoint && <span>checkpoint: {result.checkpoint}</span>}
          {result.threshold != null && <span>threshold: {result.threshold}</span>}
          <span>image: {summary.image}</span>
        </div>
      )}
      <ContaminationBanner summary={summary} />
      <SummaryCards summary={summary} />

      <div className="result-grid">
        <div className="image-panel">
          <div className="image-tabs">
            {views.map((v) => (
              <button
                key={v.key}
                className={view === v.key ? "active" : ""}
                onClick={() => setView(v.key)}
              >
                {v.label}
              </button>
            ))}
            <a className="download" href={result.csv_url} download>
              ⬇ Download CSV
            </a>
          </div>
          <div className="image-frame">
            <img src={result[view]} alt={view} />
          </div>

          {/* Hotspot badge — shown only when viewing the heatmap */}
          {view === "heatmap_url" && hotspot && (
            <div className="heatmap-info">
              <div className="heatmap-badge">
                <span className="heatmap-badge-icon">📍</span>
                <div className="heatmap-badge-content">
                  <div className="heatmap-badge-title">Peak Hotspot</div>
                  <div className="heatmap-badge-detail">
                    x: {hotspot.peak_x}, y: {hotspot.peak_y}
                  </div>
                </div>
              </div>
              <div className="heatmap-badge">
                <span className="heatmap-badge-icon">🔬</span>
                <div className="heatmap-badge-content">
                  <div className="heatmap-badge-title">Density Clusters</div>
                  <div className="heatmap-badge-detail">
                    {hotspot.n_clusters} cluster{hotspot.n_clusters !== 1 ? "s" : ""} detected
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <h3 className="section-title">
        Per-particle measurements ({result.particles.length})
      </h3>
      <ParticleTable particles={result.particles} calibrated={calibrated} />
    </section>
  );
}
