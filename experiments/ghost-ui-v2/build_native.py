"""Generate C1.2 PERFORM-only MPC-native prototype in an isolated build folder."""
import json, os, pathlib, runpy, shutil, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'build/ghost-c12-prototype';OUT.mkdir(parents=True,exist_ok=True)
shutil.rmtree(OUT/'native-skin',ignore_errors=True)
for preview in OUT.glob('gui-preview-*.png'):preview.unlink()
sys.path.insert(0,str(ROOT/'experiments/ghost-c1'))
import bindings
bindings.OUT=OUT
# Reuse the established native component exporter, replacing only its PERFORM layout.
asset_scope=runpy.run_path(str(ROOT/'experiments/ghost-ui-v2/render.py'))
layout_fragment=(ROOT/'experiments/ghost-ui-v2/perform.layout').read_text().splitlines()
from PIL import Image,ImageDraw,ImageFont
source=(ROOT/'experiments/ghost-c1/gui.py').read_text()
needle="for name,keys in pages:\n lines+=['\\n[tab '+name+']'"
replacement="for name,keys in pages:\n if name=='PERFORM':\n  lines.extend((ROOT/'experiments/ghost-ui-v2/perform.layout').read_text().splitlines());continue\n lines+=['\\n[tab '+name+']'"
assert source.count(needle)==1
source=source.replace(needle,replacement)
source=source.replace('GHOST C1.1 OFFLINE PREVIEW','GHOST C1.2 BALANCED PROTOTYPE')
source=source.replace('GHOST C1.1 /','GHOST C1.2 /')
old_grid="x=130+245*(j%4);y=220+130*(j//4);p=lookup[key]"
new_grid="x=130+245*(j%4);y=220+130*(j//4);y+=(90 if name=='MOTION' and 8<=j<12 else 45 if ((name=='MOTION' and 4<=j<8) or (name=='GENERATIVE' and 4<=j<12) or (name=='SETTINGS' and 8<=j<12)) else 0);p=lookup[key]"
assert source.count(old_grid)==1
source=source.replace(old_grid,new_grid)
old_append="lines.append(line+condition)"
new_append="if name=='BUFFER' and key=='buffer':line=f'knob cx={x} cy={y-18} r=21 bw=180 key=buffer ns=16 vs=20'\n   if name=='BUFFER' and key=='g_dest':line=f'knob cx={x} cy={y-18} r=21 bw=180 key=g_dest ns=16 vs=20'\n   lines.append(line+condition)"
assert source.count(old_append)==1
source=source.replace(old_append,new_append)
source=source.replace('Five native pages, eight DSP-bound mascot states, skin geometry checks passed:',
                      'Five top-level pages with four PERFORM Q-Link banks; eight status-linked mascot states; geometry checks passed:')
old_format='else f\'{p["default"]:.2f} {p.get("unit","")}\''
new_format='''else ('EMPTY' if p['key']=='g_take' and p['default']<.5 else 'TAKE' if p['key']=='g_take' else p['options'][int(p['default'])] if p.get('options') else f'{p["default"]:.0f}' if p['key']=='g_density' else f'{p["default"]*100:.2f} %' if p['key'] in ('g_chaos','g_mdepth','g_chance','g_energy') else f'{p["default"]:.2f} {p.get("unit","")}')'''
assert source.count(old_format)==1
source=source.replace(old_format,new_format)
exec(compile(source,str(ROOT/'experiments/ghost-c1/gui.py'),'exec'),{'__name__':'__main__'})
# The status sprites change only on genuine state telemetry; preserve the other pages' C1.1 art.
skin=OUT/'native-skin/MPC-EURO - VST - BeatRepeat/Plugin Skins'
for i,state in enumerate(['idle','listen','capture','repeat','freeze','motion','chaos','clean']):
 src=ROOT/f'build/ghost-ui-concepts/v2/ghost-{state}.png'
 assert src.is_file(),src
 (skin/f'v2-ghost-{state}.png').write_bytes(src.read_bytes())
