# Contrato: `medicion`

Librería + CLI. El contrato es la firma pública de `medicion.orquestador`
(sin CLI) y el comportamiento observable descrito en `spec.md`. `medicion.cli`
es una capa de invocación delgada sobre `ejecutar_corrida`, sin lógica
propia que probar por separado más allá del parseo de argumentos
(FR-004).

## `construir_lista_temas`

```python
def construir_lista_temas(
    modo: ModoEjecucion,
    root_dir: Path,
    *,
    tamano_submuestra: int = 40,
    semilla_submuestra: int = 20260904,
) -> list[str]:
    ...
```

Módulo: `medicion.orquestador`.

### Postcondiciones

1. **`modo="submuestra_hito1"` (FR-002).** Devuelve
   `[f"validation/{t}" for t in random.Random(semilla_submuestra).sample(sorted(os.listdir(root_dir / "validation")), tamano_submuestra)]`
   — reproducible sin estado externo: la misma `root_dir` produce siempre
   la misma lista.
2. **`modo="conjunto_completo"` (FR-003).** Devuelve la unión de
   `[f"train/{t}" for t in sorted(os.listdir(root_dir / "train"))]` y
   `[f"validation/{t}" for t in sorted(os.listdir(root_dir / "validation"))]`.
   **Nunca** enumera `root_dir / "test"` ni `root_dir / "omitted"`
   (FR-014, research.md #7) — no hay parámetro que pueda hacer que los
   liste.
3. Los parámetros `tamano_submuestra`/`semilla_submuestra` existen para
   que los tests puedan ejercitar la función con datasets sintéticos
   pequeños (research.md #8); una invocación real de "submuestra del
   hito 1" siempre usa los valores por defecto (40, `20260904`) — el CLI
   (FR-002) nunca los expone como flags.

## `procesar_tema`

```python
def procesar_tema(
    tema_id: str,
    root_dir: Path,
    separador: Separador,
) -> ResultadoProcesamientoTema:
    ...
```

Módulo: `medicion.orquestador`. No importa `torch`/`demucs` — recibe
`separador` ya construido (mismo patrón que `separar_guitarra` de la
Feature 003).

### Postcondiciones

1. **Lectura fallida (FR-006).** Si `leer_tema(tema_id, root_dir)` levanta
   `TemaNoExisteError`, `ArchivoAudioNoLegibleError` o
   `LongitudInconsistenteError` (Feature 001), el resultado es
   `ResultadoProcesamientoTema(tema_id, reporte=None, exclusion=ExclusionMedicion(tema_id, "fallo_procesamiento", str(causa)), transformaciones=[])`
   — nunca propaga la excepción original hacia quien llama.
2. **Sin guitarra de referencia.** Si `leer_tema` devuelve una colección
   vacía de guitarras, el resultado es
   `ResultadoProcesamientoTema(tema_id, reporte=None, exclusion=ExclusionMedicion(tema_id, "sin_guitarra_referencia", ""), transformaciones=[])`
   — nunca se llama a `separar_guitarra` para un tema sin ninguna
   referencia (no hay nada contra qué medir).
3. **Separación fallida (FR-006).** Si `leer_tema` tuvo éxito pero
   `separar_guitarra` levanta `SeparacionFallidaError` (Feature 003), el
   resultado es
   `ResultadoProcesamientoTema(tema_id, reporte=None, exclusion=ExclusionMedicion(tema_id, "fallo_procesamiento", str(causa)), transformaciones=[])`
   — mismo motivo que la postcondición 1, mensaje distinguible por su
   `detalle`.
4. **Camino feliz.** Si `leer_tema` y `separar_guitarra` tienen éxito, el
   resultado es
   `ResultadoProcesamientoTema(tema_id, reporte=emparejar_tema(tema_id, guitarras, estimaciones), exclusion=None, transformaciones=resultado_separacion.transformaciones)`
   (Feature 002 para `reporte`, Feature 003 para `transformaciones` —
   `resultado_separacion` es el `ResultadoSeparacionTema` que devolvió
   `separar_guitarra`) — sin importar si `estimaciones` quedó vacía
   (Feature 003, FR-009 de 003) o si algún emparejamiento resultó
   silencioso (Feature 002, FR-016 de 002): `emparejar_tema` ya sabe
   clasificar ambos casos dentro de `ReporteTema.sin_pareja`, y eso no
   afecta a `transformaciones` — son dos datos independientes del mismo
   `resultado_separacion` (FR-010, SC-007).
5. **Transformaciones vacías cuando no hubo separación.** Si el resultado
   tiene `exclusion` no `None` (postcondiciones 1-3), `transformaciones`
   es `[]` — ni `"sin_guitarra_referencia"` ni `"fallo_procesamiento"`
   llegan a invocar `separar_guitarra` con éxito, así que no existe
   ningún `ResultadoSeparacionTema` del cual tomarlas.
6. **Nunca ambos ni ninguno.** Exactamente uno de `reporte`/`exclusion`
   del resultado es `None` (data-model.md, invariante de
   `ResultadoProcesamientoTema`).
7. **No hay reintento.** `procesar_tema` intenta la lectura y la
   separación **una sola vez** — un fallo no dispara una segunda
   llamada. Mismo criterio que `SeparacionFallidaError` ya impone dentro
   de `separar_guitarra` (Feature 003, FR-014 de 003), extendido aquí a
   la lectura.

### Modos de fallo

`procesar_tema` en sí **no levanta ninguna excepción propia** — todo
fallo de tema se convierte en un `ExclusionMedicion` (postcondiciones
1-3). La única forma de que una excepción escape de esta función es un
error de programación no anticipado (p. ej. `root_dir` no existe en
absoluto) — no cubierto por un tipo de excepción propio de esta feature.

## `ejecutar_corrida`

```python
def ejecutar_corrida(
    modo: ModoEjecucion,
    root_dir: Path,
    separador: Separador,
    directorio_trabajo: Path,
) -> ArtefactoMedicion:
    ...
```

Módulo: `medicion.orquestador`. `directorio_trabajo` es la raíz de
`data/silver/mediciones/<modo>/` (research.md #4) — parametrizada (no
hardcodeada) para que los tests usen `tmp_path`.

### Precondiciones

- Si `directorio_trabajo` ya contiene un `manifiesto.json` de una corrida
  anterior de este `modo`, su `firma_modelo` **debe** coincidir con
  `separador.modelo_declarado.firma` — ver Modos de fallo.

### Postcondiciones

1. **Primera invocación (sin progreso previo).** Crea
   `manifiesto.json` con `ManifiestoCorrida(modo, semilla, firma_modelo,
   temas=construir_lista_temas(modo, root_dir))` (FR-001/FR-002/FR-003),
   y procesa cada tema de `temas` en orden, persistiendo el resultado de
   `procesar_tema` (FR-005/FR-007) inmediatamente después de calcularlo,
   antes de continuar con el siguiente — nunca mantiene el audio de dos
   temas en memoria a la vez.
2. **Reanudación con la misma firma de modelo (FR-008).** Si
   `manifiesto.json` ya existe y su `firma_modelo` coincide, reutiliza
   `ManifiestoCorrida.temas` tal como se persistió (no lo recalcula), y
   procesa únicamente los temas de esa lista que todavía no tienen un
   archivo de progreso en `temas/` — sin releer, resseparar ni
   recalcular métrica para ninguno de los que ya lo tienen, sea cual sea
   su resultado (`reporte` o `exclusion` — aclaración de
   `/speckit-clarify`, FR-008).
3. **Reanudación con firma de modelo distinta (FR-008a).** Si
   `manifiesto.json` ya existe y su `firma_modelo` **no** coincide con
   `separador.modelo_declarado.firma`, levanta `ModeloCambiadoError`
   antes de procesar ningún tema — nunca reanuda ni mezcla reportes de
   dos modelos distintos en el mismo `ArtefactoMedicion`.
4. **Fallo individual no aborta la corrida (FR-006).** Cuando
   `procesar_tema` devuelve una `exclusion`, `ejecutar_corrida` la
   persiste igual que un `reporte` exitoso (mismo mecanismo de
   progreso — ver postcondición 1) y continúa con el siguiente tema de
   la lista, sin propagar ninguna excepción por ese tema individual.
5. **Artefacto final solo al completar todos los temas (FR-010).** Una
   vez que todos los temas de `manifiesto.json.temas` tienen progreso
   persistido (en esta invocación o en una anterior), ensambla y
   **devuelve** el `ArtefactoMedicion` completo (data-model.md) en
   memoria — antes de ese punto, `ejecutar_corrida` no devuelve nada (la
   corrida sigue en progreso; volver a invocarla continúa donde quedó,
   postcondición 2). `transformaciones_por_tema` se arma recolectando
   `progreso.transformaciones` de cada `ResultadoProcesamientoTema` cuyo
   `reporte` no es `None`, indexado por `tema_id` — un tema excluido no
   aporta entrada (data-model.md). Escribir ese valor devuelto como
   `mediciones/<modo>.json` es responsabilidad de quien llama
   (`medicion.cli`, ver más abajo), no de `ejecutar_corrida` — mantiene
   esta función testeable enteramente contra `directorio_trabajo`
   (`tmp_path` en los tests) sin tocar ninguna ruta del repositorio.
6. **Equivalencia con/sin interrupción (FR-009).** El `ArtefactoMedicion`
   de una corrida completada en una sola invocación y el de una
   completada a través de dos o más (con la misma `root_dir`, `modo` y
   `separador`) son iguales campo a campo — mismos `reportes`,
   `exclusiones`, `transformaciones_por_tema`, `mediana`,
   `distribucion_referencias_por_tema`.

### Modos de fallo

| Excepción | Cuándo | Datos que lleva |
|---|---|---|
| `ModeloCambiadoError` | `manifiesto.json` existente con `firma_modelo` distinta a la del `separador` recibido (FR-008a) | `firma_esperada`, `firma_actual` |

Ningún fallo de tema individual (lectura, separación) llega hasta acá
como excepción — `procesar_tema` ya los convirtió en `ExclusionMedicion`
antes de que `ejecutar_corrida` los vea (contrato de `procesar_tema`
arriba).

## CLI: `medicion.cli.main`

Módulo: `medicion.cli`. Único módulo de esta capa que importa
`separacion.demucs_separador.DemucsSeparador` (construye el `Separador`
real una sola vez, antes del bucle — igual que cualquier llamador real
de `separar_guitarra`, Feature 003).

```
uv run python -m guitar_tabs_analysis.medicion.cli \
    --modo {submuestra_hito1,conjunto_completo} \
    --root-dir RUTA_AL_DATASET
```

### Postcondiciones

1. **Sin modo por defecto (FR-004).** `--modo` es un argumento
   `required=True` sin `default=` — omitirlo produce un error de
   `argparse` (`SystemExit`, código de salida distinto de 0) antes de
   construir ningún `Separador` ni tocar el disco.
2. Al terminar con éxito, escribe el `ArtefactoMedicion` resultante como
   JSON en `mediciones/<modo>.json` (research.md #4) y termina con
   código de salida `0`.
3. Si `ejecutar_corrida` levanta `ModeloCambiadoError`, el CLI la deja
   propagar como fallo visible (mensaje a `stderr`, código de salida
   distinto de 0) — nunca la silencia ni reanuda de todos modos.
