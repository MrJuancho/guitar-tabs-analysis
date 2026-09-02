"""Fixture sintética de un tema de Slakh2100: construye, en un
`tmp_path`, un directorio `TrackXXXXX/` (`metadata.yaml` + `mix.flac` +
`stems/*.flac`) con formas de onda cortas generadas -- nunca audio real
(constitución Principio IV; research.md #6 de
`specs/001-lectura-tema-slakh2100/`).

Parametrizable por stem (`EspecificacionStem`) para poder construir tanto
el camino feliz como los tres casos que las fases futuras (T007 en
adelante de `tasks.md`) necesitan sin tocar este archivo de nuevo:

- una pista de guitarra cuyo número de muestras difiera del de la mezcla
  (`EspecificacionStem.n_muestras`) -- futuro test de
  `LongitudInconsistenteError` (FR-011).
- un stem con `audio_rendered=True` en los metadatos pero cuyo `.flac`
  no se escribe en disco (`EspecificacionStem.escribir_archivo=False`)
  -- futuro test de `ArchivoAudioNoLegibleError` (FR-012).
- un stem de guitarra con `audio_rendered=False`, coherentemente sin
  archivo (el default de `escribir_archivo` sigue a `audio_rendered`
  cuando no se pasa explícito) -- FR-013, exclusión silenciosa, no error.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
import yaml

# Mapeo subtype de libsndfile -> dtype de numpy que lo representa sin
# reescalado -- el mismo criterio que usará `_decodificar_audio` (T006,
# research.md #1) al leer estos archivos de vuelta.
_SUBTYPE_A_DTYPE: dict[str, str] = {
    "PCM_16": "int16",
    "PCM_24": "int32",
    "PCM_32": "int32",
    "PCM_U8": "uint8",
    "FLOAT": "float32",
    "DOUBLE": "float64",
}


@dataclass(frozen=True)
class EspecificacionStem:
    """Un stem del tema sintético a construir.

    `n_muestras=None` reutiliza el número de muestras de la mezcla
    (`n_muestras_mezcla` de `construir_tema_sintetico`) -- pásalo
    explícito para simular una discrepancia de longitud entre este stem
    y la mezcla.

    `escribir_archivo=None` sigue a `audio_rendered` (coherente con el
    dataset real: un stem no renderizado nunca tuvo archivo). Pásalo en
    `False` explícito junto con `audio_rendered=True` para simular un
    archivo que los metadatos prometen pero que no está en disco.
    """

    identificador: str
    inst_class: str
    audio_rendered: bool = True
    midi_program_name: str = "Clean Electric Guitar"
    n_muestras: int | None = None
    escribir_archivo: bool | None = None
    subtype: str = "PCM_16"


def construir_tema_sintetico(
    tmp_path: Path,
    tema_id: str = "Track00001",
    frecuencia_muestreo: int = 44100,
    n_muestras_mezcla: int = 200,
    stems: tuple[EspecificacionStem, ...] = (),
    escribir_mix: bool = True,
    subtype_mezcla: str = "PCM_16",
    semilla: int = 0,
) -> Path:
    """Construye `tmp_path/tema_id/{metadata.yaml, mix.flac, stems/*.flac}`
    y devuelve `tmp_path` -- la raíz que espera `leer_tema(tema_id,
    root_dir)` (contracts/leer_tema.md)."""
    tema_dir = tmp_path / tema_id
    stems_dir = tema_dir / "stems"
    stems_dir.mkdir(parents=True)

    rng = np.random.default_rng(semilla)

    if escribir_mix:
        _escribir_flac(
            tema_dir / "mix.flac", rng, n_muestras_mezcla, frecuencia_muestreo, subtype_mezcla
        )

    metadata_stems: dict[str, dict[str, Any]] = {}
    for spec in stems:
        n_muestras = spec.n_muestras if spec.n_muestras is not None else n_muestras_mezcla
        escribir = (
            spec.escribir_archivo if spec.escribir_archivo is not None else spec.audio_rendered
        )
        if escribir:
            _escribir_flac(
                stems_dir / f"{spec.identificador}.flac",
                rng,
                n_muestras,
                frecuencia_muestreo,
                spec.subtype,
            )
        metadata_stems[spec.identificador] = {
            "inst_class": spec.inst_class,
            "audio_rendered": spec.audio_rendered,
            "midi_program_name": spec.midi_program_name,
        }

    metadata: dict[str, Any] = {
        "UUID": tema_id,
        "audio_dir": "stems",
        "stems": metadata_stems,
    }
    (tema_dir / "metadata.yaml").write_text(yaml.safe_dump(metadata, sort_keys=False))

    return tmp_path


def _escribir_flac(
    path: Path,
    rng: np.random.Generator,
    n_muestras: int,
    frecuencia_muestreo: int,
    subtype: str,
) -> None:
    dtype = np.dtype(_SUBTYPE_A_DTYPE[subtype])
    if np.issubdtype(dtype, np.integer):
        info = np.iinfo(dtype)
        muestras = rng.integers(info.min, info.max, size=n_muestras, dtype=dtype)
    else:
        muestras = rng.uniform(-1.0, 1.0, size=n_muestras).astype(dtype)
    sf.write(str(path), muestras, frecuencia_muestreo, subtype=subtype)
