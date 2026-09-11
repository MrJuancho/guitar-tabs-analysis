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
    verdaderos_positivos: int


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


def _resultado_desde_conteos(
    verdaderos_positivos: int,
    num_notas_referencia: int,
    num_notas_estimadas: int,
) -> ResultadoSubconjunto:
    """Deriva `ResultadoSubconjunto` de tres conteos ya resueltos --
    compartido entre `evaluar_subconjunto` (conteo de UNA llamada a
    `mir_eval.transcription.match_notes`) y `agregar_conjunto` (conteos ya
    SUMADOS entre grabaciones, research.md #16) para no duplicar el guard
    de denominador-cero (FR-008) en dos lugares.

    Mismos tres casos de FR-008, resueltos antes de dividir:

    - Ambas vacías: `precision`/`exhaustividad`/`balance_f1` en `None`
      (ningún denominador tiene sentido).
    - Solo `num_notas_referencia == 0`: `exhaustividad=None` (sin
      denominador), `precision=0.0` (ninguna estimada tiene con qué
      acertar, pero SÍ hay denominador -- `num_notas_estimadas`).
    - Solo `num_notas_estimadas == 0`: `precision=None` (sin
      denominador), `exhaustividad=0.0` (nada acertó, pero SÍ hay
      denominador -- `num_notas_referencia`).
    - Ninguna vacía: `precision=TP/num_est`, `exhaustividad=TP/num_ref`,
      `balance_f1=mir_eval.util.f_measure(precision, exhaustividad)` --
      misma fórmula exacta que `mir_eval.transcription.precision_recall_f1_overlap`
      aplica internamente (verificado línea por línea contra su código
      fuente real, research.md #16)."""
    if num_notas_referencia == 0 and num_notas_estimadas == 0:
        return ResultadoSubconjunto(
            precision=None,
            exhaustividad=None,
            balance_f1=None,
            num_notas_referencia=0,
            num_notas_estimadas=0,
            verdaderos_positivos=0,
        )
    if num_notas_referencia == 0:
        return ResultadoSubconjunto(
            precision=0.0,
            exhaustividad=None,
            balance_f1=None,
            num_notas_referencia=0,
            num_notas_estimadas=num_notas_estimadas,
            verdaderos_positivos=verdaderos_positivos,
        )
    if num_notas_estimadas == 0:
        return ResultadoSubconjunto(
            precision=None,
            exhaustividad=0.0,
            balance_f1=None,
            num_notas_referencia=num_notas_referencia,
            num_notas_estimadas=0,
            verdaderos_positivos=verdaderos_positivos,
        )

    precision = verdaderos_positivos / num_notas_estimadas
    exhaustividad = verdaderos_positivos / num_notas_referencia
    balance_f1 = mir_eval.util.f_measure(precision, exhaustividad)
    return ResultadoSubconjunto(
        precision=precision,
        exhaustividad=exhaustividad,
        balance_f1=balance_f1,
        num_notas_referencia=num_notas_referencia,
        num_notas_estimadas=num_notas_estimadas,
        verdaderos_positivos=verdaderos_positivos,
    )


def _emparejar(
    notas_referencia: list[NotaReferencia],
    notas_estimadas: list[NotaEstimada],
) -> list[tuple[int, int]]:
    """Ejecuta `mir_eval.transcription.match_notes` UNA vez sobre las
    notas de UNA grabación (o un subconjunto de ellas) y devuelve los
    pares `(índice_referencia, índice_estimada)` resueltos -- extraído de
    `evaluar_subconjunto` (research.md #17) para que `evaluar_grabacion`
    pueda reutilizar el MISMO emparejamiento al derivar la partición
    mono/poli (FR-014), en vez de volver a invocar `match_notes` de forma
    independiente por subconjunto (research.md #9, superado).

    Guard explícito de listas vacías ANTES de invocar `mir_eval`
    (FR-008): `match_notes` no se invoca en absoluto si cualquiera de las
    dos listas está vacía."""
    if not notas_referencia or not notas_estimadas:
        return []

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

    # Misma validación que `precision_recall_f1_overlap` hacía por
    # dentro antes de emparejar (research.md #16) -- llamada
    # explícitamente ahora que se invoca `match_notes` directamente:
    # formas, longitudes consistentes entre intervalos/tonos, y tonos
    # estrictamente positivos.
    mir_eval.transcription.validate(ref_intervals, ref_pitches, est_intervals, est_pitches)

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
    # Anotación explícita en la asignación, no en el `return` directo:
    # `mir_eval` no distribuye stubs (`ignore_missing_imports`, arriba),
    # así que `match_notes(...)` es `Any` para mypy -- devolverlo tal
    # cual dispara `no-any-return` en modo strict. Asignar primero a una
    # variable con el tipo declarado fija el tipo estático aquí, en el
    # único lugar de todo el módulo donde `mir_eval` cruza la frontera de
    # tipos sin anotar.
    matching: list[tuple[int, int]] = mir_eval.transcription.match_notes(
        ref_intervals,
        ref_pitches,
        est_intervals,
        est_pitches,
        onset_tolerance=VENTANA_INICIO_S,
        pitch_tolerance=TOLERANCIA_TONO_CENTS,
        offset_ratio=None,
    )
    return matching


