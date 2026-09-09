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

Incidente real: `just detectar medibles` mató por el kernel dos veces
(~61 GB) sobre 288 grabaciones. Diagnóstico medido descartó audio/mirdata
-- RSS del bucle plano (151->232 MB/25 grabaciones reales). Causa real:
`agregar_conjunto` pooleaba notas de las 288 grabaciones antes de
emparejar -- `mir_eval.match_notes` arma matrices N×M, cuadrático
(research.md #16). Defecto de CORRECCIÓN, no solo memoria: permitía
aciertos entre grabaciones sin relación temporal. FR-013 lo prohíbe
ahora. Arreglo: emparejar siempre por grabación, sumar conteos
(`verdaderos_positivos` nuevo) y derivar la razón de la suma. Verificado
a escala real (288×200 notas): 0.59s, delta 23.8 MB (antes: OOM). `just
gauntlet` verde: 242 tests, 98.40%.

## Qué sigue

Re-correr `just detectar medibles <root_dir>` contra GuitarSet real -- la
corrida anterior (sin commitear) no sirve: 288/288 exclusiones por
dataset incompleto en ese momento, y con el diseño roto. Después:
mutation testing acotado antes de cerrar la Feature 006.

## Bloqueado / pendiente de decisión

Ninguno nuevo. `mediciones/deteccion_medibles.json` (sin commitear) es
basura de una corrida inválida, se sobrescribe en la próxima. Licencia
de pesos de Demucs: no verificada independientemente.
