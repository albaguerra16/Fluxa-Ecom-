"""Genera un reporte HTML standalone a partir de un AnalisisCompleto."""

from __future__ import annotations

from datetime import datetime

from trendia.analyzer.criterios import AnalisisCompleto, ESTADO_OK, ESTADO_WARN

_VEREDICTO_COLOR = {
    "LANZAR":                ("#22c55e", "#0d2818"),
    "LANZAR CON PRECAUCIÓN": ("#f59e0b", "#2a1f06"),
    "NO LANZAR":             ("#ef4444", "#2a0d0d"),
}
_VEREDICTO_ICONO = {
    "LANZAR": "🚀",
    "LANZAR CON PRECAUCIÓN": "⚡",
    "NO LANZAR": "🚫",
}
_ESTADO_STYLE = {
    ESTADO_OK:   ("border-left:4px solid #22c55e;background:#0d2818",  "#22c55e"),
    ESTADO_WARN: ("border-left:4px solid #f59e0b;background:#2a1f06", "#f59e0b"),
    "#": ("border-left:4px solid #ef4444;background:#2a0d0d", "#ef4444"),
}


def _criterio_html(c) -> str:
    from trendia.analyzer.criterios import ESTADO_OK, ESTADO_WARN
    if c.estado == ESTADO_OK:
        style = "border-left:4px solid #22c55e;background:#0d2818"
        pts_color = "#22c55e"
    elif c.estado == ESTADO_WARN:
        style = "border-left:4px solid #f59e0b;background:#2a1f06"
        pts_color = "#f59e0b"
    else:
        style = "border-left:4px solid #ef4444;background:#2a0d0d"
        pts_color = "#ef4444"

    nota = c.nota.replace("<", "&lt;").replace(">", "&gt;")
    return f"""
    <div style="border-radius:10px;padding:1rem 1.2rem;margin-bottom:.6rem;{style}">
      <div style="font-weight:700;font-size:.92rem;color:#e0e0e0;display:flex;justify-content:space-between">
        <span>{c.estado}&nbsp; C{c.numero}. {c.nombre}</span>
        <span style="color:{pts_color}">{c.puntos}/2</span>
      </div>
      <div style="font-size:.8rem;color:#999;margin-top:.35rem">{nota}</div>
    </div>"""


def _angulo_html(ang, n: int) -> str:
    copy_esc = ang.copy.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    return f"""
    <div style="background:#1a1b26;border-radius:12px;padding:1.3rem;border:1px solid #2d2d3a">
      <div style="font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#8b5cf6;margin-bottom:.5rem">[{n}] {ang.nombre}</div>
      <div style="font-size:1rem;font-weight:700;color:#e0e0e0;margin-bottom:.7rem">"{ang.hook}"</div>
      <div style="font-size:.84rem;color:#a0a0b8;line-height:1.65">{copy_esc}</div>
    </div>"""


