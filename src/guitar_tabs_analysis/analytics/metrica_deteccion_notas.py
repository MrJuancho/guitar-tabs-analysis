"""Métrica de detección de notas (capa `analytics`, importa de
`ingestion`, nunca al revés): tipos de dominio y `evaluar_subconjunto()`
para User Story 1 de `specs/006-deteccion-notas-guitarra-limpia/tasks.md`
(T006, T009).

Este módulo, en su estado actual, cubre User Story 1 completa
(`NotaEstimada`, `ClasificacionPolifonia`, `ResultadoSubconjunto`,
`evaluar_subconjunto`) -- todavía SIN `clasificar_polifonia_en_instante`,
`evaluar_grabacion` ni `agregar_conjunto` (User Story 3, T017 en
adelante), ni `ExclusionDeteccion`/`ResultadoDeteccionGrabacion` (T016).

Ver `specs/006-deteccion-notas-guitarra-limpia/data-model.md` y
`specs/006-deteccion-notas-guitarra-limpia/contracts/deteccion.md` para
el contrato completo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import mir_eval.transcription
import mir_eval.util
import numpy as np

from guitar_tabs_analysis.ingestion.guitarset import NotaReferencia

# ---------------------------------------------------------------------
# Tipos de dominio (T006) -- todos inmutables: son el resultado de un
# cálculo, no construcción incremental (data-model.md).
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class NotaEstimada:
    """Una nota que `transcripcion.transcriptor.Transcriptor.transcribir()`
    predice sobre una grabación.

    `velocity`/`pitch_bend` de Basic Pitch no se conservan (research.md
    #1) -- ningún requisito de esta feature los necesita (FR-001 solo
    pide tono e inicio). `fin_s` se conserva aunque no participe del
    criterio de acierto (FR-004), como refinamiento futuro declarado."""

    tono_midi: float
    inicio_s: float
    fin_s: float


ClasificacionPolifonia = Literal["monofonica", "polifonica"]
"""Propiedad derivada, nunca persistida de forma independiente --
research.md #8: 0 o 1 referencias solapando un instante -> "monofonica";
2 o más -> "polifonica". La función que la calcula
(`clasificar_polifonia_en_instante`) es responsabilidad de User Story 3
(T017), no de este slice."""


@dataclass(frozen=True)
class ResultadoSubconjunto:
    """Precisión, exhaustividad y balance sobre un subconjunto de notas
    (global, monofónico, o polifónico).

    `precision`/`exhaustividad`/`balance_f1` son `None` cuando el
    subconjunto correspondiente (notas estimadas / notas de referencia)
    está vacío (FR-008) -- nunca una cifra calculada sobre un
    denominador cero. `num_notas_referencia`/`num_notas_estimadas` se
    reportan siempre, aunque sean 0."""

    precision: float | None
    exhaustividad: float | None
    balance_f1: float | None
    num_notas_referencia: int
    num_notas_estimadas: int


# ---------------------------------------------------------------------
# evaluar_subconjunto (T009) -- ver contracts/deteccion.md, postcondiciones
# 1 y 2 de `analytics.metrica_deteccion_notas`.
# ---------------------------------------------------------------------

TOLERANCIA_TONO_CENTS = 50.0
"""Convención MIREX Note Tracking (task 2), research.md #3 -- el default
real de `mir_eval.transcription.precision_recall_f1_overlap`
(`pitch_tolerance`), citado explícitamente en vez de inventado."""

VENTANA_INICIO_S = 0.05
"""50 ms, misma fuente que `TOLERANCIA_TONO_CENTS` -- el default real de
`onset_tolerance` de `mir_eval`."""


def evaluar_subconjunto(
    notas_referencia: list[NotaReferencia],
    notas_estimadas: list[NotaEstimada],
) -> ResultadoSubconjunto:
    """Acierto/emparejamiento vía `mir_eval.transcription` sobre un
    conjunto de notas SIN partir por polifonía (contracts/deteccion.md,
    postcondición 1) -- `evaluar_grabacion`/`agregar_conjunto` (User
    Story 3) son quienes invocan esto una vez por subconjunto.

    Guard explícito de listas vacías ANTES de invocar `mir_eval`
    (postcondición 2, FR-008): `mir_eval.transcription.precision_recall_f1_overlap`
    devuelve `(0.0, 0.0, 0.0, 0.0)` para AMBAS métricas cuando cualquiera
    de las dos listas está vacía -- sin distinguir cuál -- así que ese
    comportamiento crudo nunca se usa directamente; los tres casos de
    FR-008 se resuelven a mano, antes de llamar a la librería:

    - Ambas vacías: `precision`/`exhaustividad`/`balance_f1` en `None`
      (ningún denominador tiene sentido).
    - Solo `notas_referencia` vacía: `exhaustividad=None` (sin
      denominador), `precision=0.0` (ninguna estimada tiene con qué
      acertar, pero SÍ hay denominador -- `num_notas_estimadas`).
    - Solo `notas_estimadas` vacía: `precision=None` (sin denominador),
      `exhaustividad=0.0` (nada acertó, pero SÍ hay denominador --
      `num_notas_referencia`).
    """
    num_notas_referencia = len(notas_referencia)
    num_notas_estimadas = len(notas_estimadas)

    if num_notas_referencia == 0 and num_notas_estimadas == 0:
        return ResultadoSubconjunto(
            precision=None,
            exhaustividad=None,
            balance_f1=None,
            num_notas_referencia=0,
            num_notas_estimadas=0,
        )
    if num_notas_referencia == 0:
        return ResultadoSubconjunto(
            precision=0.0,
            exhaustividad=None,
            balance_f1=None,
            num_notas_referencia=0,
            num_notas_estimadas=num_notas_estimadas,
        )
    if num_notas_estimadas == 0:
        return ResultadoSubconjunto(
            precision=None,
            exhaustividad=0.0,
            balance_f1=None,
            num_notas_referencia=num_notas_referencia,
            num_notas_estimadas=0,
        )

    # `dtype=np.float64` explícito en las cuatro conversiones de abajo
    # sobrevive mutado a `dtype=None` (mutation testing, T009) --
    # equivalente confirmado: `np.array()` infiere `float64` de una lista
    # de `float` de Python sin necesidad del argumento explícito (mismo
    # patrón que `.astype(np.float64)` en `metrica_separacion.si_sdr`).
    # SIN `# pragma: no mutate` en ninguna de las cuatro, a propósito:
    # `mutmut` (verificado contra su código fuente real,
    # `mutmut/mutation/pragma_handling.py::PragmaVisitor.visit_SimpleStatementLine`)
    # solo reconoce un comentario `# pragma: no mutate` como el
    # `trailing_whitespace` de la sentencia COMPLETA, y lo asocia a la
    # línea donde esa sentencia EMPIEZA -- no a la línea física donde el
    # comentario queda escrito. Para las cuatro asignaciones de abajo
    # (que `ruff format` parte en varias líneas), eso significa que un
    # pragma puesto junto a `dtype=...` no suprime nada (verificado
    # empíricamente: el conteo total de mutantes generados no cambia), y
    # un pragma puesto en la línea donde la sentencia SÍ empieza
    # suprimiría también la mutación de la lista de comprensión, que es
    # real y está cubierta (mismo criterio que `always_2d=False` en
    # `ingestion.slakh2100._decodificar_audio`, que si cabe en una sola
    # línea física). Los cuatro sobrevivientes quedan documentados aquí,
    # sin pragma, en vez de un pragma que aparentaría suprimirlos sin
    # hacerlo de verdad.
    ref_intervals = np.array(
        [[nota.inicio_s, nota.fin_s] for nota in notas_referencia], dtype=np.float64
    )
    ref_pitches = np.array(
        [mir_eval.util.midi_to_hz(nota.tono_midi) for nota in notas_referencia],
        dtype=np.float64,
    )
    est_intervals = np.array(
        [[nota.inicio_s, nota.fin_s] for nota in notas_estimadas], dtype=np.float64
    )
    est_pitches = np.array(
        [mir_eval.util.midi_to_hz(nota.tono_midi) for nota in notas_estimadas],
        dtype=np.float64,
    )

    # `onset_tolerance=VENTANA_INICIO_S`/`pitch_tolerance=TOLERANCIA_TONO_CENTS`
    # sobreviven mutados a la línea completa OMITIDA (mutation testing,
    # T009) -- equivalente confirmado: sin el argumento explícito,
    # `mir_eval` cae a sus propios defaults (`onset_tolerance=0.05`,
    # `pitch_tolerance=50.0`, research.md #3), que son EXACTAMENTE los
    # valores de `VENTANA_INICIO_S`/`TOLERANCIA_TONO_CENTS` por diseño (se
    # declaran explícitos por claridad de API/FR-003, no porque difieran
    # del default). Mutarlos a `None` sí se detecta (mata la comparación
    # numérica dentro de `mir_eval`) -- mismo motivo que arriba (la
    # llamada completa es una única sentencia multilínea): un pragma aquí
    # no suprimiría selectivamente estas dos líneas sin también suprimir
    # la mutación real de `ref_intervals`/`ref_pitches`/etc. arriba en la
    # misma sentencia, así que tampoco lleva `# pragma: no mutate`.
    precision, exhaustividad, balance_f1, _ = mir_eval.transcription.precision_recall_f1_overlap(
        ref_intervals,
        ref_pitches,
        est_intervals,
        est_pitches,
        onset_tolerance=VENTANA_INICIO_S,
        pitch_tolerance=TOLERANCIA_TONO_CENTS,
        offset_ratio=None,
    )

    return ResultadoSubconjunto(
        precision=float(precision),
        exhaustividad=float(exhaustividad),
        balance_f1=float(balance_f1),
        num_notas_referencia=num_notas_referencia,
        num_notas_estimadas=num_notas_estimadas,
    )
