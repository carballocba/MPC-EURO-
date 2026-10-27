#!/usr/bin/env python3
"""Reproducible synthetic audio, all sixteen real VST programs and reverse proof."""
import importlib.util,json,pathlib,sys
from build import ROOT,sha
sys.path[:0]=[str(ROOT/'experiments/ghost-c1'),str(ROOT/'tests')]
from test_vst import FX
from test_ghost_functional_audit import signal,tick
s=importlib.util.spec_from_file_location('reference_audio',ROOT/'experiments/ghost-c12-2/render_audio_demo.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
out=ROOT/'build/ghost-functional-final';folder=out/'audio';folder.mkdir(exist_ok=True);left,right=m.drum_loop(seconds=4);m.write_wav(folder/'dry-input.wav',(left,right),44100);rows=[]
for program in range(16):
 f=FX(out/'engine/ghost-identity-test.so')
 try:
  f.d(f.fx,2,0,program,None,0)
  if program<8:f.set(f.fx,1,1) # explicit audition only; preset itself remains unchanged
  a,b=m.process(f,left,right);peak=max(max(map(abs,a)),max(map(abs,b)));assert peak<1
  file=folder/f'{program:02d}-factory.wav';m.write_wav(file,(a,b),44100)
  rows.append({'program':program,'file':file.name,'peak':peak,'sha256':sha(file.read_bytes()),'source':'deterministic synthetic drums','activation':'Gate ON for audition' if program<8 else 'factory defaults','hardware':False})
 finally:f.close()
proof=[]
for name,path,reverse in [('reverse-before',ROOT/'build/ghost-product-final/engine/ghost-identity-test.so',1),('forward-after',out/'engine/ghost-identity-test.so',0),('reverse-after',out/'engine/ghost-identity-test.so',1)]:
 f=FX(path)
 try:
  f.d(f.fx,2,0,0,None,0);tick(f)
  for p,v in [(25,0),(0,.3),(9,0),(15,.5),(16,.5),(17,0),(18,1),(19,0),(20,0),(53,1),(14,reverse)]:f.set(f.fx,p,v)
  for k in range(400):signal(f,[.05+(k*128+j)*.000002 for j in range(128)])
  f.set(f.fx,10,1);tick(f,1);f.set(f.fx,11,1)
  for k in range(15):signal(f,[0]*128)
  a=signal(f,[0]*1024);delta=[b-a for a,b in zip(a,a[1:]) if .0000001<abs(b-a)<.00001]
  proof.append({'case':name,'peak':max(map(abs,a)),'linear_samples':len(delta),'mean_sample_step':sum(delta)/len(delta) if delta else 0,'expected_step':(-1 if reverse else 1)*.000002})
 finally:f.close()
(folder/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n');(out/'reverse-before-after.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
