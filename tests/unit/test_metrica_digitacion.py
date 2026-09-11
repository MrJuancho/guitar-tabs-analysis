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
    ExclusionDigitacion,
    Instante,
    InstanteExcluido,
    ModeloCoste,
    Posicion,
    PosicionAsignada,
    ResultadoDigitacionGrabacion,
    agregar_conjunto,
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


def test_generar_candidatas_respeta_traste_minimo_no_solo_traste_maximo() -> None:
    """`range(modelo.traste_minimo, modelo.traste_maximo + 1)` -- un
    traste_minimo > 0 excluye trastes por debajo, no solo los que
    exceden traste_maximo (mutation testing T027: `traste_minimo`
    omitido del `range()` sobrevivía sin ningún test con
    `traste_minimo != 0`)."""
    modelo = _modelo(traste_minimo=2, traste_maximo=5)
    # A46.0 = A(45) + traste 1 -- por debajo de traste_minimo=2.
    assert Posicion(cuerda="A", traste=1) not in generar_candidatas(46.0, modelo)
    # A47.0 = A(45) + traste 2 -- dentro del rango.
    assert Posicion(cuerda="A", traste=2) in generar_candidatas(47.0, modelo)


def test_generar_candidatas_tolerancia_es_limite_inclusivo() -> None:
    """`desvio_cents <= tolerancia_tono_cents`, no `<` -- un desvío
    EXACTAMENTE igual a la tolerancia declarada MUST incluirse
    (mutation testing T027: `<=` mutado a `<` sobrevivía sin un caso
    justo en el borde exacto)."""
    # A(45) + 50 cents exactos (0.5 semitonos) = 45.5 -- tolerancia por
    # defecto es 50.0 cents, exactamente en el borde.
    candidatas = generar_candidatas(45.5, MODELO_COSTE_POR_DEFECTO)
    assert Posicion(cuerda="A", traste=0) in candidatas


def test_generar_candidatas_conversion_a_cents_es_por_100_no_101() -> None:
    """`desvio_cents = ... * 100.0` -- un desvío de 0.499 semitonos da
    49.9 cents (dentro de una tolerancia de 50) con el multiplicador
    correcto, pero 50.399 (fuera) con `* 101.0` (mutation testing T027:
    ese mutante sobrevivía porque ningún test anterior caía justo en la
    banda [50/101, 50/100] semitonos que los distingue)."""
    candidatas = generar_candidatas(45.499, MODELO_COSTE_POR_DEFECTO)
    assert Posicion(cuerda="A", traste=0) in candidatas


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
    # inicio_representativo_s se propaga desde el instante, nunca None
    # (mutation testing T027).
    assert resultado.inicio_representativo_s == 0.0


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
    # inicio_representativo_s se propaga desde el instante, nunca None
    # (mutation testing T027).
    assert resultado.inicio_representativo_s == 0.0


def test_asignar_instante_exactamente_seis_notas_no_se_excluye_por_conteo() -> None:
    """`len(instante.notas) > len(cuerdas)` -- el límite es estrictamente
    MAYOR que 6, no `>=` (mutation testing T027: con `>=`, un acorde de
    exactamente 6 notas -- una por cuerda, el máximo físico real -- se
    excluiría por conteo aunque sea perfectamente tocable)."""
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_instante

    # Las seis cuerdas al aire -- 6 notas, cero estiramiento, cuerdas
    # todas distintas por construcción (una nota por cuerda abierta).
    tonos = [40.0, 45.0, 50.0, 55.0, 59.0, 64.0]
    resultado = asignar_instante(_instante(tonos), MODELO_COSTE_POR_DEFECTO)
    assert isinstance(resultado, list)
    assert len(resultado) == 6


def test_asignar_instante_nota_inalcanzable_incluso_con_tolerancia_completa() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_instante

    # 20.0 está muy por debajo del rango físico (más grave que la sexta al
    # aire, spec.md Edge Cases) -- motivo distinguible de los otros dos.
    resultado = asignar_instante(_instante([20.0]), MODELO_COSTE_POR_DEFECTO)
    assert isinstance(resultado, InstanteExcluido)
    assert resultado.motivo == "nota inalcanzable dentro de tolerancia y rango"
    assert resultado.inicio_representativo_s == 0.0


