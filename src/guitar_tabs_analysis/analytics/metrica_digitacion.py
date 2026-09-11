"""Digitación con restricción de la mano (capa `analytics`, importa de
`ingestion`, nunca al revés, ni de `digitacion` -- capa productora):
tipos de dominio (Foundational, T003), generación de candidatas y
asignación por instante (User Story 1, T006/T007) y programación
dinámica sobre la secuencia completa (User Story 2, T010-T012) de
`specs/007-digitacion-restriccion-mano/tasks.md`.

Ver `specs/007-digitacion-restriccion-mano/data-model.md` y
`specs/007-digitacion-restriccion-mano/contracts/digitacion.md` para
el contrato completo.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

from guitar_tabs_analysis.ingestion.guitarset import NotaReferencia

# ---------------------------------------------------------------------
# Tipos de dominio (T003) -- todos inmutables: son el resultado de una
# única asignación, sin ciclo de vida propio (data-model.md).
# ---------------------------------------------------------------------

NotaEntrada = NotaReferencia
"""Alias de tipo, no un tipo nuevo -- spec.md (Key Entities): "mismo
dato que `NotaReferencia` del hito 2, sin cuerda ni traste todavía".
Definir un tipo paralelo duplicaría un contrato ya cerrado sin ningún
campo nuevo que lo justifique (data-model.md)."""


@dataclass(frozen=True)
class Posicion:
    """Una posición física de mástil -- candidata o ya asignada, el
    mismo tipo sirve para ambos usos (data-model.md)."""

    cuerda: str
    traste: int


@dataclass(frozen=True)
class ModeloCoste:
    """Los parámetros declarados del modelo de coste (FR-014) -- nunca
    constantes sin nombre dentro del código. Todos los valores tienen
    evidencia real detrás (research.md #3/#4/#6/#8/#9), salvo los pesos
    de movimiento, declarados explícitamente sin calibrar todavía
    (research.md #13, T025)."""

    midi_cuerda_abierta: dict[str, int]
    traste_minimo: int
    traste_maximo: int
    tolerancia_tono_cents: float
    limite_estiramiento_trastes: int
    ventana_instante_s: float
    peso_desplazamiento: float
    peso_cruce_cuerdas: float


MODELO_COSTE_POR_DEFECTO = ModeloCoste(
    midi_cuerda_abierta={"E": 40, "A": 45, "D": 50, "G": 55, "B": 59, "e": 64},
    traste_minimo=0,
    traste_maximo=19,
    tolerancia_tono_cents=50.0,
    limite_estiramiento_trastes=5,
    ventana_instante_s=0.03,
    peso_desplazamiento=1.0,
    peso_cruce_cuerdas=1.0,
)
"""Instancia con los valores reales de `research.md` (#3 afinación,
#4 rango de trastes, #6 ventana de instante, #8 límite de estiramiento,
#9 tolerancia de tono, #13 pesos sin calibrar) -- se construye una vez
y se pasa explícitamente a cada función que la necesita, nunca leída de
una variable global implícita (data-model.md)."""


@dataclass(frozen=True)
class Instante:
    """Un grupo de una o más `NotaEntrada` cuyos `inicio_s` caen dentro
    de `ModeloCoste.ventana_instante_s` desde el PRIMER `inicio_s` del
    grupo (research.md #6 -- agrupación codiciosa sin arrastre, nunca
    solape de intervalo sostenido). Un `Instante` de una sola nota es el
    caso "nota sola", no un caso especial distinto."""

    notas: list[NotaEntrada]
    inicio_representativo_s: float


@dataclass(frozen=True)
class PosicionAsignada:
    """Una nota de entrada con la posición que el algoritmo le asignó
    -- una nota, una posición, nunca al revés."""

    nota: NotaEntrada
    posicion: Posicion


@dataclass(frozen=True)
class InstanteExcluido:
    """Un instante apartado de la digitación por no tener ninguna
    combinación de posiciones válida (FR-013) -- `motivo` es
    distinguible entre, al menos: `"más notas simultáneas que cuerdas
    disponibles"`, `"nota inalcanzable dentro de tolerancia y rango"` y
    `"excede el límite de estiramiento"` (research.md #10, tasks.md T005:
    el tercer motivo cierra un Edge Case de spec.md que ninguna FR
    nombraba con un motivo propio)."""

    inicio_representativo_s: float
    motivo: str


MOTIVO_MAS_NOTAS_QUE_CUERDAS = "más notas simultáneas que cuerdas disponibles"
MOTIVO_NOTA_INALCANZABLE = "nota inalcanzable dentro de tolerancia y rango"
MOTIVO_EXCEDE_ESTIRAMIENTO = "excede el límite de estiramiento"

# ---------------------------------------------------------------------
# generar_candidatas (T006, contracts/digitacion.md postcondición 1)
# ---------------------------------------------------------------------


def generar_candidatas(tono_midi: float, modelo: ModeloCoste) -> list[Posicion]:
    """Toda posición `(cuerda, traste)` que reproduce `tono_midi` dentro
    de `modelo.tolerancia_tono_cents`, en el rango
    `[modelo.traste_minimo, modelo.traste_maximo]` (contracts/digitacion.md
    postcondición 1). Nunca lanza -- una lista vacía es un resultado
    válido (tono inalcanzable con el rango/tolerancia declarados)."""
    candidatas: list[Posicion] = []
    for cuerda, abierta in modelo.midi_cuerda_abierta.items():
        for traste in range(modelo.traste_minimo, modelo.traste_maximo + 1):
            desvio_cents = abs(tono_midi - (abierta + traste)) * 100.0
            if desvio_cents <= modelo.tolerancia_tono_cents:
                candidatas.append(Posicion(cuerda=cuerda, traste=traste))
    return candidatas


# ---------------------------------------------------------------------
# _generar_combinaciones_validas / asignar_instante (T007, User Story 1)
# -- ver tasks.md T007a para por qué el helper es privado y compartido
# con asignar_secuencia (User Story 2, T012): asignar_instante devuelve
# UNA sola asignación (contrato público), pero la programación dinámica
# de la secuencia completa necesita el CONJUNTO de combinaciones
# válidas de cada instante para tener margen de decisión -- sin esto,
# la DP degeneraría a encadenar decisiones puramente locales.
# ---------------------------------------------------------------------


def _generar_combinaciones_validas(
    instante: Instante, modelo: ModeloCoste
) -> list[list[PosicionAsignada]] | InstanteExcluido:
    """Todas las asignaciones válidas del instante: una posición por
    nota, cuerdas todas distintas, estiramiento (sobre trastes >= 1,
    research.md #7) dentro de `modelo.limite_estiramiento_trastes`.
    Orden determinista (Principio VIII): candidatas por nota en el
    orden de `generar_candidatas` (orden de `midi_cuerda_abierta`,
    trastes ascendentes), combinaciones en el orden de
    `itertools.product` sobre esas listas.

    Precedencia de motivos de exclusión, en este orden (tasks.md T007a):
    más notas que cuerdas disponibles -> nota inalcanzable -> excede
    estiramiento. Una nota inalcanzable siempre impide cualquier
    combinación, así que se reporta antes que un posible exceso de
    estiramiento que nunca se llegaría a evaluar."""
    if len(instante.notas) > len(modelo.midi_cuerda_abierta):
        return InstanteExcluido(
            inicio_representativo_s=instante.inicio_representativo_s,
            motivo=MOTIVO_MAS_NOTAS_QUE_CUERDAS,
        )

    candidatas_por_nota = [generar_candidatas(nota.tono_midi, modelo) for nota in instante.notas]
    if any(not candidatas for candidatas in candidatas_por_nota):
        return InstanteExcluido(
            inicio_representativo_s=instante.inicio_representativo_s,
            motivo=MOTIVO_NOTA_INALCANZABLE,
        )

    validas: list[list[PosicionAsignada]] = []
    for combinacion in _producto_cartesiano(candidatas_por_nota):
        cuerdas = [p.cuerda for p in combinacion]
        if len(set(cuerdas)) != len(cuerdas):
            continue
        pisadas = [p.traste for p in combinacion if p.traste >= 1]
        estiramiento = (max(pisadas) - min(pisadas)) if len(pisadas) >= 2 else 0
        if estiramiento > modelo.limite_estiramiento_trastes:
            continue
        validas.append(
            [
                PosicionAsignada(nota=nota, posicion=posicion)
                for nota, posicion in zip(instante.notas, combinacion, strict=True)
            ]
        )

    if not validas:
        return InstanteExcluido(
            inicio_representativo_s=instante.inicio_representativo_s,
            motivo=MOTIVO_EXCEDE_ESTIRAMIENTO,
        )
    return validas


def _producto_cartesiano(listas: list[list[Posicion]]) -> list[list[Posicion]]:
    """`itertools.product` tipado sobre `list[Posicion]` -- extraído
    para que `_generar_combinaciones_validas` no dependa de `Any` en la
    firma de `itertools.product` bajo `mypy --strict`."""
    return [list(combinacion) for combinacion in itertools.product(*listas)]


def asignar_instante(
    instante: Instante, modelo: ModeloCoste
) -> list[PosicionAsignada] | InstanteExcluido:
    """Una asignación válida del instante, o su exclusión con motivo
    (contracts/digitacion.md postcondición 3, spec.md User Story 1).
    Devuelve la PRIMERA combinación válida en orden determinista --
    User Story 1 no exige minimalidad de ningún coste, solo validez
    (la minimización de coste sobre una secuencia es User Story 2)."""
    resultado = _generar_combinaciones_validas(instante, modelo)
    if isinstance(resultado, InstanteExcluido):
        return resultado
    return resultado[0]


# ---------------------------------------------------------------------
# Digitacion / agrupar_en_instantes / asignar_secuencia (User Story 2,
# T010-T012, contracts/digitacion.md postcondiciones 2 y 4, research.md
# #1/#6/#12/#13).
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Digitacion:
    """El resultado de `asignar_secuencia()` sobre una secuencia
    completa de instantes de una grabación (data-model.md)."""

    posiciones: list[PosicionAsignada]
    exclusiones: list[InstanteExcluido]
    coste_total: float


def agrupar_en_instantes(notas: list[NotaEntrada], modelo: ModeloCoste) -> list[Instante]:
    """Agrupación codiciosa SIN arrastre por proximidad de ataque
    (contracts/digitacion.md postcondición 2, research.md #6): ordena
    `notas` por `inicio_s` (no asume orden de entrada); cada nota entra
    al grupo actual si su `inicio_s` está a lo sumo
    `modelo.ventana_instante_s` del `inicio_s` de la PRIMERA nota del
    grupo -- nunca de la última agregada, para que la ventana no
    "camine" y encadene notas que en realidad no son un mismo ataque.
    NUNCA usa solape de intervalo `[inicio_s, fin_s]` -- ese criterio es
    `clasificar_polifonia_en_instante` del hito 2, un concepto distinto
    que rompe el límite físico de 6 cuerdas sobre datos reales."""
    ordenadas = sorted(notas, key=lambda n: n.inicio_s)
    instantes: list[Instante] = []
    grupo_actual: list[NotaEntrada] = []
    inicio_grupo: float | None = None
    for nota in ordenadas:
        if inicio_grupo is None or nota.inicio_s - inicio_grupo > modelo.ventana_instante_s:
            if grupo_actual:
                instantes.append(
                    Instante(notas=grupo_actual, inicio_representativo_s=inicio_grupo)  # type: ignore[arg-type]
                )
            grupo_actual = [nota]
            inicio_grupo = nota.inicio_s
        else:
            grupo_actual.append(nota)
    if grupo_actual:
        assert inicio_grupo is not None
        instantes.append(Instante(notas=grupo_actual, inicio_representativo_s=inicio_grupo))
    return instantes


EPSILON_DT_S = 1e-9
"""Salvaguarda contra división por cero en el coste de transición
(research.md #13) -- nunca debería activarse en la práctica:
`agrupar_en_instantes` garantiza instantes con `inicio_representativo_s`
estrictamente creciente, separados por más que `ventana_instante_s`, así
que `Δt` entre instantes consecutivos NO excluidos siempre es
estrictamente positivo por construcción. Se declara igual como
salvaguarda explícita, no como confianza ciega en esa garantía."""


def _estiramiento(posiciones: list[Posicion]) -> int:
    """`max(traste) - min(traste)` sobre las posiciones con `traste >= 1`
    únicamente (research.md #7: cuerdas al aire no exigen dedo, no
    participan del estiramiento). Reutilizado tanto por
    `_generar_combinaciones_validas` (implícito, misma regla) como por
    el coste de nodo de la DP de abajo."""
    pisadas = [p.traste for p in posiciones if p.traste >= 1]
    return (max(pisadas) - min(pisadas)) if len(pisadas) >= 2 else 0


def _centroide(posiciones: list[Posicion], orden_cuerdas: list[str]) -> tuple[float, float]:
    """Centroide (traste, índice de cuerda) de una combinación completa
    -- la "posición de la mano" usada para el coste de desplazamiento y
    cruce de cuerdas ENTRE instantes (tasks.md T012, decisión de
    arquitectura no resuelta por `research.md`/`contracts/digitacion.md`,
    que solo dan el ejemplo de dos notas sueltas consecutivas).

    Se promedia sobre TODAS las notas de la combinación, incluidas las
    al aire (`traste == 0`) -- a diferencia del estiramiento
    (research.md #7, que las excluye porque no exigen dedo): el
    estiramiento mide la envergadura de los DEDOS dentro de un acorde,
    mientras que este centroide mide dónde queda la MANO en el mástil, y
    la mano sigue estando en algún lugar del mástil incluso tocando una
    cuerda al aire (una mano relajada sobre cuerdas al aire tiende a
    estar cerca del clavijero, no en un lugar arbitrario).

    **Alternativa considerada, no elegida -- dejada escrita a pedido
    explícito de esta sesión, para que la revisión posterior a T025
    tenga contra qué comparar**: anclar la posición de la mano al
    TRASTE MÍNIMO de la combinación (`min(p.traste for p in
    posiciones)`), en vez de al promedio -- el traste mínimo es,
    físicamente, donde suele apoyarse el dedo índice (la mano "ancla"
    ahí, los demás dedos se extienden hacia trastes más altos), así que
    podría representar mejor dónde está realmente la mano que un
    promedio, que puede caer en un traste que ningún dedo pisa. Se
    prefirió el centroide por ahora porque es simétrico entre notas (no
    privilegia arbitrariamente la más grave) y porque el traste mínimo
    tomado solo ignoraría por completo la posición de las demás notas
    del acorde -- pero NINGUNA de las dos alternativas se verificó
    todavía contra la anotación real de GuitarSet (esa verificación es
    justamente lo que T025 hace sobre los pesos de movimiento; la
    elección de centroide-vs-mínimo en sí queda igual de abierta a
    revisión con esa misma evidencia, research.md #12/#13)."""
    trastes = [p.traste for p in posiciones]
    indices = [orden_cuerdas.index(p.cuerda) for p in posiciones]
    return sum(trastes) / len(trastes), sum(indices) / len(indices)


def _coste_arista(
    prev: list[Posicion],
    cur: list[Posicion],
    dt: float,
    modelo: ModeloCoste,
    orden_cuerdas: list[str],
) -> float:
    """`costeArista(p', p, Δt) = pesoDesplazamiento·|Δtraste_centroide|/Δt
    + pesoCruce·|Δcuerda_centroide|/Δt` (research.md #1/#13)."""
    dt_seguro = max(dt, EPSILON_DT_S)
    t_prev, c_prev = _centroide(prev, orden_cuerdas)
    t_cur, c_cur = _centroide(cur, orden_cuerdas)
    return (
        modelo.peso_desplazamiento * abs(t_cur - t_prev) / dt_seguro
        + modelo.peso_cruce_cuerdas * abs(c_cur - c_prev) / dt_seguro
    )


def asignar_secuencia(notas: list[NotaEntrada], modelo: ModeloCoste) -> Digitacion:
    """Programación dinámica (Viterbi sobre un enrejado por instantes,
    research.md #1) que minimiza la suma de coste de estiramiento por
    instante más coste de desplazamiento/cruce entre instantes
    consecutivos NO excluidos (contracts/digitacion.md postcondición 4).

    Un instante excluido no participa de ningún nodo ni arista -- el
    `Δt` de la transición siguiente se calcula contra el último instante
    NO excluido, nunca contra el excluido (se salta por completo, no se
    trata como si tuviera coste cero)."""
    instantes = agrupar_en_instantes(notas, modelo)
    orden_cuerdas = list(modelo.midi_cuerda_abierta)

    exclusiones: list[InstanteExcluido] = []
    activos: list[Instante] = []
    combos_por_instante: list[list[list[PosicionAsignada]]] = []
    for instante in instantes:
        resultado = _generar_combinaciones_validas(instante, modelo)
        if isinstance(resultado, InstanteExcluido):
            exclusiones.append(resultado)
            continue
        activos.append(instante)
        combos_por_instante.append(resultado)

    if not activos:
        return Digitacion(posiciones=[], exclusiones=exclusiones, coste_total=0.0)

    # dp[i][j] = coste mínimo del camino hasta el instante activo i
    # eligiendo su combinación j; backptr[i][j] = índice de la
    # combinación del instante i-1 que logra ese mínimo (None si i==0,
    # caso base -- ninguna combinación anterior con la que comparar).
    dp: list[list[float]] = []
    backptr: list[list[int | None]] = []

    primeras = combos_por_instante[0]
    dp.append([float(_estiramiento([pa.posicion for pa in combo])) for combo in primeras])
    fila_bp_inicial: list[int | None] = [None] * len(primeras)
    backptr.append(fila_bp_inicial)

    for i in range(1, len(activos)):
        dt = activos[i].inicio_representativo_s - activos[i - 1].inicio_representativo_s
        combos_prev = combos_por_instante[i - 1]
        combos_cur = combos_por_instante[i]
        fila_dp: list[float] = []
        fila_bp: list[int | None] = []
        for combo_cur in combos_cur:
            posiciones_cur = [pa.posicion for pa in combo_cur]
            mejor_costo: float | None = None
            mejor_k: int | None = None
            for k, combo_prev in enumerate(combos_prev):
                posiciones_prev = [pa.posicion for pa in combo_prev]
                costo = dp[i - 1][k] + _coste_arista(
                    posiciones_prev, posiciones_cur, dt, modelo, orden_cuerdas
                )
                if mejor_costo is None or costo < mejor_costo:
                    mejor_costo = costo
                    mejor_k = k
            assert mejor_costo is not None
            assert mejor_k is not None
            fila_dp.append(mejor_costo + _estiramiento(posiciones_cur))
            fila_bp.append(mejor_k)
        dp.append(fila_dp)
        backptr.append(fila_bp)

    ultima_fila = dp[-1]
    j_optimo = min(range(len(ultima_fila)), key=lambda j: ultima_fila[j])
    coste_total = ultima_fila[j_optimo]

    camino = [0] * len(activos)
    camino[-1] = j_optimo
    for i in range(len(activos) - 1, 0, -1):
        anterior = backptr[i][camino[i]]
        assert anterior is not None
        camino[i - 1] = anterior

    posiciones: list[PosicionAsignada] = []
    for i, j in enumerate(camino):
        posiciones.extend(combos_por_instante[i][j])

    return Digitacion(posiciones=posiciones, exclusiones=exclusiones, coste_total=coste_total)
