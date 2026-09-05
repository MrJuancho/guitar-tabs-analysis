"""Separación de guitarra con un modelo preentrenado (capa `separacion`,
importa de `analytics` e `ingestion`, ninguna de las dos importa de
vuelta): dada la mezcla de un tema y un `Separador` inyectado,
`separar_guitarra` verifica el formato de audio que el modelo espera
(nunca lo asume), declara cualquier transformación aplicada, y devuelve
la colección de estimaciones que el separador produjo.

Este módulo NO importa `torch` ni `demucs` -- solo depende del protocolo
`Separador` de más abajo. El adaptador real que sí los importa vive en
`separacion.demucs_separador`. Esto es lo que permite construir y probar
toda la lógica de este módulo con un `Separador` falso
(`tests/fixtures/separador_fixture.py`), sin cargar ningún modelo real ni
tocar la red (research.md #7 de
`specs/003-separacion-modelo-preentrenado/`).

Cubre T004/T011 (Foundational y User Story 1) de
`specs/003-separacion-modelo-preentrenado/tasks.md`. Ver data-model.md y
contracts/separacion.md para el contrato completo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

import numpy as np
import numpy.typing as npt
from scipy.signal import resample

from guitar_tabs_analysis.analytics.metrica_separacion import Estimacion
from guitar_tabs_analysis.ingestion.slakh2100 import PistaAudio

# ---------------------------------------------------------------------
# Tipos de dominio (T004) -- todos inmutables: son el resultado de una
# separación, no construcción incremental (data-model.md).
# ---------------------------------------------------------------------

NOMBRE_STEM_GUITARRA = "guitar"
"""Nombre de la fuente de guitarra tal como la nombra el propio modelo
(`htdemucs_6s`, research.md #1) -- se reutiliza como identificador de la
`Estimacion` producida, no se inventa uno propio."""


@dataclass(frozen=True)
class ModeloDeclarado:
    """El modelo preentrenado fijo usado para separar, identificado de
    forma verificable (FR-002)."""

    nombre: str
    variante: str
    firma: str
    checksum_sha256_prefijo: str
    licencia_pesos: str


TipoTransformacion = Literal["frecuencia_muestreo", "canales"]
DireccionTransformacion = Literal["entrada", "salida"]


@dataclass(frozen=True)
class TransformacionDeclarada:
    """Un cambio de formato aplicado -- o verificado y no necesario --
    entre el audio del conjunto y la entrada/salida del modelo (FR-005,
    FR-006, FR-007)."""

    tipo: TipoTransformacion
    direccion: DireccionTransformacion
    aplicada: bool
    detalle: str


@dataclass(frozen=True)
class ResultadoSeparacionTema:
    """El resultado de separar un tema (FR-001, FR-007)."""

    tema_id: str
    estimaciones: list[Estimacion]
    transformaciones: list[TransformacionDeclarada]
    modelo: ModeloDeclarado


class Separador(Protocol):
    """La interfaz mínima que `separar_guitarra` necesita -- no una clase
    concreta. `separacion.demucs_separador.DemucsSeparador` la implementa
    envolviendo `demucs.api.Separator`; los tests inyectan un
    `SeparadorFalso` que la implementa sin importar `torch`."""

    modelo_declarado: ModeloDeclarado

    @property
    def samplerate(self) -> int: ...

    @property
    def audio_channels(self) -> int: ...

    def separar(self, muestras: npt.NDArray[Any]) -> dict[str, npt.NDArray[Any]]: ...


class SeparacionFallidaError(Exception):
    """Un fallo real del modelo o del framework de inferencia durante un
    tema (FR-014) -- distinto del caso legítimo de `estimaciones == []`
    (FR-009). La causa original queda encadenada (`raise ... from causa`),
    nunca silenciada ni reformulada."""

    def __init__(self, tema_id: str, causa: Exception) -> None:
        self.tema_id = tema_id
        super().__init__(
            f"La separación del tema '{tema_id}' falló: {causa}. "
            "No es el caso legítimo de 'el modelo no produjo guitarra' "
            "(eso da una colección vacía, no una excepción) -- es un fallo "
            "real del modelo o del framework de inferencia, y no se "
            "reintenta automáticamente."
        )


# ---------------------------------------------------------------------
# Orquestación (T011)
# ---------------------------------------------------------------------


def separar_guitarra(
    tema_id: str,
    mezcla: PistaAudio,
    separador: Separador,
) -> ResultadoSeparacionTema:
    """Verifica (nunca asume) el formato que `separador` espera contra
    el de `mezcla`, declara cualquier transformación aplicada, y devuelve
    la colección de estimaciones que produjo -- vacía si el separador no
    incluyó la fuente `"guitar"` (FR-009), con un elemento si sí la
    incluyó, sin importar su energía (FR-010, contracts/separacion.md).
    """
    transformaciones: list[TransformacionDeclarada] = []

    frecuencia_original = mezcla.frecuencia_muestreo
    frecuencia_esperada = separador.samplerate
    if frecuencia_original == frecuencia_esperada:
        entrada = mezcla.muestras
        transformaciones.append(
            TransformacionDeclarada(
                tipo="frecuencia_muestreo",
                direccion="entrada",
                aplicada=False,
                detalle=f"{frecuencia_original} Hz -> {frecuencia_esperada} Hz (sin cambio)",
            )
        )
    else:
        n_muestras_destino = round(len(mezcla.muestras) * frecuencia_esperada / frecuencia_original)
        entrada = resample(mezcla.muestras, n_muestras_destino)
        transformaciones.append(
            TransformacionDeclarada(
                tipo="frecuencia_muestreo",
                direccion="entrada",
                aplicada=True,
                detalle=f"{frecuencia_original} Hz -> {frecuencia_esperada} Hz (remuestreado)",
            )
        )

    canales_esperados = separador.audio_channels
    if canales_esperados == 1:
        transformaciones.append(
            TransformacionDeclarada(
                tipo="canales",
                direccion="entrada",
                aplicada=False,
                detalle="1 canal -> 1 canal (sin cambio)",
            )
        )
    else:
        entrada = np.tile(entrada, (canales_esperados, 1))
        transformaciones.append(
            TransformacionDeclarada(
                tipo="canales",
                direccion="entrada",
                aplicada=True,
                detalle=f"1 canal -> {canales_esperados} canales (duplicado)",
            )
        )

    try:
        salida = separador.separar(entrada)
    except Exception as causa:
        raise SeparacionFallidaError(tema_id, causa) from causa

    estimaciones: list[Estimacion] = []
    if NOMBRE_STEM_GUITARRA in salida:
        guitarra = salida[NOMBRE_STEM_GUITARRA]
        n_canales_salida = guitarra.shape[0] if guitarra.ndim > 1 else 1
        if n_canales_salida == 1:
            muestras_mono = np.asarray(guitarra).reshape(-1)
            aplicada_salida = False
            detalle_salida = "1 canal -> 1 canal (sin cambio)"
        else:
            muestras_mono = guitarra.mean(axis=0)
            aplicada_salida = True
            detalle_salida = f"{n_canales_salida} canales -> 1 canal (promedio)"
        transformaciones.append(
            TransformacionDeclarada(
                tipo="canales",
                direccion="salida",
                aplicada=aplicada_salida,
                detalle=detalle_salida,
            )
        )
        estimaciones.append(
            Estimacion(
                identificador=NOMBRE_STEM_GUITARRA,
                audio=PistaAudio(muestras=muestras_mono, frecuencia_muestreo=frecuencia_esperada),
            )
        )

    return ResultadoSeparacionTema(
        tema_id=tema_id,
        estimaciones=estimaciones,
        transformaciones=transformaciones,
        modelo=separador.modelo_declarado,
    )
