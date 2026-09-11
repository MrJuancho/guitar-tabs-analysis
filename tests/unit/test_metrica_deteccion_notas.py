"""Tests unitarios de `analytics.metrica_deteccion_notas` (User Story 1
y User Story 3, `specs/006-deteccion-notas-guitarra-limpia/tasks.md`).

T007: los cinco Acceptance Scenarios de `spec.md` User Story 1, más el
caso de respuesta conocida (nota estimada = nota de referencia, pedido
explícito de la sesión de `/speckit-implement`).

T008: el denominador-cero de FR-008 (subconjunto vacío), en sus tres
combinaciones.

T018: `clasificar_polifonia_en_instante`. T020: `evaluar_grabacion`.
T022: `agregar_conjunto`.
"""

from __future__ import annotations

from guitar_tabs_analysis.analytics.metrica_deteccion_notas import (
    ClasificacionPolifonia,
    ExclusionDeteccion,
    NotaEstimada,
    ResultadoDeteccionGrabacion,
    ResultadoSubconjunto,
    agregar_conjunto,
    clasificar_polifonia_en_instante,
    evaluar_grabacion,
    evaluar_subconjunto,
)
from guitar_tabs_analysis.ingestion.guitarset import NotaReferencia

# ---------------------------------------------------------------------
# T007 -- Acceptance Scenarios 1-5 de spec.md User Story 1.
# ---------------------------------------------------------------------


def test_as1_mismo_tono_e_inicio_dentro_de_ventana_acierta() -> None:
    referencia = NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=1.5)
    estimada = NotaEstimada(tono_midi=60.0, inicio_s=1.02, fin_s=1.6)

    resultado = evaluar_subconjunto([referencia], [estimada])

    assert resultado.precision == 1.0
    assert resultado.exhaustividad == 1.0
    assert resultado.balance_f1 == 1.0


def test_as2_tono_fuera_de_tolerancia_no_acierta() -> None:
    # 1.0 MIDI de diferencia == 100 cents (el doble de la tolerancia de
    # 50 cents, research.md #3) -- claramente fuera, sin importar que el
    # inicio esté muy cerca.
    referencia = NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=1.5)
    estimada = NotaEstimada(tono_midi=61.0, inicio_s=1.0, fin_s=1.5)

    resultado = evaluar_subconjunto([referencia], [estimada])

    assert resultado.precision == 0.0
    assert resultado.exhaustividad == 0.0
    assert resultado.balance_f1 == 0.0


def test_as3_inicio_fuera_de_ventana_no_acierta() -> None:
    referencia = NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=1.5)
    estimada = NotaEstimada(tono_midi=60.0, inicio_s=1.5, fin_s=2.0)

    resultado = evaluar_subconjunto([referencia], [estimada])

    assert resultado.precision == 0.0
    assert resultado.exhaustividad == 0.0
    assert resultado.balance_f1 == 0.0


def test_as4_duracion_distinta_no_participa_del_criterio() -> None:
    # Tono e inicio dentro de tolerancia; la duración difiere
    # sustancialmente (0.1s vs ~4s) -- FR-004: nunca participa.
    referencia = NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=1.1)
    estimada = NotaEstimada(tono_midi=60.0, inicio_s=1.01, fin_s=5.0)

    resultado = evaluar_subconjunto([referencia], [estimada])

    assert resultado.precision == 1.0
    assert resultado.exhaustividad == 1.0
    assert resultado.balance_f1 == 1.0


def test_as5_una_sola_estimada_no_acredita_dos_referencias_ambiguas() -> None:
    # Dos referencias suficientemente cerca entre sí como para que ambas
    # caigan dentro de tolerancia/ventana de la ÚNICA nota estimada --
    # solo una puede acreditarse (FR-005): exhaustividad = 1/2, nunca 1.0.
    referencia_a = NotaReferencia(tono_midi=60.0, inicio_s=1.00, fin_s=1.3)
    referencia_b = NotaReferencia(tono_midi=60.0, inicio_s=1.01, fin_s=1.3)
    estimada = NotaEstimada(tono_midi=60.0, inicio_s=1.005, fin_s=1.3)

    resultado = evaluar_subconjunto([referencia_a, referencia_b], [estimada])

    assert resultado.num_notas_referencia == 2
    assert resultado.num_notas_estimadas == 1
    assert resultado.precision == 1.0
    assert resultado.exhaustividad == 0.5


