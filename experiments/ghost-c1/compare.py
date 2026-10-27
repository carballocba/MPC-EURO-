"""Paired real VST audio against cf0ef00; fixed inputs, seed and commands."""
import ctypes as C,math,json,wave,struct,hashlib,csv
from bindings import ROOT,OUT,IDS
from test_vst import FX
from test_hardening import alias,events
folder=OUT/'comparison-audio';folder.mkdir(exist_ok=True)
RATE=44100;N=RATE*6;BLOCK=128
reports=[]
for scenario in ['manual','motion','chaos100','capture-freeze','clean','dense-midi','high-rate']:
 rendered=[]
 for version,path in [('C1',OUT/'reference-products/beatrepeat-ghost-c1.so'),('C11',OUT/'beatrepeat-ghost-c1.so')]:
  p=FX(path);p.set(p.fx,2,.7);alias(p,'P_SEED',47321/65535)
  if scenario in ['manual','motion','dense-midi','high-rate']:p.set(p.fx,1,1)
  if scenario in ['motion','dense-midi','high-rate']:
   alias(p,'P_MDEST',8/11 if scenario=='high-rate' else 1/11);alias(p,'P_ROUTE',1);alias(p,'P_TYPE',4/7 if scenario in ['dense-midi','high-rate'] else 2/7);alias(p,'P_RATE',((5 if scenario in ['dense-midi','high-rate'] else 260)-.015625)/(60000-.015625));alias(p,'P_MOTION',1)
  if scenario in ['chaos100','capture-freeze','clean']:
   for dest in ([2,3] if scenario=='capture-freeze' else [0,1,2,3,6,8,9]):
    alias(p,'P_DEST',dest/11);alias(p,'P_RANDOM',1);p.block(32)
   alias(p,'P_GHOST',1);alias(p,'P_CHAOS_ON',1);alias(p,'P_CHAOS',1)
  channels=[[],[]];actions=[]
  for offset in range(0,N,BLOCK):
   n=min(BLOCK,N-offset)
   if scenario=='clean' and offset//BLOCK==round(4*RATE/BLOCK):alias(p,'P_CLEAN',1);actions.append({'sample':offset,'seconds':offset/RATE,'action':'Clean'})
   if scenario=='manual' and offset//BLOCK==round(4*RATE/BLOCK):p.set(p.fx,8,.7-1/128);actions.append({'sample':offset,'seconds':offset/RATE,'action':'Mix Q-Link -1 detent'})
   if scenario=='dense-midi':assert events(p,[(0xb0,1,j%128,(62-j)%n) for j in range(63)])==1
   left=[];right=[]
   for j in range(n):
    t=(offset+j)/RATE;beat=t%.5;drum=.23*math.sin(2*math.pi*62*t)*math.exp(-beat*25);chord=sum(math.sin(2*math.pi*f*t) for f in [130.81,164.81,196])/35
    left.append(drum+chord);right.append(drum+chord*math.cos(t*.7))
   l=(C.c_float*n)(*left);r=(C.c_float*n)(*right);a=(C.c_float*n)();b=(C.c_float*n)();p.process(p.fx,(C.POINTER(C.c_float)*2)(l,r),(C.POINTER(C.c_float)*2)(a,b),n);channels[0]+=a;channels[1]+=b
  p.close();invalid=sum(not math.isfinite(x) for ch in channels for x in ch);clipped=sum(abs(x)>1 for ch in channels for x in ch);assert not invalid and not clipped
  file=folder/f'{scenario}-{version}.wav'
  with wave.open(str(file),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(b''.join(struct.pack('<hh',round(a*32767),round(b*32767)) for a,b in zip(*channels)))
  (file.with_suffix('.events.json')).write_text(json.dumps({'seed':47321,'actions':actions,'MIDI':'63 ignored CC1 messages per block' if scenario=='dense-midi' else None,'block':BLOCK,'rate':RATE},indent=2))
  rendered.append(channels)
  print(scenario,version,flush=True)
 difference=[a-b for ca,cb in zip(*rendered) for a,b in zip(ca,cb)]
 reports.append({'scenario':scenario,'samples':N,'rate':RATE,'peak_difference':max(abs(x) for x in difference),'difference_rms':math.sqrt(sum(x*x for x in difference)/len(difference)),'bit_exact':not any(difference),'invalid':0,'clipped':0,'hashes':{v:hashlib.sha256((folder/f'{scenario}-{v}.wav').read_bytes()).hexdigest() for v in ['C1','C11']}})
(OUT/'audio-C1-comparison.json').write_text(json.dumps(reports,indent=2))
# Core musical behavior: original C1 audio set must remain bit-identical.
old=json.loads((ROOT/'build/ghost-c1-demo/audio-validation.json').read_text());new=json.loads((OUT/'audio-validation.json').read_text())
core={'examples':50,'identical':sum(a['sha256']==b['sha256'] for a,b in zip(old,new)),'source_commit':'cf0ef00'}
(OUT/'core-audio-C1-comparison.json').write_text(json.dumps(core,indent=2));assert core['identical']==50,core
