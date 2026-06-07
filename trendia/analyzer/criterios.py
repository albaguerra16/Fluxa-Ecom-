"""Estructuras de datos para el framework de 9 criterios COD Colombia."""

from __future__ import annotations

from dataclasses import dataclass, field

ESTADO_OK   = "✅"
ESTADO_WARN = "⚠️"
ESTADO_FAIL = "❌"

NOMBRES_CRITERIOS = [
    "Saturación del mercado",
    "Stock y proveedores",
    "Catálogo público (Dollar City / D1 / Ara)",
    "Oportunidad de importación",
    "Ticket (rango de precio COP)",
    "Suple una necesidad real",
    "Potencial de anuncio cautivador",
    "Percepción de valor y marca",
    "Producto / oferta black (políticas Meta & TikTok)",
]


@dataclass
class CriterioResultado:
    numero: int       # 1–9
    nombre: str
    estado: str       # ESTADO_OK / WARN / FAIL
    nota: str         # explicación con datos concretos
    puntos: int       # 0 (❌) | 1 (⚠️) | 2 (✅)


@dataclass
class AnguloVenta:
    nombre: str   # ej. TESTIMONIAL | DEMOSTRACIÓN | URGENCIA
    hook: str     # primera frase gancho
    copy: str     # copy completo listo para usar


@dataclass
class MarcaSugerida:
    nombre: str
    razon: str
    copy_anuncio: str
    valor_agregado: str
    empaque: str


@dataclass
class AnalisisCompleto:
    keyword: str
    criterios: list[CriterioResultado]
    score_total: int           # 0–18 (suma de puntos)
    angulos_venta: list[AnguloVenta]
    marca: MarcaSugerida
    riesgos: list[str]
    veredicto: str             # LANZAR | LANZAR CON PRECAUCIÓN | NO LANZAR
    tokens_entrada: int = 0
    tokens_salida: int = 0

    @property
    def score_pct(self) -> float:
        return round(self.score_total / 18 * 100, 1)

    @property
    def aprobados(self) -> int:
        return sum(1 for c in self.criterios if c.estado == ESTADO_OK)

    @property
    def en_riesgo(self) -> int:
        return sum(1 for c in self.criterios if c.estado == ESTADO_WARN)

    @property
    def reprobados(self) -> int:
        return sum(1 for c in self.criterios if c.estado == ESTADO_FAIL)
