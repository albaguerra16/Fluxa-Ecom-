"""Fluxa — Suite de lanzamiento para dropshipping COD Colombia.

Lanzar:
    streamlit run Inicio.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).parent
os.chdir(_ROOT)
sys.path.insert(0, str(_ROOT))

import streamlit as st

from fluxa import db, styles
from fluxa.auth import check_login

# ── Config ────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Fluxa",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(styles.BASE_CSS, unsafe_allow_html=True)

# ── Auth ──────────────────────────────────────────────────────────────────────
if not check_login():
    st.stop()

# ── Estado ────────────────────────────────────────────────────────────────────

def _s(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

_s("pagina", "productos")
_s("pid", None)
_s("pnombre", "")
_s("mostrar_nuevo", False)

db.init_db()


def _ir(pagina: str, pid=None, pnombre=""):
    st.session_state.pagina = pagina
    if pid is not None:
        st.session_state.pid = pid
        st.session_state.pnombre = pnombre
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

_NAV_LABELS = {
    "productos":   "📦 Mis Productos",
    "validacion":  "🔍 Validar Producto",
    "copy":        "🎯 Copy & Ángulos",
    "storyboards": "🎬 Storyboards",
    "landing":     "📄 Landing Sections",
    "upsells":     "🖼️ Upsells",
    "resenas":     "🌟 Reseñas Visuales",
    "lanzar":      "🚀 Lanzar",
    "margenes":    "💰 Márgenes COD",
}

_NAV_GROUPS = [
    ("", ["productos"]),
    ("INVESTIGAR", ["validacion"]),
    ("CREAR", ["copy", "storyboards", "landing", "upsells", "resenas"]),
    ("LANZAR", ["lanzar", "margenes"]),
]

with st.sidebar:
    st.markdown("""
    <div style="padding:1.5rem 0 1rem;text-align:center">
      <span style="font-size:1.6rem;font-weight:900;color:#f0f0f8;
                   letter-spacing:-0.04em">⚡ fluxa</span>
    </div>
    """, unsafe_allow_html=True)

    pg = st.session_state.pagina

    for group_label, keys in _NAV_GROUPS:
        if group_label:
            st.markdown(f"""
            <div style="padding:0.8rem 0 0.2rem 0.5rem;font-size:0.6rem;font-weight:700;
                        letter-spacing:0.14em;text-transform:uppercase;color:#2a2a42">
              {group_label}
            </div>
            """, unsafe_allow_html=True)
        for key in keys:
            label = _NAV_LABELS[key]
            is_active = pg == key
            btn_style = (
                "background-color:#13132a;color:#a78bfa;font-weight:600;"
                if is_active else
                "background-color:transparent;color:#4a4a6a;"
            )
            st.markdown(f"""
            <style>
            div[data-testid="stSidebar"] div[data-testid="stButton"]
              button[kind="secondary"]#btn_{key} {{
                {btn_style}
            }}
            </style>
            """, unsafe_allow_html=True)
            if st.sidebar.button(
                label, key=f"_nav_{key}",
                use_container_width=True,
                type="secondary",
            ):
                st.session_state.pagina = key
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    nombre = st.session_state.get("_auth_name", "Alba Guerra")
    st.markdown(f"""
    <div style="padding:0.8rem 0.5rem;border-top:1px solid #111120;
                font-size:0.78rem;color:#2a2a42">
      {nombre}
    </div>
    """, unsafe_allow_html=True)
    if st.sidebar.button("↩ Cerrar sesión", key="_logout", use_container_width=True):
        st.session_state["_auth_ok"] = False
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# UTILIDADES COMPARTIDAS
# ══════════════════════════════════════════════════════════════════════════════

def _page_header(icon: str, title: str, sub: str = ""):
    st.markdown(f"""
    <div class="fx-page-header">
      <div class="fx-page-title">{icon} {title}</div>
      {'<div class="fx-page-sub">' + sub + '</div>' if sub else ''}
    </div>
    """, unsafe_allow_html=True)


def _selector_producto(modulo: str) -> tuple[int | None, str]:
    productos = db.listar(modulo="producto", limite=50)

    if not productos:
        st.markdown("""
        <div class="fx-empty">
          <span class="fx-empty-icon">📦</span>
          <div class="fx-empty-text">Sin productos aún</div>
          <div class="fx-empty-sub">Ve a Mis Productos y crea el primero</div>
        </div>
        """, unsafe_allow_html=True)
        col_, col_btn, col__ = st.columns([2, 1, 2])
        with col_btn:
            if st.button("→ Mis Productos", type="primary"):
                _ir("productos")
        return None, ""

    st.markdown('<span class="fx-section-label">Producto de trabajo</span>', unsafe_allow_html=True)

    pid_actual = st.session_state.pid
    cols = st.columns(min(len(productos), 7), gap="small")

    for col, p in zip(cols, productos):
        nombre = p["datos"].get("nombre", p["producto"])
        emoji  = p["datos"].get("emoji",  "📦")
        es_act = p["id"] == pid_actual
        with col:
            cls_name = "active" if es_act else ""
            name_cls = "active" if es_act else ""
            st.markdown(f"""
            <div class="fx-selector-item {cls_name}" style="margin-bottom:0.3rem">
              <span class="fx-selector-emoji">{emoji}</span>
              <span class="fx-selector-name {name_cls}">{nombre[:12]}</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("·" if not es_act else "✓", key=f"_sel_{modulo}_{p['id']}",
                         use_container_width=True):
                st.session_state.pid = p["id"]
                st.session_state.pnombre = nombre
                st.rerun()

    st.markdown("<div class='fx-divider'></div>", unsafe_allow_html=True)
    return st.session_state.pid, st.session_state.pnombre


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: MIS PRODUCTOS
# ══════════════════════════════════════════════════════════════════════════════

