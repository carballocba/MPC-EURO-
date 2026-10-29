#!/usr/bin/env python3
import os,sys,time,pathlib,tempfile,subprocess,shutil,json,hashlib,signal,unittest,zipfile
HERE=pathlib.Path(__file__).resolve().parent;R=HERE.parents[1];T=R/'package-template';F='MPC-EURO - VST - GHOST';OUT=R/'evidence/hardening';OUT.mkdir(parents=True,exist_ok=True)
SUM=shutil.which('sha256sum')
if not SUM:
 _SUM_DIR=tempfile.TemporaryDirectory(prefix='ghost-test-sha-')
 SUM=str(pathlib.Path(_SUM_DIR.name)/'sha256sum');subprocess.run(['cc','-Wno-deprecated-declarations',str(HERE/'sha256sum-macos.c'),'-o',SUM],check=True)
def inventory(p):return {str(f.relative_to(p)):(hashlib.sha256(f.read_bytes()).hexdigest(),f.stat().st_mode&0o777) for f in p.rglob('*') if f.is_file()} if p.exists() else {}
def sums(p):
 (p/'SHA256SUMS').unlink(missing_ok=True);(p/'SHA256SUMS').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.relative_to(p).as_posix()+'\n' for f in sorted(p.rglob('*')) if f.is_file()))
