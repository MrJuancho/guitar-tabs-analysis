# Quickstart: Detección de notas sobre guitarra limpia

Valida `ingestion.guitarset`, `transcripcion`, `analytics.metrica_deteccion_notas`
y `deteccion.orquestador` (ver [contracts/deteccion.md](./contracts/deteccion.md))
contra `spec.md`. Dos secciones, mismo patrón que el hito 1: lo que corre
siempre y rápido, y el único camino que toca el modelo real.

## Lo que corre en `just gauntlet` (rápido, sin `basic_pitch` cargado)

```bash
uv sync
just gauntlet
```

Todo esto usa un `TranscriptorFalso` sintético (mismo patrón que
`SeparadorFalso` del hito 1) y notas de referencia construidas a mano,
en milisegundos, sin `basic_pitch`/`onnxruntime`/`mir_eval` cargando
ningún modelo real:

- Pares de notas dentro/fuera de tolerancia de tono, dentro/fuera de
  ventana de inicio, en el borde exacto de cada una, con duraciones
  distintas que no afectan el acierto (spec.md US1).
- Varias notas de referencia y estimadas sobre la misma grabación,
  emparejadas sin acreditar ninguna dos veces (US1 AS5).
- Notas de referencia superpuestas (acorde) y no superpuestas (nota
  suelta), clasificadas monofónico/polifónico solo a partir de la
  referencia (US3 AS2).
- Un conjunto con subconjunto monofónico o polifónico vacío, reportado
  explícitamente como sin datos (US3 AS3, FR-008).
- Una grabación cuyo `TranscriptorFalso` levanta una excepción
  arbitraria, registrada como exclusión, sin detener el resto de la
  corrida (spec.md US2 AS4, FR-012).

## Lo que corre con el modelo real (lento, sin red tras la primera vez)

Un único test marcado `@pytest.mark.modelo_real`, mismo mecanismo de
aviso visible que el hito 1 (`tests/conftest.py`) -- nunca corre como
parte de `just gauntlet`:

```bash
uv run pytest -m modelo_real -v
```

Qué valida: `BasicPitchTranscriptor.transcribir()` de punta a punta
sobre una grabación corta real de GuitarSet, produciendo una lista de
`NotaEstimada` (o vacía, si el clip no tiene nada que Basic Pitch
reconozca) sin lanzar ninguna excepción no controlada.

**Prerrequisito, fuera del repositorio (Principio IV):** GuitarSet no
viene con este repositorio -- se descarga aparte (por ejemplo, vía
`mirdata.initialize("guitarset").download()`) a una ruta local que el
test/CLI recibe como parámetro, igual que Slakh2100 en el hito 1.

## Ejecución manual real -- medir sobre GuitarSet completo

**No es un test.** Requiere GuitarSet real en disco y tarda del orden de
minutos (research.md #12: no estimado a priori, se mide en
`/speckit-implement`) -- fuera del ciclo de test-y-verificación.

```bash
uv run python -m guitar_tabs_analysis.deteccion.cli --root-dir /ruta/a/guitarset
```

(CLI exacto a definir en `/speckit-tasks` de esta feature -- este
comando es ilustrativo del patrón que seguirá, mismo espíritu que
`medicion.cli` del hito 1: sin valor por defecto, con salida de
progreso.)

Resultado esperado: un artefacto con la lista de grabaciones medidas,
las exclusiones con su motivo, y las tres cifras (global, monofónico,
polifónico) de precisión, exhaustividad y balance -- listo para
comentarlo en `/speckit-constitution` y fijar el presupuesto del
Principio VII con la cifra real (spec.md, "PRESUPUESTO").
