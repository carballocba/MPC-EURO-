"""GPL-3.0-only. V2 visual mockups only; not a production MPC skin."""
from pathlib import Path
import json, math
from PIL import Image, ImageDraw, ImageFont
R=Path(__file__).resolve().parents[2]; O=R/'build/ghost-ui-concepts/v2'; O.mkdir(parents=True,exist_ok=True)
F=str(R/'vendor/fonts/DejaVuSansMono.ttf'); BG='#0b1012'; SUR='#141e20'; CARD='#1a2729'; HI='#f0ede4'; DIM='#93a5a2'; TEAL='#63dec9'; AMB='#ffad5a'; RED='#ff6d5c'; GRID='#263638'
# The original silhouette's broken hem, two square eyes and tapered crown are recreated as new low-res pixel art.
def sprite(state,frame=0):
 im=Image.new('RGBA',(32,32));p=im.load(); white=(240,237,228,255); aqua=(99,222,201,255); amber=(255,173,90,255)
 accent=amber if state=='CHAOS' else aqua
 # outline mask, deliberately pixelated; folded hem and asymmetric crown echo original ghost.
 pts=[(8,27),(7,13),(9,8),(12,6),(15,6),(18,3),(21,7),(24,8),(26,12),(26,27),(22,24),(18,28),(14,25),(11,28)]
 ImageDraw.Draw(im).line(pts+[pts[0]],fill=white,width=1)
 d=ImageDraw.Draw(im)
 if state=='FREEZE':
  d.line((11,14,14,14),fill=accent,width=1);d.line((19,14,22,14),fill=accent,width=1);d.line((13,20,21,20),fill=accent,width=1)
 elif state=='CLEAN':
  d.point((12,14),fill=accent);d.point((20,14),fill=accent);d.line((14,20,19,20),fill=accent)
 else:
  for x,y in ([(12,13),(20,13)] if state not in ('CAPTURE','CHAOS') else [(13,13),(20,13)]): d.rectangle((x,y,x+1,y+2),fill=accent)
  d.line((14,20,17,21,19,19),fill=accent,width=1)
 if state=='IDLE': d.point((18,3),fill=accent)
 if state=='LISTEN':
  d.line((3,13,5,13,6,10,8,16,9,13),fill=accent,width=1)
  d.point((26,10),fill=accent);d.point((28,12),fill=accent)
 if state=='CAPTURE':
  for x,y in [(4,8),(6,11),(3,15),(5,19)]:d.point((x,y),fill=accent)
 if state=='REPEAT':
  for off in (0,4,8):d.line((27+off//4,9+off,30+off//4,9+off),fill=accent,width=1)
 if state=='MOTION':
  d.line((2,23,5,21,7,24),fill=accent,width=1);d.point((3,26),fill=accent)
 if state=='CHAOS':
  d.rectangle((6,12,9,13),fill=BG);d.line((3,9,8,9),fill=accent,width=1);d.line((25,20,30,20),fill=accent,width=1);d.point((28,6),fill=accent)
 if state=='CLEAN':
  for x,y in [(5,6),(27,7),(4,22),(28,24)]:d.point((x,y),fill=accent)
 if frame:
  # Four lightweight preview frames per state. Static sprite is the C1.1 fallback.
  if state=='IDLE':
   shifted=Image.new('RGBA',im.size);shifted.paste(im,(0,[0,-1,-2,-1][frame%4]));im=shifted
  elif state=='CAPTURE':
   for j in range(1,5-frame): ImageDraw.Draw(im).point((3+j*2,9+j*3),fill=accent)
  elif state=='REPEAT':
   echo=im.copy();echo.putalpha(echo.getchannel('A').point(lambda a:a*30//255)); shifted=Image.new('RGBA',im.size);shifted.paste(echo,(min(5,frame*2),0));im=Image.alpha_composite(shifted,im)
  elif state=='MOTION':
   shifted=Image.new('RGBA',im.size);shifted.paste(im,([-1,0,1,0][frame%4],0));im=shifted
  elif state=='CHAOS':
   yy=10+(frame*4)%13;ImageDraw.Draw(im).rectangle((4,yy,10,yy+1),fill=BG);ImageDraw.Draw(im).rectangle((22,yy+1,28,yy+2),fill=amber)
  elif state=='CLEAN':
   im.putalpha(im.getchannel('A').point(lambda a:a*(3-frame)//3))
 return im.resize((128,128),Image.Resampling.NEAREST)
states=['IDLE','LISTEN','CAPTURE','REPEAT','FREEZE','MOTION','CHAOS','CLEAN']
sheet=Image.new('RGB',(8*180,190),BG);sd=ImageDraw.Draw(sheet)
for i,s in enumerate(states):
 im=sprite(s);sheet.paste(im,(i*180+26,5),im);sd.text((i*180+90,157),s,font=ImageFont.truetype(F,15),anchor='mm',fill=HI)
 im.save(O/f'ghost-{s.lower()}.png')
sheet.save(O/'ghost-states.png')
anim=Image.new('RGB',(8*4*148,164),BG);ad=ImageDraw.Draw(anim)
for i,state in enumerate(states):
 for frame in range(4):
  x=(i*4+frame)*148;im=sprite(state,frame);anim.paste(im,(x+10,0),im);ad.text((x+74,139),f'{state[:3]} / {frame+1}',font=ImageFont.truetype(F,11),anchor='mm',fill=HI)
anim.save(O/'ghost-animation-concepts.png')
# mockup primitives

def font(size):return ImageFont.truetype(F,size)
def label(d,x,y,t,size=16,color=HI):d.text((x,y),t,font=font(size),fill=color)
def panel(d,x,y,w,h,fill=CARD,rad=13):d.rounded_rectangle((x,y,x+w,y+h),rad,fill=fill)
def wave(d,x,y,w,h,variant=0):
 panel(d,x,y,w,h,SUR,12);label(d,x+15,y+10,'BUFFER  ·  SIMULATED WAVEFORM',13,DIM)
 # Draw the selection tint before the trace so it never obscures the waveform.
 d.rounded_rectangle((x+w*.37,y+34,x+w*.69,y+h-15),radius=3,fill='#214640')
 # deliberately illustrative; label is adjacent and persistent.
 for i in range(3,w-12,4):
  t=i/w; env=(.28+.72*(math.sin(t*math.pi)**.5)); seed={'balanced':0,'performance':1,'experimental':2}.get(variant,0); v=abs(math.sin(i*.032+seed*.4))*(.35+.65*abs(math.sin(i*.105+seed)))
  amp=(h*.37)*env*v
  col='#a1f0dc' if .37<t<.69 else TEAL
  d.line((x+i,y+h*.59-amp,x+i,y+h*.59+amp),fill=col,width=2)
 # playhead & event ticks are illustrative
 d.line((x+w*.53,y+31,x+w*.53,y+h-14),fill=HI,width=2)
 for off in (.2,.31,.73,.87):d.line((x+w*off,y+h-20,x+w*off,y+h-12),fill=AMB,width=2)

def knob(d,x,y,r,name,value,frac,color=TEAL):
 # MCP skin supports native knobs/filmstrips. Circular illustrated dial is a proposal, not a widget.
 d.ellipse((x-r,y-r,x+r,y+r),fill=CARD,outline=GRID,width=2)
 d.arc((x-r+4,y-r+4,x+r-4,y+r-4),135,405,fill='#344648',width=4)
 d.arc((x-r+4,y-r+4,x+r-4,y+r-4),135,135+270*max(0,min(1,frac)),fill=color,width=4)
 a=math.radians(135+270*max(0,min(1,frac)));d.ellipse((x+math.cos(a)*(r-2)-3,y+math.sin(a)*(r-2)-3,x+math.cos(a)*(r-2)+3,y+math.sin(a)*(r-2)+3),fill=color)
 d.text((x,y-7),value,font=font(16),anchor='mm',fill=HI);d.text((x,y+r+8),name.upper(),font=font(13),anchor='mt',fill=DIM)
def slider(d,x,y,w,name,value,frac,color=TEAL):
 label(d,x,y,name.upper(),13,DIM);label(d,x,y+19,value,17,HI);yy=y+54;d.rounded_rectangle((x,yy,x+w,yy+5),radius=2,fill=GRID);xx=x+frac*w;d.rounded_rectangle((x,yy,xx,yy+5),radius=2,fill=color);d.ellipse((xx-6,yy-4,xx+6,yy+9),fill=color)
def button(d,x,y,w,h,name,detail='',kind='action'):
 fill=('#4b3021' if kind=='clean' else '#164139' if kind=='on' else SUR)
 edge=AMB if kind=='clean' else TEAL if kind=='on' else GRID
 d.rounded_rectangle((x,y,x+w,y+h),radius=10,fill=fill,outline=edge,width=2)
 label(d,x+12,y+8,name.upper(),15,AMB if kind=='clean' else HI)
 if detail:label(d,x+12,y+h-23,detail,11,DIM)
def header(d):
 label(d,26,95,'GHOST',24,HI);label(d,26,124,'LIVING INSTRUMENT',10,DIM)
 pages=['PERFORM','BUFFER','MOTION','GENERATIVE','SETTINGS']
 for i,p in enumerate(pages):
  x=220+i*204; active=i==0
  panel(d,x,93,190,42,'#1d3a35' if active else SUR,8)
  if active:d.rounded_rectangle((x+1,126,x+189,129),radius=2,fill=TEAL)
  label(d,x+15,105,p,15,TEAL if active else DIM)
def qstrip(d):
 # Exact, unchanged C1.1 Program Mode Q-Link assignments; informational strip only.
 labels=['MIX','CAPTURE','PITCH','STATE','BREAK','BUFFER','REVERSE','MUTATE','LENGTH','POSITION','CORRUPT','DENSITY','GATE','FREEZE','BEND','CHANCE']
 x0=27;y=669;label(d,27,y-1,'PROGRAM Q-LINKS',10,DIM)
 for i,t in enumerate(labels):
  x=x0+i*76
  d.rounded_rectangle((x,y+15,x+71,y+39),radius=5,fill=SUR)
  d.text((x+5,y+20),f'{i+1:02} {t}',font=font(9),fill=TEAL if i in (0,8,12,15) else DIM)
def mascot_block(im,state,position=(1030,205),scale=1):
 x,y=position;w=round(128*scale);h=w
 frame=Image.new('RGBA',(w,h),(0,0,0,0));sp=sprite(state).resize((w,h),Image.Resampling.NEAREST);im.paste(sp,(x,y),sp)

def mock(name,title,variant):
 im=Image.new('RGB',(1280,800),BG);d=ImageDraw.Draw(im)
 # reserved host header/footer: no imagined plugin drawing in those bands.
 d.rectangle((0,0,1280,85),fill='#070b0c');label(d,25,29,'HOST DISPLAY / RESERVED',12,'#627271');label(d,1050,29,'GHOST C1.2  ·  CONCEPT',12,AMB)
 d.rectangle((0,86,1280,713),fill=BG);header(d)
 # Main buffer region / mascot card. Third variation stylizes scene but keeps state legible.
 if variant=='experimental':
  panel(d,27,151,1226,210,'#101719');wave(d,39,163,952,185,2)
  for i in range(28):
   xx=53+(i*67)%920; yy=180+(i*47)%145
   d.rectangle((xx,yy,xx+3,yy+3),fill=AMB if i%4==0 else TEAL)
  panel(d,1005,163,236,185,'#1c2728');mascot_block(im,'CHAOS',(1057,171),1.0)
  label(d,1020,302,'CHAOS  /  ARMED',13,AMB);label(d,1020,325,'BUFFER HELD',11,DIM)
 else:
  wave(d,27,151,952,210,variant)
  panel(d,995,151,258,210,SUR)
  state={'balanced':'REPEAT','performance':'MOTION'}[variant]
  mascot_block(im,state,(1058,161),1.0 if variant=='balanced' else .87)
  label(d,1015,303,{'balanced':'REPEAT  ·  ACTIVE','performance':'MOTION  ·  ACTIVE'}[variant],13,TEAL)
  label(d,1015,328,'CAPTURED TAKE  /  READY',10,DIM)
 # Continuous primary controls, represented with touch-size native knob suggestion.
 specs=[('Density','4',.25,TEAL),('Chaos','32%',.32,AMB),('Motion Depth','68%',.68,TEAL),('Dry / Wet','68%',.68,TEAL)]
 centers=[130,350,570,790]
 for (n,v,f,c),cx in zip(specs,centers):
  knob(d,cx,420,47,n,v,f,c)
 # Performance buttons retain meaningful distinctions; Clean remains prominent and latched state feedback explicit.
 button(d,895,380,164,74,'CAPTURE','READY','action')
 button(d,1074,380,163,74,'FREEZE','LIVE','action')
 button(d,895,466,164,66,'DICE','BUFFER','action')
 button(d,1074,466,163,66,'CLEAN','ARMED · REARM GHOST','clean')
 # secondary continuous controls: never mini-knobs; actual Motion Depth stays main and motion enable separate.
 slider(d,37,495,233,'LENGTH','100 ms',.22)
 slider(d,300,495,233,'BREAK','OFF',0)
 slider(d,563,495,233,'CHANCE','75 %',.75)
 # toggles and truthful real-time indicators. All values here are clearly mock content.
 button(d,37,582,136,56,'GATE','OFF','action');button(d,183,582,136,56,'GHOST','ON','on');button(d,329,582,136,56,'MOTION','ON','on');button(d,475,582,136,56,'CHAOS','OFF','action')
 d.rounded_rectangle((621,580,1238,641),radius=10,fill='#151f20',outline=GRID,width=1)
 label(d,636,590,'ENGINE STATE  ·  MOCK',11,DIM)
 label(d,636,612,{'balanced':'REPEAT','performance':'MOTION','experimental':'CHAOS'}[variant],16,TEAL if variant!='experimental' else AMB)
 label(d,837,613,'ENERGY',10,DIM);d.rounded_rectangle((904,618,1036,626),radius=4,fill=GRID);d.rounded_rectangle((904,618,978,626),radius=4,fill=TEAL)
 label(d,1052,613,'TAKE READY',11,HI)
 qstrip(d)
 label(d,27,744,title,22,HI);label(d,27,778,'OFFLINE MOCKUP · WAVEFORM / VALUES SIMULATED · LIVE STATE REQUIRES ENGINE TELEMETRY',11,AMB)
 im.save(O/f'perform-{name}.png')
mock('balanced','LIVING INSTRUMENT V2 / BALANCED','balanced')
mock('performance','LIVING INSTRUMENT V2 / PERFORMANCE','performance')
mock('experimental','LIVING INSTRUMENT V2 / EXPERIMENTAL','experimental')
# Map: names resolve back to actual C1.1 parameters; actions/continuous classes reflect code.
registry=json.load(open(R/'build/ghost-c11-demo/parameters.json'));idx={p['key']:i for i,p in enumerate(registry)}
interaction={
 'continuous':{'Density':'g_density','Chaos amount':'g_chaos','Motion depth':'g_mdepth','Dry/Wet':'mix_live','Length':'length','Break':'break','Chance':'g_chance'},
 'switches':{'Gate':'gate','Ghost enable':'g_ghost','Motion enable':'g_motion','Chaos enable':'g_chaoson','Freeze':'freeze'},
 'actions':{'Capture':'capture','Buffer Dice':'g_bufdice','Clean':'g_clean'},
 'unchanged_program_qlinks':{'1':'mix_live','2':'capture','3':'pitch','4':'state','5':'break','6':'buffer','7':'reverse','8':'mutation','9':'length','10':'position','11':'corrupt','12':'density','13':'gate','14':'freeze','15':'bend','16':'chance'}}
interaction['indices']={k:idx[v] for group in ('continuous','switches','actions') for k,v in interaction[group].items()}
interaction['note']='Informational mock map; touchscreen bindings and Q-Link assignments are unchanged/nonexistent in this prototype.'
(O/'interaction-map.json').write_text(json.dumps(interaction,indent=2))
print('Rendered three 1280x800 mockups and 8-state pixel sprite sheet.')
