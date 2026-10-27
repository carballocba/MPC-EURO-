#!/usr/bin/env python3
"""Generate audit artifacts from the single built product (offline only)."""
import ctypes as C,csv,hashlib,json,pathlib,sys
from PIL import Image,ImageDraw
from build import ROOT,DEFAULT,FOLDER,font
from elftools.elf.elffile import ELFFile
out=DEFAULT
rows=json.loads((out/'function-matrix.json').read_text());q=json.loads((out/'package'/FOLDER/'Plugin Skins/Q-Links.json').read_text())
for r in rows:
 ids={r['parameter']}
 if r['alias_of'] is not None:ids.add(r['alias_of'])
 r['qlinks']=[f'Tab {v["Tab"]}/Sub {v["SubTab"]}: {k}' for v in q['Screen Mode Q-Links']['map'] for k,p in v['Q-Links'].items() if p in ids]
 r['qlinks'] += ['Program: '+k for k,p in q['Program Mode Q-Links'].items() if p in ids]
(out/'function-matrix.json').write_text(json.dumps(rows,indent=2)+'\n')
with (out/'function-matrix.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Parameter','Function','State','Activation','GUI','Q-Link','Preset','Test','Notes'])
 for r in rows:w.writerow([r['parameter'],r['name'],r['state_path'],r['condition'],','.join(sorted({v['view'] for v in r['gui']})),','.join(r['qlinks']),r['preset'],r['test'],r['notes'] or ''])
text=['# GHOST — matriz completa de parámetros y acceso','', 'Generada del grafo nativo final: 126 índices, 0..123 conservados y aliases de reloj 124/125 añadidos. Los aliases no agregan estados DSP independientes. `state_path` en JSON, condiciones de activación, vistas, bounds y mapas están disponibles en los artefactos completos.','', '| ID | Función | GUI / alias | Q-Link | Persistencia / condición |','| --- | --- | --- | --- | --- |']
for r in rows:
 views=', '.join(sorted({v['view'].replace('|',' / ') for v in r['gui']})) or (r['notes'] or 'telemetría')
 text.append(f'| {r["parameter"]} | {r["name"]} | {views} | {"; ".join(r["qlinks"])} | {r["preset"]}: {r["condition"]} |')
(ROOT/'docs/ghost/GHOST_PRODUCT_MATRIX.md').write_text('\n'.join(text)+'\n')
attrs=[]
for p in sorted((out/'engine/arm-build').glob('unit-*.o')):
 with p.open('rb') as f:
  elf=ELFFile(f);a={}
  for s in elf.get_section_by_name('.ARM.attributes').iter_subsections():
   for ss in s.iter_subsubsections():
    for x in ss.iter_attributes():a[str(x.tag)]=x.value
  assert a.get('TAG_CPU_ARCH')==10 and a.get('TAG_ABI_VFP_ARGS')==1
  attrs.append({'file':p.name,'attributes':a})
assert len(attrs)==9
(out/'arm-objects.json').write_text(json.dumps(attrs,indent=2)+'\n')
canvas=Image.new('RGB',(3*640,3*400),'#090e11')
for i,p in enumerate(sorted((out/'previews').glob('*.png'))):canvas.paste(Image.open(p).resize((640,400)),((i%3)*640,(i//3)*400))
canvas.save(out/'previews/contact-sheet.png')
paths=[ROOT/'experiments/ghost-c1'/n for n in ['core.c','motion.c','params.c','state.c','vst.c','base.c','prepare.py','factory_product.h']]
paths += [ROOT/'src'/n for n in ['engine.c','plugin.c','repeat.c','vst2_abi.h']]
paths += [ROOT/'tools'/n for n in ['ghost_product.py','ghost-product-transaction.sh','ghost-product.command']]
paths += list((ROOT/'experiments/ghost-product').glob('*.py'))
paths += list((ROOT/'tests').glob('test_ghost_product*.py'))
paths += [ROOT/'tests/ghost_product_host.c',ROOT/'ui/params.json',ROOT/'ui/presets.json',ROOT/'build/params.h']
(out/'source-sha256.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
print('PASS matrix / CSV / ARMv7 attributes / contact sheet / source provenance')
