"""Métrica de detección de notas (capa `analytics`, importa de
`ingestion`, nunca al revés): tipos de dominio y funciones de User
Story 1 (`evaluar_subconjunto`, T006/T009) y User Story 3
(`ExclusionDeteccion`/`ResultadoDeteccionGrabacion`,
`clasificar_polifonia_en_instante`, `evaluar_grabacion`,
`agregar_conjunto` -- T016-T022) de
`specs/006-deteccion-notas-guitarra-limpia/tasks.md`.

`ExclusionDeteccion`/`ResultadoDeteccionGrabacion` viven aquí, no en
`deteccion.orquestador`: `agregar_conjunto` los necesita en su propia
firma pública, y `analytics` no puede importar de `deteccion` sin crear
una dependencia circular (research.md #11) -- `deteccion.orquestador`
los importa desde aquí.

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
2 o más -> "polifonica". Se calcula con `clasificar_polifonia_en_instante`
(T017, más abajo)."""


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


@dataclass(frozen=True)
class ExclusionDeteccion:
    """Una grabación apartada de la medición por fallo de inferencia
    (FR-012, data-model.md) -- vive aquí, no en `deteccion.orquestador`:
    `agregar_conjunto` (T021, más abajo) recibe `list[ResultadoDeteccionGrabacion]`
    en su propia firma pública, y `analytics` no puede importar de
    `deteccion` sin crear una dependencia circular (`deteccion` importa
    de las tres capas de abajo, nunca al revés -- research.md #11).
    `deteccion.orquestador` importa este tipo desde aquí."""

    grabacion_id: str
    detalle: str


@dataclass(frozen=True)
class ResultadoDeteccionGrabacion:
    """El resultado de medir una única grabación -- unión etiquetada,
    igual patrón que `ResultadoProcesamientoTema` del hito 1
    (`medicion.orquestador`). `notas_referencia`/`notas_estimadas` son
    `None` si y solo si `exclusion` no es `None` (data-model.md)."""

    grabacion_id: str
    notas_referencia: list[NotaReferencia] | None
    notas_estimadas: list[NotaEstimada] | None
    exclusion: ExclusionDeteccion | None


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


# ---------------------------------------------------------------------
# clasificar_polifonia_en_instante (T017) -- research.md #8, FR-006.
# ---------------------------------------------------------------------


def clasificar_polifonia_en_instante(
    instante_s: float, notas_referencia: list[NotaReferencia]
) -> ClasificacionPolifonia:
    """Clasifica un instante como `"polifonica"` o `"monofonica"`
    contando cuántos intervalos `[inicio_s, fin_s]` de `notas_referencia`
    solapan `instante_s` (solape parcial cuenta, incluido el borde exacto
    de un intervalo) -- contracts/deteccion.md postcondición 3.

    La fuente de la clasificación es SIEMPRE `notas_referencia` -- nunca
    ninguna nota estimada. Dos o más referencias solapando ->
    `"polifonica"`; 0 o 1 (incluido el caso degenerado de cero
    referencias) -> `"monofonica"` (FR-006)."""
    num_solapando = sum(1 for nota in notas_referencia if nota.inicio_s <= instante_s <= nota.fin_s)
    return "polifonica" if num_solapando >= 2 else "monofonica"


# ---------------------------------------------------------------------
# _particionar_por_polifonia -- helper compartido entre evaluar_grabacion
# (T019) y agregar_conjunto (T021): ambas necesitan clasificar las notas
# de UNA grabación (referencia y estimada) contra las referencias de esa
# MISMA grabación y partir en mono/poli -- extraído para no duplicar el
# bucle de clasificación dos veces (mismo criterio de extracción que
# `calcular_mediana_agregada`/`calcular_distribucion_referencias` en
# Feature 004, ver tasks.md T016-T024, "Reutilización sugerida").
# ---------------------------------------------------------------------


