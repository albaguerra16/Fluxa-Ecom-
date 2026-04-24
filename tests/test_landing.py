"""Tests de generator.py, templates.py y shopify.py."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from trendia.landing.generator import LandingCopy, _build_user_prompt, _parse_json, generar_copy

# ── Fixture de respuesta Claude ───────────────────────────────────────────────

_COPY_VALIDO = {
    "headline": "Moldea tu figura sin pagar un peso por adelantado",
    "subheadline": "Recíbela en casa y paga solo si te encanta — Contra Entrega garantizado",
    "bullets": [
        "🔥 Reduce hasta 3 tallas visualmente desde el primer uso",
        "💪 Material transpirable que se adapta a tu cuerpo todo el día",
        "📦 Llega a tu puerta en 2-5 días hábiles a cualquier ciudad de Colombia",
        "✅ Pago Contra Entrega — no necesitas tarjeta ni datos bancarios",
        "🔄 Cambio gratis si no queda perfecta",
    ],
    "cta_principal": "Pedir ahora — pago al recibir",
    "cta_secundario": "¡Solo quedan 8 unidades disponibles hoy!",
    "garantia": "Si no te gusta, la devuelves sin costo y sin preguntas",
    "badge_cod": "Pago al recibir",
}


def _mock_response(data: dict, cache_hit: bool = False) -> MagicMock:
    usage = SimpleNamespace(
        input_tokens=850,
        output_tokens=312,
        cache_read_input_tokens=700 if cache_hit else 0,
        cache_creation_input_tokens=0 if cache_hit else 700,
    )
    content = SimpleNamespace(text=json.dumps(data))
    resp = MagicMock()
    resp.content = [content]
    resp.usage = usage
    return resp


# ── Tests _parse_json ─────────────────────────────────────────────────────────

class TestParseJson:
    def test_json_limpio(self):
        raw = json.dumps(_COPY_VALIDO)
        result = _parse_json(raw)
        assert result["headline"] == _COPY_VALIDO["headline"]

    def test_json_con_texto_alrededor(self):
        raw = f"Aquí está el copy:\n```json\n{json.dumps(_COPY_VALIDO)}\n```"
        result = _parse_json(raw)
        assert "headline" in result

    def test_sin_json_lanza_error(self):
        with pytest.raises(ValueError, match="No se encontró JSON"):
            _parse_json("Lo siento, no puedo generar ese contenido.")


# ── Tests _build_user_prompt ──────────────────────────────────────────────────

class TestBuildUserPrompt:
    def test_contiene_keyword(self):
        p = _build_user_prompt("faja colombiana", 63.8, ["MCO-BODY_SHAPERS"], "")
        assert "faja colombiana" in p

    def test_nivel_alto(self):
        p = _build_user_prompt("producto", 75.0, [], "")
        assert "alta demanda" in p

    def test_nivel_medio(self):
        p = _build_user_prompt("producto", 55.0, [], "")
        assert "demanda media" in p

    def test_nivel_nicho(self):
        p = _build_user_prompt("producto", 30.0, [], "")
        assert "nicho" in p

    def test_dominio_formateado(self):
        p = _build_user_prompt("producto", 50.0, ["MCO-BODY_SHAPERS"], "")
        assert "Body Shapers" in p

    def test_contexto_extra_incluido(self):
        p = _build_user_prompt("producto", 50.0, [], "Precio objetivo: $89.900")
        assert "Precio objetivo" in p


# ── Tests generar_copy ────────────────────────────────────────────────────────

class TestGenerarCopy:
    def _patch_and_run(self, data=None, cache_hit=False, api_key="sk-test"):
        data = data or _COPY_VALIDO
        mock_resp = _mock_response(data, cache_hit)
        with patch("trendia.landing.generator.config", return_value=api_key), \
             patch("trendia.landing.generator.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = mock_resp
            return generar_copy(
                keyword="faja colombiana",
                score=63.8,
                dominios=["MCO-BODY_SHAPERS"],
            )

    def test_retorna_landing_copy(self):
        result = self._patch_and_run()
        assert isinstance(result, LandingCopy)

    def test_campos_correctos(self):
        result = self._patch_and_run()
        assert result.headline == _COPY_VALIDO["headline"]
        assert result.badge_cod == _COPY_VALIDO["badge_cod"]
        assert len(result.bullets) == 5

    def test_detecta_cache_hit(self):
        result = self._patch_and_run(cache_hit=True)
        assert result.cache_hit is True

    def test_detecta_cache_miss(self):
        result = self._patch_and_run(cache_hit=False)
        assert result.cache_hit is False

    def test_tokens_registrados(self):
        result = self._patch_and_run()
        assert result.tokens_entrada == 850
        assert result.tokens_salida == 312

    def test_sin_api_key_lanza_error(self):
        with patch("trendia.landing.generator.config", return_value=""):
            with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
                generar_copy("faja colombiana")

    def test_campos_faltantes_lanza_error(self):
        datos_incompletos = {k: v for k, v in _COPY_VALIDO.items() if k != "garantia"}
        with pytest.raises(ValueError, match="garantia"):
            self._patch_and_run(data=datos_incompletos)

    def test_bullets_truncados_a_5(self):
        datos = {**_COPY_VALIDO, "bullets": _COPY_VALIDO["bullets"] + ["extra bullet 1", "extra bullet 2"]}
        result = self._patch_and_run(data=datos)
        assert len(result.bullets) == 5

    def test_str_legible(self):
        result = self._patch_and_run(cache_hit=True)
        output = str(result)
        assert "faja colombiana" in output
        assert "Headline" in output
        assert "cache hit" in output.lower()


# ══════════════════════════════════════════════════════════════════════════════
# templates.py
# ══════════════════════════════════════════════════════════════════════════════

from trendia.landing.templates import LandingHTML, renderizar  # noqa: E402


def _make_copy(**kwargs) -> LandingCopy:
    defaults = dict(
        keyword="faja colombiana",
        headline="Moldea tu figura sin pagar por adelantado",
        subheadline="Recíbela y paga solo si te encanta",
        bullets=["🔥 Bullet 1", "💪 Bullet 2", "📦 Bullet 3", "✅ Bullet 4", "🔄 Bullet 5"],
        cta_principal="Pedir ahora — pago al recibir",
        cta_secundario="¡Solo quedan 8 unidades!",
        garantia="Si no te gusta, la devuelves sin costo",
        badge_cod="Pago al recibir",
    )
    defaults.update(kwargs)
    return LandingCopy(**defaults)


class TestRenderizar:
    def test_retorna_landing_html(self):
        result = renderizar(_make_copy())
        assert isinstance(result, LandingHTML)

    def test_html_contiene_headline(self):
        copy = _make_copy()
        result = renderizar(copy)
        assert copy.headline in result.html

    def test_html_contiene_todos_los_bullets(self):
        copy = _make_copy()
        result = renderizar(copy)
        for bullet in copy.bullets:
            assert bullet in result.html

    def test_html_contiene_badge_cod(self):
        copy = _make_copy()
        result = renderizar(copy)
        assert copy.badge_cod.upper() in result.html

    def test_html_contiene_garantia(self):
        copy = _make_copy()
        result = renderizar(copy)
        assert copy.garantia in result.html

    def test_imagen_incluida_si_se_pasa(self):
        result = renderizar(_make_copy(), imagen_url="https://cdn.ejemplo.com/img.jpg")
        assert "https://cdn.ejemplo.com/img.jpg" in result.html

    def test_imagen_omitida_si_no_se_pasa(self):
        result = renderizar(_make_copy(), imagen_url="")
        assert "<img" not in result.html

    def test_html_es_valido_con_comillas_especiales(self):
        copy = _make_copy(headline='Moldea & "transforma" tu figura <hoy>')
        result = renderizar(copy)
        # Jinja2 autoescape escapa HTML — el contenido no puede inyectar tags
        assert "<hoy>" not in result.html
        assert "&lt;hoy&gt;" in result.html

    def test_preview_trunca(self):
        result = renderizar(_make_copy())
        assert len(result.preview(50)) <= 53  # 50 chars + "…"


# ══════════════════════════════════════════════════════════════════════════════
# shopify.py
# ══════════════════════════════════════════════════════════════════════════════

from trendia.landing.shopify import ShopifyPage, _slugify, publicar  # noqa: E402


class TestSlugify:
    def test_basico(self):
        assert _slugify("Faja Colombiana") == "faja-colombiana"

    def test_acentos(self):
        assert _slugify("Cinturón de fuerza") == "cinturon-de-fuerza"

    def test_caracteres_especiales(self):
        assert _slugify("Producto #1 (Colombia)") == "producto-1-colombia"

    def test_espacios_multiples(self):
        assert _slugify("faja   colombiana") == "faja-colombiana"

    def test_trunca_a_100(self):
        largo = "a" * 200
        assert len(_slugify(largo)) <= 100


class TestPublicar:
    def _setup_mocks(self, page_id=12345, existing=False):
        page_resp = {
            "page": {
                "id": page_id,
                "handle": "faja-colombiana",
                "title": "Moldea tu figura",
                "published_at": "2024-01-01T00:00:00",
            }
        }
        copy = _make_copy()
        landing = renderizar(copy)

        existing_data = {"id": page_id, "handle": "faja-colombiana"} if existing else None

        return copy, landing, page_resp, existing_data

    def _run(self, existing=False, post_raises=None):
        copy, landing, page_resp, existing_data = self._setup_mocks(existing=existing)

        with patch("trendia.landing.shopify.config", side_effect=lambda k, default="": {
            "SHOPIFY_STORE_URL": "mitienda.myshopify.com",
            "SHOPIFY_ACCESS_TOKEN": "shpat_test123",
        }.get(k, default)), \
        patch("trendia.landing.shopify._get_by_handle", return_value=existing_data), \
        patch("trendia.landing.shopify._post", return_value=page_resp) as mock_post, \
        patch("trendia.landing.shopify._put", return_value=page_resp) as mock_put:
            result = publicar(copy, landing)
            return result, mock_post, mock_put

    def test_retorna_shopify_page(self):
        result, _, _ = self._run()
        assert isinstance(result, ShopifyPage)

    def test_url_publica_correcta(self):
        result, _, _ = self._run()
        assert result.url == "https://mitienda.myshopify.com/pages/faja-colombiana"

    def test_admin_url_correcta(self):
        result, _, _ = self._run()
        assert "admin/pages/12345" in result.admin_url

    def test_crea_si_no_existe(self):
        _, mock_post, mock_put = self._run(existing=False)
        mock_post.assert_called_once()
        mock_put.assert_not_called()

    def test_actualiza_si_existe(self):
        _, mock_post, mock_put = self._run(existing=True)
        mock_put.assert_called_once()
        mock_post.assert_not_called()

    def test_sin_credenciales_lanza_error(self):
        copy, landing, _, _ = self._setup_mocks()
        with patch("trendia.landing.shopify.config", return_value=""):
            with pytest.raises(EnvironmentError, match="SHOPIFY"):
                publicar(copy, landing)

    def test_str_shopify_page(self):
        result, _, _ = self._run()
        out = str(result)
        assert "faja-colombiana" in out
        assert "Pública" in out
