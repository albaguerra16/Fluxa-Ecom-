"""Generador de storyboards — Director Creativo Senior COD Colombia.

8 fases: Analizar → Ángulos (10) → Mejor ángulo → Storyboard →
         Cuadros → Prompt imagen → Prompt Veo/Kling → Copy Meta A/B/C
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


@dataclass
class CuadroStoryboard:
    escena: int
    tiempo: str
    objetivo: str
    visual: str
    texto: str
    descripcion_cuadro: str  # personajes, plano, ambiente


@dataclass
class AnguloStory:
    numero: int
    nombre: str
    descripcion: str
    potencial: str  # alto / medio / bajo


@dataclass
class StoryboardCompleto:
    producto: str
    mejor_angulo: AnguloStory
    angulo_razon: str
    angulos_todos: list[AnguloStory]
    cuadros: list[CuadroStoryboard]
    prompt_imagen: str
    prompt_veo: str
    copy_a: str   # texto principal
    copy_b: str
    copy_c: str
    titulo_meta: str
    descripcion_meta: str
    cta_meta: str
    tokens_entrada: int = 0
    tokens_salida: int = 0


_SYSTEM = """Eres un Director Creativo Senior especializado en Ecommerce Performance Marketing para LATAM,
especialmente Colombia con pago contra entrega (COD).

Tu trabajo NO es crear imágenes bonitas. Tu trabajo es crear storyboards publicitarios que maximicen:
CTR, Tiempo de visualización, Tasa de reproducción, Tasa de compra, ROAS.

Piensa como un comprador impulsivo de Meta Ads.

CONTEXTO COLOMBIA COD:
- El colombiano compra por impulso pero desconfía de pagar primero
- Triggers de confianza: "contra entrega", "sin riesgo", "si no te gusta, no lo pagas"
- El "¿y si me estafan?" es la objeción #1 — neutralízala siempre
- Ciudades clave: Bogotá, Medellín, Cali, Barranquilla, Bucaramanga, Pereira
- Prioriza venta sobre estética — si se ve bonito pero no vende, descártalo"""


_PROMPT = """Producto: {producto}
{contexto}

Sigue exactamente las 8 fases del proceso y devuelve JSON puro sin markdown:

{{
  "fase1": {{
    "problema": "...",
    "deseo": "...",
    "publico": "...",
    "objeciones": ["...", "...", "..."],
    "beneficio_principal": "...",
    "factor_wow": "..."
  }},
  "fase2_angulos": [
    {{"numero": 1, "nombre": "Beneficio", "descripcion": "...", "potencial": "alto"}},
    {{"numero": 2, "nombre": "Problema-Solución", "descripcion": "...", "potencial": "alto"}},
    {{"numero": 3, "nombre": "Comparativo", "descripcion": "...", "potencial": "medio"}},
    {{"numero": 4, "nombre": "Autoridad", "descripcion": "...", "potencial": "medio"}},
    {{"numero": 5, "nombre": "Validación social", "descripcion": "...", "potencial": "alto"}},
    {{"numero": 6, "nombre": "Emocional", "descripcion": "...", "potencial": "alto"}},
    {{"numero": 7, "nombre": "Curiosidad", "descripcion": "...", "potencial": "medio"}},
    {{"numero": 8, "nombre": "Miedo", "descripcion": "...", "potencial": "medio"}},
    {{"numero": 9, "nombre": "Conveniencia", "descripcion": "...", "potencial": "medio"}},
    {{"numero": 10, "nombre": "Antes y después", "descripcion": "...", "potencial": "alto"}}
  ],
  "fase3_mejor_angulo": {{
    "numero": 1,
    "nombre": "...",
    "descripcion": "...",
    "potencial": "alto",
    "razon": "Explicación de por qué este ángulo maximiza conversión para COD Colombia"
  }},
  "fase4_storyboard": [
    {{"escena": 1, "tiempo": "0–3s",  "objetivo": "HOOK",       "visual": "...", "texto": "..."}},
    {{"escena": 2, "tiempo": "3–8s",  "objetivo": "PROBLEMA",   "visual": "...", "texto": "..."}},
    {{"escena": 3, "tiempo": "8–12s", "objetivo": "AGITACIÓN",  "visual": "...", "texto": "..."}},
    {{"escena": 4, "tiempo": "12–18s","objetivo": "SOLUCIÓN",   "visual": "...", "texto": "..."}},
    {{"escena": 5, "tiempo": "18–22s","objetivo": "DEMO",       "visual": "...", "texto": "..."}},
    {{"escena": 6, "tiempo": "22–26s","objetivo": "BENEFICIOS", "visual": "...", "texto": "..."}},
    {{"escena": 7, "tiempo": "26–29s","objetivo": "CTA",        "visual": "...", "texto": "..."}}
  ],
  "fase5_cuadros": [
    {{
      "escena": 1,
      "descripcion_cuadro": "Describe personajes (edad, expresión, acción), tipo de plano, iluminación, ambiente, producto visible"
    }},
    {{"escena": 2, "descripcion_cuadro": "..."}},
    {{"escena": 3, "descripcion_cuadro": "..."}},
    {{"escena": 4, "descripcion_cuadro": "..."}},
    {{"escena": 5, "descripcion_cuadro": "..."}},
    {{"escena": 6, "descripcion_cuadro": "..."}},
    {{"escena": 7, "descripcion_cuadro": "..."}}
  ],
  "fase6_prompt_imagen": "Prompt profesional para imagen storyboard: estilo hiperrealista, calidad comercial premium, 7 cuadros numerados, continuidad de personajes y producto, texto legible, apariencia de agencia...",
  "fase7_prompt_veo": "Prompt cinematográfico para Veo/Gemini Omni/Kling: personajes consistentes, mismo producto y ropa, iluminación consistente, formato vertical 9:16, movimiento natural, aspecto UGC hiperrealista, sin apariencia de IA...",
  "fase8_copys": {{
    "copy_a": "Texto principal A (emocional/problema)",
    "copy_b": "Texto principal B (validación social/números)",
    "copy_c": "Texto principal C (urgencia/escasez)",
    "titulo": "Título del anuncio (máx 40 chars)",
    "descripcion": "Descripción (máx 30 chars)",
    "cta": "COMPRAR_AHORA | MÁS_INFORMACIÓN | OBTENER_OFERTA"
  }}
}}"""


def generar_storyboard(producto: str, contexto: str = "") -> StoryboardCompleto:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    ctx_str = f"\nContexto adicional: {contexto}" if contexto else ""
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=[{"type": "text", "text": _SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": _PROMPT.format(
            producto=producto, contexto=ctx_str
        )}],
    )

    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    data = json.loads(raw)

    angulos = [
        AnguloStory(
            numero=a["numero"], nombre=a["nombre"],
            descripcion=a["descripcion"], potencial=a["potencial"]
        )
        for a in data["fase2_angulos"]
    ]

    ma = data["fase3_mejor_angulo"]
    mejor = AnguloStory(
        numero=ma["numero"], nombre=ma["nombre"],
        descripcion=ma["descripcion"], potencial=ma["potencial"]
    )

    sb4 = {c["escena"]: c for c in data["fase4_storyboard"]}
    sb5 = {c["escena"]: c for c in data["fase5_cuadros"]}

    cuadros = [
        CuadroStoryboard(
            escena=i,
            tiempo=sb4[i]["tiempo"],
            objetivo=sb4[i]["objetivo"],
            visual=sb4[i]["visual"],
            texto=sb4[i]["texto"],
            descripcion_cuadro=sb5[i]["descripcion_cuadro"],
        )
        for i in range(1, 8)
        if i in sb4 and i in sb5
    ]

    c = data["fase8_copys"]

    return StoryboardCompleto(
        producto=producto,
        mejor_angulo=mejor,
        angulo_razon=ma.get("razon", ""),
        angulos_todos=angulos,
        cuadros=cuadros,
        prompt_imagen=data["fase6_prompt_imagen"],
        prompt_veo=data["fase7_prompt_veo"],
        copy_a=c["copy_a"],
        copy_b=c["copy_b"],
        copy_c=c["copy_c"],
        titulo_meta=c["titulo"],
        descripcion_meta=c["descripcion"],
        cta_meta=c["cta"],
        tokens_entrada=msg.usage.input_tokens,
        tokens_salida=msg.usage.output_tokens,
    )


def generar_storyboard_demo(producto: str) -> StoryboardCompleto:
    kw = producto.split()[0].capitalize()
    angulos = [
        AnguloStory(1, "Beneficio", f"Muestra el resultado inmediato de usar {producto}", "alto"),
        AnguloStory(2, "Problema-Solución", f"¿Cansado de X? {producto} lo resuelve en días", "alto"),
        AnguloStory(3, "Comparativo", f"{producto} vs alternativas baratas — no hay comparación", "medio"),
        AnguloStory(4, "Autoridad", f"Recomendado por expertos — {producto} con respaldo", "medio"),
        AnguloStory(5, "Validación social", f"+3.000 colombianos ya usan {producto}", "alto"),
        AnguloStory(6, "Emocional", f"Porque mereces lo mejor — {producto} para ti", "alto"),
        AnguloStory(7, "Curiosidad", f"¿Sabías que el 80% usa {producto} mal?", "medio"),
        AnguloStory(8, "Miedo", f"Cada día sin {producto} es un día perdido", "medio"),
        AnguloStory(9, "Conveniencia", f"{producto} llega a tu puerta — sin salir de casa", "medio"),
        AnguloStory(10, "Antes y después", f"Tu vida antes y después de {producto}", "alto"),
    ]
    mejor = AnguloStory(5, "Validación social", f"+3.000 colombianos ya usan {producto}", "alto")
    cuadros = [
        CuadroStoryboard(1, "0–3s", "HOOK", f"Primer plano del {producto} con efecto llamativo", f"¿Ya viste esto?", f"Mujer 28 años, expresión sorprendida, plano detalle, iluminación natural, cocina colombiana, {producto} en mano"),
        CuadroStoryboard(2, "3–8s", "PROBLEMA", f"Persona frustrada intentando solución tradicional", f"Llevas meses buscando y nada funciona...", f"Hombre 35 años, expresión frustrada, plano medio, hogar modesto Medellín, sin {producto}"),
        CuadroStoryboard(3, "8–12s", "AGITACIÓN", f"Consecuencias negativas mostradas rápido", f"El tiempo corre y el problema sigue", f"Secuencia rápida, 3 clips de 1s, plano americano, iluminación fría"),
        CuadroStoryboard(4, "12–18s", "SOLUCIÓN", f"Unboxing del {producto}, empaque premium", f"Hasta que llegó esto a mi puerta...", f"Manos abriendo caja, plano detalle, iluminación cálida, mesa de madera, empaque con logo"),
        CuadroStoryboard(5, "18–22s", "DEMO", f"Uso real del {producto} mostrando resultado", f"Mira lo que pasa desde el primer uso", f"Plano americano, persona usando {producto}, resultado visible, expresión de alivio"),
        CuadroStoryboard(6, "22–26s", "BENEFICIOS", f"Texto con 3 beneficios clave superpuesto", f"✓ Resultado rápido ✓ Sin riesgo ✓ Envío gratis", f"Producto sobre fondo limpio, texto animado, colores de marca"),
        CuadroStoryboard(7, "26–29s", "CTA", f"Badge 'Paga al recibir', producto y precio", f"Pídelo hoy — pagas cuando llegue a tu puerta", f"Producto centrado, badge COD verde, precio visible, logo de marca"),
    ]
    return StoryboardCompleto(
        producto=producto,
        mejor_angulo=mejor,
        angulo_razon=f"La validación social neutraliza la desconfianza COD #1 en Colombia. +3.000 pedidos es prueba concreta que elimina el 'y si me estafan'.",
        angulos_todos=angulos,
        cuadros=cuadros,
        prompt_imagen=f"Professional advertising storyboard image, 7 numbered frames in 3x3 grid layout, hyperrealistic commercial quality, Colombian household settings, {producto} product featured prominently, consistent characters across frames, natural lighting, UGC style, readable frame numbers and duration labels, agency quality layout, white background between frames.",
        prompt_veo=f"Vertical 9:16 video ad, hyperrealistic UGC style, Colombian home environment, {producto} product, consistent female character 28 years old throughout video, casual clothing unchanged, natural handheld camera movement, authentic lighting, no AI appearance, 29 seconds, Meta Ads format, COD ecommerce Colombia.",
        copy_a=f"😱 No podía creer que esto llegara a mi casa y pagara al recibirlo...\n\nLlevaba meses buscando {producto} hasta que una amiga me lo recomendó. Llegó en 3 días y lo mejor: pagué cuando el mensajero tocó mi puerta.\n\n📦 Envío a todo Colombia\n✅ Sin pagar por adelantado\n🔒 100% garantizado\n\n👇 Pídelo hoy antes de que se acabe el stock",
        copy_b=f"📊 +3.247 colombianos pidieron {producto} este mes. ¿Por qué tanto?\n\nBogotá, Medellín, Cali, Barranquilla — en todas las ciudades está llegando.\n\nTú también puedes tenerlo hoy:\n✓ Pedido en 2 minutos\n✓ Llega en 2-5 días\n✓ Pagas cuando lo recibas\n\n👇 Haz tu pedido ahora",
        copy_c=f"⚠️ Quedan pocas unidades de {producto} en tu ciudad.\n\n{kw} está agotándose más rápido de lo que podemos reabastecer. Una vez se acabe, no sabemos cuándo vuelve.\n\n🔥 Precio especial solo por hoy\n📦 Envío gratis a tu puerta\n💳 Paga cuando llegue — sin tarjeta\n\n👇 Asegura el tuyo antes de que sea tarde",
        titulo_meta=f"{kw} Colombia — Paga al Recibir",
        descripcion_meta=f"Envío gratis · Sin riesgo",
        cta_meta="COMPRAR_AHORA",
        tokens_entrada=0,
        tokens_salida=0,
    )