def test_asignar_instante_acorde_que_excede_estiramiento_propaga_inicio_representativo() -> None:
    """Mismo chequeo que arriba, para la última rama de exclusión
    (`InstanteExcluido` cuando `not validas` -- mutation testing T027:
    `inicio_representativo_s=None` sobrevivía específicamente en ESTA
    construcción, distinta de las otras dos)."""
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_instante

    modelo = _modelo(limite_estiramiento_trastes=1)
    instante = Instante(
        notas=[
            NotaReferencia(tono_midi=48.0, inicio_s=3.5, fin_s=4.0),
            NotaReferencia(tono_midi=80.0, inicio_s=3.5, fin_s=4.0),
        ],
        inicio_representativo_s=3.5,
    )
    resultado = asignar_instante(instante, modelo)
    assert isinstance(resultado, InstanteExcluido)
    assert resultado.inicio_representativo_s == 3.5


def test_generar_combinaciones_validas_traste_uno_cuenta_como_pisada() -> None:
    """`p.traste >= 1` (no `> 1` ni `>= 2`) -- traste 1 SÍ cuenta como
    pisada para el estiramiento (research.md #7: solo el traste 0, al
    aire, no exige dedo). Mutation testing T027: con `> 1`/`>= 2`, el
    traste 1 se descarta de `pisadas`, y una combinación que debería
    excluirse por estiramiento real (5, sobre el límite de 4) queda dentro
    del límite aparente (al quedar un solo elemento pisado, o ninguno)."""
    from guitar_tabs_analysis.analytics.metrica_digitacion import (
        _generar_combinaciones_validas,
    )

    modelo = _modelo(traste_maximo=6, limite_estiramiento_trastes=4)
    # 41.0 -- única candidata en todo el rango: E traste 1 (ninguna otra
    # cuerda alcanza 41 con traste >= 0). 56.0 -- única candidata con
    # traste_maximo=6: D traste 6 (G exigiría traste 1, pero G+1=56
    # también compite -- se filtra abajo por cuerda exacta).
    instante = Instante(
        notas=[
            NotaReferencia(tono_midi=41.0, inicio_s=0.0, fin_s=0.5),
            NotaReferencia(tono_midi=56.0, inicio_s=0.0, fin_s=0.5),
        ],
        inicio_representativo_s=0.0,
    )
    resultado = _generar_combinaciones_validas(instante, modelo)
    assert isinstance(resultado, list)
    combos = [{(pa.posicion.cuerda, pa.posicion.traste) for pa in combo} for combo in resultado]
    # (E,1)+(D,6): estiramiento real = 6-1 = 5 > 4 -- MUST NOT ser válida.
    assert {("E", 1), ("D", 6)} not in combos


def test_generar_combinaciones_validas_estiramiento_es_resta_no_suma() -> None:
    """`max(pisadas) - min(pisadas)`, no `+` (mutation testing T027):
    con `+`, dos pisadas cercanas (estiramiento real bajo) se calculan
    como una suma mucho mayor, que puede exceder el límite en falso."""
    from guitar_tabs_analysis.analytics.metrica_digitacion import (
        _generar_combinaciones_validas,
    )

    modelo = _modelo(traste_maximo=4, limite_estiramiento_trastes=4)
    # 42.0 -- única candidata: E traste 2. 53.0 -- única candidata: D
    # traste 3 (A exigiría traste 8, fuera de traste_maximo=4).
    instante = Instante(
        notas=[
            NotaReferencia(tono_midi=42.0, inicio_s=0.0, fin_s=0.5),
            NotaReferencia(tono_midi=53.0, inicio_s=0.0, fin_s=0.5),
        ],
        inicio_representativo_s=0.0,
    )
    resultado = _generar_combinaciones_validas(instante, modelo)
    assert isinstance(resultado, list)
    combos = [{(pa.posicion.cuerda, pa.posicion.traste) for pa in combo} for combo in resultado]
    # (E,2)+(D,3): estiramiento real = 3-2 = 1 <= 4 -- MUST ser válida
    # (la suma, 5, excedería el límite -- por eso discrimina la resta).
    assert {("E", 2), ("D", 3)} in combos


