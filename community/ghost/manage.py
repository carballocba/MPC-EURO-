#!/usr/bin/env python3
"""GHOST community installer. Python3 runs on the COMPUTER, never on the MPC.
No default host, personal baseline, other-plugin rollback or network dependency beyond SSH.
"""
import argparse,datetime,hashlib,io,json,os,pathlib,re,secrets,shlex,subprocess,tarfile,time,xml.etree.ElementTree as E
HERE=pathlib.Path(__file__).resolve().parent;FOLDER='MPC-EURO - VST - GHOST';UID='47485354';BINARY='588019130b31ced7077f7e4afe35bd23b0753df7a2959e2af39fa825e1b81afd'
def sha(b):return hashlib.sha256(b).hexdigest()
def safe_path(p):
 if not p.startswith('/') or any(c in p for c in '\r\n\0') or '..' in pathlib.PurePosixPath(p).parts or p=='/':raise ValueError('Unsafe absolute path')
 return p.rstrip('/')
def sem(e):return e.tag,sorted(e.attrib.items()),(e.text or '').strip(),[sem(c) for c in e]
def xml(raw):
 if not raw.strip():raise ValueError('TRANSPORT FAILURE: empty settings')
 if not raw.endswith(b'\n') or b'\0' in raw:raise ValueError('Settings must be newline-terminated XML without NUL')
 try:r=E.fromstring(raw)
 except E.ParseError as ex:raise ValueError('INVALID XML: '+str(ex)) from ex
 lists=r.findall('.//KNOWNPLUGINS')
 if r.tag!='PROPERTIES' or len(lists)!=1:raise ValueError('Unsupported plugin registry structure; no device changes')
 return r,lists[0]
def ghost(p):return p.get('uid','').lower() in (UID,str(int(UID,16)))
def registry_plan(raw,entry,action,target):
 """Validate XML locally, then splice only the exact GHOST lexical token."""
 a,plugins=xml(raw);own=[p for p in plugins if ghost(p)];fileowners=[p for p in plugins if p.get('file')==target+'/ghost.so']
 if len(own)>1 or any(not ghost(p) for p in fileowners):raise ValueError('Identity/path collision')
 if any(not ghost(p) and p.get('file','').startswith(target+'/') for p in plugins):raise ValueError('Another registered plugin is inside the GHOST folder; refuse replacement')
 if own and (own[0].get('uid')!=UID or own[0].get('file')!=target+'/ghost.so'):raise ValueError('GHOST identity/path differs; explicit migration required')
 tokens=[]
 for match in re.finditer(rb'<PLUGIN\s[^>]*?(?:/>|>\s*</PLUGIN>)',raw,re.S):
  p=E.fromstring(match[0])
  if ghost(p):tokens.append(match)
 if len(tokens)!=len(own):raise ValueError('Unsupported lexical PLUGIN representation')
 old=tokens[0][0] if tokens else b''
 if action=='install':
  p=E.fromstring(entry);p.set('file',target+'/ghost.so');new=E.tostring(p,encoding='utf-8')
  if not ghost(p) or p.get('uid')!=UID or p.get('isInstrument')!='0':raise ValueError('Invalid GHOST package identity')
  # Preserve settings inode/bytes on same-identity updates whenever attributes already match.
  if own and own[0].attrib==p.attrib:new=old
 else:new=b''
 if tokens:
  t=tokens[0];after=raw[:t.start()]+new+raw[t.end():]
 else:
  if action=='uninstall':after=raw
  else:
   new=new+b'\n'
   if raw.count(b'</KNOWNPLUGINS>')==1:after=raw.replace(b'</KNOWNPLUGINS>',new+b'</KNOWNPLUGINS>',1)
   else:
    empty=list(re.finditer(rb'<KNOWNPLUGINS\s*/>',raw))
    if len(empty)!=1:raise ValueError('Unsupported empty registry; no device changes')
    hit=empty[0];after=raw[:hit.start()]+b'<KNOWNPLUGINS>\n'+new+b'</KNOWNPLUGINS>'+raw[hit.end():]
 b,bl=xml(after)
 for tree in (a,b):
  pl=tree.find('.//KNOWNPLUGINS')
  for p in list(pl):
   if ghost(p):pl.remove(p)
 if sem(a)!=sem(b):raise ValueError('Unrelated settings/registry changed by plan')
 parsed,pl=xml(after);count=sum(ghost(p) for p in pl)
 if count!=(1 if action=='install' else 0):raise ValueError('GHOST registration count failed')
 return after,old,new

