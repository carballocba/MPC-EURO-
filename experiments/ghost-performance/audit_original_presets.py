import sys,pathlib,json,zipfile,ctypes as C,math
r=pathlib.Path(__file__).resolve().parents[2];sys.path[:0]=[str(r/'experiments/ghost-performance'),str(r/'experiments/ghost-c1'),str(r/'tests')]
from test_vst import FX
from preset_library import signal,FIXTURES,OUT
b=r/'build/ghost-preset-library';d=json.loads((b/'validation.json').read_text())
with zipfile.ZipFile(b/'REFERENCE-armv7.zip') as z:
 for x in d['original']:
  raw=z.read(x['file']);f=FX(OUT/'native/ghost.so');assert raw[60:64] in [b'PEF1',b'GBF1',b'GCX1'];assert f.load(raw[60:])==1;f.block();p={str(i):f.get(f.fx,i) for i in [1,4,11,14,49,53,54,56,61,76,101,126,128,131,132,139]};a=signal(f,FIXTURES[4]);x.update(parameters=p,required=['LIVE','HISTORY'],capture_required=False,held_required=False,performance_required=p['131']>.5,initial_action='Feed audio; inspect saved Gate/Repeat/Ghost flags. If dry, use PUNCH in BUFFER; no automatic capture performed.',audio_probe=dict(peak=max(map(abs,a)),rms_delta=math.sqrt(sum((v-w)**2 for v,w in zip(a,FIXTURES[4]))/len(a)),finite=all(math.isfinite(v) for v in a)),dependency_confidence='Saved flags and dry percussion probe; original preset musical activation not redesigned');f.close()
(b/'original-audit.json').write_text(json.dumps(d['original'],indent=2)+'\n');(b/'validation.json').write_text(json.dumps(d,indent=2)+'\n')