def test_asignar_instante_nota_sola_con_pisada_nunca_excede_estiramiento_cero() -> None:
    """El caso base `else 0` (no `else 1`) cuando hay menos de dos
    pisadas -- una sola nota fretteada nunca "estira" nada, sin importar
    cuán bajo sea el límite declarado (mutation testing T027)."""
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_instante

    modelo = _modelo(limite_estiramiento_trastes=0)
    resultado = asignar_instante(_instante([41.0]), modelo)
    assert isinstance(resultado, list)
    assert resultado[0].posicion == Posicion(cuerda="E", traste=1)


def test_asignar_instante_estiramiento_igual_al_limite_es_valido_no_excede() -> None:
    """`estiramiento > limite`, no `>=` -- un estiramiento EXACTAMENTE
    igual al límite declarado MUST seguir siendo válido (mutation
    testing T027)."""
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_instante

    modelo = _modelo(traste_maximo=6, limite_estiramiento_trastes=5)
    # 41.0 -> única candidata E1; 70.0 -> única candidata e6 (con
    # traste_maximo=6, ninguna otra cuerda alcanza 70). Estiramiento
    # real = 6-1 = 5, exactamente el límite.
    resultado = asignar_instante(_instante([41.0, 70.0]), modelo)
    assert isinstance(resultado, list)


def test_asignar_instante_sigue_evaluando_tras_una_combinacion_invalida_por_estiramiento() -> None:
    """`continue`, no `break`, cuando una combinación excede el límite
    -- las combinaciones siguientes en la iteración (candidatas de la
    misma nota en otra cuerda) MUST seguir evaluándose (mutation testing
    T027: `break` corta la búsqueda entera en la primera combinación
    inválida, aunque combinaciones válidas existan más adelante)."""
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_instante

    modelo = _modelo(traste_maximo=6, limite_estiramiento_trastes=4)
    # 41.0 -> única candidata E1. 56.0 -> dos candidatas con
    # traste_maximo=6: D6 (primera, por orden de cuerdas E/A/D/G/B/e) y
    # G1 (segunda). La combinación (E1,D6) excede el límite (5 > 4) y
    # aparece PRIMERO en el orden de itertools.product -- (E1,G1),
    # válida (estiramiento 0), aparece después y MUST evaluarse igual.
    resultado = asignar_instante(_instante([41.0, 56.0]), modelo)
    assert isinstance(resultado, list)


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


def test_agrupar_en_instantes_compara_diferencia_no_suma_de_inicios() -> None:
    """`nota.inicio_s - inicio_grupo`, no `+` (mutation testing T027):
    con inicio_grupo en 0.0 (el caso de la mayoría de los tests, primer
    instante de una secuencia empezando en el origen), resta y suma dan
    el mismo resultado -- este test usa un `inicio_grupo` NO nulo para
    que discriminen."""
    from guitar_tabs_analysis.analytics.metrica_digitacion import agrupar_en_instantes

    modelo = _modelo(ventana_instante_s=0.03)
    n1 = NotaReferencia(tono_midi=40.0, inicio_s=10.0, fin_s=10.5)
    n2 = NotaReferencia(tono_midi=45.0, inicio_s=10.02, fin_s=10.5)
    instantes = agrupar_en_instantes([n1, n2], modelo)
    assert len(instantes) == 1
    assert instantes[0].notas == [n1, n2]


def test_agrupar_en_instantes_ventana_exacta_sigue_en_el_mismo_grupo() -> None:
    """`> modelo.ventana_instante_s`, no `>=` -- una diferencia de inicio
    EXACTAMENTE igual a la ventana MUST seguir agrupada (mutation testing
    T027)."""
    from guitar_tabs_analysis.analytics.metrica_digitacion import agrupar_en_instantes

    modelo = _modelo(ventana_instante_s=0.03)
    n1 = NotaReferencia(tono_midi=40.0, inicio_s=0.0, fin_s=0.5)
    n2 = NotaReferencia(tono_midi=45.0, inicio_s=0.03, fin_s=0.5)
    instantes = agrupar_en_instantes([n1, n2], modelo)
    assert len(instantes) == 1
    assert instantes[0].notas == [n1, n2]