def tree(raw):
 if not raw:raise ValueError('TRANSPORT FAILURE: empty archive')
 out={}
 with tarfile.open(fileobj=io.BytesIO(raw)) as t:
  for m in t:
   if m.isdir():continue
   p=pathlib.PurePosixPath(m.name.removeprefix('./'))
   if not m.isfile() or p.is_absolute() or '..' in p.parts or any(c in str(p) for c in '\n\r\0') or str(p) in out:raise ValueError('Unsupported live file/link/path')
   out[str(p)]=t.extractfile(m).read()
 return out

def preserve_user_files(new,old):
 result=dict(new)
 for n,b in old.items():
  if n.endswith('.fxp') or (n not in result and n not in ('manifest.json','SHA256SUMS')):result[n]=b
 return result

def manifest(files):return ''.join(sha(b)+'  '+n+'\n' for n,b in sorted(files.items())).encode()
def make_plan(dest,raw,entry,old,new,action,synths,settings,service,pid,restarts,protected=b'',missing=b'',mode='600',observe=10,guard=180):
 dest.mkdir(parents=True,exist_ok=False);target=synths+'/'+FOLDER;after,before_token,after_token=registry_plan(raw,entry,action,target)
 records={'settings.before':raw,'settings.after':after,'registry.before.token':before_token,'registry.after.token':after_token,'current.sha256':manifest(old),'candidate.sha256':manifest(new),'protected.sha256':protected,'protected.missing':missing}
 conf=dict(TARGET=target,SYNTHS=synths,SETTINGS=settings,SERVICE=service,BEFORE_SHA=sha(raw),AFTER_SHA=sha(after),OLD_EXISTS=int(bool(old)),OP=action,EXPECT_PID=pid,EXPECT_RESTARTS=restarts,SETTINGS_MODE=mode,BEFORE_TOKEN_LEN=len(before_token),AFTER_TOKEN_LEN=len(after_token),OBSERVE_SECONDS=observe,GUARD_SECONDS=guard,GUARD_GRACE=5)
 records['plan.conf']=''.join(k+'='+shlex.quote(str(v))+'\n' for k,v in conf.items()).encode()
 for n,b in records.items():(dest/n).write_bytes(b)
 for n in ('transaction.sh','registry_inverse.awk'):(dest/n).write_bytes((HERE/n).read_bytes())
 if action=='install':
  for n,b in new.items():p=dest/'candidate'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 return conf

def state(raw):
 v=dict(line.split('=',1) for line in raw.decode().splitlines() if '=' in line)
 if v.get('ActiveState')!='active' or v.get('SubState')!='running' or int(v.get('MainPID','0'))<2:raise ValueError('Host inactive/unstable')
 return v
class Device:
 def __init__(self,host):
  if not re.fullmatch(r'(?:root@)?[A-Za-z0-9][A-Za-z0-9.-]*',host):raise ValueError('Unsafe SSH host')
  self.host=host;self.ssh=['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=3',host]
 def read(self,cmd,timeout=60):
  p=subprocess.run(self.ssh+[cmd],capture_output=True,timeout=timeout)
  if p.returncode:raise RuntimeError('SSH/REMOTE FAILURE: '+p.stderr.decode(errors='replace'))
  return p.stdout
 def service(self,s):return state(self.read('systemctl show '+s+' -p ActiveState -p SubState -p MainPID -p NRestarts'))

