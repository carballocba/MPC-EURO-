#!/usr/bin/env python3
"""Offline command mocks. Never included in a runtime package."""
import os,sys,json,time,pathlib,subprocess,zlib,fcntl
root=pathlib.Path(os.environ['FIXTURE']);name=pathlib.Path(sys.argv[0]).name;args=sys.argv[1:]
c=json.loads((root/'control.json').read_text())
def event(s):
 with (root/'events').open('a') as f:f.write(s+'\n')
def state():return json.loads((root/'service.json').read_text())
def save(s):
 p=root/('service.'+str(os.getpid()));p.write_text(json.dumps(s));p.replace(root/'service.json')
if name=='identity':
 try:
  os.kill(int(args[0]),0)
  s=subprocess.check_output(['/bin/ps','-p',args[0],'-o','lstart='],stderr=subprocess.DEVNULL).strip()
  if not s:sys.exit(1)
  print(zlib.crc32(s))
 except (ProcessLookupError,subprocess.CalledProcessError):sys.exit(1)
elif name=='id':print(c.get('uid',0))
elif name=='uname':print(c.get('arch','armv7l'))
elif name=='sleep':time.sleep(float(args[0])*.025)
elif name=='stat':
 p=pathlib.Path(args[-1]);device=os.stat(p).st_dev
 if c.get('crossfs') and str(p).startswith(str(root/'recovery')):device+=1
 if c.get('bad_workfs') and str(p).startswith(str(root/'work')):device+=2
 fmt=args[1]
 if fmt=='%u':print(c.get('root_owner',0))
 elif fmt=='%a':print(oct(os.stat(p).st_mode&0o777)[2:])
 elif fmt=='%d:%i':print(str(device)+':'+str(os.stat(p).st_ino))
 else:print(device)
elif name=='df':
 print('Filesystem 1024-blocks Used Available Capacity Mounted on');print('mock 999999 10',c.get('free_kb',900000),'1%',root)
elif name=='pidof':
 if state()['active']:print(state()['pid'])
 else:sys.exit(1)
elif name=='systemctl':
 a=[v for v in args if not v.startswith('--')]
 if a[0]=='cat':sys.exit(0)
 s=state()
 if a[0] in ['stop','start']:
  op=a[0];event(op+' begin '+str(os.getpid()));time.sleep(c.get('delay_'+op,0))
  if op=='stop':
   if c.get('rewrite_stop'):
    p=root/'MPC.settings';p.write_text(p.read_text().replace('val="before"','val="saved-on-stop"'))
   s.update(active=False,pid=0)
  else:
   if c.get('fail_start'):sys.exit(1)
   s.update(active=True,pid=2222)
  save(s);event(op+' end '+str(os.getpid()));sys.exit(0)
 if a[0]=='is-active':sys.exit(0 if s['active'] else 3)
 if a[0]=='show':print(s['pid'] if 'MainPID' in a else s.get('restarts',0))
 else:sys.exit(2)
else:raise SystemExit('unknown mock '+name)
