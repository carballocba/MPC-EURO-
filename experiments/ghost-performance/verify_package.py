#!/usr/bin/env python3
"""Fail closed on mismatched payload, metadata, native mappings or baseline presets. No SSH."""
import argparse,hashlib,json,pathlib,sys,xml.etree.ElementTree as ET,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'build/ghost-performance-edition';FOLDER='MPC-EURO - VST - GHOST/'
def sha(b):return hashlib.sha256(b).hexdigest()
def verify(path):
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  names=z.namelist();assert len(names)==len(set(names)) and all(n.startswith(FOLDER) and '..' not in pathlib.PurePosixPath(n).parts for n in names)
  files={n[len(FOLDER):]:z.read(n) for n in names}
 manifest=json.loads(files['manifest.json']);assert manifest['uid']==1195922260 and manifest['identifier']=='MPC-EURO.vst.ghost' and manifest['parameters']==148
 assert set(files)==set(manifest['files'])|{'manifest.json','SHA256SUMS'}
 assert all(sha(files[n])==h for n,h in manifest['files'].items())
 sums={n:h for h,n in (line.split('  ',1) for line in files['SHA256SUMS'].decode().splitlines())};assert set(sums)==set(files)-{'SHA256SUMS'};assert all(sha(files[n])==h for n,h in sums.items())
 meta=ET.fromstring(files['plugin-meta.xml']);plugin=meta if meta.tag=='PLUGIN' else meta.find('.//PLUGIN');assert int(plugin.attrib['uid'],16)==1195922260 and plugin.attrib['isInstrument']=='0' and plugin.attrib['category']=='Effect'
 assert ET.fromstring(files['version.xml']).findtext('identifier')=='MPC-EURO.vst.ghost'
 sys.path[:0]=[str(ROOT/'experiments/ghost-c12-2'),str(ROOT/'experiments/ghost-c1')];import build_integration_recovery as ref
 tui=json.loads(files['Plugin Skins/TUI.json']);assert [t['tabName'] for t in tui['pageData']['tabs']]==['PLAY','BUFFER','EVENTS','MOTION','RANDOM','TIMING','GLOBAL','MIDI','SCENES'];assert ref.referenced_images(tui)<=set(files)
 with zipfile.ZipFile(ROOT/'build/ghost-buffer-engine-final/ghost-buffer-engine-armv7-TRIAL.zip') as z:baseline={n[len(FOLDER):]:z.read(n) for n in z.namelist()}
 for n,data in baseline.items():
  if n.startswith('Presets/'):assert files[n]==data,'Original preset changed: '+n
 for n in ['Q-Links.json','Q-Links - 8by1.json']:
  q=json.loads(files['Plugin Skins/'+n]);b=json.loads(baseline['Plugin Skins/'+n]);assert q['Program Mode Q-Links']==b['Program Mode Q-Links'];assert [sum(v>=0 for v in row['Q-Links'].values()) for row in q['Screen Mode Q-Links']['map']]==[16,15,12,12,9,8,12,10,9]
 abi=json.loads((OUT/'arm/build-report.json').read_text());assert sha(files['ghost.so'])==abi['sha256'];assert abi['elf_bits']==32 and abi['hard_float'] and abi['exports']==['VSTPluginMain']
 report=dict(status='PASS OFFLINE PAYLOAD',zip_sha256=sha(path.read_bytes()),binary_sha256=sha(files['ghost.so']),files=len(files),preserved_factory_presets=True,uid=1195922260,device_access=False,arm_execution=False)
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('zip',nargs='?',type=pathlib.Path,default=OUT/'ghost-performance-edition-armv7-TRIAL.zip');args=p.parse_args();r=verify(args.zip);(OUT/'package-verification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
