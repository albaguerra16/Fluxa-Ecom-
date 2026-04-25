"""Scorer: combina señales ML + Google Trends + Meta Ads + Marketplace en un puntaje 0-100."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from trendia.triangulator.mercadolibre import MLResultado
from trendia.triangulator.trends import TrendsResultado

# ── Pesos base ────────────────────────────────────────────────────────────────
# Trends pesa más porque refleja intención de compra activa del consumidor.
# Competencia penaliza mercados saturados donde el margen COD se erosiona.
_PESO_TRENDS = 0.55
_PESO_DEMANDA = 0.25
_PESO_COMPETENCIA = 0.20

# ── Umbrales de normalización ─────────────────────────────────────────────────
_DEMANDA_CAP = 5_000    # productos en catálogo que saturan el score de demanda
_MARCAS_CAP = 150       # marcas a partir de las cuales competencia = 0
_BONUS_TENDENCIA = 5.0  # puntos extra si la tendencia semanal es positiva (>0.5)

# ── Ajustes sociales (bonus/penalización sobre score base) ────────────────────
# Meta Ads: sweet spot COD = 5-25 anuncios activos (mercado probado, no saturado).
# Marketplace: cada publicación adicional confirma demanda real.
_META_ADS_SWEET_MIN = 5
_META_ADS_SWEET_MAX = 25
_META_ADS_SATURADO = 60   # umbral de saturación FB

_MKT_DEMANDA_MEDIA = 5    # publicaciones que indican demanda moderada
_MKT_DEMANDA_ALTA = 20    # publicaciones que indican demanda alta


@dataclass
class ProductScore:
    keyword: str
    score: float               # 0–100 (score final con todos los ajustes)
    score_trends: float        # componente tendencia Google (0–100)
    score_demanda: float       # componente demanda ML (0–100)
    score_competencia: float   # componente competencia inversa (0–100)
    recomendacion: str         # ALTO / MEDIO / BAJO / DESCARTAR
    razon: str                 # explicación de los factores dominantes
    # Señales sociales opcionales (0 = sin datos)
    num_meta_ads: int = 0
    num_marketplace: int = 0
    ajuste_social: float = 0.0  # suma de bonus/penalización sociales

    def __str__(self) -> str:
        base = (
            f"ProductScore('{self.keyword}': {self.score:.1f}/100 → {self.recomendacion}\n"
            f"  trends={self.score_trends:.0f}  demanda={self.score_demanda:.0f}  "
            f"competencia={self.score_competencia:.0f}"
        )
        if self.num_meta_ads > 0 or self.num_marketplace > 0:
            ajuste_str = f"{self.ajuste_social:+.1f}" if self.ajuste_social else "0"
            base += (
                f"  ajuste_social={ajuste_str}\n"
                f"  meta_ads={self.num_meta_ads}  marketplace={self.num_marketplace}"
            )
        base += f"\n  {self.razon})"
        return base


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


def _ajuste_meta_ads(num_anuncios: int) -> float:
    """
    Bonus/penalización por competencia en Meta Ads Colombia.

    Para COD: tener anuncios activos confirma que el producto convierte en FB.
    Demasiados anuncios = CPM alto, margen reducido.
      0       → sin señal (neutral)
      1–4     → +2  (poca prueba pero no saturado)
      5–25    → +5  (sweet spot: mercado probado, no saturado)
      26–60   → 0   (competitivo, viable)
      61+     → -5  (mercado saturado, CPM alto)
    """
    if num_anuncios == 0:
        return 0.0
    if num_anuncios <= 4:
        return +2.0
    if num_anuncios <= _META_ADS_SWEET_MAX:
        return +5.0
    if num_anuncios <= _META_ADS_SATURADO:
        return 0.0
    return -5.0


def _ajuste_marketplace(num_publicaciones: int) -> float:
    """
    Bonus por demanda comprobada en Marketplace Colombia.

    Publicaciones activas = gente buscando/vendiendo el producto = demanda real.
      0     → sin señal (neutral)
      1–4   → +1
      5–19  → +2
      20+   → +3
    """
    if num_publicaciones == 0:
        return 0.0
    if num_publicaciones < _MKT_DEMANDA_MEDIA:
        return +1.0
    if num_publicaciones < _MKT_DEMANDA_ALTA:
        return +2.0
    return +3.0


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
    num_meta_ads: int,
    num_marketplace: int,
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

    if num_meta_ads > _META_ADS_SWEET_MAX:
        partes.append(f"saturado en Meta Ads ({num_meta_ads} anuncios)")
    elif _META_ADS_SWEET_MIN <= num_meta_ads <= _META_ADS_SWEET_MAX:
        partes.append(f"sweet spot Meta Ads ({num_meta_ads} anuncios)")
    elif 0 < num_meta_ads < _META_ADS_SWEET_MIN:
        partes.append(f"poca competencia en FB ({num_meta_ads} anuncios)")

    if num_marketplace >= _MKT_DEMANDA_ALTA:
        partes.append(f"alta demanda Marketplace ({num_marketplace} publicaciones)")
    elif num_marketplace >= _MKT_DEMANDA_MEDIA:
        partes.append(f"demanda Marketplace ({num_marketplace} publicaciones)")

    return " · ".join(partes) if partes else "señales mixtas"


# ── Función pública ───────────────────────────────────────────────────────────

def puntuar(
    ml: MLResultado,
    trends: TrendsResultado,
    meta_ads: object | None = None,
    marketplace: object | None = None,
) -> ProductScore:
    """
    Puntúa un producto para dropshipping COD Colombia en 0-100.

    Lógica:
        - Trends (55%): intención de compra activa del consumidor colombiano.
        - Demanda ML (25%): tamaño del catálogo como proxy de mercado probado.
        - Competencia inversa (20%): menos marcas = más oportunidad de entrada.
        - Bonus +5 si la tendencia semanal es positiva (momentum).
        - Ajuste ±5 según señales sociales de Meta Ads y Marketplace (opcional).

    Args:
        ml:          Resultado de mercadolibre.buscar().
        trends:      Resultado de trends.interes_colombia().
        meta_ads:    MetaAdsResultado opcional (num_anuncios).
        marketplace: MarketplaceResultado opcional (num_publicaciones).

    Returns:
        ProductScore con score, componentes, ajuste social, recomendación y razón.
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

    # Señales sociales opcionales (duck-typing — evita imports circulares)
    num_ads = int(getattr(meta_ads, "num_anuncios", 0) or 0)
    num_mkt = int(getattr(marketplace, "num_publicaciones", 0) or 0)

    ajuste_social = _ajuste_meta_ads(num_ads) + _ajuste_marketplace(num_mkt)
    score += ajuste_social

    score = round(min(100.0, max(0.0, score)), 2)

    return ProductScore(
        keyword=ml.keyword,
        score=score,
        score_trends=round(s_trends, 2),
        score_demanda=s_demanda,
        score_competencia=s_competencia,
        recomendacion=_recomendacion(score),
        razon=_razon(s_trends, s_demanda, s_competencia, trends.tendencia, num_ads, num_mkt),
        num_meta_ads=num_ads,
        num_marketplace=num_mkt,
        ajuste_social=round(ajuste_social, 1),
    )
