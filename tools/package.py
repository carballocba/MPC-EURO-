#!/usr/bin/env python3
"""Create a local review package + matching source; never install/register."""
import hashlib,json,shutil,subprocess,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(__file__).resolve().parents[1]
name='MPC-EURO - VST - BeatRepeat'
checks=json.loads((root/'build/validation/summary.json').read_text())
assert checks['all_checks_passed']
for p,h in {**checks['inputs'],**checks['binaries']}.items():
    assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h,f'Changed since validation: {p}; rerun capture_validation.py'
source_dirs=['src','tests','tools','ui','vendor','docs','research','.github']
files=[root/x for x in ['README.md','LICENSE','Makefile','.gitignore']]
for folder in source_dirs:
    files.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
files=sorted(files,key=lambda p:str(p.relative_to(root)))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source_hash=hashlib.sha256()
for p in files:source_hash.update(str(p.relative_to(root)).encode()+b'\0'+p.read_bytes()+b'\0')
def zip_files(path,pairs):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p,arc in sorted(pairs,key=lambda x:x[1]):
            info=zipfile.ZipInfo(arc,(1980,1,1,0,0,0));info.create_system=3
            info.external_attr=(0o100755 if p.name=='build_arm.sh' else 0o100644)<<16
            z.writestr(info,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
out=root/'build/package'
if out.exists():shutil.rmtree(out)
out.mkdir(parents=True)
source=out/'MPC-EURO-beatrepeat-source.zip'
zip_files(source,[(p,'MPC-EURO-beatrepeat/'+str(p.relative_to(root))) for p in files])
folder=out/name
shutil.copytree(root/'build/skin'/name,folder)
shutil.copy2(root/'build/arm/beatrepeat.so',folder/'beatrepeat.so')
# Community-native folder metadata is portable; this does not register it.
entry=ET.fromstring((root/'build/pluginlist-entry.xml').read_text())
entry.set('file',f'%payload-path%/{name}/beatrepeat.so')
(folder/'plugin-meta.xml').write_text(ET.tostring(entry,encoding='unicode')+'\n')
shutil.copy2(root/'LICENSE',folder/'LICENSE')
shutil.copy2(root/'docs/PROVENANCE.md',folder/'NOTICE.md')
lic=folder/'LICENSES';lic.mkdir()
for src,label in [('vendor/mpc/LICENSE','community-MIT.txt'),('vendor/mpc/tools/vendor/force-shadow/LICENSE','force-shadow-MIT.txt'),('vendor/fonts/LICENSE','DejaVu.txt'),('vendor/zig/LICENSE','Zig-MIT.txt')]:
    shutil.copy2(root/src,lic/label)
# stb's complete license remains in matching source (offline renderer only).
validation=json.loads((root/'build/arm/validation.json').read_text())
assert validation['exports']==['VSTPluginMain'] and not validation['physical_mpc_tested']
manifest={'project':'MPC-EURO','plugin':'BeatRepeat','version':'0.1.0-experimental','format':'VST2 SDK-free',
    'uid':'45754272','identity':'EuBr','inputs':2,'outputs':2,'wet':'mono centered','dry':'stereo float',
    'sample_rates':[16000,96000],'target_sample_rate':44100,'target_block_frames':128,
    'params':json.loads((root/'ui/params.json').read_text()),
    'implementation_commit':'60f2b25502a25d619c99c04d07ac503cc452828f',
    'installation':'manual native plugin folder; registration requires separate approval',
    'installation_reference_pin':'e18a0a1da84515096d354f399dd4cd7f9c079fb5',
    'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
    'working_tree_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True)),
    'source_tree_sha256':source_hash.hexdigest(),'source_archive':source.name,'source_archive_sha256':sha(source),
    'dsp_pin':'66ee010f822c915adb893c8c03279e30a52bd839','community_pin':'ce6278d53091ba40127838020fc8a7887894551f',
    'license':'GPL-3.0-only with retained third-party notices','arm_validation':validation,
    'hakai_3_9_1_verified':False,'installer_included':False,'gui':'native TUI + Q-Links; host redraw unverified'}
(folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
shutil.copy2(root/'build/pluginlist-entry.xml',out/'pluginlist-entry.xml')
shutil.copytree(root/'docs',out/'documentation')
shutil.copy2(root/'docs/INSTALL.md',out/'INSTALL.md')
shutil.copy2(root/'docs/ROLLBACK.md',out/'ROLLBACK.md')
(folder/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(folder)}\n' for p in sorted(folder.rglob('*')) if p.is_file()))
(out/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(out)}\n' for p in sorted(out.rglob('*')) if p.is_file()))
archive=out/'MPC-EURO-BeatRepeat-armv7-proof.zip'
zip_files(archive,[(p,str(p.relative_to(out))) for p in out.rglob('*') if p.is_file() and p!=archive])
(out/(archive.name+'.sha256')).write_text(f'{sha(archive)}  {archive.name}\n')
print('Manual trial package:',archive)
print('SHA256:',sha(archive),'| matching source:',sha(source))
