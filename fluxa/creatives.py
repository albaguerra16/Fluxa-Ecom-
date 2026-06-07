"""Generador de creatives para dropshipping COD Colombia.

Recibe el nombre del producto y devuelve:
- 3 opciones de marca
- Problemas que resuelve el producto
- 5 ángulos de venta con título, texto principal, descripción, copy Meta Ads
- Storyboard de 20 s por cada ángulo (hook 3s + desarrollo + CTA)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


# ── Estructuras de datos ──────────────────────────────────────────────────────

@dataclass
class OpcionMarca:
    nombre: str
    razon: str
    slogan: str


@dataclass
class Escena:
    tiempo: str      # ej. "0–3s"
    etiqueta: str    # HOOK, DESARROLLO, CTA
    descripcion: str # lo que se ve en pantalla
    locucion: str    # texto hablado / caption


@dataclass
class Storyboard:
    angulo: str
    duracion_total: str
    escenas: list[Escena] = field(default_factory=list)


@dataclass
class AnguloCreativo:
    tipo: str           # BENEFICIO | COMPETITIVO | VALIDACIÓN | TESTIMONIAL | EMOCIONAL
    titulo: str
    texto_principal: str
    descripcion: str
    copy_meta: str       # texto primario del anuncio Meta
    storyboard: Storyboard | None = None


@dataclass
class CreativosResultado:
    producto: str
    marcas: list[OpcionMarca]
    problemas: list[str]
    beneficios: list[str]
    angulos: list[AnguloCreativo]
    tokens_entrada: int = 0
    tokens_salida: int = 0


# ── Prompt del sistema ────────────────────────────────────────────────────────

_SYSTEM = """Eres un experto en marketing directo para dropshipping COD (pago contra entrega) en Colombia.
Tu especialidad es crear creativos de alto impacto para Meta Ads y TikTok orientados al mercado colombiano:
ciudades intermedias (Cali, Medellín, Barranquilla, Bucaramanga, Pereira), NSE C y D, adultos 25–45 años.

Siempre escribes en español colombiano coloquial, cálido y persuasivo.
El CTA siempre termina en variantes de: "Pídelo hoy · Paga cuando llegue a tu puerta".
Conoces los miedos del comprador COD: desconfianza, miedo a no recibir, percepción de baja calidad.
Tus creativos atacan esos miedos de frente y los convierten en ventajas."""


_USER_PROMPT = """Producto: {producto}

Genera una respuesta en JSON puro (sin markdown, sin texto extra) con exactamente esta estructura:

{{
  "marcas": [
    {{"nombre": "...", "razon": "...", "slogan": "..."}},
    {{"nombre": "...", "razon": "...", "slogan": "..."}},
    {{"nombre": "...", "razon": "...", "slogan": "..."}}
  ],
  "problemas": ["...", "...", "...", "...", "..."],
  "beneficios": ["...", "...", "...", "...", "..."],
  "angulos": [
    {{
      "tipo": "BENEFICIO",
      "titulo": "...",
      "texto_principal": "...",
      "descripcion": "...",
      "copy_meta": "...",
      "storyboard": {{
        "duracion_total": "20s",
        "escenas": [
          {{"tiempo": "0–3s",  "etiqueta": "HOOK",       "descripcion": "...", "locucion": "..."}},
          {{"tiempo": "3–12s", "etiqueta": "DESARROLLO", "descripcion": "...", "locucion": "..."}},
          {{"tiempo": "12–17s","etiqueta": "BENEFICIO",  "descripcion": "...", "locucion": "..."}},
          {{"tiempo": "17–20s","etiqueta": "CTA",        "descripcion": "...", "locucion": "..."}}
        ]
      }}
    }},
    {{
      "tipo": "COMPETITIVO",
      "titulo": "...",
      "texto_principal": "...",
      "descripcion": "...",
      "copy_meta": "...",
      "storyboard": {{
        "duracion_total": "20s",
        "escenas": [
          {{"tiempo": "0–3s",  "etiqueta": "HOOK",        "descripcion": "...", "locucion": "..."}},
          {{"tiempo": "3–12s", "etiqueta": "COMPARACIÓN", "descripcion": "...", "locucion": "..."}},
          {{"tiempo": "12–17s","etiqueta": "VENTAJA",     "descripcion": "...", "locucion": "..."}},
          {{"tiempo": "17–20s","etiqueta": "CTA",         "descripcion": "...", "locucion": "..."}}
        ]
      }}
    }},
    {{
      "tipo": "VALIDACIÓN",
      "titulo": "...",
      "texto_principal": "...",
      "descripcion": "...",
      "copy_meta": "...",
      "storyboard": {{
        "duracion_total": "20s",
        "escenas": [
          {{"tiempo": "0–3s",  "etiqueta": "HOOK",       "descripcion": "...", "locucion": "..."}},
          {{"tiempo": "3–12s", "etiqueta": "PRUEBA",     "descripcion": "...", "locucion": "..."}},
          {{"tiempo": "12–17s","etiqueta": "RESULTADO",  "descripcion": "...", "locucion": "..."}},
          {{"tiempo": "17–20s","etiqueta": "CTA",        "descripcion": "...", "locucion": "..."}}
        ]
      }}
    }},
    {{
      "tipo": "TESTIMONIAL",
      "titulo": "...",
      "texto_principal": "...",
      "descripcion": "...",
      "copy_meta": "...",
      "storyboard": {{
        "duracion_total": "20s",
        "escenas": [
          {{"tiempo": "0–3s",  "etiqueta": "HOOK",        "descripcion": "...", "locucion": "..."}},
          {{"tiempo": "3–12s", "etiqueta": "TESTIMONIO",  "descripcion": "...", "locucion": "..."}},
          {{"tiempo": "12–17s","etiqueta": "TRANSFORMACIÓN","descripcion": "...", "locucion": "..."}},
          {{"tiempo": "17–20s","etiqueta": "CTA",         "descripcion": "...", "locucion": "..."}}
        ]
      }}
    }},
    {{
      "tipo": "EMOCIONAL",
      "titulo": "...",
      "texto_principal": "...",
      "descripcion": "...",
      "copy_meta": "...",
      "storyboard": {{
        "duracion_total": "20s",
        "escenas": [
          {{"tiempo": "0–3s",  "etiqueta": "HOOK",       "descripcion": "...", "locucion": "..."}},
          {{"tiempo": "3–12s", "etiqueta": "EMOCIÓN",    "descripcion": "...", "locucion": "..."}},
          {{"tiempo": "12–17s","etiqueta": "CONEXIÓN",   "descripcion": "...", "locucion": "..."}},
          {{"tiempo": "17–20s","etiqueta": "CTA",        "descripcion": "...", "locucion": "..."}}
        ]
      }}
    }}
  ]
}}

Reglas:
- titulo: máx 8 palabras, impactante
- texto_principal: 2–3 oraciones, persuasivo, habla directo al cliente
- descripcion: 1 oración que explica el ángulo
- copy_meta: texto primario del anuncio listo para pegar en Meta Ads, 3–5 oraciones, emojis moderados, CTA COD al final
- storyboard escenas:
  * Hook 0–3s: pregunta o afirmación que genere impresión inmediata, ataca un problema real
  * Desarrollo (3–17s): muestra el producto, solución, prueba o emoción según el ángulo
  * CTA 17–20s: siempre termina con pago contra entrega y urgencia suave
