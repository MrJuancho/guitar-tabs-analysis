# Contrato: digitación con restricción de la mano

El contrato es la firma pública de un módulo extendido y dos módulos
nuevos, y el comportamiento observable descrito en `spec.md`.

## `ingestion.guitarset.leer_grabacion_con_posicion_real`

```python
def leer_grabacion_con_posicion_real(
    grabacion_id: str, root_dir: Path
) -> list[NotaConPosicionReal]:
    ...
```

Extensión de `ingestion/guitarset.py` (research.md #5) -- no un módulo
nuevo, no toca `leer_grabacion()` del hito 2 (que sigue usando
`notes_all`, sin cambios). No importa `transcripcion` ni `analytics`
(capa base, mismo lugar que `leer_grabacion`).

### Precondiciones

Mismas que `leer_grabacion` (contracts/deteccion.md, hito 2): `root_dir`
es la raíz de una distribución de GuitarSet ya presente en disco.

### Postcondiciones

1. **Éxito.** Si `grabacion_id` existe en el índice de `mirdata`, MUST
   devolver una lista de `NotaConPosicionReal` -- una por cada nota
   anotada en CUALQUIERA de las seis cuerdas (`track.notes`, research.md
   #5), con `cuerda_real` fijada a la clave del diccionario en la que
   apareció y `traste_real` derivado (`round(tono_midi -
   MIDI_CUERDA_ABIERTA[cuerda_real])`) -- nunca leído de un campo de
   traste directo, porque `mirdata`/GuitarSet no lo anota (verificado
   contra el código fuente real de `load_notes`, research.md #5). La
   lista MUST estar ordenada por `inicio_s` -- la fusión de las seis
   listas por cuerda no se asume ya ordenada, se ordena explícitamente.
2. **Grabación inexistente o índice corrupto.** MUST levantar
   `GrabacionNoExisteError` (el mismo tipo que `leer_grabacion`, no uno
   paralelo) -- nunca una excepción cruda de `mirdata` sin envolver.

## `analytics.metrica_digitacion`

```python
def generar_candidatas(
    tono_midi: float, modelo: ModeloCoste
) -> list[Posicion]:
    ...

def agrupar_en_instantes(
    notas: list[NotaEntrada], modelo: ModeloCoste
) -> list[Instante]:
    ...

def asignar_instante(
    instante: Instante, modelo: ModeloCoste
) -> list[PosicionAsignada] | InstanteExcluido:
    ...

def asignar_secuencia(
    notas: list[NotaEntrada], modelo: ModeloCoste
) -> Digitacion:
    ...

def evaluar_coincidencia(
    digitacion: Digitacion, notas_con_posicion_real: list[NotaConPosicionReal]
) -> ResultadoCoincidencia:
    ...

def agregar_conjunto(
    resultados: list[ResultadoDigitacionGrabacion]
) -> ResultadoCoincidencia:
    ...
```

Módulo nuevo: `analytics/metrica_digitacion.py`. Puede importar de
`ingestion` (para `NotaReferencia`/`NotaConPosicionReal`), nunca de
`digitacion` (capa productora) sin crear una dependencia circular --
mismo criterio de capas que `analytics.metrica_deteccion_notas` (hito
2, research.md #11 de esa feature). `ExclusionDigitacion`/
`ResultadoDigitacionGrabacion` se definen aquí, no en
`digitacion/orquestador.py`, por el mismo motivo exacto que
`ExclusionDeteccion`/`ResultadoDeteccionGrabacion` viven en
`analytics.metrica_deteccion_notas`: `agregar_conjunto` los necesita en
su propia firma pública.

### Postcondiciones

1. **`generar_candidatas` -- corrección por construcción (FR-001,
   FR-012).** MUST devolver toda posición `(cuerda, traste)` con
   `traste` en `[modelo.traste_minimo, modelo.traste_maximo]` tal que
   `|tono_midi - (modelo.midi_cuerda_abierta[cuerda] + traste)| ≤
   modelo.tolerancia_tono_cents / 100` (conversión de cents a
   semitonos) -- MUST NOT incluir ninguna posición fuera de esa
   tolerancia o ese rango. Puede devolver una lista vacía (tono
   inalcanzable incluso con tolerancia y rango completos) -- MUST NOT
   fallar en ese caso, es responsabilidad de quien la invoca decidir
   qué hacer con una lista vacía (postcondición 3).
2. **`agrupar_en_instantes` -- FR-006 de research.md.** MUST agrupar
   `notas` (ya ordenadas por `inicio_s`) de forma codiciosa SIN
   arrastre: una nota entra al grupo actual si su `inicio_s` está a lo
   sumo `modelo.ventana_instante_s` del `inicio_s` de la PRIMERA nota
   del grupo, nunca de la última agregada. MUST NOT usar solape de
   intervalo `[inicio_s, fin_s]` para esta agrupación (research.md #6:
   ese criterio corresponde a "clasificar_polifonia_en_instante" del
   hito 2, un concepto distinto -- qué suena al mismo tiempo
   acústicamente, no qué debe fretear la mano al mismo tiempo -- y
   produce polifonía por encima de 6 sobre datos reales, físicamente
   imposible).
3. **`asignar_instante` -- FR-002/FR-013.** Para cada nota del
   instante, MUST generar sus candidatas (postcondición 1). Si alguna
   nota tiene cero candidatas, o si NINGUNA asignación de una cuerda
   distinta a cada nota (nunca la misma cuerda dos veces en el mismo
   instante) mantiene `max(traste) - min(traste)` sobre las posiciones
   con `traste ≥ 1` (research.md #7: cuerdas al aire no cuentan para el
   estiramiento) dentro de `modelo.limite_estiramiento_trastes`, MUST
   devolver `InstanteExcluido` con motivo distinguible entre "más notas
   simultáneas que cuerdas disponibles" (si `len(instante.notas) > 6`)
   y "excede el límite de estiramiento" (en cualquier otro caso sin
   combinación válida) -- MUST NOT devolver una lista de posiciones que
   viole cualquiera de las dos condiciones.
4. **`asignar_secuencia` -- FR-005/FR-006, research.md #1.** MUST
   agrupar en instantes (postcondición 2), y MUST calcular la
   combinación de posiciones -- una por instante no excluido -- que
   minimiza la suma de coste de estiramiento de cada instante más el
   coste de desplazamiento y cruce de cuerdas entre cada par de
   instantes consecutivos NO EXCLUIDOS (un instante excluido no
   participa de ningún coste de transición; el `Δt` de la transición
   siguiente se calcula contra el último instante no excluido, nunca
   contra el excluido) usando programación dinámica sobre las
   candidatas de cada instante (research.md #1) -- MUST NOT calcular
   por fuerza bruta ni por una heurística sin verificar contra el
   óptimo. El caso base (primer instante no excluido de la secuencia)
   MUST tener coste de transición cero -- no hay instante anterior.
5. **`evaluar_coincidencia` -- FR-007.** MUST comparar, nota por nota,
   la `Posicion` de cada `PosicionAsignada` de `digitacion.posiciones`
   contra la `PosicionReal` derivada de la `NotaConPosicionReal`
   correspondiente (misma nota, identificada por `NotaEntrada`) --
   coincide si y solo si `cuerda` Y `traste` son iguales exactamente
   (Principio VIII: resultado discreto, igualdad exacta, nunca
   tolerancia numérica). Notas de instantes excluidos MUST NOT contar
   en el denominador -- no recibieron ninguna posición que comparar.
   MUST NOT derivar esta cifra del `coste_total` de la digitación
   (sería circular, FR-007) -- MUST leer exclusivamente
   `notas_con_posicion_real`, nunca el propio resultado de
   `asignar_secuencia`.
6. **`agregar_conjunto` -- mismo patrón que el hito 2, research.md #16
   de esa feature.** MUST sumar `num_notas_medidas`/
   `num_notas_coincidentes` de cada `ResultadoDigitacionGrabacion` no
   excluido y derivar `fraccion_coincidencia` de esa suma -- MUST NOT
   promediar las fracciones por grabación, MUST NOT poolear notas
   crudas de grabaciones distintas antes de medir (la programación
   dinámica de la postcondición 4 ya corrió una vez por grabación, esta
   función solo suma conteos ya resueltos).

## `digitacion.orquestador`

```python
def ejecutar_digitacion(
    grabaciones: list[str], root_dir: Path
) -> ArtefactoDigitacion:
    ...
```

Paquete nuevo: `digitacion/orquestador.py` -- excluido a propósito del
contrato `layers` de import-linter (research.md #11 del hito 2, mismo
criterio que `deteccion`/`medicion`): importa de `ingestion` y
`analytics` a la vez. **Reutiliza
`deteccion.orquestador.construir_lista_grabaciones` tal cual** para
cualquier necesidad de partición medibles/reservado -- MUST NOT definir
una segunda función de partición que pudiera divergir de la ya cerrada
(Principio VI).

### Postcondiciones

1. **Por grabación (mismo patrón que `ejecutar_deteccion`, hito 2).**
   Para cada `grabacion_id` de `grabaciones`, MUST leer sus notas
   (`ingestion.guitarset.leer_grabacion_con_posicion_real`); si esa
   lectura falla con `GrabacionNoExisteError`, MUST registrar la
   grabación como `ExclusionDigitacion` con el detalle del error y MUST
   continuar con la siguiente -- nunca abortar la corrida completa por
   un fallo individual. Si la lectura tiene éxito, MUST llamar
   `analytics.metrica_digitacion.asignar_secuencia` sobre las notas
   (proyectadas a `NotaEntrada`, sin la posición real) y
   `evaluar_coincidencia` sobre el resultado más las
   `NotaConPosicionReal` originales.
2. **Artefacto final (FR-016).** Al completar todas las grabaciones,
   MUST devolver un único `ArtefactoDigitacion` con el modelo de coste
   aplicado, la lista de grabaciones, las exclusiones de grabación con
   su motivo, los resultados crudos por grabación (incluidas las
   exclusiones de instante dentro de cada uno), y el resultado de
   coincidencia agregado con `analytics.metrica_digitacion.agregar_conjunto`
   sobre las grabaciones no excluidas.
3. **Sin umbral (FR-015).** MUST NOT comparar `fraccion_coincidencia`
   ni ninguna otra cifra contra ningún valor de aprobación -- termina
   en devolver el artefacto.
4. **Conjunto reservado (FR-008, Principio VI).** MUST NOT invocarse,
   en ningún punto del desarrollo del hito 3, con una lista de
   `grabaciones` que incluya alguna de las 72 reservadas -- esta función
   no lo verifica por sí misma (no es su responsabilidad decidir qué
   grabaciones recibe, mismo criterio que `ejecutar_deteccion` del hito
   2); es responsabilidad de quien construye la lista (la CLI, fuera de
   alcance de este plan hasta que `/speckit-tasks` la agregue) usar
   `construir_lista_grabaciones("medibles", ...)`, nunca `"reservado"`,
   durante el desarrollo.
