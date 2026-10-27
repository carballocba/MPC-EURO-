#!/usr/bin/env python3
"""Audit and render the exported native graph, not an independent mockup."""
import ctypes as C,json,pathlib,sys
from PIL import Image,ImageDraw
from build import ROOT,DEFAULT,FOLDER,font,READONLY,sha
sys.path.insert(0,str(ROOT/'experiments/ghost-c1'))
from test_vst import FX

def param(c,current=None):
 for m in c.get('handle remapping',{}).get('map',[]):
  if str(m['value']).startswith('Parameter '):return int(m['value'].split()[1])
 return current
def visible(c,get):
 for h in c['bounds'].get('additionalInvalidatingHandles',[]):
  if h.startswith('IndexedEnabling/'):
   _,slot,total,p=h.split('/');idx=min(int(total)-1,int(get(int(p.split()[1]))*int(total)))
   if idx!=int(slot):return False
 return True
def intersects(a,b):return a[0]<b[0]+b[2] and b[0]<a[0]+a[2] and a[1]<b[1]+b[3] and b[1]<a[1]+a[3]
def exclusives(a,b):
 def sel(v):return {s.split('/')[3]:s.split('/')[1] for s in v if s.startswith('IndexedEnabling/')}
 x,y=sel(a),sel(b);return any(k in y and y[k]!=v for k,v in x.items())
def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=pathlib.Path,default=DEFAULT);args=ap.parse_args();out=args.out
 skin=out/'package'/FOLDER/'Plugin Skins';page=json.loads((skin/'TUI.json').read_text())['pageData'];defs={d['key']:d['value'] for d in page['componentDefinitions']['localComponentDefinitions']};graph=json.loads((out/'control-graph.json').read_text());problems=[];report=[]
 native=out/'engine/ghost-identity-test.so'
 if not native.exists():native=out/'ghost-identity-test.so'
 f=FX(native)
 try:
  f.d(f.fx,2,0,8,None,0)
  for k in range(200):f.block(index=k*128) # actual offline audio/capture telemetry
  def get(p):return f.get(f.fx,p)
  def display(p):
   buf=C.create_string_buffer(9);f.d(f.fx,7,p,0,buf,0);return buf.value.decode(errors='replace')
  def paint(im,children,ox=0,oy=86,current=None):
   draw=ImageDraw.Draw(im)
   for c in children:
    if not visible(c,get):continue
    x,y,w,h=map(int,c['bounds']['bounds'].split());x+=ox;y+=oy;p=param(c,current);cd=c['componentData'];d=cd.get('data',{});kind=cd['type']
    if kind in defs:paint(im,defs[kind]['componentsData'],x,y,p)
    elif kind=='Image':
     a=Image.open(skin/d['image']).convert('RGBA').resize((w,h));im.paste(a,(x,y),a)
    elif kind=='Knob':
     a=Image.open(skin/d['filmStrip']).convert('RGBA');frames=d['numFrames'];fh=a.height//frames;index=round(get(p)*(frames-1));a=a.crop((0,index*fh,a.width,(index+1)*fh)).resize((w,h));im.paste(a,(x,y),a)
    elif kind=='Button':
     selected=(min(d['numButtonsInGroup']-1,int(get(p)*(d['numButtonsInGroup']-1)+.5))==d['buttonId']) if d['numButtonsInGroup']>1 else get(p)>=.5
     a=Image.open(skin/d['onImage'] if selected else skin/d['offImage']).convert('RGBA').resize((w,h));im.paste(a,(x,y),a)
    elif kind=='Label':
     text=display(p);fs=d['textStyle']['font']['height'];glyph=font(int(fs)).getbbox(text)
     if glyph[2]-glyph[0]>w or glyph[3]-glyph[1]>h:problems.append(f'Clipped value {p}: {text}')
     draw.text((x+w//2,y+h//2),text,font=font(int(fs)),fill='#b3d6d1',anchor='mm')
  preview=out/'previews';preview.mkdir(exist_ok=True)
  for index,tab in enumerate(page['tabs']):
   rows=[r for r in graph if r['view']==tab['componentName'] and r['interactive']]
   for r in rows:
    x,y,w,h=r['bounds']
    if not (0<=x and 0<=y and x+w<=1280 and y+h<=628):problems.append('Out of viewport '+str(r))
   for i,a in enumerate(rows):
    for b in rows[i+1:]:
     if not exclusives(a['visibility'],b['visibility']) and intersects(a['bounds'],b['bounds']):problems.append('Overlap '+str((a,b)))
   focus=[r for r in rows if r['focus']];assert len(focus)==4
   for r,rect in zip(focus,tab['qlinkBoundsData']):assert r['bounds']==list(map(int,rect.split()))
   im=Image.new('RGB',(1280,800),'#090e11');ImageDraw.Draw(im).text((25,25),'OFFLINE NATIVE GRAPH / HARDWARE NAVIGATION + HIGHLIGHT PENDING',font=font(16),fill='#aabfc4');paint(im,defs[tab['componentName']]['componentsData']);im.save(preview/f'{index+1:02d}-{tab["componentName"].replace("|","-")}.png')
   report.append({'view':tab['componentName'],'controls':len(rows),'focus':[dict(parameter=r['parameter'],plugin_rect=r['bounds'],expected_host_rect=[r['bounds'][0],r['bounds'][1]+86,*r['bounds'][2:]]) for r in focus]})
 finally:f.close()
 report={'viewport':[1280,628],'host_preview_offset_y':86,'hardware_highlight':'PENDING; host owns final drawing','problems':problems,'views':report}
 (out/'geometry-report.json').write_text(json.dumps(report,indent=2)+'\n')
 if problems:raise SystemExit('\n'.join(problems))
 print('PASS nine exported views, touch geometry, value glyphs and four focus rectangles per view')
if __name__=='__main__':main()
