"""GPL-3.0-only. Actual native MPC assets, isolated from protected skin outputs."""
import json,os,sys,pathlib
from bindings import ROOT,OUT,Native,IDS
sys.path.insert(0,str(ROOT/'vendor/mpc/tools'))
import shadow_skin as sk,skin_check
from PIL import Image,ImageDraw,ImageFont
os.chdir(ROOT)
os.environ['SHADOW_TITLE_FONT']=str(ROOT/'vendor/fonts/DejaVuSansMono.ttf')
fontpath=str(ROOT/'vendor/fonts/DejaVuSansMono.ttf')
STATES=['IDLE','LISTEN','CAPTURE','REPEAT','FREEZE','MOTION','CHAOS','CLEAN']
DEST=['LENGTH','BREAK','CAPTURE','FREEZE','POSITION','SIZE','REVERSE','BEND','PITCH','CORRUPT','MIX','GATE']
native=Native();registry=native.registry();native.close()
params=json.loads((ROOT/'ui/params.json').read_text())
commands={'clean','bufdice','motdice','reset','capture','dice'}
enums={'dest':DEST,'mdest':DEST,'type':['STEP','SMOOTH','WALK','S/H','SINE','TRI','GATE','REPEAT'],'source':[str(i+1) for i in range(8)],'edit':['OK','BOUND LINKED','FIXED 0/1','NO GRID','QUEUE FULL','MIDI REJECT'],'status':STATES,'clock':['FREE MS','BEATS'],'sync':['FREE MS','BEATS']}
for p in registry:
 q={'key':'g_'+p['key'],'name':p['name'],'min':p['min'],'max':p['max'],'default':p['default'],'saved':not p['readonly'] and p['key'] not in commands}
 if p['key'].startswith(('r0','r5')):q['unit']='ms'
 if p['key'].startswith(('r7','r8')):q['unit']='st'
 if p['key'].startswith(('r1','r4','r9','r10')):q['unit']='%';q['min']=0;q['max']=100;q['default']*=100
 if p['key'] in enums:q['options']=enums[p['key']]
 elif p['id']<IDS['P_R0MIN'] and p['min']==0 and p['max']==1 and p['key'] not in ['mix','break','chaos','depth','prob','mdepth','mmin','mmax','chance','position','corrupt','lprob','energy']:q['options']=['OFF','ON']
 params.append(q)
