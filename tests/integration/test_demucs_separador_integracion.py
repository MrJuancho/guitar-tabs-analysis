"""Único test de esta feature marcado `@pytest.mark.modelo_real`
(research.md #7 de `specs/003-separacion-modelo-preentrenado/`): ejercita
`DemucsSeparador` real de punta a punta sobre un clip sintético corto (no
un tema completo -- eso ya lo mide T016 aparte). Se salta, con motivo
específico, si la carga del modelo no se completa (sin red la primera
vez que se descargan los pesos, o cualquier error real de carga) -- el
hook de `tests/conftest.py` (T017) hace que ese salto nunca pase
desapercibido.
"""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np
import pytest

from guitar_tabs_analysis.separacion.demucs_separador import DemucsSeparador
from guitar_tabs_analysis.separacion.separador import separar_guitarra
from tests.fixtures.separador_fixture import mezcla_sintetica


@pytest.fixture(scope="module")
def separador_real() -> Iterator[DemucsSeparador]:
    try:
        yield DemucsSeparador()
    except Exception as causa:  # noqa: BLE001 -- cualquier fallo real de carga es un salto, no un error de test
        pytest.skip(f"DemucsSeparador no se pudo cargar: {causa}")


@pytest.mark.modelo_real
def test_propiedades_reales_del_modelo(separador_real: DemucsSeparador) -> None:
    """research.md #4: leídas de las propiedades reales del modelo, no
    hardcodeadas -- este test es la única verificación de que
    `htdemucs_6s` sigue reportando lo esperado."""
    assert separador_real.samplerate == 44100
    assert separador_real.audio_channels == 2


@pytest.mark.modelo_real
def test_separar_guitarra_de_punta_a_punta_sin_excepcion(separador_real: DemucsSeparador) -> None:
    mezcla = mezcla_sintetica(n_muestras=44100 * 2)  # 2 s -- clip corto, no un tema completo

    resultado = separar_guitarra("clip-prueba", mezcla, separador_real)

    assert resultado.tema_id == "clip-prueba"
    assert resultado.modelo.variante == "htdemucs_6s"
    assert len(resultado.estimaciones) <= 1


@pytest.mark.modelo_real
def test_determinismo_real_dentro_de_tolerancia(separador_real: DemucsSeparador) -> None:
    """FR-015: el caso NO trivial de determinismo -- con el modelo real,
    no con un `SeparadorFalso` (ese ya lo cubre T010)."""
    mezcla = mezcla_sintetica(n_muestras=44100 * 2)

    resultado_1 = separar_guitarra("clip-prueba", mezcla, separador_real)
    resultado_2 = separar_guitarra("clip-prueba", mezcla, separador_real)

    if not resultado_1.estimaciones or not resultado_2.estimaciones:
        pytest.skip("el clip sintético no produjo una estimación de guitarra en esta corrida")
    np.testing.assert_allclose(
        resultado_1.estimaciones[0].audio.muestras,
        resultado_2.estimaciones[0].audio.muestras,
        rtol=1e-5,
        atol=1e-6,
    )
