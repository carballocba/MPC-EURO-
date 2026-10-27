#!/usr/bin/env python3
"""Actual native stereo renders and real region/gate traces, no device access."""
import pathlib,sys,struct,wave,json,hashlib,subprocess,ctypes as C,math
from generate import ROOT,OUT
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'experiments/ghost-c1')]
from test_ghost_random_repeat import setup,rrstats
from test_ghost_live_repeat_fix import process,source,probe,FX
D=ROOT/'build/ghost-random-repeat';D.mkdir(parents=True,exist_ok=True)
def render(mode):
 f=setup(mode);out=[[],[]];trace=[];dry=source(44100*8)
 try:
  for k in range(0,len(dry[0]),128):
   a=process(f,dry[0][k:k+128],dry[1][k:k+128]);out[0]+=a[0];out[1]+=a[1];p=probe(f);trace.append([k,f.get(f.fx,154),p[3],p[4],p[5],rrstats(f)[4]])
  return out,dry,trace,rrstats(f)
 finally:f.close()
def manual(path):
 f=FX(path);f.d(f.fx,2,0,0,None,0);f.block()
 try:
  for p,v in [(131,0),(48,0),(53,1),(9,0),(17,0),(15,.5),(16,.5),(18,1)]:f.set(f.fx,p,v)
  process(f,*source(44100));audio=[[],[]]
  for p,v in [(128,1),(134,.1),(134,.8),(128,0),(14,1),(14,0),(128,1)]:
   f.set(f.fx,p,v);a=process(f,*source(11025));audio[0]+=a[0];audio[1]+=a[1]
  print(hashlib.sha256(b''.join(struct.pack('<%df'%len(a),*a) for a in audio)).hexdigest())
 finally:f.close()
def main():
 rows=[]
 for name,mode in [('independent',1/3),('performance',2/3),('both',1)]:
  out,dry,trace,s=render(mode);again,_,_,t=render(mode);assert out==again and s==t
  assert all(math.isfinite(x) and abs(x)<1 for ch in out for x in ch)
  pcm=b''.join(struct.pack('<hh',round(l*32767),round(r*32767)) for l,r in zip(*out))
  with wave.open(str(D/(name+'.wav')),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(44100);w.writeframes(pcm)
  lengths=sorted({int(x[4]) for x in trace if x[1]>.5});row=dict(mode=name,stats=s,actual_region_lengths=lengths,bit_exact_repeat=True,pcm_sha256=hashlib.sha256(pcm).hexdigest(),rms_delta=math.sqrt(sum((a-b)**2 for a,b in zip(out[0],dry[0]))/len(out[0])))
  if name=='independent':
   assert len(lengths)>2
   rests=[];active=[];run=0;last=None
   for k,state,*_ in trace:
    run=run+1 if state==last else 1;last=state
    if run>=8:
     delta=sum((a-b)**2 for a,b in zip(out[0][k:k+128],dry[0][k:k+128]))
     (active if state>.5 else rests).append(delta)
   assert rests and max(rests)<1e-10;assert active and max(active)>.01
   row.update(stable_rest_max_squared_delta=max(rests),active_max_squared_delta=max(active))
  rows.append(row);(D/(name+'-trace.json')).write_text(json.dumps(trace)+'\n')
 old=subprocess.check_output([sys.executable,__file__,'old']).decode().strip();new=subprocess.check_output([sys.executable,__file__,'new']).decode().strip();assert old==new
 report=dict(cases=rows,manual_reference_and_new_bit_exact=True,manual_sha256=new,native_sha256=hashlib.sha256((OUT/'native/ghost.so').read_bytes()).hexdigest(),signal='synthetic nonperiodic stereo, not MPC recording',device_access=False)
 (D/'audio-evidence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
 if len(sys.argv)>1:manual(ROOT/'build/ghost-random-repeat/reference/native.so' if sys.argv[1]=='old' else OUT/'native/ghost.so')
 else:main()
