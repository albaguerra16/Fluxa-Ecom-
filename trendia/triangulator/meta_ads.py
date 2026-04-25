"""Meta Ads Library scraper — anuncios activos en Colombia para un keyword.

URL pública sin login requerido: facebook.com/ads/library (filtro país=CO,
active_status=active). Si falla por cualquier razón (bot detection, timeout,
selector roto) retorna 0 y continúa el pipeline sin interrumpirlo.

Estrategias de extracción en orden de preferencia:
  1. Regex sobre texto de la página buscando patrones de conteo.
  2. Conteo de contenedores de anuncios rendered (role=article, etc).
"""

from __future__ import annotations

import asyncio
import random
import re
from dataclasses import dataclass
from urllib.parse import quote

from playwright.async_api import async_playwright

_URL = (
    "https://www.facebook.com/ads/library/"
    "?active_status=active&ad_type=all&country=CO"
    "&q={q}&search_type=keyword_unordered"
)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1",
]

_LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
]

# Selectores de botones de consentimiento de cookies (Facebook varía por región)
_CONSENT_SELECTORS = [
    "button[data-cookiebanner='accept_button']",
    "button[title='Allow all cookies']",
    "[data-testid='cookie-policy-manage-dialog-accept-button']",
    "button:has-text('Aceptar todo')",
    "button:has-text('Accept All')",
    "button:has-text('Allow all')",
]

# Patrones de conteo en el texto de la página (español e inglés)
_COUNT_PATTERNS = [
    r"(\d[\d\s,\.]*)\s+(?:anuncios?\s+activos?|anuncios?\s+encontrados?)",
    r"(\d[\d\s,\.]*)\s+(?:results?|resultados?)\s+(?:for|para|encontrados?)",
    r"(?:encontramos|found|showing)\s+(\d[\d\s,\.]+)\s+(?:ads?|anuncios?)",
    r"(\d[\d,\.]+)\s+ads?\s+match",
]

# Selectores de contenedores de anuncios individuales
_AD_CARD_SELECTORS = [
    "[data-testid='ad-library-preview-card']",
    "[data-testid='ad_library_preview_card']",
    "div[role='article']",
    "a[href*='/ads/library/']",
]


def _random_delay_ms() -> int:
    return int(random.uniform(2.0, 5.0) * 1000)


def _random_ua() -> str:
    return random.choice(_USER_AGENTS)


def _parse_count(text: str) -> int | None:
    for pattern in _COUNT_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            raw = re.sub(r"[\s,\.]", "", m.group(1))
            if raw.isdigit() and len(raw) <= 7:
                return int(raw)
    return None


@dataclass
class MetaAdsResultado:
    keyword: str
    num_anuncios: int   # anuncios activos en Colombia; 0 si no se pudo scrapear

    def __str__(self) -> str:
        return (
            f"MetaAdsResultado(keyword='{self.keyword}', "
            f"anuncios_activos_CO={self.num_anuncios})"
        )


async def _scrape_async(keyword: str) -> MetaAdsResultado:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=_LAUNCH_ARGS)
        context = await browser.new_context(
            user_agent=_random_ua(),
            locale="es-CO",
            timezone_id="America/Bogota",
            extra_http_headers={"Accept-Language": "es-CO,es;q=0.9,en;q=0.8"},
        )
        page = await context.new_page()

        # Ocultar señales de automatización
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        try:
            url = _URL.format(q=quote(keyword))
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(_random_delay_ms())

            # Aceptar diálogos de cookies si aparecen
            for selector in _CONSENT_SELECTORS:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=1_500):
                        await btn.click()
                        await page.wait_for_timeout(1_000)
                        break
                except Exception:
                    pass

            # Esperar a que carguen resultados dinámicos
            await page.wait_for_timeout(_random_delay_ms())

            # Estrategia 1: extraer conteo del texto de la página
            body_text = await page.inner_text("body")
            count = _parse_count(body_text)
            if count is not None:
                return MetaAdsResultado(keyword=keyword, num_anuncios=count)

            # Estrategia 2: contar contenedores de anuncios rendered
            for selector in _AD_CARD_SELECTORS:
                items = await page.locator(selector).all()
                if len(items) > 0:
                    return MetaAdsResultado(keyword=keyword, num_anuncios=len(items))

            return MetaAdsResultado(keyword=keyword, num_anuncios=0)

        except Exception:
            return MetaAdsResultado(keyword=keyword, num_anuncios=0)
        finally:
            await browser.close()


def scrapear(keyword: str) -> MetaAdsResultado:
    """Scraper sincrónico — retorna 0 en cualquier error para no romper el pipeline."""
    try:
        return asyncio.run(_scrape_async(keyword))
    except Exception:
        return MetaAdsResultado(keyword=keyword, num_anuncios=0)
