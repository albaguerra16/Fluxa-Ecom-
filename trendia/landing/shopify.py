"""Cliente Shopify Admin REST API para publicar landing pages COD.

Rate limiting: Shopify usa un bucket de 40 créditos/segundo (REST).
Cada POST /pages.json cuesta ~2 créditos. Implementamos un rate limiter
conservador de 2 req/s para operar lejos del límite y soportar carga concurrente
de otras partes de la app usando la misma key.
"""

from __future__ import annotations

import re
import threading
import time
import unicodedata
from dataclasses import dataclass

import httpx
from decouple import config
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from trendia.landing.generator import LandingCopy
from trendia.landing.templates import LandingHTML

_API_VERSION = "2024-04"
_MIN_INTERVAL = 0.5  # segundos entre requests → 2 req/s


# ── Rate limiter ──────────────────────────────────────────────────────────────

class _RateLimiter:
    """Token bucket simple — thread-safe para uso en pipeline paralelo futuro."""

    def __init__(self, min_interval: float = _MIN_INTERVAL) -> None:
        self._min_interval = min_interval
        self._last_call = 0.0
        self._lock = threading.Lock()

    def esperar(self) -> None:
        with self._lock:
            ahora = time.monotonic()
            transcurrido = ahora - self._last_call
            if transcurrido < self._min_interval:
                time.sleep(self._min_interval - transcurrido)
            self._last_call = time.monotonic()


_limiter = _RateLimiter()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    """Convierte un texto a handle URL-safe para Shopify (ej. 'Faja Colombiana' → 'faja-colombiana')."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:100]  # Shopify limita handles a 255 chars; 100 es suficiente


def _base_url(store_url: str) -> str:
    store_url = store_url.rstrip("/")
    if not store_url.startswith("https://"):
        store_url = f"https://{store_url}"
    return f"{store_url}/admin/api/{_API_VERSION}"


def _auth_headers(token: str) -> dict[str, str]:
    return {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# ── Dataclass de resultado ────────────────────────────────────────────────────

@dataclass
class ShopifyPage:
    id: int
    handle: str
    title: str
    url: str         # URL pública de la página
    admin_url: str   # URL del editor en el panel de Shopify

    def __str__(self) -> str:
        return (
            f"ShopifyPage(id={self.id}, handle='{self.handle}')\n"
            f"  Pública:  {self.url}\n"
            f"  Admin:    {self.admin_url}"
        )


# ── HTTP ──────────────────────────────────────────────────────────────────────

@retry(
    retry=retry_if_exception_type(httpx.HTTPStatusError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _post(base: str, headers: dict, payload: dict) -> dict:
    _limiter.esperar()
    with httpx.Client(timeout=20) as client:
        resp = client.post(f"{base}/pages.json", json=payload, headers=headers)
        if resp.status_code == 429:
            retry_after = float(resp.headers.get("Retry-After", 2))
            time.sleep(retry_after)
            resp.raise_for_status()
        resp.raise_for_status()
        return resp.json()


@retry(
    retry=retry_if_exception_type(httpx.HTTPStatusError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _put(base: str, page_id: int, headers: dict, payload: dict) -> dict:
    _limiter.esperar()
    with httpx.Client(timeout=20) as client:
        resp = client.put(f"{base}/pages/{page_id}.json", json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


def _get_by_handle(base: str, headers: dict, handle: str) -> dict | None:
    """Busca una página existente por handle. Retorna None si no existe."""
    _limiter.esperar()
    with httpx.Client(timeout=15) as client:
        resp = client.get(
            f"{base}/pages.json",
            params={"handle": handle, "fields": "id,handle,title"},
            headers=headers,
        )
        resp.raise_for_status()
        pages = resp.json().get("pages", [])
        return pages[0] if pages else None


# ── Función pública ───────────────────────────────────────────────────────────

def publicar(
    copy: LandingCopy,
    landing: LandingHTML,
    publicada: bool = True,
) -> ShopifyPage:
    """
    Crea o actualiza una página en Shopify con el copy y HTML generados.

    Si ya existe una página con el mismo handle (keyword slugificado), la
    actualiza en lugar de crear un duplicado.

    Args:
        copy:      LandingCopy con headline (usado como título de página).
        landing:   LandingHTML renderizado por templates.renderizar().
        publicada: Si True, la página queda visible de inmediato en la tienda.

    Returns:
        ShopifyPage con id, handle, url pública y url del admin.

    Raises:
        EnvironmentError: Si SHOPIFY_STORE_URL o SHOPIFY_ACCESS_TOKEN faltan en .env.
        httpx.HTTPStatusError: Si la API de Shopify retorna un error no recuperable.
    """
    store_url = config("SHOPIFY_STORE_URL", default="")
    access_token = config("SHOPIFY_ACCESS_TOKEN", default="")

    if not store_url or not access_token:
        raise EnvironmentError(
            "Faltan SHOPIFY_STORE_URL y/o SHOPIFY_ACCESS_TOKEN en .env"
        )

    base = _base_url(store_url)
    headers = _auth_headers(access_token)
    handle = _slugify(copy.keyword)
    store_domain = store_url.rstrip("/").removeprefix("https://").removeprefix("http://")

    payload = {
        "page": {
            "title": copy.headline,
            "handle": handle,
            "body_html": landing.html,
            "published": publicada,
        }
    }

    # Upsert: actualizar si ya existe, crear si no
    existing = _get_by_handle(base, headers, handle)
    if existing:
        data = _put(base, existing["id"], headers, payload)
        page_data = data["page"]
    else:
        data = _post(base, headers, payload)
        page_data = data["page"]

    page_id = page_data["id"]

    return ShopifyPage(
        id=page_id,
        handle=handle,
        title=copy.headline,
        url=f"https://{store_domain}/pages/{handle}",
        admin_url=f"https://{store_domain}/admin/pages/{page_id}",
    )
