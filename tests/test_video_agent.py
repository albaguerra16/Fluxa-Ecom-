"""Tests de src/video_agent — mockea fal_client.subscribe_async."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, call, patch

import fal_client
import pytest

from src.video_agent import (
    Angulo,
    Formato,
    LoteVariaciones,
    VariacionVideo,
    VideoAgente,
    _construir_prompt,
    _MODEL_IMAGE_TO_VIDEO,
    _MODEL_TEXT_TO_VIDEO,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

VIDEO_URL = "https://cdn.ejemplo.com/faja.mp4"
VIDEO_RESULTADO = "https://fal.media/files/out/video.mp4"


def _agente(**kwargs) -> VideoAgente:
    defaults = dict(
        keyword="faja colombiana",
        headline="Moldea tu figura sin pagar por adelantado",
        cta_principal="Pedir ahora — pago al recibir",
        cta_secundario="¡Solo quedan 8 unidades!",
        video_original_url=VIDEO_URL,
    )
    defaults.update(kwargs)
    return VideoAgente(**defaults)


def _fal_ok(url: str = VIDEO_RESULTADO) -> dict:
    return {"video": {"url": url}, "request_id": "req_test_123"}


def _mock_subscribe(side_effect=None, return_value=None):
    """Parcha subscribe_async y config(FAL_KEY) para que pasen las validaciones."""
    if side_effect:
        mock = AsyncMock(side_effect=side_effect)
    else:
        mock = AsyncMock(return_value=return_value or _fal_ok())
    return (
        patch("src.video_agent.fal_client.subscribe_async", mock),
        patch("src.video_agent.config", return_value="test_fal_key"),
    )


# ── VariacionVideo ────────────────────────────────────────────────────────────


class TestVariacionVideo:
    def test_exitoso_con_url(self):
        v = VariacionVideo(Angulo.TESTIMONIAL, Formato.REELS, "p", video_url=VIDEO_RESULTADO)
        assert v.exitoso is True

    def test_no_exitoso_sin_url(self):
        v = VariacionVideo(Angulo.DEMOSTRACION, Formato.FEED, "p")
        assert v.exitoso is False

    def test_no_exitoso_si_hay_error(self):
        v = VariacionVideo(Angulo.URGENCIA, Formato.REELS, "p", video_url=VIDEO_RESULTADO, error="timeout")
        assert v.exitoso is False

    def test_str_exitoso_contiene_angulo_y_formato(self):
        v = VariacionVideo(Angulo.TESTIMONIAL, Formato.REELS, "p", video_url=VIDEO_RESULTADO)
        out = str(v)
        assert "testimonial" in out
        assert "REELS" in out
        assert "✅" in out

    def test_str_fallido_muestra_error(self):
        v = VariacionVideo(Angulo.URGENCIA, Formato.FEED, "p", error="API error")
        out = str(v)
        assert "❌" in out
        assert "API error" in out


# ── LoteVariaciones ───────────────────────────────────────────────────────────


class TestLoteVariaciones:
    def _lote(self) -> LoteVariaciones:
        variaciones = [
            VariacionVideo(Angulo.TESTIMONIAL, Formato.REELS, "p", video_url="https://a.mp4"),
            VariacionVideo(Angulo.TESTIMONIAL, Formato.FEED, "p", video_url="https://b.mp4"),
            VariacionVideo(Angulo.DEMOSTRACION, Formato.REELS, "p", video_url="https://c.mp4"),
            VariacionVideo(Angulo.DEMOSTRACION, Formato.FEED, "p", error="timeout"),
            VariacionVideo(Angulo.URGENCIA, Formato.REELS, "p", video_url="https://d.mp4"),
            VariacionVideo(Angulo.URGENCIA, Formato.FEED, "p", video_url="https://e.mp4"),
        ]
        return LoteVariaciones("faja colombiana", VIDEO_URL, variaciones)

    def test_exitosas(self):
        assert len(self._lote().exitosas) == 5

    def test_fallidas(self):
        assert len(self._lote().fallidas) == 1

    def test_por_formato_reels(self):
        reels = self._lote().por_formato(Formato.REELS)
        assert len(reels) == 3
        assert all(v.formato == Formato.REELS for v in reels)

    def test_por_formato_feed(self):
        feed = self._lote().por_formato(Formato.FEED)
        assert len(feed) == 3
        assert all(v.formato == Formato.FEED for v in feed)

    def test_por_angulo(self):
        vs = self._lote().por_angulo(Angulo.TESTIMONIAL)
        assert len(vs) == 2
        assert all(v.angulo == Angulo.TESTIMONIAL for v in vs)

    def test_str_muestra_keyword_y_conteo(self):
        out = str(self._lote())
        assert "faja colombiana" in out
        assert "5/6" in out


# ── _construir_prompt ─────────────────────────────────────────────────────────


class TestConstruirPrompt:
    def _prompt(self, angulo: Angulo, formato: Formato = Formato.REELS, **kw) -> str:
        defaults = dict(
            keyword="faja colombiana",
            headline="Moldea tu figura",
            cta_principal="Pedir ahora",
            cta_secundario="¡Solo 8 quedan!",
            stock=8,
        )
        defaults.update(kw)
        return _construir_prompt(angulo, formato, **defaults)

    def test_contiene_keyword(self):
        assert "faja colombiana" in self._prompt(Angulo.TESTIMONIAL)

    def test_testimonial_contiene_cta(self):
        p = self._prompt(Angulo.TESTIMONIAL, cta_principal="Pedir ya")
        assert "Pedir ya" in p

    def test_demostracion_contiene_headline(self):
        p = self._prompt(Angulo.DEMOSTRACION)
        assert "Moldea tu figura" in p

    def test_urgencia_contiene_stock(self):
        p = self._prompt(Angulo.URGENCIA, stock=5)
        assert "5" in p

    def test_reels_sufijo(self):
        p = self._prompt(Angulo.TESTIMONIAL, formato=Formato.REELS)
        assert "9:16" in p or "Reels" in p

    def test_feed_sufijo(self):
        p = self._prompt(Angulo.TESTIMONIAL, formato=Formato.FEED)
        assert "1:1" in p or "Feed" in p

    def test_todos_los_angulos_generan_prompt_no_vacio(self):
        for angulo in Angulo:
            for fmt in Formato:
                assert len(self._prompt(angulo, fmt)) > 80


# ── VideoAgente.generar() ─────────────────────────────────────────────────────


class TestVideoAgenteGenerar:
    def test_retorna_lote_variaciones(self):
        patch_sub, patch_cfg = _mock_subscribe()
        with patch_sub, patch_cfg:
            lote = _agente().generar()
        assert isinstance(lote, LoteVariaciones)

    def test_genera_6_variaciones_por_defecto(self):
        patch_sub, patch_cfg = _mock_subscribe()
        with patch_sub, patch_cfg:
            lote = _agente().generar()
        assert len(lote.variaciones) == 6  # 3 ángulos × 2 formatos

    def test_genera_3_variaciones_con_un_formato(self):
        patch_sub, patch_cfg = _mock_subscribe()
        with patch_sub, patch_cfg:
            lote = _agente().generar(formatos=[Formato.REELS])
        assert len(lote.variaciones) == 3

    def test_todos_los_angulos_presentes(self):
        patch_sub, patch_cfg = _mock_subscribe()
        with patch_sub, patch_cfg:
            lote = _agente().generar()
        angulos = {v.angulo for v in lote.variaciones}
        assert angulos == set(Angulo)

    def test_ambos_formatos_presentes(self):
        patch_sub, patch_cfg = _mock_subscribe()
        with patch_sub, patch_cfg:
            lote = _agente().generar()
        formatos = {v.formato for v in lote.variaciones}
        assert formatos == {Formato.REELS, Formato.FEED}

    def test_todas_exitosas_happy_path(self):
        patch_sub, patch_cfg = _mock_subscribe()
        with patch_sub, patch_cfg:
            lote = _agente().generar()
        assert len(lote.exitosas) == 6
        assert len(lote.fallidas) == 0

    def test_urls_extraidas_correctamente(self):
        patch_sub, patch_cfg = _mock_subscribe(return_value=_fal_ok(VIDEO_RESULTADO))
        with patch_sub, patch_cfg:
            lote = _agente().generar()
        assert all(v.video_url == VIDEO_RESULTADO for v in lote.exitosas)

    def test_keyword_en_lote(self):
        patch_sub, patch_cfg = _mock_subscribe()
        with patch_sub, patch_cfg:
            lote = _agente().generar()
        assert lote.keyword == "faja colombiana"

    def test_video_original_url_en_lote(self):
        patch_sub, patch_cfg = _mock_subscribe()
        with patch_sub, patch_cfg:
            lote = _agente().generar()
        assert lote.video_original_url == VIDEO_URL

    def test_usa_image_to_video_si_hay_video_url(self):
        mock_sub = AsyncMock(return_value=_fal_ok())
        with patch("src.video_agent.fal_client.subscribe_async", mock_sub), \
             patch("src.video_agent.config", return_value="test_key"):
            _agente(video_original_url=VIDEO_URL).generar()
        calls_models = [c.args[0] for c in mock_sub.call_args_list]
        assert all(m == _MODEL_IMAGE_TO_VIDEO for m in calls_models)

    def test_usa_text_to_video_sin_video_url(self):
        mock_sub = AsyncMock(return_value=_fal_ok())
        with patch("src.video_agent.fal_client.subscribe_async", mock_sub), \
             patch("src.video_agent.config", return_value="test_key"):
            _agente(video_original_url="").generar()
        calls_models = [c.args[0] for c in mock_sub.call_args_list]
        assert all(m == _MODEL_TEXT_TO_VIDEO for m in calls_models)

    def test_image_url_en_argumentos_si_hay_video_url(self):
        mock_sub = AsyncMock(return_value=_fal_ok())
        with patch("src.video_agent.fal_client.subscribe_async", mock_sub), \
             patch("src.video_agent.config", return_value="test_key"):
            _agente(video_original_url=VIDEO_URL).generar()
        for c in mock_sub.call_args_list:
            assert c.kwargs["arguments"]["image_url"] == VIDEO_URL

    def test_sin_image_url_en_argumentos_sin_video(self):
        mock_sub = AsyncMock(return_value=_fal_ok())
        with patch("src.video_agent.fal_client.subscribe_async", mock_sub), \
             patch("src.video_agent.config", return_value="test_key"):
            _agente(video_original_url="").generar()
        for c in mock_sub.call_args_list:
            assert "image_url" not in c.kwargs["arguments"]

    def test_duracion_propagada(self):
        mock_sub = AsyncMock(return_value=_fal_ok())
        with patch("src.video_agent.fal_client.subscribe_async", mock_sub), \
             patch("src.video_agent.config", return_value="test_key"):
            _agente().generar(duracion=10)
        for c in mock_sub.call_args_list:
            assert c.kwargs["arguments"]["duration"] == "10"


# ── Manejo de errores ─────────────────────────────────────────────────────────


class TestVideoAgenteErrores:
    def test_sin_fal_key_lanza_environment_error(self):
        with patch("src.video_agent.config", return_value=""):
            with pytest.raises(EnvironmentError, match="FAL_KEY"):
                _agente().generar()

    def test_timeout_registra_error_sin_propagar(self):
        patch_sub, patch_cfg = _mock_subscribe(side_effect=asyncio.TimeoutError())
        with patch_sub, patch_cfg:
            lote = _agente().generar()
        assert len(lote.fallidas) == 6
        assert all("Timeout" in v.error for v in lote.fallidas)

    def test_fal_error_registra_error_sin_propagar(self):
        patch_sub, patch_cfg = _mock_subscribe(
            side_effect=fal_client.FalClientError("API down")
        )
        with patch_sub, patch_cfg:
            lote = _agente().generar()
        assert len(lote.fallidas) == 6
        assert all("fal.ai error" in v.error for v in lote.fallidas)

    def test_respuesta_sin_url_registra_error(self):
        patch_sub, patch_cfg = _mock_subscribe(return_value={"video": {}})
        with patch_sub, patch_cfg:
            lote = _agente().generar()
        assert len(lote.fallidas) == 6

    def test_fallo_parcial_continua_lote(self):
        """Un ángulo falla; los demás siguen."""
        call_count = 0

        async def _selectivo(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise fal_client.FalClientError("error parcial")
            return _fal_ok()

        with patch("src.video_agent.fal_client.subscribe_async", side_effect=_selectivo), \
             patch("src.video_agent.config", return_value="test_key"):
            lote = _agente().generar()

        assert len(lote.fallidas) == 1
        assert len(lote.exitosas) == 5

    def test_request_id_registrado(self):
        patch_sub, patch_cfg = _mock_subscribe(return_value=_fal_ok())
        with patch_sub, patch_cfg:
            lote = _agente().generar()
        assert all(v.request_id == "req_test_123" for v in lote.exitosas)


# ── VideoAgente.generar_async() ───────────────────────────────────────────────


class TestVideoAgenteAsync:
    async def test_generar_async_retorna_lote(self):
        mock_sub = AsyncMock(return_value=_fal_ok())
        with patch("src.video_agent.fal_client.subscribe_async", mock_sub), \
             patch("src.video_agent.config", return_value="test_key"):
            lote = await _agente().generar_async()
        assert isinstance(lote, LoteVariaciones)
        assert len(lote.variaciones) == 6

    async def test_generar_async_formato_unico(self):
        mock_sub = AsyncMock(return_value=_fal_ok())
        with patch("src.video_agent.fal_client.subscribe_async", mock_sub), \
             patch("src.video_agent.config", return_value="test_key"):
            lote = await _agente().generar_async(formatos=[Formato.FEED])
        assert all(v.formato == Formato.FEED for v in lote.variaciones)
        assert len(lote.variaciones) == 3