def test_as5_una_sola_referencia_no_se_acredita_dos_veces() -> None:
    # Simétrico al caso anterior: dos estimadas ambiguas contra una sola
    # referencia -- solo una puede acreditarse: precisión = 1/2, nunca 1.0.
    referencia = NotaReferencia(tono_midi=60.0, inicio_s=1.00, fin_s=1.3)
    estimada_a = NotaEstimada(tono_midi=60.0, inicio_s=1.00, fin_s=1.3)
    estimada_b = NotaEstimada(tono_midi=60.0, inicio_s=1.01, fin_s=1.3)

    resultado = evaluar_subconjunto([referencia], [estimada_a, estimada_b])

    assert resultado.num_notas_referencia == 1
    assert resultado.num_notas_estimadas == 2
    assert resultado.exhaustividad == 1.0
    assert resultado.precision == 0.5


def test_respuesta_conocida_estimada_igual_a_referencia_da_uno_exacto() -> None:
    """Caso de respuesta conocida (mismo criterio que SI-SDR del hito 1,
    pedido explícito de esta sesión): la MISMA lista de `NotaReferencia`,
    reconstruida como `NotaEstimada` con idéntico tono_midi/inicio_s,
    debe dar precisión/exhaustividad/balance EXACTAMENTE 1.0 -- cada
    nota se empareja consigo misma, sin tolerancia de por medio."""
    referencias = [
        NotaReferencia(tono_midi=60.0, inicio_s=0.0, fin_s=0.5),
        NotaReferencia(tono_midi=64.0, inicio_s=1.0, fin_s=1.3),
        NotaReferencia(tono_midi=67.0, inicio_s=2.0, fin_s=2.7),
    ]
    estimadas = [
        NotaEstimada(tono_midi=r.tono_midi, inicio_s=r.inicio_s, fin_s=r.fin_s) for r in referencias
    ]

    resultado = evaluar_subconjunto(referencias, estimadas)

    assert resultado.precision == 1.0
    assert resultado.exhaustividad == 1.0
    assert resultado.balance_f1 == 1.0
    assert resultado.num_notas_referencia == 3
    assert resultado.num_notas_estimadas == 3


# ---------------------------------------------------------------------
# T008 -- Subconjunto vacío (FR-008), las tres combinaciones.
# ---------------------------------------------------------------------


def test_subconjunto_vacio_ambas_listas_da_todo_none() -> None:
    resultado = evaluar_subconjunto([], [])

    assert resultado == ResultadoSubconjunto(
        precision=None,
        exhaustividad=None,
        balance_f1=None,
        num_notas_referencia=0,
        num_notas_estimadas=0,
        verdaderos_positivos=0,
    )


def test_subconjunto_vacio_solo_referencia_da_exhaustividad_none_precision_cero() -> None:
    estimada = NotaEstimada(tono_midi=60.0, inicio_s=1.0, fin_s=1.5)

    resultado = evaluar_subconjunto([], [estimada])

    assert resultado.exhaustividad is None
    assert resultado.precision == 0.0
    assert resultado.balance_f1 is None
    assert resultado.num_notas_referencia == 0
    assert resultado.num_notas_estimadas == 1


def test_subconjunto_vacio_solo_estimada_da_precision_none_exhaustividad_cero() -> None:
    referencia = NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=1.5)

    resultado = evaluar_subconjunto([referencia], [])

    assert resultado.precision is None
    assert resultado.exhaustividad == 0.0
    assert resultado.balance_f1 is None
    assert resultado.num_notas_referencia == 1
    assert resultado.num_notas_estimadas == 0


# ---------------------------------------------------------------------
# T018 -- clasificar_polifonia_en_instante (research.md #8, FR-006): la
# clasificación sale EXCLUSIVAMENTE de `notas_referencia` -- ninguno de
# estos tests pasa nunca una nota estimada como argumento.
# ---------------------------------------------------------------------


def test_clasificar_acorde_de_dos_referencias_solapando_es_polifonica() -> None:
    referencias = [
        NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=2.0),
        NotaReferencia(tono_midi=64.0, inicio_s=1.2, fin_s=2.2),
    ]

    resultado: ClasificacionPolifonia = clasificar_polifonia_en_instante(1.5, referencias)

    assert resultado == "polifonica"


