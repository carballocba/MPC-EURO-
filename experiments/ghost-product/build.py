#!/usr/bin/env python3
"""One complete offline GHOST candidate; native components reconstructed from PLAY.
No network/device operations. Historical packages are read-only inputs.
"""
from __future__ import annotations
import argparse,copy,ctypes as C,hashlib,importlib.util,io,json,pathlib,struct,subprocess,sys,xml.etree.ElementTree as ET,zipfile
from PIL import Image,ImageDraw,ImageFont
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'experiments/ghost-c1'),str(ROOT/'experiments/ghost-c12-2'),str(ROOT/'tests')]
import build_integration_recovery as ref
from bindings import IDS
from test_vst import FX
FOLDER=ref.FOLDER
DEFAULT=ROOT/'build/ghost-product-final'
FONT=ROOT/'vendor/fonts/DejaVuSansMono.ttf'
ACCENT='#65dbc6';AMBER='#f5ac66';BG='#0b1115';INK='#e9edf1'
ALIASES={69:124,78:125,2:53,8:53,50:1,51:0,52:9,82:10,83:11,84:12,85:13,86:14,87:15,88:16,89:17,103:24}
READONLY={6,7,40,41,42,43,44,45,98,99,100,101,123}
COMMANDS={10,36,47,56,58,59,81,106}
TOGGLES={1,4,5,11,14,22,24,25,27,31,32,35,39,46,48,49,54,57,61,67,73,74,91,92,96,97,102,104}
NAMES={0:'Length',1:'Gate / Repeat',3:'Output gain',4:'PUNCH / CANCEL',5:'Bypass',9:'Break',10:'Capture',11:'Freeze',12:'Position',13:'Buffer size',14:'Reverse',15:'Bend',16:'Pitch',17:'Corrupt',18:'Cycle chance',19:'Bend density',20:'Mutation',21:'Scene select',22:'Scene run',23:'Scene division',24:'Quantize',25:'Length clock',26:'Length grid',27:'Gate MIDI mode',28:'Drive',29:'Mix smooth',30:'MIDI channel',31:'MIDI enabled',32:'Host sync',33:'Internal tempo',34:'DSP seed',35:'Scene random',36:'Store scene',37:'Scene chance',38:'Scene duration',39:'Scene enabled',46:'Freeze MIDI mode',47:'Apply scene',48:'Legacy mode',49:'Ghost events',53:'Dry / Wet %',54:'Motion enabled',55:'Chaos amount %',56:'Clean',57:'Buffer actions',58:'Buffer Dice',59:'Motion Dice',60:'Random target',61:'Random enabled',64:'Random depth',65:'Random probability',66:'Event interval',67:'Target lock',68:'Motion type',69:'Motion rate',124:'Motion rate',125:'Event distance',70:'Motion depth %',71:'Source minimum',72:'Source maximum',73:'Motion clock',74:'Source hold',75:'Event seed',76:'Density',77:'Event chance %',78:'Event distance',79:'Event duration',80:'Event rest',81:'Reset clock',90:'Motion target',91:'Motion route',92:'Listen enabled',93:'Onset threshold',94:'Listen spacing',95:'Listen chance',96:'Listen Capture',97:'Listen Repeat',102:'Event clock',104:'Chaos enabled',105:'Motion source',106:'Parameter Dice'}
BANKS=[('CORE',[76,55,70,53]),('REPEAT',[0,9,77,49]),('ENGINE',[1,54,104,10]),('ACTION',[11,58,59,56])]
COMMON=[1,49,54,104,10,11,0,9,77,91,105,90,4,58,59,106,67,56]
# Four focus knobs + <=15 compact controls per view.
DEEP=[('BUFFER','BUFFER',1,0,[10,11,12,13],[14,15,16,17,57,58,60,61,64,65,66,67,106,'min','max']),
 ('MOTION','MOTION',2,0,[68,124,70,90],[54,59,105,91,73,74,71,72,'min','max',67,56]),
 ('GENERATIVE','GENERATIVE',3,0,[76,77,125,79],[49,55,104,80,75,102,81,60,61,64,65,66,67,106]),
 ('SETTINGS','GLOBAL',4,0,[29,33,30,93],[31,32,92,94,95,96,97,25,24,48,5,3,28,34,102]),
 ('SETTINGS','SCENES',4,1,[21,22,23,35],[36,37,38,39,47,18,19,20,26,27,46])]
