import React from "react";

const LEVEL_CLASS = {
  Low: "level-low",
  Moderate: "level-moderate",
  High: "level-high",
  Severe: "level-severe",
};

export default function ContaminationBanner({ summary }) {
  const level = summary.contamination_level;
  return (
    <div className={`banner ${LEVEL_CLASS[level] || ""}`}>
      <div className="banner-level">
        <span className="banner-dot" />
        {level} contamination
      </div>
      <div className="banner-stats">
        <span>{summary.particle_count} particles</span>
        <span>·</span>
        <span>{(summary.plastic_area_fraction * 100).toFixed(2)}% area</span>
        <span>·</span>
        <span>index {summary.contamination_index}</span>
      </div>
    </div>
  );
}