def test_clasificar_tres_referencias_solapando_sigue_siendo_polifonica() -> None:
    referencias = [
        NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=2.0),
        NotaReferencia(tono_midi=64.0, inicio_s=1.0, fin_s=2.0),
        NotaReferencia(tono_midi=67.0, inicio_s=1.0, fin_s=2.0),
    ]

    assert clasificar_polifonia_en_instante(1.5, referencias) == "polifonica"


def test_clasificar_una_sola_nota_suelta_es_monofonica() -> None:
    referencias = [NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=2.0)]

    assert clasificar_polifonia_en_instante(1.5, referencias) == "monofonica"


def test_clasificar_dos_referencias_sin_solapar_el_instante_es_monofonica() -> None:
    # Dos referencias en la grabación, pero solo UNA solapa el instante --
    # 1 solapando, no 2, sigue siendo "monofonica".
    referencias = [
        NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=2.0),
        NotaReferencia(tono_midi=64.0, inicio_s=5.0, fin_s=6.0),
    ]

    assert clasificar_polifonia_en_instante(1.5, referencias) == "monofonica"


def test_clasificar_borde_exacto_del_intervalo_cuenta_como_solape() -> None:
    referencias = [
        NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=2.0),
        NotaReferencia(tono_midi=64.0, inicio_s=2.0, fin_s=3.0),
    ]

    # instante == fin de la primera == inicio de la segunda: solape
    # parcial cuenta (pedido explícito de tasks.md T017).
    assert clasificar_polifonia_en_instante(2.0, referencias) == "polifonica"


def test_clasificar_cero_referencias_es_monofonica_caso_degenerado() -> None:
    assert clasificar_polifonia_en_instante(1.5, []) == "monofonica"


# ---------------------------------------------------------------------
# T020 -- evaluar_grabacion: partición mono/poli SIEMPRE contra
# notas_referencia (FR-006), evaluar_subconjunto una vez por subconjunto
# (contracts/deteccion.md postcondición 4).
# ---------------------------------------------------------------------


def test_evaluar_grabacion_pasajes_mixtos_da_las_tres_cifras_esperadas_a_mano() -> None:
    # Pasaje monofónico: una única nota aislada en su propio instante.
    ref_mono = NotaReferencia(tono_midi=60.0, inicio_s=0.0, fin_s=0.5)
    # Pasaje polifónico: un acorde de dos notas simultáneas.
    ref_poli_a = NotaReferencia(tono_midi=64.0, inicio_s=2.0, fin_s=3.0)
    ref_poli_b = NotaReferencia(tono_midi=67.0, inicio_s=2.0, fin_s=3.0)
    notas_referencia = [ref_mono, ref_poli_a, ref_poli_b]

    est_mono_correcta = NotaEstimada(tono_midi=60.0, inicio_s=0.02, fin_s=0.5)
    est_poli_a_correcta = NotaEstimada(tono_midi=64.0, inicio_s=2.01, fin_s=3.0)
    # Tono muy fuera de tolerancia (3 semitonos = 300 cents) -- no acierta
    # contra ref_poli_b pese a compartir el instante de inicio.
    est_poli_b_incorrecta = NotaEstimada(tono_midi=70.0, inicio_s=2.01, fin_s=3.0)
    # Nota estimada suelta, sin ninguna referencia cerca -- su propio
    # instante (10.0) no solapa ninguna referencia, así que se clasifica
    # monofónica por el caso degenerado (FR-006) y resta precisión ahí.
    est_extra_sin_referencia = NotaEstimada(tono_midi=72.0, inicio_s=10.0, fin_s=10.5)
    notas_estimadas = [
        est_mono_correcta,
        est_poli_a_correcta,
        est_poli_b_incorrecta,
        est_extra_sin_referencia,
    ]

    global_, mono, poli = evaluar_grabacion(notas_referencia, notas_estimadas)

    # Global: 2 de 3 referencias acertadas, 2 de 4 estimadas acertaron.
    assert global_.num_notas_referencia == 3
    assert global_.num_notas_estimadas == 4
    assert global_.precision == 0.5
    assert global_.exhaustividad == 2 / 3

    # Monofónico: solo ref_mono (1) vs [est_mono_correcta, est_extra_sin_referencia] (2).
    assert mono.num_notas_referencia == 1
    assert mono.num_notas_estimadas == 2
    assert mono.precision == 0.5
    assert mono.exhaustividad == 1.0

    # Polifónico: [ref_poli_a, ref_poli_b] (2) vs [est_poli_a_correcta, est_poli_b_incorrecta] (2).
    assert poli.num_notas_referencia == 2
    assert poli.num_notas_estimadas == 2
    assert poli.precision == 0.5
    assert poli.exhaustividad == 0.5


