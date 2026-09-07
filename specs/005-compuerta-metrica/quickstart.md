# Quickstart: Compuerta de la métrica

Valida `medicion.compuerta` (ver [contracts/compuerta.md](./contracts/compuerta.md))
contra el spec. Una sola sección: a diferencia de las Features 003/004,
esta compuerta nunca invoca el modelo real, así que no hay una segunda
sección de "corrida lenta" -- todo lo que existe de esta feature corre en
`just gauntlet`.

## Lo que corre en `just gauntlet` (instantáneo, sin artefacto real)

```bash
uv sync
just gauntlet
```

Todo esto construye `dict`s sintéticos directamente (nunca corre
`medicion.orquestador` ni el modelo real) y los pasa a `evaluar_artefacto`:

- Un artefacto sintético cuya mediana de `emparejadas` es mayor, igual, y
  menor a `-8.0 dB` → veredicto de aprobación / aprobación (límite
  inclusive) / rechazo, respectivamente, cada uno con la mediana, el
  presupuesto y la fracción sin pareja en el resultado (spec.md US1).
- Una ruta de artefacto inexistente, un archivo con contenido que no es
  JSON válido, y un artefacto sin `reportes` o con el pool de
  `emparejadas` vacío (incluyendo el caso de `reportes` no vacío pero
  ninguna referencia emparejada) → los tres terminan en
  `ArtefactoInvalidoError`/código de salida `2`, nunca en aprobación
  (spec.md US2).
- Dos artefactos sintéticos distintos, uno por cada `modo` de la Feature
  004 → cada invocación de `--modo` juzga solo el suyo, con el mismo
  `PRESUPUESTO_SI_SDR_DB` en ambos, y sin que la ausencia del otro afecte
  el resultado (spec.md US3).
- Un property test (Hypothesis) sobre pools arbitrarios de valores
  finitos y `+inf` (nunca `-inf`, research.md #3) que confirma
  `statistics.median` coincide exactamente con la mediana de estadístico
  de orden que la Feature 002 ya usa para la mediana global -- lo que
  hace seguro no depender de esa función privada.

## Ejecución manual real -- juzgar el artefacto versionado de verdad

**Esto sí es él mismo el mecanismo real, no una simulación** -- a
diferencia de la Feature 004, aquí no hace falta ninguna invocación
"lenta" aparte: juzgar el artefacto real de la submuestra del hito 1 ya
versionado en el repositorio toma el mismo tiempo que cualquier caso
sintético.

```bash
just compuerta submuestra_hito1
```

Con la evidencia registrada en la constitución (Principio VII, v1.5.0:
mediana de emparejadas `-6.95 dB` sobre `mediciones/submuestra_hito1.json`),
el resultado esperado es aprobación (`-6.95 >= -8.0`), con `fraccion_sin_pareja`
reportada en `70/110 ≈ 0.636`.

Para juzgar el conjunto evaluable completo, una vez que exista su
artefacto (`mediciones/conjunto_completo.json`, producido por `just medir
conjunto_completo <ruta-slakh2100>`, Feature 004):

```bash
just compuerta conjunto_completo
```

## Integración con `just gauntlet`

`just gauntlet` incluye la evaluación de `mediciones/submuestra_hito1.json`
como paso final (research.md #8) -- si una corrida futura reemplaza ese
archivo con una medición peor que `-8.0 dB`, `just gauntlet` falla ahí,
igual que fallaría por cobertura insuficiente o por un contrato de
`import-linter` roto.
