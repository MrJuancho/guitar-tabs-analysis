# Research: Medición de la línea base

**Input**: [spec.md](./spec.md) | **Output**: decisiones que resuelven cada
`NEEDS CLARIFICATION` de `plan.md` antes de Phase 1.

## 1. Agregación incremental por tema, no `agregar_conjunto` en bloque

**Decisión**: `medicion.orquestador` llama a `emparejar_tema(tema_id,
referencias, estimaciones)` (Feature 002) directamente, una vez por tema,
inmediatamente después de `separar_guitarra`, y persiste el `ReporteTema`
resultante antes de continuar. **No** acumula una `list[EntradaConjunto]`
en memoria para llamar a `agregar_conjunto()` al final.

**Rationale**: `agregar_conjunto()` es, por diseño (FR-007 en adelante de
la Feature 002), una función de **bloque**: recibe la lista completa de
`EntradaConjunto` — referencias y estimaciones ya en memoria — y
recalcula todo desde ahí. Eso es exactamente lo que la Restricción de
Memoria de esta feature (spec.md) prohíbe: retener el audio (o incluso
solo las referencias/estimaciones ya separadas) de más de un tema a la
vez. FR-005 y FR-007 de esta feature exigen soltar el audio de un tema
tan pronto como se calculó su reporte, y persistir ese reporte de
inmediato (no solo al final) — ninguna de las dos cosas es posible si la
agregación final necesita la lista cruda de entrada completa.

**Alternatives considered**:
- Usar `agregar_conjunto()` tal cual, manteniendo todas las
  `EntradaConjunto` en memoria hasta el final de la corrida. Descartada:
  viola FR-005 directamente (1559 temas × ~40 MB en el peor caso de 6
  guitarras excede con creces cualquier margen razonable), y no permite
  persistencia incremental por tema (FR-007) porque no hay nada que
  persistir hasta que la corrida completa termina.
