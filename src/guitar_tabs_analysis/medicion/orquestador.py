"""Orquestación de la medición del hito 1 (capa `medicion`, importa de
`ingestion`, `separacion` y `analytics` a la vez -- excluida a propósito
del contrato de layers de import-linter, research.md #6 de
`specs/004-medicion-linea-base/`): dado un modo de ejecución, procesa cada
tema de a uno (`leer_tema` → `separar_guitarra` → `emparejar_tema`),
persiste su resultado de inmediato, y al completar todos los temas de una
corrida ensambla un único `ArtefactoMedicion`.

Este módulo no importa `torch` ni `demucs` -- recibe un `Separador` ya
construido (mismo patrón que `separacion.separador`). El adaptador real
que sí los importa vive en `medicion.cli`.

Ver `specs/004-medicion-linea-base/data-model.md` y
`specs/004-medicion-linea-base/contracts/medicion.md` para el contrato
completo.
"""

from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from guitar_tabs_analysis.analytics.metrica_separacion import (
    ReferenciaEmparejada,
    ReferenciaSinPareja,
    ReporteTema,
    emparejar_tema,
)
from guitar_tabs_analysis.ingestion.slakh2100 import (
    ArchivoAudioNoLegibleError,
    LongitudInconsistenteError,
    TemaNoExisteError,
    leer_tema,
)
from guitar_tabs_analysis.separacion.separador import (
    SeparacionFallidaError,
    Separador,
    TransformacionDeclarada,
    separar_guitarra,
)

# ---------------------------------------------------------------------
# Tipos de dominio (T006) -- todos inmutables: son el resultado de
# procesar un tema o de ensamblar una corrida, no construcción
# incremental (data-model.md).
# ---------------------------------------------------------------------

ModoEjecucion = Literal["submuestra_hito1", "conjunto_completo"]
"""Los dos modos de FR-001/FR-002/FR-003, mutuamente excluyentes y sin
valor por defecto (FR-004)."""

MotivoExclusionMedicion = Literal["fallo_procesamiento", "sin_guitarra_referencia"]
"""Dos valores, no los tres de `MotivoExclusion` de la Feature 002: el
tercero (`"directorio_omitido"`) nunca puede ocurrir aquí, porque
`construir_lista_temas` no lista jamás el directorio `omitted`
(research.md #7)."""


@dataclass(frozen=True)
class ExclusionMedicion:
    """Un tema apartado del resultado agregado de una corrida, con su
    motivo (FR-006, FR-010)."""

    tema_id: str
    motivo: MotivoExclusionMedicion
    detalle: str


@dataclass(frozen=True)
class ResultadoProcesamientoTema:
    """El resultado de procesar un único tema (`procesar_tema`, FR-005) --
    una unión etiquetada, nunca ambos casos a la vez (`reporte`/
    `exclusion`)."""

    tema_id: str
    reporte: ReporteTema | None
    exclusion: ExclusionMedicion | None
    transformaciones: list[TransformacionDeclarada] = field(default_factory=list)


@dataclass(frozen=True)
class ManifiestoCorrida:
    """Los metadatos de identidad de una corrida, persistidos junto con
    el progreso (FR-008a) -- lo que permite reconocer, al reanudar, si se
    trata de la misma corrida o de una con un modelo distinto."""

    modo: ModoEjecucion
    semilla: int | None
    firma_modelo: str
    temas: list[str]


class ModeloCambiadoError(Exception):
    """El progreso persistido de una corrida fue calculado con un modelo
    de firma distinta a la del `Separador` recibido en esta invocación
    (FR-008a) -- no es un "modo de fallo de tema", es un fallo de la
    corrida completa antes de procesar ningún tema."""

    def __init__(self, firma_esperada: str, firma_actual: str) -> None:
        self.firma_esperada = firma_esperada
        self.firma_actual = firma_actual
        super().__init__(
            f"El modelo declarado cambió desde la interrupción: el progreso "
            f"persistido se calculó con la firma '{firma_esperada}', pero el "
            f"modelo vigente tiene la firma '{firma_actual}'. No se reanuda "
            f"la corrida para no mezclar reportes de dos modelos distintos "
            f"en el mismo artefacto."
        )


# ---------------------------------------------------------------------
# procesar_tema (T008) -- ver contracts/medicion.md para el contrato
# completo.
# ---------------------------------------------------------------------

_FALLOS_DE_LECTURA = (TemaNoExisteError, ArchivoAudioNoLegibleError, LongitudInconsistenteError)


