"""Tests del módulo triangulator con mocks — sin dependencia de APIs externas."""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

from trendia.triangulator.mercadolibre import MLResultado, buscar
from trendia.triangulator.scorer import ProductScore, _norm_competencia, _norm_demanda, puntuar
from trendia.triangulator.trends import TrendsResultado, interes_colombia


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _ml_page(total: int = 500) -> dict:
    return {
        "paging": {"total": total, "limit": 50, "offset": 0},
        "results": [
            {
                "id": f"MCO{i}",
                "domain_id": "MCO-BODY_SHAPERS",
                "name": f"Faja {i}",
                "attributes": [{"id": "BRAND", "value_name": f"marca_{i % 5}"}],
            }
            for i in range(3)
        ],
    }


def _trends_df(keyword: str, valores: list[int]) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=len(valores), freq="D")
    return pd.DataFrame({keyword: valores, "isPartial": [False] * len(valores)}, index=idx)


# ── MercadoLibre ──────────────────────────────────────────────────────────────

class TestBuscar:
    def test_metricas_basicas(self):
        with patch("trendia.triangulator.mercadolibre._get", return_value=_ml_page(500)):
            r = buscar("faja colombiana", max_items=50)

        assert isinstance(r, MLResultado)
        assert r.keyword == "faja colombiana"
        assert r.total_productos == 500
        assert r.num_marcas == 3           # marca_0, marca_1, marca_2 (i % 5 con 3 items)
        assert "MCO-BODY_SHAPERS" in r.dominios

    def test_sin_resultados(self):
        with patch("trendia.triangulator.mercadolibre._get", return_value={"paging": {"total": 0}, "results": []}):
            r = buscar("xyz_inexistente")
        assert r.total_productos == 0
        assert r.num_marcas == 0

    def test_str_legible(self):
        r = MLResultado("faja", 500, 10, ["MCO-BODY_SHAPERS"])
        assert "10,000" not in str(r)   # no confundir con 10k
        assert "faja" in str(r)


# ── Google Trends ─────────────────────────────────────────────────────────────

class TestInteresColombia:
    def test_metricas_basicas(self):
        valores = [0] * 85 + [100, 80, 60, 40, 20]
        df = _trends_df("faja colombiana", valores)
        with patch("trendia.triangulator.trends._fetch_trends", return_value=df):
            r = interes_colombia("faja colombiana")

        assert isinstance(r, TrendsResultado)
        assert r.interes_peak == 100
        assert r.semanas_con_datos == 90
        assert r.interes_promedio > 0

    def test_df_vacio_retorna_ceros(self):
        with patch("trendia.triangulator.trends._fetch_trends", return_value=pd.DataFrame()):
            r = interes_colombia("nada")
        assert r.interes_promedio == 0.0
        assert r.interes_peak == 0
        assert r.semanas_con_datos == 0

    def test_excluye_dia_parcial(self):
        idx = pd.date_range("2024-01-01", periods=5, freq="D")
        df = pd.DataFrame(
            {"kw": [10, 20, 30, 40, 50], "isPartial": [False, False, False, False, True]},
            index=idx,
        )
        with patch("trendia.triangulator.trends._fetch_trends", return_value=df):
            r = interes_colombia("kw")
        assert r.semanas_con_datos == 4
        assert r.interes_peak == 40     # excluye el 50 (parcial)

    def test_tendencia_positiva(self):
        df = _trends_df("trend", [10, 20, 30, 40, 50])
        with patch("trendia.triangulator.trends._fetch_trends", return_value=df):
            r = interes_colombia("trend")
        assert r.tendencia > 0

    def test_tendencia_negativa(self):
        df = _trends_df("trend", [50, 40, 30, 20, 10])
        with patch("trendia.triangulator.trends._fetch_trends", return_value=df):
            r = interes_colombia("trend")
        assert r.tendencia < 0


# ── Scorer ────────────────────────────────────────────────────────────────────

class TestNormalizadores:
    def test_demanda_cero(self):
        assert _norm_demanda(0) == 0.0

    def test_demanda_cap(self):
        assert _norm_demanda(5_000) == pytest.approx(100.0)

    def test_demanda_logaritmica(self):
        d100 = _norm_demanda(100)
        d1000 = _norm_demanda(1_000)
        assert 0 < d100 < d1000 < 100

    def test_competencia_sin_marcas(self):
        assert _norm_competencia(0) == 100.0

    def test_competencia_cap(self):
        assert _norm_competencia(150) == 0.0

    def test_competencia_intermedia(self):
        assert 0 < _norm_competencia(75) < 100


class TestPuntuar:
    def _make(self, interes=60, peak=80, tendencia=0.0, total=1000, marcas=30):
        ml = MLResultado("test", total, marcas, ["MCO-BODY_SHAPERS"])
        tr = TrendsResultado("test", interes, peak, tendencia, 90)
        return ml, tr

    def test_retorna_product_score(self):
        ml, tr = self._make()
        r = puntuar(ml, tr)
        assert isinstance(r, ProductScore)
        assert 0 <= r.score <= 100

    def test_producto_alto(self):
        ml, tr = self._make(interes=80, peak=100, tendencia=1.5, total=2000, marcas=10)
        r = puntuar(ml, tr)
        assert r.recomendacion == "ALTO"
        assert r.score >= 70

    def test_producto_descartar(self):
        ml, tr = self._make(interes=0, peak=0, tendencia=-2.0, total=5, marcas=200)
        r = puntuar(ml, tr)
        assert r.recomendacion == "DESCARTAR"
        assert r.score < 30

    def test_bonus_tendencia_positiva(self):
        ml, tr_flat = self._make(tendencia=0.0)
        ml2, tr_up = self._make(tendencia=1.5)
        assert puntuar(ml2, tr_up).score > puntuar(ml, tr_flat).score

    def test_str_legible(self):
        ml, tr = self._make()
        r = puntuar(ml, tr)
        assert "test" in str(r)
        assert "/100" in str(r)
