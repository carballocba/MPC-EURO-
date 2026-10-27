#!/usr/bin/env python3
"""Actual private VST units under sanitizers and RT interposition, offline only."""
import os,pathlib,subprocess
from generate import ROOT,OUT,generate
src=generate();val=OUT/'validation';val.mkdir(exist_ok=True)
(val/'integration-inputs.json').write_bytes((OUT/'integration-inputs.json').read_bytes())
base=['cc','-std=c11','-O1','-g','-ffp-contract=off','-DGHOST_STANDALONE_UID=0x47485354','-DGHOST_FINAL_PRODUCT=1','-DGHOST_BUFFER_ENGINE=1','-fno-omit-frame-pointer','-I'+str(src),'-I'+str(ROOT/'src'),'-I'+str(ROOT/'build'),'-I'+str(ROOT/'experiments/ghost-c1')]
sources=[src/n for n in ['core.c','motion.c','params.c','state.c','vst.c','base.c','engine.c','performance.c']]+[ROOT/'experiments/ghost/ghost.c',ROOT/'src/repeat.c']
host=(ROOT/'tests/ghost_product_host.c').read_text().replace('numParams==126','numParams==156').replace('k<3200','k<12000').replace('3200 blocks / 409600 frames','12000 blocks / 1536000 frames')
host=host.replace('  f->setParameter(f,124', '''  if(k%89==0)f->setParameter(f,143,(k%16)/15.f);
  f->setParameter(f,148,(k%3+1)/3.f);f->setParameter(f,149,.8f);f->setParameter(f,150,1);f->setParameter(f,151,1);f->setParameter(f,152,1);f->setParameter(f,153,.4f);f->setParameter(f,131,1);f->setParameter(f,132,(k%101)/100.f);f->setParameter(f,133,1);f->setParameter(f,139,1);
  if(k%71==0)f->setParameter(f,126,1);if(k%71==43)f->setParameter(f,126,0);
  if(k%19==0)f->setParameter(f,141,1);
  f->setParameter(f,124''')
(val/'stress.c').write_text(host)
concurrent=(ROOT/'experiments/ghost-c1/concurrency.c').read_text().replace('fx->setParameter(fx,2,.5f);','''fx->setParameter(fx,148,(attempts%3+1)/3.f);fx->setParameter(fx,151,1);fx->setParameter(fx,131,1);fx->setParameter(fx,132,(attempts%101)/100.f);fx->setParameter(fx,133,1);fx->setParameter(fx,139,.5f);
  fx->setParameter(fx,126,(attempts/5)%2);fx->setParameter(fx,127,(attempts%101)/100.f);fx->setParameter(fx,128,attempts%2);fx->getParameter(fx,129);
  if(attempts%11==0)fx->setParameter(fx,143,(attempts%16)/15.f);
  fx->setParameter(fx,2,.5f);''')
(val/'concurrent.c').write_text(concurrent)
for name,flags,source,env in [('asan-ubsan',['-fsanitize=address,undefined'],val/'stress.c',dict(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')),('tsan',['-fsanitize=thread'],val/'concurrent.c',dict(TSAN_OPTIONS='halt_on_error=1'))]:
 exe=val/name;cmd=base+flags+list(map(str,sources))+[str(source),'-lm','-pthread','-o',str(exe)];subprocess.run(cmd,check=True)
 (val/(name+'-command.txt')).write_text(' '.join(cmd)+'\n')
 with (val/(name+'.log')).open('w') as log:subprocess.run([str(exe)],env=dict(os.environ,**env),stdout=log,stderr=subprocess.STDOUT,check=True)
 print('PASS',name,flush=True)
# Reuse baseline interposition counters, but exercise the new native preset request under RT.
ref=(ROOT/'tests/test.c').read_text();guard=ref[ref.index('static _Thread_local int audio;'):ref.index('static intptr_t host(')].replace('violations, notices, display_updates, control_echoes','violations')
includes='#include <stdlib.h>\n#include <stdio.h>\n#include <pthread.h>\n#include <stdatomic.h>\n#include <stdarg.h>\n#include <fcntl.h>\n#include <unistd.h>\n'
rt_host=host.replace('return op==audioMasterGetTime?','if(op!=audioMasterGetTime)GUARD();return op==audioMasterGetTime?').replace('f->processReplacing(f,in,out,128);','audio=1;if(k%53==0)f->setParameter(f,143,(k%16)/15.f);f->processReplacing(f,in,out,128);audio=0;').replace(' puts("PASS final product:', ' assert(atomic_load(&violations)==0);puts("PASS zero RT allocation/mutex/file/join/host violations");\n puts("PASS final product:')
(val/'rt-host.c').write_text(includes+guard+rt_host)
wraps='malloc calloc realloc free pthread_mutex_lock pthread_mutex_trylock pthread_mutex_unlock pthread_join open fopen read write'.split();objects=[]
for i,source in enumerate(sources):
 obj=val/f'rt-{i}.o';subprocess.run(base+[f'-D{x}=__wrap_{x}' for x in wraps]+['-c',str(source),'-o',str(obj)],check=True);objects.append(str(obj))
exe=val/'rt-guard';subprocess.run(base+objects+[str(val/'rt-host.c'),str(ROOT/'tests/rt_real_darwin.c'),'-lm','-pthread','-o',str(exe)],check=True)
with (val/'rt-guard.log').open('w') as log:subprocess.run([str(exe)],stdout=log,stderr=subprocess.STDOUT,check=True)
print('PASS RT guard',flush=True)
