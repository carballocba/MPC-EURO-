#!/usr/bin/env python3
"""Validate real skin geometry, assets, actions, registry and plugin bindings."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'vendor/mpc/tools'))
import skin_check
sys.path.insert(0,str(root/'tests'))
from test_shared import Plugin
skin=root/'build/skin/MPC-EURO - VST - BeatRepeat/Plugin Skins'
tui=json.loads((skin/'TUI.json').read_text()); q=json.loads((skin/'Q-Links.json').read_text())
params=json.loads((root/'ui/params.json').read_text())
assert [x['key'] for x in params]==['length','gate','mix','gain','punch','bypass','active','status']
assert not skin_check.check(str(skin))
tabs=tui['pageData']['tabs'];assert len(tabs)==1 and tabs[0]['initialSize']=='0 0 1280 628'
defs={x['key']:x['value'] for x in tui['pageData']['componentDefinitions']['localComponentDefinitions']}
kids=defs[tabs[0]['componentName']]['componentsData']
bound={}
for c in kids:
    for m in c.get('handle remapping',{}).get('map',[]):
        if str(m['value']).startswith('Parameter '):
            i=int(m['value'].split()[1]);assert 0<=i<len(params);bound.setdefault(i,[]).append(c)
assert set(range(8))<=set(bound)
for i in [0,1,2,3,4,5]:
    assert any(defs.get(c['componentData']['type'],{}).get('actions') for c in bound[i])
    assert any(float(c['bounds']['bounds'].split()[2])>=100 for c in bound[i])
for i in [6,7]:
    assert all(not defs.get(c['componentData']['type'],{}).get('actions') for c in bound[i])
slots=q['Screen Mode Q-Links']['map'][0]['Q-Links']
# Bottom-up column ordering from the inspected native community generator.
assert [slots[f'Q-Link {n}'] for n in [13,9,5,1,14,10]]==[0,1,2,3,4,5]
def walk(x):
    if isinstance(x,dict):
        for k,v in x.items():
            if k in ['image','filmStrip','offImage','onImage'] and v:
                assert (skin/v).is_file(),v
                with Image.open(skin/v) as im:
                    im.verify()
            if k=='type':assert v!='Meter' # Known unsupported native component
            walk(v)
    elif isinstance(x,list):
        for v in x:walk(v)
walk(tui)
entry=ET.fromstring((root/'build/pluginlist-entry.xml').read_text())
assert entry.attrib['uid']=='45754272' and entry.attrib['isInstrument']=='0'
# Simulate the exported GUI's parameter actions against the real shared .so.
p=Plugin()
for i,x in [(0,0.7),(1,1),(2,0.4),(3,0.8),(5,1)]:
    p.set(p.fx,i,x);assert abs(p.get(p.fx,i)-x)<0.000001
    assert p.display(i)
for i in [6,7]:
    old=p.get(p.fx,i);p.set(p.fx,i,1);assert p.get(p.fx,i)==old
p.close()
print('PASS 8 skin checks: geometry, touch actions, assets, 8 bindings, Q-Links, read-only status, metadata, real plugin actions')
