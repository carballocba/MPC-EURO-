#!/usr/bin/env python3
"""Single offline buffer-engine candidate. Never contacts a device."""
import copy,ctypes as C,hashlib,importlib.util,json,pathlib,struct,subprocess,sys,xml.etree.ElementTree as ET,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'build/ghost-buffer-engine-final'
sys.path[:0]=[str(ROOT/'experiments/ghost-product'),str(ROOT/'experiments/ghost-c12-2'),str(ROOT/'experiments/ghost-c1')]
import build as product
import build_independent_ghost as compiler
sha=product.sha

def main():
 OUT.mkdir(exist_ok=True)
 archive=OUT/'ghost-buffer-engine-armv7-TRIAL.zip'
 if archive.exists():raise SystemExit('Refusing to overwrite a packaged candidate')
 subprocess.run([sys.executable,str(ROOT/'experiments/ghost-c1/prepare.py')],check=True)
 compiler.OUT=OUT
 binary,abi=compiler.compile_arm(strip_debug=True,final_product=True,buffer_engine=True)
 native=compiler.compile_native_identity_test(final_product=True,buffer_engine=True)
 source=ROOT/'build/ghost-functional-final/ghost-living-instrument-armv7-TRIAL.zip'
 assert sha(source.read_bytes())=='1d2986ca3d36bb631f240b54d4d21a5f1bd8d735ac3471044b3311379d7eda1a'
 reference=ROOT/'build/ghost-integration-recovery/candidate/ghost-integration-recovery-armv7-OFFLINE.zip'
 assert sha(reference.read_bytes())=='b84aad39a034c27dbde1c5fa9050a801dc9a54ccace4ce4f246b5a2a268e3904'
 files=product.ref.zip_files(reference,product.FOLDER+'/')
 files.pop('manifest.json');files.pop('SHA256SUMS');files['ghost.so']=binary.read_bytes()
 product.NAMES.update({126:'Capture',127:'REC max',128:'Live Repeat',129:'Record state',130:'Record fill'})
 # Existing one-shot parameter indices remain unchanged; only Capture UI binds new latch.
 product.BANKS=[(n,[126 if p==10 else p for p in ps]) for n,ps in product.BANKS]
 product.COMMON=[126 if p==10 else p for p in product.COMMON]
 product.DEEP=[(a,b,t,s,[126 if p==10 else p for p in f],e) for a,b,t,s,f,e in product.DEEP]
 product.COMMANDS.add(126) # Proven single-button ToggleSwitch, NOT a momentary command in DSP.
 product.COMMANDS.add(128)
 original_readout=product.Skin.readout
 def readout(self,p,title,rect):return original_readout(self,p,'BUFFER READY' if p==101 else title,rect)
 product.Skin.readout=readout
 original=product.Skin.make_view
 def make_view(self,*args):
  original(self,*args)
  # Guidance matches the new state machine, using no simulated signal graphics.
  from PIL import Image,ImageDraw
  import io
  area,bank=args[:2];bgname='Plugin Skins/product_bg_'+area+'_'+bank+'.png'
  if area=='BUFFER':
   im=Image.open(io.BytesIO(self.files[bgname]));draw=ImageDraw.Draw(im);draw.rectangle((0,600,1279,627),fill=product.BG)
   draw.text((26,608),'LIVE: REVERSE / LIVE REPEAT. CAPTURE: TAP START / TAP COMMIT -> HELD. CLEAN STOPS; MATERIAL RETAINED.',font=product.font(13),fill='#95adb0')
   self.files[bgname]=product.png(im)
  root=self.defs[-1]['value'];children=root['componentsData'];view=self.views[-1]['view']
  children += [self.control(127,(950,75,128,64)),self.control(128,(800,8,200,58))]
  children += self.readout(129,'RECORD / FULL',(544,8,216,58))
  for p,b in [(127,[950,75,128,64]),(128,[800,8,200,58]),(129,[552,32,200,31])]:
   self.graph.append({'view':view,'parameter':p,'name':product.NAMES[p],'bounds':b,'focus':False,'visibility':[],'interactive':p!=129})
 product.Skin.make_view=make_view
 skin=product.Skin(files);tui=skin.finish()
 # Persistent controls have explicit state captions, unlike legacy one-shot actions.
 from PIL import Image,ImageDraw
 import io
 for key,d in skin.composites.items():
  if not (key.startswith('product_126_') or key.startswith('product_128_')):continue
  p=int(key.split('_')[1]);button=next(c for c in d['componentsData'] if c['componentData']['type']=='Button')
  for state in ('on','off'):
   name='Plugin Skins/'+button['componentData']['data'][state+'Image'];im=Image.open(io.BytesIO(files[name]));draw=ImageDraw.Draw(im)
   label=('REC / TAP TO END' if state=='on' else 'TAP TO RECORD') if p==126 else state.upper()
   draw.text((12,im.height-25),label,font=product.font(14),fill=product.ACCENT if state=='on' else '#9bb1b5');files[name]=product.png(im)
 # Program Mode Capture assignment follows same latch as Screen mode; other 15 unchanged.
 for n in ('Q-Links.json','Q-Links - 8by1.json'):
  key='Plugin Skins/'+n;q=json.loads(files[key])
  def remap(x):
   if isinstance(x,dict):
    for k,v in x.items():
     if k.startswith('Q-Link ') and v==10:x[k]=126
     else:remap(v)
   elif isinstance(x,list):
    for v in x:remap(v)
  remap(q);files[key]=(json.dumps(q,indent=2)+'\n').encode()
 used=product.ref.referenced_images(tui)
 files={n:v for n,v in files.items() if not n.startswith('Plugin Skins/') or n in used or n.endswith('.json')}
 assert used<=files.keys()
 f=product.FX(native);presets=[]
 try:
  f.d(f.fx,12,0,0,None,0)
  for index in range(16):
   assert f.d(f.fx,2,0,index,None,0)==1
   name=C.create_string_buffer(25);f.d(f.fx,29,index,0,name,0);name=name.value.decode();data=f.chunk();assert data.startswith(b'GBF1')
   raw=struct.pack('>4sI4sIIII28sI',b'CcnK',52+len(data),b'FPCh',1,0x47485354,2000,1,name.encode()[:27].ljust(28,b'\0'),len(data))+data
   stem=f'{index:02d}-'+''.join(c if c.isalnum() else '-' for c in name);files['Presets/'+stem+'.fxp']=raw
   presets.append({'program':index,'name':name,'sha256':sha(data)})
 finally:f.close()
 files['Presets/index.json']=(json.dumps(presets,indent=2)+'\n').encode()
 params=json.loads((ROOT/'build/ghost-functional-final/parameters.json').read_text())
 for key,name,default,saved in [('g_capture_latch','Capture',0,False),('g_capture_max','REC max',1,True),('g_live_repeat','Live Repeat',0,True),('g_record_state','Record state',0,False),('g_record_fill','Record fill',0,False)]:params.append(dict(key=key,name=name,min=0,max=1,default=default,saved=saved))
 (OUT/'parameters.json').write_text(json.dumps(params,indent=2)+'\n')
 (OUT/'control-graph.json').write_text(json.dumps(skin.graph,indent=2)+'\n')
 v=ET.fromstring(files['version.xml']);v.find('version').text='2.3.0.3';files['version.xml']=ET.tostring(v,encoding='utf-8',xml_declaration=True)+b'\n'
 manifest={'candidate':'GHOST Buffer Engine / single supervised-trial candidate','uid':1195922260,'xml_uid':'47485354','identifier':'MPC-EURO.vst.ghost','version':'2.3.0.3','parameters':131,'factory_programs':16,'top_level_areas':5,'views':skin.views,'hardware_validation':'PENDING','device_access':False,'abi':abi,'files':{n:sha(v) for n,v in sorted(files.items())}}
 files['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode();files['SHA256SUMS']=''.join(f'{sha(v)}  {n}\n' for n,v in sorted(files.items())).encode()
 folder=OUT/'package'/product.FOLDER
 for n,v in files.items():p=folder/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(v)
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for n,v in sorted(files.items()):
   i=zipfile.ZipInfo(product.FOLDER+'/'+n,(2026,10,19,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,v)
 report=dict(zip=str(archive),zip_sha256=sha(archive.read_bytes()),binary_sha256=sha(files['ghost.so']),files=len(files),native=str(native),abi=abi,views=skin.views,presets=presets,hardware_validation='PENDING',device_access=False)
 (OUT/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ('views','presets')},indent=2))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--out',type=pathlib.Path,default=OUT);OUT=p.parse_args().out.resolve();main()
