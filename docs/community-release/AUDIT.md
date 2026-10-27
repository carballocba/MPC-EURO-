# GHOST2.4.2 — cierre de bloqueos comunitarios (2026-10-26)

**GO para revisión y preparación de ensayo físico supervisado. NO-GO para publicación todavía.**

## Instalador seguro: implementado y validado offline

Controlador genérico de escritorio (Python3 local, SSH, sin IP ni baseline personal) y backend POSIX/BusyBox con backup persistente fuera de GHOST, copia independiente en ordenador, watchdog nohup independiente de acvs, PID+identidad de inicio y rollback automático de archivos/registro propio. Activación por rename, hashes antes/después y host activo/estable. Ningún plugin ajeno es objetivo de escritura. Si otro plugin está registrado dentro de GHOST se rechaza la operación.

Updates con metadata igual preservan los bytes, inode y preferencias de MPC.settings. Instalación limpia/eliminación cambian sólo el registro GHOST; no es posible registrar limpiamente y mantener ese archivo entero idéntico. XML validado localmente y comparación estructural de todas las demás entradas/preferencias. La inversa de registro es literal y selectiva; preserva DNS y cambios externos. Backups y el candidato fallido no se borran. Se mantienen FXP editados y archivos extra del usuario; no se abren ni convierten proyectos.

**28/28 tests del paquete**: instalación limpia, update, desinstalación, rollback repetido, fallos en cinco etapas de instalación y cinco de eliminación, SIGKILL y trabajador bloqueado, arranque fallido, herramientas ausentes, copia fallida, settings concurrentes antes/después del registro, permisos, PD LAB/MPC-CORE preservados, locks y recuperación desde cada copia redundante. Se detectó/corrigió una carrera de guardianes durante rollback inmediato. Logs anteriores conservados como evidencia; no se oculta el fallo inicial.

Límite honesto: guardián automático con el dispositivo encendido; tras corte eléctrico quedan checkpoints/backups y recuperación SSH persistente, no un nuevo servicio de boot automático. Fallo físico de disco/host o cambios externos incompatibles en el propio registro GHOST requieren revisión; nunca se reportan como éxito. El controlador intenta recuperar el servicio incluso ante un conflicto de registro. No se promete una garantía imposible frente a hardware destruido o edición concurrente arbitraria como root.

## Procedencia: bloqueos identificados cerrados

sh_knob_r32.png se generó desde fuentes MIT de sd88me/force-shadow y el tema original, sin firmware ni imágenes Akai. El PNG coincide BYTE A BYTE:45c6f5fa8999ccd1c8c1f0535e8c7665bba9c4fc2b3948f9c46650e4254f430c. También se reprodujeron byte a byte los ocho estados del fantasma desde su función de pixel art original. Nada visual tuvo que reemplazarse.

Fuentes canónicas: unidades C exactas y recursos nativos editables JSON/PNG/FXP, con generadores de origen, renderer, fuente tipográfica, dependencias, notices, scripts de build/instalación y manifiesto de hashes. El build soportado no depende de ZIP históricos, backup personal o firmware. GPL-3.0-only para el derivado; MIT para ABI/framework/runtime; términos DejaVu/Bitstream y stb retenidos. No se atribuye procedencia conocida a componentes ajenos a los inspeccionados ni se concede autorización de marcas. Ver LICENSE_AUDIT.md.

## DSP/ABI y validación

Binario aprobado conservado exactamente:588019130b31ced7077f7e4afe35bd23b0753df7a2959e2af39fa825e1b81afd. ELF32 ARM hard-float, único export VSTPluginMain; libc/libm/libpthread, símbolos GLIBC2.4/2.27.156 parámetros y UID1195922260/47485354. GUI, Q-Links, version.xml y52FXP del ZIP son idénticos al BOTH FIX;16programas están preservados en ese mismo binario.

29/29 regresiones nativas: BOTH7, LIVE8, Random Repeat12, presets2. ASan/UBSan PASS sobre12000bloques; TSan PASS con5120000eventos MIDI,102756gestos y10000recalls; guarda RT PASS sin nuevas allocations/mutex/file/join/host violations en callback. Son pruebas nativas, no ejecución del plugin ARM ni certificación de deadlines en la MPC. Recompilación ARMv7 y ABI offline verificados; el archivo fuente final debe reproducir además el ZIP exacto con rebuild.py/package.py.

## Pendientes concretos antes de publicar

1. Ensayo físico autorizado del ZIP final: CPU/callback p99/max, outliers, dropouts, GUI/touchscreen, foco y16Q-Links, INDEPENDENT/BOTH, presets, instalación/desinstalación/rollback. Protocolo con criterios en HARDWARE_PROTOCOL.md. No se ha conectado ni modificado la MPC.
2. Revisión de mantenedores para el controlador seguro: checker del catálogo sin errores pero con DOS warnings por install.sh/uninstall.sh personalizados. Una aplicación que copie directamente portable/ omitiría esta transacción; no se recomienda ni declara segura esa ruta. No ignorar las advertencias para afirmar integración comunitaria aprobada.
3. Revisión/autorización del snapshot y del commit/tag final antes de cualquier distribución. No hay push, merge, PR, tag ni release creados. El viejo commit base por sí solo no representa esta fuente; FILES.sha256 identifica el snapshot completo.

Las pruebas físicas y el canal de catálogo siguen pendientes expresamente; los bloqueos técnicos de recuperación y procedencia identificados tienen implementación/evidencia offline. Estado: READY FOR SUPERVISED HARDWARE VALIDATION / PUBLICATION NO-GO.
