#!/usr/bin/env python3
"""Deterministic audio through the real native VST, including record/commit/LIVE."""
import ctypes as C,hashlib,json,math,pathlib,struct,sys,wave
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'build/ghost-buffer-engine-final';sys.path[:0]=[str(ROOT/'experiments/ghost-c1'),str(ROOT/'tests')]
from test_vst import FX
from test_ghost_functional_audit import signal
RATE=44100

def render(mode):
 f=FX(OUT/'ghost-identity-test.so');audio=[];dry=[]
 try:
  f.d(f.fx,2,0,0,None,0)
  for p,v in [(48,0),(25,0),(0,.35),(9,0),(53,1),(1,0),(11,0),(14,0),(49,0),(54,0),(18,1),(34,.2),(75,.3)]:f.set(f.fx,p,v)
  for block in range((RATE*5+127)//128):
   t0=block*128
   if block==180:
    if mode=='live-reverse':f.set(f.fx,14,1)
    if mode=='live-repeat':f.set(f.fx,128,1)
    if mode in ('capture-held','capture-half-mix'):f.set(f.fx,126,1)
   if block==420 and mode.startswith('capture'):
    f.set(f.fx,126,0);f.set(f.fx,14,1)
    if mode=='capture-half-mix':f.set(f.fx,53,.5)
   if block==1000 and mode.startswith('capture'):f.set(f.fx,56,1)
   x=[]
   for j in range(min(128,RATE*5-t0)):
    t=(t0+j)/RATE;p=t%.25
    kick=.35*math.exp(-p*42)*math.sin(2*math.pi*(56*p+26*(1-math.exp(-p*25))))
    hat=.06*math.exp(-(t%.125)*150)*math.sin(2*math.pi*6200*t)
    x.append(kick+hat+.07*math.sin(2*math.pi*(170+18*math.sin(t))*t))
   dry+=x;audio+=signal(f,x)
 finally:f.close()
 return audio,dry

def main():
 folder=OUT/'audio';folder.mkdir(exist_ok=True);rows=[]
 for mode in ('transparent','live-reverse','live-repeat','capture-held','capture-half-mix'):
  a,b=render(mode);a2,_=render(mode);assert a==a2,'Nondeterminism '+mode
  raw=b''.join(struct.pack('<h',round(max(-1,min(1,x))*32767)) for x in a)
  path=folder/(mode+'.wav')
  with wave.open(str(path),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(raw)
  rows.append({'mode':mode,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'peak':max(map(abs,a)),'rms_difference_from_dry':math.sqrt(sum((x-y)**2 for x,y in zip(a,b))/len(a)),'repeat_render_bit_exact':True,'engine':'actual native VST; not ARM/hardware','seconds':5})
 (folder/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
