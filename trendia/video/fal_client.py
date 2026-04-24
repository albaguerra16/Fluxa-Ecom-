"""Wrapper sobre fal-client SDK para generación de video con kling-video.

Patrón: submit_async → polling interno vía subscribe_async → resultado con URL.
El modelo kling-video acepta texto en inglés; los prompts se construyen en
variations.py a partir del copy en español.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum

import fal_client
from decouple import config

FAL_MODEL = "fal-ai/kling-video/v1.6/standard/text-to-video"

# Tiempo máximo de espera por video (kling tarda 2-5 min en producción)
_TIMEOUT_SEGUNDOS = 600


class Angulo(Enum):
    TESTIMONIAL = "testimonial"
    DEMOSTRACION = "demostracion"
    URGENCIA = "urgencia"


@dataclass
class VideoJob:
    angulo: Angulo
    prompt: str
    model: str = FAL_MODEL
    video_url: str = ""
    duracion_segundos: int = 5
    aspect_ratio: str = "9:16"  # vertical — optimizado para móvil/Reels/TikTok
    request_id: str = ""
    error: str = ""

    @property
    def exitoso(self) -> bool:
        return bool(self.video_url) and not self.error

    def __str__(self) -> str:
        estado = f"✅ {self.video_url}" if self.exitoso else f"❌ {self.error or 'pendiente'}"
        return (
            f"VideoJob({self.angulo.value} | {self.duracion_segundos}s {self.aspect_ratio})\n"
            f"  Prompt: {self.prompt[:80]}…\n"
            f"  Estado: {estado}"
        )


def _fal_key() -> str:
    key = config("FAL_KEY", default="")
    if not key:
        raise EnvironmentError("FAL_KEY no está configurado en .env")
    return key


def _on_queue_update(update: object) -> None:
    """Callback de progreso — registra posición en cola sin bloquear."""
    if isinstance(update, fal_client.InProgress):
        logs = getattr(update, "logs", [])
        if logs:
            print(f"  [fal.ai] {logs[-1].get('message', '')}")


async def _submit_y_esperar(
    prompt: str,
    angulo: Angulo,
    model: str,
    duracion: int,
    aspect_ratio: str,
) -> VideoJob:
    """Submite un job y espera el resultado de forma asíncrona."""
    fal_client.api_key = _fal_key()  # lanza EnvironmentError antes del try/except

    job = VideoJob(
        angulo=angulo,
        prompt=prompt,
        model=model,
        duracion_segundos=duracion,
        aspect_ratio=aspect_ratio,
    )
    try:

        result = await asyncio.wait_for(
            fal_client.subscribe_async(
                model,
                arguments={
                    "prompt": prompt,
                    "duration": str(duracion),
                    "aspect_ratio": aspect_ratio,
                },
                on_queue_update=_on_queue_update,
            ),
            timeout=_TIMEOUT_SEGUNDOS,
        )

        # El resultado de kling-video tiene forma: {"video": {"url": "..."}}
        video = result.get("video", {})
        job.video_url = video.get("url", "")
        job.request_id = str(result.get("request_id", ""))

        if not job.video_url:
            job.error = f"fal.ai no retornó URL de video. Respuesta: {str(result)[:200]}"

    except asyncio.TimeoutError:
        job.error = f"Timeout después de {_TIMEOUT_SEGUNDOS}s esperando el video"
    except fal_client.FalClientError as exc:
        job.error = f"fal.ai error: {exc}"
    except Exception as exc:  # noqa: BLE001
        job.error = f"Error inesperado: {exc}"

    return job


async def generar_video_async(
    prompt: str,
    angulo: Angulo,
    model: str = FAL_MODEL,
    duracion: int = 5,
    aspect_ratio: str = "9:16",
) -> VideoJob:
    """
    Genera un video con fal.ai de forma asíncrona.

    Args:
        prompt:       Prompt en inglés optimizado para el modelo.
        angulo:       Ángulo narrativo (TESTIMONIAL / DEMOSTRACION / URGENCIA).
        model:        Modelo fal.ai a usar.
        duracion:     Duración en segundos (5 ó 10 para kling-video).
        aspect_ratio: "9:16" (móvil/Reels), "16:9" (landscape), "1:1" (feed).

    Returns:
        VideoJob con video_url si el job fue exitoso, o error string si falló.
    """
    return await _submit_y_esperar(prompt, angulo, model, duracion, aspect_ratio)
