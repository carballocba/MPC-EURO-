"""Offline Cortex-A9 hard-float build. No installation, network or original outputs."""
import os,pathlib,subprocess,json,hashlib,shutil
from bindings import ROOT,OUT
zig=ROOT/'build/venv/lib/python3.13/site-packages/ziglang/zig'
if not zig.is_file():raise SystemExit('Offline Zig unavailable; no download attempted.')
subprocess.run(['python3',str(ROOT/'experiments/ghost-c1/prepare.py')],check=True)
arm=OUT/'arm';arm.mkdir(exist_ok=True)
env=dict(os.environ,ZIG_GLOBAL_CACHE_DIR=str(OUT/'zig-global-cache'),ZIG_LOCAL_CACHE_DIR=str(OUT/'zig-local-cache'))
flags=[str(zig),'cc','-target','arm-linux-gnueabihf.2.31','-mcpu=cortex_a9','-std=c11','-O2','-ffp-contract=off','-fPIC','-fvisibility=hidden','-I'+str(ROOT/'build'),'-I'+str(ROOT/'src')]
files=['core.c','motion.c','params.c','state.c','vst.c','base.c','../ghost/ghost.c','../../src/engine.c','../../src/repeat.c']
objects=[]
for i,file in enumerate(files):
 obj=arm/f'unit-{i}.o';subprocess.run([*flags,'-c',str(ROOT/'experiments/ghost-c1'/file),'-o',str(obj)],env=env,check=True);objects.append(str(obj))
binary=arm/'beatrepeat-ghost-c1.so'
subprocess.run([*flags,'-shared',*objects,'-lm','-pthread','-Wl,--no-undefined','-Wl,--version-script='+str(ROOT/'src/exports.map'),'-o',str(binary)],env=env,check=True)
from elftools.elf.elffile import ELFFile
with binary.open('rb') as f:
 elf=ELFFile(f);assert elf.elfclass==32 and elf['e_machine']=='EM_ARM';symbols=elf.get_section_by_name('.dynsym');exports=[s.name for s in symbols.iter_symbols() if s['st_shndx']!='SHN_UNDEF' and s['st_info']['bind']=='STB_GLOBAL'];assert exports==['VSTPluginMain'];assert elf['e_flags']&0x400
 libs=[t.needed for t in elf.get_section_by_name('.dynamic').iter_tags() if t.entry.d_tag=='DT_NEEDED'];assert set(libs)<= {'libc.so.6','libm.so.6','libpthread.so.0','ld-linux-armhf.so.3'}
 versions=elf.get_section_by_name('.gnu.version_r');glibc=sorted({aux.name for _,auxes in versions.iter_versions() for aux in auxes if aux.name.startswith('GLIBC_')}) if versions else []
 assert all(tuple(map(int,v[6:].split('.'))) <= (2,31) for v in glibc)
 report={'glibc_versions':glibc,'hard_float':True,'target':'arm-linux-gnueabihf.2.31 Cortex-A9','elf_bits':32,'machine':'ARM','e_flags':elf['e_flags'],'exports':exports,'needed':libs,'sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'bytes':binary.stat().st_size,'executed_on_arm':False,'hardware_validated':False}
(arm/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

# Package candidate in an isolated folder; never install/register it.
import zipfile
package=OUT/'package/MPC-EURO - VST - BeatRepeat'
shutil.copytree(OUT/'native-skin/MPC-EURO - VST - BeatRepeat',package,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.art'))
shutil.copy2(binary,package/'beatrepeat.so')
(package/'version.xml').write_text("<?xml version='1.0' encoding='utf-8'?>\n<plugincontent version='1.0'><identifier>MPC-EURO.vst.beatrepeat</identifier><version>2.1.1.0</version></plugincontent>\n")
manifest={'candidate':'GHOST C1.1 experimental, offline only','uid':'45754272','binary_sha256':report['sha256'],'files':{str(p.relative_to(package)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(package.rglob('*')) if p.is_file() and '.art' not in p.parts}}
(OUT/'package-manifest.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(OUT/'beatrepeat-ghost-c11-armv7-OFFLINE.zip','w',zipfile.ZIP_DEFLATED) as archive:
 for relative in manifest['files']:
  info=zipfile.ZipInfo('MPC-EURO - VST - BeatRepeat/'+relative,(2026,10,15,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;archive.writestr(info,(package/relative).read_bytes())
