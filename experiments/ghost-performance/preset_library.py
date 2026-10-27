#!/usr/bin/env python3
"""Offline external FXP library. Does not rebuild or alter DSP/GUI or internal programs."""
import ctypes as C,hashlib,json,math,pathlib,struct,sys,wave,zipfile,shutil
from generate import ROOT,OUT
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'experiments/ghost-c1')]
from test_vst import FX
from test_ghost_functional_audit import signal
DEST=ROOT/'build/ghost-preset-library'; RATE=44100
GROUPS=[('TAPE & TEXTURE',['Dusty Tape','Broken Cassette','Wow & Flutter','Vinyl Fragments','Haunted Rhodes','Tape Collapse']),('RHYTHM & BREAKS',['Broken Drummer','Stutter Funk','Beat Surgery','Reverse Groove','Half-Time Ghost','Microcuts']),('GENERATIVE & CHAOS',['Slow Mutation','Controlled Chaos','Ghost Machine','Probability Storm','Fractal Breaks','Total Collapse']),('AMBIENT & DRONES',['Frozen Memory','Endless Fragments','Dark Matter','Spectral Drift','Ghost Drone']),('VOCAL DESTRUCTION',['Broken Words','Vocal Stutter','Phantom Voice','Speech Corrupt','Vocal Scatter']),('LIVE PERFORMANCE',['Safe Glitch','Punch Machine','Live Dice','Emergency Freeze'])]
# Explicit musical recipes: activity, chaos, fragment milliseconds, mix, repeat/reverse/cut weights,
# rest, evolution, break, corrupt. No spectral/reverb/tape model is implied by creative names.
RECIPES=[(.15,.1,180,.45,.8,.15,.05,.75,.12,.05,.12),(.45,.5,90,.7,.6,.3,.1,.4,.3,.3,.4),(.12,.2,280,.5,.3,.65,.05,.7,.7,.03,.05),(.3,.45,45,.6,.4,.5,.1,.55,.25,.2,.25),(.18,.25,220,.65,.2,.75,.05,.7,.4,.08,.08),(.95,.95,12,.95,.45,.25,.3,.1,.9,.8,.85),(.55,.3,65,.8,.65,.2,.15,.35,.2,.3,.2),(.55,.15,28,.75,.9,.05,.05,.4,.1,.5,.1),(.8,.6,18,.85,.6,.15,.25,.25,.3,.65,.3),(.45,.3,170,.8,.1,.85,.05,.5,.25,.1,.1),(.6,.15,350,.85,.85,.1,.05,.4,.15,.2,.1),(.85,.65,8,.9,.35,.1,.55,.3,.4,.8,.3),(.2,.3,190,.65,.45,.5,.05,.7,.2,.1,.1),(.4,.45,75,.75,.65,.25,.1,.55,.45,.3,.2),(.6,.65,110,.8,.4,.45,.15,.45,.65,.4,.3),(.75,.9,24,.85,.3,.3,.4,.4,.8,.65,.5),(.65,.7,40,.85,.7,.2,.1,.35,.9,.6,.3),(1,1,9,1,.3,.2,.5,.05,1,1,1),(.35,.2,390,.9,.15,.8,.05,.6,.25,.05,.1),(.5,.4,260,.85,.7,.25,.05,.65,.6,.2,.15),(.35,.5,320,.9,.2,.65,.15,.7,.45,.15,.4),(.3,.45,200,.8,.25,.7,.05,.7,.8,.1,.2),(.5,.65,380,.95,.5,.45,.05,.6,.65,.2,.3),(.55,.4,70,.8,.65,.2,.15,.5,.2,.35,.15),(.7,.2,25,.85,.85,.1,.05,.35,.1,.6,.1),(.35,.45,160,.75,.1,.85,.05,.6,.55,.1,.2),(.75,.7,35,.85,.4,.2,.4,.3,.3,.7,.65),(.55,.85,50,.8,.45,.45,.1,.5,.75,.4,.25),(.15,.15,100,.5,.8,.15,.05,.8,.1,.1,.05),(.8,.35,22,.9,.9,.05,.05,.3,.2,.8,.2),(.45,.7,65,.75,.5,.4,.1,.6,.6,.4,.25),(.3,.2,300,.9,.6,.35,.05,.65,.25,.1,.1)]
sha=lambda b:hashlib.sha256(b).hexdigest()
def settings(i):
 a,c,ms,mix,r,v,cut,rest,e,br,cr=RECIPES[i]
 return [(48,0),(131,1),(132,max(.4,a)),(133,c),(134,math.log(ms/8)/math.log(50)),(53,mix),(135,r),(136,v),(137,cut),(138,min(.55,rest)),(139,e),(9,br),(17,cr),(77,1),(79,.005),(75,(1001+i*97)/65535),(32,1),(61,0),(54,0)]
