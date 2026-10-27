#!/usr/bin/env python3
"""Reproducible musical fixtures through the actual native VST; no hardware claims."""
import hashlib,json,math,pathlib,struct,sys,wave
from generate import ROOT,OUT
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'experiments/ghost-c1')]
from test_ghost_final_integration import FX,COMMON,RANDOM,MOTION,setup
from test_ghost_functional_audit import signal
RATE=44100
CASES=[('manual-repeat',[(131,0),(128,1),(0,.1)],[]),('manual-reverse',[(131,0),(14,1)],[]),
 ('evolution-0',[(139,0)],[]),('evolution-low',[(139,.15)],[]),('evolution-mid',[(139,.5)],[]),('evolution-high',[(139,1)],[]),
 ('random-run',RANDOM+[(61,1)],[]),('motion-run',MOTION+[(54,1)],[]),
 ('dice-run',[(139,.5)],[(2.,141,1)]),
 ('hybrid',RANDOM+MOTION+[(61,1),(54,1),(139,1),(32,0)],[(1.,12,.7),(1.5,11,1),(2.,11,0),(2.5,126,1),(3.,126,0),(3.5,61,0),(4.,54,0),(4.3,33,.3),(5.,56,1),(5.3,4,1)])]
def render(values,events):
 f=FX(OUT/'native/ghost.so');out=[];dry=[];k_event=0
 try:
  setup(f,COMMON+values)
  for k in range(0,RATE*6,128):
   while k_event<len(events) and k/RATE>=events[k_event][0]:_,p,v=events[k_event];f.set(f.fx,p,v);k_event+=1
   data=[]
   for j in range(min(128,RATE*6-k)):
    t=(k+j)/RATE;beat=t%.5;snare=(t-.5)%1;hat=t%.125;noise=(((k+j)*1103515245+12345)&65535)/32768-1
    data.append(.3*math.exp(-beat*35)*math.sin(2*math.pi*(55*beat+25*(1-math.exp(-beat*30))))+.11*math.exp(-snare*70)*noise+.045*math.exp(-hat*200)*noise+.025*math.sin(2*math.pi*131*t))
   dry+=data;out+=signal(f,data)
  s=(__import__('ctypes').c_uint64*6)();f.lib.ghost_pe_stats.argtypes=[__import__('ctypes').c_void_p,__import__('ctypes').POINTER(__import__('ctypes').c_uint64)];f.lib.ghost_pe_stats(f.fx,s)
  return out,dry,list(s)
 finally:f.close()
def main():
 folder=OUT/'audio/final';folder.mkdir(parents=True,exist_ok=True);rows=[]
 for name,values,events in CASES:
  out,dry,counts=render(values,events);again,_,counts2=render(values,events);assert out==again and counts==counts2
  assert all(math.isfinite(x) and abs(x)<1 for x in out)
  path=folder/(name+'.wav')
  with wave.open(str(path),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(b''.join(struct.pack('<h',round(x*32767)) for x in out))
  rows.append(dict(case=name,seconds=6,settings=values,actions=events,events=counts[0],active_frames=counts[1],peak=max(map(abs,out)),rms_from_dry=math.sqrt(sum((a-b)**2 for a,b in zip(out,dry))/len(out)),max_adjacent_delta=max(abs(a-b) for a,b in zip(out,out[1:])),bit_exact_repeat=True,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 report=dict(fixture='synthetic musical drum/tonal loop; NOT a recorded performance or MPC audio',native_sha256=hashlib.sha256((OUT/'native/ghost.so').read_bytes()).hexdigest(),cases=rows,device_access=False)
 (folder/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
