# Contrato: `compuerta`

Librería + CLI. El contrato es la firma pública de `medicion.compuerta`:
`evaluar_artefacto` (juicio puro), `leer_artefacto` (lectura de disco) y
`main` (CLI). `main` es una capa de invocación delgada: resuelve `--modo`
a una ruta de archivo, delega en `leer_artefacto` y en `evaluar_artefacto`,
y traduce el resultado a un código de salida.

## `evaluar_artefacto`

```python
def evaluar_artefacto(datos: dict[str, Any]) -> Veredicto:
    ...
```

Módulo: `medicion.compuerta`. Función pura: no toca disco, no importa
`separacion`/`analytics`/`ingestion`/`medicion.orquestador` (research.md
#1). Recibe el `dict` ya parseado (`json.load` corrió antes, fuera de
esta función).

### Precondiciones

`datos` es el resultado de deserializar con JSON un artefacto producido
por `medicion.orquestador.artefacto_a_dict` (Feature 004) -- o cualquier
`dict` que comparta esa forma en las claves que esta función lee
(data-model.md de esta feature).

### Postcondiciones

1. **Artefacto incompleto o irreconocible (FR-005/FR-006).** Si `datos`
   no tiene la clave `reportes`, o algún elemento de `reportes` no tiene
   `emparejadas`/`sin_pareja` con la forma esperada, levanta
   `ArtefactoInvalidoError` con un mensaje que identifica la clave
   faltante o mal formada. Nunca calcula un veredicto parcial.
2. **Sin evidencia suficiente (FR-006).** Si, tras recorrer todos los
   `reportes`, el pool de valores `si_sdr` de `emparejadas` queda vacío
   (incluye tanto `reportes == []` como el caso donde todas las
   referencias de todos los temas están en `sin_pareja`), levanta
   `ArtefactoInvalidoError` con motivo "sin evidencia suficiente para
   juzgar". Nunca invoca `statistics.median` sobre una lista vacía.
3. **Presupuesto aplicado (FR-002, FR-003).** En cualquier otro caso,
   calcula `mediana_emparejadas = statistics.median(pool)` sobre el pool
   de `si_sdr` de todas las `emparejadas` de todos los `reportes`
   (research.md #3), compara contra la constante `PRESUPUESTO_SI_SDR_DB
   = -8.0` (Principio VII de la constitución, v1.5.0), y devuelve un
   `Veredicto` con `aprobado = mediana_emparejadas >= PRESUPUESTO_SI_SDR_DB`
   -- un empate exacto en el presupuesto es aprobación (spec.md, User
   Story 1, escenario 3).
4. **Fracción sin pareja siempre presente (FR-003).** `Veredicto` incluye
   siempre `fraccion_sin_pareja`, `total_emparejadas` y `total_sin_pareja`
   -- nunca solo la mediana. `fraccion_sin_pareja = total_sin_pareja /
   (total_emparejadas + total_sin_pareja)` (research.md #4, denominador
   restringido a `reportes`, nunca a `exclusiones`).
5. **Contexto sin comparación (FR-009).** `Veredicto` incluye
   `modelo_nombre`/`modelo_variante`/`modelo_firma` (de `datos["modelo"]`),
   `modo` y `semilla` tal cual aparecen en `datos`, sin comparar ninguno
   contra un valor esperado ni afectar `aprobado` (research.md #6).

## `leer_artefacto`

```python
def leer_artefacto(ruta: Path) -> dict[str, Any]:
    ...
```

Módulo: `medicion.compuerta`. Único punto de esta feature que toca disco
antes de `evaluar_artefacto` -- añadido al contrato tras el hallazgo F1 de
`/speckit-analyze` (las tareas ya lo usaban como si tuviera contrato
documentado; ahora lo tiene). Junto con `evaluar_artefacto`, cierra el
círculo completo de FR-004/FR-005 bajo una única excepción (`main` solo
necesita atrapar `ArtefactoInvalidoError`, nunca `FileNotFoundError` ni
`json.JSONDecodeError` directamente).

### Postcondiciones

1. **Ruta ausente (FR-004).** Si `ruta` no existe, atrapa
   `FileNotFoundError` y levanta `ArtefactoInvalidoError` con un mensaje
   que identifica la ruta ausente.
2. **Contenido no interpretable (FR-005).** Si el contenido de `ruta` no
   es JSON válido, atrapa `json.JSONDecodeError` y levanta
   `ArtefactoInvalidoError` con un mensaje que identifica el problema de
   formato (nunca el mismo mensaje que el caso anterior -- cada motivo de
   rechazo por evidencia es distinguible, mismo criterio que
   `evaluar_artefacto`).
3. **Éxito.** En cualquier otro caso, devuelve el resultado de
   `json.load` tal cual -- no valida la forma del artefacto (eso es
   responsabilidad exclusiva de `evaluar_artefacto`, postcondiciones 1/2
   de abajo).

## `main`

```python
def main(argv: list[str] | None = None) -> int:
    ...
```

Módulo: `medicion.compuerta`. Único punto que invoca `sys.exit`.

### Postcondiciones

1. **Selección de artefacto (FR-008).** `--modo {submuestra_hito1,conjunto_completo}`,
   sin `default` -- omitirlo o pasar un valor fuera de las dos opciones es
   un error de `argparse` (`SystemExit`, código distinto de 0) antes de
   intentar leer ningún archivo. Se resuelve a `mediciones/<modo>.json`
   (misma convención de nombres que `medicion.cli`).
2. **Ruta ausente (FR-004).** Si `leer_artefacto` levanta
   `ArtefactoInvalidoError` por ruta ausente, imprime su mensaje a
   `stderr` y devuelve `2` -- nunca `0`.
3. **Artefacto inválido (FR-005/FR-006).** Si `leer_artefacto` o
   `evaluar_artefacto` levantan `ArtefactoInvalidoError` por cualquier
   otro motivo (contenido no interpretable, forma irreconocible, o sin
   evidencia suficiente), imprime el mensaje de la excepción a `stderr` y
   devuelve `2` -- la misma rama de `main` maneja las dos funciones, sin
   distinguir de cuál vino la excepción.
4. **Veredicto (FR-002, FR-003, FR-007, FR-009).** En cualquier otro
   caso, imprime el veredicto completo (aprobado/rechazado, mediana de
   emparejadas, presupuesto, fracción sin pareja, modelo/modo/semilla) a
   `stdout`, y devuelve `0` si `aprobado`, `1` si no -- nunca ejecuta
   `evaluar_artefacto` dos veces ni recalcula nada fuera de esa función.
5. **Nunca modifica el presupuesto (FR-010).** `PRESUPUESTO_SI_SDR_DB` no
   es un argumento de `main` ni tiene ninguna forma de sobrescribirse
   desde la línea de comandos.

### Códigos de salida

| Código | Significado |
|---|---|
| `0` | Aprobado: `mediana_emparejadas >= PRESUPUESTO_SI_SDR_DB` |
| `1` | Rechazado por presupuesto: artefacto válido, mediana por debajo |
| `2` | Rechazado por evidencia: artefacto ausente, ilegible, o sin evidencia suficiente (FR-004/005/006) |

`0` es la única salida de aprobación; `1` y `2` son ambos "no aprobado"
para cualquier consumidor que solo mire "cero o no cero" (FR-007), y
distinguibles entre sí para quien quiera diferenciar programáticamente
un problema de calidad de un problema de evidencia.
