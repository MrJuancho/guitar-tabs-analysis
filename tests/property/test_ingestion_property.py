"""EJEMPLO -- property test con Hypothesis para la capa de ingestion.

Las invariantes de dominio real casi nunca se descubren con ejemplos a
mano; property-based testing genera cientos de entradas variadas y busca
el contraejemplo. TODO: reemplaza `normalizar_texto` por las funciones
reales de tu `ingestion/` y las propiedades por las invariantes reales de
tu dominio (ver `reviewer.md` -- el patrón `xfail(strict=True)` documentado
ahí es para cuando un property test encuentra un defecto real que decides
no arreglar todavía: el test se queda en rojo controlado, documentado, en
vez de silenciarse).
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from guitar_tabs_analysis.ingestion.normalizar import normalizar_texto

texto_arbitrario = st.text(min_size=0, max_size=200)


@given(texto_arbitrario)
def test_normalizar_texto_es_idempotente(valor: str) -> None:
    """MATA cualquier mutante que rompa la idempotencia de normalizar_texto
    -- aplicarla dos veces debe dar lo mismo que aplicarla una vez."""
    una_vez = normalizar_texto(valor)
    dos_veces = normalizar_texto(una_vez)
    assert una_vez == dos_veces


@given(texto_arbitrario)
def test_normalizar_texto_nunca_tiene_espacios_al_borde(valor: str) -> None:
    resultado = normalizar_texto(valor)
    assert resultado == resultado.strip()