RANGES={0:(107,108),1:(109,110),4:(111,112),5:(113,114),7:(115,116),8:(117,118),9:(119,120),10:(121,122)}

def sha(b):return hashlib.sha256(b).hexdigest()
def png(im):
 b=io.BytesIO();im.save(b,format='PNG',optimize=True);return b.getvalue()
def font(n):return ImageFont.truetype(str(FONT),n)
def clone(x):return copy.deepcopy(x)
def rectangle(x):return list(map(int,x['bounds']['bounds'].split()))

def conditions(c,selector,slot,total=12):
 c['bounds']['additionalInvalidatingHandles']=[f'IndexedEnabling/{slot}/{total}/Parameter {selector}'];return c

class Skin:
 def __init__(self,files):
  self.files=files;old=json.loads(files['Plugin Skins/TUI.json']);self.page=clone(old['pageData']);self.defs=[];self.tabs=[];self.qrows=[];self.graph=[];self.views=[]
  d={x['key']:x['value'] for x in self.page['componentDefinitions']['localComponentDefinitions']}
  self.knob=clone(d['shKnob32_ls1.2_ns20_vs27_bw200']);self.button=clone(d['shTrig_punch_PUNCH___CANCEL']);self.segment=clone(d['shSeg_gate_0']);self.root=clone(d['PLAY|PLAY']);self.root['componentsData']=[]
  self.leaf=clone(d['PLAY|PLAY']['componentsData'][1]);self.image=clone(d['PLAY|PLAY']['componentsData'][0]);self.value=clone(self.knob['componentsData'][-1]);self.composites={}
 def asset(self,name,im):self.files['Plugin Skins/'+name]=png(im);return name
 def image_at(self,name,bounds,tag):
  c=clone(self.image);c['componentData']['name']=tag;c['componentData']['data']['image']=name;c['bounds']['bounds']=' '.join(map(str,bounds));return c
 def placed(self,key,param,bounds,focus=False):
  c=clone(self.leaf);c['componentData']['name']=NAMES.get(param,f'Range {param}');c['componentData']['type']=key;c['handle remapping']['map'][0]['value']=f'Parameter {param}';c['bounds']['bounds']=' '.join(map(str,bounds));c['bounds']['acceptsHWFocus']='Yes' if focus else 'No';return c
 def control(self,p,rect,hero=False,focus=False):
  w,h=rect[2:];key=f'product_{p}_{w}_{h}_{int(hero)}';title=NAMES.get(p,'Minimum' if p%2 else 'Maximum')
  if key not in self.composites:
   if p in TOGGLES or p in COMMANDS:
    d=clone(self.button)
    for c in d['componentsData']:c['bounds']['bounds']=f'0 0 {w} {h}'
    child=next(c for c in d['componentsData'] if c['componentData']['type']=='Button');child['bounds']['bounds']=f'0 0 {w} {h}'
    for state in ['on','off']:
     im=Image.new('RGB',(w,h),BG);draw=ImageDraw.Draw(im);active=state=='on';color=AMBER if p in (55,56,104) else ACCENT
     draw.rounded_rectangle((1,1,w-2,h-2),8,fill='#203832' if active else '#152025',outline=color if active else '#34474e',width=2)
     label='CANCEL' if p==4 and active else title.upper();suffix='' if p in COMMANDS else ('ON' if active else 'OFF')
     if p in (73,102):suffix='BEATS' if active else 'MS'
     if p==25:suffix='GRID' if active else 'MS'
     if p==11:suffix='HELD' if active else 'LIVE'
     if p==48:suffix='LEGACY' if active else 'MODERN'
     if p==4:suffix='RUNNING' if active else 'READY'
     size=18 if w>=185 else 16
     while draw.textbbox((0,0),label,font=font(size))[2]>w-16 and size>12:size-=1
     draw.text((12,8),label,font=font(size),fill=color if active else INK)
     if suffix:draw.text((12,h-27),suffix,font=font(16),fill=ACCENT if active else '#9bb1b5')
     child['componentData']['data'][state+'Image']=self.asset(key+'_'+state+'.png',im)
   else:
    d=clone(self.knob);focus_leaf=clone(next(c for c in self.knob['componentsData'] if c['componentData']['type']=='Focus'));focus_leaf['bounds']['bounds']=f'0 0 {w} {h}';children=[focus_leaf]
    # The native knob owns touch/overlay; titles are static, values are real labels.
    im=Image.new('RGB',(w,h),BG);draw=ImageDraw.Draw(im);draw.rounded_rectangle((0,0,w-1,h-1),10,fill='#121d22',outline='#2d4148')
    size=18
    while draw.textbbox((0,0),title.upper(),font=font(size))[2]>w-(16 if hero else 74) and size>12:size-=1
    draw.text((w//2 if hero else 66,85 if hero else 6),title.upper(),font=font(size),fill='#b2c6c9',anchor='mt' if hero else 'lt')
    children.append(self.image_at(self.asset(key+'_panel.png',im),(0,0,w,h),'Card'))
    k=clone(next(c for c in self.knob['componentsData'] if c['componentData']['type']=='Knob'));k['bounds']['bounds']=f'{(w-74)//2} 5 74 74' if hero else f'4 {(h-56)//2} 56 56';children.append(k)
    v=clone(self.value);v['bounds']['bounds']=f'5 106 {w-10} 28' if hero else f'64 31 {w-71} 30';v['componentData']['data']['textStyle']['font']['height']=24 if hero else 22;children.append(v);d['componentsData']=children
   if p in TOGGLES:
    # Stateful controls use the hardware-proven PLAY Gate segment contract.
    # One gesture selects an absolute value; no parent toggle can undo the child.
    d=clone(self.segment);d['componentsData']=[]
    panel=Image.new('RGB',(w,28),BG);draw=ImageDraw.Draw(panel);label=title.upper();size=16
    while draw.textbbox((0,0),label,font=font(size))[2]>w-12 and size>12:size-=1
    draw.text((w//2,14),label,font=font(size),fill=INK,anchor='mm')
    d['componentsData'].append(self.image_at(self.asset(key+'_title.png',panel),(0,0,w,28),'Control title'))
    for state in (0,1):
     child=clone(self.segment['componentsData'][0]);child['componentData']['name']='Select '+str(state)
     child['bounds']['bounds']=f'{state*(w//2)} 28 {w//2} {h-28}'
     data=child['componentData']['data'];data.update(buttonId=state,numButtonsInGroup=2)
     for selected in ('off','on'):
      im=Image.new('RGB',(w//2,h-28),BG);draw=ImageDraw.Draw(im);active=selected=='on'
      draw.rounded_rectangle((1,1,w//2-2,h-30),6,fill='#203832' if active else '#152025',outline=ACCENT if active else '#34474e',width=2)
      caption=('PUNCH' if state else 'CANCEL') if p==4 else ('ON' if state else 'OFF')
      if p==11:caption='HELD' if state else 'LIVE'
      if p in (73,102):caption='BEATS' if state else 'MS'
      if p==48:caption='LEGACY' if state else 'MODERN'
      draw.text((w//4,(h-28)//2),caption,font=font(16),fill=ACCENT if active else '#9bb1b5',anchor='mm')
      data[selected+'Image']=self.asset(f'{key}_select_{state}_{selected}.png',im)
     d['componentsData'].append(child)
    if focus:
     f=clone(self.button['componentsData'][0]);f['bounds']['bounds']=f'0 0 {w} {h}';d['componentsData'].insert(0,f)
   self.composites[key]=d;self.defs.append({'key':key,'value':d})
  return self.placed(key,p,rect,focus)
 def readout(self,p,title,rect):
  x,y,w,h=rect;im=Image.new('RGB',(w,h),BG);draw=ImageDraw.Draw(im);draw.rounded_rectangle((0,0,w-1,h-1),8,fill='#142125');draw.text((10,5),title,font=font(14),fill='#91a9ad')
  base=self.image_at(self.asset(f'readout_{p}.png',im),rect,title)
  v=clone(self.value);v['bounds']['bounds']=f'{x+8} {y+24} {w-16} {h-27}';v['handle remapping']['map']=[{'key':'Data','value':f'Parameter {p}'}];v['componentData']['name']=title;v['componentData']['data']['textStyle']['font']['height']=22
  return [base,v]
 def make_view(self,area,bank,tab,sub,focus,extra,perform):
  key=area+'|'+bank;children=[];bg=Image.new('RGB',(1280,628),BG);d=ImageDraw.Draw(bg)
  d.text((26,13),'GHOST',font=font(27),fill=INK);d.text((162,18),f'{area} / {bank}',font=font(20),fill=ACCENT)
  d.text((26,49),'LIVING INSTRUMENT / NATIVE VST2',font=font(13),fill='#728d93')
  note={'PERFORM':'LEGACY OFF. DENSITY: GHOST + TARGET / CHAOS: GHOST + CHAOS ON / DEPTH: MOTION + ROUTE + REPEAT.',
        'BUFFER':'LEGACY OFF. REVERSE / BEND / PITCH / CORRUPT: REPEAT OR FREEZE. RANDOM: GHOST + UNLOCKED TARGET.',
        'MOTION':'LEGACY OFF: MOTION + ROUTE ON. HOLD / LOCK / MANUAL EDITS CAN OVERRIDE. REPEAT OR FREEZE TO HEAR.',
        'GENERATIVE':'LEGACY OFF: GHOST + CHANCE + DENSITY > 0. CHAOS ALSO NEEDS CHAOS ON. CLEAN STOPS; PUNCH OR ENGINE REARMS.',
        'SETTINGS':'LEGACY ON DISABLES GHOST / MOTION. SYNC: HOST OR INTERNAL. LISTEN NEEDS ONSETS + CAPTURE / REPEAT SWITCHES.'}[area]
  d.text((26,608),note,font=font(13),fill='#95adb0')
  children.append(self.image_at(self.asset('product_bg_'+area+'_'+bank+'.png',bg),(0,0,1280,628),'Background'))
  # No fabricated waveform. Four labels consume real engine telemetry.
  for p,title,x in [(98,'ENGINE STATE',26),(101,'CAPTURED TAKE',260),(100,'INPUT ENERGY %',494),(123,'EDIT FEEDBACK',728)]:children+=self.readout(p,title,(x,75,216,58))
  for state,name in enumerate(['idle','listen','capture','repeat','freeze','motion','chaos','clean']):
   path=ROOT/f'build/ghost-ui-concepts/v2/ghost-{name}.png';im=Image.open(path).convert('RGBA');im.thumbnail((100,96))
   canvas=Image.new('RGBA',(100,96),(0,0,0,0));canvas.alpha_composite(im,((100-im.width)//2,(96-im.height)//2));asset=self.asset('product_ghost_'+name+'.png',canvas)
   c=self.image_at(asset,(1090,58,100,96),'Ghost '+name);conditions(c,98,state,8);children.append(c)
  bounds=[]
  for x,p in zip((30,345,660,975),focus):
   rect=(x,170 if not perform else 210,200,135);children.append(self.control(p,rect,hero=True,focus=True));bounds.append(' '.join(map(str,rect)))
  controls=[]
  for j,p in enumerate(extra):
   rect=((30+(j%6)*205,364+(j//6)*74,190,64) if perform else (26+(j%5)*248,316+(j//5)*94,236,86))
   if isinstance(p,int) and p in focus:continue # no duplicate binding or fake focus target
   if p in ('min','max'):
    selector=90 if area=='MOTION' else 60
    for dest,pair in RANGES.items():
     pp=pair[0 if p=='min' else 1];c=self.control(pp,rect);conditions(c,selector,dest);children.append(c)
   else:
    c=self.control(p,rect)
    if p==64:
     for dest in RANGES:children.append(conditions(clone(c),60,dest))
    else:children.append(c)
  root=clone(self.root);root['componentsData']=children;self.defs.append({'key':key,'value':root})
  tab_data=clone(self.page['tabs'][0]);tab_data.update(tabName=area+' / '+bank if area in ('PERFORM','SETTINGS') else area,fnKeyIndex=tab,fnKeySubIndex=sub,componentName=key,qlinkBoundsData=bounds);self.tabs.append(tab_data)
  q={f'Q-Link {i}':-1 for i in range(1,17)};q.update({f'Q-Link {i}':p for i,p in zip((13,9,5,1),focus)});self.qrows.append({'Tab':tab+1,'SubTab':sub+1,'Bank Direction':'Column','Q-Links':q})
  for c in children:
   for m in c.get('handle remapping',{}).get('map',[]):
    if str(m['value']).startswith('Parameter '):
     pp=int(m['value'].split()[1]);self.graph.append({'view':key,'parameter':pp,'name':c['componentData']['name'],'bounds':rectangle(c),'focus':c['bounds']['acceptsHWFocus']=='Yes','visibility':c['bounds'].get('additionalInvalidatingHandles',[]),'interactive':c['componentData']['type'] in self.composites})
  self.views.append({'view':key,'focus':focus,'tab':tab,'subtab':sub})
 def finish(self):
  for i,(name,ps) in enumerate(BANKS):self.make_view('PERFORM',name,0,i,ps,COMMON,True)
  for a,b,t,s,f,e in DEEP:self.make_view(a,b,t,s,f,e,False)
  self.page['componentDefinitions']['localComponentDefinitions']=self.defs;self.page['tabs']=self.tabs
  tui={'pageData':self.page};self.files['Plugin Skins/TUI.json']=(json.dumps(tui,separators=(',',':'))+'\n').encode()
  for name in ['Q-Links.json','Q-Links - 8by1.json']:
   q=json.loads(self.files['Plugin Skins/'+name]);q['Screen Mode Q-Links']['map']=self.qrows;self.files['Plugin Skins/'+name]=(json.dumps(q,indent=2)+'\n').encode()
  return tui

def native_presets(native,files,out):
 f=FX(native);manifest=[]
 try:
  f.d(f.fx,12,0,0,None,0)
  for index in range(16):
   assert f.d(f.fx,2,0,index,None,0)==1
   name=C.create_string_buffer(25);f.d(f.fx,29,index,0,name,0);name=name.value.decode()
   data=f.chunk();assert data.startswith(b'GCX1')
   raw=struct.pack('>4sI4sIIII28sI',b'CcnK',52+len(data),b'FPCh',1,0x47485354,2000,1,name.encode()[:27].ljust(28,b'\0'),len(data))+data
   stem=f'{index:02d}-'+''.join(c if c.isalnum() else '-' for c in name);files['Presets/'+stem+'.fxp']=raw
   manifest.append({'program':index,'name':name,'file':'Presets/'+stem+'.fxp','chunk_sha256':sha(data),'chunk_size':len(data),'gate_and_freeze_on_recall':False})
 finally:f.close()
 files['Presets/index.json']=(json.dumps(manifest,indent=2)+'\n').encode();return manifest

def matrix(skin,params):
 by={i:[] for i in range(126)}
 for c in skin.graph:by[c['parameter']].append(c)
 rows=[]
 dependencies={76:'Ghost ON; events must be audible (Gate OFF or randomized destinations)',55:'Ghost ON + Chaos ON; event/random destinations',70:'Motion ON + selected route ON + audible destination + Gate/Punch/event',49:'Stereo modern engine, Legacy OFF',54:'Legacy OFF; selected route enabled',91:'Selected destination/source; Motion ON',58:'Buffer enabled; unlocked buffer destinations; activate Repeat to hear',59:'Unlocked Motion source; route + Motion required',106:'Selected unlocked destination; Repeat to hear',92:'Input onset above sensitivity/probability; Listen Capture/Repeat switches',4:'Running audio, buffer available; Freeze retains held source',56:'Latched stop; explicit Ghost/Motion/Gate rearm',61:'Selected random destination; Ghost events',64:'Continuous destination only; Ghost events',69:'Clock determines ms/beats; minimum 5 ms or 1/64 beat'}
 for i,p in enumerate(params):
  alias=ALIASES.get(i);special=None
  if i in (62,63):special='Legacy aggregate alias; safe per-destination Min/Max 107..122 instead'
  if i in READONLY:special='Host telemetry; state/take/input/edit exposed in header; detailed legacy meters host automation'
  rows.append({'parameter':i,'key':p['key'],'name':NAMES.get(i,p['name']),'alias_of':alias,'readonly':i in READONLY,'gui':by[i] or (by.get(alias,[]) if alias is not None else []),'condition':dependencies.get(i,'Selected destination/source where applicable; see manual'),
   'state_path':('base target/Engine' if i<49 else 'C1 parameters/state -> scheduler/Motion -> effective Engine config'),'preset':False if i in COMMANDS or i in READONLY or i in (1,4,11,50,82,83) else True,'notes':special,'test':'test_ghost_product.py + control-recovery + core stress'})
 return rows

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=pathlib.Path,default=DEFAULT);args=parser.parse_args();out=args.out.resolve()
 if out.exists():raise SystemExit('Refusing to overwrite candidate/history: '+str(out))
 out.mkdir(parents=True)
 subprocess.run([sys.executable,str(ROOT/'experiments/ghost-c1/prepare.py')],check=True)
 compiler=ref.module(ROOT/'experiments/ghost-c12-2/build_independent_ghost.py','product_compiler');compiler.OUT=out/'engine';compiler.OUT.mkdir()
 binary,abi=compiler.compile_arm(True,strip_debug=True,final_product=True);native=compiler.compile_native_identity_test(True,final_product=True)
 source=ROOT/'build/ghost-integration-recovery/candidate/ghost-integration-recovery-armv7-OFFLINE.zip';assert sha(source.read_bytes())=='b84aad39a034c27dbde1c5fa9050a801dc9a54ccace4ce4f246b5a2a268e3904'
 files=ref.zip_files(source,FOLDER+'/');files.pop('manifest.json');files.pop('SHA256SUMS');files['ghost.so']=binary.read_bytes()
 skin=Skin(files);tui=skin.finish()
 presets=native_presets(native,files,out)
 # Drop unreferenced historical art: retain only resources used by the new native graph.
 used=ref.referenced_images(tui)
 files={n:v for n,v in files.items() if not n.startswith('Plugin Skins/') or n in used or n.endswith('.json')}
 assert used<=files.keys()
 params=json.loads((ROOT/'build/ghost-c12-prototype/parameters.json').read_text());assert len(params)==124
 params += [{'key':'g_rate_live','name':'Motion rate','min':0,'max':1,'default':0,'saved':False},{'key':'g_distance_live','name':'Event distance','min':0,'max':1,'default':0,'saved':False}]
 rows=matrix(skin,params)
 for r in rows:
  if r['parameter'] in (124,125):r['condition']='Clock-aware logarithmic alias; changes are resolved in audio queue order; canonical 69/78 persist';r['preset']='via canonical 69/78'
 missing=[r['parameter'] for r in rows if not r['gui'] and not r['readonly'] and r['parameter'] not in (62,63)]
 if missing:raise RuntimeError('GUI-inaccessible writable parameters '+str(missing))
 (out/'function-matrix.json').write_text(json.dumps(rows,indent=2)+'\n');(out/'control-graph.json').write_text(json.dumps(skin.graph,indent=2)+'\n')
 (out/'parameters.json').write_text(json.dumps(params,indent=2)+'\n')
 v=ET.fromstring(files['version.xml']);v.find('version').text='2.3.0.2';files['version.xml']=ET.tostring(v,encoding='utf-8',xml_declaration=True)+b'\n'
 manifest={'candidate':'GHOST Living Instrument / complete supervised-trial candidate','uid':1195922260,'xml_uid':'47485354','identifier':'MPC-EURO.vst.ghost','version':'2.3.0.2','parameters':126,'factory_programs':16,'top_level_areas':5,'views':skin.views,'hardware_validation':'PENDING; previous Integration Recovery PLAY/audio only verified by user','device_access':False,'abi':abi,'files':{n:sha(v) for n,v in sorted(files.items())}}
 files['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode();files['SHA256SUMS']=''.join(f'{sha(v)}  {n}\n' for n,v in sorted(files.items())).encode()
 folder=out/'package'/FOLDER
 for n,v in files.items():
  p=folder/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(v)
 archive=out/'ghost-living-instrument-armv7-TRIAL.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for n,v in sorted(files.items()):
   i=zipfile.ZipInfo(FOLDER+'/'+n,(2026,10,19,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,v)
 report={'zip':str(archive),'zip_sha256':sha(archive.read_bytes()),'binary_sha256':sha(files['ghost.so']),'files':len(files),'native':str(native),'abi':abi,'views':skin.views,'presets':presets,'hardware_validation':'PENDING','device_access':False}
 (out/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')
 delivery={'package_sha256':report['zip_sha256'],'binary_sha256':report['binary_sha256'],
  'transaction_sha256':sha((ROOT/'tools/ghost-product-transaction.sh').read_bytes()),
  'runner_sha256':sha((ROOT/'tools/ghost_functional_trial.py').read_bytes()),'shared_runner_sha256':sha((ROOT/'tools/ghost_product.py').read_bytes()),'registry_write_required':False,
  'physical_validation':'PENDING','baseline_binary_sha256':'3c59398b851d2d08a59abd76c9704c9553e04105180b6c2f123dd28342595e04','fallback_zip_sha256':'d9f0b015f61abe615e5e5660cfa6a1134fbae5ce90e9d0994682de8e5cf93c45'}
 (out/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ('presets','views')},indent=2))
if __name__=='__main__':main()