- descripcion del storyboard: lo que se VE en pantalla (visual)
- locucion: lo que se DICE / aparece como caption"""


# ── Generador ────────────────────────────────────────────────────────────────

def _llamar_claude(system: str, user: str, max_tokens: int = 4096) -> tuple[str, int, int]:
    """Llama a Anthropic via HTTP directo (sin SDK). Retorna (texto, tokens_in, tokens_out)."""
    import httpx

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no está configurada en Railway Variables")

    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    with httpx.Client(timeout=httpx.Timeout(120.0, connect=20.0), verify=True) as client:
        resp = client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
        )

    if resp.status_code == 401:
        raise ValueError("ANTHROPIC_API_KEY inválida o expirada. Verifica en console.anthropic.com")
    if resp.status_code != 200:
        raise ValueError(f"Anthropic respondió {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    text = data["content"][0]["text"]
    usage = data.get("usage", {})
    return text, usage.get("input_tokens", 0), usage.get("output_tokens", 0)


def generar_creatives(producto: str) -> CreativosResultado:
    raw, tok_in, tok_out = _llamar_claude(_SYSTEM, _USER_PROMPT.format(producto=producto))
    raw = raw.strip()

    # Limpiar posible markdown code fence
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    data = json.loads(raw)

    marcas = [OpcionMarca(**m) for m in data["marcas"]]
    problemas = data["problemas"]
    beneficios = data["beneficios"]

    angulos: list[AnguloCreativo] = []
    for a in data["angulos"]:
        sb_data = a.get("storyboard")
        sb = None
        if sb_data:
            escenas = [Escena(**e) for e in sb_data["escenas"]]
            sb = Storyboard(
                angulo=a["tipo"],
                duracion_total=sb_data.get("duracion_total", "20s"),
                escenas=escenas,
            )
        angulos.append(
            AnguloCreativo(
                tipo=a["tipo"],
                titulo=a["titulo"],
                texto_principal=a["texto_principal"],
                descripcion=a["descripcion"],
                copy_meta=a["copy_meta"],
                storyboard=sb,
            )
        )

    return CreativosResultado(
        producto=producto,
        marcas=marcas,
        problemas=problemas,
        beneficios=beneficios,
        angulos=angulos,
        tokens_entrada=tok_in,
        tokens_salida=tok_out,
    )


# ── Demo / dry-run ────────────────────────────────────────────────────────────

def generar_creatives_demo(producto: str) -> CreativosResultado:
    """Devuelve datos simulados sin llamar a la API."""
    kw = producto.split()[0].capitalize()
    marcas = [
        OpcionMarca(f"{kw}Pro", "Proyecta calidad y profesionalismo", f"El {producto} que Colombia necesitaba"),
        OpcionMarca(f"{kw}Lab", "Evoca ciencia y resultados probados", f"Resultados reales, envío a tu puerta"),
        OpcionMarca(f"Nova{kw}", "Nuevo, moderno, aspiracional", f"La nueva forma de vivir mejor"),
    ]
    problemas = [
        f"Pérdida de tiempo buscando solución para {producto}",
        "Gasto innecesario en productos que no funcionan",
        "Inseguridad al comprar online sin garantía",
        "Falta de opciones accesibles en tiendas físicas",
        "Resultados inconsistentes con alternativas baratas",
    ]
    beneficios = [
        f"{producto} de alta calidad a precio justo",
        "Pago contra entrega — pagas solo si te gusta",
        "Envío a todo Colombia en 2–5 días hábiles",
        "Garantía de satisfacción incluida",
        "Miles de colombianos ya lo usan con resultados reales",
    ]
    angulos_demo = [
        AnguloCreativo(
            tipo="BENEFICIO",
            titulo=f"{producto}: Resultados desde el primer uso",
            texto_principal=f"Descubrí que el verdadero problema no era falta de disciplina, era no tener el {producto} correcto. Desde el primer día noté la diferencia. Hoy no puedo imaginar mi rutina sin él.",
            descripcion="Resalta el beneficio tangible e inmediato del producto",
            copy_meta=f"✅ ¿Cansado de buscar sin encontrar? El {producto} que miles de colombianos ya usan llegó a ti.\n\n¿Lo mejor? Pagas SOLO cuando te llegue a casa. Sin riesgo. Sin estrés.\n\n📦 Envío a todo Colombia · Garantía total\n\n👇 Pídelo hoy y paga al recibirlo",
            storyboard=Storyboard(
                angulo="BENEFICIO",
                duracion_total="20s",
                escenas=[
                    Escena("0–3s", "HOOK", f"Primer plano del {producto} siendo usado con resultado inmediato visible", f"¿Sabías que el 80% de la gente usa {producto} mal?"),
                    Escena("3–12s", "DESARROLLO", f"Demostración paso a paso del {producto}: antes vs después, manos usando el producto", f"Con {producto} correcto los resultados se ven desde el primer día. Mira…"),
                    Escena("12–17s", "BENEFICIO", "Persona sonriendo con el resultado final, texto con beneficios en pantalla", f"Más de 3.000 colombianos ya cambiaron su rutina con {kw}Pro"),
                    Escena("17–20s", "CTA", "Producto sobre fondo limpio, logo de marca, badge 'Paga al recibir'", "Pídelo hoy. Llega a tu puerta. Pagas solo cuando lo tengas en manos. ¡Quedan pocas unidades!"),
                ],
            ),
        ),
        AnguloCreativo(
            tipo="COMPETITIVO",
            titulo=f"Por qué {producto} supera a la competencia",
            texto_principal=f"En el mercado hay decenas de opciones. Pero solo una llegará directo a tu puerta con garantía real. El {producto} que estás viendo no lo encontrarás en tiendas.",
            descripcion="Diferenciación frente a alternativas del mercado",
            copy_meta=f"🔥 El {producto} que NO venden en tiendas.\n\nMientras otros se conforman con lo que hay, tú puedes tener el mejor.\n\n📦 Directo a tu casa en todo Colombia\n💳 Pagas cuando llegue — sin tarjeta, sin apps\n\n👇 Ordena ahora antes de que se acabe el stock",
            storyboard=Storyboard(
                angulo="COMPETITIVO",
                duracion_total="20s",
                escenas=[
                    Escena("0–3s", "HOOK", "Comparación visual: producto genérico vs este producto, calidad evidente", f"Esto es lo que compras en tienda… y esto es {kw}Pro"),
                    Escena("3–12s", "COMPARACIÓN", "Split screen mostrando diferencias clave, texto con comparativa", "Materiales mejores. Resultados visibles. Precio justo. No hay comparación."),
                    Escena("12–17s", "VENTAJA", "Unboxing del producto con packaging premium, reacción positiva", f"Y llega a tu puerta en Colombia en días, no semanas"),
                    Escena("17–20s", "CTA", "Logo, precio, badge COD", "El mejor {producto} del mercado. Tuyo hoy, pagas al recibirlo."),
                ],
            ),
        ),
        AnguloCreativo(
            tipo="VALIDACIÓN",
            titulo=f"Miles ya lo compraron — ¿Tú esperas qué?",
            texto_principal=f"+3.000 pedidos entregados en Colombia. Los números no mienten: el {producto} que estás viendo tiene resultados reales de personas reales. No es publicidad, es evidencia.",
            descripcion="Prueba social y validación con datos reales",
            copy_meta=f"📊 +3.000 colombianos ya recibieron su {producto} y están felices.\n\nNo lo decimos nosotros — lo dicen sus reseñas de 5 estrellas ⭐⭐⭐⭐⭐\n\n✅ Envío garantizado · Pago al recibir · Sin riesgo\n\n👇 Únete hoy — quedan unidades disponibles",
            storyboard=Storyboard(
                angulo="VALIDACIÓN",
                duracion_total="20s",
                escenas=[
                    Escena("0–3s", "HOOK", "Número grande en pantalla: 3.000+ pedidos, mapa de Colombia con puntos de entrega", "3.247 colombianos pidieron esto este mes…"),
                    Escena("3–12s", "PRUEBA", "Screenshots reales de reseñas, fotos de clientes con el producto", "Y todos dicen lo mismo: 'Ojalá lo hubiera pedido antes'"),
                    Escena("12–17s", "RESULTADO", "Testimonios rápidos 2–3 segundos cada uno, nombres y ciudades colombianas", "Bogotá, Medellín, Cali, Barranquilla — resultados en todo el país"),
                    Escena("17–20s", "CTA", "Producto con badge de bestseller, badge COD", "Sé el próximo. Pídelo hoy y paga al recibirlo."),
                ],
            ),
        ),
        AnguloCreativo(
            tipo="TESTIMONIAL",
            titulo=f"Ella no creía — hasta que lo usó",
            texto_principal=f"'Yo era súper desconfiada con comprar online. Pero como pagaba al recibir, dije — pruebo. Y fue la mejor decisión. El {producto} llegó en 3 días y superó mis expectativas.' — María, Medellín",
            descripcion="Historia real de transformación de cliente colombiana",
            copy_meta=f"'No creía que comprar online fuera seguro… hasta que llegó mi {producto} y pagué en la puerta de mi casa' 😱\n\nAsí es como funciona: lo pides, llega, lo revisas, pagas. Sin sorpresas.\n\n📦 Envío a todo Colombia\n✅ Garantía total de satisfacción\n\n👇 Tú también puedes. Pídelo hoy",
            storyboard=Storyboard(
                angulo="TESTIMONIAL",
                duracion_total="20s",
                escenas=[
                    Escena("0–3s", "HOOK", "Mujer colombiana a cámara, expresión de sorpresa genuina", "'Yo no le creí cuando me lo recomendaron...'"),
                    Escena("3–12s", "TESTIMONIO", "Video UGC: unboxing, usando el producto, mostrando resultado a cámara", "'Llegó súper rápido, el packaging estaba genial y pagué cuando el mensajero llegó'"),
                    Escena("12–17s", "TRANSFORMACIÓN", "Antes/después, sonrisa, pulgar arriba, nombre y ciudad en pantalla", "'Lo mejor fue el resultado desde el primer día. ¡Lo recomiendo 100%!' — María, Medellín"),
                    Escena("17–20s", "CTA", "Badge 'Paga al recibir', número de WhatsApp o link", "Tú también puedes. Pídelo hoy, sin riesgo."),
                ],
            ),
        ),
        AnguloCreativo(
            tipo="EMOCIONAL",
            titulo=f"Mereces sentirte bien todos los días",
            texto_principal=f"No es un lujo. Es lo que mereces. El {producto} que te da esa confianza extra, esa seguridad, ese bienestar que has estado buscando. Porque cuidarte no debería ser complicado.",
            descripcion="Conexión emocional con el deseo de bienestar y autoestima",
            copy_meta=f"💜 Porque tú mereces sentirte bien todos los días.\n\nNo esperes a la próxima ocasión. El {producto} que te cambia el día llegó a Colombia.\n\n✨ Pídelo hoy · Lo recibes en casa · Pagas al recibirlo\n\n👇 Date ese gusto — lo mereces",
            storyboard=Storyboard(
                angulo="EMOCIONAL",
                duracion_total="20s",
                escenas=[
                    Escena("0–3s", "HOOK", "Mujer mirándose al espejo con inseguridad, transición a seguridad y sonrisa", "¿Cuánto tiempo llevas posponiendo cuidarte?"),
                    Escena("3–12s", "EMOCIÓN", "Lifestyle: mañana tranquila, usando el producto, música suave, luz cálida", f"El {producto} no es un gasto. Es una inversión en ti misma."),
                    Escena("12–17s", "CONEXIÓN", "Primer plano de expresión de bienestar y confianza, texto motivacional", "Porque cuando te ves bien, te sientes bien. Y cuando te sientes bien, todo cambia."),
                    Escena("17–20s", "CTA", "Producto sobre fondo suave, texto 'Paga al recibir', ambiente cálido", "Pídelo hoy. Llega a tu puerta. Pagas cuando llegue. Te lo mereces."),
                ],
            ),
        ),
    ]

    return CreativosResultado(
        producto=producto,
        marcas=marcas,
        problemas=problemas,
        beneficios=beneficios,
        angulos=angulos_demo,
        tokens_entrada=0,
        tokens_salida=0,
    )
