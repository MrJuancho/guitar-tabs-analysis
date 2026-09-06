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

Feature 004: User Story 3 completa (T025-T028) -- las tres historias y el
CLI real. Se saboteó `ejecutar_corrida` para confirmar que T021/T022 (US2)
se ponen en rojo -- lo hacen, revertido sin diff residual. T025/T026:
`conjunto_completo` de punta a punta y los dos modos sin interferencia,
sin implementación nueva. T027/T028: `medicion/cli.py` -- `--modo` sin
default (`SystemExit` claro, `DemucsSeparador` nunca se construye antes,
verificado con monkeypatch); escritura atómica del artefacto (tmp +
`os.replace`) con test de interrupción simulada; `_ejecutar_y_escribir`
(núcleo testeable) probado con `SeparadorFalso`, incluye que
`ModeloCambiadoError` no escribe artefacto. `just gauntlet` verde: 144
tests, 98.51%.

## Qué sigue

Feature 004 con las tres user stories cerradas. Queda Polish (T029-T033):
test `modelo_real`, mutation testing, recipe `just medir`, validación de
`quickstart.md`. Después, la corrida real sobre la submuestra del hito 1
para cerrar el presupuesto numérico del Principio VII.

## Bloqueado / pendiente de decisión

Ninguno. Feature 001: dtype en `_decodificar_audio` -- diferido a hito 2.
Licencia de pesos de Demucs (research.md #3 de 003): cita del usuario, no
verificada de forma independiente (`github.com` bloqueado).
