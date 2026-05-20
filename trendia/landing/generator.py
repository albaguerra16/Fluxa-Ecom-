"""Generador de copy para landing page COD Colombia usando Claude API.

Diseño de prompts:
- System prompt cacheado (ephemeral): contexto fijo de COD Colombia que no cambia
  entre productos → cache hit desde la segunda llamada, reduce costo ~90%.
- User prompt: datos variables del producto (keyword, score, dominios ML).
- Respuesta estructurada en JSON con schema fijo para facilitar el render en Shopify.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

import anthropic
from decouple import config

_MODEL = "claude-sonnet-4-6"

# System prompt fijo — candidato a prompt caching (>1024 tokens requeridos por Anthropic)
_SYSTEM_PROMPT = """\
Eres un experto en copywriting de alta conversión para e-commerce con modalidad \
Contra Entrega (COD) en Colombia. Tu especialidad es escribir copy que supere las \
objeciones específicas del comprador colombiano COD:

CONTEXTO DEL COMPRADOR COLOMBIANO COD:
- Desconfía de pagar por adelantado; prefiere ver el producto antes de pagar.
- Es sensible al precio pero valora la garantía de satisfacción.
- Responde bien a la urgencia real (stock limitado, oferta por tiempo).
- Confía más en el testimonio de personas de su ciudad/región.
- El miedo a ser estafado es la objeción #1 — la promesa COD la elimina directamente.
- Lenguaje: español colombiano natural, sin anglicismos innecesarios, con "usted" en CTA formal \
o "tú" en tono cercano según el producto.

ESTRUCTURA DE COPY QUE DEBES GENERAR:
1. headline: Frase principal (máx 12 palabras). Debe contener el beneficio #1 y/o el gancho emocional.
2. subheadline: Amplifica el headline con la promesa COD (máx 20 palabras).
3. bullets: Lista de 5 beneficios/características. Cada bullet empieza con emoji relevante \
y termina con el beneficio tangible, no la característica.
4. cta_principal: Llamada a acción principal (máx 8 palabras). Debe reforzar el COD.
5. cta_secundario: CTA de urgencia/escasez (máx 10 palabras).
6. garantia: Frase corta de garantía que elimine el riesgo de compra (máx 15 palabras).
7. badge_cod: Texto corto para el badge de Contra Entrega (máx 6 palabras).

REGLAS ABSOLUTAS:
- Nunca menciones el precio (se configurará en Shopify).
- No uses frases genéricas como "producto de alta calidad" o "el mejor del mercado".
- El copy debe ser específico al producto, no aplica para cualquier cosa.
- Si el producto es de salud/belleza, enfatiza transformación y confianza.
- Si es hogar/tecnología, enfatiza ahorro de tiempo y facilidad.
- Responde ÚNICAMENTE con JSON válido, sin markdown, sin explicaciones adicionales.

FORMATO DE RESPUESTA (JSON estricto):
{
  "headline": "...",
  "subheadline": "...",
  "bullets": ["...", "...", "...", "...", "..."],
  "cta_principal": "...",
  "cta_secundario": "...",
  "garantia": "...",
  "badge_cod": "..."
}
"""


@dataclass
class LandingCopy:
    keyword: str
    headline: str
    subheadline: str
    bullets: list[str]
    cta_principal: str
    cta_secundario: str
    garantia: str
    badge_cod: str
    tokens_entrada: int = 0
    tokens_salida: int = 0
    cache_hit: bool = False

    def __str__(self) -> str:
        lineas = [
            f"── LandingCopy: '{self.keyword}' ──",
            f"  Headline:     {self.headline}",
            f"  Subheadline:  {self.subheadline}",
            f"  Bullets:",
            *[f"    {b}" for b in self.bullets],
            f"  CTA principal:   {self.cta_principal}",
            f"  CTA urgencia:    {self.cta_secundario}",
            f"  Garantía:        {self.garantia}",
            f"  Badge COD:       {self.badge_cod}",
            f"  Tokens: {self.tokens_entrada}↑ {self.tokens_salida}↓"
            + (" [cache hit]" if self.cache_hit else ""),
        ]
        return "\n".join(lineas)


def _build_user_prompt(
    keyword: str,
    score: float,
    dominios: list[str],
    contexto_extra: str,
) -> str:
    categoria = ", ".join(d.replace("MCO-", "").replace("_", " ").title() for d in dominios) or "General"
    nivel = "alta demanda y alta oportunidad" if score >= 70 else (
        "demanda media — diferéncialo con garantía y urgencia" if score >= 50
        else "nicho específico — enfatiza exclusividad"
    )

    prompt = f"""Genera el copy de landing page COD para el siguiente producto:

