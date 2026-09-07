# Data Model: Compuerta de la métrica

## Entrada: subconjunto leído del artefacto de la Feature 004

Esta feature no define un tipo nuevo para el artefacto -- lee el `dict`
JSON tal como `medicion.orquestador.artefacto_a_dict` lo serializa
(`specs/004-medicion-linea-base/data-model.md`), y solo usa estas claves:

| Clave leída | Forma | Uso en esta feature |
|---|---|---|
| `modelo.nombre`, `modelo.variante`, `modelo.firma` | `str` | Contexto informativo del veredicto (FR-009) |
| `modo` | `"submuestra_hito1" \| "conjunto_completo"` | Contexto informativo del veredicto |
| `semilla` | `int \| null` | Contexto informativo del veredicto (puede ser `null` en modo `conjunto_completo`) |
| `reportes[].emparejadas[].si_sdr` | `float` (puede ser `Infinity`) | Pool de la mediana de emparejadas (research.md #3) |
| `reportes[].sin_pareja` | `list` | Solo se usa su longitud, para el numerador de la fracción sin pareja |

Explícitamente **no se lee** `mediana` (es la mediana global, incluye
`sin_pareja` como `-inf` -- justo lo que el Principio VII prohíbe usar
para el presupuesto) ni `exclusiones`, `transformaciones_por_tema`,
`distribucion_referencias_por_tema`, `temas`, ni `checksum_sha256_prefijo`/
`licencia_pesos` de `modelo` -- ninguno lo necesita el veredicto.

## `Veredicto`

El resultado de evaluar un artefacto (Key Entity de `spec.md`).

| Campo | Tipo | Descripción |
|---|---|---|
| `aprobado` | `bool` | `mediana_emparejadas >= presupuesto` (FR-002) |
| `mediana_emparejadas` | `float` | `statistics.median` sobre el pool de `si_sdr` de referencias emparejadas (research.md #3) |
| `presupuesto` | `float` | Constante `-8.0`, Principio VII de la constitución v1.5.0 -- nunca se recalcula (FR-010) |
| `fraccion_sin_pareja` | `float` | `total_sin_pareja / (total_emparejadas + total_sin_pareja)` (research.md #4) |
| `total_emparejadas` | `int` | Tamaño del pool de la mediana -- contexto para interpretar `fraccion_sin_pareja` |
| `total_sin_pareja` | `int` | Numerador de `fraccion_sin_pareja` |
| `modelo_nombre`, `modelo_variante`, `modelo_firma` | `str` | Eco de `artefacto["modelo"]`, sin comparar contra ningún valor externo (FR-009, research.md #6) |
| `modo` | `str` | Eco de `artefacto["modo"]` |
| `semilla` | `int \| None` | Eco de `artefacto["semilla"]` |

Invariante: `aprobado is True` si y solo si `mediana_emparejadas >=
presupuesto`. Un `Veredicto` frozen (`dataclass(frozen=True)`), igual que
el resto de los tipos de dominio del proyecto.

## `ArtefactoInvalidoError`

Excepción para las tres condiciones de rechazo por evidencia (distintas
de un rechazo por presupuesto no alcanzado, que nunca es una excepción:
es un `Veredicto` con `aprobado=False`):

| Condición | Disparador | FR |
|---|---|---|
| Ruta ausente | `FileNotFoundError` al abrir el archivo | FR-004 |
| Contenido no interpretable | `json.JSONDecodeError`, o el `dict` no tiene la forma esperada (falta `reportes`, `modelo`, etc.) | FR-005 |
| Sin evidencia suficiente para juzgar | El pool de `si_sdr` de emparejadas queda vacío tras leer todos los `reportes` -- incluye tanto "cero referencias en total" como "solo referencias sin pareja" (research.md #5) | FR-006 |

`ArtefactoInvalidoError.mensaje` identifica cuál de las tres condiciones
ocurrió y, cuando aplica, la ruta o el valor faltante concreto -- nunca
un mensaje genérico ("artefacto inválido") sin decir por qué.

## Relación con el modelo de datos de la Feature 004

```text
ArtefactoMedicion (004, en disco como JSON)
  └─ reportes: list[ReporteTema]              ← ÚNICA fuente de datos de 005
       ├─ emparejadas: list[ReferenciaEmparejada]   → pool de la mediana
       └─ sin_pareja: list[ReferenciaSinPareja]     → numerador de la fracción

Veredicto (005, no persistido -- solo impreso/devuelto)
  ← calculado desde el subconjunto de arriba + la constante de presupuesto
```

No hay transiciones de estado: `evaluar_artefacto` es una función pura
sobre un `dict` ya leído, sin persistencia propia.