def evaluar_subconjunto(
    notas_referencia: list[NotaReferencia],
    notas_estimadas: list[NotaEstimada],
) -> ResultadoSubconjunto:
    """Acierto/emparejamiento vía `mir_eval.transcription.match_notes`
    sobre las notas de UNA grabación (o un subconjunto de ellas, mono/
    poli) -- SIN partir por polifonía dentro de esta función
    (contracts/deteccion.md, postcondición 1). MUST NOT recibir notas de
    más de una grabación a la vez (research.md #16, FR-013): esta
    función asume que ambas listas pertenecen a la MISMA grabación, no lo
    verifica por sí misma -- es responsabilidad de quien la invoca
    (`evaluar_grabacion`/`agregar_conjunto`).

    Delega el emparejamiento a `_emparejar` (research.md #17) para
    exponer `verdaderos_positivos` (`len(matching)`) -- research.md #16:
    verificado línea por línea contra el código fuente real de
    `precision_recall_f1_overlap` que internamente hace exactamente
    `matching = match_notes(...)`, `precision = len(matching)/len(est_pitches)`,
    `recall = len(matching)/len(ref_pitches)`,
    `f_measure = mir_eval.util.f_measure(precision, recall)` -- mismo
    resultado exacto, ahora con el conteo intermedio expuesto para que
    `agregar_conjunto` pueda sumarlo entre grabaciones sin reemparejar."""
    matching = _emparejar(notas_referencia, notas_estimadas)
    return _resultado_desde_conteos(len(matching), len(notas_referencia), len(notas_estimadas))


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
# evaluar_grabacion (T019) -- contracts/deteccion.md postcondición 4,
# corregida en research.md #17/FR-014: un ÚNICO emparejamiento por
# grabación, partición mono/poli HEREDADA de él -- nunca reclasificando
# ni reemparejando cada lado por separado (research.md #9, superado).
# ---------------------------------------------------------------------


def evaluar_grabacion(
    notas_referencia: list[NotaReferencia],
    notas_estimadas: list[NotaEstimada],
) -> tuple[ResultadoSubconjunto, ResultadoSubconjunto, ResultadoSubconjunto]:
    """Devuelve `(global, monofonico, polifonico)` para una grabación
    (contracts/deteccion.md postcondición 4, research.md #17): empareja
    UNA sola vez (`_emparejar`), y cada par `(ref_idx, est_idx)` resuelto
    hereda la clasificación de SU nota de referencia
    (`clasificar_polifonia_en_instante`, siempre contra
    `notas_referencia`, FR-006) -- la nota estimada del par NUNCA se
    reevalúa por su propio inicio (FR-014): si se hiciera, un par cuya
    referencia cae en un instante polifónico pero cuya estimada empareja
    unos milisegundos fuera de esa densidad (dentro de la ventana de
    50ms de `mir_eval`) se partiría entre dos subconjuntos distintos y
    desaparecería de ambos, aunque sea un acierto real en el global
    (el defecto medido en research.md #17: 7313 de 36995 verdaderos
    positivos perdidos sobre `mediciones/deteccion_medibles.json`).

    Cada nota de referencia (emparejada o no) sigue clasificándose por su
    propio inicio, sin cambios (FR-006). Cada nota estimada que NO
    aparece en ningún par (falso positivo) se clasifica por la regla
    general de `clasificar_polifonia_en_instante` evaluada en su propio
    inicio -- no hay ninguna referencia de la cual heredar (research.md
    #8, alcance corregido: aplica solo a estimadas sin pareja)."""
    matching = _emparejar(notas_referencia, notas_estimadas)
    global_ = _resultado_desde_conteos(len(matching), len(notas_referencia), len(notas_estimadas))

    clase_por_referencia = [
        clasificar_polifonia_en_instante(nota.inicio_s, notas_referencia)
        for nota in notas_referencia
    ]
    ref_mono = sum(1 for clase in clase_por_referencia if clase == "monofonica")
    ref_poli = sum(1 for clase in clase_por_referencia if clase == "polifonica")

    clase_por_estimada_emparejada: dict[int, ClasificacionPolifonia] = {
        est_idx: clase_por_referencia[ref_idx] for ref_idx, est_idx in matching
    }
    tp_mono = sum(1 for clase in clase_por_estimada_emparejada.values() if clase == "monofonica")
    tp_poli = sum(1 for clase in clase_por_estimada_emparejada.values() if clase == "polifonica")

    est_mono = est_poli = 0
    for est_idx, nota_est in enumerate(notas_estimadas):
        if est_idx in clase_por_estimada_emparejada:
            clase = clase_por_estimada_emparejada[est_idx]
        else:
            clase = clasificar_polifonia_en_instante(nota_est.inicio_s, notas_referencia)
        if clase == "polifonica":
            est_poli += 1
        else:
            est_mono += 1

    monofonico = _resultado_desde_conteos(tp_mono, ref_mono, est_mono)
    polifonico = _resultado_desde_conteos(tp_poli, ref_poli, est_poli)
    return global_, monofonico, polifonico


