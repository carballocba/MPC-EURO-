#!/usr/bin/env python3
"""Offline only. Preserve hardware-tested PLAY, expose existing enable parameters."""
import argparse,copy,io,json,pathlib,subprocess,sys,xml.etree.ElementTree as ET,zipfile
import build_integration_recovery as b
from PIL import Image,ImageDraw,ImageFont
ROOT=b.ROOT
OUT=ROOT/'build/ghost-control-recovery/candidate'
def skin(files):
 tui=json.loads(files['Plugin Skins/TUI.json']);defs=tui['pageData']['componentDefinitions']['localComponentDefinitions']
 play=next(d['value'] for d in defs if d['key']=='PLAY|PLAY');children=play['componentsData']
 template=next(c for c in children if c['componentData']['name']=='PUNCH / CANCEL')
 button=next(d['value'] for d in defs if d['key']==template['componentData']['type'])
 font=ImageFont.truetype(str(ROOT/'vendor/fonts/DejaVuSansMono.ttf'),20)
 for x,label,param in [(30,'GHOST',49),(345,'CHAOS',104),(660,'MOTION',54),(975,'ROUTE',91)]:
  key='control_enable_'+str(param);d=copy.deepcopy(button)
  inner=next(c for c in d['componentsData'] if c['componentData']['type']=='Button')
  for state in ['on','off']:
   name=f'{key}_{state}.png';inner['componentData']['data'][state+'Image']=name
   image=Image.new('RGB',(205,56),'#253847' if state=='on' else '#141e28');draw=ImageDraw.Draw(image)
   draw.rectangle((0,0,204,55),outline='#eeb75b' if state=='on' else '#536b7a',width=2)
   draw.text((102,28),label+(' ON' if state=='on' else ' OFF'),font=font,anchor='mm',fill='#e6f6fa')
   s=io.BytesIO();image.save(s,format='PNG');files['Plugin Skins/'+name]=s.getvalue()
  defs.insert(-1,{'key':key,'value':d});c=copy.deepcopy(template);c['componentData']['name']=label;c['componentData']['type']=key
  c['handle remapping']['map'][0]['value']=f'Parameter {param}';c['bounds']['bounds']=f'{x} 350 205 56';children.append(c)
 # Preserve every existing component, tab, knob and Q-Link binding. Only add enables.
 files['Plugin Skins/TUI.json']=(json.dumps(tui,separators=(',',':'))+'\n').encode()
 assert b.referenced_images(tui)<=files.keys()
 return tui

def main():
 global OUT
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--out',type=pathlib.Path,default=OUT)
 OUT=parser.parse_args().out.resolve()
 if OUT.exists():raise SystemExit('Refusing to overwrite candidate')
 subprocess.run([sys.executable,str(ROOT/'experiments/ghost-c1/prepare.py')],check=True)
 OUT.mkdir(parents=True)
 source=ROOT/'build/ghost-integration-recovery/candidate/ghost-integration-recovery-armv7-OFFLINE.zip'
 assert b.sha(source.read_bytes())=='b84aad39a034c27dbde1c5fa9050a801dc9a54ccace4ce4f246b5a2a268e3904'
 files=b.zip_files(source,b.FOLDER+'/');files.pop('manifest.json');files.pop('SHA256SUMS')
 compiler=b.module(ROOT/'experiments/ghost-c12-2/build_independent_ghost.py','control_compiler');compiler.OUT=OUT/'engine';compiler.OUT.mkdir()
 binary,abi=compiler.compile_arm(True,strip_debug=True);native=compiler.compile_native_identity_test(True);files['ghost.so']=binary.read_bytes()
 tui=skin(files)
 v=ET.fromstring(files['version.xml']);v.find('version').text='2.2.0.2';files['version.xml']=ET.tostring(v,encoding='utf-8',xml_declaration=True)+b'\n'
 manifest={'candidate':'GHOST PLAY control recovery / OFFLINE','uid':1195922260,'xml_uid':'47485354','abi':abi,'hardware_validation':'PENDING','dsp_algorithms_changed':False,'integration_changes':['manual Gate/Punch priority','fresh live capture on Punch except Freeze','explicit Motion/route re-arm releases previous manual lease'],'files':{n:b.sha(v) for n,v in sorted(files.items())}}
 files['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode();files['SHA256SUMS']=''.join(f'{b.sha(v)}  {n}\n' for n,v in sorted(files.items())).encode()
 for n,v in files.items():
  p=OUT/'package'/b.FOLDER/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(v)
 path=OUT/'ghost-play-control-recovery-armv7-OFFLINE.zip'
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for n,v in sorted(files.items()):
   i=zipfile.ZipInfo(b.FOLDER+'/'+n,(2026,10,18,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,v)
 report={'zip':str(path),'zip_sha256':b.sha(path.read_bytes()),'binary_sha256':b.sha(files['ghost.so']),'native':str(native),'files':len(files),'abi':abi,'device_access':False,'hardware_validation':'PENDING'}
 (OUT/'build-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
