"""Trendia — Analizador de Producto COD Colombia.

Lanzar:
    streamlit run app.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).parent
os.chdir(_ROOT)
sys.path.insert(0, str(_ROOT))

import streamlit as st

# ── Config de página ──────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Trendia — Analizador de Producto",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
  /* Fondo y tipografía base */
  .stApp { background: #0f1117; }
  h1, h2, h3 { color: #f0f0f0 !important; }

  /* Input principal */
  .stTextInput > div > div > input {
    font-size: 1.1rem;
    padding: 0.7rem 1rem;
    border-radius: 10px;
    border: 2px solid #2d2d3a !important;
    background: #1a1b26 !important;
    color: #e0e0e0 !important;
  }
  .stTextInput > div > div > input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.3) !important;
  }

  /* Botón analizar */
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border: none;
    border-radius: 10px;
    font-size: 1rem;
    font-weight: 700;
    padding: 0.6rem 2rem;
    color: white;
    width: 100%;
    transition: opacity 0.2s;
  }
  .stButton > button[kind="primary"]:hover { opacity: 0.85; }

  /* Tarjetas de criterios */
  .criterio-card {
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    border-left: 4px solid transparent;
  }
  .criterio-ok   { background: #0d2818; border-left-color: #22c55e; }
  .criterio-warn { background: #2a1f06; border-left-color: #f59e0b; }
  .criterio-fail { background: #2a0d0d; border-left-color: #ef4444; }
  .criterio-titulo { font-weight: 700; font-size: 0.95rem; color: #e0e0e0; }
  .criterio-nota   { font-size: 0.82rem; color: #a0a0b0; margin-top: 0.3rem; }

  /* Score grande */
  .score-box {
    background: #1a1b26;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    text-align: center;
    border: 1px solid #2d2d3a;
  }
  .score-num  { font-size: 3.5rem; font-weight: 900; color: #6366f1; line-height: 1; }
  .score-sub  { font-size: 0.9rem; color: #888; margin-top: 0.3rem; }

  /* Veredicto */
  .veredicto-lanzar     { background: #0d2818; border: 2px solid #22c55e; border-radius: 16px; padding: 1.5rem 2rem; text-align: center; }
  .veredicto-precaucion { background: #2a1f06; border: 2px solid #f59e0b; border-radius: 16px; padding: 1.5rem 2rem; text-align: center; }
  .veredicto-no         { background: #2a0d0d; border: 2px solid #ef4444; border-radius: 16px; padding: 1.5rem 2rem; text-align: center; }
  .veredicto-texto      { font-size: 1.6rem; font-weight: 900; color: #f0f0f0; }
  .veredicto-icono      { font-size: 3rem; }

  /* Ángulos de venta */
  .angulo-box {
    background: #1a1b26;
    border-radius: 12px;
    padding: 1.2rem;
    border: 1px solid #2d2d3a;
    height: 100%;
  }
  .angulo-titulo { font-size: 0.75rem; font-weight: 700; letter-spacing: 0.1em;
                   color: #8b5cf6; text-transform: uppercase; margin-bottom: 0.5rem; }
  .angulo-hook   { font-size: 1rem; font-weight: 700; color: #e0e0e0; margin-bottom: 0.6rem; }
  .angulo-copy   { font-size: 0.85rem; color: #b0b0c0; line-height: 1.6; }

  /* Marca */
  .marca-box {
    background: #13131f;
    border-radius: 12px;
    padding: 1.4rem;
    border: 1px solid #2d2d3a;
  }
  .marca-nombre { font-size: 2rem; font-weight: 900; color: #6366f1; }
  .marca-label  { font-size: 0.72rem; letter-spacing: 0.08em; color: #666; text-transform: uppercase; margin-top: 1rem; margin-bottom: 0.2rem; }
  .marca-val    { font-size: 0.9rem; color: #c0c0d0; }

  /* Riesgos */
  .riesgo-item {
    background: #1f1208;
    border-left: 3px solid #f59e0b;
    border-radius: 6px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.88rem;
    color: #d0b080;
  }

  /* Barra de progreso de criterios */
  .barra-wrap { display: flex; gap: 4px; margin-top: 0.5rem; }
  .barra-ok   { flex: 1; height: 8px; background: #22c55e; border-radius: 4px; }
  .barra-warn { flex: 1; height: 8px; background: #f59e0b; border-radius: 4px; }
  .barra-fail { flex: 1; height: 8px; background: #ef4444; border-radius: 4px; }

  /* Sección header */
  .seccion-header {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #666;
    border-bottom: 1px solid #2d2d3a;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
  }

  /* Textarea de copy */
  .stTextArea textarea {
    background: #1a1b26 !important;
    color: #c0c0d0 !important;
    border-color: #2d2d3a !important;
    font-size: 0.85rem;
  }

  /* Ocultar footer de Streamlit */
  footer { display: none; }
  #MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Helpers de datos ──────────────────────────────────────────────────────────

def _dry_run_datos(keyword: str) -> tuple[dict, dict, dict, dict]:
    return (
        {"total_productos": 1_500, "num_marcas": 22, "dominios": ["MCO-BODY_SHAPERS"]},
        {"interes_promedio": 55.0, "interes_peak": 100, "tendencia": 0.8},
        {"num_anuncios": 12},
        {"num_publicaciones": 18},
    )


def _triangular_real(keyword: str) -> tuple[dict, dict, dict, dict]:
    from trendia.triangulator.mercadolibre import buscar
    from trendia.triangulator.trends import interes_colombia
    from trendia.triangulator.meta_ads import _scrape_async as _meta_async
    from trendia.triangulator.fb_marketplace import _scrape_async as _mkt_async

    ml_r = buscar(keyword)
    tr_r = interes_colombia(keyword)

    async def _par():
        return await asyncio.gather(_meta_async(keyword), _mkt_async(keyword))

    meta_r, mkt_r = asyncio.run(_par())

    return (
        {"total_productos": ml_r.total_productos, "num_marcas": ml_r.num_marcas, "dominios": ml_r.dominios},
        {"interes_promedio": tr_r.interes_promedio, "interes_peak": tr_r.interes_peak, "tendencia": tr_r.tendencia},
        {"num_anuncios": meta_r.num_anuncios},
        {"num_publicaciones": mkt_r.num_publicaciones},
    )


# ── Renderizado de resultados ─────────────────────────────────────────────────

_ESTADO_CLASE = {
    "✅": "criterio-ok",
    "⚠️": "criterio-warn",
    "❌": "criterio-fail",
}

_VEREDICTO_CLASE = {
    "LANZAR": "veredicto-lanzar",
    "LANZAR CON PRECAUCIÓN": "veredicto-precaucion",
    "NO LANZAR": "veredicto-no",
}

_VEREDICTO_ICONO = {
    "LANZAR": "🚀",
    "LANZAR CON PRECAUCIÓN": "⚡",
    "NO LANZAR": "🚫",
}


def _mostrar_resultados(a) -> None:
    from trendia.analyzer.criterios import ESTADO_OK, ESTADO_WARN, ESTADO_FAIL

    # ── Fila superior: score + veredicto ─────────────────────────────────────
    col_score, col_veredicto = st.columns([1, 2], gap="large")

    with col_score:
        barra_html = "".join(
            f'<div class="barra-ok"></div>' * a.aprobados
            + f'<div class="barra-warn"></div>' * a.en_riesgo
            + f'<div class="barra-fail"></div>' * a.reprobados
        )
        st.markdown(f"""
        <div class="score-box">
          <div class="score-num">{a.score_total}<span style="font-size:1.5rem;color:#555">/18</span></div>
          <div class="score-sub">{a.score_pct:.0f}% de viabilidad</div>
          <div class="barra-wrap" style="margin-top:1rem">{barra_html}</div>
          <div style="margin-top:0.5rem;font-size:0.8rem;color:#666">
            ✅ {a.aprobados} &nbsp; ⚠️ {a.en_riesgo} &nbsp; ❌ {a.reprobados}
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_veredicto:
        clase = _VEREDICTO_CLASE.get(a.veredicto, "veredicto-no")
        icono = _VEREDICTO_ICONO.get(a.veredicto, "❓")
        st.markdown(f"""
        <div class="{clase}" style="height:100%;display:flex;flex-direction:column;justify-content:center">
          <div class="veredicto-icono">{icono}</div>
          <div class="veredicto-texto">{a.veredicto}</div>
          <div style="font-size:0.85rem;color:#999;margin-top:0.5rem">{a.keyword}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 9 Criterios ───────────────────────────────────────────────────────────
    st.markdown('<div class="seccion-header">Evaluación de criterios</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2, gap="medium")
    mitad = (len(a.criterios) + 1) // 2

    for col, criterios_grupo in [(col_a, a.criterios[:mitad]), (col_b, a.criterios[mitad:])]:
        with col:
            for c in criterios_grupo:
                clase = _ESTADO_CLASE.get(c.estado, "criterio-fail")
                pts_color = "#22c55e" if c.puntos == 2 else ("#f59e0b" if c.puntos == 1 else "#ef4444")
                nota_esc = c.nota.replace("<", "&lt;").replace(">", "&gt;")
                st.markdown(f"""
                <div class="criterio-card {clase}">
                  <div class="criterio-titulo">
                    {c.estado} &nbsp; C{c.numero}. {c.nombre}
                    <span style="float:right;color:{pts_color};font-size:0.85rem">{c.puntos}/2</span>
                  </div>
                  <div class="criterio-nota">{nota_esc}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 3 Ángulos de venta ────────────────────────────────────────────────────
    st.markdown('<div class="seccion-header">3 ángulos de venta</div>', unsafe_allow_html=True)

    cols_angulos = st.columns(3, gap="medium")
    for col, ang in zip(cols_angulos, a.angulos_venta):
        with col:
            st.markdown(f"""
            <div class="angulo-box">
              <div class="angulo-titulo">{ang.nombre}</div>
              <div class="angulo-hook">"{ang.hook}"</div>
              <div class="angulo-copy">{ang.copy}</div>
            </div>
            """, unsafe_allow_html=True)
            st.text_area(
                "Copiar",
                value=f"{ang.hook}\n\n{ang.copy}",
                height=120,
                key=f"angulo_{ang.nombre}",
                label_visibility="collapsed",
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Marca sugerida ────────────────────────────────────────────────────────
    st.markdown('<div class="seccion-header">Marca sugerida</div>', unsafe_allow_html=True)

    col_marca, col_copy_marca = st.columns([1, 2], gap="large")

    with col_marca:
        st.markdown(f"""
        <div class="marca-box">
          <div class="marca-nombre">{a.marca.nombre}</div>
          <div class="marca-label">Por qué funciona</div>
          <div class="marca-val">{a.marca.razon}</div>
          <div class="marca-label">Valor agregado</div>
          <div class="marca-val">{a.marca.valor_agregado}</div>
          <div class="marca-label">Empaque</div>
          <div class="marca-val">{a.marca.empaque}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_copy_marca:
        st.markdown("**Copy de anuncio principal**")
        st.text_area(
            "Copy",
            value=a.marca.copy_anuncio,
            height=140,
            key="copy_marca",
            label_visibility="collapsed",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Riesgos ───────────────────────────────────────────────────────────────
    st.markdown('<div class="seccion-header">Riesgos antes de lanzar</div>', unsafe_allow_html=True)

    for r in a.riesgos:
        r_esc = r.replace("<", "&lt;").replace(">", "&gt;")
        st.markdown(f'<div class="riesgo-item">⚠ &nbsp; {r_esc}</div>', unsafe_allow_html=True)

    if a.tokens_entrada:
        st.markdown(f"<br><small style='color:#444'>Tokens: {a.tokens_entrada}↑ {a.tokens_salida}↓</small>", unsafe_allow_html=True)


# ── UI principal ──────────────────────────────────────────────────────────────

st.markdown("""
<div style="padding:2rem 0 1rem">
  <h1 style="font-size:2rem;margin:0;color:#f0f0f0">🔍 Trendia</h1>
  <p style="color:#666;margin:0.2rem 0 0">Analizador de producto · Dropshipping COD Colombia · 9 criterios</p>
</div>
""", unsafe_allow_html=True)

# ── Formulario ────────────────────────────────────────────────────────────────

col_input, col_btn = st.columns([4, 1], gap="small")

with col_input:
    keyword = st.text_input(
        "Producto",
        placeholder="faja colombiana, cepillo masajeador, rodillo facial...",
        label_visibility="collapsed",
    )

with col_btn:
    analizar_btn = st.button("🔍 Analizar", type="primary", disabled=not keyword.strip())

col_opt1, col_opt2, col_opt3 = st.columns(3)
with col_opt1:
    usar_web = st.checkbox("Búsqueda web real (TikTok · Alibaba · Amazon)", value=True)
with col_opt2:
    usar_triangulador = st.checkbox("Triangulador completo (ML · Trends · Meta · Marketplace)", value=True)
with col_opt3:
    dry_run = st.checkbox("Modo demo (sin APIs)", value=False)

# ── Datos manuales de Facebook (el scraper falla por bot detection) ────────────
with st.expander("📱 Datos de Facebook — ingrésalos tú (Ads Library actualizada 2026)"):
    st.markdown(
        "<small style='color:#888'>La nueva Ads Library muestra impresiones y tiempo de gasto por anunciante. "
        "Abre el link, busca tu producto y llena los campos.</small>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<a href='https://www.facebook.com/ads/library/?country=CO&active_status=active&ad_type=all' "
        "target='_blank' style='font-size:.82rem;color:#6366f1;font-weight:700'>→ Abrir Meta Ads Library Colombia</a>"
        "&nbsp;&nbsp;"
        "<a href='https://www.facebook.com/marketplace/bogota/search/' "
        "target='_blank' style='font-size:.82rem;color:#6366f1;font-weight:700'>→ Abrir Marketplace Bogotá</a>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown("**Meta Ads Library**")
        meta_manual = st.number_input(
            "¿Cuántos anuncios activos ves?",
            min_value=0, value=0, step=1,
            help="Cuenta los anuncios que aparecen al buscar tu producto en Colombia",
        )
        meta_impresiones = st.selectbox(
            "Impresiones del anuncio más activo",
            options=[
                "No sé / no aparece",
                "Menos de 1.000",
                "1.000 – 10.000",
                "10.000 – 50.000",
                "50.000 – 100.000",
                "100.000 – 500.000",
                "Más de 500.000",
            ],
            help="Haz clic en el anuncio con más tiempo corriendo → abajo dice el rango de impresiones",
        )
        meta_meses = st.selectbox(
            "¿Cuánto lleva corriendo el anuncio más antiguo?",
            options=[
                "No sé",
                "Menos de 1 mes",
                "1 – 3 meses",
                "3 – 6 meses",
                "6 – 12 meses",
                "Más de 12 meses",
            ],
            help="La fecha de inicio aparece en cada anuncio de la biblioteca",
        )

    with col_m2:
        st.markdown("**Facebook Marketplace**")
        mkt_manual = st.number_input(
            "¿Cuántas publicaciones ves?",
            min_value=0, value=0, step=1,
            help="Busca tu producto en Marketplace → cuenta las publicaciones activas",
        )
        st.markdown(
            "<small style='color:#666'>El Marketplace de Bogotá es el más activo de Colombia "
            "— sirve como referencia del volumen nacional.</small>",
            unsafe_allow_html=True,
        )

st.markdown("---")

# ── Análisis ──────────────────────────────────────────────────────────────────

if analizar_btn and keyword.strip():
    kw = keyword.strip()

    with st.status(f"Analizando **{kw}**…", expanded=True) as status:

        # Paso 1: triangulación
        if usar_triangulador and not dry_run:
            st.write("📊 Consultando MercadoLibre Colombia…")
            from trendia.triangulator.mercadolibre import buscar
            ml_r = buscar(kw)
            ml_data = {"total_productos": ml_r.total_productos, "num_marcas": ml_r.num_marcas, "dominios": ml_r.dominios}
            st.write(f"   ✓ {ml_r.total_productos:,} productos · {ml_r.num_marcas} marcas")

            st.write("📈 Consultando Google Trends Colombia…")
            from trendia.triangulator.trends import interes_colombia
            tr_r = interes_colombia(kw)
            tr_data = {"interes_promedio": tr_r.interes_promedio, "interes_peak": tr_r.interes_peak, "tendencia": tr_r.tendencia}
            dir_t = "↑" if tr_r.tendencia > 0.5 else ("↓" if tr_r.tendencia < -0.5 else "→")
            st.write(f"   ✓ Interés promedio {tr_r.interes_promedio:.0f}/100 · peak {tr_r.interes_peak} · {dir_t}")

            st.write("📱 Scrapeando Meta Ads + Marketplace (paralelo)…")
            from trendia.triangulator.meta_ads import _scrape_async as _meta_a
            from trendia.triangulator.fb_marketplace import _scrape_async as _mkt_a

            async def _par():
                return await asyncio.gather(_meta_a(kw), _mkt_a(kw))

            meta_r, mkt_r = asyncio.run(_par())

            # Preferir valor manual si el usuario lo ingresó; el scraper falla por bot detection
            n_meta = meta_manual if meta_manual > 0 else meta_r.num_anuncios
            n_mkt  = mkt_manual  if mkt_manual  > 0 else mkt_r.num_publicaciones

            meta_data = {"num_anuncios": n_meta}
            mkt_data  = {"num_publicaciones": n_mkt}

            meta_src = "manual" if meta_manual > 0 else ("scraper" if meta_r.num_anuncios > 0 else "⚠ no detectado")
            mkt_src  = "manual" if mkt_manual  > 0 else ("scraper" if mkt_r.num_publicaciones > 0 else "⚠ no detectado")
            st.write(f"   ✓ {n_meta} anuncios Meta [{meta_src}] · {n_mkt} publicaciones Marketplace [{mkt_src}]")
            if meta_impresiones != "No sé / no aparece":
                st.write(f"   ✓ Impresiones top anuncio: {meta_impresiones} · Antigüedad: {meta_meses}")

        elif dry_run:
            st.write("🎭 Modo demo — datos simulados")
            ml_data, tr_data, meta_data, mkt_data = _dry_run_datos(kw)
        else:
            st.write("⏭️ Triangulador desactivado — solo búsqueda web + Claude")
            ml_data   = {"total_productos": 0, "num_marcas": 0, "dominios": []}
            tr_data   = {"interes_promedio": 0, "interes_peak": 0, "tendencia": 0}
            meta_data = {"num_anuncios": meta_manual}
            mkt_data  = {"num_publicaciones": mkt_manual}

        # Paso 2: análisis 9 criterios
        if dry_run:
            st.write("🎭 Generando análisis simulado…")
            from trendia.analyzer.criterios import (
                AnalisisCompleto, AnguloVenta, CriterioResultado,
                MarcaSugerida, NOMBRES_CRITERIOS,
            )
            import random; random.seed(hash(kw) % 9999)
            estados = ["✅","✅","⚠️","✅","⚠️","✅","✅","⚠️","✅"]
            pts_map = {"✅": 2, "⚠️": 1, "❌": 0}
            criterios_d = [
                CriterioResultado(i+1, NOMBRES_CRITERIOS[i], estados[i],
                                  f"Dato simulado para '{kw}' — activa las APIs para datos reales.", pts_map[estados[i]])
                for i in range(9)
            ]
            analisis = AnalisisCompleto(
                keyword=kw,
                criterios=criterios_d,
                score_total=sum(c.puntos for c in criterios_d),
                angulos_venta=[
                    AnguloVenta("TESTIMONIAL", f"Yo no creía — hasta que probé {kw}",
                                f"Llevaba meses buscando solución y nada funcionaba. Una amiga me recomendó {kw} y desde el primer uso noté la diferencia. Lo mejor: llegó a mi casa y pagué solo cuando lo recibí. ¡Sin riesgo ninguno!"),
                    AnguloVenta("DEMOSTRACIÓN", f"Mira lo que hace el {kw} en 30 segundos",
                                f"[Mostrar producto] Antes: el problema visible. Después: el resultado. Así de sencillo. Sin complicaciones, sin trucos. Pídelo hoy con pago al recibir — si no te convence, no pagas."),
                    AnguloVenta("URGENCIA", f"Quedan solo 7 unidades de {kw} en stock",
                                f"No es broma — cada día salen más pedidos de {kw} y el stock se agota rápido. Si ves esto, todavía hay unidades disponibles. Pide el tuyo ahora: llega a tu puerta y pagas al recibirlo."),
                ],
                marca=MarcaSugerida(
                    nombre=f"{kw.split()[0].capitalize()}Pro",
                    razon="Nombre corto, fácil de recordar, proyecta calidad sin sonar genérico",
                    copy_anuncio=f"Descubre por qué miles de colombianos eligen {kw.split()[0].capitalize()}Pro. Envío a todo el país · Pago al recibir · Garantía total.",
                    valor_agregado="Incluir guía de uso + bolsa premium + tarjeta de garantía impresa",
                    empaque="Caja negra mate con logo dorado, papel tissue, sticker de agradecimiento personalizado",
                ),
                riesgos=[
                    "Validar precio FOB real antes de importar — el margen puede ser menor al esperado",
                    "Revisar política de devoluciones del courier — las tasas COD en Colombia son 15-25%",
                    "Probar creative exhaustion en Meta Ads — este tipo de producto quema audiencias rápido",
                ],
                veredicto="LANZAR CON PRECAUCIÓN",
                tokens_entrada=0,
                tokens_salida=0,
            )
        else:
            web_label = "con búsqueda web real" if usar_web else "sin búsqueda web"
            st.write(f"🤖 Evaluando 9 criterios {web_label} (Claude)…")
            from trendia.analyzer.motor import analizar as _analizar
            analisis = _analizar(
                keyword=kw,
                ml_data=ml_data,
                trends_data=tr_data,
                meta_data=meta_data,
                marketplace_data=mkt_data,
                usar_web_search=usar_web,
                meta_impresiones=meta_impresiones if meta_impresiones != "No sé / no aparece" else "",
                meta_meses=meta_meses if meta_meses != "No sé" else "",
            )

        status.update(label="¡Análisis completo!", state="complete", expanded=False)

    st.markdown("<br>", unsafe_allow_html=True)
    _mostrar_resultados(analisis)

elif not analizar_btn:
    # Estado vacío
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem;color:#444">
      <div style="font-size:3rem;margin-bottom:1rem">🔍</div>
      <div style="font-size:1.1rem;color:#555">Escribe el nombre de un producto y pulsa <strong style="color:#6366f1">Analizar</strong></div>
      <div style="font-size:0.85rem;color:#3a3a4a;margin-top:0.8rem">
        MercadoLibre · Google Trends · Meta Ads · TikTok · Alibaba · Dollar City · Amazon
      </div>
    </div>
    """, unsafe_allow_html=True)
