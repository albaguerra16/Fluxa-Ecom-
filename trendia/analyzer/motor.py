"""Motor de análisis de 9 criterios COD Colombia.

Combina datos del triangulador existente con búsqueda web real (web_search_20250305)
para evaluar viabilidad de un producto en dropshipping COD Colombia.

Flujo:
  datos_triangulador → Claude + web_search → 9 criterios + reporte completo
"""

from __future__ import annotations

import json
import re
from typing import Any

import anthropic
from decouple import config

from trendia.analyzer.criterios import (
    ESTADO_FAIL,
    ESTADO_OK,
    ESTADO_WARN,
    AnalisisCompleto,
    AnguloVenta,
    CriterioResultado,
    MarcaSugerida,
    NOMBRES_CRITERIOS,
)

_MODEL = "claude-sonnet-4-6"

_WEB_SEARCH_TOOL: dict[str, str] = {
    "type": "web_search_20250305",
    "name": "web_search",
}

# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
Eres un experto en análisis de productos para dropshipping COD (Contra Entrega) en Colombia.
Tu tarea es evaluar si un producto es viable para lanzar usando 9 criterios específicos.
Tienes acceso a búsqueda web — ÚSALA para obtener datos reales y actualizados.

═══════════════════════════════════════════════════════════════════
FRAMEWORK DE 9 CRITERIOS — DROPSHIPPING COD COLOMBIA
═══════════════════════════════════════════════════════════════════

CRITERIO 1 — SATURACIÓN DEL MERCADO
  Analiza: MercadoLibre CO (dato provisto) + Meta Ads CO (dato provisto) + TikTok CO (buscar)
  Usa los nuevos datos de Meta Ads Library 2026: impresiones del anuncio más activo y tiempo corriendo.
  Interpretación de impresiones (sweet spot COD = producto probado, no saturado):
    • Sin anuncios → nadie ha probado → riesgo alto (pero oportunidad si hay demanda)
    • 1-5 anuncios con <10K impresiones → etapa exploración → buena oportunidad
    • 1-5 anuncios con 10K-100K impresiones → mercado probado, competencia baja → IDEAL
    • 5-15 anuncios con 100K-500K impresiones → competitivo pero viable
    • +15 anuncios con 500K+ impresiones → saturado → CPM alto, márgenes comprimidos
  Tiempo corriendo: 3-6 meses = producto rentable probado. +12 meses = muy establecido.
  ✅ (2pts) Pocos anunciantes (1-10) con impresiones 1K-100K O ninguno pero demanda clara en ML/Trends
  ⚠️ (1pt)  10-20 anunciantes O impresiones 100K-500K en varios anuncios O mercado mediano ML
  ❌ (0pts) +20 anunciantes activos O múltiples anuncios con 500K+ impresiones O ML muy saturado

CRITERIO 2 — STOCK Y PROVEEDORES
  Analiza: Alibaba / AliExpress (buscar), precio FOB estimado, inversión de competencia
  ✅ (2pts) ≥ 5 proveedores confiables, precio FOB < 30% del PVP objetivo, buena disponibilidad
  ⚠️ (1pt)  2–4 proveedores O margen justo O stock irregular
  ❌ (0pts) < 2 proveedores O FOB muy alto O producto difícil de importar

CRITERIO 3 — CATÁLOGO PÚBLICO (Dollar City / D1 / Ara / Marketplace)
  Analiza: si el producto está en tiendas de descuento masivo en CO (buscar)
  ✅ (2pts) NO está en Dollar City / D1 / Ara + presencia baja en Marketplace CO
  ⚠️ (1pt)  Presencia parcial en tiendas O Marketplace moderado
  ❌ (0pts) Disponible masivamente en almacenes de descuento O Marketplace saturado CO