class Fixture:
 def __init__(self,control=None,hook=None,full=False):
  self.tmp=tempfile.TemporaryDirectory(prefix='ghost-harden-');self.r=pathlib.Path(self.tmp.name).resolve();r=self.r;self.c=control or {};self.hook=hook or {};self.ps=[]
  self.pkg=r/'package';shutil.copytree(T,self.pkg);self.target=r/'Synths'/F;(r/'Synths').mkdir();(r/'recovery').mkdir();(r/'work').mkdir();(r/'bin').mkdir();(r/'proc/sys/kernel/random').mkdir(parents=True)
  (r/'proc/sys/kernel/random/boot_id').write_text('boot-a');(r/'proc/mounts').write_text('mock / mock '+self.c.get('mount','rw,exec')+' 0 0\n')
  (r/'control.json').write_text(json.dumps(self.c));(r/'service.json').write_text(json.dumps(dict(active=not self.c.get('defer',False),pid=1111,restarts=0)))
  self.settings=r/'MPC.settings';self.settings.write_text(f'<PROPERTIES>\n<VALUE name="preference" val="before"/>\n<VALUE name="SynthContentLocations"><SynthContentLocations><Location>{r}/Synths</Location><Location>{r}/other-content</Location></SynthContentLocations></VALUE>\n<VALUE name="pluginList-arm">\n<KNOWNPLUGINS>\n<PLUGIN name="PD LAB" uid="50644c33" file="/other/pd.so"/>\n<PLUGIN name="MPC-CORE" uid="4d435232" file="/other/core.so"/>\n</KNOWNPLUGINS>\n</VALUE>\n</PROPERTIES>\n');self.settings.chmod(0o600)
  for p in ['PD LAB','MPC-CORE']:
   d=r/'Synths'/p;d.mkdir();(d/'binary.so').write_text('foreign '+p)
  self.foreign={p:inventory(r/'Synths'/p) for p in ['PD LAB','MPC-CORE']}
  for n in ['identity','id','uname','sleep','stat','df','pidof','systemctl']:(r/'bin'/n).symlink_to(HERE/'mock.py')
  (HERE/'mock.py').chmod(0o755);(r/'bin/sha256sum').symlink_to(SUM)
  payload=self.pkg/'portable'/F
  shutil.copy2(R/'rebuild/ghost.so',payload/'ghost.so')
  if not full:
   keep=['ghost.so','mpc-plugin.json','plugin-meta.xml','version.xml','Plugin Skins/TUI.json','Plugin Skins/Q-Links.json']
   fxps=[p.relative_to(payload).as_posix() for p in payload.rglob('*.fxp')][:2];keep+=fxps
   for p in list(payload.rglob('*')):
    if p.is_file() and p.relative_to(payload).as_posix() not in keep:p.unlink()
   for p in sorted(payload.rglob('*'),reverse=True):
    if p.is_dir() and not list(p.iterdir()):p.rmdir()
  self.old=r/'old';shutil.copytree(payload,self.old)
  self.fx=next(self.old.rglob('*.fxp')).relative_to(self.old)
  # Instrument only an ephemeral harness copy: no bypass/hook executable is shipped.
  for p in self.pkg.glob('*.sh'):
   s=p.read_text().replace('/proc',str(r/'proc'))
   if p.name=='common.sh':
    a=s.index('proc_id() {');b=s.index('\nboot()',a);s=s[:a]+'proc_id() { identity "$1"; }'+s[b:]
   if p.name=='transaction.sh':
    for name,cmd in self.hook.items():s=s.replace('# @HOOK '+name,cmd)
   if p.name=='rollback.sh':s=s.replace('# @HOOK rollback-owned','printf "owned %s\\n" "$$" >> "'+str(r/'rollback-owners')+'"\n'+self.c.get('rollback_hook',''))
   if p.name=='watchdog.sh' and self.c.get('timeout'):s=s.replace('-ge 180','-ge 2')
   p.write_text(s)
  # Legacy ownership is frozen for this synthetic fixture, not a forged production baseline.
  self.manifest(payload,self.pkg/'payload.sha256');self.manifest(self.old,self.pkg/'legacy-owned.sha256');sums(self.pkg)
  self.env=dict(os.environ,PATH=str(r/'bin')+':'+os.environ['PATH'],FIXTURE=str(r),MPC_SETTINGS=str(self.settings),GHOST_RECOVERY_ROOT=str(r/'recovery'),GHOST_WORK_ROOT=str(r/'work'))
 def manifest(self,root,p):p.write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.relative_to(root).as_posix()+'\n' for f in sorted(root.rglob('*')) if f.is_file()))
 def old_install(self):
  shutil.copytree(self.old,self.target);(self.target/'custom.fxp').write_bytes(b'custom-root');(self.target/self.fx).write_bytes(b'edited factory preset')
 def run(self,action='install',extra=(),env=None,background=False):
  log=self.r/('out-'+str(len(self.ps))+'.log');fh=log.open('wb');p=subprocess.Popen(['sh',action+'.sh','-y','-t',str(self.r/'Synths'),*extra],cwd=self.pkg,env=env or self.env,stdout=fh,stderr=subprocess.STDOUT,start_new_session=True);fh.close();self.ps.append(p)
  if background:return p,log
  try:return p.wait(timeout=100),log.read_text()
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);raise
 def tx(self):return sorted((self.r/'recovery/ghost-community-v2').glob('tx-*'))[-1]
 def recover(self,tx=None,background=False):
  t=tx or self.tx();log=self.r/('recover-'+str(len(self.ps))+'.log');fh=log.open('wb');p=subprocess.Popen(['sh',str(t/'recover.sh'),str(t)],env=self.env,stdout=fh,stderr=subprocess.STDOUT,start_new_session=True);fh.close();self.ps.append(p)
  return (p,log) if background else (p.wait(timeout=100),log.read_text())
 def waitfor(self,p):
  end=time.time()+20
  while time.time()<end:
   if p.exists():return
   time.sleep(.03)
  raise AssertionError('checkpoint not reached '+str(p)+'\n'+'\n'.join(f.read_text()[-1600:] for f in self.r.glob('out-*')))
 def clear_hooks(self):
  p=self.pkg/'transaction.sh';s=p.read_text()
  for k,v in self.hook.items():s=s.replace(v,'# @HOOK '+k)
  p.write_text(s);sums(self.pkg)
 def control(self,**kw):self.c.update(kw);(self.r/'control.json').write_text(json.dumps(self.c))
 def check_foreign(self):
  assert all(inventory(self.r/'Synths'/p)==v for p,v in self.foreign.items())
  assert b'PD LAB' in self.settings.read_bytes() and b'MPC-CORE' in self.settings.read_bytes()
 def close(self):
  # Test children only; no device/network tools exist in the harness.
  for p in self.ps:
   if p.poll() is None:
    try:os.killpg(p.pid,signal.SIGKILL)
    except ProcessLookupError:pass
  self.tmp.cleanup()