def test_evaluar_grabacion_100_por_ciento_monofonica_reporta_polifonico_none() -> None:
    referencia_a = NotaReferencia(tono_midi=60.0, inicio_s=0.0, fin_s=0.5)
    referencia_b = NotaReferencia(tono_midi=62.0, inicio_s=0.6, fin_s=1.0)
    notas_referencia = [referencia_a, referencia_b]
    notas_estimadas = [
        NotaEstimada(tono_midi=60.0, inicio_s=0.01, fin_s=0.5),
        NotaEstimada(tono_midi=62.0, inicio_s=0.61, fin_s=1.0),
    ]

    global_, mono, poli = evaluar_grabacion(notas_referencia, notas_estimadas)

    assert poli == ResultadoSubconjunto(
        precision=None,
        exhaustividad=None,
        balance_f1=None,
        num_notas_referencia=0,
        num_notas_estimadas=0,
        verdaderos_positivos=0,
    )
    assert mono.num_notas_referencia == 2
    assert mono.precision == 1.0
    assert mono.exhaustividad == 1.0
    assert global_.precision == 1.0
    assert global_.exhaustividad == 1.0


def test_evaluar_grabacion_estimada_sin_ninguna_referencia_es_monofonica_y_resta_precision() -> (
    None
):
    notas_referencia: list[NotaReferencia] = []
    notas_estimadas = [NotaEstimada(tono_midi=60.0, inicio_s=1.0, fin_s=1.5)]

    global_, mono, poli = evaluar_grabacion(notas_referencia, notas_estimadas)

    assert global_.precision == 0.0
    assert global_.exhaustividad is None
    assert mono.precision == 0.0
    assert mono.exhaustividad is None
    assert poli == ResultadoSubconjunto(
        precision=None,
        exhaustividad=None,
        balance_f1=None,
        num_notas_referencia=0,
        num_notas_estimadas=0,
        verdaderos_positivos=0,
    )


# ---------------------------------------------------------------------
# FR-014, research.md #17 -- corrección posterior a T035: la partición
# mono/poli hereda del ÚNICO emparejamiento de la grabación, nunca
# reclasifica ni reempareja cada lado por separado. Guarda permanente:
# verdaderos_positivos(mono) + verdaderos_positivos(poli) ==
# verdaderos_positivos(global), SIEMPRE (SC-007) -- el property test de
# tests/property/test_metrica_deteccion_notas_property.py generaliza
# esta misma afirmación sobre entradas arbitrarias.
# ---------------------------------------------------------------------


def test_evaluar_grabacion_par_hereda_clase_de_referencia_no_del_instante_de_estimada() -> None:
    """`ref_a` y `ref_b` arrancan juntas (acorde: 2 referencias solapando
    su propio inicio) -> ambas clasifican "polifonica". `est_b` empareja
    con `ref_b` (mismo tono, inicio dentro de los 50ms de ventana), pero
    el propio inicio de `est_b` (2.04) ya no solapa a `ref_a` (que
    termina en 2.02) -- evaluado en soledad, el instante de `est_b`
    clasificaria "monofonica" (afirmado explícitamente abajo, research.md
    #17: esa discrepancia entre los dos lados del par era la causa real
    del defecto). El par MUST contar como acierto polifónico, heredado de
    `ref_b`, no perderse por la discrepancia."""
    ref_a = NotaReferencia(tono_midi=60.0, inicio_s=2.00, fin_s=2.02)
    ref_b = NotaReferencia(tono_midi=64.0, inicio_s=2.00, fin_s=3.00)
    est_b = NotaEstimada(tono_midi=64.0, inicio_s=2.04, fin_s=3.00)

    # El propio instante de `est_b`, evaluado en soledad contra las
    # referencias, clasificaría monofónica -- la fuente exacta del
    # defecto que este test fija.
    assert clasificar_polifonia_en_instante(est_b.inicio_s, [ref_a, ref_b]) == "monofonica"

    global_, mono, poli = evaluar_grabacion([ref_a, ref_b], [est_b])

    assert global_.verdaderos_positivos == 1
    assert poli.verdaderos_positivos == 1
    assert mono.verdaderos_positivos == 0
    assert mono.verdaderos_positivos + poli.verdaderos_positivos == global_.verdaderos_positivos


