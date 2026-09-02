"""Property tests (Hypothesis) para `leer_tema()` (T011-T012 de
`specs/001-lectura-tema-slakh2100/tasks.md`, User Story 1/P1).

La estrategia muestrea `subtype` del dominio real que soporta
`_decodificar_audio` (`_SUBTYPE_A_DTYPE`, en el propio módulo de
producción) en vez de una lista ad hoc escrita a mano en el test (ver
AGENTS.md "Property tests: muestrea del dominio real").

Nota sobre "la frecuencia declarada por el conjunto" (FR-007): en
Slakh2100 esa frecuencia no vive en un campo separado de
`metadata.yaml` -- está embebida en el propio encabezado de cada
`.flac` (research.md #1: `soundfile.info().samplerate`), y todos los
archivos de un mismo tema la comparten. Por eso este test la modela
como el parámetro `frecuencia_muestreo` que `construir_tema_sintetico`
usa para escribir mezcla y stems -- exactamente el mismo valor que
`sf.info(...)` reportaría para cada archivo del tema (data-model.md,
campo `PistaAudio.frecuencia_muestreo`).

Cada ejemplo generado usa su propio directorio (`tmp_path_factory`, no
`tmp_path`): con `@given`, la función del test se invoca muchas veces
dentro de una sola llamada de pytest, y `tmp_path` sería el mismo
directorio para todas esas invocaciones -- `tmp_path_factory.mktemp(...)`
da un directorio nuevo por ejemplo.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
import pytest
import soundfile as sf
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.strategies import DrawFn

from guitar_tabs_analysis.ingestion.slakh2100 import _SUBTYPE_A_DTYPE, leer_tema
from tests.fixtures.slakh2100_fixture import EspecificacionStem, construir_tema_sintetico

# Dominio real de subtypes: intersección entre lo que `_decodificar_audio`
# sabe representar sin reescalar (las claves del mapeo de producción) y lo
# que el contenedor FLAC admite de verdad -- Slakh2100 se distribuye
# enteramente en `.flac` (research.md #1), y `libsndfile` solo admite
# PCM_S8/PCM_16/PCM_24 dentro de ese contenedor
# (`sf.available_subtypes("FLAC")`); `PCM_32`/`PCM_U8`/`FLOAT`/`DOUBLE` son
# subtypes reales para OTROS formatos que `_decodificar_audio` también
# sabe leer, pero no para el que este dataset usa -- muestrearlos aquí
# escribiría un `.flac` inválido, no ejercitaría un caso real del dominio.
_SUBTYPES_SOPORTADOS = tuple(
    subtype for subtype in _SUBTYPE_A_DTYPE if subtype in {"PCM_16", "PCM_24"}
)

_frecuencias_muestreo = st.sampled_from([8000, 16000, 22050, 44100, 48000, 96000])
_n_muestras_mezcla = st.integers(min_value=1, max_value=300)
_n_guitarras = st.integers(min_value=1, max_value=4)


@st.composite
def _especificaciones_de_tema(
    draw: DrawFn,
) -> tuple[int, int, str, tuple[EspecificacionStem, ...]]:
    """Genera (frecuencia_muestreo, n_muestras_mezcla, subtype_mezcla,
    stems de guitarra), cada stem con su propio `subtype` muestreado del
    dominio real."""
    frecuencia_muestreo = draw(_frecuencias_muestreo)
    n_muestras_mezcla = draw(_n_muestras_mezcla)
    subtype_mezcla = draw(st.sampled_from(_SUBTYPES_SOPORTADOS))
    n_guitarras = draw(_n_guitarras)
    stems = tuple(
        EspecificacionStem(
            identificador=f"S{indice:02d}",
            inst_class="Guitar",
            audio_rendered=True,
            subtype=draw(st.sampled_from(_SUBTYPES_SOPORTADOS)),
        )
        for indice in range(n_guitarras)
    )
    return frecuencia_muestreo, n_muestras_mezcla, subtype_mezcla, stems


@given(especificacion=_especificaciones_de_tema())
@settings(max_examples=50)
def test_mezcla_y_guitarras_comparten_longitud_y_frecuencia_de_muestreo(
    tmp_path_factory: pytest.TempPathFactory,
    especificacion: tuple[int, int, str, tuple[EspecificacionStem, ...]],
) -> None:
    """spec.md Acceptance Scenario US1.4, FR-006/FR-007: la mezcla y cada
    guitarra devuelta comparten longitud y frecuencia de muestreo, y esa
    frecuencia coincide con la declarada por el conjunto para el tema."""
    frecuencia_muestreo, n_muestras_mezcla, subtype_mezcla, stems = especificacion
    root_dir = construir_tema_sintetico(
        tmp_path_factory.mktemp("t011"),
        tema_id="TrackProp",
        frecuencia_muestreo=frecuencia_muestreo,
        n_muestras_mezcla=n_muestras_mezcla,
        subtype_mezcla=subtype_mezcla,
        stems=stems,
    )

    resultado = leer_tema("TrackProp", root_dir)

    assert resultado.mezcla.frecuencia_muestreo == frecuencia_muestreo
    assert len(resultado.mezcla.muestras) == n_muestras_mezcla
    assert len(resultado.guitarras) == len(stems)
    for guitarra in resultado.guitarras:
        assert guitarra.audio.frecuencia_muestreo == frecuencia_muestreo
        assert len(guitarra.audio.muestras) == len(resultado.mezcla.muestras)


# Dominio real e independiente del mapeo de producción `_SUBTYPE_A_DTYPE`:
# la correspondencia subtype -> dtype para PCM_16/PCM_24 es un hecho fijo
# del formato (no algo que este proyecto decida), así que se repite aquí a
# propósito en vez de importar `_SUBTYPE_A_DTYPE` -- si esa tabla de
# producción tuviera un error de mapeo, esta referencia independiente
# seguiría leyendo con el dtype correcto y lo detectaría (T012, SC-005).
_DTYPE_ESPERADO_POR_SUBTYPE = {"PCM_16": "int16", "PCM_24": "int32"}


def _leer_referencia(path: Path, subtype: str) -> npt.NDArray[Any]:
    dtype = _DTYPE_ESPERADO_POR_SUBTYPE[subtype]
    muestras, _ = sf.read(str(path), dtype=dtype, always_2d=False)
    return np.asarray(muestras)


@given(especificacion=_especificaciones_de_tema())
@settings(max_examples=50)
def test_muestras_identicas_al_archivo_de_origen_finitas_y_en_rango(
    tmp_path_factory: pytest.TempPathFactory,
    especificacion: tuple[int, int, str, tuple[EspecificacionStem, ...]],
) -> None:
    """spec.md Acceptance Scenario US1.5, SC-005: las muestras devueltas
    (mezcla y guitarras) son idénticas, entero a entero, a las del
    archivo de origen -- sin resampleo/normalización -- y además (FR-008)
    finitas y dentro del rango representable por su dtype."""
    frecuencia_muestreo, n_muestras_mezcla, subtype_mezcla, stems = especificacion
    tema_id = "TrackProp"
    root_dir = construir_tema_sintetico(
        tmp_path_factory.mktemp("t012"),
        tema_id=tema_id,
        frecuencia_muestreo=frecuencia_muestreo,
        n_muestras_mezcla=n_muestras_mezcla,
        subtype_mezcla=subtype_mezcla,
        stems=stems,
    )
    tema_dir = root_dir / tema_id

    resultado = leer_tema(tema_id, root_dir)

    referencia_mezcla = _leer_referencia(tema_dir / "mix.flac", subtype_mezcla)
    np.testing.assert_array_equal(resultado.mezcla.muestras, referencia_mezcla)
    _assert_finita_y_en_rango(resultado.mezcla.muestras)

    for guitarra, spec in zip(resultado.guitarras, stems, strict=True):
        referencia = _leer_referencia(
            tema_dir / "stems" / f"{spec.identificador}.flac", spec.subtype
        )
        np.testing.assert_array_equal(guitarra.audio.muestras, referencia)
        _assert_finita_y_en_rango(guitarra.audio.muestras)


def _assert_finita_y_en_rango(muestras: npt.NDArray[Any]) -> None:
    assert np.isfinite(muestras).all()
    info = np.iinfo(muestras.dtype)
    assert bool(np.all(muestras >= info.min))
    assert bool(np.all(muestras <= info.max))
