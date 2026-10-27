#!/usr/bin/env python3
"""Separate-process native factory audio comparison, avoiding dyld symbol interposition."""
import sys,json,hashlib,struct,subprocess
from generate import ROOT
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'experiments/ghost-c1')]
from test_ghost_live_repeat_fix import FX,process,source,P,OLD
D=ROOT/'build/ghost-live-repeat-fix'
def worker(path):
 rows=[]
 for program in range(16):
  f=FX(path)
  try:
   f.d(f.fx,2,0,program,None,0);f.block();out=process(f,*source(44100));raw=b''.join(struct.pack('<%df'%len(a),*a) for a in out);rows.append(hashlib.sha256(raw).hexdigest())
  finally:f.close()
 print(json.dumps(rows))
if __name__=='__main__':
 if len(sys.argv)>1:worker(OLD if sys.argv[1]=='old' else P)
 else:
  old,new=[json.loads(subprocess.check_output([sys.executable,__file__,k])) for k in ['old','new']];assert old==new
  (D/'factory-compat.json').write_text(json.dumps(dict(original_programs=16,old_audio_sha256=old,new_audio_sha256=new,bit_exact=True,process_isolation=True),indent=2)+'\n');print('PASS16 factory programs bit-exact in isolated processes')