# ---------------------------------------------------------------------
# T022 -- agregar_conjunto: pool plano sobre todas las grabaciones no
# excluidas, nunca promedio de resultados por grabación (contracts/
# deteccion.md postcondición 5).
# ---------------------------------------------------------------------


def test_agregar_conjunto_excluye_las_grabaciones_con_exclusion_del_pool() -> None:
    referencia = NotaReferencia(tono_midi=60.0, inicio_s=0.0, fin_s=0.5)
    estimada = NotaEstimada(tono_midi=60.0, inicio_s=0.01, fin_s=0.5)
    resultados = [
        ResultadoDeteccionGrabacion(
            grabacion_id="rec_ok",
            notas_referencia=[referencia],
            notas_estimadas=[estimada],
            exclusion=None,
        ),
        ResultadoDeteccionGrabacion(
            grabacion_id="rec_excluida",
            notas_referencia=None,
            notas_estimadas=None,
            exclusion=ExclusionDeteccion("rec_excluida", "fallo simulado"),
        ),
    ]

    global_, _mono, _poli = agregar_conjunto(resultados)

    # Si la grabación excluida contaminara el pool, estas cifras no
    # coincidirían con el cálculo de una única grabación limpia.
    assert global_.num_notas_referencia == 1
    assert global_.num_notas_estimadas == 1
    assert global_.precision == 1.0
    assert global_.exhaustividad == 1.0


def test_agregar_conjunto_no_detiene_el_pool_si_la_exclusion_esta_en_medio() -> None:
    # La exclusión va en el MEDIO de la lista, no al final -- si el bucle
    # usara `break` en vez de `continue` al toparse con una exclusión
    # (mutation testing, T026), rec2 nunca se procesaría y el pool
    # quedaría incompleto sin que ningún test lo notara.
    ref1 = NotaReferencia(tono_midi=60.0, inicio_s=0.0, fin_s=0.5)
    est1 = NotaEstimada(tono_midi=60.0, inicio_s=0.01, fin_s=0.5)
    ref2 = NotaReferencia(tono_midi=64.0, inicio_s=5.0, fin_s=5.5)
    est2 = NotaEstimada(tono_midi=64.0, inicio_s=5.01, fin_s=5.5)
    resultados = [
        ResultadoDeteccionGrabacion(
            grabacion_id="rec1", notas_referencia=[ref1], notas_estimadas=[est1], exclusion=None
        ),
        ResultadoDeteccionGrabacion(
            grabacion_id="rec_excluida",
            notas_referencia=None,
            notas_estimadas=None,
            exclusion=ExclusionDeteccion("rec_excluida", "fallo simulado"),
        ),
        ResultadoDeteccionGrabacion(
            grabacion_id="rec2", notas_referencia=[ref2], notas_estimadas=[est2], exclusion=None
        ),
    ]

    global_, _mono, _poli = agregar_conjunto(resultados)

    assert global_.num_notas_referencia == 2
    assert global_.num_notas_estimadas == 2
    assert global_.precision == 1.0
    assert global_.exhaustividad == 1.0