def _pagina_productos():
    _page_header("📦", "Mis Productos",
                 "Crea un producto — trabaja en él desde cualquier módulo del sidebar")

    productos = db.listar(modulo="producto", limite=50)

    # Grid 5 columnas
    cols = st.columns(5, gap="medium")

    for i, p in enumerate(productos):
        nombre = p["datos"].get("nombre", p["producto"])
        emoji  = p["datos"].get("emoji",  "📦")
        fecha  = p["fecha"][:10]
        piezas = len([s for s in db.listar(limite=500)
                      if s["producto"] == nombre and s["modulo"] != "producto"])
        with cols[i % 5]:
            st.markdown(f"""
            <div class="fx-prod">
              <div class="fx-prod-icon">{emoji}</div>
              <div class="fx-prod-body">
                <div class="fx-prod-nombre">{nombre}</div>
                <div class="fx-prod-fecha">{fecha}</div>
                {'<span class="fx-prod-badge">' + str(piezas) + ' piezas</span>' if piezas else ''}
              </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Abrir", key=f"_prod_{p['id']}", use_container_width=True):
                st.session_state.pid = p["id"]
                st.session_state.pnombre = nombre
                _ir("copy")

    # Card nuevo producto
    with cols[len(productos) % 5]:
        st.markdown("""
        <div class="fx-prod-new" style="min-height:160px">
          <span style="font-size:1.8rem;opacity:0.4">＋</span>
          <span style="margin-top:0.4rem;font-size:0.8rem">Nuevo producto</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Crear", key="_nuevo_btn", use_container_width=True):
            st.session_state.mostrar_nuevo = True
            st.rerun()

    # Input nuevo producto
    if st.session_state.mostrar_nuevo:
        st.markdown("<div class='fx-divider'></div>", unsafe_allow_html=True)
        st.markdown('<span class="fx-section-label">Nuevo producto</span>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 5, 1], gap="small")
        with c1:
            emoji_n = st.text_input("Emoji", value="📦", max_chars=2,
                                    label_visibility="collapsed")
        with c2:
            nombre_n = st.text_input("Nombre", placeholder="ej: faja moldeadora...",
                                     label_visibility="collapsed")
        with c3:
            if st.button("Crear", type="primary", disabled=not nombre_n.strip()):
                pid = db.guardar(nombre_n.strip(), "producto",
                                 {"nombre": nombre_n.strip(), "emoji": emoji_n.strip() or "📦"})
                st.session_state.mostrar_nuevo = False
                st.session_state.pid = pid
                st.session_state.pnombre = nombre_n.strip()
                _ir("copy")

        if st.button("Cancelar", key="_cancel_nuevo"):
            st.session_state.mostrar_nuevo = False
            st.rerun()

    # Gestionar
    if productos:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("Gestionar productos"):
            for p in productos:
                nombre = p["datos"].get("nombre", p["producto"])
                ca, cb = st.columns([6, 1])
                with ca:
                    st.write(f"**{p['datos'].get('emoji','📦')}** {nombre}")
                with cb:
                    if st.button("Eliminar", key=f"_del_{p['id']}"):
                        db.eliminar(p["id"])
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: VALIDAR PRODUCTO
# ══════════════════════════════════════════════════════════════════════════════

def _pagina_validacion():
    _page_header("🔍", "Validar Producto",
                 "9 criterios · Score de viabilidad · Veredicto · Buyer Persona")

    pid, pnombre = _selector_producto("validacion")
    if not pid:
        return

    # Cargar resultado previo
    hist = [s for s in db.listar(limite=300)
            if s["producto"] == pnombre and s["modulo"] == "analisis"]
    datos_prev = hist[0]["datos"] if hist else None

    # Controles
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1], gap="small")
    with c1:
        demo = st.checkbox("Modo demo", value=False)
    with c2:
        usar_web = st.checkbox("Búsqueda web real", value=True)
    with c3:
        usar_tri = st.checkbox("ML + Trends + Meta", value=True)
    with c4:
        analizar_btn = st.button("⚡ Analizar", type="primary")

    if analizar_btn:
        import asyncio
        with st.status(f"Analizando **{pnombre}**…", expanded=True) as status:
            try:
                if demo:
                    ml_d  = {"total_productos": 1500, "num_marcas": 22, "dominios": []}
                    tr_d  = {"interes_promedio": 55.0, "interes_peak": 100, "tendencia": 0.8}
                    meta_d = {"num_anuncios": 12}
                    mkt_d  = {"num_publicaciones": 18}
                else:
                    if usar_tri:
                        from trendia.triangulator.mercadolibre import buscar
                        from trendia.triangulator.trends import interes_colombia
                        from trendia.triangulator.meta_ads import _scrape_async as _ma
                        from trendia.triangulator.fb_marketplace import _scrape_async as _fm

                        st.write("📊 MercadoLibre…")
                        ml_r = buscar(pnombre)
                        ml_d = {"total_productos": ml_r.total_productos,
                                "num_marcas": ml_r.num_marcas, "dominios": ml_r.dominios}

                        st.write("📈 Google Trends…")
                        tr_r = interes_colombia(pnombre)
                        tr_d = {"interes_promedio": tr_r.interes_promedio,
                                "interes_peak": tr_r.interes_peak, "tendencia": tr_r.tendencia}

                        st.write("📱 Meta Ads + Marketplace…")
                        meta_r, mkt_r = asyncio.run(asyncio.gather(_ma(pnombre), _fm(pnombre)))
                        meta_d = {"num_anuncios": meta_r.num_anuncios}
                        mkt_d  = {"num_publicaciones": mkt_r.num_publicaciones}
                    else:
                        ml_d  = {"total_productos": 0, "num_marcas": 0, "dominios": []}
                        tr_d  = {"interes_promedio": 0, "interes_peak": 0, "tendencia": 0}
                        meta_d = {"num_anuncios": 0}
                        mkt_d  = {"num_publicaciones": 0}

                st.write("🤖 Claude — 9 criterios + buyer persona…")
                from trendia.analyzer.motor import analizar as _analizar
                analisis = _analizar(
                    keyword=pnombre,
                    ml_data=ml_d, trends_data=tr_d,
                    meta_data=meta_d, marketplace_data=mkt_d,
                    usar_web_search=usar_web,
                )

                datos_g = {
                    "keyword": analisis.keyword,
                    "score_total": analisis.score_total,
                    "score_pct": analisis.score_pct,
                    "veredicto": analisis.veredicto,
                    "aprobados": analisis.aprobados,
                    "en_riesgo": analisis.en_riesgo,
                    "reprobados": analisis.reprobados,
                    "criterios": [{"numero": c.numero, "nombre": c.nombre,
                                   "estado": c.estado, "nota": c.nota,
                                   "puntos": c.puntos} for c in analisis.criterios],
                    "angulos_venta": [{"nombre": a.nombre, "hook": a.hook, "copy": a.copy}
                                      for a in analisis.angulos_venta],
                    "marca": {"nombre": analisis.marca.nombre, "razon": analisis.marca.razon,
                              "copy_anuncio": analisis.marca.copy_anuncio,
                              "valor_agregado": analisis.marca.valor_agregado,
                              "empaque": analisis.marca.empaque},
                    "riesgos": analisis.riesgos,
                    "tokens_entrada": analisis.tokens_entrada,
                    "tokens_salida": analisis.tokens_salida,
                }

                for s in hist:
                    db.eliminar(s["id"])
                db.guardar(pnombre, "analisis", datos_g)
                status.update(label="¡Análisis completo!", state="complete", expanded=False)
                st.session_state["analisis_cache"] = datos_g
                st.rerun()

            except Exception as e:
                status.update(label=f"Error: {e}", state="error")
                st.error(str(e))
        return

    datos = st.session_state.get("analisis_cache") or datos_prev
    if not datos:
        st.markdown("""
        <div class="fx-empty">
          <span class="fx-empty-icon">🔍</span>
          <div class="fx-empty-text">Pulsa ⚡ Analizar para evaluar el producto</div>
          <div class="fx-empty-sub">MercadoLibre · Google Trends · Meta Ads · 9 criterios · Buyer Persona</div>
        </div>
        """, unsafe_allow_html=True)
        return

    _mostrar_analisis(datos)