def fixture(kind,n):
 out=[]
 for k in range(n):
  t=k/RATE;noise=((k*1103515245+12345)&65535)/32768-1
  if kind==0:x=sum(.09/j*math.sin(2*math.pi*f*t)*math.exp(-(t%1)*2) for j,f in enumerate([130.81,164.81,196],1))
  elif kind==1:x=sum(.09/j*math.sin(2*math.pi*110*j*t)*math.exp(-(t%.75)*6) for j in range(1,6))
  elif kind in (2,4):x=.28*math.sin(2*math.pi*60*t)*math.exp(-(t%(60/(151 if kind==2 else 120)))*40)+.1*noise*math.exp(-(t%.125)*90)
  elif kind==3:x=.17*math.sin(2*math.pi*(120*t+4*math.sin(t*4)))*(0.5+0.5*math.sin(2*math.pi*3*t))+.035*noise*max(0,math.sin(t*19))
  else:x=.13*math.sin(2*math.pi*98*t)+.07*math.sin(2*math.pi*147.1*t)
  out.append(x)
 return out
FIXTURES=[fixture(k,RATE*3) for k in range(6)]
def render(chunk,kind,held=False):
 f=FX(OUT/'native/ghost.so')
 try:
  assert f.load(chunk)==1;f.block();f.set(f.fx,32,0);f.set(f.fx,33,([60,80,151,100,120,60][kind]-40)/200);dry=FIXTURES[kind] # no host callback in this fixture; saved preset remains HOST sync
  if held:
   f.set(f.fx,126,1);signal(f,dry[:RATE]);f.set(f.fx,126,0);signal(f,dry[:128]);assert f.get(f.fx,11)==1
  out=signal(f,dry)
  assert all(math.isfinite(x) and abs(x)<1 for x in out)
  assert sum(x*x for x in out)>1e-8,'unexpected silence'
  return out
 finally:f.close()
