"""Fixture de prueba para `separacion.separador`: un `Separador` falso
que implementa el protocolo sin importar `torch` ni `demucs`, y un helper
de mezcla mono sintética -- nunca audio real del dataset (constitución
Principio IV) ni el modelo real (research.md #7 de
`specs/003-separacion-modelo-preentrenado/`).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

from guitar_tabs_analysis.ingestion.slakh2100 import PistaAudio
from guitar_tabs_analysis.separacion.separador import NOMBRE_STEM_GUITARRA, ModeloDeclarado

MODELO_FALSO = ModeloDeclarado(
    nombre="ModeloFalso",
    variante="v0-prueba",
    firma="dummy0000",
    checksum_sha256_prefijo="dummy1111",
    licencia_pesos="ninguna -- solo para tests",
)


def mezcla_sintetica(
    n_muestras: int = 44100,
    frecuencia_muestreo: int = 44100,
    frecuencia_onda: float = 220.0,
) -> PistaAudio:
    """Mezcla mono sintética (`float64`, una sola dimensión) -- misma
    forma que `PistaAudio.muestras` de Feature 001 (Slakh2100 es mono)."""
    t = np.arange(n_muestras, dtype=np.float64) / frecuencia_muestreo
    muestras = 1000.0 * np.sin(2 * np.pi * frecuencia_onda * t)
    return PistaAudio(muestras=muestras, frecuencia_muestreo=frecuencia_muestreo)


class SeparadorFalso:
    """Implementa el protocolo `Separador` (data-model.md) de forma
    completamente configurable, para ejercitar `separar_guitarra` sin
    ningún costo de red ni de cómputo real.

    Por defecto, `separar()` devuelve un eco de la entrada como la fuente
    `"guitar"` (mismo número de canales, mismos valores) -- suficiente
    para los casos donde el contenido no importa, pero **no** para los
    tests que verifican el colapso de canales de salida (ahí se pasa
    `salida` explícito con canales distintos, para que el test no pase
    por accidente si el código promediara mal).
    """

    def __init__(
        self,
        *,
        samplerate: int = 44100,
        audio_channels: int = 1,
        modelo_declarado: ModeloDeclarado = MODELO_FALSO,
        salida: dict[str, npt.NDArray[Any]] | None = None,
        omitir_guitarra: bool = False,
        excepcion: Exception | None = None,
    ) -> None:
        self.modelo_declarado = modelo_declarado
        self._samplerate = samplerate
        self._audio_channels = audio_channels
        self._salida = salida
        self._omitir_guitarra = omitir_guitarra
        self._excepcion = excepcion
        self.llamadas = 0
        self.ultima_entrada: npt.NDArray[Any] | None = None

    @property
    def samplerate(self) -> int:
        return self._samplerate

    @property
    def audio_channels(self) -> int:
        return self._audio_channels

    def separar(self, muestras: npt.NDArray[Any]) -> dict[str, npt.NDArray[Any]]:
        self.llamadas += 1
        self.ultima_entrada = muestras
        if self._excepcion is not None:
            raise self._excepcion
        if self._omitir_guitarra:
            return {}
        if self._salida is not None:
            return self._salida
        return {NOMBRE_STEM_GUITARRA: np.array(muestras, copy=True)}
