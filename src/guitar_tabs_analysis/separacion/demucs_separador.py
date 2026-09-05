"""Adaptador real que envuelve `demucs.api.Separator` (capa
`separacion`) -- único módulo de esta feature que importa `torch`/
`demucs`. Implementa el protocolo `Separador` de
`separacion.separador`, así que `separar_guitarra()` no sabe ni le
importa que detrás hay una red neuronal real.

Cubre T012/T015 (User Story 2) de
`specs/003-separacion-modelo-preentrenado/tasks.md`. Ver research.md
#1/#2/#4 para las decisiones verificadas (modelo, procedencia,
verificación de formato) y `docs/ATRIBUCIONES.md` para la licencia de
los pesos (FR-003/004).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt
import torch
from demucs.api import Separator

from guitar_tabs_analysis.separacion.separador import ModeloDeclarado

MODELO_DECLARADO = ModeloDeclarado(
    nombre="Demucs",
    variante="htdemucs_6s",
    firma="5c90dfd2",
    checksum_sha256_prefijo="d2a1745f0744",
    licencia_pesos=(
        "Provistos solo con fines científicos, distinto del MIT del código "
        "-- ver docs/ATRIBUCIONES.md"
    ),
)
"""Declaración fija del modelo (FR-002), verificada en vivo contra el
modelo real (research.md #1/#2 de
specs/003-separacion-modelo-preentrenado/) -- no se recalcula por
corrida."""


class DemucsSeparador:
    """Implementa el protocolo `Separador` envolviendo
    `demucs.api.Separator(model="htdemucs_6s", device="cpu")` --
    `device="cpu"` fijo, sin ninguna ruta que intente usar GPU (hardware
    del proyecto sin GPU utilizable, Assumptions de spec.md)."""

    modelo_declarado: ModeloDeclarado = MODELO_DECLARADO

    def __init__(self) -> None:
        self._separator = Separator(model=MODELO_DECLARADO.variante, device="cpu")

    @property
    def samplerate(self) -> int:
        return int(self._separator.samplerate)

    @property
    def audio_channels(self) -> int:
        return int(self._separator.audio_channels)

    def separar(self, muestras: npt.NDArray[Any]) -> dict[str, npt.NDArray[Any]]:
        entrada = torch.from_numpy(np.asarray(muestras, dtype=np.float32))
        _, fuentes = self._separator.separate_tensor(entrada, sr=self.samplerate)
        return {nombre: tensor.numpy() for nombre, tensor in fuentes.items()}
