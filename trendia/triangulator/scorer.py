"""Scorer: combina señales ML + Google Trends en un puntaje 0-100 para COD Colombia."""

from __future__ import annotations

import math
from dataclasses import dataclass

from trendia.triangulator.mercadolibre import MLResultado
from trendia.triangulator.trends import TrendsResultado

# ── Pesos ────────────────────────────────────────────────────────────────────
# Trends pesa más porque refleja intención de compra activa del consumidor.
# Competencia penaliza mercados saturados donde el margen COD se erosiona.
_PESO_TRENDS = 0.55
_PESO_DEMANDA = 0.25
_PESO_COMPETENCIA = 0.20

# ── Umbrales de normalización ─────────────────────────────────────────────────
_DEMANDA_CAP = 5_000    # productos en catálogo que saturan el score de demanda
_MARCAS_CAP = 150       # marcas a partir de las cuales competencia = 0
_BONUS_TENDENCIA = 5.0  # puntos extra si la tendencia semanal es positiva (>0.5)


@dataclass
class ProductScore:
    keyword: str
    score: float               # 0–100
    score_trends: float        # componente tendencia Google (0–100)
    score_demanda: float       # componente demanda ML (0–100)
    score_competencia: float   # componente competencia inversa (0–100)
    recomendacion: str         # ALTO / MEDIO / BAJO / DESCARTAR
    razon: str                 # explicación de los factores dominantes

    def __str__(self) -> str:
        return (
            f"ProductScore('{self.keyword}': {self.score:.1f}/100 → {self.recomendacion}\n"
            f"  trends={self.score_trends:.0f}  demanda={self.score_demanda:.0f}  "
            f"competencia={self.score_competencia:.0f}\n"
            f"  {self.razon})"
        )


# ── Normalizadores ────────────────────────────────────────────────────────────

def _norm_demanda(total_productos: int) -> float:
    """
    Escala logarítmica: mercados con pocos productos puntúan bajo (poca demanda),
    mercados enormes saturan en 100.
      0 prod → 0 | 100 → 40 | 1 000 → 70 | 5 000+ → 100
    """
    if total_productos <= 0:
        return 0.0
    return round(
        min(100.0, math.log10(total_productos + 1) / math.log10(_DEMANDA_CAP + 1) * 100),
        2,
    )


def _norm_competencia(num_marcas: int) -> float:
    """
    Inverso lineal: pocas marcas = mercado abierto = score alto.
      0 marcas → 100 | 75 → 50 | 150+ → 0
    """
    if num_marcas <= 0:
        return 100.0
    return round(max(0.0, (1 - num_marcas / _MARCAS_CAP) * 100), 2)


def _recomendacion(score: float) -> str:
    if score >= 70:
        return "ALTO"
    if score >= 50:
        return "MEDIO"
    if score >= 30:
        return "BAJO"
    return "DESCARTAR"


def _razon(
    s_trends: float,
    s_demanda: float,
    s_competencia: float,
    tendencia: float,
) -> str:
    partes: list[str] = []
    if s_trends >= 70:
        partes.append("alta demanda en Google")
    elif s_trends <= 30:
        partes.append("baja búsqueda en Google")

    if s_demanda >= 70:
        partes.append("mercado grande en ML")
    elif s_demanda <= 20:
        partes.append("mercado pequeño en ML")

    if s_competencia >= 70:
        partes.append("poca competencia")
    elif s_competencia <= 30:
        partes.append("mercado saturado")

    if tendencia > 0.5:
        partes.append("tendencia creciente ↑")
    elif tendencia < -0.5:
        partes.append("tendencia decreciente ↓")

    return " · ".join(partes) if partes else "señales mixtas"


# ── Función pública ───────────────────────────────────────────────────────────

def puntuar(ml: MLResultado, trends: TrendsResultado) -> ProductScore:
    """
    Puntúa un producto para dropshipping COD Colombia en 0-100.

    Lógica:
        - Trends (55%): intención de compra activa del consumidor colombiano.
        - Demanda ML (25%): tamaño del catálogo como proxy de mercado probado.
        - Competencia inversa (20%): menos marcas = más oportunidad de entrada.
        - Bonus +5 si la tendencia semanal es positiva (momentum).

    Args:
        ml:     Resultado de mercadolibre.buscar().
        trends: Resultado de trends.interes_colombia().

    Returns:
        ProductScore con score, componentes, recomendación y razón.
    """
    # Con datos diarios por geo='CO', el promedio es muy bajo aunque haya picos altos.
    # Usamos: 40% del peak + 60% del promedio → captura tanto demanda sostenida como viral.
    s_trends = round(trends.interes_promedio * 0.6 + trends.interes_peak * 0.4, 2)
    s_demanda = _norm_demanda(ml.total_productos)
    s_competencia = _norm_competencia(ml.num_marcas)

    score = (
        s_trends * _PESO_TRENDS
        + s_demanda * _PESO_DEMANDA
        + s_competencia * _PESO_COMPETENCIA
    )

    # Bonus de momentum: producto en ascenso tiene ventaja para COD
    if trends.tendencia > 0.5:
        score += _BONUS_TENDENCIA

    score = round(min(100.0, max(0.0, score)), 2)

    return ProductScore(
        keyword=ml.keyword,
        score=score,
        score_trends=round(s_trends, 2),
        score_demanda=s_demanda,
        score_competencia=s_competencia,
        recomendacion=_recomendacion(score),
        razon=_razon(s_trends, s_demanda, s_competencia, trends.tendencia),
    )
