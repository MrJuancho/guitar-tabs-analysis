"""Tests unitarios de `analytics.metrica_digitacion`: tipos de dominio
(Foundational, T003), `generar_candidatas`/`asignar_instante` (User
Story 1, T004-T007) y `agrupar_en_instantes`/`asignar_secuencia` (User
Story 2, T008-T012) -- notas construidas a mano, sin GuitarSet real
(spec.md, Independent Test de cada historia).
"""

from __future__ import annotations

import dataclasses
import itertools

import pytest

from guitar_tabs_analysis.analytics.metrica_digitacion import (
    MODELO_COSTE_POR_DEFECTO,
    Digitacion,
    Instante,
    InstanteExcluido,
    ModeloCoste,
    Posicion,
    PosicionAsignada,
    evaluar_coincidencia,
    generar_candidatas,
)
from guitar_tabs_analysis.ingestion.guitarset import NotaConPosicionReal, NotaReferencia


def _modelo(**overrides: object) -> ModeloCoste:
    return dataclasses.replace(MODELO_COSTE_POR_DEFECTO, **overrides)  # type: ignore[arg-type]


# ---------------------------------------------------------------------
# Tipos de dominio (T003)
# ---------------------------------------------------------------------


def test_posicion_es_inmutable_y_expone_sus_campos() -> None:
    posicion = Posicion(cuerda="A", traste=3)
    assert posicion.cuerda == "A"
    assert posicion.traste == 3
    with pytest.raises(dataclasses.FrozenInstanceError):
        posicion.traste = 4  # type: ignore[misc]


def test_modelo_coste_por_defecto_expone_los_valores_de_research_md() -> None:
    m = MODELO_COSTE_POR_DEFECTO
    assert m.midi_cuerda_abierta == {"E": 40, "A": 45, "D": 50, "G": 55, "B": 59, "e": 64}
    assert m.traste_minimo == 0
    assert m.traste_maximo == 19
    assert m.tolerancia_tono_cents == 50.0
    assert m.limite_estiramiento_trastes == 5
    assert m.ventana_instante_s == 0.03
    assert m.peso_desplazamiento == 1.0
    assert m.peso_cruce_cuerdas == 1.0


def test_instante_de_una_sola_nota_no_es_un_caso_especial() -> None:
    nota = NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=1.5)
    instante = Instante(notas=[nota], inicio_representativo_s=1.0)
    assert instante.notas == [nota]


# ---------------------------------------------------------------------
# generar_candidatas (T004, contracts/digitacion.md postcondición 1)
# ---------------------------------------------------------------------


def test_generar_candidatas_tono_entero_exacto_incluye_la_posicion_esperada() -> None:
    # A2 (traste 0 de la cuerda "A", MIDI 45) -- también alcanzable en otras
    # cuerdas (p.ej. traste 5 de la "E"), pero DEBE incluir la posición
    # entera exacta en su cuerda "natural".
    candidatas = generar_candidatas(45.0, MODELO_COSTE_POR_DEFECTO)
    assert Posicion(cuerda="A", traste=0) in candidatas


def test_generar_candidatas_tono_fraccionario_dentro_de_tolerancia() -> None:
    # 45 + 49 cents (0.49 semitonos) -- dentro de 50 cents de tolerancia.
    candidatas = generar_candidatas(45.49, MODELO_COSTE_POR_DEFECTO)
    assert Posicion(cuerda="A", traste=0) in candidatas


def test_generar_candidatas_tono_fraccionario_fuera_de_tolerancia() -> None:
    # 45 + 51 cents -- justo por encima de los 50 cents de tolerancia.
    candidatas = generar_candidatas(45.51, MODELO_COSTE_POR_DEFECTO)
    assert Posicion(cuerda="A", traste=0) not in candidatas