tui_path=skin/'TUI.json';tui=json.loads(tui_path.read_text())
defs={x['key']:x['value'] for x in tui['pageData']['componentDefinitions']['localComponentDefinitions']}
for ti,tab in enumerate(tui['pageData']['tabs']):
 key=tab['componentName'];children=defs[key]['componentsData']
 if ti==0:
  for c in children:
   name=c['componentData']['name']
   if name.startswith('Ghost '):
    state=name.split(' ',1)[1].lower()
    c['componentData']['data']['image']=f'v2-ghost-{state}.png'
  # Keep all eight status-linked mascot states; add an input-energy level bar from real telemetry.
  sys.path.insert(0,str(ROOT/'vendor/mpc/tools'))
  import shadow_skin as sk
  energy_index=49+bindings.IDS['P_ENERGY']
  for level in range(8):
   im=Image.new('RGBA',(150,18),(0,0,0,0));draw=ImageDraw.Draw(im);draw.rounded_rectangle((0,5,149,13),radius=4,fill='#2b3b49')
   if level:draw.rounded_rectangle((0,5,round(149*level/7),13),radius=4,fill='#65dbc6')
   filename=f'v2-energy-{level}.png';im.save(skin/filename)
   bounds=sk._bounds(740,250,150,18,focus='No',show='Hide')
   bounds['additionalInvalidatingHandles']=[f'IndexedEnabling/{level}/8/Parameter {energy_index}']
   children.append(sk._sub('Image',{'version':1,'image':filename},bounds,f'Energy level {level}'))
  # shadow_skin names enum art by parameter key alone. The legacy BUFFER and MOTION pages
  # reuse Freeze/Motion with different sizes, overwriting the PERFORM art. Give PERFORM
  # private assets and definitions while leaving those existing pages untouched.
  definitions=tui['pageData']['componentDefinitions']['localComponentDefinitions']
  by_key={d['key']:d for d in definitions}
  font_path=pathlib.Path('/System/Library/Fonts/Supplemental/Arial.ttf')
  font=ImageFont.truetype(str(font_path),17) if font_path.is_file() else ImageFont.load_default()
  # Enum PNG names are global in the skin. C1.1's BUFFER Freeze (LIVE/FROZEN),
  # PERFORM Freeze (LIVE/HELD), and two Motion controls reused the same image
  # names, so the font pass wrote multiple labels on top of each other. Give
  # each page its own native radio definitions and clean, correctly sized art.
  enum_views=(
   ('PERFORM|01 / CORE','freeze',('LIVE','HELD'),'perform-freeze',70,56),
   ('PERFORM|02 / REPEAT','freeze',('LIVE','HELD'),'perform-freeze',70,56),
   ('PERFORM|03 / ENGINE','freeze',('LIVE','HELD'),'perform-freeze',70,56),
   ('PERFORM|04 / ACTION','freeze',('LIVE','HELD'),'perform-freeze',70,56),
   ('BUFFER|BUFFER','freeze',('LIVE','HELD'),'buffer-freeze',95,56),
   ('PERFORM|01 / CORE','g_motion',('OFF','ON'),'perform-motion',62,56),
   ('PERFORM|02 / REPEAT','g_motion',('OFF','ON'),'perform-motion',62,56),
   ('PERFORM|03 / ENGINE','g_motion',('OFF','ON'),'perform-motion',62,56),
   ('PERFORM|04 / ACTION','g_motion',('OFF','ON'),'perform-motion',62,56),
   ('MOTION|MOTION','g_motion',('OFF','ON'),'motion-page',98,44),
  )
  for page_key,param,labels,scope,width,height in enum_views:
   page_def=by_key[page_key]['value']
   for slot,label in enumerate(labels):
    source_def=by_key[f'shSeg_{param}_{slot}']['value']
    clone=json.loads(json.dumps(source_def))
    slug=label.lower()
    clone_key=f'c12{scope.title().replace("-", "")}_{slug}'
    data=clone['componentsData'][0]['componentData']['data']
    data['onImage']=f'c12-{scope}-{slug}-on.png'
    data['offImage']=f'c12-{scope}-{slug}-off.png'
    clone['componentsData'][0]['bounds']['bounds']=f'0 0 {width} {height}'
    definitions.append({'key':clone_key,'value':clone})
    for component in page_def.get('componentsData',[]):
     name=component['componentData']['name']
     if component['componentData']['type']==f'shSeg_{param}_{slot}':
      component['componentData']['type']=clone_key
      component['componentData']['name']=f'{param} {label}'
    for selected in (False,True):
     im=Image.new('RGBA',(width,height),'#10151b');draw=ImageDraw.Draw(im)
     draw.rounded_rectangle((1,1,width-2,height-2),radius=8,fill='#65dbc6' if selected else '#26333e',outline='#65dbc6' if selected else '#435361',width=2)
     box=draw.textbbox((0,0),label,font=font)
     draw.text(((width-(box[2]-box[0]))/2,(height-(box[3]-box[1]))/2-1),label,font=font,fill='#10151b' if selected else '#e9edf1')
     im.save(skin/f'c12-{scope}-{slug}-{"on" if selected else "off"}.png')
  import skin_check
  errors=skin_check.check(str(skin))
  if errors:raise SystemExit('Native skin validation failed: '+'; '.join(errors))
  break
# Punch is a touch-only immediate action. Keep it visible in the ACTION bank,
# but do not let this extra control acquire Q-Link host focus.
for definition in tui['pageData']['componentDefinitions']['localComponentDefinitions']:
 for component in definition['value'].get('componentsData',[]):
  if component.get('componentData',{}).get('name')=='PUNCH':
   component['bounds']['acceptsHWFocus']='No'
(tui_path).write_text(json.dumps(tui,separators=(',',':')))
sys.path.insert(0,str(ROOT/'experiments/ghost-ui-v2'))
import native_geometry
geometry=native_geometry.audit_and_render()
if geometry['problems']:
 raise SystemExit('Native geometry audit failed: '+'; '.join(geometry['problems']))
# Build a host-native VST for offline wrapper tests, reusing the protected C1.1 integration include.
reference_include=ROOT/'build/ghost-c11-demo/base-render.inc'
if not reference_include.is_file():raise SystemExit('Missing validated C1.1 base-render include; refusing to regenerate it')
cc=shutil.which('cc')
if not cc:raise SystemExit('A C compiler is required for the native offline test binary')
cwd=ROOT/'experiments/ghost-c1';base_obj=OUT/'base-plugin.o';native_vst=OUT/'beatrepeat-ghost-c1.so'
flags=['-std=c11','-Wall','-Wextra','-Werror','-ffp-contract=off','-I../../src','-I../ghost','-I.','-I../../build','-O2','-fPIC']
subprocess.run([cc,*flags,'-c','base.c','-o',str(base_obj)],cwd=cwd,check=True)
subprocess.run([cc,*flags,'-shared','core.c','motion.c','params.c','state.c','../ghost/ghost.c','../../src/engine.c','vst.c',str(base_obj),'../../src/repeat.c','-lm','-pthread','-o',str(native_vst)],cwd=cwd,check=True)
print('Generated isolated native skin:',skin)
print('Generated native offline VST:',native_vst)
