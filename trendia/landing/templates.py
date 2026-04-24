"""Plantillas Jinja2 para generar el body_html de páginas Shopify.

El HTML resultante se inyecta directamente en body_html del endpoint
/pages.json — sin dependencia de secciones del tema activo. Usa inline CSS
para máxima compatibilidad entre temas. Diseño mobile-first para el
comprador colombiano (>70% tráfico desde móvil).
"""

from __future__ import annotations

from dataclasses import dataclass

from jinja2 import BaseLoader, Environment

from trendia.landing.generator import LandingCopy

# ── Template HTML ─────────────────────────────────────────────────────────────

_LANDING_HTML = """\
<div class="tnd-landing" style="
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  max-width: 680px;
  margin: 0 auto;
  padding: 16px;
  color: #1a1a1a;
  line-height: 1.5;
">

  {# ── Badge COD ── #}
  <div style="
    background: #0a7c42;
    color: #fff;
    text-align: center;
    padding: 10px 16px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 15px;
    letter-spacing: 0.5px;
    margin-bottom: 20px;
  ">
    🔒 {{ copy.badge_cod | upper }}
  </div>

  {# ── Imagen del producto ── #}
  {% if imagen_url %}
  <div style="text-align: center; margin-bottom: 20px;">
    <img
      src="{{ imagen_url }}"
      alt="{{ copy.keyword }}"
      style="max-width: 100%; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,.12);"
    />
  </div>
  {% endif %}

  {# ── Headline ── #}
  <h1 style="
    font-size: clamp(22px, 5vw, 34px);
    font-weight: 800;
    line-height: 1.2;
    margin: 0 0 10px;
    color: #111;
  ">{{ copy.headline }}</h1>

  {# ── Subheadline ── #}
  <p style="
    font-size: clamp(15px, 3.5vw, 18px);
    color: #444;
    margin: 0 0 24px;
  ">{{ copy.subheadline }}</p>

  {# ── Bullets de beneficios ── #}
  <ul style="
    list-style: none;
    padding: 0;
    margin: 0 0 28px;
    background: #f7f9fc;
    border-radius: 10px;
    padding: 16px 20px;
  ">
    {% for bullet in copy.bullets %}
    <li style="
      padding: 8px 0;
      font-size: 15px;
      {% if not loop.last %}border-bottom: 1px solid #e8ecf0;{% endif %}
    ">{{ bullet }}</li>
    {% endfor %}
  </ul>

  {# ── CTA principal ── #}
  <a href="#product-form" style="
    display: block;
    background: #e85d04;
    color: #fff;
    text-align: center;
    padding: 18px 24px;
    border-radius: 10px;
    font-size: clamp(16px, 4vw, 20px);
    font-weight: 800;
    text-decoration: none;
    margin-bottom: 12px;
    box-shadow: 0 4px 14px rgba(232,93,4,.35);
    letter-spacing: 0.3px;
  ">{{ copy.cta_principal }}</a>

  {# ── CTA urgencia ── #}
  <p style="
    text-align: center;
    font-size: 14px;
    color: #c0392b;
    font-weight: 700;
    margin: 0 0 28px;
  ">⚡ {{ copy.cta_secundario }}</p>

  {# ── Banner de garantía ── #}
  <div style="
    border: 2px solid #0a7c42;
    border-radius: 10px;
    padding: 14px 18px;
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 24px;
    background: #f0faf5;
  ">
    <span style="font-size: 26px; line-height: 1; flex-shrink: 0;">🛡️</span>
    <p style="margin: 0; font-size: 14px; color: #1a5c35; font-weight: 600;">
      {{ copy.garantia }}
    </p>
  </div>

  {# ── Footer de confianza ── #}
  <div style="
    text-align: center;
    color: #888;
    font-size: 12px;
    border-top: 1px solid #eee;
    padding-top: 16px;
  ">
    <span style="margin: 0 8px;">🔒 Pago seguro</span>
    <span style="margin: 0 8px;">📦 Envío a todo Colombia</span>
    <span style="margin: 0 8px;">↩️ Devolución fácil</span>
  </div>

</div>
"""


# ── Dataclass de salida ───────────────────────────────────────────────────────

@dataclass
class LandingHTML:
    keyword: str
    html: str
    imagen_url: str

    def preview(self, chars: int = 300) -> str:
        return self.html[:chars] + ("…" if len(self.html) > chars else "")


# ── Función pública ───────────────────────────────────────────────────────────

_env = Environment(loader=BaseLoader(), autoescape=True)


def renderizar(copy: LandingCopy, imagen_url: str = "") -> LandingHTML:
    """
    Renderiza el copy en HTML listo para inyectar en Shopify body_html.

    Args:
        copy:       LandingCopy generado por generator.generar_copy().
        imagen_url: URL de imagen del producto. Si está vacía, se omite el bloque.

    Returns:
        LandingHTML con el HTML completo y metadatos.
    """
    tmpl = _env.from_string(_LANDING_HTML)
    html = tmpl.render(copy=copy, imagen_url=imagen_url)
    return LandingHTML(keyword=copy.keyword, html=html, imagen_url=imagen_url)
