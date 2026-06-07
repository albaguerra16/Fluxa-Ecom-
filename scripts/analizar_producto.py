#!/usr/bin/env python3
"""Analizador de 9 criterios para dropshipping COD Colombia.

Flujo: recibe keyword → triangulador (ML + Trends + Meta Ads + Marketplace)
       → búsqueda web real → 9 criterios → reporte completo.

Uso:
    python scripts/analizar_producto.py "faja colombiana"
    python scripts/analizar_producto.py "faja colombiana" --dry-run
    python scripts/analizar_producto.py "faja colombiana" --sin-web
    python scripts/analizar_producto.py "faja colombiana" --solo-reporte

Flags:
    --dry-run       Simula sin llamar a APIs externas (útil para CI/tests)
    --sin-web       Desactiva web_search (más rápido, menos preciso)
    --solo-reporte  Solo muestra el reporte final, suprime logs del triangulador
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(_PROJECT_ROOT)
sys.path.insert(0, str(_PROJECT_ROOT))

from trendia.analyzer.criterios import (
    ESTADO_FAIL,
    ESTADO_OK,
    ESTADO_WARN,
    AnalisisCompleto,
)


# ── Helpers de salida ─────────────────────────────────────────────────────────

def _linea(char: str = "─", ancho: int = 68) -> None:
    print(char * ancho)


def _titulo(texto: str, char: str = "═", ancho: int = 68) -> None:
    relleno = max(0, ancho - len(texto) - 2)
    izq = relleno // 2
    der = relleno - izq
    print(f"\n{char * izq} {texto} {char * der}")


def _seccion(texto: str) -> None:
    print(f"\n  ▸ {texto}")


# ── Datos de dry-run ──────────────────────────────────────────────────────────

def _dry_run_datos(keyword: str) -> tuple[dict, dict, dict, dict]:
    ml    = {"total_productos": 1_500, "num_marcas": 22, "dominios": ["MCO-BODY_SHAPERS"]}
    tr    = {"interes_promedio": 55.0, "interes_peak": 100, "tendencia": 0.8}
    meta  = {"num_anuncios": 12}
    mkt   = {"num_publicaciones": 18}
    print(f"  [dry-run] ML:          {ml}")
    print(f"  [dry-run] Trends:      {tr}")
    print(f"  [dry-run] Meta Ads:    {meta}")
    print(f"  [dry-run] Marketplace: {mkt}")
    return ml, tr, meta, mkt


# ── Triangulación real ────────────────────────────────────────────────────────

def _triangular(keyword: str) -> tuple[dict, dict, dict, dict]:
    from trendia.triangulator.mercadolibre import buscar
    from trendia.triangulator.trends import interes_colombia
    from trendia.triangulator.meta_ads import _scrape_async as _meta_async
    from trendia.triangulator.fb_marketplace import _scrape_async as _mkt_async

    print("  → MercadoLibre Colombia…")
    ml_r = buscar(keyword)
    print(f"    {ml_r}")

    print("  → Google Trends Colombia…")
    tr_r = interes_colombia(keyword)
    print(f"    {tr_r}")

    print("  → Meta Ads Library + FB Marketplace (paralelo)…")

    async def _paralelo():
        return await asyncio.gather(_meta_async(keyword), _mkt_async(keyword))

    meta_r, mkt_r = asyncio.run(_paralelo())
    print(f"    {meta_r}")
    print(f"    {mkt_r}")

    ml   = {"total_productos": ml_r.total_productos, "num_marcas": ml_r.num_marcas, "dominios": ml_r.dominios}
    tr   = {"interes_promedio": tr_r.interes_promedio, "interes_peak": tr_r.interes_peak, "tendencia": tr_r.tendencia}
    meta = {"num_anuncios": meta_r.num_anuncios}
    mkt  = {"num_publicaciones": mkt_r.num_publicaciones}
    return ml, tr, meta, mkt


# ── Reporte de salida ─────────────────────────────────────────────────────────

_ICONOS_VEREDICTO = {
    "LANZAR": "🚀",
    "LANZAR CON PRECAUCIÓN": "⚡",
    "NO LANZAR": "🚫",
}


def _imprimir_reporte(a: AnalisisCompleto) -> None:
    _titulo(f"ANÁLISIS 9 CRITERIOS — {a.keyword.upper()}")

    # ── Score resumen ──────────────────────────────────────────────────────────
    print()
    barra_ok   = "█" * a.aprobados
    barra_warn = "▒" * a.en_riesgo
    barra_fail = "░" * a.reprobados
    barra = barra_ok + barra_warn + barra_fail
    print(f"  Score   {a.score_total}/18  ({a.score_pct:.0f}%)   [{barra}]")
    print(f"  {ESTADO_OK} {a.aprobados}  {ESTADO_WARN} {a.en_riesgo}  {ESTADO_FAIL} {a.reprobados}")

    # ── 9 criterios ───────────────────────────────────────────────────────────
    _titulo("EVALUACIÓN DE CRITERIOS", char="─")
    for c in a.criterios:
        print(f"\n  {c.estado}  C{c.numero}. {c.nombre}  [{c.puntos}/2]")
        # Partir nota en líneas si es muy larga
        nota = c.nota.strip()
        if len(nota) > 72:
            palabras = nota.split()
            linea_actual = "       "
            for palabra in palabras:
                if len(linea_actual) + len(palabra) + 1 > 72:
                    print(linea_actual)
                    linea_actual = "       " + palabra
                else:
                    linea_actual += " " + palabra
            if linea_actual.strip():
                print(linea_actual)
        else:
            print(f"       {nota}")

    # ── Ángulos de venta ──────────────────────────────────────────────────────
    _titulo("3 ÁNGULOS DE VENTA", char="─")
    for i, ang in enumerate(a.angulos_venta, 1):
        print(f"\n  [{i}] {ang.nombre}")
        print(f"  Hook: {ang.hook}")
        print()
        # Partir copy en líneas de 70 chars
        palabras = ang.copy.split()
        linea_actual = "  "
        for p in palabras:
            if len(linea_actual) + len(p) + 1 > 70:
                print(linea_actual)
                linea_actual = "  " + p
            else:
                linea_actual += " " + p
        if linea_actual.strip():
            print(linea_actual)

    # ── Marca sugerida ────────────────────────────────────────────────────────
    _titulo("MARCA SUGERIDA", char="─")
    print(f"\n  Nombre:          {a.marca.nombre}")
    print(f"  Razón:           {a.marca.razon}")
    print(f"\n  Copy de anuncio:")
    print(f"  {a.marca.copy_anuncio}")
    print(f"\n  Valor agregado:  {a.marca.valor_agregado}")
    print(f"  Empaque:         {a.marca.empaque}")

    # ── Riesgos ───────────────────────────────────────────────────────────────
    _titulo("RIESGOS ANTES DE LANZAR", char="─")
    for r in a.riesgos:
        print(f"\n  ⚠  {r}")

    # ── Veredicto ─────────────────────────────────────────────────────────────
    icono = _ICONOS_VEREDICTO.get(a.veredicto, "❓")
    _titulo("VEREDICTO", char="═")
    print()
    print(f"  {icono}  {a.veredicto}")
    print()
    _linea("═")

    if a.tokens_entrada:
        print(f"  Tokens: {a.tokens_entrada}↑ {a.tokens_salida}↓")


# ── CLI ───────────────────────────────────────────────────────────────────────

def _args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Analizador 9 criterios dropshipping COD Colombia",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("keyword", help="Producto a analizar (ej: 'faja colombiana')")
    p.add_argument("--dry-run", action="store_true", help="Simula sin llamar a APIs externas")
    p.add_argument("--sin-web", action="store_true", help="Desactiva búsqueda web (más rápido)")
    p.add_argument("--solo-reporte", action="store_true", help="Suprime logs del triangulador")
    return p.parse_args()


def main() -> int:
    args = _args()

    _titulo(f"TRENDIA — Analizador de Producto")
    print(f"  Producto: {args.keyword!r}")
    modo_parts = []
    if args.dry_run:
        modo_parts.append("dry-run")
    if args.sin_web:
        modo_parts.append("sin web search")
    if modo_parts:
        print(f"  Modo: {', '.join(modo_parts)}")
    print()

    # ── Paso 1: Triangulación ─────────────────────────────────────────────────
    _linea()
    print("  [1/2] TRIANGULACIÓN")
    _linea()

    t0 = time.monotonic()
    try:
        if args.dry_run:
            ml_data, tr_data, meta_data, mkt_data = _dry_run_datos(args.keyword)
        else:
            if args.solo_reporte:
                # Redirigir stdout temporalmente para suprimir logs del triangulador
                import io
                old_out = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    ml_data, tr_data, meta_data, mkt_data = _triangular(args.keyword)
                finally:
                    sys.stdout = old_out
            else:
                ml_data, tr_data, meta_data, mkt_data = _triangular(args.keyword)
    except Exception as exc:
        print(f"\n  ❌ Triangulación falló: {exc}", file=sys.stderr)
        return 1

    print(f"\n  Tiempo triangulación: {time.monotonic() - t0:.1f}s")

    # ── Paso 2: Análisis 9 criterios ──────────────────────────────────────────
    _linea()
    web_label = "búsqueda web real" if not args.sin_web else "sin búsqueda web"
    print(f"  [2/2] ANÁLISIS 9 CRITERIOS ({web_label})")
    _linea()

    if args.dry_run:
        from trendia.analyzer.criterios import CriterioResultado, NOMBRES_CRITERIOS
        import random
        random.seed(hash(args.keyword))
        estados = [ESTADO_OK, ESTADO_OK, ESTADO_WARN, ESTADO_OK, ESTADO_WARN,
                   ESTADO_OK, ESTADO_OK, ESTADO_WARN, ESTADO_OK]
        puntos_map = {ESTADO_OK: 2, ESTADO_WARN: 1, ESTADO_FAIL: 0}
        criterios_dry = [
            CriterioResultado(
                numero=i + 1,
                nombre=NOMBRES_CRITERIOS[i],
                estado=estados[i],
                nota=f"[dry-run] Dato simulado para {args.keyword}",
                puntos=puntos_map[estados[i]],
            )
            for i in range(9)
        ]
        from trendia.analyzer.criterios import AnalisisCompleto, AnguloVenta, MarcaSugerida
        analisis = AnalisisCompleto(
            keyword=args.keyword,
            criterios=criterios_dry,
            score_total=sum(c.puntos for c in criterios_dry),
            angulos_venta=[
                AnguloVenta("TESTIMONIAL", "[dry-run] Hook testimonial", "[dry-run] Copy testimonial completo."),
                AnguloVenta("DEMOSTRACIÓN", "[dry-run] Hook demo", "[dry-run] Copy demo completo."),
                AnguloVenta("URGENCIA", "[dry-run] Hook urgencia", "[dry-run] Copy urgencia completo."),
            ],
            marca=MarcaSugerida(
                nombre="[DryBrand]",
                razon="Simulado para pruebas",
                copy_anuncio="[dry-run] Copy de anuncio simulado.",
                valor_agregado="[dry-run] Valor agregado simulado.",
                empaque="[dry-run] Empaque simulado.",
            ),
            riesgos=["[dry-run] Riesgo 1 simulado", "[dry-run] Riesgo 2 simulado"],
            veredicto="LANZAR CON PRECAUCIÓN",
        )
        print("  [dry-run] Análisis simulado generado")
    else:
        t1 = time.monotonic()
        if not args.sin_web:
            print("  → Buscando en web (TikTok, Alibaba, Dollar City, Amazon…)")
        print("  → Evaluando 9 criterios con Claude…")
        try:
            from trendia.analyzer.motor import analizar
            analisis = analizar(
                keyword=args.keyword,
                ml_data=ml_data,
                trends_data=tr_data,
                meta_data=meta_data,
                marketplace_data=mkt_data,
                usar_web_search=not args.sin_web,
            )
        except EnvironmentError as exc:
            print(f"\n  ❌ {exc}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"\n  ❌ Análisis falló: {exc}", file=sys.stderr)
            raise

        print(f"\n  Tiempo análisis: {time.monotonic() - t1:.1f}s")

    # ── Reporte ───────────────────────────────────────────────────────────────
    _imprimir_reporte(analisis)
    return 0


if __name__ == "__main__":
    sys.exit(main())