def test_generar_candidatas_respeta_el_rango_de_trastes_en_los_bordes() -> None:
    modelo = _modelo(traste_maximo=19)
    # Cuerda "e" (MIDI 64 abierta): traste 19 -> MIDI 83, dentro del rango.
    candidatas_en_borde = generar_candidatas(83.0, modelo)
    assert Posicion(cuerda="e", traste=19) in candidatas_en_borde
    # Traste 20 (fuera del rango) nunca aparece, aunque el tono exista.
    candidatas_fuera = generar_candidatas(84.0, modelo)
    assert Posicion(cuerda="e", traste=20) not in candidatas_fuera


def test_generar_candidatas_tono_fuera_de_rango_fisico_devuelve_lista_vacia() -> None:
    # Más grave que la sexta (E, MIDI 40) al aire.
    assert generar_candidatas(20.0, MODELO_COSTE_POR_DEFECTO) == []
    # Más agudo que el traste más alto de la primera (e=64, traste 19 -> 83).
    assert generar_candidatas(120.0, MODELO_COSTE_POR_DEFECTO) == []


# ---------------------------------------------------------------------
# asignar_instante (T005, spec.md US1 Acceptance Scenarios,
# contracts/digitacion.md postcondición 3)
# ---------------------------------------------------------------------


def _instante(tonos: list[float]) -> Instante:
    notas = [NotaReferencia(tono_midi=t, inicio_s=0.0, fin_s=0.5) for t in tonos]
    return Instante(notas=notas, inicio_representativo_s=0.0)


def test_asignar_instante_nota_sola_reproduce_su_tono() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_instante

    resultado = asignar_instante(_instante([45.0]), MODELO_COSTE_POR_DEFECTO)
    assert isinstance(resultado, list)
    assert len(resultado) == 1
    asignada = resultado[0]
    abierta = MODELO_COSTE_POR_DEFECTO.midi_cuerda_abierta[asignada.posicion.cuerda]
    assert abierta + asignada.posicion.traste == 45


def test_asignar_instante_acorde_alcanzable_cuerdas_distintas_y_dentro_del_limite() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_instante

    # Acorde de Mi mayor abierto: E2(40), B3(59), E4(64) -- tres notas
    # tocables con cero estiramiento (todas al aire es una posición válida
    # y trivialmente dentro del límite).
    resultado = asignar_instante(_instante([40.0, 59.0, 64.0]), MODELO_COSTE_POR_DEFECTO)
    assert isinstance(resultado, list)
    assert len(resultado) == 3
    cuerdas = [pa.posicion.cuerda for pa in resultado]
    assert len(set(cuerdas)) == 3
    pisadas = [pa.posicion.traste for pa in resultado if pa.posicion.traste >= 1]
    if len(pisadas) >= 2:
        assert max(pisadas) - min(pisadas) <= MODELO_COSTE_POR_DEFECTO.limite_estiramiento_trastes


def test_asignar_instante_acorde_que_excede_estiramiento_en_toda_combinacion() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_instante

    modelo = _modelo(limite_estiramiento_trastes=1)
    # Dos notas que solo son alcanzables con trastes muy separados en
    # cualquier cuerda común -- construidas para que NINGUNA combinación
    # de cuerdas distintas quede dentro de limite_estiramiento_trastes=1.
    # C4 (60.0) y G#5 (80.0): en la cuerda "e" (64 abierta) darían
    # trastes -4 (inválido) y 16; en cualquier par de cuerdas válidas la
    # separación de trastes es mayor a 1.
    resultado = asignar_instante(_instante([48.0, 80.0]), modelo)
    assert isinstance(resultado, InstanteExcluido)
    assert resultado.motivo == "excede el límite de estiramiento"


def test_asignar_instante_dos_notas_mismo_tono_reciben_cuerdas_distintas() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_instante

    resultado = asignar_instante(_instante([64.0, 64.0]), MODELO_COSTE_POR_DEFECTO)
    assert isinstance(resultado, list)
    assert len(resultado) == 2
    assert resultado[0].posicion.cuerda != resultado[1].posicion.cuerda
    for pa in resultado:
        abierta = MODELO_COSTE_POR_DEFECTO.midi_cuerda_abierta[pa.posicion.cuerda]
        assert abierta + pa.posicion.traste == 64


