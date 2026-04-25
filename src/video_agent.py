"""Agente de variaciones de video para ads COD Colombia.

Toma un video/imagen de referencia del producto y genera 3 variaciones
narrativas en paralelo vía fal.ai (kling-video).

Ángulos del funnel COD colombiano:
  TESTIMONIAL  → rompe la desconfianza (persona real, experiencia auténtica)
  DEMOSTRACION → muestra el producto en acción (beneficios tangibles)
  URGENCIA     → cierra la venta (stock limitado + badge Contra Entrega)

Formatos de salida:
  REELS → 9:16 — Reels, Stories, TikTok
  FEED  → 1:1  — Facebook Feed, Instagram Feed

Por defecto genera 3 ángulos × 2 formatos = 6 videos en paralelo.
Si se provee video_original_url, usa image-to-video (referencia visual).
Si no, usa text-to-video sin ancla visual.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

import fal_client
from decouple import config

_MODEL_IMAGE_TO_VIDEO = "fal-ai/kling-video/v1.6/standard/image-to-video"
_MODEL_TEXT_TO_VIDEO = "fal-ai/kling-video/v1.6/standard/text-to-video"
_TIMEOUT = 600
_STOCK_DEFAULT = 8

# ── Enums ─────────────────────────────────────────────────────────────────────


class Angulo(Enum):
    TESTIMONIAL = "testimonial"
    DEMOSTRACION = "demostracion"
    URGENCIA = "urgencia"


class Formato(Enum):
    REELS = "9:16"  # Reels, Stories, TikTok
    FEED = "1:1"    # Facebook Feed, Instagram Feed


# ── Plantillas de prompt ──────────────────────────────────────────────────────
# Kling responde mejor a descriptores cinematográficos en inglés.
# Variables sustituidas en _construir_prompt: keyword, headline, cta,
# cta_urgencia, stock.

_PROMPTS: dict[Angulo, str] = {
    Angulo.TESTIMONIAL: (
        "Authentic lifestyle ad for {keyword}. Happy Colombian woman at home "
        "showing the product with genuine excitement. Natural warm lighting, "
        "handheld camera movement. She smiles and points at the product's benefits. "
        "Text overlay: \"{cta}\". UGC aesthetic, realistic skin tones."
    ),
    Angulo.DEMOSTRACION: (
        "Product demonstration ad for {keyword}. Close-up unboxing and use "
        "sequence showing key features in action. Before state then dramatic "
        "improvement after. Clean neutral background, ring-light quality. "
        "Bold animated headline: \"{headline}\". Fast satisfying cuts, "
        "smooth slow-motion reveals."
    ),
    Angulo.URGENCIA: (
        "Urgency-driven limited offer ad for {keyword}. Animated stock counter "
        "showing 'Solo {stock} unidades!', pulsing red warning badge. "
        "Prominent badge: 'PAGO CONTRA ENTREGA — PAGA AL RECIBIR'. "
        "Bold CTA: \"{cta_urgencia}\". Energetic motion graphics, "
        "high-contrast red and orange palette, countdown feel."
    ),
}

# Sufijo de formato añadido al final de cada prompt
_SUFIJOS_FORMATO: dict[Formato, str] = {
    Formato.REELS: (
        "Vertical 9:16 full-bleed composition, optimized for Reels and Stories."
    ),
    Formato.FEED: (
        "Square 1:1 centered composition, optimized for Facebook Feed."
    ),
}


# ── Dataclasses ───────────────────────────────────────────────────────────────


@dataclass
class VariacionVideo:
    angulo: Angulo
    formato: Formato
    prompt: str
    video_url: str = ""
    request_id: str = ""
    error: str = ""

    @property
    def exitoso(self) -> bool:
        return bool(self.video_url) and not self.error

    def __str__(self) -> str:
        estado = f"✅ {self.video_url}" if self.exitoso else f"❌ {self.error or 'pendiente'}"
        return f"  [{self.angulo.value:12s} | {self.formato.name:5s}] {estado}"


@dataclass
class LoteVariaciones:
    keyword: str
    video_original_url: str
    variaciones: list[VariacionVideo] = field(default_factory=list)

    @property
    def exitosas(self) -> list[VariacionVideo]:
        return [v for v in self.variaciones if v.exitoso]

    @property
    def fallidas(self) -> list[VariacionVideo]:
        return [v for v in self.variaciones if not v.exitoso]

    def por_formato(self, fmt: Formato) -> list[VariacionVideo]:
        return [v for v in self.variaciones if v.formato == fmt]

    def por_angulo(self, angulo: Angulo) -> list[VariacionVideo]:
        return [v for v in self.variaciones if v.angulo == angulo]

    def __str__(self) -> str:
        lines = [
            f"LoteVariaciones '{self.keyword}' "
            f"({len(self.exitosas)}/{len(self.variaciones)} exitosas)"
        ]
        lines.extend(str(v) for v in self.variaciones)
        return "\n".join(lines)


# ── Helpers internos ──────────────────────────────────────────────────────────


def _fal_key() -> str:
    key = config("FAL_KEY", default="")
    if not key:
        raise EnvironmentError("FAL_KEY no está configurado en .env")
    return key


def _construir_prompt(
    angulo: Angulo,
    formato: Formato,
    keyword: str,
    headline: str,
    cta_principal: str,
    cta_secundario: str,
    stock: int,
) -> str:
    """Combina plantilla del ángulo + sufijo de formato con los datos del producto."""
    base = _PROMPTS[angulo].format(
        keyword=keyword,
        headline=headline,
        cta=cta_principal,
        cta_urgencia=cta_secundario,
        stock=stock,
    )
    return f"{base} {_SUFIJOS_FORMATO[formato]}"


def _on_queue_update(update: object) -> None:
    if isinstance(update, fal_client.InProgress):
        logs = getattr(update, "logs", [])
        if logs:
            print(f"  [fal.ai] {logs[-1].get('message', '')}")


async def _generar_variacion(
    angulo: Angulo,
    formato: Formato,
    prompt: str,
    video_original_url: str,
    duracion: int,
) -> VariacionVideo:
    """Submite un job de generación de video y espera el resultado."""
    # _fal_key() lanza EnvironmentError antes del try/except para que no
    # quede silenciado dentro de job.error
    fal_client.api_key = _fal_key()

    variacion = VariacionVideo(angulo=angulo, formato=formato, prompt=prompt)
    model = _MODEL_IMAGE_TO_VIDEO if video_original_url else _MODEL_TEXT_TO_VIDEO

    arguments: dict = {
        "prompt": prompt,
        "duration": str(duracion),
        "aspect_ratio": formato.value,
    }
    if video_original_url:
        arguments["image_url"] = video_original_url

    try:
        result = await asyncio.wait_for(
            fal_client.subscribe_async(
                model,
                arguments=arguments,
                on_queue_update=_on_queue_update,
            ),
            timeout=_TIMEOUT,
        )
        video = result.get("video", {})
        variacion.video_url = video.get("url", "")
        variacion.request_id = str(result.get("request_id", ""))

        if not variacion.video_url:
            variacion.error = f"fal.ai no retornó URL. Respuesta: {str(result)[:200]}"

    except asyncio.TimeoutError:
        variacion.error = f"Timeout después de {_TIMEOUT}s"
    except fal_client.FalClientError as exc:
        variacion.error = f"fal.ai error: {exc}"
    except Exception as exc:  # noqa: BLE001
        variacion.error = f"Error inesperado: {exc}"

    return variacion


# ── Clase pública ─────────────────────────────────────────────────────────────


class VideoAgente:
    """Genera variaciones de video del producto para ads COD Colombia.

    Args:
        keyword:            Nombre del producto (ej. 'faja colombiana').
        headline:           Título principal del copy.
        cta_principal:      CTA principal (ej. 'Pedir ahora — pago al recibir').
        cta_secundario:     CTA de urgencia (ej. '¡Solo quedan 8 unidades!').
        video_original_url: URL del video o imagen de referencia del producto.
                            Si se omite, genera sin referencia visual (text-to-video).
        stock:              Unidades visibles en el ángulo de urgencia.
    """

    def __init__(
        self,
        keyword: str,
        headline: str,
        cta_principal: str,
        cta_secundario: str,
        video_original_url: str = "",
        stock: int = _STOCK_DEFAULT,
    ) -> None:
        self.keyword = keyword
        self.headline = headline
        self.cta_principal = cta_principal
        self.cta_secundario = cta_secundario
        self.video_original_url = video_original_url
        self.stock = stock

    def generar(
        self,
        formatos: Sequence[Formato] | None = None,
        duracion: int = 5,
    ) -> LoteVariaciones:
        """Genera 3 ángulos × N formatos en paralelo.

        Por defecto: REELS (9:16) + FEED (1:1) → 6 videos.
        El tiempo total es el del job más lento, no la suma.

        Args:
            formatos: Formatos a generar. Default: [Formato.REELS, Formato.FEED].
            duracion: Segundos de video (5 ó 10 para kling-video).

        Returns:
            LoteVariaciones con todas las variaciones (exitosas y fallidas).

        Raises:
            EnvironmentError: Si FAL_KEY no está configurado en .env.
        """
        if formatos is None:
            formatos = [Formato.REELS, Formato.FEED]
        return asyncio.run(self._generar_async(list(formatos), duracion))

    async def generar_async(
        self,
        formatos: Sequence[Formato] | None = None,
        duracion: int = 5,
    ) -> LoteVariaciones:
        """Versión async de generar() — para usar dentro de pipelines async."""
        if formatos is None:
            formatos = [Formato.REELS, Formato.FEED]
        return await self._generar_async(list(formatos), duracion)

    async def _generar_async(
        self,
        formatos: list[Formato],
        duracion: int,
    ) -> LoteVariaciones:
        tareas = [
            _generar_variacion(
                angulo=angulo,
                formato=fmt,
                prompt=_construir_prompt(
                    angulo,
                    fmt,
                    self.keyword,
                    self.headline,
                    self.cta_principal,
                    self.cta_secundario,
                    self.stock,
                ),
                video_original_url=self.video_original_url,
                duracion=duracion,
            )
            for angulo in Angulo
            for fmt in formatos
        ]
        variaciones: list[VariacionVideo] = await asyncio.gather(*tareas)
        return LoteVariaciones(
            keyword=self.keyword,
            video_original_url=self.video_original_url,
            variaciones=list(variaciones),
        )