# ---------------------------------------------------------------------
# _estiramiento / _centroide (helpers internos de asignar_secuencia,
# T012) -- probados directamente, no solo a través de asignar_secuencia,
# porque son el cálculo de coste de nodo/arista de la DP: un error ahí
# se propagaría a costes agregados de muchos instantes, difícil de
# aislar desde afuera.
# ---------------------------------------------------------------------


def test_estiramiento_traste_uno_cuenta_como_pisada() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import _estiramiento

    assert _estiramiento([Posicion(cuerda="E", traste=1), Posicion(cuerda="D", traste=6)]) == 5


def test_estiramiento_es_resta_no_suma() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import _estiramiento

    assert _estiramiento([Posicion(cuerda="E", traste=2), Posicion(cuerda="D", traste=3)]) == 1


def test_estiramiento_con_exactamente_dos_pisadas_usa_la_resta() -> None:
    """`len(pisadas) >= 2`, no `> 2` ni `>= 3` -- EXACTAMENTE dos
    pisadas ya activa el cálculo real, no el caso base (mutation
    testing T027)."""
    from guitar_tabs_analysis.analytics.metrica_digitacion import _estiramiento

    assert _estiramiento([Posicion(cuerda="E", traste=3), Posicion(cuerda="D", traste=7)]) == 4


def test_centroide_promedia_trastes_no_multiplica() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import _centroide

    t, _c = _centroide(
        [Posicion(cuerda="E", traste=2), Posicion(cuerda="A", traste=4)],
        ["E", "A", "D", "G", "B", "e"],
    )
    assert t == 3.0


def test_centroide_promedia_indices_de_cuerda_no_multiplica() -> None:
    from guitar_tabs_analysis.analytics.metrica_digitacion import _centroide

    _t, c = _centroide(
        [Posicion(cuerda="E", traste=2), Posicion(cuerda="D", traste=2)],
        ["E", "A", "D", "G", "B", "e"],
    )
    assert c == 1.0  # (0 + 2) / 2


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


def test_asignar_secuencia_desempate_de_costo_igual_conserva_el_primero() -> None:
    """`costo < mejor_costo`, no `<=` -- ante un empate exacto de coste
    entre dos candidatas del instante anterior, MUST conservar la
    PRIMERA encontrada (orden determinista de `generar_candidatas`,
    Principio VIII), nunca la última que empate (mutation testing T027).
    """
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_secuencia

    modelo = _modelo(traste_maximo=5)
    # 45.0 -> candidatas [(E,5), (A,0)], en ese orden. 48.0 -> única
    # candidata (A,3). Ambos caminos hacia (A,3) cuestan exactamente lo
    # mismo: (E,5)->(A,3) = |3-5|+|1-0| = 3; (A,0)->(A,3) = |3-0|+0 = 3.
    notas = [
        NotaReferencia(tono_midi=45.0, inicio_s=0.0, fin_s=0.4),
        NotaReferencia(tono_midi=48.0, inicio_s=1.0, fin_s=1.4),
    ]
    digitacion = asignar_secuencia(notas, modelo)
    assert digitacion.posiciones[0].posicion == Posicion(cuerda="E", traste=5)


def test_asignar_secuencia_costo_de_nodo_se_suma_no_se_resta() -> None:
    """`costeNodo(p) + mín(...)`, no `-` -- el coste de estiramiento de
    un acorde en un instante que NO es el primero MUST sumarse al
    coste acumulado (mutation testing T027: `coincide_con_fuerza_bruta`
    no lo detectaba porque sus secuencias no tenían ningún acorde con
    estiramiento distinto de cero después del primer instante)."""
    from guitar_tabs_analysis.analytics.metrica_digitacion import (
        agrupar_en_instantes,
        asignar_secuencia,
    )

    modelo = _modelo(traste_maximo=4)
    notas = [
        NotaReferencia(tono_midi=45.0, inicio_s=0.0, fin_s=0.4),  # A0, único
        NotaReferencia(tono_midi=42.0, inicio_s=1.0, fin_s=1.4),  # acorde: E2
        NotaReferencia(tono_midi=53.0, inicio_s=1.0, fin_s=1.4),  # acorde: D3 (estiramiento 1)
    ]
    digitacion = asignar_secuencia(notas, modelo)
    instantes = agrupar_en_instantes(notas, modelo)
    esperado = _fuerza_bruta_coste_minimo(instantes, modelo)
    assert digitacion.coste_total == pytest.approx(esperado)


