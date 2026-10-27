#!/usr/bin/env python3
"""Reproducible offline A/B: low, 250 ms silence, high; no hardware access."""
import hashlib,json,pathlib,struct,sys,wave
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tests'))
from test_ghost_control_recovery import render,rmsdiff
OUT=ROOT/'build/ghost-control-recovery/audio';OUT.mkdir(exist_ok=True)
report={}
for name,common,p in [('density',[(49,1),(1,0)],76),('chaos',[(49,1),(104,1),(76,.5)],55),('motion-depth',[(1,1),(91,1),(54,1)],70)]:
 a,_,_=render(common+[(p,0)]);b,_,_=render(common+[(p,1)])
 data=a+[0.0]*11025+b;assert max(map(abs,data))<1
 path=OUT/(name+'-low-then-high.wav')
 with wave.open(str(path),'wb') as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(44100);w.writeframes(b''.join(struct.pack('<h',round(x*32767)) for x in data))
 report[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'difference_rms':rmsdiff(a,b),'seed':1,'order':'3 s low / 0.25 s silence / 3 s high','source':'synthetic deterministic drum-like test input; left output channel','hardware':False}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