CRITERIO 4 — OPORTUNIDAD DE IMPORTACIÓN
  Analiza: validación en Amazon US/ES, AliExpress ventas, tracción en mercados maduros
  ✅ (2pts) Validado en mercados maduros (buenas reseñas, volumen) sin importador consolidado en CO
  ⚠️ (1pt)  Algo de competencia importadora en CO O tracción moderada en mercados externos
  ❌ (0pts) Ya hay importadores consolidados en CO O sin tracción en mercados maduros

CRITERIO 5 — TICKET (PRECIO DE VENTA COP)
  Analiza: precio actual en Colombia, margen estimado con logística COD
  ✅ (2pts) $100.000–$200.000 COP → margen óptimo para COD (cubre logística + devoluciones + ads)
  ⚠️ (1pt)  $50.000–$99.000 COP (margen justo) O $201.000–$400.000 COP (ticket alto, conv. difícil)
  ❌ (0pts) < $50.000 COP (inviable COD) O > $400.000 COP (muy difícil vender COD)

CRITERIO 6 — SUPLE UNA NECESIDAD REAL
  Analiza: ¿resuelve un problema concreto? ¿compra por impulso? ¿fácil de entender el beneficio?
  ✅ (2pts) Resuelve problema concreto + alto potencial de compra por impulso + beneficio obvio
  ⚠️ (1pt)  Necesidad moderada O requiere educación del comprador O beneficio no inmediato
  ❌ (0pts) Producto de lujo puro / decorativo sin función / muy nicho sin demanda masiva

CRITERIO 7 — POTENCIAL DE ANUNCIO CAUTIVADOR
  Analiza: ¿fácil demostración visual? ¿antes/después? ¿métricas TikTok? (buscar trending videos)
  ✅ (2pts) Demostración visual impactante, antes/después claro, trending en TikTok CO/LATAM
  ⚠️ (1pt)  Demostración posible pero compleja O poca tracción orgánica TikTok
  ❌ (0pts) Difícil de mostrar visualmente O sin momento "wow" O nada en TikTok

CRITERIO 8 — PERCEPCIÓN DE VALOR Y MARCA
  Analiza: potencial de naming diferencial, copy transformador, empaque premium, lenguaje aspiracional
  ✅ (2pts) Se puede crear marca con naming fuerte + copy transformador + empaque premium percibido
  ⚠️ (1pt)  Naming limitado O producto algo commoditizado pero diferenciable
  ❌ (0pts) Producto genérico imposible de diferenciar, percibido como "de segunda mano" o "chino barato"

CRITERIO 9 — PRODUCTO / OFERTA BLACK (POLÍTICAS META & TIKTOK)
  Analiza: políticas de Meta Ads y TikTok Ads sobre el producto (buscar si hay restricciones)
  ✅ (2pts) Sin restricciones — admitido sin reservas en Meta y TikTok
  ⚠️ (1pt)  Requiere aprobación especial O restricciones menores (ej: antes/después salud necesita disclosure)
  ❌ (0pts) Prohibido o muy restringido en Meta/TikTok (suplementos, afirmaciones médicas, adultos)

═══════════════════════════════════════════════════════════════════
ESCALA: ✅ = 2pts | ⚠️ = 1pt | ❌ = 0pts → Máximo 18pts
VEREDICTO: 13–18pts → LANZAR | 8–12pts → LANZAR CON PRECAUCIÓN | 0–7pts → NO LANZAR
═══════════════════════════════════════════════════════════════════

INSTRUCCIONES DE BÚSQUEDA:
Usa web_search para los siguientes datos ANTES de evaluar cada criterio:
  1. "{keyword} tiktok" — ver videos virales, volumen, vendedores CO
  2. "{keyword} alibaba site:alibaba.com" — ver proveedores y precios FOB
  3. "{keyword} dollar city colombia" — ver si está en catálogo masivo
  4. "{keyword} D1 colombia" o "{keyword} ara supermercados" — catálogo
  5. "{keyword} amazon site:amazon.com" o "amazon.es" — validación mercados maduros
  6. "{keyword} precio colombia" — estimar rango de ticket
  7. "{keyword} meta ads policy" o "tiktok ads policy" si hay duda sobre restricciones

