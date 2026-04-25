"""Cliente Shopify Admin REST API para publicar landing pages COD.

Autenticación: OAuth 2.0 client_credentials.
  1. POST /admin/oauth/access_token con client_id + client_secret
     → Shopify devuelve un access_token offline (no expira en custom apps)
  2. Todas las llamadas Admin REST usan X-Shopify-Access-Token: {token}

El token se cachea en memoria durante la vida del proceso para no repetir
el intercambio en cada llamada. Si el token es rechazado (401) se limpia
el caché y se reintenta el intercambio una vez.

Rate limiting: bucket de 40 créditos/segundo (REST). Operamos a 2 req/s.
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
    """Token bucket simple — thread-safe."""

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

# Caché del access token OAuth en memoria
_token_cache: dict[str, str] = {}   # clave: client_id → valor: access_token
_token_lock = threading.Lock()


# ── OAuth client_credentials ──────────────────────────────────────────────────

def _intercambiar_credenciales(store_url: str, client_id: str, client_secret: str) -> str:
    """
    Intercambia Client ID + Client Secret por un access token de Shopify.

    Shopify devuelve un token offline para custom apps; no expira mientras
    la app siga instalada en la tienda.
    """
    endpoint = f"{_normalizar_url(store_url)}/admin/oauth/access_token"
    with httpx.Client(timeout=15) as client:
        resp = client.post(
            endpoint,
            json={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            },
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

    token = data.get("access_token", "")
    if not token:
        raise ValueError(
            f"Shopify no retornó access_token. Respuesta: {data}"
        )
    return token


def _obtener_token(store_url: str, client_id: str, client_secret: str) -> str:
    """Retorna el access token cacheado o realiza el intercambio OAuth."""
    with _token_lock:
        if client_id in _token_cache:
            return _token_cache[client_id]
        token = _intercambiar_credenciales(store_url, client_id, client_secret)
        _token_cache[client_id] = token
        return token


def _invalidar_token(client_id: str) -> None:
    with _token_lock:
        _token_cache.pop(client_id, None)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    """Convierte texto a handle URL-safe para Shopify."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:100]


def _normalizar_url(store_url: str) -> str:
    store_url = store_url.rstrip("/")
    if not store_url.startswith("https://"):
        store_url = f"https://{store_url}"
    return store_url


def _base_url(store_url: str) -> str:
    return f"{_normalizar_url(store_url)}/admin/api/{_API_VERSION}"


def _auth_headers(token: str) -> dict[str, str]:
    return {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _credenciales() -> tuple[str, str, str]:
    """Lee y valida las tres variables requeridas de .env."""
    store_url = config("SHOPIFY_STORE_URL", default="")
    client_id = config("SHOPIFY_CLIENT_ID", default="")
    client_secret = config("SHOPIFY_CLIENT_SECRET", default="")

    faltantes = [k for k, v in {
        "SHOPIFY_STORE_URL": store_url,
        "SHOPIFY_CLIENT_ID": client_id,
        "SHOPIFY_CLIENT_SECRET": client_secret,
    }.items() if not v]

    if faltantes:
        raise EnvironmentError(
            f"Faltan en .env: {', '.join(faltantes)}\n"
            "Configura SHOPIFY_STORE_URL, SHOPIFY_CLIENT_ID y SHOPIFY_CLIENT_SECRET."
        )
    return store_url, client_id, client_secret


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


# ── HTTP con retry y manejo de 401 ────────────────────────────────────────────

def _request_con_retry(
    method: str,
    url: str,
    client_id: str,
    store_url: str,
    client_secret: str,
    **kwargs,
) -> dict:
    """Ejecuta un request Admin REST. Si recibe 401, renueva el token y reintenta una vez."""
    for intento in range(2):
        _limiter.esperar()
        token = _obtener_token(store_url, client_id, client_secret)
        headers = _auth_headers(token)

        with httpx.Client(timeout=20) as client:
            resp = getattr(client, method)(url, headers=headers, **kwargs)

        if resp.status_code == 401 and intento == 0:
            _invalidar_token(client_id)
            continue

        if resp.status_code == 429:
            time.sleep(float(resp.headers.get("Retry-After", 2)))
            resp.raise_for_status()

        resp.raise_for_status()
        return resp.json()

    raise RuntimeError("No se pudo autenticar con Shopify después de renovar el token.")


@retry(
    retry=retry_if_exception_type(httpx.HTTPStatusError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _post(base: str, client_id: str, store_url: str, client_secret: str, payload: dict) -> dict:
    return _request_con_retry("post", f"{base}/pages.json", client_id, store_url, client_secret, json=payload)


@retry(
    retry=retry_if_exception_type(httpx.HTTPStatusError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _put(base: str, page_id: int, client_id: str, store_url: str, client_secret: str, payload: dict) -> dict:
    return _request_con_retry("put", f"{base}/pages/{page_id}.json", client_id, store_url, client_secret, json=payload)


def _get_by_handle(base: str, client_id: str, store_url: str, client_secret: str, handle: str) -> dict | None:
    result = _request_con_retry(
        "get", f"{base}/pages.json", client_id, store_url, client_secret,
        params={"handle": handle, "fields": "id,handle,title"},
    )
    pages = result.get("pages", [])
    return pages[0] if pages else None


# ── Función pública ───────────────────────────────────────────────────────────

def publicar(
    copy: LandingCopy,
    landing: LandingHTML,
    publicada: bool = True,
) -> ShopifyPage:
    """
    Crea o actualiza una página en Shopify con el copy y HTML generados.

    Autenticación: OAuth client_credentials (SHOPIFY_CLIENT_ID + SHOPIFY_CLIENT_SECRET).
    El access token se obtiene automáticamente y se cachea en memoria.

    Si ya existe una página con el mismo handle, la actualiza (upsert).

    Args:
        copy:      LandingCopy con headline (título de página) y keyword (handle).
        landing:   LandingHTML renderizado por templates.renderizar().
        publicada: Si True, la página queda visible de inmediato.

    Returns:
        ShopifyPage con id, handle, url pública y url del admin.

    Raises:
        EnvironmentError: Si faltan variables en .env.
        httpx.HTTPStatusError: Si la API retorna un error no recuperable.
    """
    store_url, client_id, client_secret = _credenciales()

    base = _base_url(store_url)
    handle = _slugify(copy.keyword)
    store_domain = _normalizar_url(store_url).removeprefix("https://")

    payload = {
        "page": {
            "title": copy.headline,
            "handle": handle,
            "body_html": landing.html,
            "published": publicada,
        }
    }

    existing = _get_by_handle(base, client_id, store_url, client_secret, handle)
    if existing:
        data = _put(base, existing["id"], client_id, store_url, client_secret, payload)
    else:
        data = _post(base, client_id, store_url, client_secret, payload)

    page_data = data["page"]
    page_id = page_data["id"]

    return ShopifyPage(
        id=page_id,
        handle=handle,
        title=copy.headline,
        url=f"https://{store_domain}/pages/{handle}",
        admin_url=f"https://{store_domain}/admin/pages/{page_id}",
    )
