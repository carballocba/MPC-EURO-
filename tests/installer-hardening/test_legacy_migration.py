#!/usr/bin/env python3
"""Full sanitized real366 predecessor, all52 FXP; mocks only service/process/platform."""
import unittest,importlib.util,pathlib,shutil,json,hashlib,subprocess,os,signal
HERE=pathlib.Path(__file__).resolve().parent;R=HERE.parents[1];FIX=HERE/'fixtures/desktop-242'
spec=importlib.util.spec_from_file_location('harness',HERE/'run.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
class Legacy(unittest.TestCase):
 def setUp(self):self.fs=[]
 def tearDown(self):
  for f in self.fs:f.close()
 def legacy(self,**kw):
  f=h.Fixture(full=True,**kw);self.fs.append(f);shutil.copytree(f.old,f.target)
  (f.target/'plugin-meta.xml').write_bytes((FIX/'plugin-meta.xml.in').read_bytes().replace(b'%payload-path%',str(f.r/'Synths').encode()))
  (f.target/'mpc-plugin.json').write_bytes((FIX/'mpc-plugin.json').read_bytes())
  # Use the shipped known legacy manifest, not a freshly blessed target manifest.
  shutil.copyfile(R/'package-template/legacy-owned.sha256',f.pkg/'legacy-owned.sha256');h.sums(f.pkg)
  for row in json.loads((FIX/'layout.json').read_text())['files']:(f.target/row['path']).chmod(row['mode'])
  self.assertEqual(len(h.inventory(f.target)),366)
  entry=(f.target/'plugin-meta.xml').read_text().strip()
  foreign=''.join(f'<PLUGIN name="Foreign{i}" uid="{i+1000:08x}" file="/unrelated/plugin-{i}.so"/>\n' for i in range(80))
  f.settings.write_text(f.settings.read_text().replace('</KNOWNPLUGINS>',foreign+entry+'\n</KNOWNPLUGINS>').replace('</SynthContentLocations>','<Location>/media/ANON&#61480;/Synths</Location></SynthContentLocations>'))
  return f
 def ok(self,r):self.assertEqual(r[0],0,r[1])
 def presets(self,f):return {k:v for k,v in h.inventory(f.target).items() if k.lower().endswith('.fxp')}
 def rollback(self,f,tx):return subprocess.run(['sh',str(tx/'rollback.sh'),str(tx)],env=f.env,capture_output=True,text=True,timeout=100)
 def test_complete_real_predecessor_install_update_reinstall_uninstall_restore(self):
  f=self.legacy();old=h.inventory(f.target);pres=self.presets(f);self.assertEqual(len(pres),52)
  (f.target/'custom-outside-user-data.txt').write_bytes(b'user content');(f.target/f.fx).write_bytes(b'edited preset');old=h.inventory(f.target);pres=self.presets(f)
  self.ok(f.run());first=f.tx();after=h.inventory(f.target);self.assertEqual(pres,self.presets(f));f.check_foreign()
  self.ok(f.run());self.assertEqual(after,h.inventory(f.target));self.ok(f.run());self.assertEqual(after,h.inventory(f.target))
  # Retention is intentionally bounded: separate fixture for uninstall checkpoint.
  g=self.legacy();(g.target/'custom-outside-user-data.txt').write_bytes(b'user content');before=h.inventory(g.target);p=self.presets(g)
  self.ok(g.run());one=g.tx();self.ok(g.run('uninstall'));three=g.tx();self.assertEqual(p,self.presets(g));self.assertFalse((g.target/'ghost.so').exists());self.assertEqual((g.target/'custom-outside-user-data.txt').read_bytes(),b'user content');g.check_foreign()
  self.assertEqual(self.rollback(g,three).returncode,0);self.assertEqual(self.rollback(g,one).returncode,0);self.assertEqual(before,h.inventory(g.target));self.assertEqual(self.rollback(g,one).returncode,0)
 def test_direct_legacy_uninstall_preserves_all52(self):
  f=self.legacy();pres=self.presets(f);old=h.inventory(f.target);self.ok(f.run('uninstall'));self.assertEqual(pres,self.presets(f));self.assertFalse((f.target/'ghost.so').exists());tx=f.tx();r=self.rollback(f,tx);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(old,h.inventory(f.target))
 def test_modified_runtime_refuses_before_host_stop(self):
  for name in ['ghost.so','Plugin Skins/TUI.json','plugin-meta.xml','mpc-plugin.json']:
   f=self.legacy();(f.target/name).write_bytes(b'unknown edited runtime');before=h.inventory(f.target);self.assertNotEqual(f.run()[0],0,name);self.assertEqual(before,h.inventory(f.target));self.assertFalse((f.r/'events').exists())
 def test_fake_ownership_cannot_delete_unknown(self):
  f=self.legacy();(f.target/'custom.txt').write_bytes(b'user');manifest=(f.pkg/'payload.sha256').read_text()+hashlib.sha256(b'user').hexdigest()+'  custom.txt\n';(f.target/'.ghost-owned.sha256').write_text(manifest);before=h.inventory(f.target);self.assertNotEqual(f.run()[0],0);self.assertEqual(before,h.inventory(f.target))
 def test_directory_collisions(self):
  f=self.legacy();p=f.target/f.fx;p.unlink();p.mkdir();before=h.inventory(f.target);self.assertNotEqual(f.run()[0],0);self.assertEqual(before,h.inventory(f.target));self.assertFalse((f.r/'events').exists())
 def test_unknown_metadata_fields_not_blessed(self):
  f=self.legacy();p=f.target/'mpc-plugin.json';j=json.loads(p.read_text());j['uid']='deadbeef';p.write_text(json.dumps(j));before=h.inventory(f.target);self.assertNotEqual(f.run()[0],0);self.assertEqual(before,h.inventory(f.target))
 def test_path_expansion_requires_exact_destination(self):
  f=self.legacy();p=f.target/'plugin-meta.xml';p.write_text(p.read_text().replace(str(f.r/'Synths'),'/other/Synths'));self.assertNotEqual(f.run()[0],0);self.assertFalse((f.r/'events').exists())
 def test_registration_failure_recovers_real_predecessor(self):
  f=self.legacy(hook={'registered':'false'});before=h.inventory(f.target);settings=f.settings.read_bytes();self.assertNotEqual(f.run()[0],0);self.assertEqual(before,h.inventory(f.target));self.assertEqual(settings,f.settings.read_bytes());self.assertTrue(json.loads((f.r/'service.json').read_text())['active'])
 def test_copy_failure_preserves_real_predecessor(self):
  f=self.legacy(hook={'staged':'false'});before=h.inventory(f.target);self.assertNotEqual(f.run()[0],0);self.assertEqual(before,h.inventory(f.target));self.assertFalse((f.r/'events').exists())
 def interrupted(self,action,point):
  f=self.legacy(hook={point:'touch "$WORK/checkpoint";while [ ! -e "$WORK/release" ];do sleep 1;done'});before=h.inventory(f.target);p,log=f.run(action,background=True)
  end=__import__('time').time()+40
  while __import__('time').time()<end:
   txs=list((f.r/'recovery/ghost-community-v2').glob('tx-*'))
   if txs:
    tx=txs[-1];w=pathlib.Path((tx/'work').read_text().strip()) if (tx/'work').exists() else None
    if w and (w/'checkpoint').exists():break
   __import__('time').sleep(.02)
  else:self.fail(log.read_text())
  p.send_signal(signal.SIGKILL);p.wait(timeout=10);f.waitfor(tx/'rollback.done');self.assertEqual(before,h.inventory(f.target));f.check_foreign()
 def test_interrupted_install(self):self.interrupted('install','activated')
 def test_interrupted_uninstall(self):self.interrupted('uninstall','activated')
 def test_interrupted_update(self):
  f=self.legacy();self.ok(f.run());before=h.inventory(f.target)
  p=f.pkg/'transaction.sh';p.write_text(p.read_text().replace('# @HOOK activated','false'));h.sums(f.pkg);self.assertNotEqual(f.run()[0],0);self.assertEqual(before,h.inventory(f.target))
 def test_slow_service_shutdown_rewrite(self):
  f=self.legacy(control={'rewrite_stop':True,'delay_stop':.2,'delay_start':.2});self.ok(f.run());self.assertIn('saved-on-stop',f.settings.read_text());self.assertEqual(len(self.presets(f)),52)
 def test_three_slot_sequence_requires_retention_checkpoint(self):
  f=self.legacy(hook={'staged':'false'});self.assertNotEqual(f.run()[0],0);f.clear_hooks();self.ok(f.run());self.ok(f.run());before=h.inventory(f.target);self.assertNotEqual(f.run('uninstall')[0],0);self.assertEqual(before,h.inventory(f.target))
 def test_export_aborted_packet_allows_complete_three_operation_sequence(self):
  f=self.legacy(hook={'staged':'false'});initial=h.inventory(f.target);self.assertNotEqual(f.run()[0],0);aborted=f.tx();f.clear_hooks()
  self.ok(f.run());first=f.tx();export=f.r/'export-aborted'
  r=subprocess.run(['sh',str(aborted/'cleanup.sh'),str(aborted),'--export',str(export),'--confirm'],env=f.env,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertTrue((export/'transaction/backup').is_dir());self.assertFalse(aborted.exists())
  self.ok(f.run());self.ok(f.run('uninstall'));last=f.tx();self.assertEqual(len(self.presets(f)),52);self.assertEqual(self.rollback(f,last).returncode,0);self.assertEqual(self.rollback(f,first).returncode,0);self.assertEqual(initial,h.inventory(f.target))
 def test_uninstall_then_reinstall_preserves_retained_presets(self):
  f=self.legacy();pres=self.presets(f);self.ok(f.run());self.ok(f.run('uninstall'));self.ok(f.run());self.assertEqual(pres,self.presets(f));self.assertTrue((f.target/'ghost.so').is_file());f.check_foreign()
 def test_duplicate_uid_other_path_refuses_before_transaction(self):
  f=self.legacy();f.settings.write_text(f.settings.read_text().replace('</KNOWNPLUGINS>','<PLUGIN name="Other" uid="47485354" file="/unrelated/other.so"/></KNOWNPLUGINS>'));old=h.inventory(f.target);self.assertNotEqual(f.run()[0],0);self.assertEqual(old,h.inventory(f.target));self.assertFalse((f.r/'events').exists())
 def test_foreign_entry_inside_target_refuses_before_transaction(self):
  f=self.legacy();f.settings.write_text(f.settings.read_text().replace('</KNOWNPLUGINS>',f'<PLUGIN name="Other" uid="abcdef01" file="{f.target}/other.so"/></KNOWNPLUGINS>'));old=h.inventory(f.target);self.assertNotEqual(f.run()[0],0);self.assertEqual(old,h.inventory(f.target));self.assertFalse((f.r/'events').exists())
if __name__=='__main__':unittest.main(verbosity=2)
