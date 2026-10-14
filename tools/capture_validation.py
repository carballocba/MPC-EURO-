#!/usr/bin/env python3
"""Run required checks and retain exact results; stop immediately on failure."""
import os,subprocess,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'build/validation';out.mkdir(parents=True,exist_ok=True)
for name,target in [('native','test'),('sanitizers','sanitize'),('skin','skin'),('arm','arm')]:
    p=subprocess.run(['make',target],cwd=root,env=os.environ,capture_output=True,text=True)
    (out/f'{name}.txt').write_text(p.stdout+p.stderr)
    print(p.stdout+p.stderr,end='')
    if p.returncode:raise SystemExit(p.returncode)
inputs=[p for folder in ['src','tests','ui','tools','vendor'] for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']+[root/'Makefile']
summary={'all_checks_passed':True,'inputs':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(inputs)},'binaries':{str(p):hashlib.sha256((root/p).read_bytes()).hexdigest() for p in [Path('build/beatrepeat-native.so'),Path('build/arm/beatrepeat.so')]}}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print('PASS all required checks; logs and input fingerprints in build/validation/')
