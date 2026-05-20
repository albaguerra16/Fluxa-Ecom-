"""Plantillas Jinja2 para generar el body_html de páginas Shopify.

El HTML resultante se inyecta directamente en body_html del endpoint
/pages.json — sin dependencia de secciones del tema activo. Usa inline CSS
para máxima compatibilidad entre temas. Diseño mobile-first para el
comprador colombiano (>70% tráfico desde móvil).
"""

from __future__ import annotations

from dataclasses import dataclass

from jinja2 import BaseLoader, Environment

from trendia.landing.generator import LandingCopy, LandingCopyPremium

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

  {# ── Formulario Releasit COD ──────────────────────────────────────────────────
     Requiere:
       1. App Embed "Releasit COD Form" activado en el tema de Shopify.
       2. Opción "Show on all pages" habilitada en ajustes de Releasit.
       3. product_handle debe coincidir con el handle del producto en Shopify
          (no el handle de esta página).
  ── #}
  {% if product_handle %}
  <div id="product-form" style="
    margin: 0 0 28px;
    padding: 20px;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,.08);
  ">
    <div
      data-releasit-form
      data-product-handle="{{ product_handle }}"
    ></div>
  </div>
  {% else %}
  {# Fallback: anchor vacío para que el CTA no rompa el scroll #}
  <div id="product-form"></div>
  {% endif %}

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


def renderizar(
    copy: LandingCopy,
    imagen_url: str = "",
    product_handle: str = "",
) -> LandingHTML:
    """
    Renderiza el copy en HTML listo para inyectar en Shopify body_html.

    Args:
        copy:           LandingCopy generado por generator.generar_copy().
        imagen_url:     URL de imagen del producto. Si está vacía, se omite el bloque.
        product_handle: Handle del producto en Shopify (ej. "cepillo-masajeador").
                        Si se provee, activa el bloque del formulario Releasit COD.
                        Debe coincidir con el handle del producto, no el de la página.

    Returns:
        LandingHTML con el HTML completo y metadatos.
    """
    tmpl = _env.from_string(_LANDING_HTML)
    html = tmpl.render(copy=copy, imagen_url=imagen_url, product_handle=product_handle)
    return LandingHTML(keyword=copy.keyword, html=html, imagen_url=imagen_url)


# ── Template Premium v3 (Conversion-Optimized · azul oscuro #0A1628) ─────────
# Design system: Social Proof-Focused + Dark Mode · Rubik/Nunito Sans
# Mejoras v3: hero gradient, countdown prominente, stat counter animado,
#   stock progress bar, section pills, testimonials con quote SVG,
#   footer grid 3 col, sticky CTA con pulse animation.

_PREMIUM_HTML = """\
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700;800&family=Rubik:wght@500;700;800;900&display=swap');
#tnd-p *{box-sizing:border-box;margin:0;padding:0}
#tnd-p{font-family:'Nunito Sans',-apple-system,BlinkMacSystemFont,sans-serif;overflow:hidden}
#tnd-p h1,#tnd-p h2{font-family:'Rubik',-apple-system,sans-serif}
@keyframes tnd-pulse{0%,100%{box-shadow:0 4px 20px rgba(249,115,22,.45)}50%{box-shadow:0 6px 36px rgba(249,115,22,.75),0 0 0 4px rgba(249,115,22,.15)}}
@media(prefers-reduced-motion:reduce){ #tnd-p *{animation:none!important;transition:none!important} }
</style>

<div id="tnd-p" style="max-width:680px;margin:0 auto;background:#0A1628;color:#fff;">

{# ══ 1. HERO ══ #}
<section style="padding:24px 20px 36px;background:linear-gradient(160deg,#0D1E3A 0%,#0A1628 55%,#071020 100%);">

  {# Badge COD #}
  <div style="display:inline-flex;align-items:center;gap:6px;background:#1A56DB;color:#fff;font-size:11px;font-weight:700;letter-spacing:1.5px;padding:6px 14px;border-radius:20px;margin-bottom:16px;">
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
    {{ copy.badge_cod | upper }}
  </div>

  {# Countdown prominente #}
  <div style="background:rgba(26,86,219,.15);border:1px solid rgba(26,86,219,.4);border-radius:12px;padding:14px 18px;margin-bottom:22px;display:flex;align-items:center;gap:14px;">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#93B4D4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="flex-shrink:0"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
    <div style="flex:1;">
      <div style="font-size:10px;color:#93B4D4;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">Oferta termina en</div>
      <span id="tnd-cd" style="font-size:30px;font-weight:900;color:#fff;font-variant-numeric:tabular-nums;letter-spacing:3px;font-family:'Rubik',sans-serif;line-height:1;" aria-live="polite">23:47:12</span>
    </div>
    <div style="text-align:center;background:rgba(249,115,22,.15);border:1px solid rgba(249,115,22,.35);border-radius:8px;padding:8px 12px;">
      <div style="font-size:10px;color:#F97316;font-weight:700;letter-spacing:0.5px;">PRECIO</div>
      <div style="font-size:10px;color:#F97316;font-weight:700;letter-spacing:0.5px;">ESPECIAL</div>
    </div>
  </div>

  {# Imagen del producto #}
  {% if imagen_url %}
  <div style="text-align:center;margin-bottom:22px;">
    <img src="{{ imagen_url }}" alt="{{ copy.keyword }}" loading="lazy"
      style="max-width:100%;border-radius:16px;max-height:300px;object-fit:contain;box-shadow:0 8px 32px rgba(26,86,219,.3);" />
  </div>
  {% endif %}

  {# Headline #}
  <h1 style="font-size:clamp(26px,6.5vw,40px);font-weight:900;line-height:1.15;margin-bottom:12px;color:#fff;letter-spacing:-0.5px;">{{ copy.headline }}</h1>

  {# Subheadline #}
  <p style="font-size:clamp(15px,3.5vw,17px);color:#93B4D4;margin-bottom:24px;line-height:1.65;">{{ copy.subheadline }}</p>

  {# Social proof — grid con stat counter animado #}
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
    <div style="background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.09);border-radius:12px;padding:14px 16px;">
      <div id="tnd-counter" style="font-size:24px;font-weight:800;color:#fff;font-family:'Rubik',sans-serif;line-height:1;margin-bottom:4px;" aria-live="polite">2.847</div>
      <div style="font-size:12px;color:#93B4D4;display:flex;align-items:center;gap:5px;">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        pedidos este mes
      </div>
    </div>
    <div style="background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.09);border-radius:12px;padding:14px 16px;">
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
        <span style="color:#FBBF24;font-size:16px;letter-spacing:2px;line-height:1;" aria-label="5 de 5 estrellas">★★★★★</span>
      </div>
      <div style="font-size:12px;color:#93B4D4;">4.9 de 5 · 318 reseñas</div>
    </div>
  </div>

</section>

{# ══ 2. BARRA DE URGENCIA + STOCK PROGRESS ══ #}
<div role="status" style="background:#1A56DB;color:#fff;padding:14px 20px;">
  <div style="display:flex;align-items:center;justify-content:center;gap:8px;font-size:14px;font-weight:700;letter-spacing:0.2px;margin-bottom:10px;">
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>
    Solo {{ stock }} unidades disponibles · {{ viendo }} personas viendo ahora
  </div>
  <div style="background:rgba(255,255,255,.25);border-radius:4px;height:6px;overflow:hidden;" aria-hidden="true">
    <div id="tnd-stock-bar" style="height:100%;border-radius:4px;background:#fff;width:0%;transition:width 1.4s cubic-bezier(.25,.46,.45,.94);"></div>
  </div>
</div>

{# ══ 3. BENEFICIOS ══ #}
<section style="background:#fff;color:#1a1a1a;padding:36px 20px;">
  <div style="text-align:center;margin-bottom:24px;">
    <div style="display:inline-flex;align-items:center;gap:5px;background:#EBF2FF;color:#1A56DB;font-size:10px;font-weight:800;letter-spacing:1.2px;padding:5px 14px;border-radius:20px;margin-bottom:10px;text-transform:uppercase;">Beneficios</div>
    <h2 style="font-size:22px;font-weight:800;color:#0A1628;line-height:1.3;">¿Por qué miles de colombianas<br>lo eligen?</h2>
  </div>
  <ul style="list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:10px;">
    {% for b in copy.beneficios %}
    <li style="display:flex;align-items:flex-start;gap:14px;font-size:15px;line-height:1.6;color:#222;padding:14px 16px;background:#F7FAFF;border-radius:10px;border-left:3px solid #1A56DB;">
      <span style="color:#1A56DB;flex-shrink:0;margin-top:2px;" aria-hidden="true">
        <svg width="17" height="17" viewBox="0 0 17 17" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="2,8.5 6.5,13 15,4"/></svg>
      </span>
      <span>{{ b }}</span>
    </li>
    {% endfor %}
  </ul>
</section>

{# ══ 4. ANTES / AHORA ══ #}
<section style="background:#EBF2FF;padding:36px 20px;color:#1a1a1a;">
  <div style="text-align:center;margin-bottom:22px;">
    <div style="display:inline-flex;align-items:center;gap:5px;background:#DDE8FF;color:#1A56DB;font-size:10px;font-weight:800;letter-spacing:1.2px;padding:5px 14px;border-radius:20px;margin-bottom:10px;text-transform:uppercase;">Transformación</div>
    <h2 style="font-size:22px;font-weight:800;color:#0A1628;line-height:1.3;">El cambio que vas a notar</h2>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">

    {# Columna Antes #}
    <div style="background:#fff;border-radius:12px;padding:16px;border:1px solid #D1DCF0;">
      <div style="font-size:10px;font-weight:800;color:#8899BB;letter-spacing:1.5px;margin-bottom:12px;text-align:center;text-transform:uppercase;">Antes</div>
      <ul style="list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:9px;">
        {% for a in copy.antes %}
        <li style="font-size:13px;color:#555;display:flex;align-items:flex-start;gap:7px;line-height:1.5;">
          <span style="color:#e74c3c;flex-shrink:0;margin-top:2px;" aria-hidden="true">
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><line x1="2.5" y1="2.5" x2="10.5" y2="10.5"/><line x1="10.5" y1="2.5" x2="2.5" y2="10.5"/></svg>
          </span>
          {{ a }}
        </li>
        {% endfor %}
      </ul>
    </div>

    {# Columna Ahora #}
    <div style="background:#fff;border-radius:12px;padding:16px;border:2px solid #1A56DB;">
      <div style="font-size:10px;font-weight:800;color:#1A56DB;letter-spacing:1.5px;margin-bottom:12px;text-align:center;text-transform:uppercase;">Con el cepillo</div>
      <ul style="list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:9px;">
        {% for n in copy.ahora %}
        <li style="font-size:13px;color:#222;display:flex;align-items:flex-start;gap:7px;line-height:1.5;">
          <span style="color:#1A56DB;flex-shrink:0;margin-top:2px;" aria-hidden="true">
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="1.5,7 5,10.5 11.5,2.5"/></svg>
          </span>
          {{ n }}
        </li>
        {% endfor %}
      </ul>
    </div>

  </div>
</section>

{# ══ 5. FORMULARIO RELEASIT ══ #}
<section id="product-form" style="background:#fff;padding:36px 20px;color:#1a1a1a;">
  <div style="text-align:center;margin-bottom:22px;">
    <div style="display:inline-flex;align-items:center;gap:5px;background:#EBF2FF;color:#1A56DB;font-size:10px;font-weight:800;letter-spacing:1.2px;padding:5px 14px;border-radius:20px;margin-bottom:10px;text-transform:uppercase;">Pedido Seguro</div>
    <h2 style="font-size:22px;font-weight:800;color:#0A1628;line-height:1.3;margin-bottom:8px;">Pide el tuyo ahora</h2>
    <p style="font-size:14px;color:#666;line-height:1.55;">Completa tus datos · Pagas solo cuando llegue a tu puerta</p>
  </div>
  <div style="display:flex;align-items:center;justify-content:center;gap:7px;margin-bottom:22px;font-size:13px;color:#1A56DB;font-weight:700;background:#EBF2FF;padding:11px 18px;border-radius:10px;">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
    Pago 100% seguro — sin tarjeta de crédito
  </div>
  {% if product_handle %}
  <div data-releasit-form data-product-handle="{{ product_handle }}"></div>
  {% else %}
  <div style="background:#F0F5FF;border:2px dashed #1A56DB;border-radius:10px;padding:24px;text-align:center;color:#1A56DB;font-size:14px;font-weight:600;">[ Formulario Releasit — configura product_handle ]</div>
  {% endif %}
</section>

{# ══ 6. TESTIMONIOS ══ #}
<section style="background:#0A1628;padding:36px 20px;">
  <div style="text-align:center;margin-bottom:24px;">
    <div style="display:inline-flex;align-items:center;gap:5px;background:rgba(26,86,219,.2);color:#93B4D4;font-size:10px;font-weight:800;letter-spacing:1.2px;padding:5px 14px;border-radius:20px;margin-bottom:10px;text-transform:uppercase;">Testimonios Reales</div>
    <h2 style="font-size:22px;font-weight:800;color:#fff;line-height:1.3;">Lo que dicen nuestras clientas</h2>
  </div>
  <div style="display:flex;flex-direction:column;gap:14px;">
    {% for t in copy.testimoniales %}
    <div style="background:#0F2040;border-radius:12px;padding:20px;border:1px solid rgba(26,86,219,.3);position:relative;overflow:hidden;">
      {# Decorative quote mark #}
      <div style="position:absolute;top:14px;right:16px;opacity:0.1;" aria-hidden="true">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="#93B4D4"><path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z"/></svg>
      </div>
      <div style="color:#FBBF24;font-size:16px;margin-bottom:10px;letter-spacing:2px;" aria-label="{{ t.estrellas }} de 5 estrellas">
        {% for _ in range(t.estrellas) %}★{% endfor %}
      </div>
      <p style="font-size:14px;color:#CBD8E8;margin-bottom:16px;line-height:1.65;font-style:italic;">"{{ t.texto }}"</p>
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#1A56DB,#3B82F6);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:14px;font-weight:800;color:#fff;font-family:'Rubik',sans-serif;" aria-hidden="true">{{ t.nombre[0] }}</div>
        <div>
          <div style="font-size:13px;color:#fff;font-weight:700;">{{ t.nombre }}</div>
          <div style="font-size:12px;color:#5A7A9A;">{{ t.ciudad }}, Colombia · Compra verificada</div>
        </div>
      </div>
    </div>
    {% endfor %}
  </div>
</section>

{# ══ 7. FOOTER CONFIANZA ══ #}
<section style="background:#060E1C;padding:28px 20px;">
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:20px;">
    <div style="text-align:center;padding:16px 8px;background:rgba(255,255,255,.04);border-radius:12px;border:1px solid rgba(255,255,255,.07);">
      <div style="margin-bottom:8px;display:flex;justify-content:center;">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1A56DB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
      </div>
      <div style="font-size:11px;color:#93B4D4;font-weight:700;line-height:1.5;">Pago 100%<br>Seguro</div>
    </div>
    <div style="text-align:center;padding:16px 8px;background:rgba(255,255,255,.04);border-radius:12px;border:1px solid rgba(255,255,255,.07);">
      <div style="margin-bottom:8px;display:flex;justify-content:center;">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1A56DB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="1" y="3" width="15" height="13" rx="2"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>
      </div>
      <div style="font-size:11px;color:#93B4D4;font-weight:700;line-height:1.5;">Envío Gratis<br>Colombia</div>
    </div>
    <div style="text-align:center;padding:16px 8px;background:rgba(255,255,255,.04);border-radius:12px;border:1px solid rgba(255,255,255,.07);">
      <div style="margin-bottom:8px;display:flex;justify-content:center;">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1A56DB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
      </div>
      <div style="font-size:11px;color:#93B4D4;font-weight:700;line-height:1.5;">Garantía<br>30 días</div>
    </div>
  </div>
  <p style="font-size:12px;color:#3A5070;line-height:1.6;text-align:center;">Pagas solo cuando el producto llegue a tu puerta. Sin tarjeta. Sin riesgo.</p>
</section>

</div>

{# ══ STICKY CTA — se oculta cuando el form está visible ══ #}
<div id="tnd-sticky" style="position:fixed;bottom:0;left:0;right:0;z-index:50;padding:12px 16px 20px;background:linear-gradient(to bottom,rgba(6,14,28,0) 0%,rgba(6,14,28,.97) 30%,#060E1C 100%);pointer-events:none;">
  <div style="max-width:680px;margin:0 auto;">
    <a href="#product-form" style="display:block;background:linear-gradient(135deg,#F97316,#EA580C);color:#fff;text-align:center;padding:17px 24px;border-radius:14px;font-size:17px;font-weight:800;text-decoration:none;pointer-events:auto;cursor:pointer;letter-spacing:0.2px;transition:opacity 150ms;animation:tnd-pulse 2.2s ease-in-out infinite;font-family:'Rubik',sans-serif;">{{ copy.cta_principal }}</a>
  </div>
</div>

<script>
(function(){
  /* Countdown — persiste en localStorage para no reiniciar en cada visita */
  var KEY='tnd_cd_v3';
  var SECS=23*3600+47*60+12;
  var stored=localStorage.getItem(KEY);
  var end=stored?parseInt(stored,10):Date.now()+SECS*1000;
  if(!stored) localStorage.setItem(KEY,end);
  var cdEl=document.getElementById('tnd-cd');
  if(cdEl){
    function tick(){
      var r=Math.max(0,Math.floor((end-Date.now())/1000));
      var h=Math.floor(r/3600),m=Math.floor(r%3600/60),s=r%60;
      cdEl.textContent=[h,m,s].map(function(v){return('0'+v).slice(-2)}).join(':');
      if(r>0) setTimeout(tick,1000);
    }
    tick();
  }
  /* Stock progress bar — anima al cargar */
  var bar=document.getElementById('tnd-stock-bar');
  if(bar) setTimeout(function(){bar.style.width='{{ (stock / 20 * 100)|int }}%';},500);
  /* Count-up para pedidos — activa al entrar en viewport */
  var ctrEl=document.getElementById('tnd-counter');
  if(ctrEl&&'IntersectionObserver' in window){
    var target=2847,started=false;
    new IntersectionObserver(function(e){
      if(e[0].isIntersecting&&!started){
        started=true;
        var t0=Date.now(),dur=1400;
        (function step(){
          var p=Math.min(1,(Date.now()-t0)/dur);
          var ease=p<.5?2*p*p:1-Math.pow(-2*p+2,2)/2;
          ctrEl.textContent=Math.floor(ease*target).toLocaleString('es-CO');
          if(p<1) requestAnimationFrame(step);
          else ctrEl.textContent=target.toLocaleString('es-CO');
        })();
      }
    },{threshold:0.5}).observe(ctrEl);
  }
  /* Sticky CTA — ocultar cuando el form es visible */
  var sticky=document.getElementById('tnd-sticky');
  var form=document.getElementById('product-form');
  if(sticky&&form&&'IntersectionObserver' in window){
    new IntersectionObserver(function(e){
      sticky.style.display=e[0].isIntersecting?'none':'block';
    },{threshold:0.1}).observe(form);
  }
})();
</script>
"""


def renderizar_premium(
    copy: LandingCopyPremium,
    imagen_url: str = "",
    product_handle: str = "",
    stock: int = 7,
    viendo: int = 23,
) -> LandingHTML:
    """
    Renderiza el template premium azul oscuro listo para Shopify body_html.

    Args:
        copy:           LandingCopyPremium generado por generar_copy_premium().
        imagen_url:     URL de imagen del producto (opcional).
        product_handle: Handle del producto Shopify para el form Releasit COD.
        stock:          Unidades para la barra de urgencia.
        viendo:         Personas viendo para la barra de urgencia.

    Returns:
        LandingHTML con el HTML completo.
    """
    tmpl = _env.from_string(_PREMIUM_HTML)
    html = tmpl.render(
        copy=copy,
        imagen_url=imagen_url,
        product_handle=product_handle,
        stock=stock,
        viendo=viendo,
    )
    return LandingHTML(keyword=copy.keyword, html=html, imagen_url=imagen_url)
