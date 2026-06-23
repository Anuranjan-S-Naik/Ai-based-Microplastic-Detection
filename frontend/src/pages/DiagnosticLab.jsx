import React, { useEffect, useState } from "react";
import Dropzone from "../components/Dropzone.jsx";
import ResultView from "../components/ResultView.jsx";
import { analyzeImage } from "../api.js";

export default function DiagnosticLab({ cfg }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [checkpoint, setCheckpoint] = useState("");
  const [threshold, setThreshold] = useState(0.5);
  const [calibrate, setCalibrate] = useState(true);
  const [umPerPixel, setUmPerPixel] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (cfg) {
      setCheckpoint(cfg.default_checkpoint || "");
      if (cfg.default_threshold != null) setThreshold(cfg.default_threshold);
    }
  }, [cfg]);

  function onFile(f) {
    setFile(f);
    setResult(null);
    setError(null);
    setPreview(URL.createObjectURL(f));
  }

  async function onRun() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await analyzeImage(file, {
        umPerPixel,
        calibrate,
        threshold,
        weights: checkpoint,
      });
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="lab">
      <aside className="lab-sidebar">
        <div className="panel">
          <div className="panel-head">⚙ Inference Parameters</div>

          <label className="field-label">MP-NET MODEL CHECKPOINT</label>
          <div className="select-wrap">
            <select
              value={checkpoint}
              onChange={(e) => setCheckpoint(e.target.value)}
            >
              {(cfg?.checkpoints || []).map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            <span className="select-icon">≣</span>
          </div>

          <div className="field-row">
            <label className="field-label">DETECTION THRESHOLD</label>
            <span className="field-chip">{Number(threshold).toFixed(2)}</span>
          </div>
          <input
            className="slider"
            type="range"
            min="0.1"
            max="1.0"
            step="0.05"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
          />
          <div className="slider-legend">
            <span>0.10 (High sensitivity)</span>
            <span>1.00 (High precision)</span>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">▣ Sample Acquisition</div>
          <Dropzone onFile={onFile} preview={preview} fileName={file?.name} />

          <div className="calib-row">
            <label className="opt">
              <input
                type="checkbox"
                checked={calibrate}
                onChange={(e) => setCalibrate(e.target.checked)}
              />
              Spiked calibration
              {cfg?.spiked_um_per_pixel ? ` (${cfg.spiked_um_per_pixel} µm/px)` : ""}
            </label>
            <label className="opt opt-inline">
              µm/px
              <input
                type="number"
                step="0.01"
                placeholder="auto"
                value={umPerPixel}
                onChange={(e) => setUmPerPixel(e.target.value)}
              />
            </label>
          </div>

          <button className="btn-run" onClick={onRun} disabled={!file || loading}>
            {loading ? "◌ Running…" : "▢ Run Optical Inference"}
          </button>
        </div>
      </aside>

      <section className="lab-main">
        {loading ? (
          <div className="lab-empty">
            <div className="spinner big" />
            <h2>Running MP-Net Segmentation…</h2>
            <p>
              The model is processing your sample on CPU. Large microscope
              images can take 30–60 seconds.
            </p>
          </div>
        ) : error ? (
          <div className="lab-empty">
            <div className="empty-icon error">!</div>
            <h2>Inference Failed</h2>
            <p>{error}</p>
          </div>
        ) : result ? (
          <ResultView result={result} />
        ) : (
          <div className="lab-empty">
            <div className="empty-icon">?</div>
            <h2>No Core Sample Loaded</h2>
            <p>
              Acquire a water microscope image using the capture panel on the
              left to execute MP-Net segmentation diagnostics.
            </p>
            <div className="engine-note">
              <div className="engine-title">Optical Engine Diagnostics</div>
              <div className="engine-body">
                MP-Net feeds the RGB microscope image through a U-Net
                (ResNet-101) encoder–decoder to generate a per-pixel plastic
                mask. An OpenCV layer then converts the mask into per-particle
                shape, size and contamination metrics.
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
