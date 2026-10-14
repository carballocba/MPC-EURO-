#!/usr/bin/env python3
"""Reject unexpected DSP/ABI/UI or generated-artifact drift from the tested proof."""
import hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
b=json.loads((root/'docs/validation/proof-artifact-baseline.json').read_text())
paths=['src','ui','vendor','Makefile']
subprocess.run(['git','diff','--exit-code',b['implementation_commit'],'--',*paths],cwd=root,check=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(root/'build/arm/beatrepeat.so')==b['arm_sha256'],'ARM binary changed'
skin=root/'build/skin/MPC-EURO - VST - BeatRepeat'
actual={str(p.relative_to(skin)):sha(p) for p in sorted(skin.rglob('*')) if p.is_file()}
assert actual==b['skin'],'Exported native skin changed'
result={'implementation_commit':b['implementation_commit'],'source_controls_abi_unchanged':True,'arm_sha256':b['arm_sha256'],'skin_files_verified':len(actual)}
(root/'build/validation/proof-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS unchanged proof sources, exact ARM binary and all',len(actual),'native skin files')