def _mostrar_analisis(datos: dict):
    from trendia.analyzer.criterios import ESTADO_OK, ESTADO_WARN

    veredicto = datos["veredicto"]
    v_cls = ("fx-veredicto-lanzar" if "LANZAR" in veredicto and "PRECAUCIÓN" not in veredicto
             else "fx-veredicto-precaucion" if "PRECAUCIÓN" in veredicto
             else "fx-veredicto-no")
    v_ico = "🚀" if "LANZAR" in veredicto and "PRECAUCIÓN" not in veredicto else ("⚡" if "PRECAUCIÓN" in veredicto else "🚫")
    score_color = (styles.COLORS["green"] if datos["score_total"] >= 13
                   else styles.COLORS["yellow"] if datos["score_total"] >= 8
                   else styles.COLORS["red"])

    # ── Score + veredicto ─────────────────────────────────────────────────────
    col_score, col_v = st.columns([1, 2], gap="large")
    with col_score:
        barra = ("".join(['<div style="flex:1;height:6px;background:#10b981;border-radius:3px"></div>'] * datos["aprobados"])
               + "".join(['<div style="flex:1;height:6px;background:#f59e0b;border-radius:3px"></div>'] * datos["en_riesgo"])
               + "".join(['<div style="flex:1;height:6px;background:#ef4444;border-radius:3px"></div>'] * datos["reprobados"]))
        st.markdown(f"""
        <div class="fx-stat">
          <div class="fx-stat-num" style="color:{score_color}">
            {datos['score_total']}<span style="font-size:1.5rem;color:#2a2a42">/18</span>
          </div>
          <div class="fx-stat-lbl">{datos['score_pct']:.0f}% viabilidad</div>
          <div style="display:flex;gap:3px;margin-top:1.2rem">{barra}</div>
          <div style="margin-top:0.5rem;font-size:0.75rem;color:#2a2a42;display:flex;gap:1rem;justify-content:center">
            <span style="color:#10b981">✓ {datos['aprobados']}</span>
            <span style="color:#f59e0b">⚡ {datos['en_riesgo']}</span>
            <span style="color:#ef4444">✗ {datos['reprobados']}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_v:
        st.markdown(f"""
        <div class="fx-veredicto {v_cls}" style="height:100%;min-height:160px">
          <div style="font-size:2.5rem">{v_ico}</div>
          <div class="fx-veredicto-titulo" style="margin-top:0.5rem">{veredicto}</div>
          <div class="fx-veredicto-kw">{datos['keyword']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='fx-divider'></div>", unsafe_allow_html=True)

    # ── 9 Criterios ───────────────────────────────────────────────────────────
    st.markdown('<span class="fx-section-label">9 criterios</span>', unsafe_allow_html=True)
    ca, cb = st.columns(2, gap="medium")
    mitad = (len(datos["criterios"]) + 1) // 2
    for col, grupo in [(ca, datos["criterios"][:mitad]), (cb, datos["criterios"][mitad:])]:
        with col:
            for c in grupo:
                cls = ("fx-criterio-ok" if c["estado"] == "✅"
                       else "fx-criterio-warn" if c["estado"] == "⚠️"
                       else "fx-criterio-fail")
                pts_c = ("#10b981" if c["puntos"] == 2 else
                         "#f59e0b" if c["puntos"] == 1 else "#ef4444")
                nota = c["nota"].replace("<", "&lt;").replace(">", "&gt;")
                st.markdown(f"""
                <div class="fx-criterio {cls}">
                  <div class="fx-criterio-titulo">
                    {c['estado']} C{c['numero']}. {c['nombre']}
                    <span style="float:right;color:{pts_c}">{c['puntos']}/2</span>
                  </div>
                  <div class="fx-criterio-nota">{nota}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<div class='fx-divider'></div>", unsafe_allow_html=True)

    # ── Ángulos + Riesgos ─────────────────────────────────────────────────────
    col_ang, col_risk = st.columns(2, gap="large")

    with col_ang:
        st.markdown('<span class="fx-section-label">Ángulos de venta</span>', unsafe_allow_html=True)
        for ang in datos.get("angulos_venta", []):
            st.markdown(f"""
            <div class="fx-card-flat" style="margin-bottom:0.6rem">
              <div style="font-size:0.7rem;font-weight:700;color:#3a3a5a;
                          text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem">
                {ang['nombre']}
              </div>
              <div style="font-size:0.95rem;font-weight:700;color:#e0e0f0;margin-bottom:0.4rem">
                "{ang['hook']}"
              </div>
              <div style="font-size:0.82rem;color:#4a4a6a;line-height:1.6">{ang['copy']}</div>
            </div>
            """, unsafe_allow_html=True)

    with col_risk:
        st.markdown('<span class="fx-section-label">Riesgos antes de lanzar</span>', unsafe_allow_html=True)
        for r in datos.get("riesgos", []):
            r_esc = r.replace("<", "&lt;").replace(">", "&gt;")
            st.markdown(f'<div class="fx-riesgo">⚠ {r_esc}</div>', unsafe_allow_html=True)

    st.markdown("<div class='fx-divider'></div>", unsafe_allow_html=True)

    # ── Marca sugerida ────────────────────────────────────────────────────────
    m = datos.get("marca", {})
    if m:
        st.markdown('<span class="fx-section-label">Marca sugerida</span>', unsafe_allow_html=True)
        cm1, cm2 = st.columns([1, 2], gap="large")
        with cm1:
            st.markdown(f"""
            <div class="fx-card-flat">
              <div style="font-size:2rem;font-weight:900;color:#a78bfa;letter-spacing:-0.04em">
                {m.get('nombre','')}
              </div>
              <div class="fx-info-row"><span class="fx-info-label">Razón</span>
                <span class="fx-info-value" style="font-size:0.82rem;text-align:right;max-width:60%">
                  {m.get('razon','')}
                </span>
              </div>
              <div class="fx-info-row"><span class="fx-info-label">Valor agregado</span>
                <span class="fx-info-value" style="font-size:0.82rem;text-align:right;max-width:60%">
                  {m.get('valor_agregado','')}
                </span>
              </div>
              <div class="fx-info-row"><span class="fx-info-label">Empaque</span>
                <span class="fx-info-value" style="font-size:0.82rem;text-align:right;max-width:60%">
                  {m.get('empaque','')}
                </span>
              </div>
            </div>
            """, unsafe_allow_html=True)
        with cm2:
            st.markdown("**Copy de anuncio principal**")
            st.text_area("copy_marca", value=m.get("copy_anuncio", ""),
                         height=140, label_visibility="collapsed")

    tok = datos.get("tokens_entrada", 0)
    if tok:
        st.markdown(
            f"<div style='font-size:0.72rem;color:#1e1e30;margin-top:1rem'>"
            f"Tokens: {tok:,}↑ {datos.get('tokens_salida',0):,}↓</div>",
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: COPY & ÁNGULOS
# ══════════════════════════════════════════════════════════════════════════════

def _pagina_copy():
    from fluxa.creatives import generar_creatives, generar_creatives_demo

    _page_header("🎯", "Copy & Ángulos",
                 "5 ángulos de venta · Título · Texto · Copy Meta Ads · Storyboard 20s")

    pid, pnombre = _selector_producto("copy")
    if not pid:
        return

    hist = [s for s in db.listar(limite=300)
            if s["producto"] == pnombre and s["modulo"] == "creatives"]
    datos_prev = hist[0]["datos"] if hist else None

    c1, c2 = st.columns([3, 1], gap="small")
    with c1:
        demo = st.checkbox("Modo demo (sin API)", value=False)
    with c2:
        gen_btn = st.button("⚡ Generar", type="primary")

    if gen_btn:
        with st.status(f"Generando copy para **{pnombre}**…", expanded=True) as status:
            st.write("🎯 Creando 5 ángulos de venta…")
            try:
                res = generar_creatives_demo(pnombre) if demo else generar_creatives(pnombre)
                datos_g = {
                    "producto": res.producto,
                    "marcas": [{"nombre": m.nombre, "razon": m.razon, "slogan": m.slogan}
                               for m in res.marcas],
                    "problemas": res.problemas,
                    "beneficios": res.beneficios,
                    "angulos": [{
                        "tipo": a.tipo, "titulo": a.titulo,
                        "texto_principal": a.texto_principal,
                        "descripcion": a.descripcion, "copy_meta": a.copy_meta,
                        "storyboard": {
                            "duracion_total": a.storyboard.duracion_total,
                            "escenas": [{"tiempo": e.tiempo, "etiqueta": e.etiqueta,
                                         "descripcion": e.descripcion, "locucion": e.locucion}
                                        for e in a.storyboard.escenas]
                        } if a.storyboard else None,
                    } for a in res.angulos],
                    "tokens_entrada": res.tokens_entrada,
                    "tokens_salida": res.tokens_salida,
                }
                for s in hist:
                    db.eliminar(s["id"])
                db.guardar(pnombre, "creatives", datos_g)
                status.update(label="¡Listo!", state="complete", expanded=False)
                st.session_state["copy_cache"] = datos_g
                st.rerun()
            except Exception as e:
                status.update(label=f"Error: {e}", state="error")
                st.error(str(e))
        return

    datos = st.session_state.get("copy_cache") or datos_prev
    if not datos:
        st.markdown("""
        <div class="fx-empty">
          <span class="fx-empty-icon">🎯</span>
          <div class="fx-empty-text">Pulsa ⚡ Generar para crear los 5 ángulos</div>
          <div class="fx-empty-sub">Marca · Problemas · Beneficios · Copy Meta · Storyboard</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Marcas
    st.markdown('<span class="fx-section-label">Opciones de marca</span>', unsafe_allow_html=True)
    cm = st.columns(3, gap="medium")
    for col, m in zip(cm, datos.get("marcas", [])):
        with col:
            st.markdown(f"""
            <div class="fx-card" style="text-align:center">
              <div style="font-size:1.4rem;font-weight:900;color:#a78bfa;letter-spacing:-0.03em">
                {m['nombre']}
              </div>
              <div style="font-size:0.82rem;color:#3a3a5a;font-style:italic;margin:0.5rem 0">
                "{m['slogan']}"
              </div>
              <div style="font-size:0.75rem;color:#2a2a42">{m['razon']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div class='fx-divider'></div>", unsafe_allow_html=True)

    # Problemas + Beneficios
    cp, cb = st.columns(2, gap="large")
    with cp:
        st.markdown('<span class="fx-section-label">Problemas que resuelve</span>', unsafe_allow_html=True)
        for p in datos.get("problemas", []):
            st.markdown(f'<div class="fx-riesgo">⚠ {p}</div>', unsafe_allow_html=True)
    with cb:
        st.markdown('<span class="fx-section-label">Beneficios clave</span>', unsafe_allow_html=True)
        for b in datos.get("beneficios", []):
            st.markdown(f'<div class="fx-beneficio">✓ {b}</div>', unsafe_allow_html=True)

    st.markdown("<div class='fx-divider'></div>", unsafe_allow_html=True)

    # 5 Ángulos
    st.markdown('<span class="fx-section-label">5 ángulos de venta</span>', unsafe_allow_html=True)
    for ang in datos.get("angulos", []):
        tipo   = ang["tipo"]
        b_cls, b_ico = styles.ANGULO_BADGE.get(tipo, ("fx-badge-purple", "🎯"))
        border = styles.ANGULO_BORDER.get(tipo, "#a78bfa")

        with st.expander(f"{b_ico} {tipo} — {ang['titulo']}", expanded=False):
            cl, cr = st.columns(2, gap="large")
            with cl:
                st.markdown(f"""
                <div class="fx-card" style="border-left:3px solid {border}">
                  <span class="fx-badge {b_cls}">{tipo}</span>
                  <div style="font-size:1.05rem;font-weight:700;color:#e8e8f8;
                              letter-spacing:-0.02em;margin-bottom:0.5rem">{ang['titulo']}</div>
                  <div style="font-size:0.8rem;color:#3a3a5a;font-style:italic;
                              margin-bottom:0.8rem">{ang['descripcion']}</div>
                  <div style="font-size:0.88rem;color:#c0c0d8;line-height:1.7">
                    {ang['texto_principal']}</div>
                </div>
                """, unsafe_allow_html=True)

            with cr:
                st.markdown(f"<div style='font-size:0.75rem;font-weight:700;color:#2a2a42;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.4rem'>Copy Meta Ads</div>", unsafe_allow_html=True)
                st.text_area("m", value=ang["copy_meta"], height=160,
                             key=f"_meta_{tipo}", label_visibility="collapsed")

                sb = ang.get("storyboard")
                if sb:
                    st.markdown(f"<div style='font-size:0.75rem;font-weight:700;color:#2a2a42;text-transform:uppercase;letter-spacing:0.1em;margin:0.8rem 0 0.4rem'>Storyboard {sb['duracion_total']}</div>", unsafe_allow_html=True)
                    for esc in sb["escenas"]:
                        st.markdown(f"""
                        <div class="fx-scene">
                          <div class="fx-scene-header">
                            <span class="fx-scene-time">{esc['tiempo']}</span>
                            <span class="fx-scene-label">{esc['etiqueta']}</span>
                          </div>
                          <div class="fx-scene-key">👁 Visual</div>
                          <div class="fx-scene-val">{esc['descripcion']}</div>
                          <div class="fx-scene-key">🎙 Locución</div>
                          <div class="fx-scene-val-em">"{esc['locucion']}"</div>
                        </div>
                        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: STORYBOARDS (próximamente full)
# ══════════════════════════════════════════════════════════════════════════════

def _pagina_storyboards():
    _page_header("🎬", "Storyboards",
                 "8 fases · 10 ángulos · Cuadros visuales · Prompt imagen · Prompt Veo/Kling · Copy A/B/C")

    pid, pnombre = _selector_producto("storyboards")
    if not pid:
        return

    st.markdown("""
    <div class="fx-card" style="text-align:center;padding:3rem">
      <div style="font-size:2rem;margin-bottom:1rem">🎬</div>
      <div style="font-size:1.1rem;font-weight:700;color:#e0e0f0;letter-spacing:-0.02em">
        Storyboards completos — en construcción
      </div>
      <div style="font-size:0.85rem;color:#3a3a5a;margin-top:0.5rem">
        8 fases · 10 ángulos ordenados por conversión · Cuadros con personajes y planos<br>
        Prompt imagen hiperrealista · Prompt Veo/Gemini Omni/Kling · 3 copies A/B/C Meta
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: LANDING SECTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _pagina_landing():
    _page_header("📄", "Landing Sections",
                 "Hero · Beneficios · Características · Comparativa · Envíos — 1080×1600px · gpt-image-2")

    pid, pnombre = _selector_producto("landing")
    if not pid:
        return

    st.markdown("""
    <div class="fx-card" style="text-align:center;padding:3rem">
      <div style="font-size:2rem;margin-bottom:1rem">📄</div>
      <div style="font-size:1.1rem;font-weight:700;color:#e0e0f0;letter-spacing:-0.02em">
        Landing Sections — en construcción
      </div>
      <div style="font-size:0.85rem;color:#3a3a5a;margin-top:0.5rem">
        Hero · Beneficios · Características · Comparativa · Envíos<br>
        Imágenes 1080×1600px · gpt-image-2 · Producto nunca se altera
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: UPSELLS
# ══════════════════════════════════════════════════════════════════════════════

def _pagina_upsells():
    _page_header("🖼️", "Upsells",
                 "Foto producto → ×1 ×2 ×3 fondo blanco HD · gpt-image-2 · Releasit COD")

    pid, pnombre = _selector_producto("upsells")
    if not pid:
        return

    st.markdown("""
    <div class="fx-card" style="text-align:center;padding:3rem">
      <div style="font-size:2rem;margin-bottom:1rem">🖼️</div>
      <div style="font-size:1.1rem;font-weight:700;color:#e0e0f0;letter-spacing:-0.02em">
        Upsells — en construcción
      </div>
      <div style="font-size:0.85rem;color:#3a3a5a;margin-top:0.5rem">
        Sube la foto del producto → genera combo ×1, ×2, ×3<br>
        Fondo blanco HD · Sin alterar el producto · Releasit listo
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: RESEÑAS VISUALES
# ══════════════════════════════════════════════════════════════════════════════

def _pagina_resenas():
    _page_header("🌟", "Reseñas Visuales",
                 "Prompts UGC hiperrealistas · Cliente colombiano · 5+ escenas por producto")

    pid, pnombre = _selector_producto("resenas")
    if not pid:
        return

    st.markdown("""
    <div class="fx-card" style="text-align:center;padding:3rem">
      <div style="font-size:2rem;margin-bottom:1rem">🌟</div>
      <div style="font-size:1.1rem;font-weight:700;color:#e0e0f0;letter-spacing:-0.02em">
        Reseñas Visuales — en construcción
      </div>
      <div style="font-size:0.85rem;color:#3a3a5a;margin-top:0.5rem">
        5+ prompts UGC · Foto llegó · En mano · En uso · WhatsApp · Unboxing<br>
        Estilo cliente colombiano real · Ambiente cotidiano · Sin apariencia de IA
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: LANZAR
# ══════════════════════════════════════════════════════════════════════════════

def _pagina_lanzar():
    _page_header("🚀", "Lanzar", "Landing → Shopify · Videos → Gemini Omni / Kling")

    pid, pnombre = _selector_producto("lanzar")
    if not pid:
        return

    st.markdown("""
    <div class="fx-card" style="text-align:center;padding:3rem">
      <div style="font-size:2rem;margin-bottom:1rem">🚀</div>
      <div style="font-size:1.1rem;font-weight:700;color:#e0e0f0">Lanzar — próximamente</div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: MÁRGENES COD
# ══════════════════════════════════════════════════════════════════════════════

def _pagina_margenes():
    _page_header("💰", "Márgenes COD",
                 "Margen real proyectado considerando courier, rechazo y publicidad")

    c_izq, c_der = st.columns(2, gap="large")

    with c_izq:
        st.markdown('<span class="fx-section-label">Producto</span>', unsafe_allow_html=True)
        precio_venta   = st.number_input("Precio de venta (COP)", value=89_900, step=1_000, format="%d")
        costo_producto = st.number_input("Costo producto + aduana (COP)", value=20_000, step=500, format="%d")
        costo_empaque  = st.number_input("Empaque + embalaje (COP)", value=3_000, step=500, format="%d")

        st.markdown('<span class="fx-section-label" style="margin-top:1.2rem;display:block">Logística COD</span>', unsafe_allow_html=True)
        costo_courier  = st.number_input("Tarifa courier por envío (COP)", value=8_500, step=500, format="%d")
        tasa_rechazo   = st.slider("Tasa de rechazo COD (%)", 0, 50, 20)
        costo_dev      = st.number_input("Costo devolución por rechazo (COP)", value=5_000, step=500, format="%d")

        st.markdown('<span class="fx-section-label" style="margin-top:1.2rem;display:block">Publicidad</span>', unsafe_allow_html=True)
        cpa_meta       = st.number_input("CPA estimado Meta Ads (COP)", value=15_000, step=1_000, format="%d")

    with c_der:
        st.markdown('<span class="fx-section-label">Proyección por 100 pedidos</span>', unsafe_allow_html=True)

        pedidos            = 100
        entregados         = pedidos * (1 - tasa_rechazo / 100)
        rechazados         = pedidos * (tasa_rechazo / 100)
        ingresos           = entregados * precio_venta
        costo_prod_total   = pedidos * (costo_producto + costo_empaque)
        costo_cour_total   = pedidos * costo_courier
        costo_dev_total    = rechazados * costo_dev
        costo_pub_total    = pedidos * cpa_meta
        costos_totales     = costo_prod_total + costo_cour_total + costo_dev_total + costo_pub_total
        utilidad           = ingresos - costos_totales
        margen_pct         = (utilidad / ingresos * 100) if ingresos > 0 else 0
        roi                = (utilidad / costo_pub_total * 100) if costo_pub_total > 0 else 0

        c_m = (styles.COLORS["green"] if margen_pct >= 25
               else styles.COLORS["yellow"] if margen_pct >= 10
               else styles.COLORS["red"])
        veredicto = ("Buen margen" if margen_pct >= 25
                     else "Margen ajustado" if margen_pct >= 10
                     else "No rentable")

        st.markdown(f"""
        <div class="fx-stat" style="margin-bottom:1.5rem">
          <div class="fx-stat-num" style="color:{c_m}">{margen_pct:.1f}%</div>
          <div class="fx-stat-lbl">margen neto · {veredicto}</div>
        </div>
        """, unsafe_allow_html=True)

        def _row(label, val, tipo="normal"):
            color = (styles.COLORS["green"] if tipo == "pos"
                     else styles.COLORS["red"] if tipo == "neg"
                     else "#f0f0f8" if tipo == "total"
                     else "#c0c0d8")
            prefix = "−" if tipo == "neg" else ""
            weight = "800" if tipo == "total" else "600"
            st.markdown(f"""
            <div class="fx-margen-row">
              <span class="fx-margen-label">{label}</span>
              <span style="color:{color};font-weight:{weight}">{prefix}${abs(val):,.0f}</span>
            </div>""", unsafe_allow_html=True)

        _row("Ingresos (entregas)", ingresos, "pos")
        _row("Costo producto + empaque", costo_prod_total, "neg")
        _row("Courier (todos los pedidos)", costo_cour_total, "neg")
        _row(f"Devoluciones ({rechazados:.0f} rechazos)", costo_dev_total, "neg")
        _row("Inversión Meta Ads", costo_pub_total, "neg")
        _row("Utilidad neta", utilidad, "total")

        st.markdown(f"""
        <div style="font-size:0.75rem;color:#2a2a42;margin-top:0.8rem;text-align:right">
          ROI sobre ads: <strong style="color:{c_m}">{roi:.0f}%</strong> &nbsp;·&nbsp;
          {rechazados:.0f} rechazos de {pedidos} pedidos
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════

_ROUTER = {
    "productos":   _pagina_productos,
    "validacion":  _pagina_validacion,
    "copy":        _pagina_copy,
    "storyboards": _pagina_storyboards,
    "landing":     _pagina_landing,
    "upsells":     _pagina_upsells,
    "resenas":     _pagina_resenas,
    "lanzar":      _pagina_lanzar,
    "margenes":    _pagina_margenes,
}

_ROUTER.get(st.session_state.pagina, _pagina_productos)()