(OUT/'parameters.json').write_text(json.dumps(params,indent=2))
header=(ROOT/'ui/layout.conf').read_text().split('[tab PLAY]')[0]
lines=[header]
pages=[('PERFORM',['gate','length','break','mix','g_ghost','g_chaos','g_chaoson','g_clean']),('BUFFER',['g_buffer','capture','freeze','position','buffer','reverse','g_bufdice','g_dest','g_random','g_prob','g_interval','g_lock','g_dice','bend','pitch','corrupt']),('MOTION',['g_motion','g_motdice','g_type','g_rate','g_mdepth','g_mdest','g_source','g_route','g_sync','g_hold','g_mmin','g_mmax']),('GENERATIVE',['g_density','g_chance','g_distance','g_duration','g_rest','g_seed','g_clock','g_reset','g_dest','g_minimum','g_maximum','g_depth']),('SETTINGS',['legacy','time_mode','timing','smooth','midi_channel','midi_enable','g_listen','g_sens','g_spacing','g_lprob','g_lcap','g_lrepeat'])]
lookup={p['key']:p for p in params}
for name,keys in pages:
 lines+=['\n[tab '+name+']',f'text cx=330 cy=120 label="GHOST C1.1 / {name}" size=1.6 color=e9edf1', 'text cx=1110 cy=250 label="STATE" size=1.2 color=8899a8','readout cx=1110 cy=290 w=190 h=40 key=g_status label="" tsize=22','readout cx=1110 cy=400 w=180 h=36 key=g_energy label="INPUT ENERGY" tsize=20','readout cx=1110 cy=510 w=180 h=36 key=g_take label="CAPTURED TAKE" tsize=20','readout cx=1110 cy=610 w=210 h=36 key=g_edit label="RANGE FEEDBACK" tsize=17']
 if name=='PERFORM':lines+=['text cx=490 cy=650 label="CLEAN LATCHES / TURN GHOST OR MOTION ON TO REARM" size=1.05 color=8899a8','text cx=490 cy=690 label="STEREO ENGINE REQUIRED FOR GENERATIVE PLAY" size=1.05 color=f5ac66']
 for j,key in enumerate(keys):
  x=130+245*(j%4);y=220+130*(j//4);p=lookup[key]
  if key in {'g_minimum','g_maximum','g_depth'}:
   # Only continuous destinations expose range/depth editors. Discrete trigger ranges are fixed.
   conditions=[' when=g_dest:'+d for d in DEST if d not in ['CAPTURE','FREEZE','REVERSE','GATE']]
  else:conditions=['']
  for condition in conditions:
   if key in {'g_minimum','g_maximum'}:
    dest=DEST.index(condition.split(':')[1]);bound='min' if key=='g_minimum' else 'max';actual=f'g_r{dest}{bound}';lines.append(f'knob cx={x} cy={y} r=25 bw=210 key={actual} ns=18 vs=23'+condition);continue
   if key.startswith('g_') and key[2:] in commands:line=f'button cx={x} cy={y} w=204 h=46 key={key} label="{p["name"].upper()}" label_on="{p["name"].upper()}"'
   elif p.get('options') and len(p['options'])==2:
    lines.append(f'text cx={x} cy={y-42} label="{p["name"].upper()}" size=1.2 color=8899a8'+condition)
    line=f'enum_h cx={x} cy={y} sw=98 sh=44 key={key}'
   else:line=f'knob cx={x} cy={y} r=25 bw=210 key={key} ns=18 vs=23'
   lines.append(line+condition)
 qkeys=[key for key in keys[:16] if key not in ['g_minimum','g_maximum']]
 if name=='PERFORM':
  lines+=['readout cx=865 cy=560 w=210 h=35 key=mix_live label="FAST Q-LINK MIX" tsize=19'];qkeys=['gate','length','break','mix_live','g_ghost','g_chaos','g_chaoson','g_clean']
 lines.append('qlinks "'+name+'" = '+','.join(qkeys))
layout=OUT/'layout.conf';layout.write_text('\n'.join(lines)+'\n')
folder=pathlib.Path(sk.write_skin(str(OUT/'native-skin'),'MPC-EURO','BeatRepeat',str(layout),params,str(ROOT/'build/shadow_art')))
skin=folder/'Plugin Skins'
# Replace baked bitmap text with the bundled licensed font, in exported assets.
for page,tab in enumerate(sk.parse_layout(str(layout))[0]):
 bg=skin/f'sh_bg_{page}.png';im=Image.open(bg).convert('RGB');draw=ImageDraw.Draw(im)
 for w in tab['widgets']:
  if w['kind']=='text' and not w.get('when'):
   x,y,width,height=sk.text_box(w);y-=86;draw.rectangle((x,y,x+width,y+height),fill='#10151b');draw.text((w['cx'],w['cy']-86),w['label'],font=ImageFont.truetype(fontpath,17 if float(w.get('size',1))<1.4 else 22),anchor='mm',fill='#'+w.get('color','e9edf1'))
 im.save(bg)
# Original geometric character: asymmetric folded base, slit eyes, small antenna.
sheet=Image.new('RGB',(8*128,160),'#10151b')
for state,name in enumerate(STATES):
 im=Image.new('RGBA',(96,96),(0,0,0,0));d=ImageDraw.Draw(im);accent='#65dbc6' if state!=6 else '#f5ac66'
 dx=3 if state==5 else 0
 d.line([(21+dx,76),(20+dx,40),(25+dx,23),(39+dx,16),(59+dx,18),(72+dx,31),(75+dx,77),(61+dx,70),(48+dx,79),(35+dx,71),(21+dx,76)],fill='#e9edf1',width=3)
 if state==4:
  d.line((31,39,43,39),fill=accent,width=3);d.line((54,39,66,39),fill=accent,width=3);d.rectangle((32,54,64,59),outline=accent,width=2)
 elif state==7:d.line((32,44,43,44),fill=accent,width=2);d.line((54,44,65,44),fill=accent,width=2)
 else:
  d.rectangle((32+dx,36,37+dx,47 if state==2 else 43),fill=accent);d.rectangle((55+dx,36,60+dx,43),fill=accent)
 if state==1:d.arc((7,24,86,70),-40,40,fill=accent,width=2)
 if state==2:d.ellipse((42,52,55,65),outline=accent,width=2)
 if state==3:d.line((31,57,43,51,43,63,31,57),fill=accent,width=2);d.line((54,57,66,51,66,63,54,57),fill=accent,width=2)
 if state==5:d.line((6,61,16,57),fill=accent,width=2)
 if state==6:d.rectangle((17,49,40,53),fill='#10151b');d.line((13,50,39,50),fill=accent,width=3);d.line((64,28,84,28),fill=accent,width=3)
 im.save(skin/f'ghost-{state}.png');sheet.paste(im,(state*128+16,10),im)
 ImageDraw.Draw(sheet).text((state*128+64,125),name,font=ImageFont.truetype(fontpath,13),anchor='mm',fill='#e9edf1')
sheet.save(OUT/'ghost-state-sheet.png');Image.open(skin/'ghost-0.png').save(OUT/'ghost-static.png')
tui=json.loads((skin/'TUI.json').read_text());defs={x['key']:x['value'] for x in tui['pageData']['componentDefinitions']['localComponentDefinitions']}
for tab in tui['pageData']['tabs']:
 kids=defs[tab['componentName']]['componentsData']
 for state in range(8):
  b=sk._bounds(1060,42,96,96,focus='No',show='Hide');b['additionalInvalidatingHandles'].append(f'IndexedEnabling/{state}/8/Parameter {49+IDS["P_STATUS"]}')
  kids.append(sk._sub('Image',{'version':1,'image':f'ghost-{state}.png'},b,'Ghost '+STATES[state]))
(skin/'TUI.json').write_text(json.dumps(tui,separators=(',',':')))
errors=skin_check.check(str(skin))
if errors:raise SystemExit('\n'.join(errors))
# Render the exported native component graph, not a separate interface mockup.
def paint(preview,children,ox,oy,param=None):
 for c in children:
  if any(s.startswith('IndexedEnabling/') and s.split('/')[1]!='0' for s in c['bounds'].get('additionalInvalidatingHandles',[])):continue
  local=param
  for m in c.get('handle remapping',{}).get('map',[]):
   if m['key']=='Data' and m['value'].startswith('Parameter '):local=int(m['value'].split()[1])
  d=c['componentData'];x,y,w,h=[round(float(v)) for v in c['bounds']['bounds'].split()];x+=ox;y+=oy;data=d.get('data',{});kind=d['type']
  if kind in defs:paint(preview,defs[kind].get('componentsData',[]),x,y,local)
  elif kind=='Image' and (skin/data.get('image','')).is_file():
   im=Image.open(skin/data['image']).convert('RGBA').resize((w,h));preview.paste(im,(x,y),im)
  elif kind=='Knob' and data.get('filmStrip'):
   im=Image.open(skin/data['filmStrip']).convert('RGBA');p=params[local];t=(p['default']-p['min'])/(p['max']-p['min']);fy=round(t*(im.height//im.width-1))*im.width;im=im.crop((0,fy,im.width,fy+im.width)).resize((w,h));preview.paste(im,(x,y),im)
  elif kind=='Label' and local is not None:
   p=params[local];style=data['textStyle'];font=ImageFont.truetype(fontpath,round(style['font']['height']));label=p['name'] if data.get('type')=='Name' else (p['options'][int(p['default'])] if p.get('options') else f'{p["default"]:.2f} {p.get("unit","")}');ImageDraw.Draw(preview).text((x+w/2,y+h/2),label,font=font,anchor='mm',fill='#'+style['colour'][-6:])
  elif kind=='Button' and data.get('offImage'):
   im=Image.open(skin/data['offImage']).convert('RGBA').resize((w,h));preview.paste(im,(x,y),im)
for i,tab in enumerate(tui['pageData']['tabs']):
 im=Image.new('RGB',(1280,800),'#10151b');paint(im,defs[tab['componentName']]['componentsData'],0,86);ImageDraw.Draw(im).text((35,25),'MPC HOST / BEATREPEAT / GHOST C1.1 OFFLINE PREVIEW',fill='#8899a8',font=ImageFont.truetype(fontpath,18));im.save(OUT/f'gui-preview-{i+1}.png')
print('Five native pages, eight DSP-bound mascot states, skin geometry checks passed:',folder)