PRODUCTO: {keyword}
CATEGORÍA ML: {categoria}
NIVEL DE OPORTUNIDAD: {nivel} (score triangulator: {score:.0f}/100)
"""
    if contexto_extra:
        prompt += f"\nCONTEXTO ADICIONAL DEL VENDEDOR:\n{contexto_extra}\n"

    prompt += "\nRecuerda: responde SOLO con el JSON, sin texto adicional."
    return prompt


def _parse_json(raw: str) -> dict:
    """Extrae el JSON de la respuesta aunque Claude agregue texto alrededor."""
    raw = raw.strip()
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise ValueError(f"No se encontró JSON en la respuesta: {raw[:200]}")
    return json.loads(match.group())


def generar_copy(
    keyword: str,
    score: float = 50.0,
    dominios: list[str] | None = None,
    contexto_extra: str = "",
) -> LandingCopy:
    """
    Genera copy completo de landing page optimizado para COD Colombia.

    Usa prompt caching en el system prompt: la primera llamada escribe al caché,
    las siguientes ahorran ~90% del costo de tokens de entrada.

    Args:
        keyword:       Nombre/keyword del producto (ej. 'faja colombiana').
        score:         Score del triangulator (0–100) — ajusta el tono del copy.
        dominios:      Lista de domain_id de ML para inferir categoría.
        contexto_extra: Info adicional del vendedor (USP, precio objetivo, etc.).

    Returns:
        LandingCopy con todos los campos listos para inyectar en la plantilla Shopify.
    """
    api_key = config("ANTHROPIC_API_KEY", default="")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY no está configurado en .env")

    client = anthropic.Anthropic(api_key=api_key)
    user_prompt = _build_user_prompt(keyword, score, dominios or [], contexto_extra)

    response = client.messages.create(
        model=_MODEL,
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = response.content[0].text
    data = _parse_json(raw_text)

    usage = response.usage
    cache_hit = getattr(usage, "cache_read_input_tokens", 0) > 0

    required = {"headline", "subheadline", "bullets", "cta_principal", "cta_secundario", "garantia", "badge_cod"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Claude omitió campos requeridos: {missing}")

    return LandingCopy(
        keyword=keyword,
        headline=data["headline"],
        subheadline=data["subheadline"],
        bullets=data["bullets"][:5],
        cta_principal=data["cta_principal"],
        cta_secundario=data["cta_secundario"],
        garantia=data["garantia"],
        badge_cod=data["badge_cod"],
        tokens_entrada=getattr(usage, "input_tokens", 0),
        tokens_salida=getattr(usage, "output_tokens", 0),
        cache_hit=cache_hit,
    )


# ── Template premium ──────────────────────────────────────────────────────────

_SYSTEM_PROMPT_PREMIUM = """\
Eres copywriter especialista en e-commerce COD (Contra Entrega) Colombia. Tu trabajo es
generar copy de alta conversión para landing pages premium de productos de belleza y cuidado
personal. Conoces a fondo la psicología del comprador colombiano digital.

PERFIL DE LA COMPRADORA COLOMBIANA:
- Mujer 25–45 años, compra desde el celular.
- Máxima objeción: "¿y si no llega?" o "¿y si no sirve?" → la modalidad COD elimina esto.
- Lenguaje: español colombiano natural. "Usted" en CTA formal, "tu" en tono cercano.
- Responde a la transformación visual y emocional, no a las especificaciones técnicas.
- Desconfía de los superlativos genéricos; confía en detalles específicos y testimonios verosímiles.
- Ciudades con mayor volumen de pedidos online: Bogotá, Medellín, Cali, Barranquilla, Bucaramanga.

ESTRUCTURA DE CONTENIDO QUE DEBES GENERAR:
1. headline: Promesa transformacional (máx 10 palabras). Sin signos de pregunta.
   Evita clichés como "el mejor", "increíble", "revolucionario".
2. subheadline: Amplía con el diferencial COD (máx 20 palabras).
   Tono cercano, como habla una amiga que ya lo usó.
3. beneficios: 5 frases de beneficio EMOCIONAL (no características técnicas).
   Sin prefijos ni emojis (el template los añade). Máx 15 palabras c/u.
   Comienzan con verbo en presente o sustantivo del beneficio tangible.
4. antes: 4 problemas reales y específicos que tenía la compradora.
   Frases cortas (< 10 palabras). Alta resonancia emocional, sin exagerar.
5. ahora: 4 soluciones directamente correspondientes a antes[].
   Mismo orden. Optimistas pero creíbles. Verbos de acción o resultado.
