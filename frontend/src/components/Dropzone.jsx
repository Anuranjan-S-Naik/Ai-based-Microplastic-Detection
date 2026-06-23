import React, { useCallback, useRef, useState } from "react";

export default function Dropzone({ onFile, preview, fileName }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const handleFiles = useCallback(
    (files) => {
      const f = files?.[0];
      if (f && f.type.startsWith("image/")) onFile(f);
      else if (f) onFile(f); // allow .tif/.tiff that some browsers don't tag
    },
    [onFile]
  );

  return (
    <div
      className={`dropzone ${dragging ? "dragging" : ""} ${preview ? "has-image" : ""}`}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*,.tif,.tiff"
        hidden
        onChange={(e) => handleFiles(e.target.files)}
      />
      {preview ? (
        <div className="preview-wrap">
          <img src={preview} alt="preview" className="preview" />
          <span className="filename">{fileName}</span>
        </div>
      ) : (
        <div className="dz-placeholder">
          <div className="dz-icon">⬆</div>
          <p className="dz-title">Drop a microscopy image here</p>
          <p className="dz-hint">or click to browse · PNG, JPG, TIFF</p>
        </div>
      )}
    </div>
  );
}