def generar_html(a: AnalisisCompleto) -> str:
    fecha = datetime.now().strftime("%d %b %Y · %H:%M")

    barra_ok   = '<div style="flex:1;height:10px;background:#22c55e;border-radius:4px"></div>' * a.aprobados
    barra_warn = '<div style="flex:1;height:10px;background:#f59e0b;border-radius:4px"></div>' * a.en_riesgo
    barra_fail = '<div style="flex:1;height:10px;background:#ef4444;border-radius:4px"></div>' * a.reprobados

    v_color, v_bg = _VEREDICTO_COLOR.get(a.veredicto, ("#6366f1", "#1a1b26"))
    v_icono = _VEREDICTO_ICONO.get(a.veredicto, "❓")

    criterios_html = "".join(_criterio_html(c) for c in a.criterios)

    angulos_html = "".join(
        f'<div style="flex:1;min-width:260px">{_angulo_html(ang, i+1)}</div>'
        for i, ang in enumerate(a.angulos_venta)
    )

    riesgos_html = "".join(
        f'<div style="background:#1f1208;border-left:3px solid #f59e0b;border-radius:6px;padding:.7rem 1rem;margin-bottom:.5rem;font-size:.86rem;color:#d0b080">⚠&nbsp;&nbsp;{r}</div>'
        for r in a.riesgos
    )

    tokens_html = (
        f'<p style="font-size:.72rem;color:#333;margin-top:2rem;text-align:center">Tokens: {a.tokens_entrada}↑ {a.tokens_salida}↓</p>'
        if a.tokens_entrada else ""
    )

    copy_anuncio = a.marca.copy_anuncio.replace("<", "&lt;").replace(">", "&gt;")
    valor_ag = a.marca.valor_agregado.replace("<", "&lt;").replace(">", "&gt;")
    empaque = a.marca.empaque.replace("<", "&lt;").replace(">", "&gt;")
    marca_razon = a.marca.razon.replace("<", "&lt;").replace(">", "&gt;")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trendia — {a.keyword}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#0f1117;color:#e0e0e0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:2rem 1rem}}
  .wrap{{max-width:960px;margin:0 auto}}
  h2{{font-size:.72rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#444;border-bottom:1px solid #2d2d3a;padding-bottom:.5rem;margin:2rem 0 1rem}}
  .copy-box{{background:#1a1b26;border:1px solid #2d2d3a;border-radius:8px;padding:1rem;font-size:.85rem;color:#b0b0c0;line-height:1.65;white-space:pre-wrap;cursor:text;user-select:all}}
  .copy-box:focus{{outline:2px solid #6366f1}}
  .label{{font-size:.7rem;letter-spacing:.07em;text-transform:uppercase;color:#555;margin-top:1rem;margin-bottom:.25rem}}
  @media(max-width:640px){{.angulos{{flex-direction:column!important}}}}
</style>
</head>
<body>
<div class="wrap">

  <!-- Header -->
  <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:1.5rem;flex-wrap:wrap;gap:.5rem">
    <div>
      <div style="font-size:1.3rem;font-weight:900;color:#6366f1">🔍 Trendia</div>
      <div style="font-size:.8rem;color:#555;margin-top:.15rem">Analizador COD Colombia · 9 criterios</div>
    </div>
    <div style="font-size:.78rem;color:#444;text-align:right">
      <div style="font-size:1.1rem;font-weight:700;color:#e0e0e0">{a.keyword}</div>
      {fecha}
    </div>
  </div>

  <!-- Score + Veredicto -->
  <div style="display:flex;gap:1.5rem;flex-wrap:wrap;margin-bottom:2rem">
    <div style="background:#1a1b26;border:1px solid #2d2d3a;border-radius:16px;padding:1.5rem 2rem;min-width:200px;text-align:center">
      <div style="font-size:3.5rem;font-weight:900;color:#6366f1;line-height:1">{a.score_total}<span style="font-size:1.5rem;color:#555">/18</span></div>
      <div style="font-size:.85rem;color:#777;margin-top:.3rem">{a.score_pct:.0f}% de viabilidad</div>
      <div style="display:flex;gap:4px;margin-top:.8rem">{barra_ok}{barra_warn}{barra_fail}</div>
      <div style="font-size:.78rem;color:#555;margin-top:.4rem">✅ {a.aprobados} &nbsp;⚠️ {a.en_riesgo} &nbsp;❌ {a.reprobados}</div>
    </div>

    <div style="flex:1;min-width:220px;background:{v_bg};border:2px solid {v_color};border-radius:16px;padding:1.5rem 2rem;display:flex;flex-direction:column;justify-content:center">
      <div style="font-size:2.8rem;line-height:1;margin-bottom:.4rem">{v_icono}</div>
      <div style="font-size:1.5rem;font-weight:900;color:#f0f0f0">{a.veredicto}</div>
      <div style="font-size:.82rem;color:#888;margin-top:.4rem">{a.keyword}</div>
    </div>
  </div>

  <!-- 9 Criterios -->
  <h2>Evaluación de criterios</h2>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:.5rem">
    {criterios_html}
  </div>

  <!-- Ángulos de venta -->
  <h2>3 ángulos de venta</h2>
  <div class="angulos" style="display:flex;gap:1rem;flex-wrap:wrap">
    {angulos_html}
  </div>

  <!-- Marca sugerida -->
  <h2>Marca sugerida</h2>
  <div style="background:#13131f;border:1px solid #2d2d3a;border-radius:12px;padding:1.5rem;display:grid;grid-template-columns:1fr 2fr;gap:1.5rem">
    <div>
      <div style="font-size:2.2rem;font-weight:900;color:#6366f1;margin-bottom:.8rem">{a.marca.nombre}</div>
      <div class="label">Por qué funciona</div>
      <div style="font-size:.85rem;color:#b0b0c0">{marca_razon}</div>
      <div class="label">Valor agregado</div>
      <div style="font-size:.85rem;color:#b0b0c0">{valor_ag}</div>
      <div class="label">Empaque</div>
      <div style="font-size:.85rem;color:#b0b0c0">{empaque}</div>
    </div>
    <div>
      <div class="label">Copy de anuncio principal</div>
      <div class="copy-box" tabindex="0">{copy_anuncio}</div>
    </div>
  </div>

  <!-- Riesgos -->
  <h2>Riesgos antes de lanzar</h2>
  {riesgos_html}

  {tokens_html}
</div>
</body>
</html>"""
