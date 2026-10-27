#!/usr/bin/env python3
from pathlib import Path
import zipfile,hashlib,argparse,shutil,tempfile
R=Path(__file__).resolve().parent
a=argparse.ArgumentParser();a.add_argument('--out',default='dist');x=a.parse_args();out=Path(x.out);out.mkdir(parents=True,exist_ok=True)
binary=(R/'rebuild/ghost.so').read_bytes();assert hashlib.sha256(binary).hexdigest()=='588019130b31ced7077f7e4afe35bd23b0753df7a2959e2af39fa825e1b81afd'
with tempfile.TemporaryDirectory() as t:
 stage=Path(t)/'GHOST-2.4.2';shutil.copytree(R/'package-template',stage)
 (stage/'portable/MPC-EURO - VST - GHOST/ghost.so').write_bytes(binary)
 manifest=lambda r: ''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(r).as_posix()+'\n' for p in sorted(r.rglob('*')) if p.is_file())
 (stage/'SHA256SUMS').write_text(manifest(stage))
 z=out/'GHOST-2.4.2-mpc-armv7.zip'
 with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as f:
  for p in sorted(stage.rglob('*')):
   if p.is_file():
    i=zipfile.ZipInfo('GHOST-2.4.2/'+p.relative_to(stage).as_posix(),(2026,10,27,0,0,0));i.create_system=3;i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;f.writestr(i,p.read_bytes())
 print(hashlib.sha256(z.read_bytes()).hexdigest(),z)
