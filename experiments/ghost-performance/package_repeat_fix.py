#!/usr/bin/env python3
"""One offline update candidate plus existing FXP library. Uses existing transaction."""
import pathlib,json,zipfile,hashlib,sys,subprocess
from generate import ROOT,OUT
from package import make,source_archive
D=ROOT/'build/ghost-live-repeat-fix';D.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 core=D/'ghost-live-repeat-core-armv7.zip';make(core)
 with zipfile.ZipFile(core) as z:files={n:z.read(n) for n in z.namelist()}
 prefix='MPC-EURO - VST - GHOST/'
 with zipfile.ZipFile(ROOT/'build/ghost-live-repeat-reference/previous-library-armv7.zip') as z:
  for n in z.namelist():
   if n.startswith(prefix+'Preset Library/'):files[n]=z.read(n)
 manifest=json.loads(files[prefix+'manifest.json']);manifest['candidate']='GHOST LIVE REPEAT + A/B Q-Link fix / offline trial';manifest['preset_library']='32 unchanged external FXP; host import remains pending';manifest['files']={n[len(prefix):]:sha(b) for n,b in sorted(files.items()) if n not in [prefix+'manifest.json',prefix+'SHA256SUMS']};files[prefix+'manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode();files[prefix+'SHA256SUMS']=''.join(sha(b)+'  '+n[len(prefix):]+'\n' for n,b in sorted(files.items()) if n!=prefix+'SHA256SUMS').encode()
 target=D/'ghost-live-repeat-qlink-armv7-TRIAL.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for n,b in sorted(files.items()):info=zipfile.ZipInfo(n,(2026,10,21,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,b)
 # Verify identity and all checksums on final payload.
 for n,h in manifest['files'].items():assert sha(files[prefix+n])==h
 assert manifest['uid']==1195922260 and manifest['parameters']==148
 with zipfile.ZipFile(ROOT/'build/ghost-live-repeat-reference/previous-armv7.zip') as z:
  for n in z.namelist():
   if n.endswith('.fxp') or n.endswith('Q-Links.json') and '/Program/' in n:assert files[n]==z.read(n)
 old=ROOT/'build/ghost-live-repeat-reference/previous-armv7.zip'
 d=dict(candidate='GHOST Live Repeat/Q-Link fix',package_sha256=sha(target.read_bytes()),binary_sha256=sha(files[prefix+'ghost.so']),transaction_sha256=sha((ROOT/'tools/ghost-product-transaction.sh').read_bytes()),runner_sha256=sha((ROOT/'tools/ghost_live_repeat_trial.py').read_bytes()),shared_runner_sha256=sha((ROOT/'tools/ghost_product.py').read_bytes()),memory_helper_sha256=sha((ROOT/'tools/ghost_buffer_trial.py').read_bytes()),fallback_sha256=sha(old.read_bytes()),settings_reference_sha256='7298d10da787c9e37b8bf98254883cd635e936d10c11f65190fd13c9b74ec21c',fallback_files=324,fallback_binary_sha256='f5980a734a4e7bb54823a1b5480a310a4d8ec826040803164d9cbd3ea8ec49b4',files=len(files),new_fxp=32,device_access=False)
 (D/'delivery.json').write_text(json.dumps(d,indent=2)+'\n');(D/'SHA256SUMS.txt').write_text(d['package_sha256']+'  '+target.name+'\n'+d['binary_sha256']+'  ghost.so\n');print(json.dumps(d,indent=2))
if __name__=='__main__':main()
