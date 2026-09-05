"""Tests unitarios de `separacion.separador` -- toda la lógica de
orquestación se ejercita con `SeparadorFalso`
(`tests/fixtures/separador_fixture.py`), nunca con `torch`/`demucs`
reales (research.md #7 de `specs/003-separacion-modelo-preentrenado/`).
"""

from __future__ import annotations

import numpy as np
import pytest

from guitar_tabs_analysis.separacion.separador import (
    SeparacionFallidaError,
    separar_guitarra,
)
from tests.fixtures.separador_fixture import SeparadorFalso, mezcla_sintetica


def test_frecuencia_muestreo_igual_no_remuestrea_pero_declara_la_verificacion() -> None:
    """AS1 US1: cuando la mezcla ya está a la frecuencia que el modelo
    espera, no hay remuestreo -- pero la verificación queda declarada
    igual (FR-005)."""
    mezcla = mezcla_sintetica(n_muestras=1000, frecuencia_muestreo=44100)
    separador = SeparadorFalso(samplerate=44100, audio_channels=1)

    resultado = separar_guitarra("Track00001", mezcla, separador)

    transformaciones_frecuencia = [
        t for t in resultado.transformaciones if t.tipo == "frecuencia_muestreo"
    ]
    assert len(transformaciones_frecuencia) == 1
    (transformacion,) = transformaciones_frecuencia
    assert transformacion.direccion == "entrada"
    assert transformacion.aplicada is False
    assert transformacion.detalle == "44100 Hz -> 44100 Hz (sin cambio)"
    assert separador.ultima_entrada is not None
    assert separador.ultima_entrada.shape[-1] == 1000

    # audio_channels=1: la verificación de canales de entrada también se
    # declara, aunque no haga falta ninguna duplicación (FR-006).
    (canales_entrada,) = [
        t for t in resultado.transformaciones if t.tipo == "canales" and t.direccion == "entrada"
    ]
    assert canales_entrada.aplicada is False
    assert canales_entrada.detalle == "1 canal -> 1 canal (sin cambio)"


def test_frecuencia_muestreo_distinta_remuestrea_y_lo_declara() -> None:
    """AS2 US1: cuando la mezcla no está a la frecuencia que el modelo
    espera, se remuestrea antes de invocar al separador, y se declara
    (FR-005)."""
    mezcla = mezcla_sintetica(n_muestras=1000, frecuencia_muestreo=22050)
    separador = SeparadorFalso(samplerate=44100, audio_channels=1)

    resultado = separar_guitarra("Track00001", mezcla, separador)

    (transformacion,) = [t for t in resultado.transformaciones if t.tipo == "frecuencia_muestreo"]
    assert transformacion.direccion == "entrada"
    assert transformacion.aplicada is True
    assert transformacion.detalle == "22050 Hz -> 44100 Hz (remuestreado)"
    assert separador.ultima_entrada is not None
    # 1000 muestras a 22050 Hz remuestreadas a 44100 Hz -> el doble.
    assert separador.ultima_entrada.shape[-1] == 2000


