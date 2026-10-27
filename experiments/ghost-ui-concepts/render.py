"""GPL-3.0-only. Offline concepts only; never generates a production skin."""
from pathlib import Path
import json, math, hashlib
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'build/ghost-ui-concepts';OUT.mkdir(parents=True,exist_ok=True)
FONT=str(ROOT/'vendor/fonts/DejaVuSansMono.ttf')
BG='#101719'; PANEL='#192427'; WHITE='#ece8dc'; MUTED='#91a3a3'; TEAL='#66dbc6'; AMBER='#f4ad65'
params=json.loads((ROOT/'build/ghost-c11-demo/parameters.json').read_text()); ids={p['key']:i for i,p in enumerate(params)}
controls=[]
def text(x,y,s,size=20,color=WHITE):d.text((x,y),s,font=ImageFont.truetype(FONT,size),fill=color)
def box(x,y,w,h,color=PANEL):d.rounded_rectangle((x,y,x+w,y+h),radius=12,fill=color)
def control(x,y,w,h,label,value,key,accent=TEAL):
 box(x,y,w,h);text(x+18,y+13,label,18);text(x+18,y+43,value,28,accent)
 controls.append(dict(concept=concept,label=label,key=key,index=ids[key],bounds=[x,y,w,h]))
def mascot(x,y,scale=1):
 p=ROOT/'build/ghost-c11-demo/native-skin/MPC-EURO - VST - BeatRepeat/Plugin Skins/ghost-3.png'
 m=Image.open(p).convert('RGBA');m=m.resize((round(96*scale),round(96*scale)),Image.Resampling.LANCZOS);im.paste(m,(x,y),m)
def wave(x,y,w,h):
 box(x,y,w,h);text(x+16,y+12,'BUFFER / OFFLINE MOCK - NOT LIVE AUDIO',16,MUTED)
 d.rectangle((x+w*.27,y+43,x+w*.64,y+h-24),fill='#24423f')
 for i in range(0,w-40,4):
  a=(.15+.85*abs(math.sin(i*.031))**5)*(.45+.55*abs(math.sin(i*.119)))
  hh=(h-85)*.45*a;xx=x+20+i;d.line((xx,y+h*.56-hh,xx,y+h*.56+hh),fill=TEAL,width=2)
 d.line((x+w*.49,y+40,x+w*.49,y+h-22),fill=WHITE,width=2)
 text(x+16,y+h-22,'ILLUSTRATED CAPTURE REGION / PLAYHEAD',12,MUTED)
for concept,title in [('minimal','01 / MINIMAL PERFORMANCE'),('waveform','02 / BUFFER LANDSCAPE'),('hybrid','03 / LIVING INSTRUMENT')]:
 im=Image.new('RGB',(1280,800),'#090e10');d=ImageDraw.Draw(im)
 text(28,24,'MPC HOST / RESERVED AREA',16,MUTED);text(810,24,'GHOST C1.2 / DESIGN ONLY',16,AMBER)
 d.rectangle((0,86,1279,713),fill=BG)
 text(28,100,'GHOST',32);text(28,139,'LIVING INSTRUMENT',12,MUTED)
 for j,p in enumerate(['PERFORM','BUFFER','MOTION','GENERATIVE','SETTINGS']):
  x=270+j*195;box(x,99,183,60,'#25433f' if j==0 else PANEL);text(x+15,119,p,18,TEAL if j==0 else MUTED)
 if concept=='minimal':
  text(35,187,'REPEAT',50,TEAL);text(35,250,'A fragment becomes a rhythm.',20,MUTED)
  for j in range(16):d.rectangle((37+j*55,302,77+j*55,331),fill=TEAL if j in (0,3,6,8,11) else PANEL)
  text(37,347,'ILLUSTRATED EVENT PATTERN / NOT ENGINE HISTORY',15,MUTED);mascot(1030,185,1.65)
 elif concept=='waveform':wave(28,178,1224,202);mascot(1110,204,1)
 else:
  wave(28,178,890,202);box(934,178,318,202);mascot(1038,182,1.35)
  text(955,323,'REPEAT / SIMULATED',18,TEAL);text(955,352,'MOTION -> LENGTH',16,MUTED)
 for j,(label,value,key) in enumerate([('DENSITY','4','g_density'),('CHAOS / ON','32 %','g_chaos'),('MOTION','ON','g_motion'),('MIX','68 %','mix_live')]):control(28+j*310,400,294,100,label,value,key,AMBER if j==1 else TEAL)
 for j,(label,value,key) in enumerate([('CAPTURE','TAKE','capture'),('FREEZE','OFF','freeze'),('DICE','BUFFER','g_bufdice'),('CLEAN','RESET','g_clean')]):control(28+j*310,516,294,88,label,value,key,WHITE if j==3 else TEAL)
 for j,(label,value,key) in enumerate([('GATE','OFF','gate'),('LENGTH','100 ms','length'),('BREAK','0 %','break'),('GHOST','ON','g_ghost'),('CHANCE','75 %','g_chance')]):control(28+j*248,620,232,82,label,value,key)
 text(28,741,title,22,WHITE);text(28,777,'OFFLINE CONCEPT / ALL VALUES SIMULATED / USABLE AREA y=86..713',13,AMBER)
 im.save(OUT/f'perform-{concept}.png')
