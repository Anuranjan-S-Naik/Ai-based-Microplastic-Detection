import React from "react";

const STATS = [
  { value: "5 mm", label: "Upper size limit defining a microplastic" },
  { value: "~11M t", label: "Plastic entering oceans every year" },
  { value: "90%+", label: "Of bottled water samples contain microplastics" },
  { value: "5 g/wk", label: "Plastic an average person may ingest — a credit card's worth" },
];

const SOURCES = [
  { icon: "👕", title: "Synthetic textiles", body: "Washing polyester and nylon clothing sheds microfibres that pass straight through treatment plants." },
  { icon: "🛞", title: "Tyre & road wear", body: "Vehicle tyres abrade into fine particles that wash off roads into waterways." },
  { icon: "🧴", title: "Cosmetics & microbeads", body: "Exfoliants and some personal-care products historically added plastic microbeads." },
  { icon: "♻️", title: "Plastic breakdown", body: "Larger litter fragments under UV light and waves into ever-smaller secondary microplastics." },
];

const SHAPES = [
  { cls: "fibre", color: "#ffd400", body: "Long, thin, thread-like — mostly from synthetic clothing and ropes." },
  { cls: "fragment", color: "#ff9b2b", body: "Irregular angular pieces from broken-down rigid plastics." },
  { cls: "film", color: "#23d5d5", body: "Thin flat sheets from bags and packaging." },
  { cls: "bead", color: "#ff3b5c", body: "Round spheres from cosmetics and industrial pellets." },
];

const ACTIONS = [
  "Choose natural fibres and wash synthetics less often, using a microfibre-catching bag or filter.",
  "Avoid single-use plastics — carry a reusable bottle, cup and bags.",
  "Skip rinse-off cosmetics that list polyethylene or polypropylene.",
  "Dispose of and recycle plastics properly so they never reach waterways.",
  "Support legislation banning microbeads and improving wastewater filtration.",
];

export default function Awareness() {
  return (
    <div className="awareness">
      <section className="aw-hero">
        <span className="badge-pill">
          <span className="badge-dot" /> Spread Awareness
        </span>
        <h1>Why Microplastics Matter</h1>
        <p>
          Microplastics are plastic particles smaller than 5 mm. They are now
          found in oceans, rivers, soil, the air we breathe, the food we eat —
          and inside human blood, lungs and placentas. Detecting and quantifying
          them is the first step toward protecting water quality and health.
        </p>
      </section>

      <div className="aw-stats">
        {STATS.map((s) => (
          <div className="aw-stat" key={s.label}>
            <div className="aw-stat-value">{s.value}</div>
            <div className="aw-stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      <h2 className="aw-section-title">Where Do They Come From?</h2>
      <div className="aw-grid">
        {SOURCES.map((s) => (
          <div className="aw-card" key={s.title}>
            <div className="aw-card-icon">{s.icon}</div>
            <h3>{s.title}</h3>
            <p>{s.body}</p>
          </div>
        ))}
      </div>

      <h2 className="aw-section-title">The Four Shapes We Classify</h2>
      <div className="aw-shapes">
        {SHAPES.map((s) => (
          <div className="aw-shape" key={s.cls}>
            <span className="aw-shape-dot" style={{ background: s.color }} />
            <div>
              <div className="aw-shape-name">{s.cls}</div>
              <p>{s.body}</p>
            </div>
          </div>
        ))}
      </div>

      <h2 className="aw-section-title">Why It Harms</h2>
      <div className="aw-impact">
        <div className="aw-impact-col">
          <h3>🌊 Environment</h3>
          <ul>
            <li>Ingested by plankton, fish and shellfish, entering the food chain.</li>
            <li>Carries toxic pollutants and pathogens across ecosystems.</li>
            <li>Persists for hundreds of years — it never truly disappears.</li>
          </ul>
        </div>
        <div className="aw-impact-col">
          <h3>🫀 Human Health</h3>
          <ul>
            <li>Detected in human blood, lungs, gut and placental tissue.</li>
            <li>Linked to inflammation, oxidative stress and hormone disruption.</li>
            <li>Long-term effects are an active and urgent area of research.</li>
          </ul>
        </div>
      </div>

      <h2 className="aw-section-title">What You Can Do</h2>
      <ul className="aw-actions">
        {ACTIONS.map((a, i) => (
          <li key={i}>
            <span className="aw-check">✓</span>
            {a}
          </li>
        ))}
      </ul>

      <div className="aw-footer-note">
        Every sample analyzed in the Diagnostic Lab adds to the picture of how
        widespread microplastic contamination really is. Awareness drives change.
      </div>
    </div>
  );
}