def test_mono_a_estereo_duplica_entrada_y_colapsa_salida_a_mono() -> None:
    """AS3 US1: la mezcla mono se duplica para formar la entrada estéreo
    que el modelo espera, y la salida de guitarra (estéreo) se colapsa a
    mono promediando ambos canales -- ambas transformaciones declaradas
    por separado (FR-006, FR-007)."""
    mezcla = mezcla_sintetica(n_muestras=10, frecuencia_muestreo=44100)
    # Canales de salida deliberadamente distintos entre sí: si el código
    # promediara mal (p. ej. tomara solo un canal), este test lo notaría.
    canal_izquierdo = np.full(10, 2.0)
    canal_derecho = np.full(10, 6.0)
    salida_guitarra = np.stack([canal_izquierdo, canal_derecho])
    separador = SeparadorFalso(
        samplerate=44100, audio_channels=2, salida={"guitar": salida_guitarra}
    )

    resultado = separar_guitarra("Track00001", mezcla, separador)

    # Entrada duplicada: (2, 10), ambos canales idénticos a la mezcla mono.
    assert separador.ultima_entrada is not None
    assert separador.ultima_entrada.shape == (2, 10)
    np.testing.assert_array_equal(separador.ultima_entrada[0], separador.ultima_entrada[1])
    np.testing.assert_array_equal(separador.ultima_entrada[0], mezcla.muestras)

    # Salida colapsada a mono por promedio: (2+6)/2 == 4.0 en cada muestra.
    (estimacion,) = resultado.estimaciones
    assert estimacion.audio.muestras.ndim == 1
    np.testing.assert_allclose(estimacion.audio.muestras, np.full(10, 4.0))
    assert estimacion.identificador == "guitar"
    assert estimacion.audio.frecuencia_muestreo == 44100

    tipos_canal = [t for t in resultado.transformaciones if t.tipo == "canales"]
    direcciones = {t.direccion for t in tipos_canal}
    assert direcciones == {"entrada", "salida"}
    (entrada_canales,) = [t for t in tipos_canal if t.direccion == "entrada"]
    assert entrada_canales.aplicada is True
    assert entrada_canales.detalle == "1 canal -> 2 canales (duplicado)"
    (salida_canales,) = [t for t in tipos_canal if t.direccion == "salida"]
    assert salida_canales.aplicada is True
    assert salida_canales.detalle == "2 canales -> 1 canal (promedio)"

    # El resultado completo, no solo las transformaciones: eco del
    # tema_id y del modelo declarado del separador (postcondición 6 de
    # contracts/separacion.md).
    assert resultado.tema_id == "Track00001"
    assert resultado.modelo is separador.modelo_declarado


def test_salida_de_un_solo_canal_no_se_reescala_ni_se_marca_aplicada() -> None:
    """Cuando la salida del separador ya viene con un solo canal (forma
    `(1, N)`, no `(N,)` -- caso genuinamente bidimensional, no el eco
    plano por defecto de `SeparadorFalso`), no hace falta colapsar nada:
    `aplicada=False` y las muestras se aplanan sin promediar (FR-006,
    FR-007) -- distinto del caso multicanal de arriba."""
    mezcla = mezcla_sintetica(n_muestras=3, frecuencia_muestreo=44100)
    salida_un_canal = np.array([[1.0, 2.0, 3.0]])  # shape (1, 3), no (3,)
    separador = SeparadorFalso(
        samplerate=44100, audio_channels=1, salida={"guitar": salida_un_canal}
    )

    resultado = separar_guitarra("Track00001", mezcla, separador)

    (estimacion,) = resultado.estimaciones
    assert estimacion.audio.muestras.ndim == 1
    np.testing.assert_array_equal(estimacion.audio.muestras, [1.0, 2.0, 3.0])

    (salida_canales,) = [
        t for t in resultado.transformaciones if t.tipo == "canales" and t.direccion == "salida"
    ]
    assert salida_canales.aplicada is False
    assert salida_canales.detalle == "1 canal -> 1 canal (sin cambio)"


def test_fallo_real_del_separador_se_envuelve_sin_reintentar() -> None:
    """AS6 US1: un fallo real del propio modelo/framework se propaga
    como `SeparacionFallidaError` con el tema y la causa encadenada, sin
    reintento (FR-014, cerrado en /speckit-clarify)."""
    mezcla = mezcla_sintetica(n_muestras=100)
    causa = RuntimeError("forma de audio no soportada")
    separador = SeparadorFalso(excepcion=causa)

    with pytest.raises(SeparacionFallidaError) as excinfo:
        separar_guitarra("Track00001", mezcla, separador)

    error = excinfo.value
    # Mensaje completo, no solo que los identificadores aparezcan
    # (AGENTS.md, "Tests de excepciones") -- una mutación del texto
    # explicativo (p. ej. "sí se reintenta") no debe poder sobrevivir.
    assert str(error) == (
        "La separación del tema 'Track00001' falló: forma de audio no soportada. "
        "No es el caso legítimo de 'el modelo no produjo guitarra' "
        "(eso da una colección vacía, no una excepción) -- es un fallo "
        "real del modelo o del framework de inferencia, y no se "
        "reintenta automáticamente."
    )
    assert error.tema_id == "Track00001"
    assert error.__cause__ is causa
    assert separador.llamadas == 1
