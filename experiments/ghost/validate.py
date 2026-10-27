#!/usr/bin/env python3
"""Run local-only C0 acceptance, renders and evidence without rebuilding RC1."""
import array, csv, hashlib, json, math, os, pathlib, platform, re, subprocess, sys, wave
ROOT=pathlib.Path(__file__).resolve().parents[2]
HERE=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'build/ghost-prototype'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def run(name,cmd,env=None):
    with (OUT/name).open('w') as f:
        result=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,env=env)
    if result.returncode: raise RuntimeError(f'{name} failed; see {OUT/name}')
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    protected=json.loads((ROOT/'docs/research/PHASE_A_VALIDATION.json').read_text())['protected_artifacts_unchanged']
    for p,h in protected.items():
        if sha(ROOT/p)!=h: raise RuntimeError('Protected baseline differs before test: '+p)
    for action,name in [('test','tests.txt'),('sanitize','sanitizers.txt'),('render','render.txt'),('benchmark','benchmark.txt')]:
        run(name,['make','-C','experiments/ghost',action])
    for name,command in [('beatrepeat-regression-c.txt',['./build/test']),('beatrepeat-regression-vst.txt',[sys.executable,'tests/test_shared.py']),('beatrepeat-regression-v2.txt',[sys.executable,'tests/test_v2.py'])]: run(name,command)
    # Object import audit excludes harness I/O/allocation deliberately outside render.
    banned={'malloc','calloc','realloc','free','open','fopen','read','write','printf','fprintf','pthread_mutex_lock','pthread_join','system','socket'}
    imports={}
    for name,source in [('ghost',HERE/'ghost.c'),('audio',HERE/'audio.c'),('engine',ROOT/'src/engine.c')]:
        obj=OUT/(name+'-audit.o')
        run(name+'-compile.txt',['cc','-std=c11','-O2','-ffp-contract=off','-I'+str(ROOT/'src'),'-I'+str(HERE),'-c',str(source),'-o',str(obj)])
        symbols=subprocess.check_output(['nm','-u',str(obj)],text=True)
        (OUT/(name+'-imports.txt')).write_text(symbols)
        imports[name]=sorted(line.split()[-1].lstrip('_') for line in symbols.splitlines() if line.split())
        if banned.intersection(imports[name]): raise RuntimeError('Prohibited DSP imports: '+name)
    audio={};buffers={}
    for name in ['input','manual','ghost']:
        with wave.open(str(OUT/(name+'.wav')),'rb') as w:
            assert (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())==(2,2,44100,529200)
            data=w.readframes(w.getnframes());buffers[name]=data
        v=array.array('h',data)
        if sys.byteorder!='little':v.byteswap()
        peak=max(abs(x) for x in v)/32768
        audio[name]={'sha256':sha(OUT/(name+'.wav')),'seconds':12,'peak':peak,'rms':math.sqrt(sum(x*x for x in v)/len(v))/32768,'full_scale_samples':sum(abs(x)>=32767 for x in v)}
        assert audio[name]['full_scale_samples']==0
    for name in ['manual','ghost']:
        assert buffers[name]!=buffers['input']
        assert buffers[name][-44100*4:]==buffers['input'][-44100*4:], 'Clean did not return to exact dry'
    assert buffers['ghost'][:44100*4]==buffers['input'][:44100*4]
    events=list(csv.DictReader((OUT/'events.csv').open()))
    acquired=sum(int(x['capture_result'])==2 for x in events)
    frozen=sum(int(x['auto_freeze']) for x in events)
    assert acquired>0 and frozen>0
    assert len({x['length_ms'] for x in events if int(x['flags'])&1})>3
    assert len({x['break'] for x in events if int(x['flags'])&1})>3
    assert all(float(x['seconds'])<=10.01 for x in events)
    benchmark=json.loads((OUT/'benchmark-native.json').read_text());assert len(benchmark['cases'])==48
    tests=(OUT/'tests.txt').read_text();assert '21 GHOST offline test groups passed' in tests
    assert '21 GHOST offline test groups passed' in (OUT/'sanitizers.txt').read_text()
    assert 'PASS 19 native cases' in (OUT/'beatrepeat-regression-c.txt').read_text()
    assert 'Ran 28 tests' in (OUT/'beatrepeat-regression-v2.txt').read_text()
    assert (OUT/'beatrepeat-regression-v2.txt').read_text().rstrip().endswith('OK') or '\nOK\n' in (OUT/'beatrepeat-regression-v2.txt').read_text()
    for p,h in protected.items():
        if sha(ROOT/p)!=h:raise RuntimeError('Protected baseline changed: '+p)
    source_files=[p for p in HERE.iterdir() if p.is_file()]
    report={'scope':'Approved C0 offline prototype; no VST/GUI/state/identity/deployment changes','platform':platform.platform(),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),'native_test_groups':21,'asan_ubsan':'pass; macOS LeakSanitizer disabled','prior_plugin_regression_groups':19,'prior_vst_functional_tests':28,'prohibited_dsp_imports_absent':True,'dsp_imports':imports,'clock_drift_simulation':'30 minutes, 44.1 kHz / 123 BPM, opportunity error <= 1 sample','audio_block_invariance':'exact native float output and event decisions across mixed 1/17/32/127/512/511/1000-frame blocks','off_transparency':'exact against unchanged raw Engine + same adapter mix/tail; not a new VST wrapper comparison','trace_rows':len(events),'capture_acquisitions':acquired,'freeze_trace_rows':frozen,'audio':audio,'native_benchmark_cases':48,'native_benchmark_worst':max(benchmark['cases'],key=lambda x:x['max_deadline_fraction']),'native_benchmark_over_deadline_cases':sum(x['max_deadline_fraction']>=1 for x in benchmark['cases']),'hardware_tested':False,'hardware_accessed':False,'arm_build_created':False,'protected_files_unchanged':len(protected),'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in source_files},'protected_sha256':protected}
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 21 GHOST groups, ASan/UBSan, 19 baseline C groups, VST smoke + 28 baseline functional tests; protected artifacts unchanged.')
    print(f'Renders: {OUT}; native timing only; hardware trial NOT performed.')
if __name__=='__main__':main()
