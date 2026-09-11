# Quickstart: Digitación con restricción de la mano

Valida `ingestion.guitarset` (extendido), `analytics.metrica_digitacion`
y `digitacion.orquestador` (ver [contracts/digitacion.md](./contracts/digitacion.md))
contra `spec.md`. Dos secciones: lo que corre siempre y rápido, y la
ejecución manual sobre GuitarSet real -- a diferencia del hito 2, no hay
ningún modelo externo ni subproceso que distinga un tercer camino
"modelo real": todo el algoritmo de esta feature es autocontenido
(research.md #1/#2), lo único que requiere datos reales es leer
GuitarSet, igual que ya era cierto para `ingestion.guitarset` en el
hito 2.

## Lo que corre en `just gauntlet` (rápido, sin GuitarSet real en disco)

```bash
uv sync
just gauntlet
```

Todo esto usa notas construidas a mano y el índice de `mirdata`
reemplazado por `monkeypatch` (mismo patrón que `tests/unit/test_guitarset.py`
del hito 2) -- ninguna descarga, ningún archivo de audio:

- Generación de candidatas: un tono exacto da al menos la posición
  entera esperada; un tono fraccionario dentro/fuera de la tolerancia
  declarada; el rango de trastes respetado en los bordes (spec.md US1).
- Un acorde alcanzable sin exceder el límite de estiramiento asigna
  cuerdas distintas a cada nota; un acorde que lo excede en toda
  combinación se excluye con motivo, nunca en silencio (US1 AS3, FR-013).
- Dos notas simultáneas con el mismo tono reciben cuerdas distintas
  (US1 AS4).
- Una secuencia sintética corta con óptimo calculable por fuerza bruta:
  la digitación producida coincide en coste total (US2 AS1, FR-006) --
  incluida al menos una secuencia donde el mismo desplazamiento en
  trastes cuesta más con menos tiempo disponible (US2 AS2, FR-004).
- Dos notas consecutivas en cuerdas opuestas del mástil (traste 1 de la
  sexta, luego traste 1 de la primera) con coste de cruce de cuerdas
  mayor a cero pese a desplazamiento cero (US2 AS3).
- El primer instante de una secuencia sin coste de transición (US2 AS4).
- Una grabación sintética con notas de referencia y posiciones reales
  anotadas construidas a mano: la fracción de coincidencia reportada
  coincide con el cálculo esperado (US3 AS1).
- Un conjunto de grabaciones sintéticas donde ninguna de las 72
  reservadas participa (US3 AS2, FR-008) -- verificado reutilizando
  `deteccion.orquestador.construir_lista_grabaciones` tal cual, sin una
  segunda partición.

## Ejecución manual real -- medir sobre GuitarSet completo

**No es un test.** Requiere GuitarSet real en disco (Principio IV: no
viene con este repositorio) y tarda un tiempo a medir con evidencia
real en `/speckit-implement` (research.md #1 argumenta que la
complejidad es lineal en el número de instantes por grabación, no se
anticipa el mismo riesgo de escala que forzó acotar el hito 1 -- pero
se confirma, no se asume, mismo criterio que toda afirmación
cuantitativa de este proyecto).

```bash
uv run python -m guitar_tabs_analysis.digitacion.cli --root-dir /ruta/a/guitarset
```

(CLI exacto a definir en `/speckit-tasks` de esta feature -- este
comando es ilustrativo del patrón que seguirá, mismo espíritu que
`deteccion.cli` del hito 2: `--modo` sin valor por defecto, con salida
de progreso, nunca invocable sobre `"reservado"` durante el desarrollo.)

Resultado esperado: un artefacto con el modelo de coste aplicado (los
parámetros de `ModeloCoste`, todos con evidencia real detrás salvo los
pesos de movimiento, research.md #13), la lista de grabaciones medidas,
las exclusiones de grabación e instante con su motivo, y la fracción de
coincidencia agregada contra la digitación real anotada -- listo para
comentarlo en `/speckit-constitution` y fijar el presupuesto del
Principio VII del hito 3 con la cifra real (spec.md, "PRESUPUESTO").
