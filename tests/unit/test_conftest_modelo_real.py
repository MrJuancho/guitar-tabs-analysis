"""Demuestra -- no asume -- que el hook `pytest_terminal_summary` de
`tests/conftest.py` (T017 de
`specs/003-separacion-modelo-preentrenado/tasks.md`) SÍ imprime el aviso
visible cuando un test marcado `modelo_real` termina saltado, incluso
bajo `-q` (los `addopts` reales del proyecto). Mismo criterio que
`AGENTS.md` exige para un chequeo de estado: "su test de regresión debe
demostrar que el chequeo falla cuando debe fallar, no solo confirmar que
pasa cuando todo está en orden" -- aplicado aquí a "que el aviso aparece
cuando debe aparecer".

Copia el contenido REAL de `tests/conftest.py` dentro del proyecto de
prueba aislado que crea `pytester` -- no reimplementa el hook, así que
nunca puede quedar desincronizado con el mecanismo real.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_CONFTEST_REAL = Path(__file__).resolve().parents[1] / "conftest.py"


def test_bloque_visible_aparece_cuando_se_salta_modelo_real(pytester: pytest.Pytester) -> None:
    pytester.makeconftest(_CONFTEST_REAL.read_text(encoding="utf-8"))
    pytester.makepyfile(
        test_dummy="""
import pytest

@pytest.mark.modelo_real
def test_algo_que_se_salta():
    pytest.skip("sin red, motivo de prueba")
"""
    )

    resultado = pytester.runpytest("-q")

    resultado.stdout.fnmatch_lines(
        [
            "*MODELO REAL*",
            "*1*modelo_real*",
            "*sin red, motivo de prueba*",
        ]
    )


def test_sin_saltos_de_modelo_real_no_imprime_el_bloque(pytester: pytest.Pytester) -> None:
    """El aviso es específico -- no aparece cuando no hay nada que
    reportar (una corrida normal, toda en verde, no debe mostrarlo)."""
    pytester.makeconftest(_CONFTEST_REAL.read_text(encoding="utf-8"))
    pytester.makepyfile(
        test_dummy="""
def test_que_pasa():
    assert True
"""
    )

    resultado = pytester.runpytest("-q")

    salida = "\n".join(resultado.outlines)
    assert "MODELO REAL" not in salida
