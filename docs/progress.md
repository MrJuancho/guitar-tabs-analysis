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

Incidente real: 7 corridas de CI (`Guantelete`, `main`) en rojo en el
job `doctor` -- `FALTA: envs/basic_pitch_py310/.venv no existe`. Feature
006 se mergeó sin que CI pasara una vez (`gh run list`/`--log-failed`).
Causa: `doctor` trataba la ausencia de `.venv` (build local, nunca
versionado, JAMÁS existe en CI a propósito) igual que la ausencia del
directorio versionado (`envs/basic_pitch_py310/`, sí en git). Arreglo
(research.md #18): condición sobre el ESTADO de `.venv`, no CI-vs-local
-- ausente se reporta visible (criterio `modelo_real`) y `doctor` sigue
sin fallar; presente se verifica completo (intérprete, import, lock).
Directorio versionado ausente sigue siendo fallo duro. Chequeo extraído
a `scripts/verificar_entorno_basic_pitch.sh <ruta>` (códigos 0/1/2) para
probarlo con `uv venv`/`uv lock` reales sin tocar el `.venv` real. `just
gauntlet` verde: 248 tests, 98.40%.

## Qué sigue

Confirmar que el próximo push deja CI en verde (push de esta sesión
pendiente al momento de escribir esto). Después: mutation testing
acotado (T026) antes de cerrar la Feature 006.

## Bloqueado / pendiente de decisión

Ninguno nuevo. Licencia de pesos de Demucs: sin verificar.