6. testimoniales: 3 reseñas verosímiles. Reglas:
   - nombres femeninos colombianos auténticos (no "María García", sé específica)
   - ciudades: una de Medellín, una de Bogotá, una de Cali
   - texto 30–50 palabras, lenguaje coloquial colombiano natural
   - menciona un detalle concreto del producto o resultado
   - estrellas: 5
7. cta_principal: Acción directa que refuerza el COD. Máx 6 palabras.
8. badge_cod: Texto del badge de pago contraentrega. Máx 4 palabras.

REGLAS ABSOLUTAS:
- Nunca menciones precio, marca específica ni competidores.
- No uses: "increíble", "maravilloso", "sorprendente", "revolucionario", "el mejor".
- Testimoniales: detalles específicos del producto, no genéricos.
- Responde ÚNICAMENTE con JSON válido, sin markdown, sin texto adicional.

FORMATO DE RESPUESTA (JSON estricto):
{
  "headline": "...",
  "subheadline": "...",
  "beneficios": ["...", "...", "...", "...", "..."],
  "antes": ["...", "...", "...", "..."],
  "ahora": ["...", "...", "...", "..."],
  "testimoniales": [
    {"nombre": "...", "ciudad": "Medellín", "texto": "...", "estrellas": 5},
    {"nombre": "...", "ciudad": "Bogotá",   "texto": "...", "estrellas": 5},
    {"nombre": "...", "ciudad": "Cali",     "texto": "...", "estrellas": 5}
  ],
  "cta_principal": "...",
  "badge_cod": "..."
}
"""


@dataclass
class LandingCopyPremium:
    keyword: str
    headline: str
    subheadline: str
    beneficios: list[str]
    antes: list[str]
    ahora: list[str]
    testimoniales: list[dict[str, Any]]
    cta_principal: str
    badge_cod: str
    tokens_entrada: int = 0
    tokens_salida: int = 0
    cache_hit: bool = False

    def __str__(self) -> str:
        lineas = [
            f"── LandingCopyPremium: '{self.keyword}' ──",
            f"  Headline:    {self.headline}",
            f"  Subheadline: {self.subheadline}",
            f"  Beneficios:",
            *[f"    ✦ {b}" for b in self.beneficios],
            f"  Antes/Ahora: {len(self.antes)} pares",
            f"  Testimoniales: {len(self.testimoniales)}",
            f"  Tokens: {self.tokens_entrada}↑ {self.tokens_salida}↓"
            + (" [cache hit]" if self.cache_hit else ""),
        ]
        return "\n".join(lineas)


def generar_copy_premium(keyword: str, score: float = 70.0) -> LandingCopyPremium:
    """
    Genera copy completo para el template premium COD Colombia.

    Incluye headline, subheadline, 5 beneficios emocionales, comparativa
    antes/ahora, 3 testimoniales con nombres y ciudades colombianas reales,
    CTA y badge COD.

    Args:
        keyword: Nombre/keyword del producto (ej. 'cepillo masajeador de cabello').
        score:   Score del triangulator (0–100) — ajusta el tono del copy.

    Returns:
        LandingCopyPremium listo para inyectar en renderizar_premium().
    """
    api_key = config("ANTHROPIC_API_KEY", default="")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY no está configurado en .env")

    nivel = (
        "alta demanda, alta oportunidad — usa urgencia real"
        if score >= 70
        else ("demanda media — diferencia con garantía COD" if score >= 50 else "nicho — exclusividad")
    )

    user_prompt = (
        f"Genera el copy premium para: {keyword}\n"
        f"Nivel de oportunidad: {nivel} (score: {score:.0f}/100)\n"
        "Recuerda: responde SOLO con el JSON estricto."
    )

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=_MODEL,
        max_tokens=1500,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT_PREMIUM,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text
    data = _parse_json(raw)

    required = {"headline", "subheadline", "beneficios", "antes", "ahora", "testimoniales", "cta_principal", "badge_cod"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Claude omitió campos requeridos: {missing}")

    usage = response.usage
    return LandingCopyPremium(
        keyword=keyword,
        headline=data["headline"],
        subheadline=data["subheadline"],
        beneficios=data["beneficios"][:5],
        antes=data["antes"][:4],
        ahora=data["ahora"][:4],
        testimoniales=data["testimoniales"][:3],
        cta_principal=data["cta_principal"],
        badge_cod=data["badge_cod"],
        tokens_entrada=getattr(usage, "input_tokens", 0),
        tokens_salida=getattr(usage, "output_tokens", 0),
        cache_hit=getattr(usage, "cache_read_input_tokens", 0) > 0,
    )
