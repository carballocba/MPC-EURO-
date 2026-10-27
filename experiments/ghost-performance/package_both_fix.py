#!/usr/bin/env python3
"""Separate offline BOTH fix; copy installed GUI, Q-Links and presets byte-for-byte."""
import pathlib,json,hashlib,zipfile
from generate import ROOT,OUT
D=ROOT/'build/ghost-both-fix';PREFIX='MPC-EURO - VST - GHOST/'
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 previous=D/'reference/installed-armv7.zip';assert sha(previous.read_bytes())=='2798a095ac08c7ef5df4a911da4495320746650a6a2d4f1bf9deab8aaf59cc99'
 with zipfile.ZipFile(previous) as z:files={n:z.read(n) for n in z.namelist()}
 original=dict(files);files[PREFIX+'ghost.so']=(OUT/'arm/ghost.so').read_bytes();abi=json.loads((OUT/'arm/build-report.json').read_text());assert sha(files[PREFIX+'ghost.so'])==abi['sha256']
 manifest=json.loads(files[PREFIX+'manifest.json']);manifest.update(candidate='GHOST Random Repeat BOTH arbitration fix / OFFLINE TRIAL',baseline_zip_sha256=sha(previous.read_bytes()),abi={k:v for k,v in abi.items() if k not in ['commands','file']},both_fix='RR retains density; progressive phrase keys; duplicate BOTH delivery no-op; manual priority unchanged',hardware_validation='PENDING')
 for n in ['experiments/ghost-performance/random_repeat.h','experiments/ghost-performance/random_repeat_patch.py']:manifest['sources_sha256'][n]=sha((ROOT/n).read_bytes())
 manifest['files']={n[len(PREFIX):]:sha(b) for n,b in sorted(files.items()) if n not in [PREFIX+'manifest.json',PREFIX+'SHA256SUMS']};files[PREFIX+'manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode();files[PREFIX+'SHA256SUMS']=''.join(sha(b)+'  '+n[len(PREFIX):]+'\n' for n,b in sorted(files.items()) if n!=PREFIX+'SHA256SUMS').encode()
 changed=[n[len(PREFIX):] for n in files if files[n]!=original[n]];assert sorted(changed)==['SHA256SUMS','ghost.so','manifest.json']
 target=D/'ghost-random-repeat-both-fix-armv7-TRIAL.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for n,b in sorted(files.items()):i=zipfile.ZipInfo(n,(2026,10,22,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,b)
 report=dict(package_sha256=sha(target.read_bytes()),binary_sha256=sha(files[PREFIX+'ghost.so']),files=len(files),uid=manifest['uid'],parameters=manifest['parameters'],changed_files=changed,preserved_fxp=sum(n.endswith('.fxp') for n in files),gui_and_qlinks_byte_identical=True,reference_sha256=sha(previous.read_bytes()),device_access=False,arm_execution=False)
 (D/'delivery.json').write_text(json.dumps(report,indent=2)+'\n');(D/'SHA256SUMS.txt').write_text(report['package_sha256']+'  '+target.name+'\n'+report['binary_sha256']+'  ghost.so\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