def test_asignar_instante_mas_notas_que_cuerdas_disponibles() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_instante

    # 7 notas simultáneas -- más que las 6 cuerdas del instrumento
    # (research.md #10: no ocurre en datos reales, pero el código no debe
    # asumirlo garantizado por el tipo).
    tonos = [40.0, 45.0, 50.0, 55.0, 59.0, 64.0, 41.0]
    resultado = asignar_instante(_instante(tonos), MODELO_COSTE_POR_DEFECTO)
    assert isinstance(resultado, InstanteExcluido)
    assert resultado.motivo == "más notas simultáneas que cuerdas disponibles"


def test_asignar_instante_nota_inalcanzable_incluso_con_tolerancia_completa() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_instante

    # 20.0 está muy por debajo del rango físico (más grave que la sexta al
    # aire, spec.md Edge Cases) -- motivo distinguible de los otros dos.
    resultado = asignar_instante(_instante([20.0]), MODELO_COSTE_POR_DEFECTO)
    assert isinstance(resultado, InstanteExcluido)
    assert resultado.motivo == "nota inalcanzable dentro de tolerancia y rango"


def test_asignar_instante_los_tres_motivos_de_exclusion_son_distinguibles() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_instante

    m_estiramiento = asignar_instante(
        _instante([48.0, 80.0]), _modelo(limite_estiramiento_trastes=1)
    )
    m_cuerdas = asignar_instante(
        _instante([40.0, 45.0, 50.0, 55.0, 59.0, 64.0, 41.0]),
        MODELO_COSTE_POR_DEFECTO,
    )
    m_inalcanzable = asignar_instante(_instante([20.0]), MODELO_COSTE_POR_DEFECTO)
    assert isinstance(m_estiramiento, InstanteExcluido)
    assert isinstance(m_cuerdas, InstanteExcluido)
    assert isinstance(m_inalcanzable, InstanteExcluido)
    motivos = {m_estiramiento.motivo, m_cuerdas.motivo, m_inalcanzable.motivo}
    assert len(motivos) == 3


# ---------------------------------------------------------------------
# agrupar_en_instantes (T008, contracts/digitacion.md postcondición 2,
# research.md #6)
# ---------------------------------------------------------------------


def test_agrupar_en_instantes_sin_arrastre_no_encadena_mas_alla_de_la_ventana() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import agrupar_en_instantes

    modelo = _modelo(ventana_instante_s=0.03)
    # n1 en t=0.0; n2 a 0.9*ventana de n1 (dentro); n3 a 1.8*ventana de n1
    # (fuera de n1) pero solo 0.9*ventana de n2 -- CON arrastre las tres se
    # agruparían; SIN arrastre (la regla real) n3 abre un instante nuevo.
    n1 = NotaReferencia(tono_midi=40.0, inicio_s=0.0, fin_s=0.5)
    n2 = NotaReferencia(tono_midi=45.0, inicio_s=0.027, fin_s=0.5)
    n3 = NotaReferencia(tono_midi=50.0, inicio_s=0.054, fin_s=0.5)
    instantes = agrupar_en_instantes([n1, n2, n3], modelo)
    assert len(instantes) == 2
    assert instantes[0].notas == [n1, n2]
    assert instantes[1].notas == [n3]


def test_agrupar_en_instantes_notas_fuera_de_ventana_abren_instante_nuevo() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import agrupar_en_instantes

    modelo = _modelo(ventana_instante_s=0.03)
    n1 = NotaReferencia(tono_midi=40.0, inicio_s=0.0, fin_s=0.5)
    n2 = NotaReferencia(tono_midi=45.0, inicio_s=1.0, fin_s=1.5)
    instantes = agrupar_en_instantes([n1, n2], modelo)
    assert len(instantes) == 2
    assert [i.notas for i in instantes] == [[n1], [n2]]


def test_agrupar_en_instantes_una_nota_sola_no_es_caso_especial() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import agrupar_en_instantes

    n1 = NotaReferencia(tono_midi=40.0, inicio_s=0.0, fin_s=0.5)
    instantes = agrupar_en_instantes([n1], MODELO_COSTE_POR_DEFECTO)
    assert len(instantes) == 1
    assert instantes[0].notas == [n1]
    assert instantes[0].inicio_representativo_s == 0.0