def procesar_tema(tema_id: str, root_dir: Path, separador: Separador) -> ResultadoProcesamientoTema:
    """Lee, separa y mide un único tema (contracts/medicion.md).

    Nunca propaga una excepción propia de Features 001/003: todo fallo de
    tema se convierte en un `ExclusionMedicion` con motivo
    `"fallo_procesamiento"` (FR-006). Un tema sin ninguna guitarra de
    referencia se excluye con motivo `"sin_guitarra_referencia"` antes de
    intentar la separación (no hay nada contra qué medir). En el camino
    feliz, `transformaciones` es el eco de `ResultadoSeparacionTema.transformaciones`
    (Feature 003, FR-010/SC-007) -- vacía en cualquier otro caso, porque
    `separar_guitarra` nunca llegó a correr con éxito.
    """
    try:
        lectura = leer_tema(tema_id, root_dir)
    except _FALLOS_DE_LECTURA as causa:
        return ResultadoProcesamientoTema(
            tema_id=tema_id,
            reporte=None,
            exclusion=ExclusionMedicion(tema_id, "fallo_procesamiento", str(causa)),
            transformaciones=[],
        )

    if not lectura.guitarras:
        return ResultadoProcesamientoTema(
            tema_id=tema_id,
            reporte=None,
            exclusion=ExclusionMedicion(tema_id, "sin_guitarra_referencia", ""),
            transformaciones=[],
        )

    try:
        resultado_separacion = separar_guitarra(tema_id, lectura.mezcla, separador)
    except SeparacionFallidaError as causa:
        return ResultadoProcesamientoTema(
            tema_id=tema_id,
            reporte=None,
            exclusion=ExclusionMedicion(tema_id, "fallo_procesamiento", str(causa)),
            transformaciones=[],
        )

    reporte = emparejar_tema(tema_id, lectura.guitarras, resultado_separacion.estimaciones)
    return ResultadoProcesamientoTema(
        tema_id=tema_id,
        reporte=reporte,
        exclusion=None,
        transformaciones=resultado_separacion.transformaciones,
    )


# ---------------------------------------------------------------------
# Persistencia atómica por tema (T010) -- research.md #5.
# ---------------------------------------------------------------------


def _sanear_tema_id(tema_id: str) -> str:
    """`tema_id` viene calificado por split (`"validation/Track00001"`,
    research.md #3) -- el `/` se reemplaza para que sea un único nombre
    de archivo plano, no una ruta con subdirectorios."""
    return tema_id.replace("/", "__")


def _reporte_a_dict(reporte: ReporteTema) -> dict[str, Any]:
    return {
        "tema_id": reporte.tema_id,
        "num_referencias": reporte.num_referencias,
        "num_estimaciones_recibidas": reporte.num_estimaciones_recibidas,
        "emparejadas": [
            {
                "identificador_referencia": e.identificador_referencia,
                "identificador_estimacion": e.identificador_estimacion,
                "si_sdr": e.si_sdr,
            }
            for e in reporte.emparejadas
        ],
        "sin_pareja": [
            {"identificador_referencia": s.identificador_referencia, "motivo": s.motivo}
            for s in reporte.sin_pareja
        ],
    }


def _reporte_desde_dict(datos: dict[str, Any]) -> ReporteTema:
    return ReporteTema(
        tema_id=datos["tema_id"],
        num_referencias=datos["num_referencias"],
        num_estimaciones_recibidas=datos["num_estimaciones_recibidas"],
        emparejadas=[ReferenciaEmparejada(**e) for e in datos["emparejadas"]],
        sin_pareja=[ReferenciaSinPareja(**s) for s in datos["sin_pareja"]],
    )


def _transformacion_a_dict(transformacion: TransformacionDeclarada) -> dict[str, Any]:
    return {
        "tipo": transformacion.tipo,
        "direccion": transformacion.direccion,
        "aplicada": transformacion.aplicada,
        "detalle": transformacion.detalle,
    }


def _transformacion_desde_dict(datos: dict[str, Any]) -> TransformacionDeclarada:
    return TransformacionDeclarada(
        tipo=datos["tipo"],
        direccion=datos["direccion"],
        aplicada=datos["aplicada"],
        detalle=datos["detalle"],
    )


def _resultado_procesamiento_a_dict(resultado: ResultadoProcesamientoTema) -> dict[str, Any]:
    return {
        "tema_id": resultado.tema_id,
        "reporte": _reporte_a_dict(resultado.reporte) if resultado.reporte is not None else None,
        "exclusion": (
            {
                "tema_id": resultado.exclusion.tema_id,
                "motivo": resultado.exclusion.motivo,
                "detalle": resultado.exclusion.detalle,
            }
            if resultado.exclusion is not None
            else None
        ),
        "transformaciones": [_transformacion_a_dict(t) for t in resultado.transformaciones],
    }


def _resultado_procesamiento_desde_dict(datos: dict[str, Any]) -> ResultadoProcesamientoTema:
    datos_exclusion = datos["exclusion"]
    return ResultadoProcesamientoTema(
        tema_id=datos["tema_id"],
        reporte=_reporte_desde_dict(datos["reporte"]) if datos["reporte"] is not None else None,
        exclusion=ExclusionMedicion(**datos_exclusion) if datos_exclusion is not None else None,
        transformaciones=[_transformacion_desde_dict(t) for t in datos["transformaciones"]],
    )


