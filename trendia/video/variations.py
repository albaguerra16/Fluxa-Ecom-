"""Generador de variaciones de video para dropshipping COD Colombia.

Crea N prompts con ángulos narrativos distintos (testimonial, demostración,
urgencia) y los submite en paralelo via asyncio.gather. Cada ángulo apunta
a un momento distinto del funnel COD colombiano:

  TESTIMONIAL  → rompe desconfianza inicial (la persona ya lo probó y lo ama)
  DEMOSTRACION → muestra el producto en acción (responde "¿cómo funciona?")
  URGENCIA     → cierra la venta (stock limitado + Contra Entrega visible)
"""

from __future__ import annotations

import asyncio
import itertools
from dataclasses import dataclass, field

from decouple import config

from trendia.landing.generator import LandingCopy
from trendia.video.fal_client import Angulo, VideoJob, generar_video_async, FAL_MODEL

# ── Plantillas de prompt en inglés ───────────────────────────────────────────
# fal-ai/kling-video responde mejor a prompts en inglés con descriptores
# cinematográficos específicos. Las variables en {} se sustituyen en runtime.

_PLANTILLAS: dict[Angulo, str] = {
    Angulo.TESTIMONIAL: (
        "Authentic testimonial video: happy Colombian woman smiling and showing off "
        "{keyword}, wearing it confidently at home. Natural warm lighting, handheld camera "
        "feel, genuine emotion. She gestures toward the product. "
        "Text overlay at bottom: \"{cta}\". "
        "Vertical 9:16 format, cinematic color grade, lifestyle aesthetic."
    ),
    Angulo.DEMOSTRACION: (
        "Product demonstration video: close-up shots of {keyword} being unboxed and used. "
        "Show key features in action with smooth camera movements. "
        "Clean minimal background, professional lighting. "
        "Split-screen showing before and after effect. "
        "Bold text overlay: \"{headline}\". "
        "Fast-paced editing, vertical mobile format 9:16."
    ),
    Angulo.URGENCIA: (
        "Urgent limited-time offer video for {keyword}. "
        "Bold animated countdown timer, flashing 'Only {stock} left!' warning. "
        "High-energy motion graphics with red and orange color scheme. "
        "Large badge: 'PAGO CONTRA ENTREGA — PAGA AL RECIBIR'. "
        "Text: \"{cta_urgencia}\". "
        "Vertical 9:16 format, high contrast, attention-grabbing."
    ),
}

_STOCK_DEFAULT = 8  # unidades que aparecen en el video de urgencia


# ── Dataclass de resultado del lote ──────────────────────────────────────────

@dataclass
class LoteVideos:
    keyword: str
    jobs: list[VideoJob] = field(default_factory=list)

    @property
    def exitosos(self) -> list[VideoJob]:
        return [j for j in self.jobs if j.exitoso]

    @property
    def fallidos(self) -> list[VideoJob]:
        return [j for j in self.jobs if not j.exitoso]

    def __str__(self) -> str:
        lineas = [f"LoteVideos('{self.keyword}': {len(self.exitosos)}/{len(self.jobs)} exitosos)"]
        for job in self.jobs:
            lineas.append(f"  {job}")
        return "\n".join(lineas)


# ── Construcción de prompts ───────────────────────────────────────────────────

def _construir_prompt(copy: LandingCopy, angulo: Angulo, stock: int = _STOCK_DEFAULT) -> str:
    """Rellena la plantilla del ángulo con los datos del copy."""
    beneficio = copy.bullets[0].split(" ", 1)[-1] if copy.bullets else copy.keyword
    return _PLANTILLAS[angulo].format(
        keyword=copy.keyword,
        headline=copy.headline,
        cta=copy.cta_principal,
        cta_urgencia=copy.cta_secundario,
        beneficio=beneficio,
        stock=stock,
    )


def _angulos_para_n(n: int) -> list[Angulo]:
    """Reparte los ángulos disponibles de forma equitativa para N variaciones."""
    ciclo = [Angulo.TESTIMONIAL, Angulo.DEMOSTRACION, Angulo.URGENCIA]
    return list(itertools.islice(itertools.cycle(ciclo), n))


# ── Orquestación async ────────────────────────────────────────────────────────

async def _generar_lote_async(
    copy: LandingCopy,
    n: int,
    model: str,
    duracion: int,
    aspect_ratio: str,
    stock: int,
) -> LoteVideos:
    angulos = _angulos_para_n(n)
    tareas = [
        generar_video_async(
            prompt=_construir_prompt(copy, angulo, stock),
            angulo=angulo,
            model=model,
            duracion=duracion,
            aspect_ratio=aspect_ratio,
        )
        for angulo in angulos
    ]
    jobs: list[VideoJob] = await asyncio.gather(*tareas)
    return LoteVideos(keyword=copy.keyword, jobs=list(jobs))


# ── Funciones públicas ────────────────────────────────────────────────────────

def generar_variaciones(
    copy: LandingCopy,
    n: int | None = None,
    model: str = FAL_MODEL,
    duracion: int = 5,
    aspect_ratio: str = "9:16",
    stock: int = _STOCK_DEFAULT,
) -> LoteVideos:
    """
    Genera N variaciones de video en paralelo para un producto COD Colombia.

    Submite todos los jobs simultáneamente vía asyncio.gather — el tiempo
    total es el del job más lento, no la suma de todos.

    Args:
        copy:         LandingCopy del módulo landing (headline, bullets, ctas).
        n:            Número de variaciones. Default: VIDEO_VARIATIONS del .env (3).
        model:        Modelo fal.ai. Default: kling-video v1.6 standard.
        duracion:     Segundos de video (5 ó 10 para kling).
        aspect_ratio: "9:16" (Reels/TikTok) | "16:9" (YouTube) | "1:1" (feed).
        stock:        Unidades que aparecen en el video de urgencia.

    Returns:
        LoteVideos con todos los VideoJob (exitosos y fallidos).
    """
    if n is None:
        n = config("VIDEO_VARIATIONS", default=3, cast=int)

    return asyncio.run(
        _generar_lote_async(copy, n, model, duracion, aspect_ratio, stock)
    )


async def generar_variaciones_async(
    copy: LandingCopy,
    n: int | None = None,
    model: str = FAL_MODEL,
    duracion: int = 5,
    aspect_ratio: str = "9:16",
    stock: int = _STOCK_DEFAULT,
) -> LoteVideos:
    """Versión async de generar_variaciones — para usar dentro de pipelines async."""
    if n is None:
        n = config("VIDEO_VARIATIONS", default=3, cast=int)
    return await _generar_lote_async(copy, n, model, duracion, aspect_ratio, stock)
