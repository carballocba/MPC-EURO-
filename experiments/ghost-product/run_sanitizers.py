#!/usr/bin/env python3
"""Offline GHOST final VST sanitizer/stress harnesses, same private DSP units."""
import os,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];out=ROOT/'build/ghost-functional-final/validation';work=ROOT/'experiments/ghost-c1'
(out/'sanitizers').mkdir(parents=True,exist_ok=True)
base=['cc','-std=c11','-O1','-g','-ffp-contract=off','-DGHOST_STANDALONE_UID=0x47485354','-DGHOST_FINAL_PRODUCT=1','-DGHOST_INTEGRATION_PROBE=1','-I../../src','-I../../build','-I.','-I../ghost','-fno-omit-frame-pointer']
sources=['core.c','motion.c','params.c','state.c','../ghost/ghost.c','engine.c','vst.c','base.c','../../src/repeat.c']
for name,flags,host,env in [('asan',['-fsanitize=address,undefined'],'../../tests/ghost_product_host.c',dict(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')),('tsan',['-fsanitize=thread'],'concurrency.c',dict(TSAN_OPTIONS='halt_on_error=1'))]:
 binary=out/'sanitizers'/name;cmd=base+flags+sources+[host,'-lm','-pthread','-o',str(binary)]
 (out/'sanitizers'/(name+'-command.txt')).write_text(' '.join(cmd)+'\n');subprocess.run(cmd,cwd=work,check=True)
 with (out/(name+'.log')).open('w') as log:subprocess.run([str(binary)],env=dict(os.environ,**env),stdout=log,stderr=subprocess.STDOUT,check=True)
 print('PASS',name)