def writewav(path,a):
 with wave.open(str(path),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(b''.join(struct.pack('<h',round(x*32767)) for x in a))
def main():
 DEST.mkdir(parents=True,exist_ok=True);prev=OUT/'ghost-performance-edition-armv7-TRIAL.zip';assert sha(prev.read_bytes())=='a82ba46c9b3a72e502d1d5ef9b12203cc994fcfc5e73dfb4513d99613d2dd944'
 shutil.copy2(prev,DEST/'REFERENCE-armv7.zip');files={};rows=[];original=[]
 with zipfile.ZipFile(prev) as z:
  for n in z.namelist():
   if n.endswith('.fxp') and '/Performance Presets/' not in n:original.append(dict(file=n,sha256=sha(z.read(n))));files[n]=z.read(n)
 assert len(original)==16
 i=0
 for cat,names in GROUPS:
  for name in names:
   f=FX(OUT/'native/ghost.so')
   try:
    for p,v in settings(i):f.set(f.fx,p,v)
    f.block();chunk=f.chunk();assert struct.unpack_from('<I',chunk,4)[0]==2
    assert f.load(chunk)==1;f.block();assert f.chunk()==chunk
    assert f.fx.contents.numPrograms==16 and f.fx.contents.numParams==148 and f.fx.contents.uniqueID==1195922260
   finally:f.close()
   raw=struct.pack('>4sI4sIIII28sI',b'CcnK',52+len(chunk),b'FPCh',1,0x47485354,2000,1,name.encode()[:27].ljust(28,b'\0'),len(chunk))+chunk
   rel='Preset Library/'+cat.replace(' & ','-')+'/'+name+'.fxp';files[rel]=raw
   # Every recipe is usable LIVE. Four held-oriented textures also tested after explicit capture.
   held=name in ['Frozen Memory','Endless Fragments','Ghost Drone','Emergency Freeze'];metrics=[];chosen=None
   for k in range(6):
    a=render(chunk,k);again=render(chunk,k);assert a==again
    delta=math.sqrt(sum((x-y)**2 for x,y in zip(a,FIXTURES[k]))/len(a));assert delta>1e-5,(name,k,delta)
    metrics.append(dict(fixture=k,peak=max(map(abs,a)),rms_delta=delta,deterministic=True))
    if k==(0 if i<6 else 2 if i<18 else 5 if i<23 else 3 if i<28 else 4):chosen=a
   if held:render(chunk,5,True)
   # Clean stops intervention without corrupting state; reload recovers saved settings.
   f=FX(OUT/'native/ghost.so');assert f.load(chunk)==1;f.block();f.set(f.fx,56,1);f.block();assert f.get(f.fx,131)==0;assert f.load(chunk)==1;f.block();assert f.chunk()==chunk;f.close()
   demo=DEST/'demos'/cat.replace(' & ','-')/(name+'.wav');demo.parent.mkdir(parents=True,exist_ok=True);writewav(demo,chosen)
   row=dict(name=name,category=cat,file=rel,sha256=sha(raw),parameters=settings(i),state='PEF1 v2',required=['LIVE','HISTORY'],recommended=['CAPTURE','HELD'] if held else [],minimum_history='Dependent on selected window, event length, position, tempo and available samples; no fixed minimum asserted',capture_required=False,held_required=False,performance_required=True,random_required=False,motion_required=False,initial_action='Feed incoming audio; optionally CAPTURE twice to retain a phrase' if held else 'Feed incoming audio',empty_buffer='No stored audio is included; incoming dry is available while circular history fills',intensity='EXTREME' if RECIPES[i][0]>=.75 else 'SUBTLE' if RECIPES[i][0]<=.2 else 'MEDIUM',behavior='GENERATIVE' if i in range(12,18) else 'HYBRID',material='MELODY' if i<6 else 'DRUMS' if i<18 else 'ANY' if i<23 else 'VOICE' if i<28 else 'ANY',macros=['ACTIVITY','CHARACTER','FRAGMENT','EVOLUTION','POSITION','MIX'],description=f'Repeat {RECIPES[i][4]:.0%}, reverse {RECIPES[i][5]:.0%}, cut {RECIPES[i][6]:.0%}; fragment {RECIPES[i][2]} ms; evolution {RECIPES[i][8]:.0%}.',audio=metrics,demo=str(demo.relative_to(DEST)))
   rows.append(row);i+=1
 index=dict(original=original,new=rows,internal_programs=16,host_bank_capacity='Not established beyond existing 16; external categorized FXP files, not a 48-program bank',hardware_validation=False,native_sha256=sha((OUT/'native/ghost.so').read_bytes()))
 files['Preset Library/catalog.json']=(json.dumps(index,indent=2)+'\n').encode()
 # Distinct exact render fingerprints; no claim perceptual listening can be automated.
 assert len({sha((DEST/r['demo']).read_bytes()) for r in rows})==32
 with zipfile.ZipFile(prev) as z:payload={n:z.read(n) for n in z.namelist()}
 root='MPC-EURO - VST - GHOST/'
 for n,data in files.items():
  if not n.startswith(root):payload[root+n]=data
 manifest=json.loads(payload[root+'manifest.json']);manifest['preset_library']='32 external FXP / 16 unchanged internal programs';manifest['files']={n[len(root):]:sha(d) for n,d in payload.items() if n not in [root+'manifest.json',root+'SHA256SUMS']};payload[root+'manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode();payload[root+'SHA256SUMS']=''.join(sha(d)+'  '+n[len(root):]+'\n' for n,d in sorted(payload.items()) if n!=root+'SHA256SUMS').encode()
 for path,data in files.items():p=DEST/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 for target,content in [(DEST/'ghost-preset-library.zip',files),(DEST/'ghost-performance-preset-library-armv7-TRIAL.zip',payload)]:
  with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
   for n,d in sorted(content.items()):info=zipfile.ZipInfo(n,(2026,10,21,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,d)
 (DEST/'validation.json').write_text(json.dumps(index,indent=2)+'\n');print('PASS:32 presets,192 fixture renders twice,32 state/clean recalls,4 held captures; DSP unchanged')
if __name__=='__main__':main()