# ---------------------------------------------------------------------
# asignar_secuencia (T009, spec.md US2 Acceptance Scenarios, FR-006)
#
# La fuerza bruta de abajo está ESCRITA EN EL PROPIO TEST (nunca
# reutiliza `_generar_combinaciones_validas` ni la DP de producción) --
# solo reutiliza `generar_candidatas` (mapeo tono -> posiciones, un
# cálculo cerrado, no el algoritmo de minimización bajo prueba) y
# `agrupar_en_instantes` (ya verificado por separado arriba, T008 --
# agrupar en instantes no es parte de lo que FR-006 pide verificar
# contra fuerza bruta, que es específicamente la elección de
# combinación y la DP).
# ---------------------------------------------------------------------


def _combinaciones_validas_bruteforce(
    instante: Instante, modelo: ModeloCoste
) -> list[tuple[Posicion, ...]]:
    candidatas_por_nota = [generar_candidatas(n.tono_midi, modelo) for n in instante.notas]
    validas: list[tuple[Posicion, ...]] = []
    for combo in itertools.product(*candidatas_por_nota):
        cuerdas = [p.cuerda for p in combo]
        if len(set(cuerdas)) != len(cuerdas):
            continue
        pisadas = [p.traste for p in combo if p.traste >= 1]
        estiramiento = (max(pisadas) - min(pisadas)) if len(pisadas) >= 2 else 0
        if estiramiento > modelo.limite_estiramiento_trastes:
            continue
        validas.append(combo)
    return validas


def _coste_nodo_bruteforce(combo: tuple[Posicion, ...]) -> float:
    pisadas = [p.traste for p in combo if p.traste >= 1]
    return float((max(pisadas) - min(pisadas)) if len(pisadas) >= 2 else 0)


def _centroide_bruteforce(
    combo: tuple[Posicion, ...], orden_cuerdas: list[str]
) -> tuple[float, float]:
    trastes = [p.traste for p in combo]
    indices = [orden_cuerdas.index(p.cuerda) for p in combo]
    return sum(trastes) / len(trastes), sum(indices) / len(indices)


def _coste_arista_bruteforce(
    prev: tuple[Posicion, ...],
    cur: tuple[Posicion, ...],
    dt: float,
    modelo: ModeloCoste,
    orden_cuerdas: list[str],
) -> float:
    t_prev, c_prev = _centroide_bruteforce(prev, orden_cuerdas)
    t_cur, c_cur = _centroide_bruteforce(cur, orden_cuerdas)
    return (
        modelo.peso_desplazamiento * abs(t_cur - t_prev) / dt
        + modelo.peso_cruce_cuerdas * abs(c_cur - c_prev) / dt
    )


def _fuerza_bruta_coste_minimo(instantes: list[Instante], modelo: ModeloCoste) -> float:
    orden_cuerdas = list(modelo.midi_cuerda_abierta)
    combinaciones_por_instante = [_combinaciones_validas_bruteforce(i, modelo) for i in instantes]
    mejor: float | None = None
    for eleccion in itertools.product(*combinaciones_por_instante):
        costo = _coste_nodo_bruteforce(eleccion[0])
        for k in range(1, len(eleccion)):
            dt = instantes[k].inicio_representativo_s - instantes[k - 1].inicio_representativo_s
            costo += _coste_nodo_bruteforce(eleccion[k])
            costo += _coste_arista_bruteforce(
                eleccion[k - 1], eleccion[k], dt, modelo, orden_cuerdas
            )
        if mejor is None or costo < mejor:
            mejor = costo
    assert mejor is not None
    return mejor


