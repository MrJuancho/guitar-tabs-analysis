"""Tests del propio helper de fixtures (T004 de
`specs/002-metrica-separacion-guitarra/tasks.md`), no de `si_sdr()`.

Verifica que el helper puede construir tanto una señal con energía no
nula (el caso general) como silencio digital exacto (energía nula) y
variantes escaladas -- los casos que T005 en adelante necesitan sin
tocar este archivo de nuevo.
"""

from __future__ import annotations

import numpy as np
from tests.fixtures.metrica_separacion_fixture import (
    estimacion_sintetica,
    onda_senoidal,
    referencia_sintetica,
    silencio,
)

from guitar_tabs_analysis.analytics.metrica_separacion import Estimacion
from guitar_tabs_analysis.ingestion.slakh2100 import PistaGuitarra


def test_onda_senoidal_tiene_energia_no_nula() -> None:
    onda = onda_senoidal(n_muestras=1000)
    assert onda.shape == (1000,)
    assert np.sum(onda**2) > 0


def test_onda_senoidal_es_determinista_para_los_mismos_parametros() -> None:
    a = onda_senoidal(n_muestras=500, frecuencia_onda=220.0, fase=0.3, amplitud=500.0)
    b = onda_senoidal(n_muestras=500, frecuencia_onda=220.0, fase=0.3, amplitud=500.0)
    np.testing.assert_array_equal(a, b)


def test_referencia_sintetica_expone_identificador_y_audio_con_energia() -> None:
    referencia = referencia_sintetica(identificador_origen="S01", n_muestras=200)
    assert isinstance(referencia, PistaGuitarra)
    assert referencia.identificador_origen == "S01"
    assert referencia.audio.frecuencia_muestreo == 44100
    assert np.sum(referencia.audio.muestras.astype(np.float64) ** 2) > 0


def test_referencia_sintetica_acepta_muestras_explicitas() -> None:
    muestras = silencio(100)
    referencia = referencia_sintetica(identificador_origen="S02", muestras=muestras)
    np.testing.assert_array_equal(referencia.audio.muestras, muestras)


def test_estimacion_sintetica_expone_identificador_y_audio_con_energia() -> None:
    estimacion = estimacion_sintetica(identificador="sep_S01", n_muestras=200)
    assert isinstance(estimacion, Estimacion)
    assert estimacion.identificador == "sep_S01"
    assert np.sum(estimacion.audio.muestras.astype(np.float64) ** 2) > 0


def test_silencio_es_vector_cero_exacto() -> None:
    vector = silencio(50)
    assert vector.shape == (50,)
    assert np.all(vector == 0.0)
