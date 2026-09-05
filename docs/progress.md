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

**Feature 003 (separación con Demucs) completa: T001-T023, 8 fases.**
`just gauntlet` verde (113 tests, 99,45% cobertura; `separador.py` y
`demucs_separador.py` al 100%). Dos hallazgos reales, test-rojo-primero:
(1) `shifts=1` (default de `Separator`) desplaza la entrada
aleatoriamente cada llamada -- corregido con `shifts=0`, determinista
bit a bit (research.md #10); (2) mutation testing incluía `modelo_real`,
causando 22/32 mutantes en `timeout` y 0 `killed` -- corregido
excluyéndolos en `pyproject.toml`. Triage final: 153/154 mutantes
matados (99,35%), 1 equivalente sin pragma (comparte línea con uno
real). T023: corrigió `quickstart.md`, nunca verificado (patrón 002/T028).

## Qué sigue

Feature 003 cerrada. **Pendiente recomendado, no bloqueante**: correr
`/speckit-constitution` para registrar en el Principio VII la evidencia
de research.md #9 (submuestra de 40 temas de `validation`, semilla
`20260904`, para una corrida completa del hito 1).

## Bloqueado / pendiente de decisión

Feature 001: dtype en `_decodificar_audio` -- diferido a hito 2.
Licencia de pesos de Demucs (research.md #3 de 003): cita del usuario,
no verificada de forma independiente (`github.com` bloqueado).