class Tests(unittest.TestCase):
 def setUp(self):self.fixtures=[]
 def f(self,*a,**kw):f=Fixture(*a,**kw);self.fixtures.append(f);return f
 def tearDown(self):
  for f in self.fixtures:f.close()
 def ok(self,result):self.assertEqual(result[0],0,result[1])
 def test_01_fresh(self):
  f=self.f();self.ok(f.run());self.assertTrue((f.target/'ghost.so').exists());f.check_foreign()
 def test_02_update(self):
  f=self.f();f.old_install();self.ok(f.run());self.assertEqual((f.target/'custom.fxp').read_bytes(),b'custom-root');self.assertEqual((f.target/f.fx).read_bytes(),b'edited factory preset');f.check_foreign()
 def test_03_reinstall(self):
  f=self.f();self.ok(f.run());s=f.settings.read_bytes();self.ok(f.run());self.assertEqual(s,f.settings.read_bytes());f.check_foreign()
 def test_04_uninstall(self):
  f=self.f();self.ok(f.run());self.ok(f.run('uninstall'));self.assertFalse((f.target/'ghost.so').exists());f.check_foreign()
 def test_05_uninstall_custom(self):
  f=self.f();f.old_install();self.ok(f.run());self.ok(f.run('uninstall'));self.assertEqual((f.target/'custom.fxp').read_bytes(),b'custom-root');self.assertEqual((f.target/f.fx).read_bytes(),b'edited factory preset')
 def test_06_shutdown_rewrite(self):
  f=self.f({'rewrite_stop':True});self.ok(f.run());self.assertIn(b'saved-on-stop',f.settings.read_bytes());self.assertIn(b'saved-on-stop',(f.tx()/'settings.before').read_bytes());f.check_foreign()
 def test_07_concurrent_settings(self):
  f=self.f(hook={'baseline':'printf "\\n" >> "$SETTINGS"'});f.old_install();old=inventory(f.target);rc,out=f.run();self.assertNotEqual(rc,0,out);self.assertEqual(old,inventory(f.target));self.assertTrue(json.loads((f.r/'service.json').read_text())['active']);f.check_foreign()
 def interruption(self,action,old=True,sig=signal.SIGKILL,point='activated'):
  f=self.f(hook={point:'touch "$WORK/checkpoint"; while [ ! -e "$WORK/release" ];do sleep 1;done'});
  if old:f.old_install()
  before=inventory(f.target);p,log=f.run(action,background=True)
  end=time.time()+20
  while time.time()<end:
   cps=list((f.r/'work').rglob('checkpoint'))
   if cps:break
   time.sleep(.03)
  self.assertTrue(cps,log.read_text());p.send_signal(sig);p.wait(timeout=10);tx=f.tx();f.waitfor(tx/'rollback.done');self.assertEqual(before,inventory(f.target));f.check_foreign();f.clear_hooks();return f
 def test_08_interrupted_install(self):self.interruption('install',old=False)
 def test_09_interrupted_update(self):self.interruption('install')
 def test_10_interrupted_uninstall(self):self.interruption('uninstall')
 def test_11_watchdog_timeout(self):
  f=self.f({'timeout':True},hook={'baseline':'while :;do sleep 1;done'});f.old_install();before=inventory(f.target);rc,out=f.run();self.assertNotEqual(rc,0,out);f.waitfor(f.tx()/'rollback.done');self.assertEqual(before,inventory(f.target))
 def test_12_concurrent_rollback(self):
  f=self.f({'delay_stop':.3,'delay_start':.3});f.old_install();before=inventory(f.target);self.ok(f.run());tx=f.tx();ps=[]
  for _ in range(3):ps.append(subprocess.Popen(['sh',str(tx/'rollback.sh'),str(tx)],env=f.env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE))
  for p in ps:self.assertEqual(p.wait(timeout=60),0,p.stderr.read().decode())
  self.assertEqual(before,inventory(f.target));self.assertEqual(len((f.r/'rollback-owners').read_text().splitlines()),1)
 def test_13_stale_lock(self):
  f=self.interruption('install');self.ok(f.recover());self.ok(f.run());f.check_foreign()
 def test_14_insufficient_space(self):
  f=self.f({'free_kb':1});rc,out=f.run();self.assertNotEqual(rc,0);self.assertIn('insufficient',out);self.assertFalse((f.r/'events').exists())
 def test_15_readonly(self):
  f=self.f({'mount':'ro,exec'});self.assertNotEqual(f.run()[0],0);self.assertFalse((f.r/'events').exists())
 def test_16_missing_target_directory(self):
  f=self.f();(f.r/'Synths').rename(f.r/'Gone');self.assertNotEqual(f.run()[0],0)
 def test_17_invalid_checksum(self):
  f=self.f();(f.pkg/'INSTALL.md').write_text('broken');self.assertNotEqual(f.run()[0],0);self.assertFalse((f.r/'events').exists())
 def test_18_corrupt_zip(self):
  p=self.f().r/'broken.zip';p.write_bytes(b'PK garbage');self.assertRaises(zipfile.BadZipFile,zipfile.ZipFile,p)
 def test_19_symlink(self):
  f=self.f();f.old_install();(f.target/'linked').symlink_to(f.r/'MPC.settings');rc,out=f.run();self.assertNotEqual(rc,0);self.assertFalse((f.r/'events').exists())
 def test_20_foreign_plugins(self):
  f=self.f();self.ok(f.run());self.ok(f.run('uninstall'));f.check_foreign()
 def test_21_cycles_and_retention(self):
  f=self.f();f.old_install();self.ok(f.run());self.ok(f.run());self.ok(f.run());rc,out=f.run();self.assertNotEqual(rc,0);self.assertIn('three retained',out)
  txs=sorted((f.r/'recovery/ghost-community-v2').glob('tx-*'));p=subprocess.run(['sh',str(txs[0]/'cleanup.sh'),str(txs[0]),'--export',str(f.r/'exported'),'--confirm'],env=f.env,capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertTrue((f.r/'exported/transaction/backup/custom.fxp').exists());self.ok(f.run())
 def test_22_sigterm(self):self.interruption('install',sig=signal.SIGTERM)
 def test_23_delayed_systemctl(self):
  f=self.f({'delay_stop':.4,'delay_start':.4});self.ok(f.run());f.check_foreign()
 def test_24_storage_outside_content(self):
  f=self.f();self.ok(f.run());self.assertFalse((f.r/'Synths/.ghost-recovery').exists());self.assertFalse(any('stage' in str(p) or 'original' in str(p) for p in (f.r/'Synths').rglob('ghost.so')));self.assertFalse((f.tx().parent.parent/'work').exists())
 def test_25_idempotent_rollback(self):
  f=self.f();f.old_install();before=inventory(f.target);self.ok(f.run());tx=f.tx()
  for _ in range(2):
   r=subprocess.run(['sh',str(tx/'rollback.sh'),str(tx)],env=f.env,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
  self.assertEqual(before,inventory(f.target));self.assertEqual(len((f.r/'rollback-owners').read_text().splitlines()),1)
 def test_26_noexec(self):
  f=self.f({'mount':'rw,noexec'});self.assertNotEqual(f.run()[0],0);self.assertFalse((f.r/'events').exists())
 def test_27_arch_privilege_bypass(self):
  for c in [{'uid':501},{'arch':'aarch64'}]:
   f=self.f(c);self.assertNotEqual(f.run()[0],0);self.assertFalse((f.r/'events').exists())
  f=self.f();e=f.env.copy();e['MPC_INSTALL_TEST']='1';self.assertNotEqual(f.run(env=e)[0],0)
 def test_28_defer(self):
  f=self.f({'defer':True});self.ok(f.run(extra=['-n']));self.assertFalse((f.r/'events').exists());self.assertIn('DEFER=',(f.pkg/'install.sh').read_text())
 def test_29_recovery_discovery_collision(self):
  f=self.f();e=f.env.copy();e['GHOST_RECOVERY_ROOT']=str(f.r/'Synths');self.assertNotEqual(f.run(env=e)[0],0);self.assertFalse((f.r/'events').exists())
 def test_30_cross_filesystem(self):
  f=self.f({'crossfs':True});self.ok(f.run());f.check_foreign()
  f=self.f({'bad_workfs':True});self.assertNotEqual(f.run()[0],0)
 def test_31_active_lock(self):
  f=self.f(hook={'baseline':'touch "$WORK/checkpoint";while :;do sleep 1;done'});p,log=f.run(background=True)
  end=time.time()+20
  while time.time()<end and not list((f.r/'work').rglob('checkpoint')):time.sleep(.03)
  rc,out=f.run();self.assertNotEqual(rc,0);self.assertIn('active',out);p.send_signal(signal.SIGTERM);p.wait(timeout=30)
 def test_32_pid_reuse(self):
  f=self.f();self.ok(f.run());tx=f.tx();g=tx.parent/'active.lock';g.mkdir();(g/'transaction').write_text(str(tx));(g/'owner').write_text(f'{os.getpid()} 999999 boot-a\n');self.ok(f.recover());self.assertFalse(g.exists())
 def test_33_power_interruption(self):
  f=self.f(hook={'activated':'touch "$WORK/checkpoint";while :;do sleep 1;done'});f.old_install();old=inventory(f.target);p,log=f.run(background=True)
  end=time.time()+20
  while time.time()<end and not list((f.r/'work').rglob('checkpoint')):time.sleep(.03)
  tx=f.tx();self.assertTrue(list((f.r/'work').rglob('checkpoint')),log.read_text());os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=10)
  (f.r/'proc/sys/kernel/random/boot_id').write_text('boot-b');(f.r/'service.json').write_text(json.dumps(dict(active=True,pid=3333,restarts=0)))
  self.ok(f.recover());self.assertEqual(old,inventory(f.target));f.clear_hooks();self.ok(f.run())
 def test_34_unlisted_and_traversal(self):
  f=self.f();(f.pkg/'extra.sh').write_text('unexpected');self.assertNotEqual(f.run()[0],0)
  f=self.f();(f.pkg/'payload.sha256').write_text('a'*64+'  ../escape\n');sums(f.pkg);self.assertNotEqual(f.run()[0],0)
 def test_35_full_package(self):
  f=self.f(full=True);self.ok(f.run());f.check_foreign()
 def test_36_stage_failure(self):
  f=self.f(hook={'staged':'exit 71'});f.old_install();before=inventory(f.target);self.assertNotEqual(f.run()[0],0);self.assertEqual(before,inventory(f.target));self.assertFalse((f.r/'events').exists())
 def test_37_post_registration_pref_write(self):
  f=self.f(hook={'registered':'sed \'s/val="before"/val="external-pref"/\' "$SETTINGS" > "$TX/external";cat "$TX/external" > "$SETTINGS";exit 72'});f.old_install();old=inventory(f.target);self.assertNotEqual(f.run()[0],0);self.assertEqual(old,inventory(f.target));self.assertIn(b'external-pref',f.settings.read_bytes());f.check_foreign()
 def test_38_shutdown_registry_write(self):
  f=self.f(hook={'staged':'sed \'s/name="PD LAB"/name="FOREIGN CHANGE"/\' "$SETTINGS" > "$TX/external";cat "$TX/external" > "$SETTINGS"'});f.old_install();old=inventory(f.target);self.assertNotEqual(f.run()[0],0);self.assertEqual(old,inventory(f.target));self.assertIn(b'FOREIGN CHANGE',f.settings.read_bytes())
 def test_39_interrupted_rollback_owner(self):
  f=self.f();f.old_install();old=inventory(f.target);self.ok(f.run());tx=f.tx();l=tx/'rollback.lock';l.mkdir();(l/'owner').write_text('9999999 11 boot-a\n');r=subprocess.run(['sh',str(tx/'rollback.sh'),str(tx)],env=f.env,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(old,inventory(f.target))
 def test_40_actual_copy_error(self):
  f=self.f();f.old_install();old=inventory(f.target)
  p=f.r/'bin/cp';p.write_text('#!/bin/sh\ncase "$*" in */backup*) exit 44;;esac\nexec /bin/cp "$@"\n');p.chmod(0o755)
  self.assertNotEqual(f.run()[0],0);self.assertEqual(old,inventory(f.target));self.assertFalse((f.r/'events').exists())
 def test_41_newline_name(self):
  f=self.f();f.old_install();(f.target/'bad\nname').write_text('keep');old=inventory(f.target);self.assertNotEqual(f.run()[0],0);self.assertEqual(old,inventory(f.target))
 def test_42_recovery_owner(self):
  f=self.f({'root_owner':501});self.assertNotEqual(f.run()[0],0);self.assertFalse((f.r/'events').exists())
 def test_43_uninitialized_lock(self):
  f=self.f();base=f.r/'recovery/ghost-community-v2';base.mkdir();(base/'format').write_text('ghost-installer-2');(base/'active.lock').mkdir();self.assertNotEqual(f.run()[0],0);self.assertTrue((base/'active.lock').exists())
 def test_44_cleanup_newest_refused(self):
  f=self.f();self.ok(f.run());tx=f.tx();r=subprocess.run(['sh',str(tx/'cleanup.sh'),str(tx),'--export',str(f.r/'exported'),'--confirm'],env=f.env,capture_output=True,text=True);self.assertNotEqual(r.returncode,0);self.assertTrue(tx.exists())
 def test_45_int(self):self.interruption('install',sig=signal.SIGINT)
 def test_46_defer_failure(self):
  f=self.f({'defer':True},hook={'registered':'exit 73'});f.old_install();old=inventory(f.target);self.assertNotEqual(f.run(extra=['-n'])[0],0);self.assertEqual(old,inventory(f.target));self.assertFalse((f.r/'events').exists())
 def test_47_bad_xml(self):
  f=self.f();f.settings.write_text('<PROPERTIES><bad></PROPERTIES>');self.assertNotEqual(f.run()[0],0);self.assertFalse((f.r/'events').exists())
 def test_48_full_package_update_uninstall(self):
  f=self.f(full=True);f.old_install();self.ok(f.run());self.ok(f.run('uninstall'));self.assertEqual((f.target/'custom.fxp').read_bytes(),b'custom-root');self.assertEqual((f.target/f.fx).read_bytes(),b'edited factory preset');f.check_foreign()
 def test_49_timeout_slow_rollback(self):
  f=self.f({'timeout':True,'delay_stop':.25,'delay_start':.25,'rollback_hook':'sleep 20'},hook={'baseline':'while :;do sleep 1;done'});f.old_install();old=inventory(f.target);self.assertNotEqual(f.run()[0],0);f.waitfor(f.tx()/'rollback.done');self.assertEqual(old,inventory(f.target));self.assertEqual(len((f.r/'rollback-owners').read_text().splitlines()),1)
 def test_50_unknown_owner(self):
  f=self.f();self.ok(f.run());tx=f.tx();g=tx.parent/'active.lock';g.mkdir();(g/'transaction').write_text(str(tx));(g/'owner').write_text('corrupt-owner\n');self.assertNotEqual(f.recover()[0],0);self.assertTrue(g.exists())
 def test_51_killed_recovery_child(self):
  f=self.f({'rollback_hook':'touch "$TX/rb-check";while [ ! -e "$TX/rb-release" ];do sleep 1;done'});f.old_install();old=inventory(f.target);self.ok(f.run());tx=f.tx()
  p=subprocess.Popen(['sh',str(tx/'rollback.sh'),str(tx)],env=f.env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,start_new_session=True);f.ps.append(p);f.waitfor(tx/'rb-check');os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=10);(tx/'rb-release').touch()
  q=subprocess.run(['sh',str(tx/'rollback.sh'),str(tx)],env=f.env,capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stdout+q.stderr);self.assertEqual(old,inventory(f.target))
 def test_52_pid_stat_parser(self):
  text='987 (MPC name ) with spaces) S '+' '.join(str(i) for i in range(4,23))+'\n'
  r=subprocess.run(['sh','-c',"sed 's/.*) //' | awk 'NF>=20 {print $20}'"],input=text,capture_output=True,text=True);self.assertEqual(r.stdout.strip(),'22')
 def test_53_client_empty_and_xml_failure(self):
  for mode in ['empty','badxml']:
   f=self.f();candidate=f.r/'candidate.zip'
   with zipfile.ZipFile(candidate,'w') as z:
    prefix='GHOST-2.4.2/'
    for v in f.pkg.rglob('*'):
     if v.is_file():z.write(v,prefix+v.relative_to(f.pkg).as_posix())
   ssh=f.r/'bin/ssh';ssh.write_text('#!/bin/sh\ncase "$*" in *"if systemctl cat"*) echo acvs;; *"systemctl show"*) echo ActiveState=active;; *) '+('exit 0' if mode=='empty' else 'echo broken-xml')+';;esac\n');ssh.chmod(0o755)
   out=f.r/'preflight';r=subprocess.run([sys.executable,str(R/'tools/ghost_hardware_preflight.py'),'--host','root@offline-fixture','--out',str(out),'--synths','/Synths','--settings','/Settings','--recovery','/Recovery','--work','/Work','--candidate',str(candidate)],env=f.env,capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0);report=json.loads((out/'PREFLIGHT.json').read_text());self.assertIn('EMPTY SSH OUTPUT' if mode=='empty' else 'NONEMPTY SETTINGS RECEIVED BUT INVALID XML',report['error'])
 def test_54_concurrent_discovery_root(self):
  f=self.f(hook={'baseline':'sed "s|</SynthContentLocations>|<Location>$WORK</Location></SynthContentLocations>|" "$SETTINGS" > "$TX/external";cat "$TX/external" > "$SETTINGS"'});f.old_install();old=inventory(f.target);rc,out=f.run();self.assertNotEqual(rc,0);self.assertEqual(old,inventory(f.target));self.assertIn('recovery/work',out);self.assertFalse(json.loads((f.r/'service.json').read_text())['active']);self.assertTrue((f.tx().parent/'active.lock').exists())
 def signal_during_service_start(self,sig):
  f=self.f({'delay_start':.7});f.old_install();old=inventory(f.target);p,log=f.run(background=True);end=time.time()+20
  while time.time()<end:
   text=(f.r/'events').read_text() if (f.r/'events').exists() else ''
   if 'start begin' in text:break
   time.sleep(.01)
  self.assertIn('start begin',text,log.read_text());first=[l.split()[-1] for l in text.splitlines() if l.startswith('start begin')][0]
  p.send_signal(sig);p.wait(timeout=20);tx=f.tx();f.waitfor(tx/'rollback.done');self.assertEqual(old,inventory(f.target));events=(f.r/'events').read_text();self.assertNotIn('start end '+first,events);self.assertTrue(json.loads((f.r/'service.json').read_text())['active'])
 def test_55_term_during_systemctl(self):self.signal_during_service_start(signal.SIGTERM)
 def test_56_kill_orphaned_systemctl(self):self.signal_during_service_start(signal.SIGKILL)
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
 if len(sys.argv)>1:suite=unittest.TestSuite(t for t in suite if any(s in t.id() for s in sys.argv[1:]))
 result=unittest.TextTestRunner(verbosity=2).run(suite);(OUT/'RESULTS.json').write_text(json.dumps({'tests':result.testsRun,'failures':[(str(t),m) for t,m in result.failures],'errors':[(str(t),m) for t,m in result.errors],'hardware_test':False},indent=2)+'\n');sys.exit(not result.wasSuccessful())
