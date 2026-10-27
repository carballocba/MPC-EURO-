#!/usr/bin/env python3
"""Darwin source interposition on the actual GHOST units; no device access."""
import pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];out=ROOT/'build/ghost-functional-final/validation/rt';out.mkdir(parents=True,exist_ok=True)
ref=(ROOT/'tests/test.c').read_text();guard=ref[ref.index('static _Thread_local int audio;'):ref.index('static intptr_t host(')]
includes='''#include <stdlib.h>
#include <stdio.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdarg.h>
#include <fcntl.h>
#include <unistd.h>
'''
# Existing counters not used by this test; preserve only the violation counter.
guard=guard.replace('violations, notices, display_updates, control_echoes','violations')
host=(ROOT/'tests/ghost_product_host.c').read_text().replace('static intptr_t host(', 'static intptr_t host(')
host=host.replace('return op==audioMasterGetTime?', 'if(op!=audioMasterGetTime)GUARD();return op==audioMasterGetTime?')
host=host.replace('f->processReplacing(f,in,out,128);', 'audio=1;f->processReplacing(f,in,out,128);audio=0;')
host=host.replace(' puts("PASS final product:', ' assert(atomic_load(&violations)==0);puts("PASS zero RT allocation/mutex/file/join/host violations");\n puts("PASS final product:')
file=out/'host.c';file.write_text(includes+guard+host)
wraps='malloc calloc realloc free pthread_mutex_lock pthread_mutex_trylock pthread_mutex_unlock pthread_join open fopen read write'.split()
base=['cc','-std=c11','-O2','-ffp-contract=off','-DGHOST_STANDALONE_UID=0x47485354','-DGHOST_FINAL_PRODUCT=1','-DGHOST_INTEGRATION_PROBE=1','-I'+str(ROOT/'src'),'-I'+str(ROOT/'build'),'-I'+str(ROOT/'experiments/ghost-c1')]
sources=[ROOT/'experiments/ghost-c1'/n for n in ['core.c','motion.c','params.c','state.c','vst.c','base.c','engine.c']]+[ROOT/'experiments/ghost/ghost.c',ROOT/'src/repeat.c'];objects=[]
for i,s in enumerate(sources):
 p=out/f'{i}.o';subprocess.run(base+[f'-D{x}=__wrap_{x}' for x in wraps]+['-c',str(s),'-o',str(p)],check=True);objects.append(str(p))
subprocess.run(base+objects+[str(file),str(ROOT/'tests/rt_real_darwin.c'),'-lm','-pthread','-o',str(out/'test')],check=True)
subprocess.run([str(out/'test')],check=True)
