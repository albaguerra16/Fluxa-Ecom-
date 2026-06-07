"""Design system Fluxa — estilo Apple / Nu Bank."""

FONTS = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
"""

BASE_CSS = FONTS + """
<style>
/* ── Reset & base ─────────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main {
  background: #07070f !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── Ocultar elementos Streamlit ──────────────────────────────────────────── */
footer, #MainMenu, [data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

/* Ocultar solo el branding del header, NO el botón de sidebar */
header [data-testid="stAppViewBlockContainer"],
[data-testid="stHeader"] { display: none !important; }

/* Botón de expandir sidebar — siempre visible */
[data-testid="collapsedControl"] {
  display: flex !important;
  visibility: visible !important;
  opacity: 1 !important;
}

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: #05050c !important;
  border-right: 1px solid #111120 !important;
  min-width: 230px !important;
  max-width: 230px !important;
  display: block !important;
  visibility: visible !important;
}
[data-testid="stSidebar"][aria-expanded="false"] {
  min-width: 0 !important;
  max-width: 0 !important;
}
[data-testid="stSidebar"] > div:first-child {
  padding: 0 !important;
}

/* Botones del sidebar como nav items */
[data-testid="stSidebar"] .stButton > button {
  background: transparent !important;
  border: none !important;
  border-radius: 10px !important;
  color: #4a4a6a !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  text-align: left !important;
  padding: 0.55rem 1rem !important;
  width: 100% !important;
  transition: background 0.15s, color 0.15s !important;
  box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: #0f0f20 !important;
  color: #a0a0c8 !important;
}
[data-testid="stSidebar"] .stButton > button:focus {
  box-shadow: none !important;
  outline: none !important;
}

/* Sidebar nav item activo */
[data-testid="stSidebar"] .stButton > button[data-active="true"] {
  background: #13132a !important;
  color: #a78bfa !important;
  font-weight: 600 !important;
}

/* ── Tipografía ───────────────────────────────────────────────────────────── */
h1, h2, h3, h4 {
  font-family: 'Inter', sans-serif !important;
  color: #f0f0f8 !important;
  letter-spacing: -0.03em !important;
}

p, span, div { font-family: 'Inter', sans-serif !important; }

/* ── Cards ────────────────────────────────────────────────────────────────── */
.fx-card {
  background: #0d0d1a;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04);
  transition: box-shadow 0.2s;
}
.fx-card:hover {
  box-shadow: 0 4px 20px rgba(0,0,0,0.5), 0 0 0 1px rgba(167,139,250,0.15);
}
.fx-card-flat {
  background: #0d0d1a;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.04);
}

/* ── Botón primario ───────────────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
  background: #7c3aed !important;
  border: none !important;
  border-radius: 50px !important;
  color: white !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.9rem !important;
  font-weight: 600 !important;
  padding: 0.6rem 1.8rem !important;
  letter-spacing: -0.01em !important;
  transition: background 0.2s, transform 0.1s !important;
  box-shadow: 0 0 20px rgba(124,58,237,0.35) !important;
}
.stButton > button[kind="primary"]:hover {
  background: #6d28d9 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 0 30px rgba(124,58,237,0.5) !important;
}
.stButton > button[kind="primary"]:active {
  transform: translateY(0) !important;
}

/* Botón secundario */
.stButton > button[kind="secondary"] {
  background: transparent !important;
  border: 1px solid #1e1e35 !important;
  border-radius: 50px !important;
  color: #6b6b8a !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
}
.stButton > button[kind="secondary"]:hover {
  border-color: #3d3d6a !important;
  color: #a0a0c8 !important;
}

/* Botón normal (no kind) */
.stButton > button:not([kind]) {
  background: transparent !important;
  border: 1px solid #1a1a2e !important;
  border-radius: 10px !important;
  color: #5a5a7a !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.875rem !important;
  transition: all 0.15s !important;
  box-shadow: none !important;
}
.stButton > button:not([kind]):hover {
  border-color: #7c3aed !important;
  color: #a78bfa !important;
  background: rgba(124,58,237,0.06) !important;
}

