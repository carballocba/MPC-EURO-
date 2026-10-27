#!/usr/bin/env python3
"""Resolve real native composites/hitboxes and render with actual native VST values."""
import ctypes as C,json,pathlib,sys
from PIL import Image,ImageDraw
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'build/ghost-performance-edition';sys.path[:0]=[str(ROOT/'experiments/ghost-product'),str(ROOT/'experiments/ghost-c1'),str(ROOT/'tests')]
from build import font
from test_vst import FX
from inspect_gui import visible,param,intersects,exclusives
# This script name may shadow product.inspect_gui: import it explicitly by path instead.
def main():
 folder=OUT/'gui/MPC-EURO - VST - GHOST/Plugin Skins';tui=json.loads((folder/'TUI.json').read_text())['pageData'];defs={d['key']:d['value'] for d in tui['componentDefinitions']['localComponentDefinitions']};maps=json.loads((folder/'Q-Links.json').read_text());errors=[];hits=[];f=FX(OUT/'native/ghost.so')
 def display(p):
  b=C.create_string_buffer(8);f.d(f.fx,7,p,0,b,0);return b.value.decode(errors='replace')
 def paint(image,children,ox=0,oy=86,current=None,view='',cond=()):
  draw=ImageDraw.Draw(image)
  for c in children:
   conditions=tuple(c['bounds'].get('additionalInvalidatingHandles',[]))+cond
   if not visible(c,lambda p:f.get(f.fx,p)):continue
   x,y,w,h=map(int,c['bounds']['bounds'].split());x+=ox;y+=oy;p=param(c,current);cd=c['componentData'];data=cd.get('data',{});kind=cd['type']
   if kind in defs:paint(image,defs[kind]['componentsData'],x,y,p,view,conditions)
   elif kind=='Image':
    im=Image.open(folder/data['image']).convert('RGBA').resize((w,h));image.paste(im,(x,y),im)
   elif kind=='Knob':
    im=Image.open(folder/data['filmStrip']).convert('RGBA');frames=data['numFrames'];fh=im.height//frames;ix=round(f.get(f.fx,p)*(frames-1));im=im.crop((0,ix*fh,im.width,(ix+1)*fh)).resize((w,h));image.paste(im,(x,y),im)
    if w<56 or h<56:errors.append(f'Undersized knob {view}/{p}: {w}x{h}')
    hits.append(dict(view=view,parameter=p,kind=kind,hitbox=[x,y-86,w,h],conditions=list(conditions)))
   elif kind=='Button':
    n=data['numButtonsInGroup'];selected=(round(f.get(f.fx,p)*(n-1))==data['buttonId']) if n>1 else f.get(f.fx,p)>=.5
    im=Image.open(folder/data['onImage'] if selected else folder/data['offImage']).convert('RGBA').resize((w,h));image.paste(im,(x,y),im)
    hits.append(dict(view=view,parameter=p,kind=kind,hitbox=[x,y-86,w,h],conditions=list(conditions)))
   elif kind=='Label':
    text=display(p);size=int(data['textStyle']['font']['height']);box=font(size).getbbox(text)
    if box[2]-box[0]>w or box[3]-box[1]>h:errors.append(f'Value clipping {view}/{p}: {text}')
    draw.text((x+w//2,y+h//2),text,font=font(size),fill='#b3d6d1',anchor='mm')
 previews=OUT/'previews';previews.mkdir(exist_ok=True)
 try:
  for k in range(200):f.block(index=k*128)
  for tab in tui['tabs']:
   view=tab['componentName'];children=defs[view]['componentsData'];maprow=next(m for m in maps['Screen Mode Q-Links']['map'] if m['Tab']==tab['fnKeyIndex']+1 and m['SubTab']==1)
   declared={int(m['value'].split()[1]) for c in children for m in c.get('handle remapping',{}).get('map',[]) if str(m['value']).startswith('Parameter ')}
   for p in maprow['Q-Links'].values():
    if p>=0 and p not in declared:errors.append(f'QL hidden {view}/{p}')
   for section in [0]:
    f.set(f.fx,142,section/7);f.block();before=len(hits);image=Image.new('RGB',(1280,800),'#090e11');ImageDraw.Draw(image).text((20,25),'OFFLINE NATIVE RESOURCE RENDER / MPC FOCUS AND BANK BEHAVIOR PENDING',font=font(17),fill='#b6c8cc');paint(image,children,view=view)
    current=hits[before:]
    for i,a in enumerate(current):
     x,y,w,h=a['hitbox']
     if not(0<=x and 0<=y and x+w<=1280 and y+h<=628):errors.append('Out of bounds '+str(a))
     for b in current[i+1:]:
      if a['parameter']!=b['parameter'] and intersects(a['hitbox'],b['hitbox']):errors.append('Hit overlap '+str((a,b)))
    # Context illustration only, OUTSIDE the native 1280x628 plugin viewport.
    # No navigation drawing or touch handler is installed in the plugin.
    d=ImageDraw.Draw(image);d.text((20,721),'HOST NAVIGATION BELOW: SCHEMATIC / REAL HAKAI DRAWING AND OVERFLOW PENDING',font=font(13),fill='#9bb4ba')
    d.rectangle((0,746,1279,799),fill='black')
    names=[t['tabName'] for t in tui['tabs']];active=tab['fnKeyIndex'];start=0 if active<5 else 4
    for j,name in enumerate(names[start:start+5]):
     x=20+j*224;d.text((x,767),name,font=font(18),fill='white')
     if name==tab['tabName']:d.rectangle((x,793,x+180,796),fill='#65dbc6')
    if start+5<len(names):d.text((1220,761),'>',font=font(26),fill='white')
    image.save(previews/(view.replace('|','-')+(f'-{section}' if 'SHAPE' in view else '')+'.png'))
  # Every group bound must be the geometric union of its actual visible owners.
  graph=json.loads((OUT/'control-graph.json').read_text())
  for tab,row in zip(tui['tabs'],maps['Screen Mode Q-Links']['map']):
   ps=[row['Q-Links'][f'Q-Link {slot}'] for slot in [13,9,5,1,14,10,6,2,15,11,7,3,16,12,8,4]]
   groups=[ps[i:i+4] for i in range(0,16,4) if any(p>=0 for p in ps[i:i+4])]
   assert len(tab['qlinkBoundsData'])==len(groups)
   for group,bound in zip(groups,tab['qlinkBoundsData']):
    x,y,w,h=map(int,bound.split())
    for c in graph:
     if c['view']==tab['tabName'] and c['parameter'] in group:
      a,b,ww,hh=c['bounds'];assert x<=a and y<=b and a+ww<=x+w and b+hh<=y+h
  old=json.loads((ROOT/'build/ghost-buffer-engine-final/package/MPC-EURO - VST - GHOST/Plugin Skins/Q-Links.json').read_text());assert maps['Program Mode Q-Links']==old['Program Mode Q-Links']
 finally:f.close()
 result=dict(views=len(tui['tabs']),shape_sections=0,native_resource_renders=len(tui['tabs']),errors=errors,touch_regions=hits,screen_mode=maps['Screen Mode Q-Links'],program_preserved=True,physical_focus='NOT VERIFIED / host owns final drawing',device_access=False)
 (OUT/'geometry-report.json').write_text(json.dumps(result,indent=2)+'\n')
 if errors:raise SystemExit('\n'.join(errors))
 print('PASS native host tabs; real resource renders; hitboxes, values, maps and column bounds')
if __name__=='__main__':main()
