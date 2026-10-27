#!/usr/bin/env python3
"""Offline audio-owner sanitizer, concurrency and RT guard checks."""
import os,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'build/ghost-buffer-engine-final';work=ROOT/'experiments/ghost-c1';val=OUT/'validation';val.mkdir(exist_ok=True)
base=['cc','-std=c11','-O1','-g','-ffp-contract=off','-DGHOST_STANDALONE_UID=0x47485354','-DGHOST_FINAL_PRODUCT=1','-DGHOST_BUFFER_ENGINE=1','-I'+str(ROOT/'src'),'-I'+str(ROOT/'build'),'-I'+str(work),'-fno-omit-frame-pointer']
sources=[str(work/n) for n in ['core.c','motion.c','params.c','state.c','../ghost/ghost.c','engine.c','vst.c','base.c','../../src/repeat.c']]
host=(ROOT/'tests/ghost_product_host.c').read_text().replace('numParams==126','numParams==131').replace('k<3200','k<12000')
host=host.replace('  f->setParameter(f,124', '''  if(k%71==0)f->setParameter(f,126,1);
  if(k%71==43)f->setParameter(f,126,0);
  if(k%89==0)f->setParameter(f,127,(k%101)/100.f);
  if(k%47==0)f->setParameter(f,128,(k/47)%2);
  f->setParameter(f,124''')
host=host.replace('3200 blocks / 409600 frames','12000 blocks / 1536000 frames')
(val/'stress.c').write_text(host)
concurrent=(work/'concurrency.c').read_text().replace('fx->setParameter(fx,2,.5f);','fx->setParameter(fx,126,(attempts/5)%2);fx->setParameter(fx,127,(attempts%101)/100.f);fx->setParameter(fx,128,attempts%2);fx->getParameter(fx,129);fx->setParameter(fx,2,.5f);')
(val/'concurrent.c').write_text(concurrent)
for name,flags,source,env in [('asan-ubsan',['-fsanitize=address,undefined'],val/'stress.c',dict(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')),('tsan',['-fsanitize=thread'],val/'concurrent.c',dict(TSAN_OPTIONS='halt_on_error=1'))]:
 exe=val/name;cmd=base+flags+sources+[str(source),'-lm','-pthread','-o',str(exe)];(val/(name+'-command.txt')).write_text(' '.join(cmd)+'\n');subprocess.run(cmd,check=True)
 with (val/(name+'.log')).open('w') as log:subprocess.run([str(exe)],env=dict(os.environ,**env),stdout=log,stderr=subprocess.STDOUT,check=True)
 print('PASS',name,flush=True)
# Reuse existing interposition rules against the new actual DSP units and stress host.
script=(ROOT/'experiments/ghost-product/run_rt_guard.py').read_text()
script=script.replace("out=ROOT/'build/ghost-functional-final/validation/rt'","out=ROOT/'build/ghost-buffer-engine-final/validation/rt'")
script=script.replace("(ROOT/'tests/ghost_product_host.c').read_text()","(ROOT/'build/ghost-buffer-engine-final/validation/stress.c').read_text()")
script=script.replace("'-DGHOST_FINAL_PRODUCT=1'","'-DGHOST_FINAL_PRODUCT=1','-DGHOST_BUFFER_ENGINE=1'")
exec(compile(script,str(ROOT/'experiments/ghost-product/run_rt_guard.py'),'exec'),{'__file__':str(ROOT/'experiments/ghost-product/run_rt_guard.py')})