def test_asignar_secuencia_reconstruye_el_camino_optimo_no_el_indice_inicial() -> None:
    """El backtracking de backpointers MUST producir el índice óptimo
    real en cada posición de `camino`, nunca quedarse en su valor
    inicial (mutation testing T027: varios mutantes del rango del
    bucle -- `range(0,-1)`, `range(len-1,-1)`, `range(len-2,0,-1)`,
    paso `-2`, etc. -- dejan el bucle sin ejecutar ninguna iteración
    real para algún índice, indistinguible mirando solo `coste_total`,
    que se calcula ANTES de este bucle)."""
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_secuencia

    modelo = _modelo(traste_maximo=5)
    # 45.0 -> candidatas [(E,5), (A,0)]. La óptima real es (A,0):
    # estrictamente más barata hacia la siguiente candidata (A,2) que
    # (E,5) -- el backtracking MUST elegirla, no el índice 0 (E,5) que
    # `generar_candidatas` produce primero.
    notas = [
        NotaReferencia(tono_midi=45.0, inicio_s=0.0, fin_s=0.4),
        NotaReferencia(tono_midi=47.0, inicio_s=1.0, fin_s=1.4),  # única: (A,2)
        NotaReferencia(tono_midi=54.0, inicio_s=2.0, fin_s=2.4),  # única: (D,4)
    ]
    digitacion = asignar_secuencia(notas, modelo)
    assert digitacion.posiciones[0].posicion == Posicion(cuerda="A", traste=0)
    assert digitacion.posiciones[1].posicion == Posicion(cuerda="A", traste=2)
    assert digitacion.posiciones[2].posicion == Posicion(cuerda="D", traste=4)


def test_asignar_secuencia_reconstruye_camino_optimo_en_un_instante_intermedio() -> None:
    """Mismo criterio que arriba, pero con la candidata ambigua en el
    instante DEL MEDIO -- distingue mutantes del rango del bucle de
    backtracking que se truncan un paso demasiado pronto, dejando ese
    índice intermedio en su valor por defecto en vez del correctamente
    retropropagado (mutation testing T027: `range(len(activos) - 2, 0,
    -1)` sobrevivía al test anterior porque ahí la candidata ambigua
    estaba en el primer instante, cuyo índice coincide con el valor por
    defecto sin importar si el bucle lo visita o no)."""
    from guitar_tabs_analysis.analytics.metrica_digitacion import asignar_secuencia

    modelo = _modelo(traste_maximo=5)
    notas = [
        NotaReferencia(tono_midi=41.0, inicio_s=0.0, fin_s=0.4),  # única: (E,1)
        # candidatas [(E,5), (A,0)] -- la óptima real es (A,0), no la
        # primera generada.
        NotaReferencia(tono_midi=45.0, inicio_s=1.0, fin_s=1.4),
        NotaReferencia(tono_midi=47.0, inicio_s=2.0, fin_s=2.4),  # única: (A,2)
    ]
    digitacion = asignar_secuencia(notas, modelo)
    assert digitacion.posiciones[0].posicion == Posicion(cuerda="E", traste=1)
    assert digitacion.posiciones[1].posicion == Posicion(cuerda="A", traste=0)
    assert digitacion.posiciones[2].posicion == Posicion(cuerda="A", traste=2)


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


