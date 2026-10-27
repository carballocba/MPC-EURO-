#!/usr/bin/env python3
"""Native and ARMv7 build from isolated generated sources. No device operations."""
import argparse,json,os,subprocess,hashlib,pathlib
from generate import ROOT,OUT,generate

def build(arm=False,sanitize=None,destination=None):
 src=generate();folder=pathlib.Path(destination) if destination else OUT/('arm' if arm else 'native'+('-'+sanitize if sanitize else '')); folder.mkdir(parents=True,exist_ok=True)
 zig=ROOT/'build/venv/lib/python3.13/site-packages/ziglang/zig'
 flags=[str(zig),'cc','-target','arm-linux-gnueabihf.2.31','-mcpu=cortex_a9'] if arm else ['cc']
 flags+=['-std=c11','-O2','-ffp-contract=off','-fPIC','-DGHOST_STANDALONE_UID=0x47485354','-DGHOST_FINAL_PRODUCT=1','-DGHOST_BUFFER_ENGINE=1','-I'+str(src),'-I'+str(ROOT/'src'),'-I'+str(ROOT/'build'),'-I'+str(ROOT/'experiments/ghost-c1')]
 if arm:flags+=['-fvisibility=hidden']
 else:flags+=['-Wall','-Wextra','-Werror']
 if sanitize:flags+=['-O1','-g','-fno-omit-frame-pointer','-fsanitize='+sanitize]
 sources=[src/n for n in ['core.c','motion.c','params.c','state.c','vst.c','base.c','engine.c','performance.c']]+[ROOT/'experiments/ghost/ghost.c',ROOT/'src/repeat.c']
 env=dict(os.environ,ZIG_GLOBAL_CACHE_DIR=str(folder/'zig-global'),ZIG_LOCAL_CACHE_DIR=str(folder/'zig-local'));objects=[];commands=[]
 for n,s in enumerate(sources):
  obj=folder/f'unit-{n}.o';cmd=flags+['-c',str(s),'-o',str(obj)];subprocess.run(cmd,check=True,env=env);objects.append(str(obj));commands.append(cmd)
 output=folder/'ghost.so';cmd=flags+['-shared',*objects,'-lm','-pthread','-o',str(output)]
 if arm:cmd+=['-Wl,--no-undefined','-Wl,--strip-debug','-Wl,--version-script='+str(ROOT/'src/exports.map')]
 subprocess.run(cmd,check=True,env=env);commands.append(cmd)
 report={'file':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bytes':output.stat().st_size,'commands':commands,'device_access':False}
 if arm:
  from elftools.elf.elffile import ELFFile
  with output.open('rb') as f:
   e=ELFFile(f);assert e.elfclass==32 and e['e_machine']=='EM_ARM' and e['e_flags']&0x400
   exports=[s.name for s in e.get_section_by_name('.dynsym').iter_symbols() if s['st_shndx']!='SHN_UNDEF' and s['st_info']['bind']=='STB_GLOBAL'];assert exports==['VSTPluginMain']
   needed=sorted(t.needed for t in e.get_section_by_name('.dynamic').iter_tags() if t.entry.d_tag=='DT_NEEDED');assert not set(needed)-{'libc.so.6','libm.so.6','libpthread.so.0','ld-linux-armhf.so.3'}
   ver=e.get_section_by_name('.gnu.version_r');glibc=sorted({a.name for _,seq in ver.iter_versions() for a in seq if a.name.startswith('GLIBC_')});assert all(tuple(map(int,s[6:].split('.')))<=(2,31) for s in glibc)
  report.update(elf_bits=32,machine='ARM',hard_float=True,exports=exports,needed=needed,glibc=glibc,executed_on_arm=False)
 (folder/'build-report.json').write_text(json.dumps(report,indent=2)+'\n');return output
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--arm',action='store_true');a.add_argument('--sanitize');args=a.parse_args();print(build(args.arm,args.sanitize))