def _particionar_por_polifonia(
    notas_referencia: list[NotaReferencia],
    notas_estimadas: list[NotaEstimada],
) -> tuple[list[NotaReferencia], list[NotaReferencia], list[NotaEstimada], list[NotaEstimada]]:
    """Clasifica cada nota de UNA grabación (de referencia y estimada) en
    su propio inicio, SIEMPRE contra `notas_referencia` de esa misma
    grabación (FR-006, research.md #8) -- nunca contra `notas_estimadas`,
    ni para clasificar una nota de referencia ni para clasificar una
    estimada. Devuelve `(referencia_mono, referencia_poli, estimada_mono,
    estimada_poli)`."""
    referencia_mono: list[NotaReferencia] = []
    referencia_poli: list[NotaReferencia] = []
    for nota_ref in notas_referencia:
        if clasificar_polifonia_en_instante(nota_ref.inicio_s, notas_referencia) == "polifonica":
            referencia_poli.append(nota_ref)
        else:
            referencia_mono.append(nota_ref)

    estimada_mono: list[NotaEstimada] = []
    estimada_poli: list[NotaEstimada] = []
    for nota_est in notas_estimadas:
        if clasificar_polifonia_en_instante(nota_est.inicio_s, notas_referencia) == "polifonica":
            estimada_poli.append(nota_est)
        else:
            estimada_mono.append(nota_est)

    return referencia_mono, referencia_poli, estimada_mono, estimada_poli


# ---------------------------------------------------------------------
# evaluar_grabacion (T019) -- contracts/deteccion.md postcondición 4.
# ---------------------------------------------------------------------


def evaluar_grabacion(
    notas_referencia: list[NotaReferencia],
    notas_estimadas: list[NotaEstimada],
) -> tuple[ResultadoSubconjunto, ResultadoSubconjunto, ResultadoSubconjunto]:
    """Devuelve `(global, monofonico, polifonico)` para una grabación
    (contracts/deteccion.md postcondición 4): parte primero el conjunto
    de notas (referencia y estimada) en monofónico/polifónico vía
    `clasificar_polifonia_en_instante` (siempre contra `notas_referencia`,
    FR-006), y llama `evaluar_subconjunto` una vez por subconjunto --
    global (sin partir), monofónico, polifónico -- nunca calculando un
    emparejamiento global y dividiéndolo después."""
    referencia_mono, referencia_poli, estimada_mono, estimada_poli = _particionar_por_polifonia(
        notas_referencia, notas_estimadas
    )
    global_ = evaluar_subconjunto(notas_referencia, notas_estimadas)
    monofonico = evaluar_subconjunto(referencia_mono, estimada_mono)
    polifonico = evaluar_subconjunto(referencia_poli, estimada_poli)
    return global_, monofonico, polifonico


# ---------------------------------------------------------------------
# agregar_conjunto (T021) -- contracts/deteccion.md postcondición 5.
# ---------------------------------------------------------------------


def agregar_conjunto(
    resultados: list[ResultadoDeteccionGrabacion],
) -> tuple[ResultadoSubconjunto, ResultadoSubconjunto, ResultadoSubconjunto]:
    """Mismo cálculo que `evaluar_grabacion`, pero sobre el pool de todas
    las grabaciones no excluidas de `resultados` (contracts/deteccion.md
    postcondición 5): clasifica las notas de cada grabación contra las
    referencias de esa misma grabación (nunca cruzando grabaciones,
    `_particionar_por_polifonia`), acumula en tres pools (global/mono/
    poli) a través de todas las grabaciones no excluidas, y llama
    `evaluar_subconjunto` una vez por pool -- nunca promedia los
    resultados calculados por grabación (una grabación con muchas notas
    pesa más que una con pocas, por diseño)."""
    pool_referencia_global: list[NotaReferencia] = []
    pool_estimada_global: list[NotaEstimada] = []
    pool_referencia_mono: list[NotaReferencia] = []
    pool_referencia_poli: list[NotaReferencia] = []
    pool_estimada_mono: list[NotaEstimada] = []
    pool_estimada_poli: list[NotaEstimada] = []

    for resultado in resultados:
        if resultado.exclusion is not None:
            continue
        # Unión etiquetada (data-model.md): `exclusion is None` implica
        # que ambas listas de notas están presentes, nunca `None`.
        assert resultado.notas_referencia is not None
        assert resultado.notas_estimadas is not None

        pool_referencia_global.extend(resultado.notas_referencia)
        pool_estimada_global.extend(resultado.notas_estimadas)

        referencia_mono, referencia_poli, estimada_mono, estimada_poli = _particionar_por_polifonia(
            resultado.notas_referencia, resultado.notas_estimadas
        )
        pool_referencia_mono.extend(referencia_mono)
        pool_referencia_poli.extend(referencia_poli)
        pool_estimada_mono.extend(estimada_mono)
        pool_estimada_poli.extend(estimada_poli)

    global_ = evaluar_subconjunto(pool_referencia_global, pool_estimada_global)
    monofonico = evaluar_subconjunto(pool_referencia_mono, pool_estimada_mono)
    polifonico = evaluar_subconjunto(pool_referencia_poli, pool_estimada_poli)
    return global_, monofonico, polifonico