/* ── Inputs ───────────────────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
  background: #0d0d1a !important;
  border: 1px solid #1a1a2e !important;
  border-radius: 12px !important;
  color: #e0e0f0 !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.9rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: #7c3aed !important;
  box-shadow: 0 0 0 3px rgba(124,58,237,0.15) !important;
}

/* Labels */
.stTextInput label, .stTextArea label,
.stSelectbox label, .stNumberInput label,
.stSlider label, .stCheckbox label {
  color: #4a4a6a !important;
  font-size: 0.8rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.02em !important;
  text-transform: uppercase !important;
}

/* Slider */
.stSlider [data-baseweb="slider"] [data-testid="stTickBar"] {
  color: #3a3a5a !important;
}

/* ── Status / spinner ─────────────────────────────────────────────────────── */
[data-testid="stStatusWidget"] {
  background: #0d0d1a !important;
  border: 1px solid #1a1a2e !important;
  border-radius: 12px !important;
}

/* ── Expander ─────────────────────────────────────────────────────────────── */
.streamlit-expanderHeader {
  background: #0d0d1a !important;
  border: 1px solid #1a1a2e !important;
  border-radius: 12px !important;
  color: #a0a0c0 !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
}
.streamlit-expanderContent {
  background: #0a0a16 !important;
  border: 1px solid #1a1a2e !important;
  border-top: none !important;
}

/* ── Divider ──────────────────────────────────────────────────────────────── */
.fx-divider {
  height: 1px;
  background: #111120;
  margin: 1.5rem 0;
}

/* ── Page header ──────────────────────────────────────────────────────────── */
.fx-page-header {
  padding: 2rem 0 1.5rem;
  border-bottom: 1px solid #111120;
  margin-bottom: 2rem;
}
.fx-page-title {
  font-size: 1.75rem;
  font-weight: 800;
  color: #f0f0f8;
  letter-spacing: -0.04em;
  margin: 0;
  line-height: 1.1;
}
.fx-page-sub {
  font-size: 0.875rem;
  color: #3a3a5a;
  margin: 0.4rem 0 0;
  font-weight: 400;
}

/* ── Etiqueta de sección ──────────────────────────────────────────────────── */
.fx-section-label {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #2a2a42;
  margin-bottom: 0.8rem;
  display: block;
}

