#!/usr/bin/env python3
"""Read-only route gate; runs exact candidate parser/guard, never installer/service control."""
import argparse,hashlib,json,os,pathlib,shlex,subprocess,xml.etree.ElementTree as ET,zipfile
p=argparse.ArgumentParser();p.add_argument('--candidate',required=True,type=pathlib.Path);p.add_argument('--settings-file',type=pathlib.Path);p.add_argument('--host');p.add_argument('--settings',default='/data/Settings/MPC/MPC.settings');p.add_argument('--recovery',default='/storage/GHOST-Recovery');p.add_argument('--work',default='/storage/GHOST-Work');p.add_argument('--out',required=True,type=pathlib.Path);a=p.parse_args()
assert bool(a.host)!=bool(a.settings_file),'choose saved settings OR explicit SSH host'
a.out.mkdir(parents=True,exist_ok=False);a.out.chmod(0o700)
def ssh(cmd,data=None):
 r=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','-o','ServerAliveInterval=3','-o','ServerAliveCountMax=3',a.host,cmd],input=data,capture_output=True,timeout=60)
 if r.returncode:raise RuntimeError('transport/remote check failed, exit '+str(r.returncode)+': '+r.stderr.decode(errors='replace'))
 return r.stdout
result={'go':False,'device_modified':False,'scope':'path gate only, not full installation approval'}
try:
 with zipfile.ZipFile(a.candidate) as z:
  assert z.testzip() is None,'corrupt candidate ZIP'
  for line in z.read('GHOST-2.4.2/SHA256SUMS').decode().splitlines():
   digest,name=line.split('  ',1);assert hashlib.sha256(z.read('GHOST-2.4.2/'+name)).hexdigest()==digest,'candidate internal checksum mismatch'
  parser=z.read('GHOST-2.4.2/xml_contract.awk');common=z.read('GHOST-2.4.2/common.sh')
 raw=ssh('cat '+shlex.quote(a.settings)) if a.host else a.settings_file.read_bytes()
 assert raw,'empty settings transport/read output, not proof of invalid XML'
 expected=[n.text or '' for n in ET.fromstring(raw).findall('.//SynthContentLocations/Location')]
 assert expected,'missing discovery locations'
 if a.host:
  native=ssh('LC_ALL=C awk -v report=locations -f /dev/stdin '+shlex.quote(a.settings),parser)
 else:
  import tempfile
  with tempfile.NamedTemporaryFile() as f:
   f.write(parser);f.flush();r=subprocess.run(['awk','-v','report=locations','-f',f.name],input=raw,capture_output=True,env=dict(os.environ,LC_ALL='C'));assert r.returncode==0,r.stderr;native=r.stdout
 assert native==(''.join(x+'\n' for x in expected)).encode(),'native decoder differs from local XML reference'
 result.update(settings_sha256=hashlib.sha256(raw).hexdigest(),candidate_sha256=hashlib.sha256(a.candidate.read_bytes()).hexdigest(),locations=len(expected),decoder_matches=True)
 if a.host:
  # Execute only definitions and read-only canonical path comparisons; no remote temp files.
  for root in [a.recovery,a.work]:
   delimiter='GHOST_CONTENT_'+hashlib.sha256(native).hexdigest();assert delimiter.encode() not in native
   script=common+b'\nCONTENT=/dev/stdin\nchecked=$(canon '+shlex.quote(root).encode()+b')\noutside_content "$checked" <<\''+delimiter.encode()+b"'\n"+native+delimiter.encode()+b'\n'
   ssh('sh -s',script)
  assert ssh('cat '+shlex.quote(a.settings))==raw,'concurrent settings change'
  result.update(go=True,decision='PASS: exact native decoder and canonical path guards; full fresh preflight still required')
 else:result['decision']='OFFLINE decoder PASS; physical canonical paths NOT TESTED'
except Exception as e:result['error']=str(e);result['decision']='NO-GO'
f=a.out/'PATH_PREFLIGHT.json';f.write_text(json.dumps(result,indent=2)+'\n');f.chmod(0o600);print(f.read_text());raise SystemExit(1 if 'error' in result else 0)
