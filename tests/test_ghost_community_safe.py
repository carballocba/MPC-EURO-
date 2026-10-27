"""Real package, real POSIX backend, synthetic XML and fake service. Never SSH."""
import sys,pathlib,os,tempfile,shutil,subprocess,time,unittest,importlib.util,json,zipfile,hashlib,xml.etree.ElementTree as E
R=pathlib.Path(__file__).resolve().parents[1];S=R/'community/ghost'
PACKAGED=os.environ.get('GHOST_SAFE_TEST_PACKAGE')
if PACKAGED:
 PACKAGE_ROOT=tempfile.TemporaryDirectory(prefix='ghost-safe-package-')
 with zipfile.ZipFile(PACKAGED) as z:z.extractall(PACKAGE_ROOT.name)
 S=pathlib.Path(PACKAGE_ROOT.name)/'GHOST-2.4.2'
spec=importlib.util.spec_from_file_location('community_manage',S/'manage.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ZIP=R/'build/ghost-both-fix/ghost-random-repeat-both-fix-armv7-TRIAL.zip'
def real_payload():
 if PACKAGED:return {str(p.relative_to(S/'portable'/m.FOLDER)):p.read_bytes() for p in (S/'portable'/m.FOLDER).rglob('*') if p.is_file()}
 if ZIP.exists():
  with zipfile.ZipFile(ZIP) as z:return {n.split('/',1)[1]:z.read(n) for n in z.namelist()}
 data={str(p.relative_to(R/'resources')):p.read_bytes() for p in (R/'resources').rglob('*') if p.is_file()};data['ghost.so']=(R/'rebuild/ghost.so').read_bytes();return data
class SafeTransaction(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='ghost-safe-');self.r=pathlib.Path(self.temp.name);self.synths=self.r/'Synths with spaces';self.synths.mkdir();self.target=self.synths/m.FOLDER;self.settings=self.r/'MPC.settings';self.service=self.r/'service';self.service.write_text('active');self.calls=self.r/'calls';self.calls.write_text('');self.tools=self.r/'bin';self.tools.mkdir();self.tx=self.synths/'.ghost-recovery/tx-fixture';self.new=real_payload();self.old=dict(self.new);self.old['ghost.so']=b'previous GHOST with same identity';self._build_settings(True)
  for t in ('sh','sed','find','wc','cp','mv','mkdir','rmdir','rm','kill','nohup','env','cat','awk','chmod','id','uname'):(self.tools/t).symlink_to(shutil.which(t))
  (self.tools/'sleep').write_text('#!/bin/sh\n[ "$1" != 0 ] || exit 0\nexec /bin/sleep "$1"\n');(self.tools/'sleep').chmod(0o755)
  (self.tools/'sync').write_text('#!/bin/sh\nexit 0\n');(self.tools/'sync').chmod(0o755)
  (self.tools/'systemctl').write_text('''#!/bin/sh
[ "$1" != --no-block ] || shift
case "$1" in
 show) case "$*" in
 *ActiveState*) printf 'ActiveState=';cat "$FAKE_STATE";;
 *SubState*) [ "$(cat "$FAKE_STATE")" != active ] || echo SubState=running;;
 *MainPID*) if [ "$(cat "$FAKE_STATE")" = active ];then echo MainPID=335;else echo MainPID=0;fi;;
 *NRestarts*) echo NRestarts=0;;esac;;
 stop|start) echo "$1" >> "$FAKE_CALLS"
 if [ -f "$FAIL_SERVICE_ONCE" ];then rm "$FAIL_SERVICE_ONCE";exit 8;fi
 if [ "$1" = stop ];then echo inactive > "$FAKE_STATE";else echo active > "$FAKE_STATE";fi;;
 *) exit 9;;esac
''');(self.tools/'systemctl').chmod(0o755)
  (self.tools/'sha256sum').write_text('#!'+sys.executable+'''\nimport pathlib,sys,hashlib
if sys.argv[1]=='-c':
 ok=True
 for line in pathlib.Path(sys.argv[2]).read_text().splitlines():
  h,n=line.split('  ',1);p=pathlib.Path(n);ok=ok and p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==h
 sys.exit(0 if ok else 1)
for n in sys.argv[1:]:print(hashlib.sha256(pathlib.Path(n).read_bytes()).hexdigest()+'  '+n)
''');(self.tools/'sha256sum').chmod(0o755)
  self.foreign=self.synths/'PD LAB and MPC-CORE';self.foreign.mkdir();(self.foreign/'pd.so').write_bytes(b'PD LAB');(self.foreign/'core.so').write_bytes(b'MPC CORE');self.protected=''.join(m.sha(p.read_bytes())+'  '+str(p)+'\n' for p in sorted(self.foreign.iterdir())).encode()
  self.env=dict(os.environ,PATH=str(self.tools),FAKE_STATE=str(self.service),FAKE_CALLS=str(self.calls),FAIL_SERVICE_ONCE=str(self.r/'service-fail-once'),GHOST_FIXTURE='1',TX=str(self.tx))
 def _build_settings(self,installed):
  target=str(self.target)+'/ghost.so';entry=E.fromstring(self.new['plugin-meta.xml']);entry.set('file',target);token=E.tostring(entry).decode()
  self.raw=('<PROPERTIES>\n<VALUE name="Hardware.EthernetIPv4DNS" val="current-DNS"/>\n<VALUE name="pluginList-arm">\n<KNOWNPLUGINS>\n'+''.join('<PLUGIN name="%s" uid="%08x" file="/other/%d.so"/>\n'%('PD LAB' if i==0 else 'MPC-CORE' if i==1 else 'Other'+str(i),i+1,i) for i in range(80))+(token+'\n' if installed else '')+'</KNOWNPLUGINS>\n</VALUE>\n<VALUE name="RecentProject" val="keep current"/>\n</PROPERTIES>\n').encode();self.settings.write_bytes(self.raw)
 def plan(self,op='install',clean=False,guard=120):
  if clean:self._build_settings(False);old={}
  else:old=self.old
  if old:
   self.target.mkdir()
   for n,b in old.items():p=self.target/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  conf=m.make_plan(self.tx,self.raw,self.new['plugin-meta.xml'],old,self.new,op,str(self.synths),str(self.settings),'acvs','335','0',self.protected,observe=0,guard=guard)
  # Test fixture only: accelerate watchdog grace without changing production defaults.
  p=self.tx/'plan.conf';p.write_text(p.read_text().replace('GUARD_GRACE=5','GUARD_GRACE=1'));return conf
 def run_tx(self,action='run',fault=''):
  return subprocess.run(['/bin/sh',str(S/'transaction.sh')],env=dict(self.env,ACTION=action,GHOST_FAIL_AT=fault),capture_output=True,text=True,timeout=40)
 def assert_old(self,clean=False):
  self.assertEqual(self.service.read_text().strip(),'active')
  self.assertEqual(self.settings.read_bytes(),self.raw)
  if clean:self.assertFalse(self.target.exists())
  else:self.assertEqual({str(p.relative_to(self.target)):p.read_bytes() for p in self.target.rglob('*') if p.is_file()},self.old)
  self.assertEqual((self.foreign/'pd.so').read_bytes(),b'PD LAB');self.assertEqual((self.foreign/'core.so').read_bytes(),b'MPC CORE')
 def wait_guard(self):
  for _ in range(150):
   if (self.tx/'done').exists() and not (self.synths/'.ghost-community-lock').exists():return
   time.sleep(.1)
  self.fail('Guardian did not complete: '+str(list(self.tx.iterdir())))
 def tearDown(self):
  # A detached guardian must see done before the temporary fixture disappears.
  if self.tx.exists():(self.tx/'done').touch()
  time.sleep(.05);self.temp.cleanup()
 def test_update_preserves_settings_bytes_and_rollback_twice(self):
  self.plan();stamp=self.settings.stat().st_mtime_ns;ino=self.settings.stat().st_ino;p=self.run_tx();self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(self.settings.read_bytes(),self.raw);self.assertEqual(self.settings.stat().st_ino,ino);self.assertEqual(self.settings.stat().st_mtime_ns,stamp)
  for _ in range(2):p=self.run_tx('rollback');self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assert_old()
 def test_clean_install_and_exact_rollback(self):
  self.plan(clean=True);p=self.run_tx();self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(len(m.xml(self.settings.read_bytes())[1]),81);p=self.run_tx('rollback');self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assert_old(clean=True)
 def test_uninstall_then_rollback(self):
  self.plan('uninstall');p=self.run_tx();self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(self.target.exists());self.assertEqual(len(m.xml(self.settings.read_bytes())[1]),80);p=self.run_tx('rollback');self.assertEqual(p.returncode,0,p.stderr);self.assert_old()
 def test_all_stages_restore(self):
  for point in ('after-stop','after-old-moved','after-activation','after-registry','after-start'):
   with self.subTest(point=point):
    # Each failure uses its own independent fixture/session.
    t=SafeTransaction();t.setUp()
    try:t.plan();p=t.run_tx(fault=point);self.assertNotEqual(p.returncode,0);t.assert_old()
    finally:t.tearDown()
 def test_clean_registry_failure_restores_absence(self):
  self.plan(clean=True);p=self.run_tx(fault='after-registry');self.assertNotEqual(p.returncode,0);self.assert_old(clean=True)
 def test_sigkill_independent_watchdog(self):
  self.plan();p=self.run_tx(fault='kill-after-registry');self.assertNotEqual(p.returncode,0);self.wait_guard();self.assert_old();self.assertTrue((self.tx/'watchdog-recovery.log').exists())
 def test_hung_worker_deadline_recovers(self):
  self.plan(guard=2);p=self.run_tx(fault='hang-after-activation');self.assertNotEqual(p.returncode,0);self.wait_guard();self.assert_old()
 def test_failed_host_start_recovers(self):
  self.plan();ctl=self.tools/'systemctl';s=ctl.read_text().replace('stop|start) echo', 'stop|start) if [ "$1" = start ] && [ ! -f "$FAKE_STATE.once" ];then : > "$FAKE_STATE.once";exit 8;fi; echo');ctl.write_text(s);p=self.run_tx();self.assertNotEqual(p.returncode,0);self.assert_old()
 def test_preflight_change_never_stops(self):
  self.plan();changed=self.raw.replace(b'current-DNS',b'changed-DNS');self.settings.write_bytes(changed);p=self.run_tx();self.assertNotEqual(p.returncode,0);self.assertEqual(self.calls.read_text(),'');self.assertEqual(self.settings.read_bytes(),changed)
 def test_other_plugin_change_never_stops(self):
  self.plan();(self.foreign/'pd.so').write_bytes(b'new PD LAB');p=self.run_tx();self.assertNotEqual(p.returncode,0);self.assertEqual(self.calls.read_text(),'');self.assertEqual((self.foreign/'pd.so').read_bytes(),b'new PD LAB')
 def test_candidate_corruption_never_stops(self):
  self.plan();(self.tx/'candidate/ghost.so').write_bytes(b'bad');p=self.run_tx();self.assertNotEqual(p.returncode,0);self.assertEqual(self.calls.read_text(),'');self.assert_old()
 def test_concurrent_preferences_survive_rollback(self):
  self.plan(clean=True);p=self.run_tx();self.assertEqual(p.returncode,0,p.stderr);self.settings.write_bytes(self.settings.read_bytes().replace(b'current-DNS',b'new-DNS'));p=self.run_tx('rollback');self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertEqual(self.settings.read_bytes(),self.raw.replace(b'current-DNS',b'new-DNS'));self.assertFalse(self.target.exists())
 def test_uninstall_concurrent_preferences_survive_rollback(self):
  self.plan('uninstall');self.assertEqual(self.run_tx().returncode,0);self.settings.write_bytes(self.settings.read_bytes().replace(b'current-DNS',b'new-DNS'));p=self.run_tx('rollback');self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertIn(b'new-DNS',self.settings.read_bytes());self.assertEqual(len(m.xml(self.settings.read_bytes())[1]),81)
 def test_lock_refuses(self):
  self.plan();(self.synths/'.ghost-community-lock').mkdir();p=self.run_tx();self.assertNotEqual(p.returncode,0);self.assertEqual(self.calls.read_text(),'');self.assert_old()
 def test_missing_tool_refuses_without_service_changes(self):
  self.plan();(self.tools/'nohup').unlink();p=self.run_tx();self.assertNotEqual(p.returncode,0);self.assertEqual(self.calls.read_text(),'');self.assert_old()
 def test_partial_backup_copy_never_stops_host(self):
  self.plan();p=self.tools/'cp';p.unlink();p.write_text('#!/bin/sh\nexit 8\n');p.chmod(0o755);result=self.run_tx();self.assertNotEqual(result.returncode,0);self.assertEqual(self.calls.read_text(),'');self.assert_old()
 def test_all_uninstall_stages_restore(self):
  for point in ('after-stop','after-old-moved','after-activation','after-registry','after-start'):
   with self.subTest(point=point):
    t=SafeTransaction();t.setUp()
    try:t.plan('uninstall');p=t.run_tx(fault=point);self.assertNotEqual(p.returncode,0);t.assert_old()
    finally:t.tearDown()
 def test_settings_permissions_preserved(self):
  self.settings.chmod(0o640);self.plan('uninstall');p=self.run_tx();self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(self.settings.stat().st_mode&0o777,0o640);self.assertEqual(self.run_tx('rollback').returncode,0);self.assertEqual(self.settings.stat().st_mode&0o777,0o640);self.assert_old()
 def test_pre_registry_concurrent_pref_on_clean_failure(self):
  self.plan(clean=True);ctl=self.tools/'systemctl';text=ctl.read_text().replace('stop|start) echo', 'stop|start) if [ "$1" = stop ] && [ ! -f "$FAKE_STATE.pref" ];then sed \'s/current-DNS/new-DNS/\' "$PREF_SETTINGS" > "$PREF_SETTINGS.next";mv "$PREF_SETTINGS.next" "$PREF_SETTINGS"; : > "$FAKE_STATE.pref";fi; echo');ctl.write_text(text);self.env['PREF_SETTINGS']=str(self.settings);p=self.run_tx(fault='after-stop');self.assertNotEqual(p.returncode,0);self.assertEqual(self.settings.read_bytes(),self.raw.replace(b'current-DNS',b'new-DNS'));self.assertFalse(self.target.exists());self.assertEqual(self.service.read_text().strip(),'active')
 def test_bad_prior_directory_falls_back_to_verified_backup(self):
  self.plan();self.assertEqual(self.run_tx().returncode,0);(self.tx/'prior-active/ghost.so').write_bytes(b'corrupt prior');p=self.run_tx('rollback');self.assertEqual(p.returncode,0,p.stderr);self.assert_old()
 def test_bad_backup_uses_verified_original_directory(self):
  self.plan();self.assertEqual(self.run_tx().returncode,0);(self.tx/'backup/ghost.so').write_bytes(b'corrupt backup');p=self.run_tx('rollback');self.assertEqual(p.returncode,0,p.stderr);self.assert_old()
class Planning(unittest.TestCase):
 def test_empty_invalid_xml_distinguished(self):
  for raw,msg in [(b'','TRANSPORT'),(b'<bad>\n','INVALID XML')]:
   with self.assertRaisesRegex(ValueError,msg):m.xml(raw)
 def test_minified_registry_and_unrelated_preferences(self):
  raw=b'<PROPERTIES><VALUE name="DNS" val="keep"/><VALUE name="pluginList-arm"><KNOWNPLUGINS></KNOWNPLUGINS></VALUE></PROPERTIES>\n';entry=real_payload()['plugin-meta.xml'];after,old,new=m.registry_plan(raw,entry,'install','/tmp/Synths/'+m.FOLDER);self.assertEqual(old,b'');self.assertEqual(len(m.xml(after)[1]),1);self.assertIn(b'val="keep"',after)
 def test_uid_collision_refuses(self):
  raw=b'<PROPERTIES><KNOWNPLUGINS><PLUGIN uid="47485354" file="/wrong/ghost.so"/></KNOWNPLUGINS></PROPERTIES>\n'
  with self.assertRaisesRegex(ValueError,'migration'):m.registry_plan(raw,real_payload()['plugin-meta.xml'],'install','/tmp/Synths/'+m.FOLDER)

class UserData(unittest.TestCase):
 def test_user_preset_edits_and_extra_files_preserved(self):
  new={'ghost.so':b'new','Preset Library/Factory.fxp':b'factory'};old={'ghost.so':b'old','Preset Library/Factory.fxp':b'user-edit','My Presets/One.fxp':b'custom','User notes.txt':b'keep','manifest.json':b'old-record'}
  result=m.preserve_user_files(new,old);self.assertEqual(result['ghost.so'],b'new');self.assertEqual(result['Preset Library/Factory.fxp'],b'user-edit');self.assertEqual(result['My Presets/One.fxp'],b'custom');self.assertEqual(result['User notes.txt'],b'keep');self.assertNotIn('manifest.json',result)
 def test_foreign_plugin_inside_target_refuses(self):
  target='/tmp/Synths/'+m.FOLDER;raw=('<PROPERTIES><KNOWNPLUGINS><PLUGIN uid="1234" file="'+target+'/foreign.so"/></KNOWNPLUGINS></PROPERTIES>\n').encode()
  with self.assertRaisesRegex(ValueError,'Another registered'):m.registry_plan(raw,real_payload()['plugin-meta.xml'],'install',target)

class PackageIntegrity(unittest.TestCase):
 @unittest.skipUnless(PACKAGED,'Final ZIP validation only')
 def test_whole_package_checksums_and_approved_abi(self):
  data=m.payload();self.assertEqual(m.sha(data['ghost.so']),m.BINARY)
 @unittest.skipUnless(PACKAGED,'Final ZIP validation only')
 def test_unchanged_gui_qlinks_presets_and_audio(self):
  actual=real_payload()
  if ZIP.exists():
   with zipfile.ZipFile(ZIP) as z:baseline={n.split('/',1)[1]:z.read(n) for n in z.namelist()}
  else:
   baseline={str(p.relative_to(R/'resources')):p.read_bytes() for p in (R/'resources').rglob('*') if p.is_file()};baseline['ghost.so']=(R/'rebuild/ghost.so').read_bytes()
  protected=[n for n in baseline if n=='ghost.so' or n.startswith('Plugin Skins/') or n.endswith('.fxp') or n=='version.xml']
  self.assertTrue(all(actual[n]==baseline[n] for n in protected));self.assertEqual(sum(n.endswith('.fxp') for n in actual),52)
