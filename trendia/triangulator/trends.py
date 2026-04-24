"""Google Trends para Colombia usando pytrends."""

from __future__ import annotations

import time
from dataclasses import dataclass

import pandas as pd
from pytrends.request import TrendReq
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class TrendsResultado:
    keyword: str
    interes_promedio: float   # 0–100 (promedio del periodo, semanas completas)
    interes_peak: int         # valor máximo en el periodo
    tendencia: float          # pendiente lineal: positivo = creciendo, negativo = cayendo
    semanas_con_datos: int

    def __str__(self) -> str:
        direccion = "↑" if self.tendencia > 0.5 else ("↓" if self.tendencia < -0.5 else "→")
        return (
            f"TrendsResultado(keyword='{self.keyword}', "
            f"interes_promedio={self.interes_promedio}, "
            f"peak={self.interes_peak}, "
            f"tendencia={self.tendencia:+.2f} {direccion}, "
            f"semanas={self.semanas_con_datos})"
        )


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=5, max=30))
def _fetch_trends(keyword: str, geo: str, timeframe: str) -> pd.DataFrame:
    pt = TrendReq(hl="es-CO", tz=300, timeout=(10, 25))
    pt.build_payload([keyword], geo=geo, timeframe=timeframe)
    time.sleep(1.5)  # previene 429 en Cloud Shell
    return pt.interest_over_time()


def _calcular_tendencia(serie: pd.Series) -> float:
    """Pendiente de regresión lineal simple normalizada por semana."""
    if len(serie) < 2:
        return 0.0
    x = range(len(serie))
    n = len(serie)
    x_mean = (n - 1) / 2
    y_mean = serie.mean()
    num = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, serie))
    den = sum((xi - x_mean) ** 2 for xi in x)
    return round(num / den, 3) if den else 0.0


def interes_colombia(keyword: str, dias: int = 90, geo: str = "CO") -> TrendsResultado:
    """
    Retorna el interés relativo de un keyword en Colombia (últimos N días).

    Args:
        keyword: Término a consultar.
        dias:    Ventana de tiempo. 90 → 3 meses (resolución semanal).
        geo:     Código ISO del país. Default 'CO'.

    Returns:
        TrendsResultado con interes_promedio (0–100), peak, tendencia y semanas.
    """
    # `today 3-m` con geo='CO' devuelve datos diarios (~90 puntos, datos suficientes).
    # Timeframes > 90 días con geo regional producen ceros por volumen insuficiente.
    meses = max(1, round(dias / 30))
    timeframe = f"today {meses}-m"
    df = _fetch_trends(keyword, geo=geo, timeframe=timeframe)

    if df.empty or keyword not in df.columns:
        return TrendsResultado(
            keyword=keyword,
            interes_promedio=0.0,
            interes_peak=0,
            tendencia=0.0,
            semanas_con_datos=0,
        )

    serie = df[keyword]
    if "isPartial" in df.columns:
        serie = serie[~df["isPartial"].astype(bool)]

    return TrendsResultado(
        keyword=keyword,
        interes_promedio=round(float(serie.mean()), 2),
        interes_peak=int(serie.max()),
        tendencia=_calcular_tendencia(serie),
        semanas_con_datos=len(serie),
    )
