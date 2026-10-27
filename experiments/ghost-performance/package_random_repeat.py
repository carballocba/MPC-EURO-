#!/usr/bin/env python3
"""Offline same-GHOST candidate; preserve every existing preset and Q-Link assignment."""
import json,zipfile,pathlib,hashlib
from generate import ROOT,OUT
from package import make
D=ROOT/'build/ghost-random-repeat';D.mkdir(parents=True,exist_ok=True);PREFIX='MPC-EURO - VST - GHOST/'
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 core=D/'core-intermediate.zip';make(core)
 with zipfile.ZipFile(core) as z:files={n:z.read(n) for n in z.namelist()}
 previous=D/'reference/previous-armv7.zip';assert sha(previous.read_bytes())=='cf9f790c8720daac40dd4bc15d08cd4b0dca5d14c91a044d8ead82158f658266'
 with zipfile.ZipFile(previous) as z:
  for n in z.namelist():
   if n.endswith('.fxp') or n.startswith(PREFIX+'Preset Library/'):files[n]=z.read(n)
  for n in ['Q-Links.json','Q-Links - 8by1.json']:assert files[PREFIX+'Plugin Skins/'+n]==z.read(PREFIX+'Plugin Skins/'+n),'Existing Q-Link assignments changed'
 manifest=json.loads(files[PREFIX+'manifest.json']);manifest.update(candidate='GHOST Random Repeat + Performance Both / OFFLINE TRIAL',parameters=156,original_indices_unchanged=[0,147],state_format='Optional RRF1 v1 wrapping unchanged PEF1 v1/v2; legacy decoders retained',appended_controls={'148':'MODE','149':'INTENSITY','150':'PROBABILITY','151':'VARIATION','152':'RATE','153':'MAX HOLD'},appended_readonly={'154':'ACTUAL REPEAT','155':'ACTUAL FRAGMENT'},preset_library='32 external FXP preserved byte-for-byte; native import pending')
 manifest['files']={n[len(PREFIX):]:sha(b) for n,b in sorted(files.items()) if n not in [PREFIX+'manifest.json',PREFIX+'SHA256SUMS']};files[PREFIX+'manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode();files[PREFIX+'SHA256SUMS']=''.join(sha(b)+'  '+n[len(PREFIX):]+'\n' for n,b in sorted(files.items()) if n!=PREFIX+'SHA256SUMS').encode()
 target=D/'ghost-random-repeat-both-armv7-TRIAL.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for n,b in sorted(files.items()):info=zipfile.ZipInfo(n,(2026,10,21,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,b)
 report=dict(package_sha256=sha(target.read_bytes()),binary_sha256=sha(files[PREFIX+'ghost.so']),files=len(files),parameters=156,uid=1195922260,original_presets=16,external_presets=32,preset_files_total=sum(n.endswith('.fxp') for n in files),device_access=False,arm_execution=False,transaction_sha256=sha((ROOT/'tools/ghost-product-transaction.sh').read_bytes()),runner_sha256=sha((ROOT/'tools/ghost_random_repeat_trial.py').read_bytes()),shared_runner_sha256=sha((ROOT/'tools/ghost_product.py').read_bytes()),memory_helper_sha256=sha((ROOT/'tools/ghost_buffer_trial.py').read_bytes()),fallback_sha256=sha(previous.read_bytes()),fallback_files=357,fallback_binary_sha256='9b7f5584e34694a60c788360f55e2fe7a9a022152934491c31a742c80510c222')
 (D/'delivery.json').write_text(json.dumps(report,indent=2)+'\n');(D/'SHA256SUMS.txt').write_text(report['package_sha256']+'  '+target.name+'\n'+report['binary_sha256']+'  ghost.so\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
