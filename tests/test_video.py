"""Tests del módulo video — mockea fal_client.subscribe_async."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from trendia.landing.generator import LandingCopy
from trendia.video.fal_client import Angulo, VideoJob, generar_video_async
from trendia.video.variations import (
    LoteVideos,
    _angulos_para_n,
    _construir_prompt,
    generar_variaciones,
    generar_variaciones_async,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

def _copy(**kwargs) -> LandingCopy:
    defaults = dict(
        keyword="faja colombiana",
        headline="Moldea tu figura sin pagar por adelantado",
        subheadline="Recíbela y paga solo si te encanta",
        bullets=["🔥 Reduce 3 tallas desde el primer uso", "💪 Transpirable todo el día"],
        cta_principal="Pedir ahora — pago al recibir",
        cta_secundario="¡Solo quedan 8 unidades!",
        garantia="Si no te gusta, la devuelves sin costo",
        badge_cod="Pago al recibir",
    )
    defaults.update(kwargs)
    return LandingCopy(**defaults)


def _fal_result(url: str = "https://fal.media/files/test/video.mp4") -> dict:
    return {"video": {"url": url}, "request_id": "req_abc123"}


# ── Tests VideoJob ────────────────────────────────────────────────────────────

class TestVideoJob:
    def test_exitoso_con_url(self):
        job = VideoJob(Angulo.DEMOSTRACION, "prompt", video_url="https://cdn.fal.ai/video.mp4")
        assert job.exitoso is True

    def test_no_exitoso_sin_url(self):
        job = VideoJob(Angulo.DEMOSTRACION, "prompt")
        assert job.exitoso is False

    def test_no_exitoso_con_error(self):
        job = VideoJob(Angulo.DEMOSTRACION, "prompt", video_url="https://url.com", error="timeout")
        assert job.exitoso is False

    def test_str_exitoso(self):
        job = VideoJob(Angulo.TESTIMONIAL, "prompt test", video_url="https://fal.ai/v.mp4")
        assert "testimonial" in str(job)
        assert "✅" in str(job)

    def test_str_fallido(self):
        job = VideoJob(Angulo.URGENCIA, "prompt", error="Timeout")
        assert "❌" in str(job)
        assert "Timeout" in str(job)


# ── Tests generar_video_async ─────────────────────────────────────────────────

class TestGenerarVideoAsync:
    def _run(self, fal_result=None, raises=None, fal_key="test_key"):
        async def _inner():
            with patch("trendia.video.fal_client.config", return_value=fal_key), \
                 patch("trendia.video.fal_client.fal_client.subscribe_async",
                        new_callable=AsyncMock,
                        return_value=fal_result or _fal_result()) as mock_sub:
                job = await generar_video_async("test prompt", Angulo.DEMOSTRACION)
                return job, mock_sub

        if raises:
            with patch("trendia.video.fal_client.config", return_value=fal_key), \
                 patch("trendia.video.fal_client.fal_client.subscribe_async",
                        new_callable=AsyncMock, side_effect=raises):
                return asyncio.run(generar_video_async("test prompt", Angulo.DEMOSTRACION)), None

        return asyncio.run(_inner())

    def test_retorna_video_job(self):
        job, _ = self._run()
        assert isinstance(job, VideoJob)

    def test_url_extraida_correctamente(self):
        job, _ = self._run(fal_result=_fal_result("https://cdn.fal.ai/out.mp4"))
        assert job.video_url == "https://cdn.fal.ai/out.mp4"

    def test_request_id_registrado(self):
        job, _ = self._run()
        assert job.request_id == "req_abc123"

    def test_angulo_preservado(self):
        async def _inner():
            with patch("trendia.video.fal_client.config", return_value="k"), \
                 patch("trendia.video.fal_client.fal_client.subscribe_async",
                        new_callable=AsyncMock, return_value=_fal_result()):
                return await generar_video_async("p", Angulo.TESTIMONIAL)
        job = asyncio.run(_inner())
        assert job.angulo == Angulo.TESTIMONIAL

    def test_resultado_vacio_registra_error(self):
        job, _ = self._run(fal_result={"video": {}})
        assert not job.exitoso
        assert job.error

    def test_sin_fal_key_lanza_error(self):
        with pytest.raises(EnvironmentError, match="FAL_KEY"):
            self._run(fal_key="")

    def test_timeout_registra_error(self):
        job = self._run(raises=asyncio.TimeoutError())
        if isinstance(job, tuple):
            job = job[0]
        assert not job.exitoso
        assert "Timeout" in job.error or "timeout" in job.error.lower()

    def test_fal_error_registra_error(self):
        import fal_client as fc
        job = self._run(raises=fc.FalClientError("API error"))
        if isinstance(job, tuple):
            job = job[0]
        assert not job.exitoso
        assert "fal.ai" in job.error


# ── Tests _construir_prompt ───────────────────────────────────────────────────

class TestConstruirPrompt:
    def test_contiene_keyword(self):
        p = _construir_prompt(_copy(), Angulo.DEMOSTRACION)
        assert "faja colombiana" in p

    def test_testimonial_contiene_cta(self):
        p = _construir_prompt(_copy(), Angulo.TESTIMONIAL)
        assert "pago al recibir" in p.lower()

    def test_urgencia_contiene_stock(self):
        p = _construir_prompt(_copy(), Angulo.URGENCIA, stock=5)
        assert "5" in p

    def test_demostracion_contiene_headline(self):
        p = _construir_prompt(_copy(), Angulo.DEMOSTRACION)
        assert "Moldea tu figura" in p

    def test_todos_los_angulos_generan_prompt(self):
        for angulo in Angulo:
            p = _construir_prompt(_copy(), angulo)
            assert len(p) > 50


# ── Tests _angulos_para_n ─────────────────────────────────────────────────────

class TestAngulosParaN:
    def test_n1_es_testimonial(self):
        assert _angulos_para_n(1) == [Angulo.TESTIMONIAL]

    def test_n3_tiene_todos(self):
        angulos = _angulos_para_n(3)
        assert set(angulos) == {Angulo.TESTIMONIAL, Angulo.DEMOSTRACION, Angulo.URGENCIA}

    def test_n5_cicla(self):
        angulos = _angulos_para_n(5)
        assert len(angulos) == 5
        assert angulos[3] == Angulo.TESTIMONIAL  # ciclo vuelve a empezar

    def test_n0_lista_vacia(self):
        assert _angulos_para_n(0) == []


# ── Tests generar_variaciones ─────────────────────────────────────────────────

class TestGenerarVariaciones:
    def _patch_generar(self, n: int = 3, urls: list[str] | None = None):
        urls = urls or [f"https://fal.ai/video_{i}.mp4" for i in range(n)]

        async def _fake_generar(prompt, angulo, **_kwargs):
            idx = list(Angulo).index(angulo) % len(urls)
            return VideoJob(angulo, prompt, video_url=urls[idx])

        with patch("trendia.video.variations.generar_video_async", side_effect=_fake_generar), \
             patch("trendia.video.variations.config", return_value=n):
            return generar_variaciones(_copy(), n=n)

    def test_retorna_lote_videos(self):
        lote = self._patch_generar(3)
        assert isinstance(lote, LoteVideos)

    def test_n_jobs_creados(self):
        lote = self._patch_generar(3)
        assert len(lote.jobs) == 3

    def test_todos_exitosos(self):
        lote = self._patch_generar(3)
        assert len(lote.exitosos) == 3
        assert len(lote.fallidos) == 0

    def test_keyword_en_lote(self):
        lote = self._patch_generar(2)
        assert lote.keyword == "faja colombiana"

    def test_str_lote(self):
        lote = self._patch_generar(2)
        out = str(lote)
        assert "faja colombiana" in out
        assert "2/2" in out

    def test_n1_variacion(self):
        lote = self._patch_generar(1)
        assert len(lote.jobs) == 1

    def test_exitosos_y_fallidos_separados(self):
        async def _fake(prompt, angulo, **_kw):
            if angulo == Angulo.URGENCIA:
                return VideoJob(angulo, prompt, error="timeout")
            return VideoJob(angulo, prompt, video_url="https://fal.ai/ok.mp4")

        with patch("trendia.video.variations.generar_video_async", side_effect=_fake):
            lote = asyncio.run(generar_variaciones_async(_copy(), n=3))

        assert len(lote.exitosos) == 2
        assert len(lote.fallidos) == 1
