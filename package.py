#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,tempfile,shutil,zipfile,json
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--out',default='dist');a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
# Do not emit another hardware candidate before the full legacy fixture passes.
migration=(R/'evidence/rc3/migration-tests.log').read_text()
assert 'Ran 18 tests' in migration and '\nOK\n' in migration and '\nFAILED' not in migration,'legacy migration qualification required'
binary=(R/'rebuild/ghost.so').read_bytes();assert hashlib.sha256(binary).hexdigest()=='588019130b31ced7077f7e4afe35bd23b0753df7a2959e2af39fa825e1b81afd'
with tempfile.TemporaryDirectory() as tmp:
 stage=Path(tmp)/'GHOST-2.4.2';shutil.copytree(R/'package-template',stage)
 (stage/'portable/MPC-EURO - VST - GHOST/ghost.so').write_bytes(binary)
 m=json.loads((stage/'mpc-plugin.json').read_text());m['installer_revision']='2.4.2-installer2-rc3';(stage/'mpc-plugin.json').write_text(json.dumps(m,indent=2)+'\n')
 # Leave every runtime payload resource and metadata byte unchanged.
 (stage/'SHA256SUMS').unlink(missing_ok=True)
 (stage/'SHA256SUMS').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.relative_to(stage).as_posix()+'\n' for f in sorted(stage.rglob('*')) if f.is_file()))
 z=out/'GHOST-2.4.2-installer2-rc3-mpc-armv7.zip'
 with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as f:
  for p in sorted(stage.rglob('*')):
   if p.is_file():
    i=zipfile.ZipInfo('GHOST-2.4.2/'+p.relative_to(stage).as_posix(),(2026,10,29,0,0,0));i.create_system=3;i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;f.writestr(i,p.read_bytes())
 print(hashlib.sha256(z.read_bytes()).hexdigest(),z)