def test_asignar_secuencia_coincide_con_fuerza_bruta_secuencia_corta() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import (
        agrupar_en_instantes,
        asignar_secuencia,
    )

    modelo = _modelo(traste_maximo=5)
    notas = [
        NotaReferencia(tono_midi=45.0, inicio_s=0.0, fin_s=0.4),
        NotaReferencia(tono_midi=50.0, inicio_s=0.5, fin_s=0.9),
        NotaReferencia(tono_midi=55.0, inicio_s=0.55, fin_s=0.9),
    ]
    digitacion = asignar_secuencia(notas, modelo)
    instantes = agrupar_en_instantes(notas, modelo)
    esperado = _fuerza_bruta_coste_minimo(instantes, modelo)
    assert digitacion.coste_total == pytest.approx(esperado)
    assert digitacion.exclusiones == []


def test_asignar_secuencia_coincide_con_fuerza_bruta_otra_secuencia_corta() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import (
        agrupar_en_instantes,
        asignar_secuencia,
    )

    modelo = _modelo(traste_maximo=8)
    notas = [
        NotaReferencia(tono_midi=41.0, inicio_s=0.0, fin_s=0.4),
        NotaReferencia(tono_midi=64.0, inicio_s=0.2, fin_s=0.6),
        NotaReferencia(tono_midi=48.0, inicio_s=0.25, fin_s=0.6),
    ]
    digitacion = asignar_secuencia(notas, modelo)
    instantes = agrupar_en_instantes(notas, modelo)
    esperado = _fuerza_bruta_coste_minimo(instantes, modelo)
    assert digitacion.coste_total == pytest.approx(esperado)


def test_asignar_secuencia_mismo_desplazamiento_menos_tiempo_cuesta_mas_o_igual() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_secuencia

    modelo = _modelo(traste_maximo=5)
    # 40.0 (E0) y 43.0 (E3) -- candidatas únicas dentro de traste_maximo=5
    # (A45+traste sería negativo para ambas), sin ambigüedad de DP: aísla
    # la fórmula de coste en sí (AS2).
    notas_lentas = [
        NotaReferencia(tono_midi=40.0, inicio_s=0.0, fin_s=0.4),
        NotaReferencia(tono_midi=43.0, inicio_s=0.5, fin_s=0.9),
    ]
    notas_rapidas = [
        NotaReferencia(tono_midi=40.0, inicio_s=0.0, fin_s=0.4),
        NotaReferencia(tono_midi=43.0, inicio_s=0.05, fin_s=0.4),
    ]
    coste_lento = asignar_secuencia(notas_lentas, modelo).coste_total
    coste_rapido = asignar_secuencia(notas_rapidas, modelo).coste_total
    assert coste_rapido >= coste_lento


def test_asignar_secuencia_cruce_de_cuerdas_positivo_con_desplazamiento_cero() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_secuencia

    modelo = _modelo(traste_maximo=5)
    # Traste 1 de la sexta (E, MIDI 41) seguido de traste 1 de la primera
    # (e, MIDI 65) -- candidatas únicas con traste_maximo=5 (spec.md, el
    # ejemplo literal del cruce de cuerdas).
    notas = [
        NotaReferencia(tono_midi=41.0, inicio_s=0.0, fin_s=0.4),
        NotaReferencia(tono_midi=65.0, inicio_s=0.5, fin_s=0.9),
    ]
    digitacion = asignar_secuencia(notas, modelo)
    # Estiramiento (nodos) es 0 en ambos instantes (una sola nota pisada
    # cada uno); desplazamiento en trastes es 0 (traste 1 en los dos) --
    # el único término que puede producir un coste_total > 0 es el cruce
    # de cuerdas.
    assert digitacion.coste_total > 0


def test_asignar_secuencia_primer_instante_sin_coste_de_transicion() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_secuencia

    modelo = _modelo(traste_maximo=8)
    # Un único instante (acorde): 45.0 (A0/E5) + 52.0 (D2/A7). Combos con
    # cuerdas distintas y su estiramiento: (A0,D2)=0, (E5,D2)=3, (E5,A7)=2
    # -- el óptimo (sin ningún término de transición, no hay instante
    # anterior) es 0.0, vía (A0,D2).
    notas = [
        NotaReferencia(tono_midi=45.0, inicio_s=0.0, fin_s=0.4),
        NotaReferencia(tono_midi=52.0, inicio_s=0.0, fin_s=0.4),
    ]
    digitacion = asignar_secuencia(notas, modelo)
    assert digitacion.coste_total == pytest.approx(0.0)
    assert digitacion.exclusiones == []
    assert len(digitacion.posiciones) == 2


