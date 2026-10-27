#!/usr/bin/env python3
"""Finalize offline review assets. No SSH, device mutation or publication."""
import pathlib,json,hashlib,shutil,zipfile,tarfile,gzip,io,subprocess,re
R=pathlib.Path(__file__).resolve().parents[1];O=R/'build/ghost-community-safe';S=O/'source';D=R/'docs/ghost/community-release/2.4.2-safe';PYTHON=R/'build/venv/bin/python';sha=lambda b:hashlib.sha256(b).hexdigest()
log=(O/'final-package-tests.log').read_text();assert re.search(r'Ran 28 tests',log) and log.rstrip().endswith('OK')
assert json.loads((O/'ASSET_REGENERATION.json').read_text())['status']=='BYTE-IDENTICAL'
assert all(x['byte_identical'] for x in json.loads((O/'MASCOT_REGENERATION.json').read_text()))
for f in ('asan-ubsan','tsan','rt-guard'):assert (O/'validation'/f'{f}.log').read_text().startswith(('PASS','10000 blocks'))
for name,count in [('both',7),('live',8),('rr',12),('preset',2)]:
 t=(O/f'{name}-regressions.log').read_text();assert f'Ran {count} tests' in t and t.rstrip().endswith('OK')
D.mkdir(parents=True,exist_ok=True)
(D/'AUDIT.md').write_text('''# GHOST2.4.2 — cierre de bloqueos comunitarios (2026-10-26)

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
''')
for stale in (D/'catalog-check.json', S/'docs/community-release/catalog-check.json'):
 if stale.exists():stale.unlink()
for name in ('ASSET_REGENERATION.json','MASCOT_REGENERATION.json','ABI.json','catalog-check.stderr'):
 if (O/name).exists():shutil.copy2(O/name,D/name)
# Include precise preferred-source links for the newly audited pixel-art inputs.
p=D/'LICENSE_AUDIT.md';s=p.read_text();addition='\nThe eight ghost states were independently regenerated from sprite() in experiments/ghost-ui-v2/render.py and match byte-for-byte (MASCOT_REGENERATION.json). That original pixel-art source is included; no opaque mascot/stock art input is required.\n';p.write_text(s if addition.strip() in s else s+addition)
p=D/'SOURCE_README.md';s=p.read_text();addition='\nOptional: python3 regenerate_mascot.py verifies all eight original project-authored sprite states byte-for-byte from their drawing function, without private build artifacts.\n';p.write_text(s if addition.strip() in s else s+addition)
for p in D.iterdir():
 if p.is_file():dst=S/'docs/community-release'/p.name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(p.read_bytes())
(S/'SOURCE-README.md').write_bytes((D/'SOURCE_README.md').read_bytes())
for p in (R/'community/ghost').iterdir():
 if p.is_file():shutil.copy2(p,S/'community/ghost'/p.name)
(S/'tools').mkdir(exist_ok=True);shutil.copy2(__file__,S/'tools'/pathlib.Path(__file__).name)
for n in ('test_ghost_community_safe.py','test_shared.py','test.c','ghost_product_host.c','rt_real_darwin.c'):shutil.copy2(R/'tests'/n,S/'tests'/n)
# Provenance/evidence without personal device snapshots or compiler caches.
for n in ('final-package-tests.log','both-regressions.log','live-regressions.log','rr-regressions.log','preset-regressions.log','sanitizers.log'):
 dest=S/'evidence'/n;dest.parent.mkdir(exist_ok=True);dest.write_bytes((O/n).read_bytes().replace(str(R).encode(),b'<SOURCE_ROOT>'))
# Generate the final package including its final docs and no signature/publication claims.
subprocess.run([str(PYTHON),str(S/'package.py'),'--out',str(O/'dist')],check=True)
checker=S/'community-tools/tools/catalog_check.py';p=subprocess.run([str(PYTHON),str(checker),str(O/'dist/GHOST-2.4.2-mpc-armv7.zip'),'--catalog','--require-portable','--expect-id','ghost','--expect-repo','carballocba/MPC-EURO-','--json'],capture_output=True,text=True);assert p.returncode==0,p.stderr;(O/'catalog-check.json').write_text(p.stdout);(O/'catalog-check.stderr').write_text(p.stderr)
# Manifest covers source only: build products/caches are excluded from both list and archive.
def source_files():
 return [p for p in sorted(S.rglob('*')) if p.is_file() and not any(x in p.relative_to(S).parts for x in ('rebuild','dist','__pycache__','knob-rebuild','zig-global','zig-local')) and p.name!='FILES.sha256']
paths=source_files();(S/'FILES.sha256').write_text(''.join(sha(p.read_bytes())+'  '+str(p.relative_to(S))+'\n' for p in paths))
with (O/'dist/GHOST-2.4.2-source.tar.gz').open('wb') as f:
 with gzip.GzipFile(fileobj=f,mode='wb',mtime=0,filename='') as gz:
  with tarfile.open(fileobj=gz,mode='w') as t:
   for p in sorted(paths+[S/'FILES.sha256']):
    b=p.read_bytes();item=tarfile.TarInfo('GHOST-2.4.2-source/'+str(p.relative_to(S)));item.size=len(b);item.mode=0o644;item.mtime=0;t.addfile(item,io.BytesIO(b))
with zipfile.ZipFile(O/'dist/GHOST-2.4.2-review-docs.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(D.iterdir()):
  if p.is_file():i=zipfile.ZipInfo('GHOST-review/'+p.name,(2026,10,26,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,p.read_bytes())
checks={p.name:sha(p.read_bytes()) for p in sorted((O/'dist').iterdir()) if p.name!='SHA256SUMS'};(O/'dist/SHA256SUMS').write_text(''.join(h+'  '+n+'\n' for n,h in checks.items()))
report=dict(publication='NO-GO pending hardware trial and catalog maintainer review',offline='PASS',transaction_tests=28,dsp_regressions=29,sanitizers=['ASan/UBSan PASS','TSan PASS','RT guard PASS'],arm_execution=False,asset_regeneration='knob and8sprites BYTE-IDENTICAL',binary_sha256='588019130b31ced7077f7e4afe35bd23b0753df7a2959e2af39fa825e1b81afd',checksums=checks,device_access=False,published=False);(O/'FINAL_VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
