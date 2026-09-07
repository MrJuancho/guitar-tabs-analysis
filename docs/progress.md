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

`ejecutar_corrida` (orquestador.py) ahora imprime progreso -- pedido
directo tras el incidente de la sesión anterior (un proceso de 18h que
seguía vivo se dio por muerto en silencio y se relanzó encima, causando
la condición de carrera que pareció un bug de escritura). Una línea por
tema recién procesado (`[i/N] tema_id  ok  Xs  N refs` o `excluido:
motivo`), un resumen único para los temas ya cacheados (`N temas ya
procesados, se omiten` -- nunca una línea por cada uno) y un aviso al
entrar a agregación (`agregando N temas`). Sin dependencias nuevas, sin
niveles de verbosidad. Verificado contra el `conjunto_completo` real
(1559 temas cacheados): dos líneas, no 1559. `just gauntlet` verde: 175
tests, 98.75%, `orquestador.py` al 100%.

## Qué sigue

Hito 1 medido y documentado en ambos modos (constitución v1.6.0,
`mediciones/*.json` ya commiteados). Decidir el hito 2 (transcripción).

## Bloqueado / pendiente de decisión

Ninguno. Feature 001: dtype en `_decodificar_audio` -- diferido a hito 2.
Licencia de pesos de Demucs (research.md #3 de 003): cita del usuario, no
verificada de forma independiente (`github.com` bloqueado).
