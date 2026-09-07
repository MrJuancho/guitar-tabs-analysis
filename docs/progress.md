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

Feature 005 (compuerta de la métrica) implementada completa (T001-T015):
`medicion/compuerta.py` nuevo, solo `stdlib`, juzga `mediciones/<modo>.json`
contra `-8.0 dB` (Principio VII) sobre la mediana de emparejadas, con
fracción sin pareja obligatoria en el veredicto. Incorporada a `just
gauntlet` (falla si el artefacto real no alcanza el presupuesto -- hoy
aprueba, `-6.95 dB`). Mutación (triage, no conteo): 46 sobrevivientes,
18 gaps reales cerrados (contexto del `Veredicto`, mensajes de error,
`stdout` de `main`), 28 equivalentes documentados (texto de `argparse`,
prosa no diagnóstica). Hallazgo: `# pragma: no mutate` es solo
documentación en esta versión de `mutmut` (TODO propio de la
herramienta, no exclusión real) -- el triage se sostiene por revisión
humana en tasks.md. `just gauntlet` verde: 168 tests, 98.69%.

## Qué sigue

Features 004 y 005 completas -- el hito 1 tiene medición y compuerta.
Sigue evaluar la corrida sobre el conjunto completo (`just medir
conjunto_completo <ruta>`, ~23h) y decidir el hito 2 (transcripción).

## Bloqueado / pendiente de decisión

Ninguno. Feature 001: dtype en `_decodificar_audio` -- diferido a hito 2.
Licencia de pesos de Demucs (research.md #3 de 003): cita del usuario, no
verificada de forma independiente (`github.com` bloqueado).
