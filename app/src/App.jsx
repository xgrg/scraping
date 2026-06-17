import { useState } from "react";

const CLUBS = {
  "11660020": "Argèles Tennis de Table",
  "11660013": "Bourg Madame TT",
  "11660044": "Canet Roussillon Tennis de Table",
  "11660001": "Canohes Toulouges Tennis de Table",
  "11660008": "Côte Vermeille TT",
  "11660031": "ENT Vallespir Tennis de Table",
  "11660043": "Illenc Tennis de Taule",
  "11660032": "Millas Tennis de Table",
  "11660009": "Perpignan Roussillon TT",
  "11660011": "Perpignan St Gauderique TT",
  "11660041": "Prades Conflent Canigó TT",
  "11660003": "Rivesaltes CTT",
  "11660021": "TT Club Laurentin",
  "11660007": "TT Thuirinois",
  "11660019": "US Torreilles US TT",
};

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const LOADING_STEPS = [
  { label: "Connexion à l'API fédération...", pct: 10 },
  { label: "Récupération des matchs...",      pct: 35 },
  { label: "Calcul des statistiques...",      pct: 60 },
  { label: "Génération des graphiques...",    pct: 80 },
  { label: "Préparation du fichier Excel...", pct: 95 },
];

const PLOTS = [
  { key: "plot_home_away",      label: "Domicile / Extérieur" },
  { key: "plot_participations", label: "Participations par phase" },
  { key: "plot_series",         label: "Séries" },
  { key: "plot_matrix",         label: "Matrice des matchs" },
];