- Reescribir `agregar_conjunto()` para que acepte un generador en vez de
  una lista. Descartada por ahora: cambiaría el contrato público de una
  feature ya cerrada (002) sin necesidad — el mismo resultado se logra
  extrayendo solo la aritmética final que si necesita reutilizarse (ver
  #2), sin tocar la firma de `agregar_conjunto`.

## 2. Dos funciones extraídas de `agregar_conjunto` para no duplicar la mediana

**Decisión**: Se extraen de `metrica_separacion.agregar_conjunto` dos
funciones públicas nuevas, sin cambiar su comportamiento observable
existente (mismos tests de la Feature 002 siguen en verde sin
modificarlos):

```python
def calcular_mediana_agregada(reportes: list[ReporteTema]) -> float | None: ...
def calcular_distribucion_referencias(reportes: list[ReporteTema]) -> dict[int, int]: ...
```

`agregar_conjunto()` pasa a **llamarlas** internamente en vez de repetir
su lógica inline; su firma y comportamiento externo no cambian. Esta
feature (`medicion.orquestador`) las importa y las llama sobre su propia
`list[ReporteTema]` (los reportes que sí se completaron, persistidos uno
a uno — ver #1) para producir la mediana y la distribución del artefacto
final, sin reimplementar la aritmética de la mediana ni el criterio de
ponderación (spec.md#Assumptions de la Feature 002, "Ponderación de la
mediana agregada").

**Rationale**: La mediana y la distribución son puras funciones de
`list[ReporteTema]` — no necesitan las referencias/estimaciones crudas,
solo el resultado ya calculado por tema. Extraerlas evita que esta
feature reimplemente la misma matemática (pool plano de valores por
referencia, `-inf` para sin pareja, el caso NaN de la mediana entre
`+inf`/`-inf`) con el riesgo de que las dos implementaciones diverjan
silenciosamente con el tiempo.

**Alternatives considered**:
- Duplicar la lógica de la mediana dentro de `medicion.orquestador`.
  Descartada: exactamente el vicio que este proyecto evita en otros
  lados (una sola fuente de verdad para SI-SDR/mediana); dos
  implementaciones de la misma fórmula divergen tarde o temprano.
- Exponer `agregar_conjunto` para que acepte también
  `list[ReporteTema]` ya calculados como entrada alternativa (sobrecarga
  de firma). Descartada por más compleja que dos funciones pequeñas y
  con un solo propósito cada una.

## 3. Identificador de tema calificado por split

**Decisión**: El identificador de tema que usa esta feature en todas
partes (lista de temas de una corrida, nombre de archivo de progreso,
exclusiones, artefacto final) es `"<split>/<tema_id>"` (p. ej.
`"validation/Track00234"`), pasado **tal cual** como primer argumento de
`leer_tema(tema_id, root_dir)` (Feature 001), con `root_dir` fijo en la
raíz del dataset completo (el directorio que contiene `train/`,
`validation/`, `test/`, `omitted/`).

**Rationale**: Verificado, no asumido — `pathlib.Path` resuelve un
operando con `/` embebido igual que varios segmentos:
`Path("/raiz") / "validation/Track00001"` produce
`Path("/raiz/validation/Track00001")` (confirmado en esta sesión con
`Path.parts`). Esto permite usar `leer_tema` de la Feature 001 **sin
ningún cambio**, y da un identificador único incluso si `train` y
`validation` reutilizaran el mismo número de track (no verificado que
ocurra, pero el prefijo lo hace irrelevante). El modo "conjunto evaluable
completo" necesita distinguir dos splits a la vez; el modo "submuestra
del hito 1" opera solo sobre `validation`, pero usa el mismo formato de
identificador por consistencia (un solo formato en todo el módulo, no
uno por modo).

**Alternatives considered**:
- Pasar `root_dir` distinto por split (`root_dir/validation`,
  `root_dir/train`) y un `tema_id` sin prefijo. Descartada: obliga a
  cargar dos `root_dir` distintos según de qué lista viene cada tema, y
  pierde la unicidad del identificador si algún día train/validation
  comparten numeración — el prefijo de split la resuelve gratis.

## 4. Dos ubicaciones de almacenamiento con propósitos distintos

**Decisión**:
- **Progreso persistido** (efímero, regenerable corriendo de nuevo, no
  se versiona): `data/silver/mediciones/<modo>/manifiesto.json` +
  `data/silver/mediciones/<modo>/temas/<tema_id_saneado>.json` (uno por
  tema — éxito o exclusión). Ya cubierto por la regla existente
  `data/silver/*` de `.gitignore` — **sin cambios** ahí.
- **Artefacto final** (pequeño, versionado, FR-011):
  `mediciones/<modo>.json` (p. ej. `mediciones/submuestra_hito1.json`),
  un directorio **nuevo** de nivel superior, trackeado por git.

**Rationale**: `data/gold`/`data/silver` ya existen en el esqueleto del
proyecto como "artefactos de datos generados por el pipeline -- no son
fuente" (comentario real de `.gitignore`), y encajan exactamente con el
progreso persistido: se regenera corriendo la corrida de nuevo, no hace
falta commitearlo, y puede crecer a 1559 archivos pequeños sin ensuciar
el repositorio. El artefacto final es lo opuesto — es evidencia que se
quiere comparar entre corridas sin volver a ejecutar nada (ENTREGABLE de
spec.md) — necesita vivir en un directorio trackeado. Se eligió un
directorio nuevo de nivel superior (`mediciones/`) en vez de anidarlo
bajo `specs/004-medicion-linea-base/` para que la ruta no quede acoplada
al nombre de una carpeta de Spec Kit que es, por diseño, específica de
esta sesión de planificación — el artefacto es evidencia del proyecto,
no de esta feature en particular, igual que `docs/ATRIBUCIONES.md` (un
directorio nuevo de nivel superior) fue la elección de la Feature 003
para su propio artefacto nuevo.

**Alternatives considered**:
- Un único archivo por corrida (sin persistencia incremental por tema),
  reescrito completo tras cada tema. Descartada: una escritura completa
  de un archivo grande en cada iteración es más trabajo que escribir un
  archivo pequeño nuevo, y una interrupción a mitad de esa reescritura
  arriesga corromper **todo** el progreso acumulado, no solo el tema en
  curso (ver #5).
- `mediciones/` bajo `data/gold/`. Descartada: `data/gold/*` está
  completamente ignorado en `.gitignore` salvo `.gitkeep` — habría que
  añadir una excepción ahí, mientras que un directorio nuevo de nivel
  superior no toca ninguna regla existente.

## 5. Escritura atómica por tema

**Decisión**: Cada archivo de progreso por tema
(`data/silver/mediciones/<modo>/temas/<id>.json`) se escribe primero a un
archivo temporal en el mismo directorio y se renombra con `os.replace()`
al nombre final, nunca con una escritura directa al nombre final.

**Rationale**: `os.replace()` es atómico en el mismo sistema de archivos
POSIX (WSL/Ubuntu, Target Platform de esta feature) — o el archivo final
queda completo y válido, o no se toca en absoluto; no existe un estado
intermedio observable donde el archivo final exista pero a medio
escribir. Esto es lo que hace verdadera la garantía de FR-007 ("una
interrupción después del tema K deja disponibles de forma durable los
reportes... de los temas 1 a K"): sin esto, una interrupción exactamente
durante la escritura del reporte del tema K podría dejar un archivo
corrupto que el mecanismo de detección de FR-008 no sabría distinguir de
uno válido.

**Alternatives considered**:
- Escribir directo al nombre final con `open(..., "w")`. Descartada: una
  interrupción a mitad de esa escritura dejaría un JSON truncado e
  inválido con el nombre "final", que FR-008 leería como si el tema ya
  estuviera medido, o fallaría al parsearlo de forma no distinguible de
  un error real de datos.

## 6. `medicion` fuera del contrato de layers de import-linter

**Decisión**: `pyproject.toml::[tool.importlinter]` no gana una nueva
capa `"guitar_tabs_analysis.medicion"` en la lista `layers` del contrato
existente. El módulo se deja fuera a propósito, documentado como
excepción — edición concreta a hacer en `/speckit-tasks`: ningún cambio
al contrato `type = "layers"` ya existente
(`separacion` → `analytics` → `ingestion`), y opcionalmente un comentario
en `pyproject.toml` señalando que `medicion` es el orquestador excluido.

**Rationale**: AGENTS.md ya anticipa exactamente este caso ("Si el
proyecto tiene un orquestador... no lo agregues a la lista `layers`...
déjalo fuera a propósito, documentado como excepción"). `medicion`
necesita importar de las tres capas a la vez (`ingestion.leer_tema`,
`separacion.separar_guitarra`, `analytics.emparejar_tema`) — agregarlo a
la lista como una cuarta capa por encima de `separacion` no cambiaría
nada en la práctica (ya podría importar de las tres) pero afirmaría
falsamente que `medicion` participa en un orden jerárquico de capas,
cuando en realidad es el punto donde las tres se coordinan.

**Alternatives considered**:
- Agregarlo como cuarta capa (`medicion` → `separacion` → `analytics` →
  `ingestion`). Descartada: técnicamente pasaría el contrato (import en
  la dirección permitida), pero es la señal exacta que AGENTS.md pide
  evitar — "una segunda razón para cruzar capas libremente es señal de
  que esa lógica debería vivir en el orquestador, no de que el contrato
  necesita otra excepción". Tratarlo como una capa más debilitaría el
  significado del contrato para las tres capas reales.

## 7. "Conjunto evaluable completo" excluye `test`/`omitted` por construcción

**Decisión** (ya fijada en spec.md#Assumptions, repetida aquí con el
mecanismo técnico): `construir_lista_temas("conjunto_completo", root_dir)`
lista únicamente `os.listdir(root_dir / "train")` y
`os.listdir(root_dir / "validation")`. Nunca abre ni enumera
`root_dir / "test"` ni `root_dir / "omitted"`.

**Rationale**: FR-014 ("MUST NOT leer, procesar, ni incluir... ningún
tema del split `test`") se satisface por construcción — no hay ninguna
rama de código que pueda alcanzar `test/`, en vez de depender de un
chequeo en tiempo de ejecución que podría tener un caso no cubierto. Esto
también hace innecesario un campo `es_directorio_omitido` (Feature 002)
en esta feature: como `omitted/` nunca se lista, ningún tema de esta
feature podría tener ese motivo — ver data-model.md, `MotivoExclusionMedicion`
solo tiene dos valores, no los tres de `MotivoExclusion` de la Feature
002.

## 8. Verificación de dataset sintético con `metadata.yaml` real, no de memoria

**Decisión**: Los tests de esta feature construyen su dataset sintético
con `construir_tema_sintetico` (fixture de la Feature 001,
`tests/fixtures/slakh2100_fixture.py`) pasando un `tema_id` con prefijo
de split (p. ej. `tema_id="validation/Track00001"`) sobre el mismo
`tmp_path` para varios temas — sin modificar esa fixture.

**Rationale**: Verificado en esta sesión que `construir_tema_sintetico`
ya soporta esto sin cambios: internamente hace
`tema_dir = tmp_path / tema_id` seguido de `stems_dir.mkdir(parents=True)`,
que crea los directorios intermedios (`validation/`) igual que si
`tema_id` no tuviera `/`. No hace falta una fixture nueva de bajo nivel
para escribir `.flac`/`metadata.yaml` — solo una función pequeña en
`tests/fixtures/dataset_sintetico_fixture.py` que llama
`construir_tema_sintetico` varias veces sobre el mismo `tmp_path` para
poblar varios splits/temas de una vez (conveniencia de test, no una
reimplementación).

## 9. CLI: `argparse`, `--modo` sin default

**Decisión**: `medicion.cli.main()` usa `argparse` (stdlib) con
`--modo` como argumento **requerido**, `choices=["submuestra_hito1",
"conjunto_completo"]`, sin `default=`. `--root-dir` requerido también
(la raíz del dataset Slakh2100, fuera del repositorio — Principio IV).
Invocación: `uv run python -m guitar_tabs_analysis.medicion.cli --modo
submuestra_hito1 --root-dir /ruta/al/dataset`. Un recipe nuevo de `just`
(`just medir <modo> <root_dir>`) se agrega en `/speckit-tasks`, mismo
patrón que `just gates` ya usa para `quality.gates.main()`.

**Rationale**: `argparse` sin `default=` en un argumento `required=True`
hace que omitir `--modo` sea un error de parseo de línea de comandos
(`SystemExit` con mensaje claro de `argparse`), satisfaciendo FR-004 sin
lógica adicional que mantener — no hay una rama de código "modo por
defecto" que pueda existir para ejecutar por accidente. No se introduce
`click` ni otra dependencia nueva: `argparse` alcanza para dos flags
obligatorios y es lo que el resto del proyecto ya usa implícitamente
(`quality.gates.main()` no toma argumentos, pero tampoco necesita una
librería de terceros para lo que sí necesita esta feature).
