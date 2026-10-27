#!/usr/bin/env python3
"""Before/after actual native VST evidence; synthetic nonperiodic stereo material."""
import pathlib,sys,json,hashlib,struct,wave,ctypes as C,subprocess
from generate import ROOT,OUT
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'experiments/ghost-c1')]
from test_ghost_live_repeat_fix import initialize,process,source,probe,P,OLD
D=ROOT/'build/ghost-live-repeat-fix';D.mkdir(exist_ok=True,parents=True)
def main():
 rows=[]
 for label,path in [('before',OLD),('after',P)]:
  if len(sys.argv)>1 and sys.argv[1]!=label:continue
  f=initialize(path,size=.5)
  try:
   first=process(f,*source(22050));start=probe(f);tail=process(f,[0.]*(44100*10),[0.]*(44100*10));end=probe(f);n=int(end[5]);pcm=b''.join(struct.pack('<hh',round(max(-1,min(1,l))*32767),round(max(-1,min(1,r))*32767)) for l,r in zip(first[0]+tail[0],first[1]+tail[1]))
   with wave.open(str(D/(label+'.wav')),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(44100);w.writeframes(pcm)
   a=tail[0][-n:];b=tail[0][-2*n:-n];rows.append(dict(candidate=label,binary_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),voice_before=start[3:6],voice_after=end[3:6],pinned=end[0]!=end[3],last_second_energy=sum(v*v for v in tail[0][-44100:]),period_max_delta=max(abs(x-y) for x,y in zip(a,b)),last_period_sha256=hashlib.sha256(struct.pack('<%sf'%len(a),*a)).hexdigest(),previous_period_sha256=hashlib.sha256(struct.pack('<%sf'%len(b),*b)).hexdigest(),pcm_sha256=hashlib.sha256(pcm).hexdigest()))
  finally:f.close()
 if len(sys.argv)>1:
  print(json.dumps(rows[0]));return
 assert rows[1]['last_second_energy']>.01
 assert rows[1]['last_period_sha256']==rows[1]['previous_period_sha256']
 (D/'repeat-evidence.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
if __name__=='__main__':
 if len(sys.argv)>1:main()
 else:
  rows=[json.loads(subprocess.check_output([sys.executable,__file__,label])) for label in ['before','after']]
  assert rows[0]['last_second_energy']==0 and rows[1]['last_second_energy']>.01
  assert rows[1]['last_period_sha256']==rows[1]['previous_period_sha256']
  (D/'repeat-evidence.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