# ---------------------------------------------------------------------
# agregar_conjunto (T021) -- contracts/deteccion.md postcondición 5.
# ---------------------------------------------------------------------


def agregar_conjunto(
    resultados: list[ResultadoDeteccionGrabacion],
) -> tuple[ResultadoSubconjunto, ResultadoSubconjunto, ResultadoSubconjunto]:
    """Agrega sobre todas las grabaciones no excluidas de `resultados`
    (contracts/deteccion.md postcondición 5, corregida en
    research.md #16 tras el hallazgo de OOM/corrección de
    `/speckit-implement`): emparejamiento SIEMPRE dentro de cada
    grabación (`evaluar_grabacion`, una vez por grabación no excluida)
    -- MUST NOT juntar notas crudas de grabaciones distintas antes de
    emparejar (FR-013). Acumula, para cada uno de los tres subconjuntos
    (global/mono/poli), los conteos ya resueltos por grabación
    (`verdaderos_positivos`, `num_notas_referencia`, `num_notas_estimadas`)
    SUMADOS a través de todas las grabaciones no excluidas, y deriva
    precisión/exhaustividad/balance de esa suma (`_resultado_desde_conteos`)
    -- nunca promedia los `ResultadoSubconjunto` calculados por grabación
    (una grabación con muchas notas pesa más que una con pocas, por
    diseño), y nunca empareja notas de una grabación contra las de otra
    (research.md #16: aciertos espurios entre clips sin relación
    temporal, además del costo cuadrático en memoria del pool)."""
    tp_global = num_ref_global = num_est_global = 0
    tp_mono = num_ref_mono = num_est_mono = 0
    tp_poli = num_ref_poli = num_est_poli = 0

    for resultado in resultados:
        if resultado.exclusion is not None:
            continue
        # Unión etiquetada (data-model.md): `exclusion is None` implica
        # que ambas listas de notas están presentes, nunca `None`.
        assert resultado.notas_referencia is not None
        assert resultado.notas_estimadas is not None

        global_grab, mono_grab, poli_grab = evaluar_grabacion(
            resultado.notas_referencia, resultado.notas_estimadas
        )

        tp_global += global_grab.verdaderos_positivos
        num_ref_global += global_grab.num_notas_referencia
        num_est_global += global_grab.num_notas_estimadas

        tp_mono += mono_grab.verdaderos_positivos
        num_ref_mono += mono_grab.num_notas_referencia
        num_est_mono += mono_grab.num_notas_estimadas

        tp_poli += poli_grab.verdaderos_positivos
        num_ref_poli += poli_grab.num_notas_referencia
        num_est_poli += poli_grab.num_notas_estimadas

    global_ = _resultado_desde_conteos(tp_global, num_ref_global, num_est_global)
    monofonico = _resultado_desde_conteos(tp_mono, num_ref_mono, num_est_mono)
    polifonico = _resultado_desde_conteos(tp_poli, num_ref_poli, num_est_poli)
    return global_, monofonico, polifonico
