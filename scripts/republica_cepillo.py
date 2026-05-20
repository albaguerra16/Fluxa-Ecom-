#!/usr/bin/env python3
"""Republica la landing page premium del cepillo masajeador de cabello.

Flujo:
  1. Genera copy con Claude API (headline, beneficios, antes/ahora, testimonios)
  2. Renderiza template premium azul oscuro (Jinja2)
  3. Publica/actualiza en Shopify via REST API
  4. Imprime la URL pública

Uso:
    python scripts/republica_cepillo.py
    python scripts/republica_cepillo.py --imagen-url https://cdn.ejemplo.com/cepillo.jpg
    python scripts/republica_cepillo.py --stock 5 --viendo 31
    python scripts/republica_cepillo.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(_PROJECT_ROOT)
sys.path.insert(0, str(_PROJECT_ROOT))

KEYWORD = "cepillo masajeador de cabello"
PRODUCT_HANDLE = "cepillo-masajeador-de-cabello"
SCORE = 75.0


def _sep(titulo: str = "") -> None:
    relleno = (58 - len(titulo) - 2) // 2 if titulo else 0
    print(f"\n{'─' * relleno} {titulo} {'─' * relleno}" if titulo else "─" * 60)


def _ok(msg: str) -> None:
    print(f"  ✅ {msg}")


def _err(msg: str) -> None:
    print(f"  ❌ {msg}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Republica landing premium del cepillo masajeador")
    parser.add_argument("--imagen-url", default="", metavar="URL")
    parser.add_argument("--stock", type=int, default=7)
    parser.add_argument("--viendo", type=int, default=23)
    parser.add_argument("--dry-run", action="store_true", help="No publica en Shopify")
    args = parser.parse_args()

    print(f"\n{'═' * 60}")
    print(f"  TRENDIA — Landing Premium COD")
    print(f"  Producto: {KEYWORD!r}")
    if args.dry_run:
        print("  Modo: DRY-RUN")
    print(f"{'═' * 60}")

    # ── Etapa 1: Generar copy con Claude API ──────────────────────────────────
    _sep("1 · GENERANDO COPY CON CLAUDE")
    print(f"  → Keyword: {KEYWORD!r}  score: {SCORE}")

    if args.dry_run:
        from trendia.landing.generator import LandingCopyPremium
        copy = LandingCopyPremium(
            keyword=KEYWORD,
            headline="[dry-run] Cabello sin frizz desde el primer uso",
            subheadline="Masaje capilar profesional en casa. Pagas solo cuando llegue.",
            beneficios=[
                "Activa la circulación del cuero cabelludo en minutos",
                "Elimina el frizz sin dañar la fibra capilar",
                "Masaje relajante que reduces el estrés diario",
                "Compatible con cualquier tipo de cabello",
                "Batería que dura toda la semana con una sola carga",
            ],
            antes=[
                "Cabello opaco y sin vida cada mañana",
                "Cuero cabelludo tenso y con picazón",
                "Horas frente al espejo sin resultado",
                "Productos caros que no funcionan",
            ],
            ahora=[
                "Brillo natural desde el primer uso",
                "Cuero cabelludo relajado y limpio",
                "Rutina de 5 minutos con resultado visible",
                "Una sola herramienta que lo hace todo",
            ],
            testimoniales=[
                {"nombre": "Valentina Ospina", "ciudad": "Medellín", "texto": "Llevaba años con el cuero cabelludo tenso y con picazón. Con este cepillo en una semana noté la diferencia. Lo recomiendo a todas mis amigas.", "estrellas": 5},
                {"nombre": "Daniela Moreno", "ciudad": "Bogotá", "texto": "Al principio desconfiaba porque pagaba al recibirlo, pero llegó perfecto. Mi cabello se ve brillante y el masaje es muy relajante después de trabajar.", "estrellas": 5},
                {"nombre": "Alejandra Castaño", "ciudad": "Cali", "texto": "Pensé que era otro de esos productos que no sirven, pero me sorprendió. Ya llevo dos meses usándolo todos los días y mi cabello cambió.", "estrellas": 5},
            ],
            cta_principal="Pedir ahora — pago al recibir",
            badge_cod="Pago contraentrega",
        )
        print("  [dry-run] Copy simulado OK")
    else:
        t0 = time.monotonic()
        from trendia.landing.generator import generar_copy_premium
        try:
            copy = generar_copy_premium(KEYWORD, score=SCORE)
        except Exception as exc:
            _err(f"Claude API falló: {exc}")
            return 1
        cache_info = "[cache hit]" if copy.cache_hit else "[cache miss]"
        _ok(f"Copy generado {cache_info} — {copy.tokens_entrada}↑ {copy.tokens_salida}↓ tokens ({time.monotonic()-t0:.1f}s)")
        print(f"\n{copy}")

    # ── Etapa 2: Renderizar template premium ──────────────────────────────────
    _sep("2 · RENDERIZANDO TEMPLATE PREMIUM")
    from trendia.landing.templates import renderizar_premium
    landing = renderizar_premium(
        copy,
        imagen_url=args.imagen_url,
        product_handle=PRODUCT_HANDLE,
        stock=args.stock,
        viendo=args.viendo,
    )
    _ok(f"HTML generado — {len(landing.html):,} caracteres")
    print(f"  Secciones: hero · urgencia · beneficios · antes/ahora · releasit · testimonios · footer")

    if args.dry_run:
        _sep()
        print("  [dry-run] Publicación omitida.")
        print(f"  Preview HTML (500 chars):\n  {landing.html[:500]}…")
        return 0

    # ── Etapa 3: Publicar en Shopify ──────────────────────────────────────────
    _sep("3 · PUBLICANDO EN SHOPIFY")
    t0 = time.monotonic()
    from trendia.landing.shopify import publicar
    try:
        page = publicar(copy, landing)  # type: ignore[arg-type]  — duck typing OK
    except EnvironmentError as exc:
        _err(str(exc))
        print("  Configura SHOPIFY_STORE_URL, SHOPIFY_CLIENT_ID y SHOPIFY_CLIENT_SECRET en .env")
        return 1
    except Exception as exc:
        _err(f"Shopify falló: {exc}")
        return 1

    _ok(f"Página publicada en {time.monotonic()-t0:.1f}s")
    _sep()
    print(f"\n  URL pública:  {page.url}")
    print(f"  Admin:        {page.admin_url}")
    print(f"  Page ID:      {page.id}")
    print(f"  Handle:       {page.handle}")
    _sep()

    return 0


if __name__ == "__main__":
    sys.exit(main())
