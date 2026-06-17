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
    { label: "Récupération des matchs...", pct: 35 },
    { label: "Calcul des statistiques...", pct: 60 },
    { label: "Génération des graphiques...", pct: 80 },
    { label: "Préparation du fichier Excel...", pct: 95 },
];

const PLOTS = [
    { key: "plot_home_away", label: "Domicile / Extérieur" },
    { key: "plot_participations", label: "Participations par phase" },
    { key: "plot_series", label: "Séries" },
    { key: "plot_matrix", label: "Matrice des matchs" },
];


function IconStats({ active }) {
    return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={active ? "#b5f542" : "#4b5563"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="12" width="4" height="9" />
            <rect x="10" y="7" width="4" height="14" />
            <rect x="17" y="3" width="4" height="18" />
        </svg>
    );
}

function IconPoster({ active }) {
    return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={active ? "#b5f542" : "#4b5563"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <circle cx="12" cy="10" r="3" />
            <path d="M6 21v-1a6 6 0 0 1 12 0v1" />
        </svg>
    );
}

// ── Page Stats ──────────────────────────────────────────────────────────────
function PageStats() {
    const [clubId, setClubId] = useState("");
    const [status, setStatus] = useState("idle"); // idle | loading | done | error
    const [step, setStep] = useState(0);
    const [progress, setProgress] = useState(0);
    const [result, setResult] = useState(null);
    const [errorMsg, setErrorMsg] = useState("");

    async function handleLaunch() {
        if (!clubId) return;
        setStatus("loading");
        setStep(0);
        setProgress(0);
        setResult(null);

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

    return (
        
        <div style={s.page}>
            <header style={s.header}>
                <div style={s.logoLine}>
                    <div style={s.badge}>TT</div>
                    <h1 style={s.h1}>Stats Tennis de Table</h1>
                </div>
                <p style={s.subtitle}>
                    Sélectionne un club pour générer ses statistiques de saison
                </p>
                </header>

                {/* ── Selector ── */}
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

                {/* ── Loading ── */}
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

                {/* ── Error ── */}
                {status === "error" && (
                <div style={{ ...s.card, textAlign: "center" }}>
                    <p style={{ color: "#ff6b6b", marginBottom: "1rem" }}>
                    ⚠️ {errorMsg}
                    </p>
                    <button style={s.resetBtn} onClick={handleReset}>Réessayer</button>
                </div>
                )}

                {/* ── Results ── */}
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
                                        (() => {
                                            const base64 = result[key];

                                            const handleOpen = () => {
                                                const binary = atob(base64);
                                                const bytes = new Uint8Array(binary.length);

                                                for (let i = 0; i < binary.length; i++) {
                                                    bytes[i] = binary.charCodeAt(i);
                                                }

                                                const blob = new Blob([bytes], { type: "image/jpeg" });
                                                const url = URL.createObjectURL(blob);

                                                window.open(url, "_blank");

                                                setTimeout(() => URL.revokeObjectURL(url), 60000);
                                            };

                                            return (
                                                <img
                                                    src={`data:image/jpeg;base64,${base64}`}
                                                    alt={label}
                                                    style={{ ...s.plotImg, cursor: "pointer" }}
                                                    onClick={handleOpen}
                                                />
                                            );
                                        })()
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

            <div style={s.placeholder}>
                <div style={s.placeholderIcon}>📊</div>
                <p style={s.placeholderText}>Les graphiques apparaîtront ici</p>
            </div>

        </div>
    );
}

// ── Page Affiche ────────────────────────────────────────────────────────────
const PHASES = [1, 2];
const JOURNEES = [1, 2, 3, 4, 5, 6, 7];

function PagePoster() {
    const [clubId, setClubId]   = useState("");
    const [phase, setPhase]     = useState(null);
    const [journee, setJournee] = useState(null);

    const [status, setStatus]   = useState("idle"); // idle | loading | done | error
    const [poster, setPoster]   = useState(null);   // base64 string
    const [errorMsg, setErrorMsg] = useState("");

    const ready = clubId && phase && journee;

    async function handleGenerate() {
        if (!ready) return;
        setStatus("loading");
        setPoster(null);

        try {
            const res = await fetch(`${API_BASE}/social/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    club_id:     clubId,
                    phase_index: phase,
                    match_index: journee,
                }),
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail ?? `Erreur ${res.status}`);
            }
            const data = await res.json();
            setPoster(data.plot_social);
            setStatus("done");
        } catch (e) {
            setErrorMsg(e.message);
            setStatus("error");
        }
    }

    function handleReset() {
        setStatus("idle");
        setPoster(null);
        setErrorMsg("");
    }

    function handleOpenFull() {
        const binary = atob(poster);
        const bytes  = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
        const blob = new Blob([bytes], { type: "image/png" });
        const url  = URL.createObjectURL(blob);
        window.open(url, "_blank");
        setTimeout(() => URL.revokeObjectURL(url), 60_000);
    }


    return (
        <div style={s.page}>
            <header style={s.header}>
                <div style={s.logoLine}>
                    <div style={s.badge}>TT</div>
                    <h1 style={s.h1}>Affiche journée</h1>
                </div>
                <p style={s.subtitle}>Génère une affiche à partager</p>
            </header>

            <div style={s.card}>
                <div style={s.field}>
                    <label style={s.label}>Club</label>
                    <div style={s.selectWrap}>
                        <select style={s.select} value={clubId} onChange={e => {
                                setClubId(e.target.value);
                                handleReset();
                            }}>
                            <option value="">— Choisir un club —</option>
                            {Object.entries(CLUBS).map(([id, name]) => (
                                <option key={id} value={id}>{name}</option>
                            ))}
                        </select>
                        <span style={s.selectArrow} />
                    </div>
                </div>

                <div style={s.field}>
                    <label style={s.label}>Phase</label>
                    <div style={s.segRow}>
                        {PHASES.map(p => (
                            <button key={p}
                                style={{ ...s.seg, ...(phase === p ? s.segOn : {}) }}
                                onClick={() => {
                                    setPhase(p);
                                    handleReset();
                                }}>
                                Phase {p}
                            </button>
                        ))}
                    </div>
                </div>

                <div style={s.field}>
                    <label style={s.label}>Journée</label>
                    <div style={{ ...s.segRow, flexWrap: "wrap" }}>
                        {JOURNEES.map(j => (
                            <button key={j}
                                style={{ ...s.seg, ...s.segTiny, ...(journee === j ? s.segOn : {}) }}
                                onClick={() => {
                                    setJournee(j);
                                    handleReset();
                                }}>
                                J{j}
                            </button>
                        ))}
                    </div>
                </div>

                <button
                    style={{ ...s.btn, ...(!ready || status === "loading" ? s.btnOff : {}) }}
                    disabled={!ready || status === "loading"}
                    onClick={handleGenerate}>
                    {status === "loading" ? "Génération…" : "Générer l'affiche"}
                </button>
            </div>

            {/* Loading */}
            {status === "loading" && (
                <div style={{ ...s.card, textAlign: "center" }}>
                    <div style={s.ball} />
                    <p style={s.loadingTitle}>Génération de l'affiche…</p>
                    <p style={s.loadingSub}>Collecte des matchs en cours, merci de patienter.</p>
                </div>
            )}

            {/* Error */}
            {status === "error" && (
                <div style={{ ...s.card, textAlign: "center" }}>
                    <p style={{ color: "#ff6b6b", marginBottom: "1rem" }}>⚠️ {errorMsg}</p>
                    <button style={s.resetBtn} onClick={handleReset}>Réessayer</button>
                </div>
            )}

            {/* Result */}
            {status === "done" && poster && (
                <div style={s.card}>
                    <div style={s.resultsHeader}>
                        <div style={s.clubBadge}>
                            <span style={s.clubDot} />
                            {CLUBS[clubId]} — J{journee} Ph.{phase}
                        </div>
                        <button style={s.downloadBtn} onClick={handleOpenFull}>
                            ↗ Plein écran
                        </button>
                    </div>
                    <img
                        src={`data:image/png;base64,${poster}`}
                        alt="Affiche journée"
                        style={{ ...s.plotImg, cursor: "pointer", borderRadius: 8 }}
                        onClick={handleOpenFull}
                    />
                    <button style={s.resetBtn} onClick={handleReset}>
                        ↩ Nouvelle affiche
                    </button>
                </div>
            )}
        </div>
    );
}


// ── App shell avec bottom nav ───────────────────────────────────────────────
export default function App() {
    const [tab, setTab] = useState("stats");
    

    return (
        <div style={s.shell}>
            {/* Contenu scrollable */}
            <div style={s.content}>
                {tab === "stats" && <PageStats />}
                {tab === "poster" && <PagePoster />}
            </div>

            {/* Bottom nav */}
            <nav style={s.nav}>
                <button style={s.navBtn} onClick={() => setTab("stats")}>
                    <IconStats active={tab === "stats"} />
                    <span style={{ ...s.navLabel, ...(tab === "stats" ? s.navLabelOn : {}) }}>
                        Stats
                    </span>
                </button>
                <button style={s.navBtn} onClick={() => setTab("poster")}>
                    <IconPoster active={tab === "poster"} />
                    <span style={{ ...s.navLabel, ...(tab === "poster" ? s.navLabelOn : {}) }}>
                        Affiche
                    </span>
                </button>
            </nav>
        </div>
    );
}

// ── Styles ──────────────────────────────────────────────────────────────────
const s = {
  // Mobile shell
  shell: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    background: "#0f1117",
    color: "#e8e8e8",
    fontFamily: "'Inter', sans-serif",
    maxWidth: 480,
    margin: "0 auto",
    position: "relative",
  },

  content: {
    flex: 1,
    overflowY: "auto",
  },

  // Generic layouts
  page: {
    minHeight: "100vh",
    padding: "1.5rem 1rem",
  },

  app: {
    maxWidth: 900,
    margin: "0 auto",
  },

  // Headers
  pageHeader: {
    marginBottom: "1.5rem",
  },

  header: {
    marginBottom: "2rem",
  },

  logoRow: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    marginBottom: 4,
  },

  logoLine: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    marginBottom: 4,
  },

  badge: {
    width: 36,
    height: 36,
    background: "#b5f542",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: 700,
    fontSize: 14,
    color: "#0f1117",
    flexShrink: 0,
  },

  h1: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: 22,
    fontWeight: 600,
    color: "#ffffff",
    margin: 0,
    letterSpacing: "-0.3px",
  },

  subtitle: {
    fontSize: 13,
    color: "#6b7280",
    marginLeft: 48,
  },

  // Cards
  card: {
    background: "#1e2130",
    border: "0.5px solid #2d3148",
    borderRadius: 12,
    padding: "1.5rem",
    marginBottom: "1.5rem",
  },

  // Forms
  field: {
    marginBottom: "1.1rem",
  },

  label: {
    display: "block",
    fontSize: 12,
    fontWeight: 500,
    color: "#9ca3af",
    textTransform: "uppercase",
    letterSpacing: "0.6px",
    marginBottom: 8,
  },

  selectWrap: {
    position: "relative",
  },

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

  arrow: {
    position: "absolute",
    right: 14,
    top: "50%",
    transform: "translateY(-50%)",
    width: 0,
    height: 0,
    borderLeft: "5px solid transparent",
    borderRight: "5px solid transparent",
    borderTop: "5px solid #6b7280",
    pointerEvents: "none",
  },

  // Alias for compatibility
  selectArrow: {
    position: "absolute",
    right: 14,
    top: "50%",
    transform: "translateY(-50%)",
    width: 0,
    height: 0,
    borderLeft: "5px solid transparent",
    borderRight: "5px solid transparent",
    borderTop: "5px solid #6b7280",
    pointerEvents: "none",
  },

  // Segmented controls
  segRow: {
    display: "flex",
    gap: 6,
  },

  seg: {
    flex: 1,
    background: "#0f1117",
    borderWidth: "0.5px",
    borderStyle: "solid",
    borderColor: "#3d4266",
    borderRadius: 8,
    color: "#9ca3af",
    fontFamily: "inherit",
    fontSize: 13,
    padding: "9px 4px",
    cursor: "pointer",
    textAlign: "center",
    transition: "all 0.15s",
  },

  segTiny: {
    flex: "0 0 calc(12.5% - 6px)",
    minWidth: 34,
  },

  segOn: {
    background: "#b5f542",
    borderColor: "#b5f542",
    color: "#0f1117",
    fontWeight: 600,
  },

  hint: {
    marginTop: 7,
    fontSize: 12,
    color: "#4b5563",
    fontStyle: "italic",
  },

  // Buttons
  btn: {
    width: "100%",
    marginTop: "0.25rem",
    background: "#b5f542",
    color: "#0f1117",
    border: "none",
    borderRadius: 8,
    padding: 12,
    fontFamily: "inherit",
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
  },

  btnOff: {
    background: "#2d3148",
    color: "#4b5563",
    cursor: "not-allowed",
  },

  // Aliases
  launchBtn: {
    marginTop: "1rem",
    width: "100%",
    background: "#b5f542",
    color: "#0f1117",
    border: "none",
    borderRadius: 8,
    padding: 12,
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
  },

  launchBtnDisabled: {
    background: "#2d3148",
    color: "#4b5563",
    cursor: "not-allowed",
  },

  // Loading
  ball: {
    width: 28,
    height: 28,
    background: "#b5f542",
    borderRadius: "50%",
    margin: "0 auto 1.5rem",
    animation: "bounce 0.7s ease-in-out infinite alternate",
  },

  loadingTitle: {
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: 15,
    fontWeight: 500,
    color: "#ffffff",
    textAlign: "center",
    marginBottom: 6,
  },

  loadingSub: {
    fontSize: 13,
    color: "#6b7280",
    textAlign: "center",
  },

  progressBar: {
    marginTop: "1.5rem",
    height: 3,
    background: "#2d3148",
    borderRadius: 2,
    overflow: "hidden",
  },

  progressFill: {
    height: "100%",
    background: "#b5f542",
    borderRadius: 2,
    transition: "width 0.4s ease",
  },

  // Results
  resultsHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "1.25rem",
    flexWrap: "wrap",
    gap: 12,
  },

  clubBadge: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    fontFamily: "'Space Grotesk', sans-serif",
    fontSize: 15,
    fontWeight: 500,
    color: "#ffffff",
  },

  clubDot: {
    width: 8,
    height: 8,
    background: "#b5f542",
    borderRadius: "50%",
    flexShrink: 0,
  },

  downloadBtn: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    background: "transparent",
    border: "0.5px solid #b5f542",
    color: "#b5f542",
    borderRadius: 8,
    padding: "8px 14px",
    fontSize: 13,
    fontWeight: 500,
    cursor: "pointer",
    textDecoration: "none",
  },

  // Plots
  plotsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(1, minmax(0, 1fr))",
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
    fontSize: 12,
    fontWeight: 500,
    color: "#9ca3af",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },

  plotImg: {
    width: "100%",
    display: "block",
  },

  plotEmpty: {
    padding: "3rem",
    textAlign: "center",
    color: "#374151",
    fontSize: 13,
  },

  // Empty state
  placeholder: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    padding: "3rem 1rem",
    gap: 12,
  },

  placeholderIcon: {
    fontSize: 40,
    opacity: 0.3,
  },

  placeholderText: {
    fontSize: 13,
    color: "#374151",
  },

  // Reset
  resetBtn: {
    background: "transparent",
    border: "0.5px solid #2d3148",
    color: "#6b7280",
    borderRadius: 8,
    padding: "8px 14px",
    fontSize: 13,
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: 6,
    marginTop: "1rem",
    fontFamily: "inherit",
  },

  // Bottom navigation
  nav: {
    position: "fixed",
    bottom: 0,
    left: "50%",
    transform: "translateX(-50%)",
    width: "100%",
    maxWidth: 480,
    height: 64,
    background: "#1e2130",
    borderTop: "0.5px solid #2d3148",
    display: "flex",
    zIndex: 100,
  },

  navBtn: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    background: "transparent",
    border: "none",
    cursor: "pointer",
    padding: "8px 0 10px",
  },

  navLabel: {
    fontSize: 11,
    fontWeight: 500,
    color: "#4b5563",
    letterSpacing: "0.3px",
  },

  navLabelOn: {
    color: "#b5f542",
  },
};