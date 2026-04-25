#!/usr/bin/env python3
"""Pipeline completo de Trendia: triangulación → landing → video.

Uso:
    python scripts/run_pipeline.py "faja colombiana"
    python scripts/run_pipeline.py "faja colombiana" --variaciones 2
    python scripts/run_pipeline.py "faja colombiana" --solo-triangular
    python scripts/run_pipeline.py "faja colombiana" --imagen-url https://cdn.ejemplo.com/img.jpg
    python scripts/run_pipeline.py "faja colombiana" --threshold 50 --no-video
    python scripts/run_pipeline.py "faja colombiana" --no-publicar

Flags:
    --threshold INT      Score mínimo para continuar al landing (default: SCORE_THRESHOLD del .env)
    --variaciones INT    Número de variaciones de video (default: VIDEO_VARIATIONS del .env)
    --imagen-url URL     URL de imagen del producto para la landing page
    --contexto STR       Info adicional para Claude (precio, USP, restricciones)
    --solo-triangular    Detiene el pipeline tras mostrar el score
    --no-publicar        Genera el HTML pero no lo sube a Shopify
    --no-video           Omite el módulo de video
    --dry-run            Simula todo sin llamar a APIs externas (útil para CI)
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Ancla el cwd a la raíz del proyecto (parent de scripts/) para que
# python-decouple encuentre .env sin importar desde dónde se llame el script.
_PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(_PROJECT_ROOT)
sys.path.insert(0, str(_PROJECT_ROOT))

from decouple import config


# ── Helpers de presentación ───────────────────────────────────────────────────

def _sep(titulo: str = "", ancho: int = 60) -> None:
    if titulo:
        relleno = (ancho - len(titulo) - 2) // 2
        print(f"\n{'─' * relleno} {titulo} {'─' * relleno}")
    else:
        print("─" * ancho)


def _ok(msg: str) -> None:
    print(f"  ✅ {msg}")


def _warn(msg: str) -> None:
    print(f"  ⚠️  {msg}", file=sys.stderr)


def _err(msg: str) -> None:
    print(f"  ❌ {msg}", file=sys.stderr)


def _paso(n: int, total: int, nombre: str) -> None:
    print(f"\n[{n}/{total}] {nombre}")


# ── Etapas ────────────────────────────────────────────────────────────────────

def etapa_triangular(keyword: str, dry_run: bool) -> "ProductScore":  # type: ignore[name-defined]  # noqa: F821
    from trendia.triangulator.mercadolibre import buscar
    from trendia.triangulator.trends import interes_colombia
    from trendia.triangulator.scorer import puntuar, ProductScore

    if dry_run:
        from trendia.triangulator.mercadolibre import MLResultado
        from trendia.triangulator.trends import TrendsResultado
        ml = MLResultado(keyword, total_productos=1500, num_marcas=20, dominios=["MCO-BODY_SHAPERS"])
        tr = TrendsResultado(keyword, interes_promedio=55.0, interes_peak=100, tendencia=0.8, semanas_con_datos=90)
        score = puntuar(ml, tr)
        print(f"  [dry-run] ML simulado: {ml}")
        print(f"  [dry-run] Trends simulado: {tr}")
        return score

    t0 = time.monotonic()
    print("  → Consultando MercadoLibre Colombia…")
    ml = buscar(keyword)
    print(f"  {ml}")

    print("  → Consultando Google Trends Colombia…")
    tr = interes_colombia(keyword)
    print(f"  {tr}")

    score = puntuar(ml, tr)
    print(f"\n  {score}")
    print(f"  Tiempo: {time.monotonic() - t0:.1f}s")
    return score


def etapa_landing(
    score: "ProductScore",  # type: ignore[name-defined]  # noqa: F821
    imagen_url: str,
    contexto: str,
    publicar: bool,
    dry_run: bool,
) -> tuple["LandingCopy", "LandingHTML", "ShopifyPage | None"]:  # type: ignore[name-defined]  # noqa: F821
    from trendia.landing.generator import generar_copy, LandingCopy
    from trendia.landing.templates import renderizar, LandingHTML

    if dry_run:
        from trendia.landing.generator import LandingCopy
        from trendia.landing.templates import LandingHTML
        copy = LandingCopy(
            keyword=score.keyword,
            headline=f"[dry-run] {score.keyword.title()} — Pago Contra Entrega",
            subheadline="Recíbelo en casa y paga solo si te encanta",
            bullets=["🔥 Beneficio 1", "💪 Beneficio 2", "📦 Beneficio 3", "✅ Beneficio 4", "🔄 Beneficio 5"],
            cta_principal="Pedir ahora — pago al recibir",
            cta_secundario="¡Solo quedan 8 unidades!",
            garantia="Si no te gusta, la devuelves sin costo",
            badge_cod="Pago al recibir",
        )
        landing = renderizar(copy, imagen_url)
        print(f"  [dry-run] Copy generado para '{score.keyword}'")
        print(f"  [dry-run] HTML: {len(landing.html)} caracteres")
        return copy, landing, None

    t0 = time.monotonic()
    print("  → Generando copy con Claude API…")
    ml_dominios = getattr(score, "_dominios", [])  # disponible si score tiene contexto extra
    copy = generar_copy(
        keyword=score.keyword,
        score=score.score,
        dominios=ml_dominios,
        contexto_extra=contexto,
    )
    cache_info = "[cache hit]" if copy.cache_hit else "[cache miss]"
    _ok(f"Copy generado {cache_info} — {copy.tokens_entrada}↑ {copy.tokens_salida}↓ tokens")
    print(f"\n  Headline:    {copy.headline}")
    print(f"  CTA:         {copy.cta_principal}")
    print(f"  Badge COD:   {copy.badge_cod}")

    print("\n  → Renderizando HTML (Jinja2)…")
    landing = renderizar(copy, imagen_url)
    _ok(f"HTML generado — {len(landing.html):,} caracteres")

    page = None
    if publicar:
        print("  → Publicando en Shopify…")
        from trendia.landing.shopify import publicar as shopify_publicar
        page = shopify_publicar(copy, landing)
        _ok(f"Página publicada")
        print(f"  Pública:  {page.url}")
        print(f"  Admin:    {page.admin_url}")
    else:
        _warn("Publicación en Shopify omitida (--no-publicar)")

    print(f"  Tiempo: {time.monotonic() - t0:.1f}s")
    return copy, landing, page


def etapa_video(
    copy: "LandingCopy",  # type: ignore[name-defined]  # noqa: F821
    n: int,
    dry_run: bool,
) -> "LoteVideos":  # type: ignore[name-defined]  # noqa: F821
    from trendia.video.variations import generar_variaciones, LoteVideos

    if dry_run:
        from trendia.video.fal_client import Angulo, VideoJob
        jobs = [
            VideoJob(a, f"[dry-run] prompt para {a.value}", video_url=f"https://fal.ai/dry-run/{a.value}.mp4")
            for a in list(Angulo)[:n]
        ]
        lote = LoteVideos(keyword=copy.keyword, jobs=jobs)
        print(f"  [dry-run] {n} variaciones simuladas")
        return lote

    t0 = time.monotonic()
    print(f"  → Generando {n} variaciones en paralelo (fal.ai kling-video)…")
    print("  (esto puede tardar 2-5 minutos por video)")
    lote = generar_variaciones(copy, n=n)

    for job in lote.exitosos:
        _ok(f"{job.angulo.value}: {job.video_url}")
    for job in lote.fallidos:
        _err(f"{job.angulo.value}: {job.error}")

    print(f"\n  {len(lote.exitosos)}/{len(lote.jobs)} videos generados — Tiempo: {time.monotonic() - t0:.1f}s")
    return lote


# ── CLI ───────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pipeline Trendia: triangulación → landing → video (dropshipping COD Colombia)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("keyword", help="Producto a analizar (ej: 'faja colombiana')")
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Score mínimo para continuar al landing (default: SCORE_THRESHOLD en .env)",
    )
    parser.add_argument(
        "--variaciones",
        type=int,
        default=None,
        help="Número de variaciones de video (default: VIDEO_VARIATIONS en .env)",
    )
    parser.add_argument("--imagen-url", default="", metavar="URL", help="URL de imagen del producto")
    parser.add_argument("--contexto", default="", metavar="STR", help="Info adicional para Claude")
    parser.add_argument("--solo-triangular", action="store_true", help="Solo muestra el score y sale")
    parser.add_argument("--no-publicar", action="store_true", help="No sube la página a Shopify")
    parser.add_argument("--no-video", action="store_true", help="Omite la generación de video")
    parser.add_argument("--dry-run", action="store_true", help="Simula sin llamar a APIs externas")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    threshold = args.threshold or config("SCORE_THRESHOLD", default=60, cast=float)
    n_videos = args.variaciones or config("VIDEO_VARIATIONS", default=3, cast=int)
    total_pasos = 1 if args.solo_triangular else (2 if args.no_video else 3)

    print(f"\n{'═' * 60}")
    print(f"  TRENDIA — Pipeline COD Colombia")
    print(f"  Producto: {args.keyword!r}")
    if args.dry_run:
        print("  Modo: DRY-RUN (sin llamadas a APIs)")
    print(f"{'═' * 60}")

    # ── Etapa 1: Triangulación ────────────────────────────────────────────────
    _paso(1, total_pasos, "TRIANGULACIÓN (MercadoLibre + Google Trends)")
    try:
        score = etapa_triangular(args.keyword, args.dry_run)
    except Exception as exc:
        _err(f"Triangulación falló: {exc}")
        return 1

    if args.solo_triangular:
        _sep()
        print(f"  Score final: {score.score:.1f}/100 → {score.recomendacion}")
        return 0

    if score.score < threshold and not args.dry_run:
        _sep()
        _warn(
            f"Score {score.score:.1f} < threshold {threshold:.0f} → producto descartado.\n"
            f"  Usa --threshold {int(score.score)} para forzar la ejecución."
        )
        return 0

    # ── Etapa 2: Landing page ─────────────────────────────────────────────────
    _paso(2, total_pasos, "LANDING PAGE (Claude API + Shopify)")
    try:
        copy, landing, page = etapa_landing(
            score=score,
            imagen_url=args.imagen_url,
            contexto=args.contexto,
            publicar=not args.no_publicar,
            dry_run=args.dry_run,
        )
    except EnvironmentError as exc:
        _err(str(exc))
        _warn("Configura las variables en .env y vuelve a intentar.")
        return 1
    except Exception as exc:
        _err(f"Landing falló: {exc}")
        return 1

    if args.no_video:
        _sep("RESUMEN")
        print(f"  Keyword:    {args.keyword}")
        print(f"  Score:      {score.score:.1f}/100 → {score.recomendacion}")
        if page:
            print(f"  Landing:    {page.url}")
        return 0

    # ── Etapa 3: Video ────────────────────────────────────────────────────────
    _paso(3, total_pasos, f"VIDEO ({n_videos} variaciones — fal.ai kling-video)")
    try:
        lote = etapa_video(copy, n_videos, args.dry_run)
    except EnvironmentError as exc:
        _err(str(exc))
        return 1
    except Exception as exc:
        _err(f"Video falló: {exc}")
        return 1

    # ── Resumen final ─────────────────────────────────────────────────────────
    _sep("RESUMEN FINAL")
    print(f"  Keyword:      {args.keyword}")
    print(f"  Score:        {score.score:.1f}/100 → {score.recomendacion}")
    print(f"  Recomendación: {score.razon}")
    if page:
        print(f"  Landing:      {page.url}")
    print(f"  Videos:       {len(lote.exitosos)}/{len(lote.jobs)} generados")
    for job in lote.exitosos:
        print(f"    [{job.angulo.value}] {job.video_url}")
    _sep()
    return 0


if __name__ == "__main__":
    sys.exit(main())
