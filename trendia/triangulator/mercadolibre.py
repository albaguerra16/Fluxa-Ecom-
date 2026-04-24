"""MercadoLibre Colombia — catálogo vía /products/search.

Accesible desde Cloud/datacenter con token. Retorna métricas de mercado
(tamaño de catálogo, marcas únicas, dominios de categoría) en lugar de
precios por ítem, que requieren /sites/MCO/search desde IP no-datacenter.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import httpx
from decouple import config
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

_BASE = "https://api.mercadolibre.com"
_SEARCH_LIMIT = 50


def _auth_headers() -> dict[str, str]:
    token = config("MELI_ACCESS_TOKEN", default="")
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Trendia/1.0)", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


@retry(
    retry=retry_if_exception_type(httpx.HTTPStatusError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _get(url: str, params: dict | None = None) -> dict:
    with httpx.Client(timeout=15, follow_redirects=True) as client:
        resp = client.get(url, params=params, headers=_auth_headers())
        resp.raise_for_status()
        return resp.json()


def _paginar(keyword: str, max_items: int = 100) -> tuple[list[dict], int]:
    """Retorna (items_analizados, total_en_catalogo)."""
    items: list[dict] = []
    offset = 0
    total_catalogo = 0
    while len(items) < max_items:
        data = _get(
            f"{_BASE}/products/search",
            params={"site_id": "MCO", "q": keyword, "limit": _SEARCH_LIMIT, "offset": offset},
        )
        if not total_catalogo:
            total_catalogo = data.get("paging", {}).get("total", 0)
        results = data.get("results", [])
        if not results:
            break
        items.extend(results)
        offset += _SEARCH_LIMIT
        if offset >= min(total_catalogo, max_items):
            break
        time.sleep(0.3)
    return items, total_catalogo


@dataclass
class MLResultado:
    keyword: str
    total_productos: int              # total en catálogo (proxy de tamaño de mercado)
    num_marcas: int                   # marcas únicas (proxy de competencia)
    dominios: list[str] = field(default_factory=list)  # categorías ML (MCO-BODY_SHAPERS…)

    def __str__(self) -> str:
        return (
            f"MLResultado(keyword='{self.keyword}', "
            f"total_catalogo={self.total_productos:,}, "
            f"marcas_unicas={self.num_marcas}, "
            f"dominios={self.dominios[:3]})"
        )


def buscar(keyword: str, max_items: int = 100) -> MLResultado:
    """
    Busca en el catálogo ML Colombia y extrae métricas de mercado.

    Args:
        keyword:   Término de búsqueda.
        max_items: Items a analizar para extraer marcas/dominios (máx 100).

    Returns:
        MLResultado con total_productos, num_marcas y dominios.
    """
    items, total = _paginar(keyword, max_items)

    if not items:
        return MLResultado(keyword=keyword, total_productos=0, num_marcas=0)

    marcas: set[str] = set()
    dominios: set[str] = set()

    for item in items:
        if domain := item.get("domain_id"):
            dominios.add(domain)
        for attr in item.get("attributes", []):
            if attr.get("id") == "BRAND" and (brand := attr.get("value_name")):
                marcas.add(brand.upper())

    return MLResultado(
        keyword=keyword,
        total_productos=total,
        num_marcas=len(marcas),
        dominios=sorted(dominios),
    )
