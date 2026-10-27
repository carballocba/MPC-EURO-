#!/usr/bin/env python3
"""Rebuild the candidate in a separate source tree with the same pinned runtime. Offline."""
import hashlib,json,pathlib,subprocess,tarfile,tempfile,os
R=pathlib.Path(__file__).resolve().parents[2];B=R/'build/ghost-performance-edition';python=R/'build/venv/bin/python'
work=pathlib.Path(tempfile.mkdtemp(prefix='ghost-pe-source-rebuild-',dir='/private/tmp'));root=work/'checkout';root.mkdir()
with tarfile.open(B/'ghost-performance-edition-source.tar.gz') as tar:
 assert all(not pathlib.PurePosixPath(m.name).is_absolute() and '..' not in pathlib.PurePosixPath(m.name).parts and m.isfile() for m in tar.getmembers())
 tar.extractall(root,filter='data')
(root/'build/venv').symlink_to(R/'build/venv',target_is_directory=True)
commands=[]
for script,args in [('build_engine.py',[]),('build_engine.py',['--arm']),('package.py',['--out',str(work/'reproduced.zip')])]:
 command=[str(python),str(root/'experiments/ghost-performance'/script),*args];commands.append(command)
 with (work/(script+('-arm' if args==['--arm'] else '')+'.log')).open('w') as log:subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,check=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
actual=B/'ghost-performance-edition-armv7-TRIAL.zip';original=sha(actual);reproduced=sha(work/'reproduced.zip');arm_original=sha(B/'arm/ghost.so');arm_copy=sha(root/'build/ghost-performance-edition/arm/ghost.so')
report=dict(status='PASS' if original==reproduced and arm_original==arm_copy else 'FAIL',source_archive_sha256=sha(B/'ghost-performance-edition-source.tar.gz'),original_zip_sha256=original,reproduced_zip_sha256=reproduced,original_arm_sha256=arm_original,reproduced_arm_sha256=arm_copy,relocated_source_tree=str(root),runtime='same pinned clang/Python3.13/Pillow12.3/pyelftools0.32/Zig0.13 through local venv symlink',commands=commands,device_access=False)
(B/'reproducibility.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['status']=='PASS'
