#!/usr/bin/env python3
"""Fail hard on an incompatible ELF/ABI/dependency/export result."""
import subprocess,re,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];path=root/'build/arm/beatrepeat.so'
def run(*a):return subprocess.check_output(a,text=True)
head=run('readelf','-h',str(path));attrs=run('readelf','-A',str(path))
dyn=run('readelf','-d',str(path));symbols=run('nm','-D','--defined-only',str(path));versions=run('readelf','-V',str(path))
assert 'ELF32' in head and 'ARM' in head and 'little endian' in head and 'DYN' in head
assert 'hard-float ABI' in head and 'Tag_CPU_arch: v7' in attrs
# Zig's linked compiler-runtime omits the merged VFP-args tag. Verify the actual
# plugin objects' calling convention as well as the final ELF hard-float flag.
objects='\n'.join(run('readelf','-A',str(root/f'build/arm/{unit}.o')) for unit in ['plugin','repeat'])
assert objects.count('Tag_ABI_VFP_args: VFP registers')==2
assert objects.count('Tag_CPU_arch: v7')==2
exports=[x.split()[-1] for x in symbols.strip().splitlines()]
assert exports==['VSTPluginMain'],exports
needed=re.findall(r'Shared library: \[(.*?)\]',dyn)
assert set(needed)<= {'libc.so.6','libm.so.6','libpthread.so.0','ld-linux-armhf.so.3'},needed
glibc=re.findall(r'GLIBC_(\d+)\.(\d+)',versions)
highest=max((tuple(map(int,x)) for x in glibc),default=(0,0));assert highest<=(2,31),highest
assert not any(x in dyn for x in ['libatomic','libstdc++','JUCE'])
result={'architecture':'ELF32 little-endian ARMv7 hard-float','exports':exports,'dependencies':needed,
    'highest_glibc':'.'.join(map(str,highest)),'target_glibc_ceiling':'2.31',
    'cpu':'ARMv7-A / Cortex-A9 code generation, VFPv3 + NEON',
    'object_vfp_register_calling_convention':True,'linked_vfp_args_tag_present':'Tag_ABI_VFP_args' in attrs,
    'physical_mpc_tested':False,'qemu_runtime_tested':False}
(root/'build/arm/validation.json').write_text(json.dumps(result,indent=2)+'\n')
(root/'build/arm/readelf.txt').write_text(head+'\n'+attrs+'\n'+objects+'\n'+dyn+'\n'+versions)
print('PASS ARM ELF/ABI/export/dependency validation:',json.dumps(result))