def escribir_progreso_tema(directorio: Path, resultado: ResultadoProcesamientoTema) -> None:
    """Persiste `resultado` de forma atómica: escribe a un archivo
    temporal en `directorio` y lo renombra con `os.replace()` al nombre
    final -- una interrupción a mitad de escritura nunca deja el archivo
    final corrupto ni a medias (research.md #5: `os.replace()` es atómico
    en el mismo sistema de archivos POSIX)."""
    directorio.mkdir(parents=True, exist_ok=True)
    nombre_final = f"{_sanear_tema_id(resultado.tema_id)}.json"
    destino = directorio / nombre_final
    temporal = directorio / f"{nombre_final}.tmp"
    temporal.write_text(json.dumps(_resultado_procesamiento_a_dict(resultado)))
    os.replace(temporal, destino)


def leer_progreso_tema(directorio: Path, tema_id: str) -> ResultadoProcesamientoTema | None:
    """`None` si el archivo final de `tema_id` no existe -- incluyendo el
    caso de un archivo temporal presente sin que el renombre haya
    ocurrido todavía (interrupción a mitad de `escribir_progreso_tema`):
    ese archivo temporal nunca se confunde con uno completo, porque esta
    función solo mira el nombre final."""
    destino = directorio / f"{_sanear_tema_id(tema_id)}.json"
    if not destino.exists():
        return None
    return _resultado_procesamiento_desde_dict(json.loads(destino.read_text()))


# ---------------------------------------------------------------------
# construir_lista_temas (T012) -- ver contracts/medicion.md para el
# contrato completo.
# ---------------------------------------------------------------------

SEMILLA_SUBMUESTRA_HITO1 = 20260904
"""research.md #9 de la Feature 003 / Principio VII de la constitución --
la misma semilla que `ejecutar_corrida` (T018) declara en el manifiesto
de una corrida `"submuestra_hito1"`, para que ambos usos nunca diverjan."""


def construir_lista_temas(
    modo: ModoEjecucion,
    root_dir: Path,
    *,
    tamano_submuestra: int = 40,
    semilla_submuestra: int = SEMILLA_SUBMUESTRA_HITO1,
) -> list[str]:
    """Determina la lista completa de identificadores de tema
    (calificados por split, research.md #3) para `modo` -- FR-001.

    `"submuestra_hito1"`: muestreo aleatorio reproducible sobre
    `validation/` (research.md #9 de la Feature 003 / Principio VII de la
    constitución). `"conjunto_completo"`: unión de `train/` y
    `validation/`, sin muestreo -- **nunca** enumera `root_dir / "test"`
    ni `root_dir / "omitted"` (FR-014, research.md #7): no hay ninguna
    rama de código que pueda alcanzarlos.
    """
    if modo == "submuestra_hito1":
        candidatos = sorted(os.listdir(root_dir / "validation"))
        seleccionados = random.Random(semilla_submuestra).sample(candidatos, tamano_submuestra)
        return [f"validation/{tema}" for tema in seleccionados]
    if modo == "conjunto_completo":
        temas_train = sorted(os.listdir(root_dir / "train"))
        temas_validation = sorted(os.listdir(root_dir / "validation"))
        return [f"train/{tema}" for tema in temas_train] + [
            f"validation/{tema}" for tema in temas_validation
        ]
    raise ValueError(f"Modo de ejecución desconocido: {modo!r}")


# ---------------------------------------------------------------------
# Manifiesto de corrida (T014) -- lectura/escritura simple, sin
# validación de firma todavía (eso es User Story 2, T023).
# ---------------------------------------------------------------------

_NOMBRE_MANIFIESTO = "manifiesto.json"


def escribir_manifiesto(directorio: Path, manifiesto: ManifiestoCorrida) -> None:
    """Mismo mecanismo de escritura atómica que `escribir_progreso_tema`
    (research.md #5) -- el manifiesto se escribe una sola vez por corrida,
    pero una interrupción a mitad de esa única escritura no debe dejarlo
    corrupto para la próxima invocación."""
    directorio.mkdir(parents=True, exist_ok=True)
    destino = directorio / _NOMBRE_MANIFIESTO
    temporal = directorio / f"{_NOMBRE_MANIFIESTO}.tmp"
    temporal.write_text(
        json.dumps(
            {
                "modo": manifiesto.modo,
                "semilla": manifiesto.semilla,
                "firma_modelo": manifiesto.firma_modelo,
                "temas": manifiesto.temas,
            }
        )
    )
    os.replace(temporal, destino)


def leer_manifiesto(directorio: Path) -> ManifiestoCorrida | None:
    """`None` si `directorio` no tiene ningún manifiesto todavía (primera
    invocación de una corrida)."""
    destino = directorio / _NOMBRE_MANIFIESTO
    if not destino.exists():
        return None
    datos = json.loads(destino.read_text())
    return ManifiestoCorrida(
        modo=datos["modo"],
        semilla=datos["semilla"],
        firma_modelo=datos["firma_modelo"],
        temas=datos["temas"],
    )
