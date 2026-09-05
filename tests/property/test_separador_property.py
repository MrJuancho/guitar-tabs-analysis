"""Property test (Hypothesis) para `separar_guitarra()` (T010 de
`specs/003-separacion-modelo-preentrenado/tasks.md`, User Story 1).

Genera `SeparadorFalso` con número de canales arbitrario (siempre a la
misma frecuencia de muestreo que la mezcla, para aislar el invariante de
canales del de remuestreo -- ese caso lo cubre el test unitario T007 con
un ejemplo concreto) y confirma que la verificación de formato se declara
siempre, que duplicar y luego promediar canales nunca reescala la
amplitud, y que el resultado es determinista entre corridas sucesivas
(FR-015, caso trivial con un separador determinista).
"""

from __future__ import annotations

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from guitar_tabs_analysis.separacion.separador import separar_guitarra
from tests.fixtures.separador_fixture import SeparadorFalso, mezcla_sintetica

_frecuencia_onda = st.floats(
    min_value=10.0, max_value=2000.0, allow_nan=False, allow_infinity=False
)


@given(
    audio_channels=st.integers(min_value=1, max_value=4),
    n_muestras=st.integers(min_value=10, max_value=2000),
    frecuencia_onda=_frecuencia_onda,
)
@settings(max_examples=50)
def test_transformaciones_declaradas_y_sin_reescalado_para_cualquier_numero_de_canales(
    audio_channels: int, n_muestras: int, frecuencia_onda: float
) -> None:
    mezcla = mezcla_sintetica(
        n_muestras=n_muestras, frecuencia_muestreo=44100, frecuencia_onda=frecuencia_onda
    )
    separador = SeparadorFalso(samplerate=44100, audio_channels=audio_channels)

    resultado_1 = separar_guitarra("Track00001", mezcla, separador)
    resultado_2 = separar_guitarra("Track00001", mezcla, separador)

    entradas = [t for t in resultado_1.transformaciones if t.direccion == "entrada"]
    salidas = [t for t in resultado_1.transformaciones if t.direccion == "salida"]
    assert {t.tipo for t in entradas} == {"frecuencia_muestreo", "canales"}
    assert len(entradas) == 2
    assert len(resultado_1.estimaciones) == 1
    assert len(salidas) == 1
    assert salidas[0].tipo == "canales"

    # Duplicar N canales y promediar de vuelta es la identidad -- sin
    # reescalado de amplitud, para cualquier número de canales (contrato,
    # postcondición 8).
    (estimacion_1,) = resultado_1.estimaciones
    np.testing.assert_allclose(estimacion_1.audio.muestras, mezcla.muestras)

    # Determinismo trivial: mismo separador, misma entrada -> mismas
    # muestras exactas entre dos corridas (FR-015).
    (estimacion_2,) = resultado_2.estimaciones
    np.testing.assert_array_equal(estimacion_1.audio.muestras, estimacion_2.audio.muestras)