(OUT/'interaction-map.json').write_text(json.dumps(controls,indent=2))
# Geometry, preserved parameter IDs, and C1.1 artifact protection.
assert len(params)==124
for c in controls:
 x,y,w,h=c['bounds'];assert w>=56 and h>=56 and 0<=x and x+w<=1280 and 86<=y and y+h<=714
 assert params[c['index']]['key']==c['key']
for name in ('minimal','waveform','hybrid'):
 assert Image.open(OUT/f'perform-{name}.png').size==(1280,800)
 cells=[c for c in controls if c['concept']==name]
 for a in cells:
  for b in cells:
   if a is b:continue
   x,y,w,h=a['bounds'];X,Y,W,H=b['bounds'];assert x+w<=X or X+W<=x or y+h<=Y or Y+H<=y
before=json.loads((OUT/'protection-before.json').read_text());changed=[p for p,h in before.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
assert not changed,changed
(OUT/'checks.json').write_text(json.dumps(dict(previews=3,resolution=[1280,800],parameter_count=124,controls=len(controls),protected_files=len(before),changed_protected_files=changed,hardware_access=False),indent=2))
print('PASS:',len(controls),'controls; 3 full-resolution concepts;',len(before),'protected files unchanged')
# Supplemental page directions, not native components or executable controls.
im=Image.new('RGB',(1280,800),BG);d=ImageDraw.Draw(im)
text(28,20,'GHOST / DEEPER PAGES / OFFLINE DESIGN BOARD',24)
sections=[('BUFFER / LABORATORY',['Region + take / MOCK WAVE','Capture   Freeze   Position   Size','Reverse   Bend     Pitch   Corrupt','Dice / destination / lock / min-max']),('MOTION / MOVEMENT',['Shape SCHEMATIC / no live phase','Source 1-8 / Type / Rate / Sync','Destination / Route / Depth','Min-Max / Hold / Motion Dice']),('GENERATIVE / BRAIN',['Timeline MOCK / not event history','Density / Chance / Distance','Duration / Rests / Seed / Clock','Destination / ranges / Reset']),('SETTINGS / CONFIGURATION',['Engine / Legacy compatibility','Timing / smoothing / MIDI channel','Listen / sensitivity / spacing','Preset workflow / no schema change'])]
for i,(title,rows) in enumerate(sections):
 x=28+(i%2)*624;y=88+(i//2)*344;box(x,y,600,320);text(x+20,y+20,title,22,TEAL)
 for j,row in enumerate(rows):text(x+20,y+87+j*53,row,17,WHITE if j else MUTED)
text(28,778,'PROPOSED GROUPING ONLY / NO PRODUCTION GUI OR TELEMETRY IMPLEMENTED',14,AMBER)
im.save(OUT/'deeper-pages-board.png')
validation=json.loads((ROOT/'build/ghost-c11-demo/validation.json').read_text())
report=json.loads((OUT/'checks.json').read_text());report['historical_protection']={}
for field in ('source_sha256','protected_sha256'):
 entries=validation[field];bad=[p for p,h in entries.items() if not (ROOT/p).is_file() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
 report['historical_protection'][field]={'checked':len(entries),'mismatches':bad}
 # Finder metadata discrepancy is reported, never silently repaired.
 assert not [p for p in bad if p!='build/ghost-c1-demo/.DS_Store'],bad
(OUT/'checks.json').write_text(json.dumps(report,indent=2))
