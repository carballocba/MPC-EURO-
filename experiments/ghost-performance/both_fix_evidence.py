#!/usr/bin/env python3
"""Isolated native comparison of installed BOTH and corrected policy. Never connects to hardware."""
import pathlib,sys,json,struct,hashlib,subprocess,wave,math
from generate import ROOT,OUT
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'experiments/ghost-c1')]
from test_ghost_live_repeat_fix import FX,process,source,probe
from test_ghost_random_repeat import rrstats
from test_ghost_final_integration import stats as pe_stats
D=ROOT/'build/ghost-both-fix'
def render(path,mode,program=0,seconds=16,redundant=False,controls=()):
 f=FX(path);f.d(f.fx,2,0,program,None,0);f.block();f.set(f.fx,53,1)
 for p,v in controls:f.set(f.fx,p,v)
 process(f,*source(44100));f.set(f.fx,148,mode);trace=[];out=[[],[]];dry=source(44100*seconds)
 for k in range(0,len(dry[0]),128):
  if redundant:f.set(f.fx,148,mode)
  a=process(f,dry[0][k:k+128],dry[1][k:k+128]);out[0]+=a[0];out[1]+=a[1];s=rrstats(f);p=probe(f)
  trace.append([k,int(s[5]),int(s[3]),s[4],int(p[5])])
 final=rrstats(f);f.close();return out,trace,final

def worker(which):
 path=D/'reference/native.so' if which=='before' else OUT/'native/ghost.so';rows=[]
 for name,mode in [('independent',1/3),('performance',2/3),('both',1)]:
  out,trace,stats=render(path,mode);raw=b''.join(struct.pack('<%df'%len(ch),*ch) for ch in out);row=dict(case=name,stats=stats,float_audio_sha256=hashlib.sha256(raw).hexdigest(),active_lengths=sorted({r[4] for r in trace if r[2]}),finite=all(math.isfinite(x) and abs(x)<1 for ch in out for x in ch))
  (D/(which+'-'+name+'-trace.json')).write_text(json.dumps(trace)+'\n')
  with wave.open(str(D/(which+'-'+name+'.wav')),'wb') as w:
   w.setnchannels(2);w.setsampwidth(2);w.setframerate(44100);w.writeframes(b''.join(struct.pack('<hh',round(a*32767),round(b*32767)) for a,b in zip(*out)))
  rows.append(row)
 # Fixed-buffer continuous control sequence: all16 existing programs, RR disabled.
 factory=[]
 for i in range(16):
  f=FX(path);f.d(f.fx,2,0,i,None,0);f.block();a=process(f,*source(22050));factory.append(hashlib.sha256(b''.join(struct.pack('<%df'%len(ch),*ch) for ch in a)).hexdigest());f.close()
 compatibility=[]
 for mode in [1/3,2/3]:
  for program,seed,rate in [(0,.13,1),(5,.731,.2),(12,.42,.6)]:
   a,_,s=render(path,mode,program=program,seconds=4,controls=[(75,seed),(149,.9),(150,1),(151,.8),(152,rate)])
   compatibility.append(dict(mode=mode,program=program,seed=seed,audio_sha256=hashlib.sha256(b''.join(struct.pack('<%df'%len(ch),*ch) for ch in a)).hexdigest(),stats=s))
 f=FX(path);f.set(f.fx,148,1);process(f,*source(44100*4));performance_events=pe_stats(f)[0];f.close()
 print(json.dumps(dict(binary_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),cases=rows,factory_audio_sha256=factory,compatibility_matrix=compatibility,both_performance_events=performance_events)))
def main():
 reports={which:json.loads(subprocess.check_output([sys.executable,__file__,which])) for which in ['before','after']}
 before,after=reports['before'],reports['after']
 for i in [0,1]:assert before['cases'][i]['float_audio_sha256']==after['cases'][i]['float_audio_sha256'],['INDEPENDENT','PERFORMANCE'][i]+' changed'
 assert before['factory_audio_sha256']==after['factory_audio_sha256'];assert before['compatibility_matrix']==after['compatibility_matrix'];assert after['both_performance_events']>0;assert after['cases'][2]['stats'][0]>before['cases'][2]['stats'][0];assert len(after['cases'][2]['active_lengths'])>2
 reports.update(independent_bit_exact=True,performance_bit_exact=True,factory16_bit_exact=True,signal='identical synthetic stereo input; native only',device_access=False)
 (D/'comparison.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports,indent=2))
if __name__=='__main__':
 if len(sys.argv)>1:worker(sys.argv[1])
 else:main()
