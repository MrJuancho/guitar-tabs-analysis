"""Único test de esta feature marcado `@pytest.mark.modelo_real` (Polish,
T029 de `specs/004-medicion-linea-base/tasks.md`): el primero que ejercita
la cadena completa -- leer (Feature 001) → separar (Feature 003) → medir
(Feature 002) -- con el modelo real, a través de `procesar_tema`. Un solo
tema sintético corto basta; no hace falta la submuestra entera (esa
corrida es manual, fuera del ciclo de test-y-verificación -- ver
quickstart.md).

Se salta, con motivo específico, si la carga del modelo no se completa
(sin red la primera vez que se descargan los pesos, o cualquier error
real de carga) -- el hook de `tests/conftest.py` (Feature 003, T017) hace
que ese salto nunca pase desapercibido.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from guitar_tabs_analysis.medicion.orquestador import procesar_tema
from guitar_tabs_analysis.separacion.demucs_separador import DemucsSeparador
from tests.fixtures.slakh2100_fixture import EspecificacionStem, construir_tema_sintetico


@pytest.fixture(scope="module")
def separador_real() -> Iterator[DemucsSeparador]:
    try:
        yield DemucsSeparador()
    except Exception as causa:  # noqa: BLE001 -- cualquier fallo real de carga es un salto, no un error de test
        pytest.skip(f"DemucsSeparador no se pudo cargar: {causa}")


@pytest.mark.modelo_real
def test_procesar_tema_de_punta_a_punta_con_modelo_real(
    tmp_path: Path, separador_real: DemucsSeparador
) -> None:
    """leer_tema -> separar_guitarra -> emparejar_tema, con htdemucs_6s
    real, sobre un tema sintético corto (2 s, no un tema completo de
    Slakh2100 -- research.md #9 de la Feature 003 ya midió ese costo por
    separado). El resultado es un `ResultadoProcesamientoTema` con
    `reporte` o `exclusion` (nunca ambos ni ninguno), sin ninguna
    excepción no controlada."""
    guitarra = EspecificacionStem(identificador="G01", inst_class="Guitar")
    construir_tema_sintetico(
        tmp_path,
        tema_id="Track-modelo-real",
        n_muestras_mezcla=44100 * 2,
        stems=(guitarra,),
    )

    resultado = procesar_tema("Track-modelo-real", tmp_path, separador_real)

    assert resultado.tema_id == "Track-modelo-real"
    assert (resultado.reporte is None) != (resultado.exclusion is None)
    if resultado.reporte is not None:
        assert resultado.transformaciones != []
    else:
        assert resultado.transformaciones == []
