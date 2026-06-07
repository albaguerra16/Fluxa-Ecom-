"""Generación de imágenes con gpt-image-2 (OpenAI 2025).

Funciones:
- generar_imagen(prompt, size) → bytes PNG
- editar_imagen(image_bytes, prompt, size) → bytes PNG
"""

from __future__ import annotations

import base64
import io
import os


_SIZE_OPTIONS = {
    "portrait": "1024x1536",   # más cercano a 1080×1600 (landing sections)
    "square":   "1024x1024",   # upsells / reseñas
    "landscape": "1536x1024",
}


def generar_imagen(prompt: str, modo: str = "portrait") -> bytes:
    """Genera imagen desde texto. Retorna bytes PNG."""
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    size = _SIZE_OPTIONS.get(modo, "1024x1536")

    resp = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        n=1,
        size=size,
        output_format="png",
    )

    b64 = resp.data[0].b64_json
    return base64.b64decode(b64)


def editar_imagen(image_bytes: bytes, prompt: str, modo: str = "square") -> bytes:
    """Edita/transforma una imagen existente con el prompt dado. Retorna bytes PNG."""
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    size = _SIZE_OPTIONS.get(modo, "1024x1024")

    buf = io.BytesIO(image_bytes)
    buf.name = "product.png"

    resp = client.images.edit(
        model="gpt-image-1",
        image=buf,
        prompt=prompt,
        n=1,
        size=size,
    )

    b64 = resp.data[0].b64_json
    return base64.b64decode(b64)


# ── Prompts prefabricados ─────────────────────────────────────────────────────

def prompt_upsell_x1(producto: str) -> str:
    return (
        f"Professional ecommerce product photography. One unit of {producto}. "
        "Pure white background #FFFFFF. HD 4K quality. Sharp focus. Professional studio lighting. "
        "Clean catalog style. DO NOT change product shape, color, label, logo, or design. "
        "Only improve image quality, lighting, and background. Centered composition."
    )


def prompt_upsell_x2(producto: str) -> str:
    return (
        f"Professional ecommerce product photography. Two identical units of {producto} side by side. "
        "Same orientation, same scale, same label. Pure white background #FFFFFF. "
        "HD 4K quality. Professional studio lighting. "
        "DO NOT change product shape, color, label, logo, or design. Centered composition."
    )


def prompt_upsell_x3(producto: str) -> str:
    return (
        f"Professional ecommerce product photography. Three identical units of {producto} arranged together. "
        "Same orientation, same scale, same label. Pure white background #FFFFFF. "
        "HD 4K quality. Professional studio lighting. "
        "DO NOT change product shape, color, label, logo, or design. Centered composition."
    )


def prompt_resena_base() -> str:
    return (
        "Ultra realistic smartphone customer review photo, natural lighting, "
        "authentic Colombian home environment, casual clothing, slight imperfections, "
        "not professional photography, realistic skin texture, realistic shadows, "
        "product recently delivered, WhatsApp-style customer photo, genuine customer experience, "
        "natural composition, believable social proof, hyperrealistic, candid moment."
    )


def prompts_resenas(producto: str, publico: str = "mujeres colombianas 25-45 años") -> list[dict]:
    base = prompt_resena_base()
    return [
        {
            "titulo": "Le llegó el pedido",
            "prompt": f"{base} Woman receiving package at door, holding {producto} box, surprised happy expression, Colombian apartment hallway, casual home clothes, delivery bag visible.",
            "objetivo": "Prueba de entrega real",
            "recomendado": "landing / Meta Ads",
        },
        {
            "titulo": "Producto en la mano",
            "prompt": f"{base} Close-up of hand holding {producto}, natural daylight from window, casual sleeve visible, Colombian home background blurred, authentic grip.",
            "objetivo": "Mostrar producto real",
            "recomendado": "Meta Ads / WhatsApp",
        },
        {
            "titulo": "Producto en uso real",
            "prompt": f"{base} {publico.capitalize()} using {producto} in everyday Colombian home setting, natural mid-action moment, casual clothing, genuine expression of satisfaction.",
            "objetivo": "Demostración cotidiana",
            "recomendado": "landing / historia Instagram",
        },
        {
            "titulo": "Foto tipo WhatsApp",
            "prompt": f"{base} Top-down flat lay photo of {producto} on wooden table or bed, slightly off-center composition like a WhatsApp photo, Colombian home objects around, natural light.",
            "objetivo": "Credibilidad máxima",
            "recomendado": "WhatsApp / historia Instagram",
        },
        {
            "titulo": "Unboxing — caja abierta",
            "prompt": f"{base} Open delivery box with {producto} inside, tissue paper, Colombian address label visible but blurred, hands reaching in, excited expression, kitchen or living room background.",
            "objetivo": "Momento de apertura",
            "recomendado": "Meta Ads / landing",
        },
    ]


def prompt_landing_seccion(seccion: str, producto: str, copy: dict) -> str:
    prompts = {
        "hero": (
            f"Premium ecommerce landing page hero section, 1080x1536px portrait format. "
            f"Product: {producto}. Headline: '{copy.get('headline', '')}'. "
            "Dark premium background, accent violet color, product as main visual hero. "
            "Modern Colombian ecommerce style, Apple-level design quality. "
            "Large product image, brand name top left, CTA button bottom, social proof badges."
        ),
        "beneficios": (
            f"Premium landing page benefits section, 1080x1536px portrait. "
            f"Product: {producto}. Title: '{copy.get('titulo', '')}'. "
            "4-6 benefit cards with icons, clean dark background, violet accents. "
            "Visual scannable layout, each benefit with icon + short title + microtext."
        ),
        "caracteristicas": (
            f"Premium product features section, 1080x1536px portrait. "
            f"Product: {producto}. Apple/Tesla/Dyson style. "
            "Large product image center, feature callouts around it with lines, "
            "dark background, premium typography. '{copy.get('titulo', '')}'."
        ),
        "comparativa": (
            f"Product comparison section, 1080x1536px portrait. "
            f"Product: {producto} vs generic competition. "
            "Clear comparison table or visual, {producto} wins all categories shown with checkmarks, "
            "dark background, premium design. '{copy.get('titulo', '')}'."
        ),
        "envios": (
            f"Shipping and COD trust section, 1080x1536px portrait. "
            f"Colombia map with delivery routes, COD badge 'Paga al Recibir', "
            "trust icons: shield, package, checkmark. Dark background. "
            "'{copy.get('titulo', '')}'. Courier logos area. Confidence-building design."
        ),
    }
    return prompts.get(seccion, prompts["hero"])
