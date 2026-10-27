#!/usr/bin/env python3
"""Regenerate the eight project-authored sprites from their original pixel drawing function."""
import pathlib,ast,io,hashlib,json
from PIL import Image,ImageDraw
r=pathlib.Path(__file__).resolve().parent;t=ast.parse((r/'experiments/ghost-ui-v2/render.py').read_text());f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='sprite');scope=dict(Image=Image,ImageDraw=ImageDraw,BG='#0b1012');exec(compile(ast.Module(body=[f],type_ignores=[]),'<original-sprite-source>','exec'),scope)
results=[]
for name in ['idle','listen','capture','repeat','freeze','motion','chaos','clean']:
 im=scope['sprite'](name.upper()).convert('RGBA');im.thumbnail((100,96));canvas=Image.new('RGBA',(100,96),(0,0,0,0));canvas.alpha_composite(im,((100-im.width)//2,(96-im.height)//2));buf=io.BytesIO();canvas.save(buf,format='PNG',optimize=True);data=buf.getvalue()
 original=(r/'resources/Plugin Skins'/('pe_ghost_'+name+'.png')).read_bytes();assert data==original,name
 results.append(dict(state=name,sha256=hashlib.sha256(data).hexdigest(),byte_identical=True))
print(json.dumps(results,indent=2))
