"""GPL-3.0-only. Fifty deterministic synthetic stereo audio demonstrations."""
import math,wave,struct,csv,json,hashlib
from bindings import Native,OUT
RATE=44100;SECONDS=6;N=RATE*SECONDS;BLOCK=512
names=['input','C0','motion','buffer-dice','chaos25','chaos50','chaos100','clean','capture-freeze','combined']
inputs=['drums','sparse-percussion','chord','bass','stereo-mix']
folder=OUT/'audio';folder.mkdir(exist_ok=True)
def signal(kind):
 l=[];r=[]
 for i in range(N):
  t=i/RATE;phase=t%.5;noise=(((i*1664525+1013904223)&65535)/32768-1)
  kick=.28*math.sin(2*math.pi*(50*phase+35*(1-math.exp(-phase*22))))*math.exp(-phase*25)
  hat=.06*noise*math.exp(-(t%.125)*90)
  snare=.11*noise*math.exp(-((t+.25)%.5)*32)
  drum=kick+hat+snare
  chord=sum(math.sin(2*math.pi*f*t) for f in [130.81,164.81,196])/30*(.8+.2*math.sin(t))
  freq=[65.41,77.78,98,58.27][int(t*2)%4];bass=.22*math.sin(2*math.pi*freq*t)*min(1,phase*80)*math.exp(-phase*2)
  sparse=(.24*math.sin(2*math.pi*730*t)+.05*noise)*math.exp(-(t%.9)*60)
  a={'drums':drum,'sparse-percussion':sparse,'chord':chord,'bass':bass,'stereo-mix':.6*drum+chord*.7+bass*.4}[kind]
  b=a if kind!='stereo-mix' else .6*drum+chord*.7*math.cos(t*.9)+.4*bass
  l.append(a);r.append(b)
 return l,r
def configure(p,variant):
 p.set('P_SEED',47321);p.set('P_MIX',.7)
 if variant in ['motion','buffer-dice','combined']:p.set('P_GATE',1)
 if variant=='motion' or variant=='combined':
  p.set('P_MDEST',4);p.set('P_ROUTE',1);p.set('P_TYPE',2);p.set('P_RATE',260);p.set('P_MOTION',1)
 if variant in ['C0','chaos25','chaos50','chaos100','clean','capture-freeze','combined']:
  p.set('P_GHOST',1);p.set('P_DENSITY',12);p.set('P_CHANCE',.9);p.set('P_DISTANCE',.25);p.set('P_DURATION',110)
  for dest in range(4 if variant=='C0' else 12):
   p.set('P_DEST',dest);p.set('P_RANDOM',1)
  if variant=='capture-freeze':
   for dest in [0,1,*range(4,12)]:p.set('P_DEST',dest);p.set('P_RANDOM',0)
 if variant.startswith('chaos') or variant in ['clean','combined']:
  p.set('P_CHAOS_ON',1);p.set('P_CHAOS',float(variant[5:])/100 if variant.startswith('chaos') else 1)
reports=[]
for kind in inputs:
 left,right=signal(kind)
 for variant in names:
  p=Native(RATE);configure(p,variant);outl=[];outr=[];events=[];actions=[]
  for offset in range(0,N,BLOCK):
   if variant in ['buffer-dice','combined'] and offset//BLOCK%(RATE//BLOCK)==0:
    p.set('P_BUFFER_DICE',1);actions.append({'seconds':offset/RATE,'action':'Buffer Dice'})
   if variant=='clean' and offset//BLOCK==round(4*RATE/BLOCK):p.set('P_CLEAN',1);actions.append({'seconds':offset/RATE,'action':'Clean (latched)'})
   a,b,tr=p.process(left[offset:offset+BLOCK],right[offset:offset+BLOCK]);outl+=a;outr+=b;events+=tr
  p.close()
  if variant=='input':outl,outr=left,right;events=[]
  invalid=sum(not math.isfinite(x) for ch in [outl,outr] for x in ch);clipped=sum(abs(x)>1 for ch in [outl,outr] for x in ch)
  assert not invalid and not clipped,(kind,variant,invalid,clipped)
  peak=max(abs(x) for ch in [outl,outr] for x in ch);rms=math.sqrt(sum(x*x for ch in [outl,outr] for x in ch)/(2*N))
  jump=max(abs(ch[i]-ch[i-1]) for ch in [outl,outr] for i in range(1,N))
  path=folder/f'{kind}-{variant}.wav'
  with wave.open(str(path),'wb') as w:
   w.setnchannels(2);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(b''.join(struct.pack('<hh',round(a*32767),round(b*32767)) for a,b in zip(outl,outr)))
  with path.with_suffix('.events.csv').open('w') as f:
   keys=['seconds',*events[0].keys()] if events else ['seconds','flags'];writer=csv.DictWriter(f,keys);writer.writeheader()
   for e in events:writer.writerow({'seconds':e['sample']/RATE,**e})
  clean_error=max(abs(outl[i]-left[i]) for i in range(5*RATE,N)) if variant=='clean' else None
  if clean_error is not None:assert clean_error<1e-6
  reports.append({'input':kind,'variant':variant,'seed':47321,'seconds':SECONDS,'peak':peak,'rms':rms,'max_adjacent_difference':jump,'invalid':invalid,'clipped':clipped,'clean_last_second_error':clean_error,'actions':actions,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
  print(kind,variant,'peak',round(peak,4),flush=True)
(OUT/'audio-validation.json').write_text(json.dumps(reports,indent=2))