/* ── Badge de ángulo ──────────────────────────────────────────────────────── */
.fx-badge {
  display: inline-block;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 0.2rem 0.75rem;
  border-radius: 20px;
  margin-bottom: 0.75rem;
}
.fx-badge-green  { background: rgba(16,185,129,0.12); color: #10b981; }
.fx-badge-blue   { background: rgba(59,130,246,0.12); color: #60a5fa; }
.fx-badge-purple { background: rgba(167,139,250,0.12); color: #a78bfa; }
.fx-badge-orange { background: rgba(251,146,60,0.12);  color: #fb923c; }
.fx-badge-pink   { background: rgba(244,114,182,0.12); color: #f472b6; }

/* ── Stat grande ──────────────────────────────────────────────────────────── */
.fx-stat {
  padding: 2rem;
  background: #0d0d1a;
  border-radius: 20px;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.04);
  text-align: center;
}
.fx-stat-num  { font-size: 3.5rem; font-weight: 900; letter-spacing: -0.05em; line-height: 1; }
.fx-stat-lbl  { font-size: 0.8rem; color: #3a3a5a; margin-top: 0.5rem; font-weight: 500; letter-spacing: 0.04em; text-transform: uppercase; }

/* ── Veredicto ────────────────────────────────────────────────────────────── */
.fx-veredicto {
  padding: 2rem;
  border-radius: 20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.fx-veredicto-lanzar    { background: rgba(16,185,129,0.08); box-shadow: 0 0 0 1px rgba(16,185,129,0.2); }
.fx-veredicto-precaucion { background: rgba(245,158,11,0.08); box-shadow: 0 0 0 1px rgba(245,158,11,0.2); }
.fx-veredicto-no        { background: rgba(239,68,68,0.08);  box-shadow: 0 0 0 1px rgba(239,68,68,0.2); }
.fx-veredicto-titulo    { font-size: 1.75rem; font-weight: 900; color: #f0f0f8; letter-spacing: -0.04em; }
.fx-veredicto-kw        { font-size: 0.85rem; color: #3a3a5a; margin-top: 0.4rem; }

/* ── Criterio card ────────────────────────────────────────────────────────── */
.fx-criterio {
  padding: 1rem 1.2rem;
  border-radius: 12px;
  margin-bottom: 0.5rem;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.03);
}
.fx-criterio-ok   { background: rgba(16,185,129,0.06);  border-left: 3px solid #10b981; }
.fx-criterio-warn { background: rgba(245,158,11,0.06);  border-left: 3px solid #f59e0b; }
.fx-criterio-fail { background: rgba(239,68,68,0.06);   border-left: 3px solid #ef4444; }
.fx-criterio-titulo { font-size: 0.88rem; font-weight: 600; color: #d0d0e8; }
.fx-criterio-nota   { font-size: 0.78rem; color: #4a4a6a; margin-top: 0.25rem; line-height: 1.5; }

/* ── Producto card (dashboard) ────────────────────────────────────────────── */
.fx-prod {
  background: #0d0d1a;
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.04);
  transition: box-shadow 0.2s, transform 0.2s;
  cursor: pointer;
}
.fx-prod:hover {
  box-shadow: 0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(124,58,237,0.25);
  transform: translateY(-3px);
}
.fx-prod-icon {
  width: 100%;
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #111120;
  font-size: 3rem;
}
.fx-prod-body { padding: 1rem; }
.fx-prod-nombre { font-size: 0.9rem; font-weight: 700; color: #e0e0f0;
                  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.fx-prod-fecha  { font-size: 0.72rem; color: #2a2a42; margin-top: 0.2rem; }
.fx-prod-badge  {
  display: inline-block;
  background: rgba(124,58,237,0.2);
  color: #a78bfa;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 20px;
  margin-top: 0.5rem;
}

/* ── Nuevo producto card ──────────────────────────────────────────────────── */
.fx-prod-new {
  background: transparent;
  border-radius: 18px;
  border: 1px dashed #1a1a2e;
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #2a2a42;
  font-size: 0.85rem;
  font-weight: 500;
  transition: border-color 0.2s, color 0.2s;
  cursor: pointer;
}
.fx-prod-new:hover { border-color: #7c3aed; color: #7c3aed; }

/* ── Selector de producto ─────────────────────────────────────────────────── */
.fx-selector-wrap {
  display: flex;
  gap: 0.75rem;
  overflow-x: auto;
  padding: 0.25rem 0 1rem;
  scrollbar-width: none;
}
.fx-selector-wrap::-webkit-scrollbar { display: none; }
.fx-selector-item {
  flex-shrink: 0;
  background: #0d0d1a;
  border: 1px solid #1a1a2e;
  border-radius: 14px;
  padding: 0.75rem 1.2rem;
  cursor: pointer;
  transition: all 0.15s;
  text-align: center;
  min-width: 100px;
}
.fx-selector-item:hover  { border-color: #7c3aed; }
.fx-selector-item.active { border-color: #7c3aed; background: rgba(124,58,237,0.08); }
.fx-selector-emoji { font-size: 1.5rem; display: block; }
.fx-selector-name  { font-size: 0.78rem; font-weight: 600; color: #8080a0; margin-top: 0.3rem; display: block; }
.fx-selector-name.active { color: #a78bfa; }

/* ── Storyboard escena ────────────────────────────────────────────────────── */
.fx-scene {
  background: #0a0a16;
  border-radius: 12px;
  padding: 1rem 1.25rem;
  margin-bottom: 0.5rem;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.03);
}
.fx-scene-header { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.6rem; }
.fx-scene-time   { font-size: 0.68rem; font-weight: 700; color: #7c3aed; letter-spacing: 0.06em; background: rgba(124,58,237,0.1); padding: 0.15rem 0.5rem; border-radius: 6px; }
.fx-scene-label  { font-size: 0.68rem; font-weight: 700; color: #3a3a5a; letter-spacing: 0.08em; text-transform: uppercase; }
.fx-scene-key    { font-size: 0.72rem; color: #3a3a5a; text-transform: uppercase; letter-spacing: 0.06em; margin: 0.4rem 0 0.15rem; }
.fx-scene-val    { font-size: 0.88rem; color: #c0c0d8; line-height: 1.55; }
.fx-scene-val-em { font-size: 0.88rem; color: #d4c8ff; line-height: 1.55; font-style: italic; }

/* ── Info row ─────────────────────────────────────────────────────────────── */
.fx-info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.6rem 0;
  border-bottom: 1px solid #0f0f1e;
  font-size: 0.875rem;
}
.fx-info-label { color: #3a3a5a; font-weight: 500; }
.fx-info-value { color: #c0c0d8; font-weight: 600; }

/* ── Riesgo / problema ────────────────────────────────────────────────────── */
.fx-riesgo {
  background: rgba(239,68,68,0.05);
  border-left: 2px solid rgba(239,68,68,0.4);
  border-radius: 8px;
  padding: 0.65rem 1rem;
  font-size: 0.85rem;
  color: #c0a0a0;
  margin-bottom: 0.4rem;
  line-height: 1.5;
}
.fx-beneficio {
  background: rgba(16,185,129,0.05);
  border-left: 2px solid rgba(16,185,129,0.3);
  border-radius: 8px;
  padding: 0.65rem 1rem;
  font-size: 0.85rem;
  color: #90c0a8;
  margin-bottom: 0.4rem;
  line-height: 1.5;
}

/* ── Empty state ──────────────────────────────────────────────────────────── */
.fx-empty {
  text-align: center;
  padding: 4rem 2rem;
}
.fx-empty-icon { font-size: 2.5rem; margin-bottom: 1rem; display: block; opacity: 0.3; }
.fx-empty-text { color: #2a2a42; font-size: 0.95rem; font-weight: 500; }
.fx-empty-sub  { color: #1e1e30; font-size: 0.8rem; margin-top: 0.4rem; }

/* ── Márgenes ─────────────────────────────────────────────────────────────── */
.fx-margen-row {
  display: flex;
  justify-content: space-between;
  padding: 0.7rem 0;
  border-bottom: 1px solid #0f0f1e;
  font-size: 0.9rem;
}
.fx-margen-label { color: #4a4a6a; }
.fx-margen-pos   { color: #10b981; font-weight: 700; }
.fx-margen-neg   { color: #ef4444; font-weight: 700; }
.fx-margen-total { color: #f0f0f8; font-weight: 800; font-size: 1rem; }
</style>
"""

# Paleta de colores (referencia para Python)
COLORS = {
    "bg":         "#07070f",
    "bg_card":    "#0d0d1a",
    "bg_dark":    "#05050c",
    "border":     "#1a1a2e",
    "accent":     "#7c3aed",
    "accent_lt":  "#a78bfa",
    "text":       "#f0f0f8",
    "text_sec":   "#4a4a6a",
    "green":      "#10b981",
    "yellow":     "#f59e0b",
    "red":        "#ef4444",
    "blue":       "#60a5fa",
    "pink":       "#f472b6",
}

ANGULO_BADGE = {
    "BENEFICIO":   ("fx-badge-green",  "💚"),
    "COMPETITIVO": ("fx-badge-blue",   "💙"),
    "VALIDACIÓN":  ("fx-badge-purple", "💜"),
    "TESTIMONIAL": ("fx-badge-orange", "🧡"),
    "EMOCIONAL":   ("fx-badge-pink",   "🩷"),
}

ANGULO_BORDER = {
    "BENEFICIO":   "#10b981",
    "COMPETITIVO": "#60a5fa",
    "VALIDACIÓN":  "#a78bfa",
    "TESTIMONIAL": "#fb923c",
    "EMOCIONAL":   "#f472b6",
}