def test_asignar_secuencia_instante_excluido_salta_su_dt_al_anterior_no_excluido() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import (
        Instante,
        asignar_secuencia,
    )

    modelo = _modelo(traste_maximo=5)
    n1 = NotaReferencia(tono_midi=45.0, inicio_s=0.0, fin_s=0.3)
    n2 = NotaReferencia(tono_midi=20.0, inicio_s=0.2, fin_s=0.3)  # inalcanzable -> excluido
    n3 = NotaReferencia(tono_midi=50.0, inicio_s=0.25, fin_s=0.3)
    digitacion = asignar_secuencia([n1, n2, n3], modelo)

    assert len(digitacion.exclusiones) == 1
    assert digitacion.exclusiones[0].motivo == "nota inalcanzable dentro de tolerancia y rango"
    assert digitacion.exclusiones[0].inicio_representativo_s == pytest.approx(0.2)
    assert len(digitacion.posiciones) == 2

    # El Δt de la transición de n1 a n3 debe calcularse contra n1 (último
    # instante NO excluido), saltando por completo el instante de n2 --
    # equivalente a una secuencia de solo dos instantes con Δt = 0.25.
    instantes_sin_excluido = [
        Instante(notas=[n1], inicio_representativo_s=0.0),
        Instante(notas=[n3], inicio_representativo_s=0.25),
    ]
    esperado = _fuerza_bruta_coste_minimo(instantes_sin_excluido, modelo)
    assert digitacion.coste_total == pytest.approx(esperado)


def test_asignar_secuencia_todos_los_instantes_excluidos_da_digitacion_vacia() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_secuencia

    # Única nota, tono inalcanzable -- el único instante de la secuencia
    # queda excluido, sin ningún instante activo para la DP.
    notas = [NotaReferencia(tono_midi=20.0, inicio_s=0.0, fin_s=0.3)]
    digitacion = asignar_secuencia(notas, MODELO_COSTE_POR_DEFECTO)
    assert digitacion.posiciones == []
    assert digitacion.coste_total == 0.0
    assert len(digitacion.exclusiones) == 1
    assert digitacion.exclusiones[0].motivo == "nota inalcanzable dentro de tolerancia y rango"


def test_asignar_secuencia_sin_notas_da_digitacion_vacia() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_secuencia

    digitacion = asignar_secuencia([], MODELO_COSTE_POR_DEFECTO)
    assert digitacion.posiciones == []
    assert digitacion.exclusiones == []
    assert digitacion.coste_total == 0.0


# ---------------------------------------------------------------------
# evaluar_coincidencia (T014, contracts/digitacion.md postcondición 5)
#
# La comparación es SIEMPRE contra la posición REAL anotada por
# GuitarSet (NotaConPosicionReal), nunca contra el coste de la propia
# Digitacion -- medir "mi coste salió bajo" sería circular (FR-007): el
# algoritmo lo minimiza por construcción, eso no dice nada sobre si se
# parece al uso humano real.
# ---------------------------------------------------------------------


def test_evaluar_coincidencia_todo_coincide_exactamente() -> None:
    n1 = NotaReferencia(tono_midi=47.0, inicio_s=1.0, fin_s=1.5)
    digitacion = Digitacion(
        posiciones=[PosicionAsignada(nota=n1, posicion=Posicion(cuerda="A", traste=2))],
        exclusiones=[],
        coste_total=0.0,
    )
    reales = [
        NotaConPosicionReal(tono_midi=47.0, inicio_s=1.0, fin_s=1.5, cuerda_real="A", traste_real=2)
    ]
    resultado = evaluar_coincidencia(digitacion, reales)
    assert resultado.fraccion_coincidencia == 1.0
    assert resultado.num_notas_medidas == 1
    assert resultado.num_notas_coincidentes == 1


