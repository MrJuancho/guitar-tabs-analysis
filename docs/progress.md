# Progress -- handoff entre sesiones

<!--
Este archivo se SOBRESCRIBE, no se acumula -- no es un diario ni un
changelog (eso ya vive en los ADRs y en git). Cada sesión reemplaza el
contenido de las tres secciones de abajo con el estado actual; no agrega
al final ni conserva versiones previas.

Límite duro: 40 líneas, este comentario incluido. Si no entra, resume más.

Generado una sola vez por Copier (`_skip_if_exists`) -- `copier update`
nunca vuelve a tocarlo después.
-->

## En qué quedó la última sesión

Feature 006 (hito 2, detección de notas) queda especificada y
planificada por completo -- spec/plan/research/data-model/contracts, sin
código todavía. Constitución generalizada: v1.7.0 aplica Principios
VI/VII a cualquier hito; v1.8.0 cierra el `ABIERTO` de la reserva de
GuitarSet -- 72/360 grabaciones (20%), semilla `20260908`, protegidas
por el hook de `tests/holdout/`. `tasks.md` generado (35 tareas) con dos
correcciones: `ExclusionDeteccion`/`ResultadoDeteccionGrabacion` viven en
`analytics`, no en `deteccion/orquestador.py` (evita ciclo de imports),
y `evaluar_subconjunto` documentado en contracts/deteccion.md. `just
gauntlet` verde: 175 tests, 98.75% (sin cambios de código).

## Qué sigue

`/speckit-implement` de la Feature 006, empezando por User Story 1
(`evaluar_subconjunto`, MVP, sin GuitarSet ni modelo).

## Bloqueado / pendiente de decisión

Ninguno nuevo. `tests/holdout/guitarset_reservado_hito2.json` todavía no
existe -- se crea en `/implement` (T028). Feature 001: dtype en
`_decodificar_audio` -- diferido, ahora relevante para el hito 2 en curso.
Licencia de pesos de Demucs: cita del usuario, no verificada
independientemente (`github.com` bloqueado).