def test_agregar_conjunto_poolea_en_vez_de_promediar_por_grabacion() -> None:
    # rec1: 1 referencia, 1 estimada correcta -- precisión propia = 1.0.
    ref1 = NotaReferencia(tono_midi=60.0, inicio_s=0.0, fin_s=0.5)
    est1 = NotaEstimada(tono_midi=60.0, inicio_s=0.01, fin_s=0.5)

    # rec2: 3 referencias monofónicas bien separadas, 3 estimadas
    # correctas + 3 estimadas adicionales sin ninguna referencia cerca --
    # precisión propia = 3/6 = 0.5.
    ref2 = [
        NotaReferencia(tono_midi=60.0 + i, inicio_s=float(10 * i), fin_s=10 * i + 0.5)
        for i in range(3)
    ]
    est2_correctas = [
        NotaEstimada(tono_midi=60.0 + i, inicio_s=10 * i + 0.01, fin_s=10 * i + 0.5)
        for i in range(3)
    ]
    est2_sin_pareja = [
        NotaEstimada(tono_midi=90.0 + i, inicio_s=1000.0 + i, fin_s=1000.0 + i + 0.5)
        for i in range(3)
    ]
    est2 = est2_correctas + est2_sin_pareja

    resultados = [
        ResultadoDeteccionGrabacion(
            grabacion_id="rec1", notas_referencia=[ref1], notas_estimadas=[est1], exclusion=None
        ),
        ResultadoDeteccionGrabacion(
            grabacion_id="rec2", notas_referencia=ref2, notas_estimadas=est2, exclusion=None
        ),
        ResultadoDeteccionGrabacion(
            grabacion_id="rec3_excluida",
            notas_referencia=None,
            notas_estimadas=None,
            exclusion=ExclusionDeteccion("rec3_excluida", "fallo simulado"),
        ),
    ]

    global_, _mono, _poli = agregar_conjunto(resultados)

    # Pool: 4 referencias (1+3), 7 estimadas (1+6), 4 aciertos (1+3).
    assert global_.num_notas_referencia == 4
    assert global_.num_notas_estimadas == 7
    assert global_.precision == 4 / 7
    assert global_.exhaustividad == 1.0

    # El promedio de las precisiones POR grabación (1.0 y 0.5 -> 0.75) es
    # observablemente distinto del resultado pooleado (4/7 ≈ 0.571) --
    # fija que se pooleó, no se promedió (postcondición 5).
    precision_rec1 = evaluar_grabacion([ref1], [est1])[0].precision
    precision_rec2 = evaluar_grabacion(ref2, est2)[0].precision
    assert precision_rec1 is not None and precision_rec2 is not None
    promedio_por_grabacion = (precision_rec1 + precision_rec2) / 2
    assert global_.precision != promedio_por_grabacion


def test_agregar_conjunto_todas_monofonicas_da_polifonico_agregado_none() -> None:
    ref1 = NotaReferencia(tono_midi=60.0, inicio_s=0.0, fin_s=0.5)
    ref2 = NotaReferencia(tono_midi=62.0, inicio_s=10.0, fin_s=10.5)
    resultados = [
        ResultadoDeteccionGrabacion(
            grabacion_id="rec1",
            notas_referencia=[ref1],
            notas_estimadas=[NotaEstimada(tono_midi=60.0, inicio_s=0.01, fin_s=0.5)],
            exclusion=None,
        ),
        ResultadoDeteccionGrabacion(
            grabacion_id="rec2",
            notas_referencia=[ref2],
            notas_estimadas=[NotaEstimada(tono_midi=62.0, inicio_s=10.01, fin_s=10.5)],
            exclusion=None,
        ),
    ]

    _global, _mono, poli = agregar_conjunto(resultados)

    assert poli == ResultadoSubconjunto(
        precision=None,
        exhaustividad=None,
        balance_f1=None,
        num_notas_referencia=0,
        num_notas_estimadas=0,
        verdaderos_positivos=0,
    )


def test_agregar_conjunto_combina_notas_polifonicas_de_varias_grabaciones() -> None:
    # Dos grabaciones, cada una con su propio acorde de 2 notas --
    # el pool polifónico debe combinar las CUATRO referencias, no
    # quedarse con las de una sola grabación.
    resultados = [
        ResultadoDeteccionGrabacion(
            grabacion_id="rec1",
            notas_referencia=[
                NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=2.0),
                NotaReferencia(tono_midi=64.0, inicio_s=1.0, fin_s=2.0),
            ],
            notas_estimadas=[
                NotaEstimada(tono_midi=60.0, inicio_s=1.01, fin_s=2.0),
                NotaEstimada(tono_midi=64.0, inicio_s=1.01, fin_s=2.0),
            ],
            exclusion=None,
        ),
        ResultadoDeteccionGrabacion(
            grabacion_id="rec2",
            notas_referencia=[
                NotaReferencia(tono_midi=67.0, inicio_s=1.0, fin_s=2.0),
                NotaReferencia(tono_midi=71.0, inicio_s=1.0, fin_s=2.0),
            ],
            notas_estimadas=[
                NotaEstimada(tono_midi=67.0, inicio_s=1.01, fin_s=2.0),
                NotaEstimada(tono_midi=71.0, inicio_s=1.01, fin_s=2.0),
            ],
            exclusion=None,
        ),
    ]

    _global, _mono, poli = agregar_conjunto(resultados)

    assert poli.num_notas_referencia == 4
    assert poli.num_notas_estimadas == 4
    assert poli.precision == 1.0
    assert poli.exhaustividad == 1.0
