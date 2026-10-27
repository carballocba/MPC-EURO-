import os,pathlib,subprocess,tempfile,zipfile,json,hashlib,stat
ROOT=pathlib.Path(__file__).resolve().parents[2];B=ROOT/'build/ghost-release-final';B.mkdir(parents=True,exist_ok=True);ZIP=pathlib.Path(os.environ.get('GHOST_RELEASE_ZIP',B/'final/GHOST-2.4.2-mpc-armv7.zip'))
def tree(p):return {str(x.relative_to(p)):(x.read_bytes(),stat.S_IMODE(x.stat().st_mode)) for x in p.rglob('*') if x.is_file()}
results=[]
for scenario in ['clean','upgrade','reinstall','uninstall','copy','registry','stopped','renamed','activated','registered','started','collision','foreign-inside','defer','rollback-twice','watchdog-loss']+['uninstall-fail-'+n for n in ['copy','registry','stopped','renamed','activated','registered','started']]:
 if os.environ.get('GHOST_TEST_ONLY') and scenario not in os.environ['GHOST_TEST_ONLY'].split(','):continue
 with tempfile.TemporaryDirectory(prefix='ghost-tx-') as td:
  print('Testing',scenario,flush=True)
  t=pathlib.Path(td)
  with zipfile.ZipFile(ZIP) as z:z.extractall(t/'pkg')
  pkg=t/'pkg/GHOST-2.4.2';synths=t/'Synths';synths.mkdir();target=synths/'MPC-EURO - VST - GHOST'
  for n in ['PD LAB','MPC-CORE','Another Plugin']:
   (synths/n).mkdir();(synths/n/'foreign.so').write_bytes(n.encode())
  foreign={n:tree(synths/n) for n in ['PD LAB','MPC-CORE','Another Plugin']}
  settings=t/'MPC.settings';settings.write_text('<PROPERTIES>\n<VALUE name="Hardware.EthernetIPv4DNS" val="keep"/>\n<VALUE name="pluginList-arm">\n<KNOWNPLUGINS>\n<PLUGIN name="PD LAB" uid="50644c33" file="/foreign.so"/>\n</KNOWNPLUGINS>\n</VALUE>\n</PROPERTIES>\n');settings.chmod(0o600)
  shim=t/'bin';shim.mkdir();import shutil
  sumtool=shutil.which('sha256sum')
  if not sumtool:
   if not (B/'test-sha256sum').exists():subprocess.run(['cc','-Wno-deprecated-declarations',str(pathlib.Path(__file__).with_name('test-sha256sum.c')),'-o',str(B/'test-sha256sum')],check=True)
   sumtool=str(B/'test-sha256sum')
  (shim/'sha256sum').symlink_to(sumtool)
  env=dict(os.environ,PATH=str(shim)+':'+os.environ['PATH'],MPC_INSTALL_TEST='1',MPC_SETTINGS=str(settings),MPC_TEST_LOG=str(t/'service.log'))
  def run(action='install',extra=(),e=None):return subprocess.run(['sh',action+'.sh','-y','-t',str(synths),*extra],cwd=pkg,env=e or env,capture_output=True,text=True)
  if scenario!='clean':
   # Upgrade baseline is exactly the previous physically tested 366-file package.
   old=ROOT/'build/ghost-release-final/tested/GHOST-2.4.2/portable/MPC-EURO - VST - GHOST'
   import shutil
   if os.environ.get('GHOST_PREVIOUS_ZIP'):
    with zipfile.ZipFile(os.environ['GHOST_PREVIOUS_ZIP']) as previous:previous.extractall(t/'previous')
    old=t/'previous/GHOST-2.4.2/portable/MPC-EURO - VST - GHOST'
   shutil.copytree(old,target)
   (target/'custom-bank.fxp').write_bytes(b'CUSTOM ROOT');(target/'Presets/user.fxp').write_bytes(b'USER')
   f=next((target/'Preset Library').rglob('*.fxp'));f.write_bytes(b'USER EDIT')
  if scenario in ['reinstall','uninstall','rollback-twice','watchdog-loss']+['uninstall-fail-'+n for n in ['copy','registry','stopped','renamed','activated','registered','started']]:
   p=run();assert p.returncode==0,p.stdout+p.stderr
  if scenario=='collision':(target/'ghost.so').write_bytes(b'UNKNOWN MODIFIED RUNTIME')
  if scenario=='foreign-inside':settings.write_text(settings.read_text().replace('</KNOWNPLUGINS>',f'<PLUGIN name="Foreign" uid="abcdef01" file="{target}/foreign.so"/>\n</KNOWNPLUGINS>'))
  before=tree(target) if target.exists() else {};prefs=settings.read_bytes();mode=stat.S_IMODE(settings.stat().st_mode)
  ev=env.copy()
  if scenario in ['copy','registry','stopped','renamed','activated','registered','started']:ev['GHOST_FAILPOINT']=scenario
  if scenario.startswith('uninstall-fail-'):ev['GHOST_FAILPOINT']=scenario.removeprefix('uninstall-fail-')
  p=run('uninstall' if scenario=='uninstall' or scenario.startswith('uninstall-fail-') else 'install',('-n',) if scenario=='defer' else (),ev)
  rejected=scenario.startswith('uninstall-fail-') or scenario in ['copy','registry','stopped','renamed','activated','registered','started','collision','foreign-inside']
  assert (p.returncode!=0)==rejected,(scenario,p.stdout,p.stderr)
  assert stat.S_IMODE(settings.stat().st_mode)==mode,scenario+' settings mode'
  if rejected:
   assert tree(target)==before,scenario+' plugin rollback'
   assert settings.read_bytes()==prefs,scenario+' settings rollback'
  elif scenario=='uninstall':
   assert (target/'custom-bank.fxp').read_bytes()==b'CUSTOM ROOT'
   assert (target/'Presets/user.fxp').read_bytes()==b'USER'
   assert f.read_bytes()==b'USER EDIT'
   assert not (target/'ghost.so').exists()
  else:
   assert hashlib.sha256((target/'ghost.so').read_bytes()).hexdigest()=='588019130b31ced7077f7e4afe35bd23b0753df7a2959e2af39fa825e1b81afd'
   if scenario!='clean':assert (target/'custom-bank.fxp').read_bytes()==b'CUSTOM ROOT' and f.read_bytes()==b'USER EDIT'
  for n,v in foreign.items():assert tree(synths/n)==v
  assert b'Hardware.EthernetIPv4DNS" val="keep' in settings.read_bytes()
  if scenario=='defer':assert not (t/'service.log').exists()
  if scenario in ['rollback-twice','watchdog-loss']+['uninstall-fail-'+n for n in ['copy','registry','stopped','renamed','activated','registered','started']]:
   tx=sorted((synths/'.ghost-recovery').iterdir())[-1]
   if scenario=='watchdog-loss':
    (tx/'committed').unlink();(tx/'done').unlink();(tx/'worker').write_text('99999999');(tx/'worker.start').write_text('1')
    r=subprocess.run(['sh',str(tx/'watchdog.sh'),str(tx)],env=env,capture_output=True,text=True);assert r.returncode==0,r.stderr
   for _ in range(2):
    r=subprocess.run(['sh',str(tx/'rollback.sh'),str(tx)],env=env,capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
   assert tree(target)==before and settings.read_bytes()==prefs
  assert not (synths/'.ghost-installer-lock').exists(),scenario+' lock'
  results.append({'scenario':scenario,'pass':True})
(B/('INSTALLER_TEST_RESULTS'+('-EXTRA' if os.environ.get('GHOST_TEST_ONLY') else '')+'.json')).write_text(json.dumps(results,indent=2)+'\n');print(len(results),'scenarios PASS')
