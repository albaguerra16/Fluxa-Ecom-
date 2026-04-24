# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Trendia** — pipeline de dropshipping Colombia COD (Cash on Delivery). Detecta productos virales, genera landing pages y variaciones de video de forma automatizada.

## Commands

```bash
# Instalar dependencias
pip install -e ".[dev]"

# ── Pipeline ──────────────────────────────────────────────────────────────────

# Pipeline completo (triangulación + landing + video)
python scripts/run_pipeline.py "faja colombiana"

# Solo triangular — ver score sin gastar créditos de Claude/fal.ai
python scripts/run_pipeline.py "faja colombiana" --solo-triangular

# Simular todo el flujo sin llamar a ninguna API externa
python scripts/run_pipeline.py "faja colombiana" --dry-run

# Generar landing pero no publicar en Shopify
python scripts/run_pipeline.py "faja colombiana" --no-publicar

# Con imagen del producto y contexto extra para Claude
python scripts/run_pipeline.py "faja colombiana" \
  --imagen-url https://cdn.ejemplo.com/faja.jpg \
  --contexto "Precio: $89.900 COP, tallas XS-4XL"

# Bajar umbral de score y reducir variaciones de video
python scripts/run_pipeline.py "faja colombiana" --threshold 40 --variaciones 1

# Omitir el módulo de video
python scripts/run_pipeline.py "faja colombiana" --no-video

# ── Tests ─────────────────────────────────────────────────────────────────────

# Todos los tests
pytest

# Módulo específico
pytest tests/test_triangulator.py -v
pytest tests/test_landing.py -v
pytest tests/test_video.py -v

# Test individual
pytest tests/test_triangulator.py::TestPuntuar::test_producto_alto -v

# ── Calidad ───────────────────────────────────────────────────────────────────

ruff check trendia/
ruff format trendia/
mypy trendia/
```

## Architecture

El proyecto corre un pipeline secuencial de 3 etapas:

```
Triangulator → Landing → Video
(ML + Trends + Score)   (Claude API + Shopify)   (fal.ai async)
     ↓                        ↓                        ↓
 ProductScore            LandingCopy              LoteVideos
                         LandingHTML
                         ShopifyPage
```

### 1. `trendia/triangulator/` — Puntuación de productos

- **`mercadolibre.py`** — Usa `/products/search` (accesible desde Cloud/datacenter con token). Retorna `MLResultado` con `total_productos` (tamaño de mercado, escala logarítmica) y `num_marcas` (proxy de competencia). El endpoint `/sites/MCO/search` que devuelve precios y ventas por ítem está bloqueado para IPs de datacenter por el PolicyAgent de ML.
- **`trends.py`** — `pytrends` con `geo='CO'`, timeframe `today 3-m` (datos diarios ~90 puntos). Retorna `TrendsResultado` con `interes_promedio`, `interes_peak` y `tendencia` (pendiente de regresión lineal). Usar `today 3-m` y no periodos más largos: con `geo='CO'` los periodos >90 días devuelven ceros por volumen insuficiente.
- **`scorer.py`** — Pesos: Trends 55% + Demanda ML 25% + Competencia inversa 20%. Bonus +5 si `tendencia > 0.5`. El score de trends combina `interes_promedio * 0.6 + interes_peak * 0.4` para compensar la naturaleza esparcida de los datos diarios geo-filtrados.

### 2. `trendia/landing/` — Landing page automática

- **`generator.py`** — Claude `claude-sonnet-4-6` con system prompt cacheado (`cache_control: ephemeral`). Genera JSON con 7 campos fijos: `headline`, `subheadline`, `bullets[5]`, `cta_principal`, `cta_secundario`, `garantia`, `badge_cod`. El `score` del triangulator ajusta el tono (ALTO → urgencia, NICHO → exclusividad).
- **`templates.py`** — Jinja2 con `autoescape=True`. Produce HTML con inline CSS mobile-first listo para inyectar en `body_html` de Shopify. No depende del tema activo.
- **`shopify.py`** — Upsert automático: busca por handle antes de crear (evita duplicados al re-correr). Rate limiter thread-safe a 2 req/s. Lee `Retry-After` en respuestas 429. `_slugify` normaliza Unicode (acentos → ASCII).

### 3. `trendia/video/` — Variaciones de video

- **`fal_client.py`** — `subscribe_async` con `asyncio.wait_for(timeout=600s)`. `EnvironmentError` por `FAL_KEY` faltante se lanza **antes** del `try/except` para que no quede silenciado en `job.error`. Errores de red/API se almacenan en `job.error` sin propagar — el lote continúa aunque un job falle.
- **`variations.py`** — Tres ángulos narrativos para el funnel COD: `TESTIMONIAL` (rompe desconfianza), `DEMOSTRACION` (muestra beneficios), `URGENCIA` (cierra venta con badge COD visible). `asyncio.gather` submite todos en paralelo; tiempo total = job más lento. Para N > 3 cicla los ángulos.

### Configuración `.env`

```
MELI_ACCESS_TOKEN      # APP_USR-... de developers.mercadolibre.com.ar
ANTHROPIC_API_KEY      # console.anthropic.com
SHOPIFY_STORE_URL      # mitienda.myshopify.com
SHOPIFY_ACCESS_TOKEN   # permiso write_content
FAL_KEY                # fal.ai dashboard
SCORE_THRESHOLD=60     # score mínimo para pasar al landing
VIDEO_VARIATIONS=3     # variaciones de video por producto
```

### Flujo de datos entre etapas

```
buscar(keyword)          → MLResultado
interes_colombia(kw)     → TrendsResultado
puntuar(ml, tr)          → ProductScore      ← threshold gate aquí

generar_copy(kw, score)  → LandingCopy
renderizar(copy)         → LandingHTML
publicar(copy, landing)  → ShopifyPage

generar_variaciones(copy) → LoteVideos
  └─ generar_video_async × N  (asyncio.gather)
       └─ VideoJob(angulo, prompt, video_url)
```