def test_evaluar_coincidencia_nota_sin_real_no_detiene_la_evaluacion_de_las_siguientes() -> None:
    """`continue`, no `break`, cuando una nota no tiene posición real
    correspondiente -- las notas SIGUIENTES en `digitacion.posiciones`
    MUST seguir evaluándose (mutation testing T027: con `break`, una
    sola nota "huérfana" al principio de la lista haría que ninguna
    nota posterior, aunque coincida, se contara)."""
    n1 = NotaReferencia(tono_midi=99.0, inicio_s=9.0, fin_s=9.5)  # sin real correspondiente
    n2 = NotaReferencia(tono_midi=47.0, inicio_s=1.0, fin_s=1.5)
    digitacion = Digitacion(
        posiciones=[
            PosicionAsignada(nota=n1, posicion=Posicion(cuerda="A", traste=2)),
            PosicionAsignada(nota=n2, posicion=Posicion(cuerda="A", traste=2)),
        ],
        exclusiones=[],
        coste_total=0.0,
    )
    reales = [
        NotaConPosicionReal(tono_midi=47.0, inicio_s=1.0, fin_s=1.5, cuerda_real="A", traste_real=2)
    ]
    resultado = evaluar_coincidencia(digitacion, reales)
    assert resultado.num_notas_medidas == 1
    assert resultado.num_notas_coincidentes == 1


