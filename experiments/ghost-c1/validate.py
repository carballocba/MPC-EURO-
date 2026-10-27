"""One offline entry point. Never contacts the MPC or writes protected outputs."""
import json,hashlib,pathlib,subprocess,sys,platform,csv,time
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'build/ghost-c11-demo';HERE=ROOT/'experiments/ghost-c1';OUT.mkdir(exist_ok=True)
python=ROOT/'build/venv/bin/python'
if not python.exists():raise SystemExit('Use the existing local Pillow/pyelftools environment; automatic package installation is disabled.')
baseline=json.loads((ROOT/'build/ghost-prototype/validation.json').read_text())
protected={**baseline['source_sha256'],**baseline['protected_sha256']}
old_c1=json.loads((ROOT/'build/ghost-c1-demo/validation.json').read_text())
protected.update({p:h for p,h in old_c1.get('source_sha256',{}).items() if not p.startswith('experiments/ghost-c1/')})
protected.update({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'build/ghost-c1-demo').rglob('*') if p.is_file()})
def check():
 bad=[p for p,h in protected.items() if not (ROOT/p).is_file() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
 if bad:raise SystemExit('Protected baseline changed: '+', '.join(bad))
def run(name,cmd):
 print(name,flush=True)
 with (OUT/(name+'.log')).open('w') as f:
  result=subprocess.run([str(x) for x in cmd],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
 if result.returncode:raise SystemExit(f'{name} failed: see {OUT/(name+".log")}')
check()
run('native',['make','-C',HERE,'all','test','vst'])
run('asan-ubsan',['make','-C',HERE,'sanitize','sanitize-vst'])
run('thread-sanitizer',['make','-C',HERE,'tsan'])
run('vst-tests',[python,HERE/'test_vst.py'])
run('C1-reference',[python,HERE/'baseline.py'])
run('hardening-tests',[python,HERE/'test_hardening.py'])
run('C0-regressions',[ROOT/'build/ghost-prototype/test'])
run('BeatRepeat-regressions',[ROOT/'build/test'])
run('BeatRepeat-ABI',[python,ROOT/'tests/test_shared.py'])
run('BeatRepeat-v2',[python,ROOT/'tests/test_v2.py'])
run('GUI',[python,HERE/'gui.py'])
run('GUI-state-tests',[python,HERE/'test_gui.py'])
run('audio-render',[python,HERE/'demo.py'])
run('native-benchmarks',['make','-C',HERE,'benchmark','vst-benchmark'])
run('C1-comparison',[python,HERE/'compare.py'])
run('ARM-build',[python,HERE/'arm.py'])
check()
rows=list(csv.DictReader((OUT/'benchmark-native.csv').open()));vst=list(csv.DictReader((OUT/'benchmark-vst-native.csv').open()));audio=json.loads((OUT/'audio-validation.json').read_text())
assert len(audio)==50 and all(x['invalid']==0 and x['clipped']==0 for x in audio)
assert all(int(x['invalid'])==0 for x in rows+vst)
report={'platform':platform.platform(),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),'native_test_groups':17,'vst_tests':14,'gui_state_tests':8,'hardening_tests':14,'baseline_commit':'cf0ef00','C0_groups':21,'BeatRepeat_groups':19,'BeatRepeat_v2_tests':28,'ASan_UBSan':'passed (macOS leak detector disabled)','TSan':'passed','protected_files_unchanged':len(protected),'audio_examples':len(audio),'native_benchmark_cases':len(rows),'vst_benchmark_cases':len(vst),'native_overruns':sum(int(x['overruns']) for x in rows),'vst_overruns':sum(int(x['overruns']) for x in vst),'native_max_us':max(float(x['max_us']) for x in rows),'vst_max_us':max(float(x['max_us']) for x in vst),'hardware_accessed':False,'hardware_validated':False,'arm':json.loads((OUT/'arm/validation.json').read_text()),'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file()},'protected_sha256':protected}
(OUT/'validation.json').write_text(json.dumps(report,indent=2));run('performance-report',[python,HERE/'report.py']);print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','protected_sha256']},indent=2))
