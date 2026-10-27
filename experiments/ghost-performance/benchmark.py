#!/usr/bin/env python3
"""Interleaved native callback timing with paired wall/CPU raw samples. Not ARM deadlines."""
import csv,json,os,pathlib,subprocess,hashlib
from generate import ROOT,OUT
val=OUT/'validation/timing-final';val.mkdir(parents=True,exist_ok=True)
source=(ROOT/'experiments/ghost-c1/vst_benchmark.c').read_text()
source=source.replace('for(unsigned scenario=0;scenario<19;','for(unsigned scenario=0;scenario<33;')
source=source.replace('f->setParameter(f,1,1);','f->setParameter(f,131,0);f->setParameter(f,1,1);')
anchor='  struct {int32_t numEvents;'
source=source.replace(anchor,'''  if(scenario>=19){for(unsigned d=0;d<12;++d){f->setParameter(f,60,d/11.f);f->setParameter(f,61,0);}f->setParameter(f,131,1);f->setParameter(f,1,0);f->setParameter(f,49,0);f->setParameter(f,54,0);f->setParameter(f,55,0);f->setParameter(f,92,0);f->setParameter(f,14,0);f->setParameter(f,128,0);
   f->setParameter(f,132,scenario==19?0:scenario==20?.25f:1);f->setParameter(f,133,scenario>=22?1:0);
   f->setParameter(f,139,scenario==23?1:0);if(scenario==24){f->setParameter(f,127,0);f->setParameter(f,126,1);}
  }
  if(scenario>=25){f->setParameter(f,60,4.f/11);f->setParameter(f,64,1);f->setParameter(f,65,1);f->setParameter(f,61,scenario==26?0:1);f->setParameter(f,90,4.f/11);f->setParameter(f,91,1);f->setParameter(f,54,scenario>=26?1:0);f->setParameter(f,139,scenario>=27?1:0);}
  if(scenario>=28){for(unsigned d=0;d<12;++d){set(f,P_DEST,d/11.f);set(f,P_RANDOM,1);set(f,P_MDEST,d/11.f);set(f,P_ROUTE,1);float a[1]={0},b[1]={0};float *i[2]={a,a},*o[2]={b,b};f->processReplacing(f,i,o,1);}}
'''+anchor)
source=source.replace('if(scenario==11)', 'if(scenario==11||scenario==29)').replace('if(scenario==12)', 'if(scenario==12||scenario==30)').replace('if(scenario==13)', 'if(scenario==13||scenario==31)').replace('scenario==16||scenario==17)f->dispatcher','scenario==16||scenario==17||scenario==32)f->dispatcher')
source=source.replace('batch.numEvents=scenario==17?512:63;', 'batch.numEvents=(scenario==17||scenario==32)?512:63;')
source=source.replace('double t[2000],sum=0','double t[2000],paired_cpu[2000],sum=0').replace('double cpu=cpu_now()-cpu_start;cpu_sum','double cpu=cpu_now()-cpu_start;paired_cpu[k]=cpu;cpu_sum')
source=source.replace('  qsort(t,2000', '''  const char *raw_path=getenv("GHOST_TIMING_RAW");if(raw_path){FILE *raw=fopen(raw_path,scenario?"a":"w");if(!raw)return 3;if(!scenario)fprintf(raw,"scenario,iteration,wall_us,cpu_us\\n");for(unsigned k=0;k<2000;++k)fprintf(raw,"%u,%u,%.6f,%.6f\\n",scenario,k,t[k]*1e6,paired_cpu[k]*1e6);fclose(raw);}
  qsort(t,2000''')
path=val/'host.c';path.write_text(source);exe=val/'host';subprocess.run(['cc','-std=c11','-O2','-I'+str(ROOT/'src'),'-I'+str(ROOT/'experiments/ghost-c1'),str(path),'-lm','-o',str(exe)],check=True)
libs={'baseline':ROOT/'build/ghost-final-reference/native.so','performance':OUT/'native/ghost.so'};rows={k:[] for k in libs};raws={k:[] for k in libs}
for run in range(3):
 for name,lib in libs.items():
  raw=val/f'{name}-{run+1}-raw.csv';p=subprocess.run([str(exe),str(lib)],env=dict(os.environ,GHOST_TIMING_RAW=str(raw)),capture_output=True,check=True);(val/f'{name}-{run+1}.csv').write_bytes(p.stdout);(val/f'{name}-{run+1}.stderr').write_bytes(p.stderr);rows[name]+=list(csv.DictReader(p.stdout.decode().splitlines()));raws[name]+=list(csv.DictReader(raw.read_text().splitlines()))
def summarize(name,lo,hi):
 rs=[r for r in rows[name] if lo<=int(r['scenario'])<hi];raw=[r for r in raws[name] if lo<=int(r['scenario'])<hi];peak=max(raw,key=lambda r:float(r['wall_us']));return dict(mean_us=sum(float(r['mean_us']) for r in rs)/len(rs),mean_cpu_us=sum(float(r['mean_cpu_us']) for r in rs)/len(rs),max_wall_us=float(peak['wall_us']),cpu_at_max_wall_us=float(peak['cpu_us']),max_cpu_us=max(float(r['cpu_us']) for r in raw),wall_overruns=sum(int(r['overruns']) for r in rs),cpu_overruns=sum(int(r['cpu_overruns']) for r in rs),invalid=sum(int(r['invalid']) for r in rs),persistent_bytes=int(rs[0]['persistent_bytes']),intervals=len(raw))
report={'baseline_compat':summarize('baseline',0,19),'performance_compat':summarize('performance',0,19),'performance_focused':summarize('performance',19,33),'focused_cases':{str(s):summarize('performance',s,s+1) for s in range(19,33)},'limitations':'Native Mac only. Cases16/17/32 include MIDI dispatch in timed interval; others processReplacing. CPU includes instrumentation. Raw wall/CPU pairs retained. No QEMU or ARM timing. Historical18.8ms outliers remain relevant; no hardware deadline claims.'}
report['binary_inputs_sha256']={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in libs.items()}
report['compat_mean_delta_percent']=100*(report['performance_compat']['mean_cpu_us']/report['baseline_compat']['mean_cpu_us']-1)
(val/'comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
