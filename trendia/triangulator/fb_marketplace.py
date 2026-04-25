"""Facebook Marketplace scraper — publicaciones activas en Colombia para un keyword.

Intenta 3 variantes de URL en orden de preferencia (city-specific primero).
Facebook Marketplace requiere login para búsqueda completa; el scraper cuenta
los items que carguen antes del login wall y retorna 0 si el acceso es denegado.

Estrategias de extracción en orden de preferencia:
  1. Links href que apuntan a /marketplace/item/ (los más fiables).
  2. data-testid de items del feed.
  3. Imágenes de contenido en el feed principal (proxy para contar tarjetas).
  4. Regex sobre texto de página buscando patrones de conteo.
"""

from __future__ import annotations

import asyncio
import random
import re
from dataclasses import dataclass
from urllib.parse import quote

from playwright.async_api import async_playwright

# Probamos primero Bogotá (ciudad con mayor volumen), luego Colombia genérica
_URL_TEMPLATES = [
    "https://www.facebook.com/marketplace/bogota/search/?query={q}",
    "https://www.facebook.com/marketplace/category/search/?query={q}",
    "https://www.facebook.com/marketplace/search/?query={q}",
]

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]

_LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
]

_LOGIN_INDICATORS = [
    "log in to facebook",
    "iniciar sesión en facebook",
    "inicia sesión",
    "you must log in",
    "debes iniciar sesión",
]

_COUNT_PATTERNS = [
    r"(\d[\d,\.]+)\s+(?:publicaciones?|artículos?|resultados?|listings?)",
    r"(?:mostrando|showing)\s+(\d[\d,\.]+)",
    r"(\d[\d,\.]+)\s+items?\s+(?:found|encontrados?)",
]

# Selectores de items del Marketplace en orden de fiabilidad
_ITEM_SELECTORS = [
    "a[href*='/marketplace/item/']",
    "[data-testid='marketplace_feed_item']",
    "[data-testid='marketplace-product-item']",
    "div[role='main'] a[href*='marketplace']",
]


def _random_delay_ms() -> int:
    return int(random.uniform(2.0, 5.0) * 1000)


def _random_ua() -> str:
    return random.choice(_USER_AGENTS)


def _is_login_wall(title: str, body: str) -> bool:
    combined = (title + " " + body[:500]).lower()
    return any(ind in combined for ind in _LOGIN_INDICATORS)


def _parse_count(text: str) -> int | None:
    for pattern in _COUNT_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            raw = re.sub(r"[,\.]", "", m.group(1))
            if raw.isdigit() and len(raw) <= 6:
                return int(raw)
    return None


@dataclass
class MarketplaceResultado:
    keyword: str
    num_publicaciones: int  # publicaciones encontradas; 0 si login wall o error

    def __str__(self) -> str:
        return (
            f"MarketplaceResultado(keyword='{self.keyword}', "
            f"publicaciones_CO={self.num_publicaciones})"
        )


async def _contar_items(page) -> int:
    # Estrategia 1-4: selectores de items
    for selector in _ITEM_SELECTORS:
        items = await page.locator(selector).all()
        if len(items) > 0:
            return len(items)

    # Estrategia 5: imágenes de contenido scontent (proxy de tarjetas en feed)
    imgs = await page.locator("div[role='main'] img[src*='scontent']").all()
    if len(imgs) > 3:
        return len(imgs)

    # Estrategia 6: regex sobre texto de página
    body_text = await page.inner_text("body")
    count = _parse_count(body_text)
    if count is not None:
        return count

    return 0


async def _scrape_async(keyword: str) -> MarketplaceResultado:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=_LAUNCH_ARGS)
        context = await browser.new_context(
            user_agent=_random_ua(),
            locale="es-CO",
            timezone_id="America/Bogota",
            extra_http_headers={"Accept-Language": "es-CO,es;q=0.9,en;q=0.8"},
        )
        page = await context.new_page()

        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        for url_template in _URL_TEMPLATES:
            try:
                url = url_template.format(q=quote(keyword))
                await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                await page.wait_for_timeout(_random_delay_ms())

                title = await page.title()
                body_snippet = await page.inner_text("body")

                # Saltar a siguiente URL si hay login wall
                if _is_login_wall(title, body_snippet):
                    continue

                count = await _contar_items(page)
                if count > 0:
                    await browser.close()
                    return MarketplaceResultado(keyword=keyword, num_publicaciones=count)

            except Exception:
                continue

        await browser.close()
        return MarketplaceResultado(keyword=keyword, num_publicaciones=0)


def scrapear(keyword: str) -> MarketplaceResultado:
    """Scraper sincrónico — retorna 0 en cualquier error para no romper el pipeline."""
    try:
        return asyncio.run(_scrape_async(keyword))
    except Exception:
        return MarketplaceResultado(keyword=keyword, num_publicaciones=0)
