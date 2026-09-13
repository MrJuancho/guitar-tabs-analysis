# Quickstart: Preferencia por posiciones bajas en el modelo de coste

Valida `analytics.metrica_digitacion` (extendido) y
`digitacion.orquestador` (extendido) contra `spec.md` (ver
[contracts/digitacion.md](./contracts/digitacion.md)). Dos secciones,
mismo criterio que `quickstart.md` de la Feature 007: lo que corre
siempre y rápido, y la ejecución manual sobre GuitarSet real.

## Lo que corre en `just gauntlet` (rápido, sin GuitarSet real en disco)

```bash
uv sync
just gauntlet
```

- `peso_altura_traste = 0.0` (el valor de `MODELO_COSTE_POR_DEFECTO`,
  research.md #6) produce el MISMO `coste_total` que la Feature 007 sin
  este componente, sobre las mismas secuencias sintéticas ya usadas por
  esa feature (US1 AS3, FR-004).
- Una posición al aire (`traste == 0`) aporta coste `0` de este
  componente, para cualquier valor de `peso_altura_traste` (US1 AS2,
  FR-003).
- Dos posiciones candidatas con el mismo tono, mismo coste de
  estiramiento/desplazamiento/cruce, una en traste bajo y otra en
  traste alto: la de traste más bajo tiene coste total menor,
  proporcional a `peso_altura_traste` y a la diferencia de traste (US1
  AS1, FR-001).
- Los pesos de desplazamiento y cruce de cuerdas permanecen en `1.0` en
  el modelo por defecto, sin cambio respecto de la Feature 007 (US1
  AS4, FR-002).
- Una secuencia sintética corta con óptimo calculable por fuerza bruta,
  el término de altura incluido, para varios valores de
  `peso_altura_traste` (incluido `0`): la digitación producida coincide
  en coste total con ese óptimo (US2 AS1/AS2, FR-005) -- confirma que
  agregar el peso de nodo no rompe la subestructura óptima (research.md
  #1).

## Ejecución manual real -- barrer el peso sobre GuitarSet completo

**No es un test.** Requiere GuitarSet real en disco (Principio IV) y
corre en un solo proceso (research.md #4), reutilizando la lectura de
las 288 grabaciones entre los diez valores candidatos -- nunca diez
invocaciones separadas de la CLI de la Feature 007.

```bash
uv run python -m guitar_tabs_analysis.digitacion.cli_barrido --root-dir /ruta/a/guitarset
```

(CLI exacto a definir en `/speckit-tasks` de esta feature -- comando
ilustrativo del patrón; el conjunto de valores candidatos
`0, 0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100` está declarado en código
como constante nombrada, research.md #3/#5, nunca como argumento de
línea de comandos.)

Tiempo esperado: `~25s` (`~8.9s` de lectura única + `~1.6s` por cada
uno de los diez valores candidatos, research.md #4) -- confirmar con
evidencia de reloj real en `/speckit-implement` antes de asumirlo
cerrado, mismo criterio que toda afirmación cuantitativa de este
proyecto.

Resultado esperado: un `ResultadoBarrida` con los diez `PuntoBarrida`
(un `peso_altura_traste` y su `fraccion_coincidencia` cada uno), el
punto `peso_altura_traste == 0.0` coincidiendo exactamente con
`0.618633...` (la cifra ya cerrada en Principio VII), y ningún punto
comparado contra el presupuesto vigente (`0.55`, FR-009) ni entre sí
para elegir un "ganador" (FR-007) -- esa elección, con la curva
completa delante, es una decisión de una sesión posterior de
`/speckit-constitution`, fuera de alcance de esta feature.
