#!/usr/bin/env python3
"""True native VST renders of a synthetic electric-piano60BPM fixture (not a recording of Rhodes)."""
import ctypes as C,hashlib,json,math,pathlib,struct,sys,wave
from generate import ROOT,OUT
sys.path[:0]=[str(ROOT/'experiments/ghost-c1'),str(ROOT/'tests')]
from test_vst import FX
from test_ghost_functional_audit import signal
RATE=44100

def render(g,c,variant=0):
 f=FX(OUT/'native/ghost.so');a=[];dry=[]
 try:
  for p,v in [(132,g),(133,c),(134,math.log(125/8)/math.log(50)),(53,.75),(33,.1),(77,.8),(79,(250-.1)/(60000-.1)),(135,.5),(136,.45),(137,.05)]:f.set(f.fx,p,v)
  for _ in range(variant):f.set(f.fx,141,1)
  for k in range(0,RATE*12,128):
   x=[]
   for j in range(min(128,RATE*12-k)):
    t=(k+j)/RATE;age=t%2;chord=[130.8128,164.8138,195.9977] if int(t/4)%2==0 else [110,130.8128,164.8138]
    x.append(sum(.07*math.exp(-age*1.8)*(math.sin(2*math.pi*hz*t)+.18*math.exp(-age*3)*math.sin(2*math.pi*hz*4*t)) for hz in chord))
   dry+=x;a+=signal(f,x)
 finally:f.close()
 return a,dry

def main():
 folder=OUT/'audio';folder.mkdir(exist_ok=True);rows=[]
 for name,g,c,variant in [('clean',0,1,0),('low-glitch-low-chaos',.18,0,0),('low-glitch-high-chaos',.18,1,0),('high-glitch-low-chaos',.85,0,0),('high-glitch-high-chaos',.85,1,0),('dice-variation-1',.85,1,1)]:
  a,b=render(g,c,variant);repeat,_=render(g,c,variant);assert a==repeat;assert all(math.isfinite(x) and abs(x)<1 for x in a)
  raw=b''.join(struct.pack('<h',round(x*32767)) for x in a);path=folder/(name+'.wav')
  with wave.open(str(path),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(raw)
  rows.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),peak=max(map(abs,a)),rms_difference=math.sqrt(sum((x-y)**2 for x,y in zip(a,b))/len(a)),seconds=12,glitch=g,chaos=c,variant=variant,repeat_bit_exact=True,native_binary_sha256=hashlib.sha256((OUT/'native/ghost.so').read_bytes()).hexdigest(),source='synthetic electric-piano fixture at60BPM / real native VST processing / not hardware'))
 (folder/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
