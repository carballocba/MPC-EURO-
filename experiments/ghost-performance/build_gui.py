#!/usr/bin/env python3
"""Native host tabs and six existing musical controls, actual widgets/handles and source-supported column bounds."""
import copy,importlib.util,json,pathlib,sys,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'build/ghost-performance-edition'
sys.path[:0]=[str(ROOT/'experiments/ghost-product'),str(ROOT/'experiments/ghost-c12-2'),str(ROOT/'experiments/ghost-c1')]
import build as P
from PIL import Image,ImageDraw
NAMES={148:'RR MODE',149:'RR INTENSITY',150:'RR PROBABILITY',151:'RR VARIATION',152:'RR RATE',153:'RR MAX HOLD',154:'RR STATE',155:'RR FRAGMENT',131:'Performance',132:'GLITCH',133:'CHAOS',134:'SIZE',135:'REPEAT weight',136:'REVERSE weight',137:'CUT weight',138:'REST bias',139:'MOTION',140:'RATE',141:'DICE',142:'EDITOR',143:'PRESET',144:'EVENT',145:'VARIANT',146:'FRAGMENT ms',147:'BUDGET %'}
# Screen assignments change with the GUI; Program assignments remain byte-identical.
GROUPS=[[132,133,53,139],[12,134,9,17],[135,136,137,138],[140,77,79,13]]
SLOTS=[13,9,5,1,14,10,6,2,15,11,7,3,16,12,8,4]
SECTIONS=[('BUFFER',[126,11,127,128,12,13,14,15,16,17,57,58,1,0,9]),
 ('EVENTS',[135,136,137,138,139,140,77,79,80,49,76,125]),
 ('MOTION',[54,68,124,70,105,90,91,73,74,71,72,59]),
 ('RANDOM',[60,61,64,65,66,67,106,'min','max',55,104]),
 ('TIMING',[75,102,24,25,26,32,33,81]),
 ('GLOBAL',[3,5,28,29,48,34,18,19,20,92,93,94]),
 ('MIDI',[30,31,27,46,92,93,94,95,96,97]),
 ('SCENES',[21,22,23,35,36,37,38,39,47])]
MACROS={132:'ACTIVITY',133:'CHARACTER',134:'FRAGMENT ms',139:'EVOLUTION',12:'POSITION',53:'MIX %'}

