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

Feature 004 (medición de la línea base): spec/plan/tasks commiteados
(untracked, mismo hueco que Feature 001 -- ef6c18f). `/speckit-analyze`
encontró 1 CRITICAL + 4 menores, todos cerrados sin tocar código (la
feature aún no se implementa): `transformaciones` faltaba en todo el
diseño pese a que `spec.md` la exige seis veces -- agregada a
`ResultadoProcesamientoTema`/`ArtefactoMedicion` y al contrato/tasks
afectados; dos referencias cruzadas a tareas equivocadas para
"validación de firma" corregidas (T023, no T020/T021); SC-004 (un fallo
no detiene la corrida) ganó test dentro de una misma invocación, como
segundo escenario de T016; `derivar_temas_*()` renombrado a
`construir_lista_temas` en plan.md; SC-005 (memoria) documentado como
garantía de diseño, no de test dedicado (un `weakref` dependería del GC).
`just gauntlet` verde (113 tests, 99.45%).

## Qué sigue

`/speckit-implement` de la Feature 004, Foundational primero (T004/T005:
extracción de Feature 002 con su criterio de corte explícito).

## Bloqueado / pendiente de decisión

Ninguno. Feature 001: dtype en `_decodificar_audio` -- diferido a hito 2.
Licencia de pesos de Demucs (research.md #3 de 003): cita del usuario, no
verificada de forma independiente (`github.com` bloqueado).
