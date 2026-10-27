#!/usr/bin/env python3
import subprocess
from generate import ROOT,OUT,generate
s=generate();files=[s/n for n in ['core.c','motion.c','params.c','state.c','engine.c','performance.c']]+[ROOT/'experiments/ghost/ghost.c',ROOT/'experiments/ghost-performance/policy_test.c']
exe=OUT/'validation/policy-test';exe.parent.mkdir(exist_ok=True);subprocess.run(['cc','-std=c11','-O2','-DGHOST_BUFFER_ENGINE=1','-I'+str(s),'-I'+str(ROOT/'src'),'-I'+str(ROOT/'build'),'-I'+str(ROOT/'experiments/ghost-c1'),*map(str,files),'-lm','-o',str(exe)],check=True)
with (OUT/'validation/policy-test.log').open('w') as log:subprocess.run([str(exe)],stdout=log,stderr=subprocess.STDOUT,check=True)
print('PASS32 policy cases:20/60/120/400BPM, budgets, independence, transport stop')
