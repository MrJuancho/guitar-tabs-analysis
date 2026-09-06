# Quickstart: Medición de la línea base

Valida `medicion.orquestador` (ver [contracts/medicion.md](./contracts/medicion.md))
contra el spec. Tres secciones, como en la Feature 003: lo que corre
siempre y rápido, el único test que toca el modelo real, y la ejecución
manual real (la que de verdad mide el hito 1 — nunca un test de pytest).

## Lo que corre en `just gauntlet` (rápido, sin `torch` cargado)

```bash
uv sync
just gauntlet
```

Todo esto usa `SeparadorFalso` (fixture de la Feature 003) y
`construir_tema_sintetico` (fixture de la Feature 001) sobre `tmp_path`,
en milisegundos, sin red:

- Un dataset sintético con temas en `validation/` y `train/` (varios,
  con distinto número de guitarras) → `construir_lista_temas("submuestra_hito1", ...)`
  con un `tamano_submuestra` pequeño resuelve siempre a los mismos
  identificadores dada la misma semilla (contracts/medicion.md,
  `construir_lista_temas` postcondición 1; spec.md US1 AS1/AS4).
- El mismo dataset con `construir_lista_temas("conjunto_completo", ...)`
  → incluye todos los temas de `train`+`validation`, nunca los que el
  fixture coloque bajo `test/`u `omitted/` aunque existan en el mismo
  `tmp_path` (postcondición 2; spec.md US3 AS1, FR-014).
- Un tema cuyo `SeparadorFalso` levanta una excepción arbitraria al
  separar → `ResultadoProcesamientoTema.exclusion.motivo ==
  "fallo_procesamiento"`, la corrida sigue con el resto de los temas
  (spec.md Edge Cases; FR-006).
- Un tema construido sin ninguna pista de guitarra (`stems=()`) →
  `exclusion.motivo == "sin_guitarra_referencia"`, sin llamar al
  `SeparadorFalso` para ese tema (contracts/medicion.md, `procesar_tema`
  postcondición 2).
- Una corrida sobre un `tmp_path` de progreso vacío, interrumpida a
  mano tras el tema 2 de 5 (deteniendo el bucle de prueba, no matando el
  proceso real), reinvocada con el mismo `directorio_trabajo` → los
  primeros 2 temas no vuelven a invocar el `SeparadorFalso` (verificable
  contando invocaciones, mismo patrón que Feature 003 usa para verificar
  "sin reintento"), y el `ArtefactoMedicion` final coincide campo a
  campo con el de una corrida sin interrupción sobre el mismo conjunto
  (US2 AS1/AS3; FR-008, FR-009).
- Un tema que falló y quedó persistido como `fallo_procesamiento`, tras
  reinvocar la corrida → sigue excluido con el mismo motivo, el
  `SeparadorFalso` no se vuelve a invocar para ese tema (US2 AS2;
  aclaración de `/speckit-clarify`).
- Un `manifiesto.json` ya persistido con una `firma_modelo` distinta a la
  del `Separador` inyectado en la reinvocación → `ModeloCambiadoError`
  con ambas firmas en el mensaje, sin procesar ningún tema (US2 AS5;
  FR-008a).
- `mediciones/<modo>.json` nunca contiene un umbral de aprobación ni un
  veredicto de pase/falla (FR-012; SC-008).

## Lo que corre con el modelo real (lento, red la primera vez)

Un único test nuevo, marcado `@pytest.mark.modelo_real`
(`tests/integration/test_medicion_modelo_real_integracion.py`), se salta
automáticamente si no hay red o si la carga del modelo falla (mismo
mecanismo que la Feature 003 ya estableció) — nunca bloquea `just
gauntlet`. Para correrlo explícitamente:

```bash
uv run pytest -m modelo_real -v
```

Qué valida: `procesar_tema` de punta a punta con `DemucsSeparador` real
sobre un tema sintético corto (1-2s, no un tema completo de Slakh2100) —
produce un `ResultadoProcesamientoTema` con `reporte` (o con `exclusion`
si el clip no tiene nada reconocible como guitarra) sin lanzar ninguna
excepción no controlada.

## Ejecución manual real — la que de verdad mide el hito 1

**No es un test.** Requiere el dataset Slakh2100 real en disco (fuera del
repositorio, Principio IV) y tarda del orden de minutos u horas — por
diseño, fuera del ciclo de test-y-verificación (spec.md, "TESTS Y
COSTO").

Submuestra del hito 1 (40 temas, ~36 min, research.md #9 de la Feature
003):

```bash
uv run python -m guitar_tabs_analysis.medicion.cli \
    --modo submuestra_hito1 \
    --root-dir /ruta/al/slakh2100_flac_redux
```

Conjunto evaluable completo de esta feature (`train`+`validation`, 1559
temas, ~23.1 h — spec.md#Assumptions, research.md #9 de la Feature 003):

```bash
uv run python -m guitar_tabs_analysis.medicion.cli \
    --modo conjunto_completo \
    --root-dir /ruta/al/slakh2100_flac_redux
```

Interrumpir cualquiera de las dos (`Ctrl+C`, cierre de sesión) y volver a
correr el mismo comando reanuda desde el primer tema sin progreso
persistido (FR-008) — el progreso vive en
`data/silver/mediciones/<modo>/`, no en memoria.

Resultado esperado: `mediciones/submuestra_hito1.json` (o
`mediciones/conjunto_completo.json`) — el `ArtefactoMedicion` completo
(data-model.md), listo para comentarlo en `/speckit-constitution` y
cerrar el `ABIERTO` del presupuesto numérico del Principio VII con la
cifra real.

## Verificación rápida del artefacto (sin volver a correr nada)

```bash
uv run python -c "
import json
artefacto = json.load(open('mediciones/submuestra_hito1.json'))
print('Modelo:', artefacto['modelo']['nombre'], artefacto['modelo']['firma'])
print('Modo:', artefacto['modo'], '| Semilla:', artefacto['semilla'])
print('Temas medidos:', len(artefacto['temas']))
print('Mediana agregada:', artefacto['mediana'])
print('Exclusiones:', len(artefacto['exclusiones']))
print('Distribución de referencias por tema:', artefacto['distribucion_referencias_por_tema'])
"
```

Confirma SC-007: todo lo necesario para interpretar la cifra está en el
propio archivo, sin acceso a la corrida original ni a los datos crudos.
