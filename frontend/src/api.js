// Thin API client for the FastAPI backend (same-origin via Vite proxy).

export async function getConfig() {
  const res = await fetch("/api/config");
  if (!res.ok) throw new Error("Failed to load config");
  return res.json();
}

export async function getHealth() {
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error("offline");
  return res.json();
}

export async function analyzeImage(file, { umPerPixel, calibrate, threshold, weights }) {
  const form = new FormData();
  form.append("file", file);
  if (umPerPixel != null && umPerPixel !== "") {
    form.append("um_per_pixel", String(umPerPixel));
  }
  form.append("calibrate_flag", calibrate ? "true" : "false");
  if (threshold != null) form.append("threshold", String(threshold));
  if (weights) form.append("weights", weights);

  const res = await fetch("/api/analyze", { method: "POST", body: form });
  if (!res.ok) {
    let detail = "Analysis failed";
    try {
      detail = (await res.json()).detail || detail;
    } catch (_) {}
    throw new Error(detail);
  }
  return res.json();
}
