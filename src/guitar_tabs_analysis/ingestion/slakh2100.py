"""Lectura de un tema de Slakh2100 (capa `ingestion`, nivel más bajo del
contrato de import-linter): dado el identificador de un tema y la raíz
local del dataset, `leer_tema()` devuelve el audio de la mezcla y la
colección de audios de sus pistas de guitarra.

Este módulo, en su estado actual (T003, T005-T013 de
`specs/001-lectura-tema-slakh2100/tasks.md`), cubre el camino feliz
completo de User Story 1 (P1/MVP): tipos de dominio inmutables,
excepciones del contrato, los dos helpers de E/S de bajo nivel
(`_leer_metadata`, `_decodificar_audio`) y `leer_tema()` en sí --
todavía sin los modos de fallo de User Story 3 (`TemaNoExisteError`/
`ArchivoAudioNoLegibleError`/`LongitudInconsistenteError` no se lanzan
todavía desde `leer_tema()`; eso es T019-T021, fuera de este slice).

Ver `specs/001-lectura-tema-slakh2100/data-model.md` y
`specs/001-lectura-tema-slakh2100/contracts/leer_tema.md` para el
contrato completo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy.typing as npt
import soundfile as sf
import yaml

# Mapeo subtype de libsndfile -> dtype de numpy que lo representa sin
# reescalado (research.md #1) -- el `float64` que da `soundfile` por
# defecto SÍ reescala los enteros a [-1.0, 1.0], lo que FR-005 prohíbe.
_SUBTYPE_A_DTYPE: dict[str, str] = {
    "PCM_16": "int16",
    "PCM_24": "int32",
    "PCM_32": "int32",
    "PCM_U8": "uint8",
    "FLOAT": "float32",
    "DOUBLE": "float64",
}

# ---------------------------------------------------------------------
# Tipos de dominio (T003) -- todos inmutables: son el resultado de una
# única operación de lectura, sin ciclo de vida propio (data-model.md).
# ---------------------------------------------------------------------


@dataclass(frozen=True, eq=False)
class PistaAudio:
    """El audio de un archivo tal como está en disco -- mezcla o pista de
    guitarra, misma forma. `muestras` se decodifica con el `dtype` que
    coincide con el `subtype` real del archivo (research.md #1), nunca
    reescalado.

    `eq=False`: la igualdad por defecto de un dataclass compara sus campos
    con `==`, y `numpy.ndarray.__eq__` devuelve un array elemento a
    elemento en vez de un `bool` -- comparar dos `PistaAudio` con `==`
    lanzaría `ValueError: truth value of an array is ambiguous`. Se deja
    la igualdad por identidad (la de `object`); comparar contenido de
    `muestras` se hace explícitamente con `numpy.array_equal` en los
    tests, no con `==` sobre la dataclass.
    """

    muestras: npt.NDArray[Any]
    frecuencia_muestreo: int


@dataclass(frozen=True)
class PistaGuitarra:
    """Una pista de guitarra dentro de un tema, con su identidad de
    origen (la clave del stem en `metadata.yaml`, p. ej. `"S01"`)."""

    identificador_origen: str
    audio: PistaAudio


@dataclass(frozen=True)
class LecturaTema:
    """El resultado devuelto por la operación de lectura para un tema."""

    tema_id: str
    mezcla: PistaAudio
    guitarras: list[PistaGuitarra] = field(default_factory=list)


# ---------------------------------------------------------------------
# Excepciones del contrato (T003) -- ver contracts/leer_tema.md, tabla
# "Modos de fallo".
# ---------------------------------------------------------------------


class TemaNoExisteError(Exception):
    """FR-010: `tema_id` no corresponde a ningún directorio del conjunto."""

    def __init__(self, tema_id: str) -> None:
        self.tema_id = tema_id
        super().__init__(f"El tema '{tema_id}' no existe en el conjunto Slakh2100.")


class ArchivoAudioNoLegibleError(Exception):
    """FR-012: el tema existe, pero `mix.flac` o un stem con
    `audio_rendered == true` está ausente o no se puede decodificar.
    Nunca se lanza para un stem excluido por FR-013 (no renderizado)."""

    def __init__(self, tema_id: str, archivo: str) -> None:
        self.tema_id = tema_id
        self.archivo = archivo
        super().__init__(f"No se pudo leer el archivo de audio '{archivo}' del tema '{tema_id}'.")


class LongitudInconsistenteError(Exception):
    """FR-011: la mezcla y una pista de guitarra del mismo tema tienen
    distinta longitud (número de muestras). Ninguno de los dos audios se
    recorta ni se rellena para forzar coincidencia."""

    def __init__(self, tema_id: str, identificador_origen: str) -> None:
        self.tema_id = tema_id
        self.identificador_origen = identificador_origen
        super().__init__(
            f"La pista '{identificador_origen}' del tema '{tema_id}' tiene una "
            "longitud distinta a la de la mezcla."
        )


# ---------------------------------------------------------------------
# Helpers de E/S de bajo nivel (T005/T006).
# ---------------------------------------------------------------------


def _leer_metadata(tema_dir: Path) -> dict[str, Any]:
    """Parsea `tema_dir/metadata.yaml` con PyYAML (research.md #2).

    Deja propagar sin traducir cualquier error de E/S (archivo/directorio
    ausente) o de parseo -- traducirlo a `TemaNoExisteError` es
    responsabilidad de `leer_tema()` (T019, fuera de este slice), no de
    este helper de bajo nivel.
    """
    with (tema_dir / "metadata.yaml").open(encoding="utf-8") as archivo:
        metadata: dict[str, Any] = yaml.safe_load(archivo)
    return metadata


def _decodificar_audio(path: Path) -> PistaAudio:
    """Decodifica `path` con `soundfile`, leyendo con el `dtype` que
    coincide con el `subtype` real del archivo (research.md #1) -- nunca
    el `float64` reescalado que da `soundfile` por defecto.

    Deja propagar sin traducir cualquier error de `soundfile`/E/S (p. ej.
    `soundfile.LibsndfileError` ante un archivo ausente o corrupto) --
    convertirlo en `ArchivoAudioNoLegibleError` es responsabilidad de
    `leer_tema()` (T020, fuera de este slice).
    """
    info = sf.info(str(path))
    dtype = _SUBTYPE_A_DTYPE.get(info.subtype, "float64")
    muestras, frecuencia_muestreo = sf.read(str(path), dtype=dtype, always_2d=False)
    return PistaAudio(muestras=muestras, frecuencia_muestreo=frecuencia_muestreo)


# ---------------------------------------------------------------------
# leer_tema (T013, T019, T020) -- camino feliz de User Story 1 más los
# modos de fallo de User Story 3.
# ---------------------------------------------------------------------


def _decodificar_o_fallar(path: Path, tema_dir: Path, tema_id: str) -> PistaAudio:
    """Decodifica `path` traduciendo cualquier error de `soundfile`/E-S
    (archivo ausente o no legible) a `ArchivoAudioNoLegibleError(tema_id,
    archivo)` (T020, FR-012). `archivo` es la ruta de `path` relativa a
    `tema_dir` (p. ej. `"mix.flac"`, `"stems/S01.flac"`) -- mismo formato
    tanto para la mezcla como para cualquier guitarra."""
    try:
        return _decodificar_audio(path)
    except (OSError, sf.LibsndfileError) as error:
        archivo = str(path.relative_to(tema_dir))
        raise ArchivoAudioNoLegibleError(tema_id, archivo) from error


def leer_tema(tema_id: str, root_dir: Path) -> LecturaTema:
    """Lee la mezcla y las pistas de guitarra del tema `tema_id` bajo
    `root_dir` (contracts/leer_tema.md).

    Una pista cuenta para `guitarras` si y solo si `inst_class == "Guitar"`
    (FR-003; excluye bajo eléctrico y otras familias vía FR-004) **y**
    `audio_rendered is True` (FR-013: un stem de guitarra sin renderizar
    se excluye en silencio, no dispara ninguna excepción). El orden de
    `guitarras` sigue el orden de `metadata["stems"]` tal como lo entrega
    PyYAML -- determinista para un mismo `metadata.yaml` (spec.md
    Assumptions), sin garantía adicional más allá de eso.

    Lanza `TemaNoExisteError` (FR-010) si `root_dir/tema_id` no existe
    como directorio -- verificado antes de leer nada más. Lanza
    `ArchivoAudioNoLegibleError` (FR-012) si `mix.flac` o el `.flac` de
    cualquier guitarra elegible está ausente o no se puede decodificar."""
    tema_dir = root_dir / tema_id
    if not tema_dir.is_dir():
        raise TemaNoExisteError(tema_id)
    metadata = _leer_metadata(tema_dir)
    mezcla = _decodificar_o_fallar(tema_dir / "mix.flac", tema_dir, tema_id)

    stems_dir = tema_dir / metadata.get("audio_dir", "stems")
    guitarras = [
        PistaGuitarra(
            identificador_origen=identificador,
            audio=_decodificar_o_fallar(stems_dir / f"{identificador}.flac", tema_dir, tema_id),
        )
        for identificador, stem_meta in metadata.get("stems", {}).items()
        if stem_meta.get("inst_class") == "Guitar" and stem_meta.get("audio_rendered") is True
    ]
    return LecturaTema(tema_id=tema_id, mezcla=mezcla, guitarras=guitarras)
