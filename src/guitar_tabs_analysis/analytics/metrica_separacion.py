"""Métrica de separación de guitarra (capa `analytics`, importa de
`ingestion`, nunca al revés): dada la colección de pistas de guitarra
de referencia y una colección de estimaciones de un mismo tema,
calcula SI-SDR (*Scale-Invariant Signal-to-Distortion Ratio*) por par
(`si_sdr`), empareja por tema con asignación óptima (`emparejar_tema`),
y agrega sobre un conjunto de temas (`agregar_conjunto`).

Este módulo cubre las dos user stories completas de
`specs/002-metrica-separacion-guitarra/tasks.md`: T003-T017 (medición
por tema individual, User Story 1) y T018-T025 (agregación sobre un
conjunto con exclusiones y distribución, User Story 2).

Ver `specs/002-metrica-separacion-guitarra/data-model.md` y
`specs/002-metrica-separacion-guitarra/contracts/metrica_separacion.md`
para el contrato completo.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
import numpy.typing as npt
from scipy.optimize import linear_sum_assignment

from guitar_tabs_analysis.ingestion.slakh2100 import PistaAudio, PistaGuitarra

# ---------------------------------------------------------------------
# Tipos de dominio (T003) -- todos inmutables: son el resultado de un
# cálculo, no construcción incremental (data-model.md).
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Estimacion:
    """Una pista estimada por un separador (fuera de alcance de esta
    feature), con un identificador que el llamador le asigna para poder
    nombrarla en el reporte."""

    identificador: str
    audio: PistaAudio


MotivoSinPareja = Literal["sin_estimacion_disponible", "energia_nula", "estimacion_silenciosa"]


@dataclass(frozen=True)
class ReferenciaEmparejada:
    """Una referencia que quedó asociada a una estimación (FR-002)."""

    identificador_referencia: str
    identificador_estimacion: str
    si_sdr: float


@dataclass(frozen=True)
class ReferenciaSinPareja:
    """Una referencia del tema que no quedó asociada a ninguna
    estimación (FR-005), con el motivo explícito (FR-006/FR-003)."""

    identificador_referencia: str
    motivo: MotivoSinPareja


@dataclass(frozen=True)
class ReporteTema:
    """El resultado del cálculo sobre un tema individual (FR-004)."""

    tema_id: str
    num_referencias: int
    num_estimaciones_recibidas: int
    emparejadas: list[ReferenciaEmparejada] = field(default_factory=list)
    sin_pareja: list[ReferenciaSinPareja] = field(default_factory=list)


@dataclass(frozen=True)
class EntradaConjunto:
    """Un tema tal como lo aporta el llamador a la agregación sobre un
    conjunto (FR-007 en adelante), antes de aplicar las exclusiones."""

    tema_id: str
    referencias: list[PistaGuitarra]
    estimaciones: list[Estimacion]
    es_directorio_omitido: bool


MotivoExclusion = Literal["sin_guitarra_referencia", "directorio_omitido"]


@dataclass(frozen=True)
class Exclusion:
    """Un tema apartado del conjunto evaluado antes de agregar
    (FR-009/FR-010)."""

    tema_id: str
    motivo: MotivoExclusion


@dataclass(frozen=True)
class ResultadoAgregado:
    """El resultado de agregar la métrica sobre un conjunto de temas
    (FR-007 en adelante)."""

    mediana: float | None
    num_temas_evaluados: int
    distribucion_referencias_por_tema: dict[int, int]
    exclusiones: list[Exclusion] = field(default_factory=list)
    reportes_por_tema: list[ReporteTema] = field(default_factory=list)


# ---------------------------------------------------------------------
# Excepciones del contrato (T003) -- ver contracts/metrica_separacion.md.
# ---------------------------------------------------------------------


class EstimacionIncompatibleError(Exception):
    """Una referencia y una estimación candidata tienen distinta
    longitud (número de muestras) o distinta frecuencia de muestreo
    (research.md #7) -- no hay una comparación de SI-SDR bien definida
    entre ellas, así que no se recorta ni se remuestrea para forzarla."""

    def __init__(
        self, identificador_referencia: str, identificador_estimacion: str, motivo: str
    ) -> None:
        self.identificador_referencia = identificador_referencia
        self.identificador_estimacion = identificador_estimacion
        self.motivo = motivo
        super().__init__(
            f"La estimación '{identificador_estimacion}' es incompatible con la "
            f"referencia '{identificador_referencia}': {motivo}."
        )


class ReferenciaEnergiaNulaError(Exception):
    """La referencia tiene energía nula (silencio digital, research.md
    #4) -- el SI-SDR es matemáticamente indefinido (0/0) para ella,
    independientemente de la estimación candidata. `emparejar_tema()`
    (T017) nunca deja escapar esta excepción: comprueba la energía de
    cada referencia antes de llamar a `si_sdr()` sobre ella, y la
    reporta como `ReferenciaSinPareja(motivo="energia_nula")` en vez de
    propagar un fallo (FR-006). Solo la ve quien llama a `si_sdr()`
    directamente."""

    def __init__(self, identificador_referencia: str) -> None:
        self.identificador_referencia = identificador_referencia
        super().__init__(
            f"La referencia '{identificador_referencia}' tiene energía nula (silencio digital); "
            "el SI-SDR no está definido para ella."
        )


# ---------------------------------------------------------------------
# si_sdr (T005) -- ver contracts/metrica_separacion.md para el contrato
# completo (precondiciones/postcondiciones/modos de fallo).
# ---------------------------------------------------------------------


def si_sdr(referencia: PistaGuitarra, estimacion: Estimacion) -> float:
    """Calcula el SI-SDR (*Scale-Invariant Signal-to-Distortion Ratio*,
    Le Roux et al. 2019 -- research.md #1) entre `referencia` y
    `estimacion`.

    Toma `PistaGuitarra`/`Estimacion`, no `PistaAudio` desnudo: las dos
    excepciones de este contrato necesitan `identificador_origen`/
    `identificador` para su mensaje.

    Valida forma y frecuencia de muestreo antes de calcular nada
    (research.md #7): `EstimacionIncompatibleError` si difieren. Valida
    la energía de `referencia` (research.md #4): `ReferenciaEnergiaNulaError`
    si es nula -- el cálculo ni se intenta, la proyección no está
    definida. Una `estimacion` de energía nula NO lanza: el resultado es
    `-inf` **por convención, no por cálculo** (la fórmula da `0/0` en ese
    caso -- research.md #5, hallazgo verificado, no solo razonado). En
    cualquier otro caso, castea a `float64` (research.md #3, sin
    reescalar las muestras -- la invarianza a escala es propiedad de la
    fórmula) y aplica la fórmula estándar; `+inf` exacto cuando el
    residuo (`e_noise`) resulta el vector cero bit a bit (research.md
    #5), envuelto en `numpy.errstate` porque esa división por cero es el
    resultado esperado, no un error a silenciar con un epsilon.
    """
    audio_referencia = referencia.audio
    audio_estimacion = estimacion.audio

    if len(audio_referencia.muestras) != len(audio_estimacion.muestras):
        raise EstimacionIncompatibleError(
            identificador_referencia=referencia.identificador_origen,
            identificador_estimacion=estimacion.identificador,
            motivo="distinta longitud (número de muestras)",
        )
    if audio_referencia.frecuencia_muestreo != audio_estimacion.frecuencia_muestreo:
        raise EstimacionIncompatibleError(
            identificador_referencia=referencia.identificador_origen,
            identificador_estimacion=estimacion.identificador,
            motivo="distinta frecuencia de muestreo",
        )

    s = audio_referencia.muestras.astype(np.float64)
    shat = audio_estimacion.muestras.astype(np.float64)

    # Ambas energías se calculan ANTES de ramificar -- no por eficiencia,
    # sino para que la prioridad de abajo sea una decisión visible, no un
    # accidente del orden de los `if` (research.md #5, "Caso ambos-cero").
    energia_referencia = float(np.dot(s, s))
    energia_estimacion = float(np.dot(shat, shat))

    # Caso ambos-cero (referencia Y estimación con energía nula a la vez):
    # gana ReferenciaEnergiaNulaError, nunca el -inf por convención de la
    # estimación. Decisión explícita, no casualidad de que este chequeo
    # esté escrito primero: la energía nula de la referencia es la falla
    # más fundamental -- sin ella no hay ninguna proyección que formar,
    # independientemente de qué tan mala sea la estimación. La convención
    # -inf presupone una proyección bien definida sobre la que medir el
    # residuo; si la referencia también es silencio, esa premisa no se
    # cumple.
    if energia_referencia == 0.0:
        raise ReferenciaEnergiaNulaError(identificador_referencia=referencia.identificador_origen)
    if energia_estimacion == 0.0:
        return float("-inf")

    alpha = float(np.dot(shat, s)) / energia_referencia
    s_target = alpha * s
    e_noise = shat - s_target

    # La división final se mantiene en espacio NumPy a propósito -- NO
    # `float(...) / float(...)`. Esta es una dependencia no obvia que un
    # refactor futuro rompería sin querer: castear ambos operandos a
    # `float` de Python ANTES de dividir cambia la semántica de la
    # división de "produce inf/nan silenciosamente" (IEEE754, lo que
    # este resultado necesita -- research.md #5) a "lanza
    # ZeroDivisionError" (aritmética de Python puro) en cuanto el
    # denominador es exactamente cero -- exactamente el caso +inf de la
    # verificación de respuesta conocida (FR-011). Descubierto en rojo
    # la primera vez que corrió este test, no asumido.
    with np.errstate(divide="ignore", invalid="ignore"):
        cociente = np.dot(s_target, s_target) / np.dot(e_noise, e_noise)
        valor = 10.0 * np.log10(cociente)
    return float(valor)


# ---------------------------------------------------------------------
# emparejar_tema (T017) -- ver contracts/metrica_separacion.md para el
# contrato completo.
# ---------------------------------------------------------------------

# Sentinel finito para la matriz de costos de la asignación (research.md
# #2) -- ±inf reales de si_sdr() (research.md #5) se saturan a esto SOLO
# para que scipy.optimize.linear_sum_assignment tenga una matriz finita;
# el valor reportado en ReferenciaEmparejada sigue siendo el ±inf exacto.
_SENTINEL_COSTO = 1e15


def _tiene_energia_nula(muestras: npt.NDArray[Any]) -> bool:
    valores = muestras.astype(np.float64)
    return float(np.dot(valores, valores)) == 0.0


def emparejar_tema(
    tema_id: str,
    referencias: list[PistaGuitarra],
    estimaciones: list[Estimacion],
) -> ReporteTema:
    """Implementa User Story 1 completa (contracts/metrica_separacion.md).

    Separa primero las referencias de energía nula -- van directo a
    `sin_pareja` con `motivo="energia_nula"`, sin llamar a `si_sdr()`
    (research.md #4). Construye la matriz de costos `-si_sdr(...)` entre
    cada referencia restante y **todas** las estimaciones recibidas,
    incluidas las silenciosas -- sí participan como candidatas normales
    (research.md #11) -- saturando `±inf` a `_SENTINEL_COSTO` solo para
    la matriz. Resuelve la asignación óptima
    (`scipy.optimize.linear_sum_assignment`, research.md #2). Para cada
    par asignado, si la estimación elegida tiene energía nula, la
    referencia se reclasifica a `sin_pareja` con
    `motivo="estimacion_silenciosa"` (FR-016) en vez de `emparejadas` --
    un valor en `emparejadas` siempre representa una medición real. Las
    referencias que quedan sin asignar por escasez de estimaciones van a
    `sin_pareja` con `motivo="sin_estimacion_disponible"` (FR-003).
    """
    sin_pareja: list[ReferenciaSinPareja] = []
    utilizables: list[PistaGuitarra] = []

    for referencia in referencias:
        if _tiene_energia_nula(referencia.audio.muestras):
            sin_pareja.append(
                ReferenciaSinPareja(
                    identificador_referencia=referencia.identificador_origen,
                    motivo="energia_nula",
                )
            )
        else:
            utilizables.append(referencia)

    emparejadas: list[ReferenciaEmparejada] = []

    if utilizables and estimaciones:
        valores = [
            [si_sdr(referencia, estimacion) for estimacion in estimaciones]
            for referencia in utilizables
        ]
        matriz_costos = np.clip(-np.array(valores), -_SENTINEL_COSTO, _SENTINEL_COSTO)
        filas, columnas = linear_sum_assignment(matriz_costos)
        filas_asignadas = set(filas.tolist())

        for fila, columna in zip(filas.tolist(), columnas.tolist(), strict=True):
            referencia = utilizables[fila]
            estimacion = estimaciones[columna]
            if _tiene_energia_nula(estimacion.audio.muestras):
                sin_pareja.append(
                    ReferenciaSinPareja(
                        identificador_referencia=referencia.identificador_origen,
                        motivo="estimacion_silenciosa",
                    )
                )
            else:
                emparejadas.append(
                    ReferenciaEmparejada(
                        identificador_referencia=referencia.identificador_origen,
                        identificador_estimacion=estimacion.identificador,
                        si_sdr=valores[fila][columna],
                    )
                )

        for indice, referencia in enumerate(utilizables):
            if indice not in filas_asignadas:
                sin_pareja.append(
                    ReferenciaSinPareja(
                        identificador_referencia=referencia.identificador_origen,
                        motivo="sin_estimacion_disponible",
                    )
                )
    else:
        for referencia in utilizables:
            sin_pareja.append(
                ReferenciaSinPareja(
                    identificador_referencia=referencia.identificador_origen,
                    motivo="sin_estimacion_disponible",
                )
            )

    return ReporteTema(
        tema_id=tema_id,
        num_referencias=len(referencias),
        num_estimaciones_recibidas=len(estimaciones),
        emparejadas=emparejadas,
        sin_pareja=sin_pareja,
    )


# ---------------------------------------------------------------------
# agregar_conjunto (T025) -- ver contracts/metrica_separacion.md para el
# contrato completo.
# ---------------------------------------------------------------------


def _mediana_orden(pool: list[float]) -> float:
    """Mediana como estadístico de orden puro (FR-007/FR-008: "solo
    necesita la posición relativa de cada valor... no su magnitud").

    `statistics.median` no cumple esa premisa para un pool de tamaño
    par: promedia aritméticamente los dos valores centrales, y esa
    suma es NaN en IEEE754 cuando esos dos valores son +inf y -inf
    (hallado por Hypothesis, T027, 2026-09-04 -- un tema con
    referencia==estimación exacta junto a un tema completamente sin
    emparejar). Para cualquier otro caso (par de valores finitos, o
    infinitos del mismo signo) el promedio SÍ está bien definido y
    coincide con `statistics.median` -- este caso no se generaliza.

    Cuando el promedio sería NaN, se resuelve al valor más BAJO de los
    dos centrales -- política pesimista, consistente con FR-008 y con
    el Principio V de la constitución (nunca ocultar un resultado malo
    resolviendo la ambigüedad hacia el lado optimista)."""
    ordenado = sorted(pool)
    n = len(ordenado)
    if n % 2 == 1:
        return ordenado[n // 2]
    inferior = ordenado[n // 2 - 1]
    superior = ordenado[n // 2]
    promedio = (inferior + superior) / 2.0
    if math.isnan(promedio):
        return inferior
    return promedio


def agregar_conjunto(entradas: list[EntradaConjunto]) -> ResultadoAgregado:
    """Implementa User Story 2 completa (contracts/metrica_separacion.md).

    Excluye primero cada `EntradaConjunto` con `es_directorio_omitido`
    (motivo `"directorio_omitido"`, con prioridad sobre el siguiente
    chequeo si ambos aplicarían -- research.md #10), luego cada una sin
    ninguna referencia (`"sin_guitarra_referencia"`, FR-009). El resto se
    evalúa: un `ReporteTema` por `emparejar_tema(entrada.tema_id,
    entrada.referencias, entrada.estimaciones)` cada una (FR-007 en
    adelante) -- nunca se excluye un tema solo porque el separador no le
    dio ninguna estimación (`estimaciones == []`); eso es un resultado
    malo, no un tema ausente.

    La mediana se calcula sobre un único pool plano de valores por
    referencia de TODOS los temas evaluados -- nunca colapsando primero
    cada tema a su propio valor (spec.md#Assumptions, "Ponderación de la
    mediana agregada"): un tema con tres referencias aporta tres
    observaciones al pool, no una. Cada referencia sin pareja, sin
    importar el motivo (`energia_nula`, `sin_estimacion_disponible`, o
    `estimacion_silenciosa`), aporta `-inf` al pool (FR-008) -- omitirla
    en vez de aportar el peor valor posible inflaría el resultado
    contando solo los casos donde el separador acertó.
    """
    exclusiones: list[Exclusion] = []
    evaluadas: list[EntradaConjunto] = []

    for entrada in entradas:
        if entrada.es_directorio_omitido:
            exclusiones.append(Exclusion(tema_id=entrada.tema_id, motivo="directorio_omitido"))
        elif not entrada.referencias:
            exclusiones.append(Exclusion(tema_id=entrada.tema_id, motivo="sin_guitarra_referencia"))
        else:
            evaluadas.append(entrada)

    reportes_por_tema = [
        emparejar_tema(entrada.tema_id, entrada.referencias, entrada.estimaciones)
        for entrada in evaluadas
    ]

    # Pool plano: cada referencia individual entra una vez, sea cual sea
    # el tamaño del tema al que pertenece -- research.md #7/#9,
    # spec.md#Assumptions "Ponderación".
    pool: list[float] = []
    for reporte in reportes_por_tema:
        pool.extend(emparejada.si_sdr for emparejada in reporte.emparejadas)
        # -inf es válido AQUÍ únicamente porque la mediana es un
        # estadístico de orden: solo necesita la posición relativa de
        # cada valor, no su magnitud, y -inf es una posición
        # perfectamente definida (siempre el mínimo) sin inventar una
        # constante numérica arbitraria (FR-008). Si algún día se agrega
        # una MEDIA (u otro estadístico sensible a magnitud) a este
        # reporte, este mismo -inf la destruye (-inf + x = -inf para
        # cualquier x finito) -- ese cambio tendría que revisar este
        # bloque junto con FR-007/FR-008, no reusarlo tal cual.
        pool.extend(float("-inf") for _ in reporte.sin_pareja)

    mediana = _mediana_orden(pool) if pool else None

    distribucion_referencias_por_tema = dict(
        Counter(len(entrada.referencias) for entrada in evaluadas)
    )

    return ResultadoAgregado(
        mediana=mediana,
        num_temas_evaluados=len(evaluadas),
        distribucion_referencias_por_tema=distribucion_referencias_por_tema,
        exclusiones=exclusiones,
        reportes_por_tema=reportes_por_tema,
    )
