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

Feature 006, T016-T024 (US3 completa, las tres user stories cerradas):
`ExclusionDeteccion`/`ResultadoDeteccionGrabacion` en `analytics` (nunca
en `deteccion/orquestador.py`, evita el ciclo de imports),
`clasificar_polifonia_en_instante` + helper `_particionar_por_polifonia`
-- clasifican SIEMPRE contra `notas_referencia`, nunca contra lo
estimado, verificado en el código. `evaluar_grabacion`/`agregar_conjunto`
(pool plano, nunca promedio por grabación) y `deteccion/orquestador.py`
(`ejecutar_deteccion`): fallo por grabación es exclusión terminal, nunca
aborta la corrida. `just gauntlet` verde: 224 tests, 99.05% (los dos
módulos nuevos al 100%). Mutation testing acotado: 0 sobrevivientes
nuevos en `deteccion.orquestador` (2 gaps de cobertura reales cerrados).

## Qué sigue

Fase 6 (Polish, T025-T027): falta mutation testing formal de cierre y
validar `quickstart.md` a mano. Fase 7 (CLI, T028-T035):
`construir_lista_grabaciones` -- ahí se excluyen por primera vez las 72
reservadas (semilla `20260908`, Principio VI); `ejecutar_deteccion` no
lo hace, recibe la lista ya filtrada de su llamador.

## Bloqueado / pendiente de decisión

Ninguno nuevo. Manifiesto de reservados de GuitarSet: se crea en T028.
Licencia de pesos de Demucs: no verificada independientemente.
