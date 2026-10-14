#!/usr/bin/env python3
"""Use the pinned community native-skin generator; only original layout/art."""
import json
import os
import shutil
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root/'vendor/mpc/tools'))
import shadow_skin
import skin_check
os.chdir(root)
os.environ['SHADOW_TITLE_FONT']=str(root/'vendor/fonts/DejaVuSansMono.ttf')
params = json.loads((root/'ui/params.json').read_text())
dest = root/'build/skin'
if dest.exists(): shutil.rmtree(dest)
folder = Path(shadow_skin.write_skin(str(dest),'MPC-EURO','BeatRepeat',str(root/'ui/layout.conf'),params,str(root/'build/shadow_art')))
skin=folder/'Plugin Skins'
version=folder/'version.xml'
version.write_text(version.read_text().replace('1.0.0.0','0.1.0.0'))
errors=skin_check.check(str(skin))
if errors: raise SystemExit('\n'.join(errors))
# Add original deterministic scan-line/fragment marks to generated backgrounds.
# No imported logos, stock panels or plugin artwork. Live controls remain native.
for p in skin.glob('sh_bg*.png'):
    im=Image.open(p).convert('RGB'); draw=ImageDraw.Draw(im)
    for x in range(40,1240,19):
        draw.line((x,55,x+8,55),fill=(20,224,196) if (x//19)%3 else (255,68,125),width=2)
    im.save(p)
# Replace the renderer's decorative bitmap lettering with clear, original
# typesetting. The exported native controls and their dynamic labels are intact.
widgets=shadow_skin.parse_layout(str(root/'ui/layout.conf'))[0][0]['widgets']
font_path=str(root/'vendor/fonts/DejaVuSansMono.ttf')
bg=skin/'sh_bg_0.png';im=Image.open(bg).convert('RGB');dr=ImageDraw.Draw(im)
for w in widgets:
    if w['kind']=='text' and not w.get('when'):
        x,y,bw,bh=shadow_skin.text_box(w);y-=86
        dr.rectangle((x,y,x+bw,y+bh),fill='#0b1018')
        font=ImageFont.truetype(font_path,round(float(w.get('size',1.5))*14))
        dr.text((w['cx'],w['cy']-86),w['label'],font=font,anchor='mm',fill='#'+w.get('color','e6f6fa'))
    elif w['kind']=='readout':
        y=w['cy']-w['h']//2-22-86
        dr.rectangle((w['cx']-w['w']//2,y-4,w['cx']+w['w']//2,y+18),fill='#0b1018')
        dr.text((w['cx']-w['w']//2,y),w['label'],font=ImageFont.truetype(font_path,17),fill='#8ba6b1')
im.save(bg)
for i,w in enumerate(q for q in widgets if q.get('when')):
    path=skin/f'sh_mode_0_{i}.png';im=Image.open(path).convert('RGB');dr=ImageDraw.Draw(im)
    dr.rectangle((0,0,im.width,im.height),fill='#0b1018')
    font=ImageFont.truetype(font_path,15)
    dr.text((im.width/2,im.height/2),w['label'],font=font,anchor='mm',fill='#'+w['color'])
    im.save(path)
# Host metadata is inspect-only: this script never registers or installs.
(root/'build/pluginlist-entry.xml').write_text(
    '<PLUGIN name="BeatRepeat" descriptiveName="BeatRepeat" format="VST" category="Effect" '
    'manufacturer="MPC-EURO" version="0.1.0" '
    'file="/sdcard/Synths/MPC-EURO - VST - BeatRepeat/beatrepeat.so" uid="45754272" '
    'isInstrument="0" fileTime="0" infoUpdateTime="0" numInputs="2" numOutputs="2" isShell="0"/>\n')
# Preview is generated from exactly the exported component definitions/assets.
# Native value labels are represented with initial values here only; the skin
# binds them to real VST indices on the device.
tui=json.loads((skin/'TUI.json').read_text())
defs={x['key']:x['value'] for x in tui['pageData']['componentDefinitions']['localComponentDefinitions']}
tab=tui['pageData']['tabs'][0]
preview=Image.new('RGB',(1280,800),(11,16,24))
def rect(s): return tuple(round(float(x)) for x in s.split())
def paint(children,ox,oy,param=None):
    for c in children:
        handles=c['bounds'].get('additionalInvalidatingHandles',[])
        if any(s.startswith('IndexedEnabling/1/') for s in handles): continue
        local=param
        for m in c.get('handle remapping',{}).get('map',[]):
            if m['key']=='Data' and m['value'].startswith('Parameter '): local=int(m['value'].split()[1])
        d=c['componentData']; x,y,w,h=rect(c['bounds']['bounds']); x+=ox; y+=oy
        data=d.get('data',{})
        kind=d['type']
        if kind in defs: paint(defs[kind].get('componentsData',[]),x,y,local)
        elif kind=='Image':
            f=data.get('image','')
            if f and (skin/f).exists():
                im=Image.open(skin/f).convert('RGBA').resize((w,h)); preview.paste(im,(x,y),im)
        elif kind=='Knob' and data.get('filmStrip'):
            im=Image.open(skin/data['filmStrip']).convert('RGBA')
            t=(params[local]['default']-params[local]['min'])/(params[local]['max']-params[local]['min']) if local is not None else 0
            fy=round(t*(im.height//im.width-1))*im.width
            frame=im.crop((0,fy,im.width,fy+im.width)).resize((w,h)); preview.paste(frame,(x,y),frame)
        elif kind=='Label' and local is not None:
            p=params[local];style=data['textStyle'];font=ImageFont.truetype(str(root/'vendor/fonts/DejaVuSansMono.ttf'),round(style['font']['height']))
            name=data.get('type')=='Name'
            label=p['name'] if name else (p['options'][int(p['default'])] if p.get('options') else f"{p['default']:.1f} {p.get('unit','')}")
            dr=ImageDraw.Draw(preview);box=dr.textbbox((0,0),label,font=font)
            dr.text((x+(w-box[2])/2,y+(h-box[3]+box[1])/2-box[1]),label,fill='#'+style['colour'][-6:],font=font)
        elif kind=='Button' and data.get('offImage'):
            im=Image.open(skin/data['offImage']).convert('RGBA').resize((w,h));preview.paste(im,(x,y),im)
paint(defs[tab['componentName']]['componentsData'],0,86)
draw=ImageDraw.Draw(preview)
draw.text((40,25),'MPC NATIVE HOST AREA / SKIN PREVIEW',(139,166,177))
draw.text((40,760),'1280 x 800  |  Active plugin area: y=86..714  |  Runtime values are host drawn',(139,166,177))
preview.save(root/'build/gui-preview.png')
print('Skin:',folder,'(community geometry/overlap checks passed)')
