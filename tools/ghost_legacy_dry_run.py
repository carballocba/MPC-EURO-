#!/usr/bin/env python3
"""No installer invocation/uploads: exact adoption classifier via SSH stdin + live hashes."""
import argparse,pathlib,subprocess,hashlib,json,shlex,tarfile,io,zipfile,xml.etree.ElementTree as E
R=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path);p.add_argument('--host',required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--reference-package',default='/storage/GHOST-Work/incoming-rc2-validation-20261028');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);a.out.chmod(0o700)
Q=shlex.quote;target='/storage/Synths/MPC-EURO - VST - GHOST';settings='/data/Settings/MPC/MPC.settings';records=[];report={'device_modified':False,'installer_invoked':False,'go':False}
def call(n,cmd,data=None):
 r=subprocess.run(['ssh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','-o','ServerAliveInterval=3','-o','ServerAliveCountMax=3',a.host,cmd],input=data,capture_output=True,timeout=90)
 for suffix,blob in [('stdout',r.stdout),('stderr',r.stderr)]:
  f=a.out/(n+'.'+suffix);f.write_bytes(blob);f.chmod(0o600)
 records.append({'operation':n,'exit':r.returncode,'command':cmd});(a.out/'COMMAND_RESULTS.json').write_text(json.dumps(records,indent=2)+'\n')
 if r.returncode:raise RuntimeError(n+' exit '+str(r.returncode))
 return r.stdout
try:
 if a.candidate:
  blob=a.candidate.read_bytes();report['candidate_sha256']=hashlib.sha256(blob).hexdigest()
  with zipfile.ZipFile(io.BytesIO(blob)) as z:
   assert z.testzip() is None
   for line in z.read('GHOST-2.4.2/SHA256SUMS').decode().splitlines():
    digest,name=line.split('  ',1);assert hashlib.sha256(z.read('GHOST-2.4.2/'+name)).hexdigest()==digest
   for name in ['adoption.sh','common.sh','xml_contract.awk','payload.sha256','legacy-owned.sha256','portable/MPC-EURO - VST - GHOST/plugin-meta.xml']:
    assert z.read('GHOST-2.4.2/'+name)==(R/'package-template'/name).read_bytes(),'candidate/source drift: '+name
 raw=call('settings.before','cat '+Q(settings));assert raw,'empty SSH output is transport/read failure, not invalid XML';xml=E.fromstring(raw)
 hostcmd='systemctl show acvs -p ActiveState -p SubState -p MainPID -p NRestarts;cat /proc/sys/kernel/random/boot_id'
 host=call('host.before',hostcmd);assert b'ActiveState=active' in host and b'SubState=running' in host
 inventory_cmd='\n'.join('sha256sum '+Q(n.get('file','')) for n in xml.iter('PLUGIN'))
 foreign_before=call('all83-binaries.before',inventory_cmd)
 # Existing retained rc2 assets are read-only dependencies; verify every relevant byte against current source.
 names=['xml_contract.awk','payload.sha256','legacy-owned.sha256','portable/MPC-EURO - VST - GHOST/plugin-meta.xml']
 manifest=''.join(hashlib.sha256((R/'package-template'/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in names)
 call('reference-resources.verified','cd '+Q(a.reference_package)+' && sha256sum -c -',manifest.encode())
 library=(R/'package-template/common.sh').read_bytes()
 scope=library+b'\nFILE='+Q(target+'/ghost.so').encode()+b'\nTARGET='+Q(target).encode()+b'\nregistry=$(LC_ALL=C awk -v report=registry -f xml_contract.awk '+Q(settings).encode()+b')\nregistry_scope "$registry"\necho REGISTRY_SCOPE_PASS\n'
 call('native-registry-scope','cd '+Q(a.reference_package)+' && sh -s',scope)
 before=call('tree.before','tar -cf - -C '+Q(target)+' .')
 with tarfile.open(fileobj=io.BytesIO(before)) as t:
  members=t.getmembers();assert all(m.isfile() or m.isdir() for m in members);files={m.name.removeprefix('./'):(hashlib.sha256(t.extractfile(m).read()).hexdigest(),m.mode,m.uid,m.gid) for m in members if m.isfile()}
 assert len(files)==366 and sum(n.lower().endswith('.fxp') for n in files)==52
 for op in ['install','uninstall']:
  result=call('native-adoption.'+op,'cd '+Q(a.reference_package)+' && sh -s -- '+Q(target)+' /storage/Synths '+op,((R/'package-template/common.sh').read_bytes()+b'\n'+(R/'package-template/adoption.sh').read_bytes().replace(b'. ./common.sh\n',b''))).decode()
  rows=[line.split('\t',1) for line in result.splitlines()];assert len(rows)==366 and len({p for _,p in rows})==366
  report[op+'_plan_counts']={d:sum(x==d for x,_ in rows) for d,_ in rows}
  report[op+'_52_fxp_preserved']=all(d=='KEEP-PRESET' for d,n in rows if n.lower().endswith('.fxp'))
  assert report[op+'_52_fxp_preserved']
 # Predict the exact registry edit using shipped official awk; do not write any device file.
 code=(R/'package-template/plugin_list.awk').read_bytes()
 for mode in ['add','remove']:
  cmd='cd '+Q(a.reference_package)+' && awk -v mode='+mode+' -v file='+Q(target+'/ghost.so')+' -v uid=47485354 -v entryfile='+Q(target+'/plugin-meta.xml')+' -f /dev/stdin '+Q(settings)
  proposed=call('predicted-registry.'+mode,cmd,code);new=E.fromstring(proposed)
  def nodes(root):return [dict(n.attrib) for n in root.iter('PLUGIN')]
  foreign=lambda r:[x for x in nodes(r) if x.get('uid')!='47485354']
  assert foreign(xml)==foreign(new),'foreign registry edit predicted'
  def preferences_without_ghost(r):
   for parent in r.iter():
    for child in list(parent):
     if child.tag=='PLUGIN' and child.get('uid')=='47485354':parent.remove(child)
   def sem(n):return n.tag,sorted(n.attrib.items()),(n.text or '').strip(),[sem(c) for c in n]
   return sem(r)
  assert preferences_without_ghost(E.fromstring(raw))==preferences_without_ghost(E.fromstring(proposed))
  report['registry_'+mode+'_count']=len(nodes(new))
 call('layout-capacity','stat -c "%d %u %g %a %n" /storage/GHOST-Recovery /storage/GHOST-Work /storage/Synths;df -Pk /storage;du -sk '+Q(target)+' /storage/GHOST-Recovery /storage/GHOST-Work;find /storage/GHOST-Recovery/ghost-community-v2 -maxdepth 2 -type f -name state -exec cat {} \\;;find /storage/GHOST-Recovery /storage/GHOST-Work -maxdepth 3 -name "*lock*" -print')
 call('target-directory-devices','find '+Q(target)+' -type d -exec stat -c "%d %u %g %a %n" {} \\;')
 for suffix in ['.ghost-new','.ghost-restore']:
  call('settings-sidecar'+suffix,'test ! -e '+Q(settings+suffix))
 after=call('tree.after','tar -cf - -C '+Q(target)+' .')
 with tarfile.open(fileobj=io.BytesIO(after)) as t:now={m.name.removeprefix('./'):(hashlib.sha256(t.extractfile(m).read()).hexdigest(),m.mode,m.uid,m.gid) for m in t if m.isfile()}
 assert now==files,'concurrent GHOST change'
 assert call('settings.after','cat '+Q(settings))==raw,'concurrent settings change'
 assert call('all83-binaries.after',inventory_cmd)==foreign_before,'concurrent plugin binary change'
 assert call('host.after',hostcmd)==host,'concurrent host lifecycle change'
 report['all83_binaries_stable']=True
 report.update(go=True,decision='NATIVE READ-ONLY COMPATIBILITY PASS; retention export checkpoint required before third future transaction',files=366,fxp=52,settings_sha256=hashlib.sha256(raw).hexdigest(),classifier_sha256=hashlib.sha256((R/'package-template/adoption.sh').read_bytes()).hexdigest(),shared_library_sha256=hashlib.sha256((R/'package-template/common.sh').read_bytes()).hexdigest(),unknown_runtime_conflicts=0,reference_package_modified=False,physical_install_update_uninstall='NOT EXECUTED',actual_ownership='package runtime may normalize to root:root; preset/custom copied metadata retained; backup preserves original numeric owners')
except Exception as e:report.update(decision='NO-GO',error=str(e))
(a.out/'DRY_RUN.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['go'] else 1)
