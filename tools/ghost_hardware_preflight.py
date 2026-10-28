#!/usr/bin/env python3
"""Explicitly invoked read-only SSH inspection; never executes install/recovery/service control."""
import argparse,hashlib,json,os,pathlib,re,shlex,subprocess,time,tarfile,io,xml.etree.ElementTree as E,zipfile
p=argparse.ArgumentParser();p.add_argument('--host',required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--synths',required=True);p.add_argument('--settings',required=True);p.add_argument('--recovery',required=True);p.add_argument('--work',required=True);p.add_argument('--candidate',type=pathlib.Path,required=True);a=p.parse_args()
if not re.fullmatch(r'root@[a-zA-Z0-9.:-]+',a.host):p.error('explicit root@host required')
for s in [a.synths,a.settings,a.recovery,a.work]:
 if not s.startswith('/') or any(c in s for c in ['\n','\r','\x00']):p.error('absolute paths required')
a.out.mkdir(parents=True,exist_ok=False);a.out.chmod(0o700)
def save(name,data):
 f=a.out/name;f.write_bytes(data if isinstance(data,bytes) else data.encode());f.chmod(0o600)
def read(cmd,name,required=True,allow_remote_failure=False,stdin=None):
 # SSH/Python timeouts run on the computer; no GNU timeout/base64/remote Python.
 r=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','-o','ServerAliveInterval=3','-o','ServerAliveCountMax=3',a.host,cmd],capture_output=True,timeout=60,input=stdin)
 save(name+'.stderr',r.stderr)
 if r.returncode:
  if allow_remote_failure and r.returncode!=255:
   report.setdefault('remote_check_failures',[]).append({'check':name,'exit':r.returncode});save(name,r.stdout);return r.stdout
  raise RuntimeError('TRANSPORT/REMOTE COMMAND FAILURE '+name+' (exit '+str(r.returncode)+'); no XML corruption inferred')
 if required and not r.stdout:raise RuntimeError('EMPTY SSH OUTPUT '+name+'; transport/read failure, not proof of invalid XML')
 save(name,r.stdout);return r.stdout
report={'device_modified':False,'fresh_hardware_test':False,'checks':{},'go':False}
try:
 q=shlex.quote;target=a.synths+'/MPC-EURO - VST - GHOST'
 candidate=a.candidate.read_bytes();report['candidate_sha256']=hashlib.sha256(candidate).hexdigest()
 with zipfile.ZipFile(io.BytesIO(candidate)) as z:
  binary=z.read('GHOST-2.4.2/portable/MPC-EURO - VST - GHOST/ghost.so');assert hashlib.sha256(binary).hexdigest()=='588019130b31ced7077f7e4afe35bd23b0753df7a2959e2af39fa825e1b81afd'
  for l in z.read('GHOST-2.4.2/SHA256SUMS').decode().splitlines():h,n=l.split('  ',1);assert hashlib.sha256(z.read('GHOST-2.4.2/'+n)).hexdigest()==h
 service=read('if systemctl cat acvs >/dev/null 2>&1;then echo acvs;else echo inmusic-mpc;fi','service.txt').decode().strip();assert service in ['acvs','inmusic-mpc']
 cmd='systemctl show '+service+' -p ActiveState -p SubState -p MainPID -p NRestarts -p ActiveEnterTimestampMonotonic; cat /proc/sys/kernel/random/boot_id'
 before=read(cmd,'host.before.txt')
 raw=read('cat '+q(a.settings),'MPC.settings.before')
 try:xml=E.fromstring(raw)
 except E.ParseError as e:raise RuntimeError('NONEMPTY SETTINGS RECEIVED BUT INVALID XML: '+str(e)) from e
 entries=[dict(n.attrib) for n in xml.iter('PLUGIN')];report['plugins']=len(entries);report['settings_sha256']=hashlib.sha256(raw).hexdigest()
 g=[x for x in entries if x.get('uid')=='47485354'];assert len(g)==1 and g[0].get('file')==target+'/ghost.so';report['ghost']=g[0]
 assert not any(x.get('uid')=='45754272' or 'beatrepeat' in x.get('name','').lower() for x in entries)
 read('uname -m; cat /sys/firmware/devicetree/base/model; printf "\\n"; cat /etc/os-release','device.txt')
 locations=[n.text for n in xml.iter('Location') if n.text];report['configured_content_locations']=locations
 report['hakai_version']='NOT independently verified: user/physical confirmation required; os-release is not automatically Hakai version'
 read('df -Pk '+q(a.synths)+' && cat /proc/meminfo','storage-memory.txt')
 read('for c in sh awk sha256sum tar stat df du systemctl nohup pidof;do command -v "$c" || exit 1;done; cat /proc/mounts','tools-mounts.txt')
 read('ls -ld '+q(a.recovery)+' '+q(a.work)+'; stat -c "%d %u %a %n" '+q(a.synths)+' '+q(a.recovery)+' '+q(a.work),'recovery-roots.txt',required=False,allow_remote_failure=True)
 read('ls -la '+q(a.synths)+'; du -sh '+q(a.synths),'synths-listing.txt')
 journal=read('journalctl -u '+service+' -b --no-pager -n 200','host-journal.txt')
 report['journal_red_flags']=bool(re.search(rb'SIGSEGV|segfault|core.dump|Scheduled restart',journal,re.I))
 data=read('tar -cf - -C '+q(target)+' .','ghost.readonly.tar')
 with tarfile.open(fileobj=io.BytesIO(data)) as t:
  ms=t.getmembers();assert all(m.isfile() or m.isdir() for m in ms);report['ghost_files']=sum(m.isfile() for m in ms)
  bins=[m for m in ms if m.name.removeprefix('./')=='ghost.so'];assert len(bins)==1;report['installed_binary_sha256']=hashlib.sha256(t.extractfile(bins[0]).read()).hexdigest()
 report['readonly_backup_sha256']=hashlib.sha256(data).hexdigest()
 with tarfile.open(fileobj=io.BytesIO(data)) as t:
  manifest=[]
  for m in t.getmembers():
   if not m.isfile():continue
   name=m.name.removeprefix('./');assert not name.startswith('/') and '..' not in pathlib.PurePosixPath(name).parts and not any(v in name for v in ['\n','\r','\\'])
   manifest.append(hashlib.sha256(t.extractfile(m).read()).hexdigest()+'  '+name+'\n')
 read('cd '+q(target)+' && sha256sum -c -','backup-remote-verify.txt',stdin=''.join(manifest).encode())
 report['readonly_backup_remote_verified']=True
 # Dynamic inventory; no hard-coded historic registry count or private expected foreign hashes.
 cmds=[]
 for x in entries:
  path=x.get('file','')
  if path.startswith('/'):cmds.append('if [ -f '+q(path)+' ];then sha256sum '+q(path)+';else printf "MISSING %s\\n" '+q(path)+';fi')
 read('\n'.join(cmds),'plugins.sha256',required=bool(cmds))
 read('find '+q(a.recovery)+' '+q(a.work)+' -maxdepth 3 -type f -name state -print','recovery-state.txt',required=False,allow_remote_failure=True)
 time.sleep(3);after=read(cmd,'host.after.txt');assert before==after,'host identity/restart state changed during preflight'
 current=read('cat '+q(a.settings),'MPC.settings.after');assert raw==current,'settings changed concurrently during preflight'
 assert b'ActiveState=active' in after and b'SubState=running' in after
 report['checks']={'host_snapshot_stable':True,'settings_bytes_stable':True,'plugin_registration_valid':True,'candidate_internal_hashes':True,'read_only_backup_inspectable':True}
 # Root ownership/noexec/discovery checks must be independently reviewed before write authorization.
 report['decision']=('NO-GO: recovery/work roots require provision or review' if report.get('remote_check_failures') else 'READ_ONLY_EVIDENCE_COLLECTED; manual review of roots, baseline hashes and journal required before GO')
except Exception as e:report['decision']='NO-GO';report['error']=str(e)
save('PREFLIGHT.json',json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if 'error' not in report and not report.get('remote_check_failures') else 1)
