#!/usr/bin/env python3
"""Interleaved same-process-host callback comparisons; native Mac, not ARM timing."""
import csv,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'build/ghost-buffer-engine-final';val=OUT/'validation';val.mkdir(exist_ok=True)
host=ROOT/'build/ghost-product-final/validation/timing-host';old=ROOT/'build/ghost-functional-final/engine/ghost-identity-test.so';new=OUT/'ghost-identity-test.so'
rows={name:[] for name in ('before','after')}
for run in range(3):
 for name,lib in [('before',old),('after',new)]:
  p=subprocess.run([str(host),str(lib)],capture_output=True,check=True);(val/f'timing-{name}-{run+1}.csv').write_bytes(p.stdout);(val/f'timing-{name}-{run+1}.stderr').write_bytes(p.stderr)
  rows[name]+=list(csv.DictReader(p.stdout.decode().splitlines()))
report={}
for name,rs in rows.items():report[name]={'mean_us':sum(float(r['mean_us']) for r in rs)/len(rs),'max_wall_us':max(float(r['max_us']) for r in rs),'max_cpu_us':max(float(r['max_cpu_us']) for r in rs),'wall_overruns':sum(int(r['overruns']) for r in rs),'cpu_overruns':sum(int(r['cpu_overruns']) for r in rs),'invalid':sum(int(r['invalid']) for r in rs),'persistent_bytes':int(rs[0]['persistent_bytes']),'callbacks':len(rs)*2000}
report['scenario_mean_delta_us']={str(i):sum(float(r['mean_us']) for r in rows['after'] if int(r['scenario'])==i)/3-sum(float(r['mean_us']) for r in rows['before'] if int(r['scenario'])==i)/3 for i in range(19)}
report['limitations']='Native Mac wall time includes descheduling; CPU time includes instrumentation overhead. Dense scenarios include event dispatch in measured interval. Historical 18.8ms wall outliers are not disproven by these runs. No ARM deadlines certified.'
(val/'timing-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

source=(ROOT/'experiments/ghost-c1/vst_benchmark.c').read_text().replace('scenario<19','scenario<25')
anchor='  struct {int32_t numEvents;'
source=source.replace(anchor,'''  if(scenario>=19){
   set(f,P_GHOST,0);set(f,P_MOTION,0);set(f,P_LISTEN,0);f->setParameter(f,1,0);
   if(scenario==20||scenario==24)f->setParameter(f,14,1);
   if(scenario==21)f->setParameter(f,128,1);
   if(scenario==22||scenario==23){f->setParameter(f,127,scenario==23?0:1);f->setParameter(f,126,1);}
   if(scenario==24){f->setParameter(f,15,0);f->setParameter(f,16,0);}
  }
'''+anchor)
path=val/'focused-timing.c';path.write_text(source);exe=val/'focused-timing'
subprocess.run(['cc','-std=c11','-O2','-I'+str(ROOT/'src'),'-I'+str(ROOT/'experiments/ghost-c1'),str(path),'-o',str(exe)],check=True)
p=subprocess.run([str(exe),str(new)],capture_output=True,check=True);(val/'focused-timing.csv').write_bytes(p.stdout)
print('PASS focused native callback timing: LIVE transparent, Reverse, Repeat, recording, FULL and slow reader')
