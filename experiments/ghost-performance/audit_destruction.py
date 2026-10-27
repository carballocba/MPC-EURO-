#!/usr/bin/env python3
"""Audible existing DSP: deterministic synthetic drums, no new audio algorithm or device."""
import hashlib,json,math,pathlib,struct,sys,wave
from generate import ROOT,OUT
sys.path[:0]=[str(ROOT/'experiments/ghost-c1'),str(ROOT/'tests')]
from test_vst import FX
from test_ghost_functional_audit import signal
RATE=44100
CASES=[('dry',[(53,0)]),('repeat',[(128,1),(0,.02)]),('reverse',[(14,1)]),('stutter',[(128,1),(9,.95)]),('corrupt',[(128,1),(17,1)]),('pitch-jump',[(128,1),(16,.9)]),('bend-rate',[(128,1),(15,1),(19,1)]),('performance-extreme',[(131,1),(132,1),(133,1),(134,.15),(135,.5),(136,.3),(137,.2),(139,.75),(17,.65),(77,1),(79,.01),(138,.15)])]
def render(settings):
 f=FX(OUT/'native/ghost.so');out=[];dry=[]
 try:
  for p,v in [(48,0),(131,0),(53,1),(127,1),(34,.234),(75,.234),*settings]:f.set(f.fx,p,v)
  for k in range(0,RATE*6,128):
   data=[]
   for j in range(min(128,RATE*6-k)):
    t=(k+j)/RATE;beat=t%.5;snare=(t-.5)%1;hat=t%.125
    # Deterministic asymmetric impulses/harmonics expose reversal and corruption.
    noise=(((k+j)*1103515245+12345)&65535)/32768-1
    data.append(.3*math.exp(-beat*35)*math.sin(2*math.pi*(55*beat+25*(1-math.exp(-beat*30))))+.11*math.exp(-snare*70)*noise+.045*math.exp(-hat*200)*noise+.025*math.sin(2*math.pi*131*t))
   dry+=data;out+=signal(f,data)
 finally:f.close()
 return out,dry

def main():
 folder=OUT/'audio/glitch-audit';folder.mkdir(parents=True,exist_ok=True);rows=[]
 for name,settings in CASES:
  out,dry=render(settings);again,_=render(settings);assert out==again;assert all(math.isfinite(x) and abs(x)<1 for x in out)
  rms=math.sqrt(sum((a-b)**2 for a,b in zip(out,dry))/len(out));assert rms<1e-8 if name=='dry' else rms>.002,(name,rms)
  p=folder/(name+'.wav')
  with wave.open(str(p),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(b''.join(struct.pack('<h',round(x*32767)) for x in out))
  rows.append(dict(case=name,settings=settings,rms_difference_from_input=rms,peak=max(map(abs,out)),deterministic=True,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 report=dict(source='synthetic drum loop, actual native VST; NOT MPC validation',seconds=6,cases=rows,native_sha256=hashlib.sha256((OUT/'native/ghost.so').read_bytes()).hexdigest(),device_access=False)
 (folder/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
