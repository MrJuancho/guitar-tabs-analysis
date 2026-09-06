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

Feature 004 cerrada (Polish, T029-T033). T029: único test `modelo_real`
de la feature, `procesar_tema` de punta a punta con `DemucsSeparador`
real sobre 1 tema sintético de 2s. Se eliminó (no se cubrió) la rama
defensiva de modo inválido en `construir_lista_temas`: `mypy --strict`
prueba que es inalcanzable (Literal cerrado + `argparse choices` en el
único llamador real) -- misma categoría que `audio_dir` de la Feature
001; cobertura subió a 100%. Mutación (triage no conteo): 23
sobrevivientes, 3 equivalentes documentados (`transformaciones=[]`
redundante con el default del dataclass), 20 gaps reales cerrados
fortaleciendo tests existentes -- ver tasks.md T031. `just medir modo
root_dir` agregado al justfile. `just gauntlet` verde: 147 tests, 98.70%.

## Qué sigue

Feature 004 completa. Sigue la corrida real sobre la submuestra del
hito 1 (`just medir submuestra_hito1 <ruta-slakh2100>`, ~36 min) para
obtener la cifra de SI-SDR y cerrar el `ABIERTO` del presupuesto del
Principio VII -- requiere el dataset Slakh2100 real, fuera de este repo.

## Bloqueado / pendiente de decisión

Ninguno. Feature 001: dtype en `_decodificar_audio` -- diferido a hito 2.
Licencia de pesos de Demucs (research.md #3 de 003): cita del usuario, no
verificada de forma independiente (`github.com` bloqueado).