def payload():
 root=HERE/'portable'/FOLDER
 # Packaging checksums cover every file; never trust an arbitrary local .so.
 lines=(HERE/'SHA256SUMS').read_text().splitlines()
 for line in lines:
  h,n=line.split('  ',1);p=pathlib.PurePosixPath(n)
  if p.is_absolute() or '..' in p.parts or (HERE/n).is_symlink() or sha((HERE/n).read_bytes())!=h:raise ValueError('Package checksum/path mismatch: '+n)
 files={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
 expected={n.split('  ',1)[1][len('portable/'+FOLDER+'/'):] for n in lines if n.split('  ',1)[1].startswith('portable/'+FOLDER+'/')}
 if set(files)!=expected or any(p.is_symlink() for p in root.rglob('*')):raise ValueError('Unlisted payload file or symlink')
 b=files['ghost.so']
 if sha(b)!=BINARY or b[:6]!=b'\x7fELF\x01\x01' or int.from_bytes(b[18:20],'little')!=40 or not int.from_bytes(b[36:40],'little')&0x400:raise ValueError('Unapproved DSP/ARMv7 ABI')
 return files

def snapshot(d,synths,settings,service):
 q=shlex.quote;target=synths+'/'+FOLDER
 tools='df tar sha256sum systemctl sh awk sed find wc cp mv mkdir rmdir rm sleep kill nohup env sync cat chmod id uname'.split()
 d.read('test -f '+q(settings)+' && test ! -L '+q(settings)+' && test -w '+q(settings)+' && test -w '+q(synths)+' || exit 2; for t in '+' '.join(tools)+'; do command -v "$t" >/dev/null || exit 2; done; test "$(id -u)" = 0 || exit 2; case "$(uname -m)" in armv7*) ;; *) exit 2;; esac')
 first=d.service(service);raw=d.read('cat '+q(settings));_,pl=xml(raw)
 exists=d.read('if test -d '+q(target)+';then test ! -L '+q(target)+' || exit 2; echo yes;else test ! -e '+q(target)+' || exit 2; echo no;fi').strip()==b'yes'
 own=[p for p in pl if ghost(p)]
 if exists!=bool(own):raise ValueError('Unregistered directory or missing GHOST folder; review required')
 tar=d.read('tar -C '+q(target)+' -cf - .') if exists else None;old=tree(tar) if tar else {}
 inventory=b'';missing=b''
 for p in sorted({p.get('file') for p in pl if p.get('file') and not ghost(p)}):
  safe_path(p);result=d.read('if test -f '+q(p)+';then sha256sum '+q(p)+';else printf '+q('MISSING  '+p+'\n')+';fi')
  if result.startswith(b'MISSING  '):missing+=p.encode()+b'\n'
  else:
   if not re.fullmatch(rb'[0-9a-f]{64}  '+re.escape(p.encode())+rb'\n',result):raise ValueError('Incomplete other-plugin checksum')
   inventory+=result
 space=d.read('df -k '+q(synths));free=int(space.decode().splitlines()[-1].split()[3]);oldsize=sum(map(len,old.values()))
 if free*1024<max(50*1024*1024,oldsize*4):raise ValueError('Insufficient plugin disk space')
 settings_space=d.read('df -k '+q(str(pathlib.PurePosixPath(settings).parent)))
 if int(settings_space.decode().splitlines()[-1].split()[3])*1024<max(len(raw)*4,2*1024*1024):raise ValueError('Insufficient settings disk space')
 mem=d.read('cat /proc/meminfo');available=re.search(rb'^MemAvailable:\s+(\d+) kB',mem,re.M)
 if not available or int(available[1])<96*1024:raise ValueError('Insufficient/unverifiable RAM headroom')
 if d.read('cat '+q(settings))!=raw or d.service(service)!=first:raise ValueError('Concurrent settings/host change')
 return raw,old,tar,inventory,missing,first

def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('action',choices=['preflight','install','uninstall','rollback']);a.add_argument('--host',required=True);a.add_argument('--synths',required=True);a.add_argument('--settings',required=True);a.add_argument('--service',choices=['acvs','inmusic-mpc'],default='acvs');a.add_argument('--session',type=pathlib.Path);a.add_argument('--transaction');a.add_argument('--confirm',action='store_true');x=a.parse_args()
 synths=safe_path(x.synths);settings=safe_path(x.settings);d=Device(x.host);q=shlex.quote
 if x.action=='rollback':
  if not x.confirm or not x.transaction or not x.transaction.startswith(synths+'/.ghost-recovery/tx-'):raise ValueError('Rollback requires exact transaction and --confirm')
  print(d.read('env ACTION=rollback TX='+q(x.transaction)+' sh '+q(x.transaction+'/transaction.sh'),timeout=300).decode());return
 candidate=payload();raw,old,tar,protect,missing,service=snapshot(d,synths,settings,x.service)
 op='uninstall' if x.action=='uninstall' else 'install';registry_plan(raw,candidate['plugin-meta.xml'],op,synths+'/'+FOLDER)
 session=x.session or pathlib.Path('ghost-session-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+secrets.token_hex(3));session.mkdir(parents=True,exist_ok=False)
 (session/'MPC.settings.before').write_bytes(raw)
 if tar:(session/'ghost.before.tar').write_bytes(tar)
 report=dict(status='GO read-only',acvs=service,settings_sha256=sha(raw),old_files=len(old),old_binary_sha256=sha(old['ghost.so']) if old else None,new_binary_sha256=BINARY,registered_plugins=len(xml(raw)[1]))
 (session/'preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
 if x.action=='preflight':return
 if not x.confirm:raise ValueError('Device mutation requires --confirm after saving your project')
 if x.action=='uninstall' and not old:raise ValueError('No installed GHOST to remove')
 target=synths+'/'+FOLDER;new=preserve_user_files(candidate,old);new['plugin-meta.xml']=new['plugin-meta.xml'].replace(b'%payload-path%',synths.encode())
 plan=session/'stage';make_plan(plan,raw,candidate['plugin-meta.xml'],old,new,op,synths,settings,x.service,service['MainPID'],service['NRestarts'],protect,missing)
 if d.read('cat '+q(settings))!=raw or d.service(x.service)!=service:raise ValueError('Fresh gate changed; NO-GO')
 # No remote writes before this point. Independent SSH shell stays open during backup/activation/recovery.
 recovery_log=(session/'recovery-ssh.log').open('wb');recovery=subprocess.Popen(d.ssh+["printf 'RECOVERY_READY\\n'; exec sh -s"],stdin=subprocess.PIPE,stdout=recovery_log,stderr=subprocess.STDOUT)
 try:
  for _ in range(50):
   if recovery.poll() is not None:break
   if b'RECOVERY_READY' in (session/'recovery-ssh.log').read_bytes():break
   time.sleep(.1)
  if recovery.poll() is not None or b'RECOVERY_READY' not in (session/'recovery-ssh.log').read_bytes():raise ValueError('Independent SSH unavailable')
  tx=synths+'/.ghost-recovery/tx-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+secrets.token_hex(6)
  bundle=session/'stage.tar'
  with tarfile.open(bundle,'w') as t:
   for p in sorted(plan.rglob('*')):
    if p.is_file():t.add(p,arcname=str(p.relative_to(plan)),recursive=False)
  d.read('umask 077; mkdir -p '+q(synths+'/.ghost-recovery')+'; mkdir '+q(tx))
  subprocess.run(d.ssh+['umask 077; cat > '+q(tx+'/stage.tar')],input=bundle.read_bytes(),check=True,timeout=120)
  d.read('test "$(sha256sum '+q(tx+'/stage.tar')+' | sed \'s/[[:space:]].*//\')" = '+sha(bundle.read_bytes())+' && tar -xf '+q(tx+'/stage.tar')+' -C '+q(tx))
  (session/'transaction.json').write_text(json.dumps(dict(tx=tx,rollback='python3 manage.py rollback --host '+x.host+' --synths '+q(synths)+' --settings '+q(settings)+' --transaction '+q(tx)+' --confirm'),indent=2)+'\n')
  try:
   output=d.read('env ACTION=run TX='+q(tx)+' sh '+q(tx+'/transaction.sh'),timeout=300);(session/'install.log').write_bytes(output)
   after=(plan/'settings.after').read_bytes()
   if d.read('cat '+q(settings))!=after:raise ValueError('Settings postcheck failed')
   if op=='install' and tree(d.read('tar -C '+q(target)+' -cf - .'))!=new:raise ValueError('Full payload postcheck failed')
   print(json.dumps(dict(status='TECHNICAL PASS; hardware pending',host=d.service(x.service),transaction=tx,backup=tx+'/backup',settings_sha256=sha(after)),indent=2))
  except Exception:
   # Idempotent recovery from the same transaction; never starts a second install.
   try:(session/'emergency-rollback.log').write_bytes(d.read('env ACTION=rollback TX='+q(tx)+' sh '+q(tx+'/transaction.sh'),timeout=300))
   except Exception as ex:raise RuntimeError('Recovery needs review; preserve SSH and '+tx) from ex
   raise
 finally:
  if recovery.stdin:recovery.stdin.close()
  try:recovery.wait(timeout=5)
  except subprocess.TimeoutExpired:recovery.terminate()
  recovery_log.close()
if __name__=='__main__':
 try:main()
 except Exception as ex:raise SystemExit('STOPPED: '+str(ex))
