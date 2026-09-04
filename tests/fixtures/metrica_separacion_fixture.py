"""Fixture sintética para tests de `analytics.metrica_separacion`:
construye `PistaGuitarra`/`Estimacion` a partir de arrays `numpy`
generados en memoria (senoidales, silencio) -- nunca audio real del
dataset (constitución Principio IV).

A diferencia de `tests/fixtures/slakh2100_fixture.py` (Feature 001),
esta feature no lee ni escribe nada en disco -- no hay `TrackXXXXX/`
que construir, solo arrays.
"""

from __future__ import annotations

import numpy as np

from guitar_tabs_analysis.analytics.metrica_separacion import Estimacion
from guitar_tabs_analysis.ingestion.slakh2100 import PistaAudio, PistaGuitarra


def onda_senoidal(
    n_muestras: int,
    frecuencia_muestreo: int = 44100,
    frecuencia_onda: float = 220.0,
    fase: float = 0.0,
    amplitud: float = 1000.0,
) -> np.ndarray:
    """Genera una onda senoidal (`float64`) de `n_muestras` -- una señal
    sintética con energía conocida y no nula, determinista para los
    mismos parámetros (sin generador aleatorio de por medio)."""
    t = np.arange(n_muestras, dtype=np.float64) / frecuencia_muestreo
    return amplitud * np.sin(2 * np.pi * frecuencia_onda * t + fase)


def silencio(n_muestras: int) -> np.ndarray:
    """Vector cero (`float64`) -- silencio digital exacto (energía
    nula), research.md #4 de `specs/002-metrica-separacion-guitarra/`."""
    return np.zeros(n_muestras, dtype=np.float64)


def referencia_sintetica(
    identificador_origen: str = "S01",
    n_muestras: int = 1000,
    frecuencia_muestreo: int = 44100,
    muestras: np.ndarray | None = None,
) -> PistaGuitarra:
    """Construye una `PistaGuitarra` sintética -- por defecto, una onda
    senoidal con energía no nula. Pasa `muestras` explícito (p. ej.
    `silencio(...)`) para controlar el contenido exacto."""
    if muestras is None:
        muestras = onda_senoidal(n_muestras, frecuencia_muestreo)
    return PistaGuitarra(
        identificador_origen=identificador_origen,
        audio=PistaAudio(muestras=muestras, frecuencia_muestreo=frecuencia_muestreo),
    )


def estimacion_sintetica(
    identificador: str = "sep_S01",
    n_muestras: int = 1000,
    frecuencia_muestreo: int = 44100,
    muestras: np.ndarray | None = None,
) -> Estimacion:
    """Construye una `Estimacion` sintética -- por defecto, una onda
    senoidal con energía no nula. Pasa `muestras` explícito para
    controlar el contenido exacto (p. ej. una versión escalada o
    desfasada de la referencia con la que se va a comparar)."""
    if muestras is None:
        muestras = onda_senoidal(n_muestras, frecuencia_muestreo)
    return Estimacion(
        identificador=identificador,
        audio=PistaAudio(muestras=muestras, frecuencia_muestreo=frecuencia_muestreo),
    )
