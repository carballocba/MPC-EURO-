#!/usr/bin/env python3
"""Deterministic supervised-trial artifact, native states and source snapshot. No network."""
import argparse,ctypes as C,gzip,hashlib,io,json,pathlib,struct,sys,tarfile,xml.etree.ElementTree as ET,zipfile
from build_gui import ROOT,OUT,P,build_gui
sys.path[:0]=[str(ROOT/'experiments/ghost-c1'),str(ROOT/'tests')]
from test_vst import FX

def sha(data):return hashlib.sha256(data).hexdigest()
def make(destination=None):
 files,views=build_gui();arm=OUT/'arm/ghost.so';abi=json.loads((OUT/'arm/build-report.json').read_text());assert sha(arm.read_bytes())==abi['sha256']
 base=ROOT/'build/ghost-buffer-engine-final/ghost-buffer-engine-armv7-TRIAL.zip';assert sha(base.read_bytes())=='9ac94c90f7b540770d40a9f7f59a8c027b27de8a150036a3aee5df44ed186928'
 files.pop('manifest.json',None);files.pop('SHA256SUMS',None);files['ghost.so']=arm.read_bytes()
 for name,path in [('GPL-3.0.txt','LICENSE'),('MPC-native-framework-MIT.txt','vendor/mpc/LICENSE'),('DejaVu-font.txt','vendor/fonts/LICENSE')]:files['Licenses/'+name]=(ROOT/path).read_bytes()
 v=ET.fromstring(files['version.xml']);assert v.findtext('identifier')=='MPC-EURO.vst.ghost';v.find('version').text='2.4.2.0';files['version.xml']=ET.tostring(v,encoding='utf-8',xml_declaration=True)+b'\n'
 presets=[]
 for name,tempo,g,c,size,mix,weights,rest,motion in [
  ('Rhodes Ghost 60',60,.18,.45,125,.65,(.5,.45,.05),.65,0),
  ('Pocket Stutter',120,.4,.2,31.25,.7,(.85,.1,.05),.35,.1),
  ('Reverse Dust',120,.25,.65,125,.6,(.15,.8,.05),.6,.15),
  ('Live Break',120,.8,.7,15.625,.9,(.65,.2,.15),.2,.2)]:
  f=FX(OUT/'native/ghost.so')
  try:
   f.d(f.fx,2,0,0,None,0)
   settings=[(48,0),(131,1),(132,g),(133,c),(134,__import__('math').log(size/8)/__import__('math').log(50)),(53,mix),(135,weights[0]),(136,weights[1]),(137,weights[2]),(138,rest),(139,motion),(33,(tempo-40)/200),(77,.8),(79,(250-.1)/(60000-.1)),(75,1/65535)]
   for p,x in settings:f.set(f.fx,p,x)
   f.block();data=f.chunk();assert data.startswith(b'PEF1')
   raw=struct.pack('>4sI4sIIII28sI',b'CcnK',52+len(data),b'FPCh',1,0x47485354,2000,1,name.encode()[:27].ljust(28,b'\0'),len(data))+data
   file='Performance Presets/'+name.replace(' ','-')+'.fxp';files[file]=raw;presets.append(dict(name=name,file=file,sha256=sha(raw),tempo=tempo,parameters=settings))
  finally:f.close()
 files['Performance Presets/index.json']=(json.dumps(presets,indent=2)+'\n').encode()
 files['PERFORMANCE-TRIAL.txt']=b'GHOST Performance Edition / OFFLINE TRIAL ONLY\nUID 47485354 / MPC-EURO.vst.ghost\nOriginal indices 0..130 and sixteen factory programs preserved.\nOld states load COMPAT. Performance mode is explicit; new construction starts RUN.\nScreen Mode: PLAY 16 declarations / native BUFFER-EVENTS-MOTION-RANDOM-TIMING-GLOBAL-MIDI-SCENES / host PRESET selector. Program Mode unchanged.\n12 vs 16 physical reachability and host focus remain pending on MPC One Hakai 3.9.1.\nDo not deploy without explicit authorization and verified transactional backup/rollback.\nNo source/preset/audio renders constitute hardware validation.\n'
 metadata=ET.fromstring(files['plugin-meta.xml']);plugin=metadata if metadata.tag=='PLUGIN' else metadata.find('.//PLUGIN');assert plugin is not None and plugin.attrib['uid'].lower()=='47485354'
 sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for folder in [ROOT/'experiments/ghost-performance'] for p in sorted(folder.glob('*')) if p.is_file()}
 manifest={'candidate':'GHOST Final Performance Integration / glitch-only trial RC','uid':1195922260,'xml_uid':'47485354','identifier':'MPC-EURO.vst.ghost','content_version':'2.4.2.0','state_format':'PEF1 v2 / v1 and historical decoders retained','parameters':148,'original_indices_unchanged':[0,130],'factory_programs':16,'views':views,'hardware_validation':'PENDING','arm_execution':'NOT RUN / QEMU unavailable','device_access':False,'abi':{k:v for k,v in abi.items() if k not in ['commands','file']},'baseline_zip_sha256':sha(base.read_bytes()),'sources_sha256':sources,'files':{n:sha(v) for n,v in sorted(files.items())}}
 files['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode();files['SHA256SUMS']=''.join(f'{sha(v)}  {n}\n' for n,v in sorted(files.items())).encode()
 archive=pathlib.Path(destination) if destination else OUT/'ghost-performance-edition-armv7-TRIAL.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,data in sorted(files.items()):
   info=zipfile.ZipInfo(P.FOLDER+'/'+name,(2026,10,20,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data)
 folder=OUT/'package'/P.FOLDER
 for name,data in files.items():p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 report=dict(zip=str(archive),zip_sha256=sha(archive.read_bytes()),binary_sha256=sha(files['ghost.so']),files=len(files),parameters=148,views=len(views),native=str(OUT/'native/ghost.so'),baseline_zip_sha256=sha(base.read_bytes()),candidate='GHOST Performance Edition',hardware_validation='PENDING',device_access=False)
 if destination is None:(OUT/'release-candidate.json').write_text(json.dumps(report,indent=2)+'\n')
 return report

def source_archive():
 paths=set()
 for folder in ['src','ui','vendor/core','vendor/fonts','vendor/mpc/tools','experiments/ghost-performance','experiments/ghost-c1','experiments/ghost','experiments/ghost-buffer','experiments/ghost-product','experiments/ghost-c12-2']:
  for p in (ROOT/folder).rglob('*'):
   if p.is_file() and (p.suffix in ['.py','.c','.h','.inc','.json','.map','.md','.ttf'] or p.name in ['LICENSE','COPYING']) and not any(x in p.parts for x in ['__pycache__','zig-cache','build']):paths.add(p)
 for name in ['LICENSE','vendor/mpc/LICENSE','vendor/fonts/LICENSE','Makefile','tools/gen_params.py','tools/ghost_performance_trial.py','tools/ghost-performance-trial.command','tools/ghost_product.py','tools/ghost_buffer_trial.py','tools/ghost-product-transaction.sh','build/params.h','build/factory.h','build/ghost-c11-demo/base-render.inc','build/ghost-c11-demo/engine-render.inc','build/ghost-functional-final/engine/ghost-identity-test.so','build/ghost-buffer-engine-final/ghost-buffer-engine-armv7-TRIAL.zip','build/ghost-integration-recovery/candidate/ghost-integration-recovery-armv7-OFFLINE.zip','build/ghost-final-reference/package.zip','build/ghost-final-reference/source.tar.gz','build/ghost-final-reference/native.so','build/ghost-final-installed-reference/installed-performance.zip','tests/test_shared.py','tests/test_ghost_functional_audit.py','tests/test_ghost_control_recovery.py','tests/test_ghost_performance_buffer.py','tests/test_ghost_buffer_engine.py','tests/test_ghost_final_integration.py','tests/test_ghost_performance.py','tests/test_ghost_performance_gui.py']:
  paths.add(ROOT/name)
 tarbytes=io.BytesIO()
 with tarfile.open(fileobj=tarbytes,mode='w') as tar:
  for p in sorted(paths):
   info=tarfile.TarInfo(str(p.relative_to(ROOT)));data=p.read_bytes();info.size=len(data);info.mtime=0;info.mode=0o644;tar.addfile(info,io.BytesIO(data))
 path=OUT/'ghost-performance-edition-source.tar.gz'
 with path.open('wb') as f:
  with gzip.GzipFile(filename='',fileobj=f,mode='wb',mtime=0) as g:g.write(tarbytes.getvalue())
 return dict(file=str(path),sha256=sha(path.read_bytes()),files=len(paths))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--out');args=parser.parse_args();report=make(args.out)
 if not args.out:report['source']=source_archive();(OUT/'release-candidate.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
