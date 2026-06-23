import React from "react";

const CLASS_COLORS = {
  fibre: "#ffd400",
  fragment: "#ff9b2b",
  film: "#23d5d5",
  bead: "#ff3b5c",
};

export default function SummaryCards({ summary }) {
  const cc = summary.class_counts || {};
  const unit = summary.size_unit;
  return (
    <div className="cards">
      <div className="card">
        <div className="card-value">{summary.particle_count}</div>
        <div className="card-label">Total particles</div>
      </div>

      <div className="card card-classes">
        {Object.keys(cc).map((k) => (
          <div className="class-row" key={k}>
            <span className="class-swatch" style={{ background: CLASS_COLORS[k] }} />
            <span className="class-name">{k}</span>
            <span className="class-count">{cc[k]}</span>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-value">
          {summary.size_median}
          <span className="unit"> {unit}</span>
        </div>
        <div className="card-label">Median size</div>
        <div className="card-sub">
          range {summary.size_min}–{summary.size_max} {unit}
        </div>
      </div>

      <div className="card">
        <div className="card-value">
          {summary.calibration_um_per_pixel
            ? summary.calibration_um_per_pixel
            : "—"}
        </div>
        <div className="card-label">µm / pixel</div>
        <div className="card-sub">
          {summary.calibration_um_per_pixel ? "calibrated" : "pixels only"}
        </div>
      </div>
    </div>
  );
}