INSTRUCCIONES DE OUTPUT:
1. Después de buscar, evalúa los 9 criterios con datos concretos.
2. Sé honesto: no inflés scores artificialmente. Un score bajo es información valiosa.
3. Los ángulos de venta deben ser copy REAL y listo para usar, no plantillas genéricas.
4. El nombre de marca debe ser original, memorable y apropiado para el mercado colombiano.
5. Los riesgos deben ser concretos y accionables, no genéricos.
6. Responde ÚNICAMENTE con el JSON al final, sin markdown, sin texto adicional.

FORMATO DE RESPUESTA FINAL (JSON estricto):
{
  "criterios": [
    {
      "numero": 1,
      "nombre": "Saturación del mercado",
      "estado": "✅",
      "nota": "explicación concreta con datos encontrados (1-2 líneas)",
      "puntos": 2
    }
    ... (9 criterios, mismo formato)
  ],
  "score_total": 0,
  "angulos_venta": [
    {
      "nombre": "TESTIMONIAL",
      "hook": "primera frase gancho (máx 10 palabras)",
      "copy": "copy completo listo para caption/guión (50-120 palabras, español colombiano natural)"
    },
    {
      "nombre": "DEMOSTRACIÓN",
      "hook": "...",
      "copy": "..."
    },
    {
      "nombre": "URGENCIA",
      "hook": "...",
      "copy": "..."
    }
  ],
  "marca": {
    "nombre": "NombreMarca (1-2 palabras, original)",
    "razon": "por qué funciona para este producto en el mercado colombiano (1 línea)",
    "copy_anuncio": "texto del anuncio principal con la marca (40-60 palabras)",
    "valor_agregado": "qué añadir al producto/oferta para justificar precio premium y diferenciarse",
    "empaque": "sugerencia concreta de empaque y unboxing experience"
  },
  "riesgos": [
    "Riesgo 1 — concreto y accionable",
    "Riesgo 2 — ...",
    "Riesgo 3 — ..."
  ],
  "veredicto": "LANZAR"
}
"""


# ── Helpers de parseo ─────────────────────────────────────────────────────────

def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError(f"No se encontró JSON en la respuesta: {text[:400]}")
    return json.loads(match.group())


def _estado_valido(s: str) -> str:
    if "✅" in s:
        return ESTADO_OK
    if "⚠" in s:
        return ESTADO_WARN
    return ESTADO_FAIL


def _build_criterio(raw: dict[str, Any], idx: int) -> CriterioResultado:
    estado = _estado_valido(str(raw.get("estado", "❌")))
    puntos = int(raw.get("puntos", 0))
    # Sanity-check puntos vs estado
    if estado == ESTADO_OK and puntos != 2:
        puntos = 2
    elif estado == ESTADO_WARN and puntos != 1:
        puntos = 1
    elif estado == ESTADO_FAIL and puntos != 0:
        puntos = 0
    return CriterioResultado(
        numero=int(raw.get("numero", idx + 1)),
        nombre=str(raw.get("nombre", NOMBRES_CRITERIOS[idx])),
        estado=estado,
        nota=str(raw.get("nota", "")),
        puntos=puntos,
    )


def _parse_respuesta(raw_text: str, keyword: str) -> tuple[AnalisisCompleto, int, int]:
    """Parsea el JSON de Claude → AnalisisCompleto."""
    data = _parse_json(raw_text)

    criterios_raw = data.get("criterios", [])
    criterios: list[CriterioResultado] = []
    for i, c in enumerate(criterios_raw[:9]):
        criterios.append(_build_criterio(c, i))
    # Rellena si Claude omitió alguno
    while len(criterios) < 9:
        i = len(criterios)
        criterios.append(CriterioResultado(
            numero=i + 1,
            nombre=NOMBRES_CRITERIOS[i],
            estado=ESTADO_FAIL,
            nota="No evaluado",
            puntos=0,
        ))

    score_total = sum(c.puntos for c in criterios)

    angulos_raw = data.get("angulos_venta", [])
    angulos: list[AnguloVenta] = [
        AnguloVenta(
            nombre=str(a.get("nombre", f"ÁNGULO {i+1}")),
            hook=str(a.get("hook", "")),
            copy=str(a.get("copy", "")),
        )
        for i, a in enumerate(angulos_raw[:3])
    ]

    marca_raw = data.get("marca", {})
    marca = MarcaSugerida(
        nombre=str(marca_raw.get("nombre", keyword.title())),
        razon=str(marca_raw.get("razon", "")),
        copy_anuncio=str(marca_raw.get("copy_anuncio", "")),
        valor_agregado=str(marca_raw.get("valor_agregado", "")),
        empaque=str(marca_raw.get("empaque", "")),
    )

    riesgos = [str(r) for r in data.get("riesgos", [])]

    # Recalcular veredicto desde el score para consistencia
    if score_total >= 13:
        veredicto = "LANZAR"
    elif score_total >= 8:
        veredicto = "LANZAR CON PRECAUCIÓN"
    else:
        veredicto = "NO LANZAR"

    analisis = AnalisisCompleto(
        keyword=keyword,
        criterios=criterios,
        score_total=score_total,
        angulos_venta=angulos,
        marca=marca,
        riesgos=riesgos,
        veredicto=veredicto,
    )
    return analisis, 0, 0


# ── Loop de herramientas (web_search es server-side en Anthropic) ─────────────

def _run_claude(
    client: anthropic.Anthropic,
    system_blocks: list[dict[str, Any]],
    user_prompt: str,
    usar_web_search: bool,
) -> tuple[str, int, int]:
    """
    Ejecuta Claude con búsqueda web opcional y retorna (texto_final, tokens_in, tokens_out).

    web_search_20250305 es un tool server-side: Anthropic ejecuta la búsqueda
    automáticamente. El loop maneja stop_reason='tool_use' enviando los
    tool_result al siguiente turno para que Claude continúe.
    """
    tools: list[dict[str, str]] = [_WEB_SEARCH_TOOL] if usar_web_search else []
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_prompt}]
    total_in = total_out = 0

    for _turn in range(15):
        kwargs: dict[str, Any] = dict(
            model=_MODEL,
            max_tokens=4096,
            system=system_blocks,
            messages=messages,
        )
        if tools:
            kwargs["tools"] = tools

        resp = client.messages.create(**kwargs)

        total_in  += getattr(resp.usage, "input_tokens", 0)
        total_out += getattr(resp.usage, "output_tokens", 0)

        # Guardar respuesta en el historial
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "end_turn":
            # Retornar el último bloque de texto
            for block in reversed(resp.content):
                if hasattr(block, "text") and block.text.strip():
                    return block.text, total_in, total_out
            break

        if resp.stop_reason == "tool_use":
            # Construir tool_results para el siguiente turno.
            # Para web_search (server-side), los resultados ya pueden estar
            # embebidos como tool_result blocks dentro de resp.content.
            result_map: dict[str, Any] = {}
            for block in resp.content:
                if getattr(block, "type", None) == "tool_result":
                    result_map[block.tool_use_id] = block

            tool_results: list[dict[str, Any]] = []
            for block in resp.content:
                if getattr(block, "type", None) != "tool_use":
                    continue
                if block.id in result_map:
                    tr = result_map[block.id]
                    content = tr.content
                    if not isinstance(content, str):
                        content = json.dumps(content, ensure_ascii=False)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": content,
                    })
                else:
                    # El server-side tool provee resultados en la siguiente
                    # respuesta; añadimos el tool_result vacío para cumplir
                    # el protocolo y que Claude reciba los datos en el siguiente turno.
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Resultados de búsqueda procesados.",
                    })

            if tool_results:
                messages.append({"role": "user", "content": tool_results})

    raise RuntimeError("No se obtuvo una respuesta final del analizador tras los intentos máximos.")


# ── Función pública ───────────────────────────────────────────────────────────

def analizar(
    keyword: str,
    ml_data: dict[str, Any],
    trends_data: dict[str, Any],
    meta_data: dict[str, Any] | None = None,
    marketplace_data: dict[str, Any] | None = None,
    usar_web_search: bool = True,
    meta_impresiones: str = "",
    meta_meses: str = "",
) -> AnalisisCompleto:
    """
    Analiza un producto con el framework de 9 criterios COD Colombia.

    Args:
        keyword:          Producto a analizar.
        ml_data:          Dict con keys total_productos, num_marcas, dominios.
        trends_data:      Dict con keys interes_promedio, interes_peak, tendencia.
        meta_data:        Dict con key num_anuncios (opcional).
        marketplace_data: Dict con key num_publicaciones (opcional).
        usar_web_search:  Si True, habilita web_search_20250305 para datos en tiempo real.

    Returns:
        AnalisisCompleto con los 9 criterios evaluados y el reporte completo.
    """
    api_key = config("ANTHROPIC_API_KEY", default="")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY no está configurado en .env")

    meta_data = meta_data or {}
    marketplace_data = marketplace_data or {}

    tendencia_dir = (
        "↑ creciendo"
        if trends_data.get("tendencia", 0) > 0.5
        else ("↓ cayendo" if trends_data.get("tendencia", 0) < -0.5 else "→ estable")
    )

    user_prompt = f"""\