def test_evaluar_coincidencia_cuenta_incrementa_no_se_fija_en_uno() -> None:
    """`num_coincidentes += 1`, no `= 1` -- con DOS notas coincidentes,
    el conteo MUST ser 2, no quedarse fijo en 1 (mutation testing T027).
    """
    n1 = NotaReferencia(tono_midi=47.0, inicio_s=1.0, fin_s=1.5)
    n2 = NotaReferencia(tono_midi=50.0, inicio_s=2.0, fin_s=2.5)
    digitacion = Digitacion(
        posiciones=[
            PosicionAsignada(nota=n1, posicion=Posicion(cuerda="A", traste=2)),
            PosicionAsignada(nota=n2, posicion=Posicion(cuerda="D", traste=0)),
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
    assert resultado.num_notas_coincidentes == 2


def test_evaluar_coincidencia_fraccion_es_division_no_multiplicacion() -> None:
    """`num_coincidentes / num_medidas`, no `*` -- con 1 de 2 notas
    coincidentes, la fracción MUST ser 0.5 (mutation testing T027: con
    `*`, daría 2, un número que ni siquiera es una fracción válida)."""
    n1 = NotaReferencia(tono_midi=47.0, inicio_s=1.0, fin_s=1.5)
    n2 = NotaReferencia(tono_midi=50.0, inicio_s=2.0, fin_s=2.5)
    digitacion = Digitacion(
        posiciones=[
            PosicionAsignada(nota=n1, posicion=Posicion(cuerda="A", traste=2)),
            PosicionAsignada(nota=n2, posicion=Posicion(cuerda="E", traste=10)),  # no coincide
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
    assert resultado.fraccion_coincidencia == 0.5


# ---------------------------------------------------------------------
# agregar_conjunto (T015, contracts/digitacion.md postcondición 6,
# mismo patrón que agregar_conjunto del hito 2, research.md #16 de esa
# feature): SUMA conteos ya resueltos por grabación, nunca promedia
# fracciones ni poolea notas crudas entre grabaciones.
# ---------------------------------------------------------------------


def _resultado_grabacion(
    grabacion_id: str,
    posiciones: list[PosicionAsignada],
    reales: list[NotaConPosicionReal],
) -> ResultadoDigitacionGrabacion:
    return ResultadoDigitacionGrabacion(
        grabacion_id=grabacion_id,
        digitacion=Digitacion(posiciones=posiciones, exclusiones=[], coste_total=0.0),
        notas_con_posicion_real=reales,
        exclusion=None,
    )


def test_agregar_conjunto_ignora_grabaciones_excluidas() -> None:
    n1 = NotaReferencia(tono_midi=47.0, inicio_s=1.0, fin_s=1.5)
    g1 = _resultado_grabacion(
        "g1",
        [PosicionAsignada(nota=n1, posicion=Posicion(cuerda="A", traste=2))],
        [
            NotaConPosicionReal(
                tono_midi=47.0, inicio_s=1.0, fin_s=1.5, cuerda_real="A", traste_real=2
            )
        ],
    )
    g2_excluida = ResultadoDigitacionGrabacion(
        grabacion_id="g2",
        digitacion=None,
        notas_con_posicion_real=None,
        exclusion=ExclusionDigitacion(grabacion_id="g2", detalle="no existe"),
    )
    n2 = NotaReferencia(tono_midi=50.0, inicio_s=2.0, fin_s=2.5)
    g3 = _resultado_grabacion(
        "g3",
        [PosicionAsignada(nota=n2, posicion=Posicion(cuerda="D", traste=0))],
        [
            NotaConPosicionReal(
                tono_midi=50.0, inicio_s=2.0, fin_s=2.5, cuerda_real="D", traste_real=0
            )
        ],
    )

    resultado = agregar_conjunto([g1, g2_excluida, g3])

    assert resultado.num_notas_medidas == 2
    assert resultado.num_notas_coincidentes == 2
    assert resultado.fraccion_coincidencia == 1.0


def test_agregar_conjunto_suma_conteos_no_promedia_fracciones() -> None:
    """Construido para que la suma y el promedio de fracciones por
    grabación den cifras DISTINTAS -- fija que se pooleó por conteo, no
    que se promedió (mismo patrón que la Feature 006, research.md #16
    de esa feature: una grabación con más notas pesa más que una con
    pocas)."""
    n1 = NotaReferencia(tono_midi=47.0, inicio_s=1.0, fin_s=1.5)
    g_una_nota_coincide = _resultado_grabacion(
        "g1",
        [PosicionAsignada(nota=n1, posicion=Posicion(cuerda="A", traste=2))],
        [
            NotaConPosicionReal(
                tono_midi=47.0, inicio_s=1.0, fin_s=1.5, cuerda_real="A", traste_real=2
            )
        ],
    )
    notas_b = [
        NotaReferencia(tono_midi=50.0, inicio_s=2.0, fin_s=2.5),
        NotaReferencia(tono_midi=55.0, inicio_s=3.0, fin_s=3.5),
        NotaReferencia(tono_midi=59.0, inicio_s=4.0, fin_s=4.5),
    ]
    g_tres_notas_ninguna_coincide = _resultado_grabacion(
        "g2",
        [PosicionAsignada(nota=n, posicion=Posicion(cuerda="E", traste=19)) for n in notas_b],
        [
            NotaConPosicionReal(
                tono_midi=n.tono_midi,
                inicio_s=n.inicio_s,
                fin_s=n.fin_s,
                cuerda_real="D",
                traste_real=0,
            )
            for n in notas_b
        ],
    )

    resultado = agregar_conjunto([g_una_nota_coincide, g_tres_notas_ninguna_coincide])

    assert resultado.num_notas_medidas == 4
    assert resultado.num_notas_coincidentes == 1
    assert resultado.fraccion_coincidencia == pytest.approx(0.25)
    promedio_por_grabacion = (1.0 + 0.0) / 2
    assert resultado.fraccion_coincidencia != pytest.approx(promedio_por_grabacion)


def test_agregar_conjunto_sin_notas_medidas_da_fraccion_none() -> None:
    todas_excluidas = [
        ResultadoDigitacionGrabacion(
            grabacion_id="g1",
            digitacion=None,
            notas_con_posicion_real=None,
            exclusion=ExclusionDigitacion(grabacion_id="g1", detalle="no existe"),
        )
    ]
    resultado = agregar_conjunto(todas_excluidas)
    assert resultado.fraccion_coincidencia is None
    assert resultado.num_notas_medidas == 0
    assert resultado.num_notas_coincidentes == 0


def test_agregar_conjunto_con_exactamente_una_nota_medida_calcula_fraccion() -> None:
    """`num_medidas_total > 0`, no `> 1` -- con exactamente UNA nota
    medida en todo el conjunto, la fracción MUST calcularse igual, no
    quedar en `None` (mutation testing T027)."""
    n1 = NotaReferencia(tono_midi=47.0, inicio_s=1.0, fin_s=1.5)
    g1 = _resultado_grabacion(
        "g1",
        [PosicionAsignada(nota=n1, posicion=Posicion(cuerda="A", traste=2))],
        [
            NotaConPosicionReal(
                tono_midi=47.0, inicio_s=1.0, fin_s=1.5, cuerda_real="A", traste_real=2
            )
        ],
    )
    resultado = agregar_conjunto([g1])
    assert resultado.num_notas_medidas == 1
    assert resultado.fraccion_coincidencia == 1.0
