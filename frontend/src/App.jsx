import React, { useEffect, useState } from "react";
import Overview from "./pages/Overview.jsx";
import DiagnosticLab from "./pages/DiagnosticLab.jsx";
import Awareness from "./pages/Awareness.jsx";
import { getConfig, getHealth } from "./api.js";

const TABS = [
  { key: "overview", label: "Overview", icon: "▦" },
  { key: "lab", label: "Diagnostic Lab", icon: "⚕" },
  { key: "awareness", label: "Awareness", icon: "❖" },
];

export default function App() {
  const [tab, setTab] = useState("overview");
  const [cfg, setCfg] = useState(null);
  const [online, setOnline] = useState(false);
  const [theme, setTheme] = useState("dark");

  useEffect(() => {
    getConfig().then(setCfg).catch(() => setCfg(null));
  }, []);

  useEffect(() => {
    let alive = true;
    const ping = () =>
      getHealth()
        .then(() => alive && setOnline(true))
        .catch(() => alive && setOnline(false));
    ping();
    const id = setInterval(ping, 8000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  return (
    <div className="app-shell">
      <nav className="navbar">
        <div className="brand">
          <span className="brand-logo">💧</span>
          <div>
            <div className="brand-name">AQUA-SCAN</div>
            <div className="brand-sub">MICROPLASTIC ANALYZER</div>
          </div>
        </div>

        <div className="nav-tabs">
          {TABS.map((t) => (
            <button
              key={t.key}
              className={`nav-tab ${tab === t.key ? "active" : ""}`}
              onClick={() => setTab(t.key)}
            >
              <span className="nav-tab-icon">{t.icon}</span>
              {t.label}
            </button>
          ))}
        </div>

        <div className="nav-right">
          <span className={`api-status ${online ? "up" : "down"}`}>
            <span className="api-dot" />
            API: {online ? "Online" : "Offline"}
          </span>
          <button
            className="theme-toggle"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            title="Toggle theme"
          >
            {theme === "dark" ? "☀" : "☾"}
          </button>
        </div>
      </nav>

      <main className="page">
        {tab === "overview" && (
          <Overview cfg={cfg} onLaunch={() => setTab("lab")} />
        )}
        {tab === "lab" && <DiagnosticLab cfg={cfg} />}
        {tab === "awareness" && <Awareness />}
      </main>
    </div>
  );
}