Analiza este producto para dropshipping COD Colombia:

PRODUCTO: {keyword}

─── DATOS DEL TRIANGULADOR (ya recopilados) ───────────────────

MercadoLibre Colombia:
  • Total productos en catálogo: {ml_data.get('total_productos', 'N/D')}
  • Marcas únicas: {ml_data.get('num_marcas', 'N/D')}
  • Categorías: {', '.join(ml_data.get('dominios', [])) or 'N/D'}

Google Trends Colombia (últimos 90 días):
  • Interés promedio: {trends_data.get('interes_promedio', 'N/D')}/100
  • Peak: {trends_data.get('interes_peak', 'N/D')}/100
  • Tendencia: {trends_data.get('tendencia', 0):+.2f} ({tendencia_dir})

Meta Ads Library Colombia (anuncios activos) — datos nuevos Ads Library 2026:
  • Anuncios activos: {meta_data.get('num_anuncios', 0)}
  • Impresiones del anuncio más activo: {meta_impresiones or 'No disponible'}
  • Tiempo corriendo el anuncio más antiguo: {meta_meses or 'No disponible'}
  (Nota: impresiones altas + meses corriendo = el producto convierte, no es prueba)

Facebook Marketplace Colombia:
  • Publicaciones: {marketplace_data.get('num_publicaciones', 0)}

─── BÚSQUEDAS WEB RECOMENDADAS ────────────────────────────────

Busca en este orden para completar los criterios que faltan datos:
  1. "{keyword} tiktok" — saturación y viral potential (criterios 1 y 7)
  2. "{keyword} alibaba" — proveedores y precio FOB (criterio 2)
  3. "{keyword} dollar city colombia" + "{keyword} D1 tiendas" — catálogo masivo (criterio 3)
  4. "{keyword} amazon" — validación mercados maduros (criterio 4)
  5. "{keyword} precio colombia" — rango de ticket (criterio 5)
  6. Meta Ads / TikTok policy si hay duda (criterio 9)

Luego evalúa los 9 criterios y genera el reporte completo en JSON estricto.
"""

    system_blocks: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": _SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    client = anthropic.Anthropic(api_key=api_key)
    raw_text, tokens_in, tokens_out = _run_claude(
        client, system_blocks, user_prompt, usar_web_search
    )

    analisis, _, _ = _parse_respuesta(raw_text, keyword)
    analisis.tokens_entrada = tokens_in
    analisis.tokens_salida = tokens_out
    return analisis
