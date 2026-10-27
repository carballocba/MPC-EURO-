#!/usr/bin/env python3
import pathlib,subprocess,os,hashlib,shutil
r=pathlib.Path(__file__).resolve().parent;out=r/'rebuild';out.mkdir(exist_ok=True)
zig=os.environ.get('ZIG') or shutil.which('zig')
if not zig:raise SystemExit('Set ZIG to the Zig0.13.0 executable; see tools/zig-requirements.txt')
assert subprocess.check_output([zig,'version'],text=True).strip()=='0.13.0'
src=r/'build/ghost-performance-edition/source'
flags=[zig,'cc','-target','arm-linux-gnueabihf.2.31','-mcpu=cortex_a9','-std=c11','-O2','-ffp-contract=off','-fPIC','-DGHOST_STANDALONE_UID=0x47485354','-DGHOST_FINAL_PRODUCT=1','-DGHOST_BUFFER_ENGINE=1','-I'+str(src),'-I'+str(r/'src'),'-I'+str(r/'build'),'-I'+str(r/'experiments/ghost-c1'),'-fvisibility=hidden']
sources=[src/n for n in ['core.c','motion.c','params.c','state.c','vst.c','base.c','engine.c','performance.c']]+[r/'experiments/ghost/ghost.c',r/'src/repeat.c'];objects=[]
for i,p in enumerate(sources):
 o=out/('unit-%d.o'%i);subprocess.run(flags+['-c',str(p),'-o',str(o)],check=True);objects.append(str(o))
p=out/'ghost.so';subprocess.run(flags+['-shared',*objects,'-lm','-pthread','-o',str(p),'-Wl,--no-undefined','-Wl,--strip-debug','-Wl,--version-script='+str(r/'src/exports.map')],check=True)
h=hashlib.sha256(p.read_bytes()).hexdigest();print(h);assert h=='588019130b31ced7077f7e4afe35bd23b0753df7a2959e2af39fa825e1b81afd'
