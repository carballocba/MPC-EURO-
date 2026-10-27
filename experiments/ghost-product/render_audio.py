#!/usr/bin/env python3
"""Render complete factory examples from the final native VST; offline, no MIDI required."""
import hashlib,importlib.util,json,pathlib,sys
from build import ROOT,DEFAULT
sys.path[:0]=[str(ROOT/'experiments/ghost-c1'),str(ROOT/'tests')]
from test_vst import FX
s=importlib.util.spec_from_file_location('audio_reference',ROOT/'experiments/ghost-c12-2/render_audio_demo.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
out=DEFAULT/'audio';out.mkdir(exist_ok=True);left,right=m.drum_loop(seconds=4)
m.write_wav(out/'00-dry-input.wav',(left,right),44100)
rows=[]
for program in range(8,16):
 f=FX(DEFAULT/'engine/ghost-identity-test.so')
 try:
  f.d(f.fx,2,0,program,None,0);a,b=m.process(f,left,right)
  peak=max(max(map(abs,a)),max(map(abs,b)));assert peak<1
  path=out/f'{program:02d}-factory.wav';m.write_wav(path,(a,b),44100)
  difference=(sum((x-y)**2 for x,y in zip(left,a))/len(left))**.5
  rows.append({'program':program,'file':path.name,'peak':peak,'dry_difference_rms':difference,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source':'synthetic deterministic stereo drum loop','hardware':False})
 finally:f.close()
(out/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
