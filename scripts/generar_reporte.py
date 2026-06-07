#!/usr/bin/env python3
"""Genera un reporte HTML standalone del análisis de 9 criterios.

El reporte se guarda como un archivo .html que puedes abrir en cualquier
navegador con doble clic — no necesita servidor ni conexión una vez generado.

Uso:
    python3.11 scripts/generar_reporte.py "faja colombiana"
    python3.11 scripts/generar_reporte.py "faja colombiana" --dry-run
    python3.11 scripts/generar_reporte.py "faja colombiana" --sin-web
    python3.11 scripts/generar_reporte.py "faja colombiana" --no-abrir
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).parent.parent
os.chdir(_ROOT)
sys.path.insert(0, str(_ROOT))

_REPORTES = _ROOT / "reportes"


def _slug(texto: str) -> str:
    s = re.sub(r"[^a-z0-9\s-]", "", texto.lower())
    return re.sub(r"\s+", "-", s.strip())[:40]


def _triangular(keyword: str, status_fn) -> tuple[dict, dict, dict, dict]:
    from trendia.triangulator.mercadolibre import buscar
    from trendia.triangulator.trends import interes_colombia
    from trendia.triangulator.meta_ads import _scrape_async as _meta_a
    from trendia.triangulator.fb_marketplace import _scrape_async as _mkt_a

    status_fn("MercadoLibre Colombia…")
    ml_r = buscar(keyword)

    status_fn("Google Trends Colombia…")
    tr_r = interes_colombia(keyword)

    status_fn("Meta Ads + Marketplace (paralelo)…")

    async def _par():
        return await asyncio.gather(_meta_a(keyword), _mkt_a(keyword))

    meta_r, mkt_r = asyncio.run(_par())

    return (
        {"total_productos": ml_r.total_productos, "num_marcas": ml_r.num_marcas, "dominios": ml_r.dominios},
        {"interes_promedio": tr_r.interes_promedio, "interes_peak": tr_r.interes_peak, "tendencia": tr_r.tendencia},
        {"num_anuncios": meta_r.num_anuncios},
        {"num_publicaciones": mkt_r.num_publicaciones},
    )


def _dry_datos() -> tuple[dict, dict, dict, dict]:
    return (
        {"total_productos": 1_500, "num_marcas": 22, "dominios": ["MCO-BODY_SHAPERS"]},
        {"interes_promedio": 55.0, "interes_peak": 100, "tendencia": 0.8},
        {"num_anuncios": 12},
        {"num_publicaciones": 18},
    )


def main() -> int:
    p = argparse.ArgumentParser(description="Genera reporte HTML de 9 criterios COD Colombia")
    p.add_argument("keyword", help="Producto a analizar")
    p.add_argument("--dry-run",  action="store_true", help="Simula sin llamar a APIs")
    p.add_argument("--sin-web",  action="store_true", help="Desactiva búsqueda web")
    p.add_argument("--no-abrir", action="store_true", help="No abre el navegador automáticamente")
    args = p.parse_args()

    kw = args.keyword.strip()
    print(f"\n🔍 Analizando: {kw!r}")
    print("─" * 50)

    def log(msg: str) -> None:
        print(f"  → {msg}")

    # ── Triangulación ─────────────────────────────────────────────────────────
    if args.dry_run:
        log("Modo demo — datos simulados")
        ml_data, tr_data, meta_data, mkt_data = _dry_datos()
    else:
        try:
            ml_data, tr_data, meta_data, mkt_data = _triangular(kw, log)
        except Exception as exc:
            print(f"\n❌ Triangulación falló: {exc}", file=sys.stderr)
            return 1

    # ── Análisis 9 criterios ──────────────────────────────────────────────────
    if args.dry_run:
        log("Análisis simulado (dry-run)…")
        from trendia.analyzer.criterios import (
            AnalisisCompleto, AnguloVenta, CriterioResultado,
            MarcaSugerida, NOMBRES_CRITERIOS,
        )
        estados = ["✅","✅","⚠️","✅","⚠️","✅","✅","⚠️","✅"]
        pts_m   = {"✅": 2, "⚠️": 1, "❌": 0}
        crits = [
            CriterioResultado(i+1, NOMBRES_CRITERIOS[i], estados[i],
                              f"Dato simulado · activa las APIs para datos reales.", pts_m[estados[i]])
            for i in range(9)
        ]
        analisis = AnalisisCompleto(
            keyword=kw,
            criterios=crits,
            score_total=sum(c.puntos for c in crits),
            angulos_venta=[
                AnguloVenta("TESTIMONIAL",
                    f"Yo no creía hasta que probé {kw}",
                    f"Llevaba meses buscando una solución y nada funcionaba. Una amiga me recomendó {kw} y desde el primer uso noté la diferencia. Lo mejor: llegó a mi casa y pagué solo cuando lo recibí. ¡Sin riesgo ninguno!"),
                AnguloVenta("DEMOSTRACIÓN",
                    f"Mira lo que hace el {kw} en 30 segundos",
                    f"Antes: el problema visible. Después de usar {kw}: el resultado. Sin trucos, sin complicaciones. Pídelo hoy con pago al recibir — si no te convence, no pagas."),
                AnguloVenta("URGENCIA",
                    f"Quedan solo 7 unidades de {kw}",
                    f"Cada día salen más pedidos y el stock se agota rápido. Si ves esto, todavía hay unidades. Pide el tuyo ahora: llega a tu puerta y pagas cuando lo recibas."),
            ],
            marca=MarcaSugerida(
                nombre=f"{kw.split()[0].title()}Pro",
                razon="Nombre corto, fácil de recordar, proyecta calidad sin sonar genérico.",
                copy_anuncio=f"Descubre por qué miles de colombianos eligen {kw.split()[0].title()}Pro. Envío a todo el país · Pago al recibir · Garantía total.",
                valor_agregado="Incluir guía de uso + bolsa premium + tarjeta de garantía impresa.",
                empaque="Caja negra mate con logo dorado, papel tissue, sticker de agradecimiento personalizado.",
            ),
            riesgos=[
                "Validar precio FOB real — el margen puede ser menor al esperado.",
                "Revisar política de devoluciones del courier — tasas COD en Colombia son 15-25%.",
                "Probar creative exhaustion en Meta Ads — este tipo de producto quema audiencias rápido.",
            ],
            veredicto="LANZAR CON PRECAUCIÓN",
        )
    else:
        web_label = "con búsqueda web" if not args.sin_web else "sin búsqueda web"
        log(f"Evaluando 9 criterios {web_label} (Claude)…")
        try:
            from trendia.analyzer.motor import analizar
            analisis = analizar(
                keyword=kw,
                ml_data=ml_data,
                trends_data=tr_data,
                meta_data=meta_data,
                marketplace_data=mkt_data,
                usar_web_search=not args.sin_web,
            )
        except EnvironmentError as exc:
            print(f"\n❌ {exc}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"\n❌ Análisis falló: {exc}", file=sys.stderr)
            raise

    # ── Generar HTML ──────────────────────────────────────────────────────────
    from trendia.analyzer.reporte_html import generar_html

    html = generar_html(analisis)

    _REPORTES.mkdir(exist_ok=True)
    fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
    nombre = f"reporte_{_slug(kw)}_{fecha_str}.html"
    ruta = _REPORTES / nombre
    ruta.write_text(html, encoding="utf-8")

    print(f"\n✅ Reporte guardado en:")
    print(f"   {ruta}")

    if not args.no_abrir:
        webbrowser.open(ruta.as_uri())
        print("   (se abre en tu navegador automáticamente)")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