def test_evaluar_coincidencia_distinta_cuerda_o_traste_no_cuenta() -> None:
    n1 = NotaReferencia(tono_midi=47.0, inicio_s=1.0, fin_s=1.5)
    n2 = NotaReferencia(tono_midi=50.0, inicio_s=2.0, fin_s=2.5)
    digitacion = Digitacion(
        posiciones=[
            # n1: la real es cuerda "A" -- el algoritmo eligió "E" (mismo
            # tono, distinta cuerda, NO cuenta).
            PosicionAsignada(nota=n1, posicion=Posicion(cuerda="E", traste=7)),
            # n2: la real es traste 0 -- el algoritmo eligió traste 5 en
            # la misma cuerda (NO cuenta, ninguna tolerancia numérica).
            PosicionAsignada(nota=n2, posicion=Posicion(cuerda="D", traste=5)),
        ],
        exclusiones=[],
        coste_total=0.0,
    )
    reales = [
        NotaConPosicionReal(
            tono_midi=47.0, inicio_s=1.0, fin_s=1.5, cuerda_real="A", traste_real=2
        ),
        NotaConPosicionReal(
            tono_midi=50.0, inicio_s=2.0, fin_s=2.5, cuerda_real="D", traste_real=0
        ),
    ]
    resultado = evaluar_coincidencia(digitacion, reales)
    assert resultado.num_notas_medidas == 2
    assert resultado.num_notas_coincidentes == 0
    assert resultado.fraccion_coincidencia == 0.0


def test_evaluar_coincidencia_notas_de_instantes_excluidos_no_entran_al_denominador() -> None:
    n1 = NotaReferencia(tono_midi=47.0, inicio_s=1.0, fin_s=1.5)
    # La segunda nota (tono inalcanzable) fue excluida por
    # asignar_secuencia -- nunca aparece en digitacion.posiciones, pese
    # a tener posición real anotada en `reales`.
    digitacion = Digitacion(
        posiciones=[PosicionAsignada(nota=n1, posicion=Posicion(cuerda="A", traste=2))],
        exclusiones=[InstanteExcluido(inicio_representativo_s=2.0, motivo="cualquiera")],
        coste_total=0.0,
    )
    reales = [
        NotaConPosicionReal(
            tono_midi=47.0, inicio_s=1.0, fin_s=1.5, cuerda_real="A", traste_real=2
        ),
        NotaConPosicionReal(
            tono_midi=20.0, inicio_s=2.0, fin_s=2.5, cuerda_real="E", traste_real=0
        ),
    ]
    resultado = evaluar_coincidencia(digitacion, reales)
    assert resultado.num_notas_medidas == 1
    assert resultado.num_notas_coincidentes == 1
    assert resultado.fraccion_coincidencia == 1.0


def test_evaluar_coincidencia_sin_notas_medidas_da_fraccion_none() -> None:
    digitacion = Digitacion(posiciones=[], exclusiones=[], coste_total=0.0)
    resultado = evaluar_coincidencia(digitacion, [])
    assert resultado.fraccion_coincidencia is None
    assert resultado.num_notas_medidas == 0
    assert resultado.num_notas_coincidentes == 0


def test_evaluar_coincidencia_nota_asignada_sin_posicion_real_no_entra_al_denominador() -> None:
    """Caso defensivo: una `PosicionAsignada` cuya `nota` no tiene
    ninguna `NotaConPosicionReal` correspondiente (no debería ocurrir
    con datos bien formados -- la lista de posiciones reales viene de
    la misma grabación -- pero el código no lo asume garantizado)."""
    n1 = NotaReferencia(tono_midi=47.0, inicio_s=1.0, fin_s=1.5)
    digitacion = Digitacion(
        posiciones=[PosicionAsignada(nota=n1, posicion=Posicion(cuerda="A", traste=2))],
        exclusiones=[],
        coste_total=0.0,
    )
    resultado = evaluar_coincidencia(digitacion, [])
    assert resultado.num_notas_medidas == 0
    assert resultado.num_notas_coincidentes == 0
    assert resultado.fraccion_coincidencia is None