export default function App() {
  const [clubId,   setClubId]   = useState("");
  const [status,   setStatus]   = useState("idle"); // idle | loading | done | error
  const [step,     setStep]     = useState(0);
  const [progress, setProgress] = useState(0);
  const [result,   setResult]   = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [lightbox, setLightbox] = useState(null);

  async function handleLaunch() {
    if (!clubId) return;
    setStatus("loading");
    setStep(0);
    setProgress(0);
    setResult(null);

    // Avance les étapes toutes les ~10 secondes (durée réelle ~60s)
    let idx = 0;
    const interval = setInterval(() => {
      if (idx < LOADING_STEPS.length) {
        setStep(idx);
        setProgress(LOADING_STEPS[idx].pct);
        idx++;
      }
    }, 10_000);

    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ club_id: clubId }),
      });
      clearInterval(interval);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `Erreur ${res.status}`);
      }
      const data = await res.json();
      setProgress(100);
      await new Promise((r) => setTimeout(r, 300));
      setResult(data);
      setStatus("done");
    } catch (e) {
      clearInterval(interval);
      setErrorMsg(e.message);
      setStatus("error");
    }
  }

  function handleReset() {
    setStatus("idle");
    setClubId("");
    setResult(null);
    setErrorMsg("");
    setProgress(0);
    setStep(0);
  }

  const Lightbox = () => (
    <div onClick={() => setLightbox(null)} style={{
      position: "fixed", inset: 0, zIndex: 999,
      background: "rgba(0,0,0,0.85)",
      display: "flex", alignItems: "center", justifyContent: "center",
      padding: "1rem",
    }}>
      <img src={lightbox} style={{ maxWidth: "100%", maxHeight: "100%", borderRadius: 8 }} />
    </div>
  );

  return (
    <div style={s.page}>
      <div style={s.app}>

        {/* ── Header ── */}
        <header style={s.header}>
          <div style={s.logoLine}>
            <div style={s.badge}>TT</div>
            <h1 style={s.h1}>Stats Tennis de Table</h1>
          </div>
          <p style={s.subtitle}>
            Sélectionne un club pour générer ses statistiques de saison
          </p>
        </header>

        {/* ── Sélecteur ── */}
        {status === "idle" && (
          <div style={s.card}>
            <label style={s.label} htmlFor="club-select">Club</label>
            <div style={s.selectWrap}>
              <select
                id="club-select"
                style={s.select}
                value={clubId}
                onChange={(e) => setClubId(e.target.value)}
              >
                <option value="">— Choisir un club —</option>
                {Object.entries(CLUBS).map(([id, name]) => (
                  <option key={id} value={id}>{name}</option>
                ))}
              </select>
              <span style={s.selectArrow} aria-hidden="true" />
            </div>
            <button
              style={{ ...s.launchBtn, ...(clubId ? {} : s.launchBtnDisabled) }}
              disabled={!clubId}
              onClick={handleLaunch}
            >
              📊 Générer les statistiques
            </button>
          </div>
        )}

        {/* ── Chargement ── */}
        {status === "loading" && (
          <div style={s.card}>
            <div style={s.ball} />
            <p style={s.loadingTitle}>{LOADING_STEPS[step]?.label}</p>
            <p style={s.loadingSub}>Collecte en cours, merci de patienter…</p>
            <div style={s.progressBar}>
              <div style={{ ...s.progressFill, width: `${progress}%` }} />
            </div>
          </div>
        )}

        {/* ── Erreur ── */}
        {status === "error" && (
          <div style={{ ...s.card, textAlign: "center" }}>
            <p style={{ color: "#ff6b6b", marginBottom: "1rem" }}>
              ⚠️ {errorMsg}
            </p>
            <button style={s.resetBtn} onClick={handleReset}>Réessayer</button>
          </div>
        )}

        {/* ── Résultats ── */}
        {status === "done" && result && (
          <div>
            <div style={s.resultsHeader}>
              <div style={s.clubBadge}>
                <span style={s.clubDot} />
                {CLUBS[result.club_id] ?? result.club_name}
              </div>
              <a
                href={`${API_BASE}${result.excel_url}`}
                download
                style={s.downloadBtn}
              >
                ⬇ Télécharger Excel
              </a>
            </div>

            <div style={s.plotsGrid}>
              {PLOTS.map(({ key, label }) => (
                <div key={key} style={s.plotCard}>
                  <div style={s.plotHeader}>{label}</div>
                  {result[key] ? (
                    <img
                      src={`data:image/jpeg;base64,${result[key]}`}
                      alt={label}
                      style={{ ...s.plotImg, cursor: "zoom-in" }}
                      onClick={() => setLightbox(`data:image/jpeg;base64,${result[key]}`)}
                    />
                  ) : (
                    <div style={s.plotEmpty}>Aucune donnée</div>
                  )}
                </div>
              ))}
            </div>

            <button style={s.resetBtn} onClick={handleReset}>
              ↩ Analyser un autre club
            </button>
          </div>
        )}

      </div>
      {lightbox && <Lightbox />}
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────────────────
const s = {
  page: {
    minHeight: "100vh",
    background: "#0f1117",
    color: "#e8e8e8",
    fontFamily: "'Inter', sans-serif",
    padding: "2rem 1rem",
  },
  app: {
    maxWidth: 900,
    margin: "0 auto",
  },
  header: { marginBottom: "2rem" },
  logoLine: { display: "flex", alignItems: "center", gap: 12, marginBottom: 4 },
  badge: {
    width: 36, height: 36,
    background: "#b5f542",
    borderRadius: "50%",
    display: "flex", alignItems: "center", justifyContent: "center",
    fontWeight: 700, fontSize: 14, color: "#0f1117",
    flexShrink: 0,
  },
  h1: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: 22, fontWeight: 600,
    color: "#ffffff", margin: 0, letterSpacing: "-0.3px",
  },
  subtitle: { fontSize: 13, color: "#6b7280", marginLeft: 48 },

  card: {
    background: "#1e2130",
    border: "0.5px solid #2d3148",
    borderRadius: 12,
    padding: "1.5rem",
    marginBottom: "1.5rem",
  },
  label: {
    display: "block",
    fontSize: 12, fontWeight: 500,
    color: "#9ca3af",
    textTransform: "uppercase",
    letterSpacing: "0.6px",
    marginBottom: 8,
  },
  selectWrap: { position: "relative" },
  select: {
    width: "100%",
    background: "#0f1117",
    border: "0.5px solid #3d4266",
    borderRadius: 8,
    color: "#e8e8e8",
    fontFamily: "inherit",
    fontSize: 14,
    padding: "10px 14px",
    appearance: "none",
    cursor: "pointer",
    outline: "none",
  },
  selectArrow: {
    position: "absolute",
    right: 14, top: "50%",
    transform: "translateY(-50%)",
    width: 0, height: 0,
    borderLeft: "5px solid transparent",
    borderRight: "5px solid transparent",
    borderTop: "5px solid #6b7280",
    pointerEvents: "none",
  },
  launchBtn: {
    marginTop: "1rem",
    width: "100%",
    background: "#b5f542",
    color: "#0f1117",
    border: "none",
    borderRadius: 8,
    padding: 12,
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: 14, fontWeight: 600,
    cursor: "pointer",
  },
  launchBtnDisabled: {
    background: "#2d3148",
    color: "#4b5563",
    cursor: "not-allowed",
  },

  ball: {
    width: 28, height: 28,
    background: "#b5f542",
    borderRadius: "50%",
    margin: "0 auto 1.5rem",
    animation: "bounce 0.7s ease-in-out infinite alternate",
  },
  loadingTitle: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: 15, fontWeight: 500,
    color: "#ffffff", textAlign: "center", marginBottom: 6,
  },
  loadingSub: { fontSize: 13, color: "#6b7280", textAlign: "center" },
  progressBar: {
    marginTop: "1.5rem", height: 3,
    background: "#2d3148", borderRadius: 2, overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    background: "#b5f542",
    borderRadius: 2,
    transition: "width 0.4s ease",
  },

  resultsHeader: {
    display: "flex", alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "1.25rem", flexWrap: "wrap", gap: 12,
  },
  clubBadge: {
    display: "flex", alignItems: "center", gap: 8,
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: 15, fontWeight: 500, color: "#ffffff",
  },
  clubDot: {
    width: 8, height: 8,
    background: "#b5f542", borderRadius: "50%", flexShrink: 0,
  },
  downloadBtn: {
    display: "flex", alignItems: "center", gap: 6,
    background: "transparent",
    border: "0.5px solid #b5f542",
    color: "#b5f542",
    borderRadius: 8,
    padding: "8px 14px",
    fontSize: 13, fontWeight: 500,
    cursor: "pointer",
    textDecoration: "none",
  },

  plotsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
    gap: 12,
    marginBottom: "1rem",
  },
  plotCard: {
    background: "#1e2130",
    border: "0.5px solid #2d3148",
    borderRadius: 12,
    overflow: "hidden",
  },
  plotHeader: {
    padding: "10px 14px",
    borderBottom: "0.5px solid #2d3148",
    fontSize: 12, fontWeight: 500,
    color: "#9ca3af",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  plotImg: { width: "100%", display: "block" },
  plotEmpty: {
    padding: "3rem",
    textAlign: "center",
    color: "#374151",
    fontSize: 13,
  },

  resetBtn: {
    background: "transparent",
    border: "0.5px solid #2d3148",
    color: "#6b7280",
    borderRadius: 8,
    padding: "8px 14px",
    fontSize: 13,
    cursor: "pointer",
    display: "flex", alignItems: "center", gap: 6,
    marginTop: "1rem",
    fontFamily: "inherit",
  },
};
