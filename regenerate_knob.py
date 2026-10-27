import pathlib,subprocess,sys,hashlib,zipfile,json
from PIL import Image
R=pathlib.Path(__file__).resolve().parent;O=R/'knob-rebuild';O.mkdir(exist_ok=True);src=R/'vendor/mpc/tools';exe=O/'shadow-art';cmd=['cc','-O2','-I'+str(src/'vendor/force-shadow/tools'),str(src/'shadow_art.c'),'-lm','-o',str(exe)];subprocess.run(cmd,check=True)
ppm=O/'sh_knob_r32.ppm';script='theme|'+str(R/'ui/layout.conf')+'\nstrip|'+str(ppm)+'|32|128|10151b\n';subprocess.run([str(exe)],input=script,text=True,check=True);im=Image.open(ppm);out=O/'sh_knob_r32.png';im.save(out)
original=(R/'resources/Plugin Skins/sh_knob_r32.png').read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest();import io
report=dict(status='BYTE-IDENTICAL' if out.read_bytes()==original else 'PIXEL-IDENTICAL' if im.convert('RGB').tobytes()==Image.open(io.BytesIO(original)).convert('RGB').tobytes() else 'MISMATCH',original_sha256=sha(original),regenerated_sha256=sha(out.read_bytes()),generator='vendor/mpc/tools/shadow_art.c',source_sha256=sha((src/'shadow_art.c').read_bytes()),theme='ui/layout.conf',theme_sha256=sha((R/'ui/layout.conf').read_bytes()),command=script.replace(str(R),'<SOURCE_ROOT>'),dimensions=im.size,terms='MIT; sd88me2026; force-shadow MIT retained; no firmware or Akai asset input',device_access=False)
(O/'ASSET_REGENERATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