def build_gui():
 source=ROOT/'build/ghost-buffer-engine-final/ghost-buffer-engine-armv7-TRIAL.zip'
 with zipfile.ZipFile(source) as z:files={n[len(P.FOLDER)+1:]:z.read(n) for n in z.namelist() if n.startswith(P.FOLDER+'/') and not n.endswith('/')}
 ref=ROOT/'build/ghost-integration-recovery/candidate/ghost-integration-recovery-armv7-OFFLINE.zip'
 original=P.ref.zip_files(ref,P.FOLDER+'/');skin=P.Skin(original);skin.files=files
 P.NAMES.update(NAMES);P.NAMES.update({49:'Legacy events',54:'Legacy Motion',55:'Legacy Chaos %',104:'Legacy Chaos ON',70:'Source depth %',76:'Event density',53:'MIX %',13:'WINDOW ms',77:'CHANCE %',79:'DURATION MAX ms',134:'SIZE ms',140:'RATE beats',126:'CAPTURE',127:'REC max s',128:'Live Repeat',129:'RECORD',130:'REC FILL'})
 P.TOGGLES.update({131,128});P.COMMANDS.update({126,141})
 skin.defs=[];skin.tabs=[];skin.qrows=[];skin.graph=[];skin.views=[];skin.composites={}
 # Protect native Capture latch: absolute OFF/ON segments avoid release ambiguities.
 # It intentionally differs from a new engine; these select the same existing126 state.
 def background(area,tip):
  im=Image.new('RGB',(1280,628),P.BG);d=ImageDraw.Draw(im);d.text((20,10),'GHOST',font=P.font(26),fill=P.ACCENT);d.text((180,14),area+' / PERFORMANCE EDITION',font=P.font(20),fill=P.INK)
  d.text((20,603),tip,font=P.font(14),fill='#9cb4bb')
  return skin.image_at(skin.asset('pe_'+area.lower()+'.png',im),(0,0,1280,628),'Background')
 def control(p,bounds,focus=False,extra_condition=None):
  c=skin.control(p,bounds,focus=focus)
  if extra_condition:
   selector,slot,total=extra_condition;P.conditions(c,selector,slot,total)
  skin.graph.append({'view':current,'parameter':p,'bounds':list(bounds),'focus':focus,'section':None,'conditions':extra_condition,'name':P.NAMES.get(p,'Range')})
  return c
 def readout(p,label,rect):
  nodes=P.Skin.readout(skin,p,label,rect);data=nodes[0]['componentData']['data'];old=data['image'];new=old[:-4]+f'_{rect[2]}_{rect[3]}_'+label.replace(' ','_')+'.png';files['Plugin Skins/'+new]=files['Plugin Skins/'+old];data['image']=new;return nodes
 def mascot(bounds):
  kids=[]
  for state,name in enumerate(['idle','listen','capture','repeat','freeze','motion','chaos','clean']):
   data=files.get('Plugin Skins/product_ghost_'+name+'.png')
   if data:
    fn='pe_ghost_'+name+'.png';files['Plugin Skins/'+fn]=data;c=skin.image_at(fn,bounds,'Ghost '+name);P.conditions(c,98,state,8);kids.append(c)
  return kids
 def reactive_mascot(bounds):
  # Declarative native conditions only: no timer, DSP callback or audio analysis.
  nodes=[];rules=[]
  def pose(name,conditions,state,offset=(0,0)):
   filename='pe_ghost_'+name+'.png';files['Plugin Skins/'+filename]=files['Plugin Skins/product_ghost_'+name+'.png']
   x,y,w,h=bounds;c=skin.image_at(filename,(x+offset[0],y+offset[1],w,h),'Ghost '+state)
   c['bounds']['additionalInvalidatingHandles']=[f'IndexedEnabling/{slot}/{total}/Parameter {p}' for p,slot,total in conditions]
   nodes.append(c);rules.append(dict(state=state,asset=filename,conditions=conditions))
  pose('capture',[(126,1,2)],'CAPTURE')
  pose('freeze',[(126,0,2),(11,1,2)],'FREEZE')
  base=[(126,0,2),(11,0,2)]
  # Low wet remains visually calm even if an internal event exists.
  pose('idle',base+[(53,0,2)],'CALM / LOW WET')
  wet=base+[(53,1,2)]
  pose('idle',wet+[(131,1,2),(144,0,4)],'CALM / NO EVENT')
  for event in [1,2,3]:
   for activity in [0,1]:
    for character in [0,1]:
     chaotic=activity==1 and character==1
     pose('chaos' if chaotic else 'repeat',wet+[(131,1,2),(144,event,4),(132,activity,2),(133,character,2)],'CHAOTIC' if chaotic else 'ACTIVE / WET',offset=([(-1,0),(1,-1),(0,1)][event-1] if not chaotic else [(-2,0),(2,-1),(0,2)][event-1]))
  for state,name in enumerate(['idle','listen','capture','repeat','freeze','motion','chaos','clean']):
   pose(name,wet+[(131,0,2),(98,state,8)],'COMPAT / '+name)
  (OUT/'mascot-rules.json').write_text(json.dumps(dict(rules=rules,inputs=[126,11,53,131,144,132,133,98],timer='none added; existing host update only',limitations='Discrete original poses, not autonomous motion or an exact intensity meter'),indent=2)+'\n')
  return nodes
 def telemetry():
  kids=[]
  for p,label,x in [(129,'RECORD',20),(144,'EVENT',270),(146,'FRAGMENT ms',520),(145,'VARIANT',770)]:kids+=readout(p,label,(x,50,232,58))
  return kids+mascot((1110,8,100,96))
 def group_bounds(params):
  result=[]
  for group in params:
   rects=[c['bounds'] for c in skin.graph if c['view']==current and c['parameter'] in group]
   x=min(b[0] for b in rects);y=min(b[1] for b in rects);xx=max(b[0]+b[2] for b in rects);yy=max(b[1]+b[3] for b in rects)
   result.append(f'{max(0,x-4)} {max(0,y-4)} {min(1280,xx+4)-max(0,x-4)} {min(628,yy+4)-max(0,y-4)}')
  return result
 def finish(area,index,kids,map_params,bounds):
  root=P.clone(skin.root);root['componentsData']=kids;root['hideQLinkBounds']=False;key='PE|'+area;skin.defs.append({'key':key,'value':root})
  t=P.clone(skin.page['tabs'][0]);t.update(tabName=area,fnKeyIndex=index,fnKeySubIndex=0,componentName=key,qlinkBoundsData=bounds);skin.tabs.append(t)
  maps={f'Q-Link {n}':-1 for n in range(1,17)}
  for slot,p in map_params:maps[f'Q-Link {slot}']=p
  skin.qrows.append({'Tab':index+1,'SubTab':1,'Bank Direction':'Column','Q-Links':maps});skin.views.append({'view':area,'tab':index,'subtab':0,'logical_assignments':maps,'bounds':bounds})
 current='PLAY';P.NAMES.update(MACROS)
 kids=[background('PLAY','RANDOM: SELECTED TARGET / MOTION: CONFIGURED ROUTES. BASE VALUES ARE PRESERVED. PUNCH: BUFFER.')]
 kids+=reactive_mascot((608,184,64,62))
 kids+=readout(60,'RANDOM TARGET',(380,186,204,58))+readout(91,'ROUTE 0=OFF 1=ON',(696,186,204,58))
 # Layout-only derivative of the same native Focus/Knob/Label composite.
 def rotary(p,rect,large):
  w,h=rect[2:];key=f'pe_rotary_{p}_{w}_{h}';definition=P.clone(skin.knob)
  focus=P.clone(next(c for c in skin.knob['componentsData'] if c['componentData']['type']=='Focus'));focus['bounds']['bounds']=f'0 0 {w} {h}'
  title=P.NAMES.get(p,NAMES.get(p,str(p))).upper();size=18 if large else 14
  im=Image.new('RGB',(w,h),P.BG);d=ImageDraw.Draw(im)
  assert d.textbbox((0,0),title,font=P.font(size))[2]<=w-12,(p,title)
  d.text((w//2,2),title,font=P.font(size),fill=P.ACCENT if large else '#b2c6c9',anchor='mt')
  slot=SLOTS[[q for group in GROUPS for q in group].index(p)]
  order=[q for group in GROUPS for q in group].index(p);bank='ABCD'[order//4];position=order%4+1
  d.text((72 if large else 6,58 if large else 42),bank+str(position),font=P.font(13),fill='#91b8b0')
  diameter=96 if large else 56;ky=24;vy=122 if large else 82
  knob=P.clone(next(c for c in skin.knob['componentsData'] if c['componentData']['type']=='Knob'));knob['bounds']['bounds']=f'{(w-diameter)//2} {ky} {diameter} {diameter}'
  value=P.clone(skin.value);value['bounds']['bounds']=f'2 {vy} {w-4} {h-vy}';value['componentData']['data']['textStyle']['font']['height']=22 if large else 18
  definition['componentsData']=[focus,skin.image_at(skin.asset(key+'.png',im),(0,0,w,h),'Rotary label'),knob,value];skin.defs.append({'key':key,'value':definition})
  c=skin.placed(key,p,rect,True)
  skin.graph.append({'view':current,'parameter':p,'bounds':list(rect),'focus':True,'section':None,'conditions':None,'name':P.NAMES.get(p,'Range'),'rotary':True,'size':'large' if large else 'compact','slot':slot,'bank':bank,'bank_position':position,'knob':[int((w-diameter)//2),ky,diameter,diameter],'value':[2,vy,w-4,h-vy]})
  return c
 large=[132,133,134,139,12,53,9,17];small=[135,136,137,138,140,77,79,13]
 for j,p in enumerate(large):kids.append(rotary(p,(16+(j%4)*312,40+(j//4)*208,296,144),True))
 for j,p in enumerate(small):kids.append(rotary(p,(16+j*156,400,148,112),False))
 P.NAMES.update({61:'RANDOM TARGET',54:'MOTION ROUTES'})
 for j,p in enumerate([61,54,141,126,11,131,56]):kids.append(control(p,(16+j*178,522,168,74),False))
 finish('PLAY',0,kids,list(zip(SLOTS,[p for g in GROUPS for p in g])),group_bounds(GROUPS))
 # Host tabs provide the existing bottom navigation/overflow; no in-plugin browser.
 P.NAMES.update(NAMES);P.NAMES.update({53:'MIX %',12:'Position',134:'SIZE ms',139:'MOTION',140:'RATE beats',126:'CAPTURE',127:'REC max s',128:'Live Repeat',129:'RECORD',130:'REC FILL'})
 tips={'BUFFER':'LIVE HISTORY / LIVE REPEAT / LIVE REVERSE / CAPTURE TOGGLE / HELD PROTECTION. CLEAN KEEPS THE TAKE.',
       'EVENTS':'WEIGHTS SHAPE THE NEXT EVENT. ACTIVITY LIMITS INTERVENTION; CHARACTER DOES NOT INCREASE THE BUDGET.',
       'MOTION':'ADVANCED MOTION ROUTES KEEP THEIR EXISTING COMPAT CONTRACT. EVOLUTION ON PLAY USES PERFORMANCE MOTION.',
       'RANDOM':'ADVANCED RANDOM TARGETS KEEP THEIR EXISTING MODE AND LOCK CONDITIONS. MACROS DO NOT OVERWRITE THEM.',
       'TIMING':'HOST SYNC OR INTERNAL TEMPO. SEED AND RESET CONTROL REPRODUCIBLE VARIATIONS.',
       'GLOBAL':'OUTPUT / BYPASS / DRIVE / MIX SMOOTHING / LEGACY / LISTEN. PRESETS: HOST MENU.',
       'MIDI':'EXISTING MIDI AND LISTEN ROUTING. NO NEW INPUTS OR HOST CALLBACKS.',
       'SCENES':'EXISTING SCENE STORE / APPLY / SEQUENCING. SCENE FORMAT UNCHANGED.'}
 for index,(name,ps) in enumerate(SECTIONS,1):
  current=name;kids=[background(name,tips[name])]+telemetry()
  if name=='RANDOM':
   kids=[background(name,'RR MODE: MANUAL / INDEP / PERFORM / BOTH. GESTURES HAVE PRIORITY; CAPTURE/FREEZE ARE NEVER AUTOMATED.')]
   for p,label,x in [(129,'RECORD',20),(154,'REPEAT STATE',270),(155,'ACTUAL ms',520),(145,'VARIANT',770)]:kids+=readout(p,label,(x,50,232,58))
   kids+=mascot((1110,8,100,96))
  focus=[p for p in ps if isinstance(p,int)];groups=[focus[i:i+4] for i in range(0,len(focus),4)]
  for j,p in enumerate(ps):
   bounds=(20+(j%4)*312,128+(j//4)*108,296,98)
   if p in ['min','max']:
    for dest,pair in P.RANGES.items():kids.append(control(pair[p=='max'],bounds,extra_condition=(60,dest,12)))
   else:kids.append(control(p,bounds,True))
  if name=='RANDOM':
   for j,p in enumerate(range(148,154)):kids.append(control(p,(20+(j%3)*416,452+(j//3)*74,404,68),False))
  if name=='BUFFER':kids.append(control(4,(956,452,296,98),False))
  finish(name,index,kids,list(zip(SLOTS,focus)),group_bounds(groups))
 for key,definition in skin.composites.items():
  if not key.startswith('product_126_'):continue
  button=next(c for c in definition['componentsData'] if c['componentData']['type']=='Button')
  import io
  for state,label in [('on','REC / TAP TO END'),('off','TAP TO RECORD')]:
   filename='Plugin Skins/'+button['componentData']['data'][state+'Image'];im=Image.open(io.BytesIO(files[filename]));draw=ImageDraw.Draw(im);draw.text((12,im.height-25),label,font=P.font(14),fill=P.ACCENT if state=='on' else '#9bb1b5');files[filename]=P.png(im)
 tui={'pageData':P.clone(skin.page)};tui['pageData']['tabs']=skin.tabs;tui['pageData']['componentDefinitions']['localComponentDefinitions']=skin.defs
 files['Plugin Skins/TUI.json']=(json.dumps(tui,indent=2)+'\n').encode()
 for name in ['Q-Links.json','Q-Links - 8by1.json']:
  q=json.loads(files['Plugin Skins/'+name]);q['Screen Mode Q-Links']['map']=skin.qrows;files['Plugin Skins/'+name]=(json.dumps(q,indent=2)+'\n').encode()
 used=P.ref.referenced_images(tui);files={n:v for n,v in files.items() if not n.startswith('Plugin Skins/') or n in used or n.endswith('.json')}
 assert used<=files.keys();(OUT/'control-graph.json').write_text(json.dumps(skin.graph,indent=2)+'\n');(OUT/'gui-views.json').write_text(json.dumps(skin.views,indent=2)+'\n')
 folder=OUT/'gui'/P.FOLDER
 for n,v in files.items():p=folder/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(v)
 return files,skin.views
if __name__=='__main__':files,views=build_gui();print('Native GUI resources',len(files),'views',len(views))
