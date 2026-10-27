"""Offline tests of the exact upstream-generated community scripts; no SSH/device code."""
import pathlib,os,subprocess,shutil,tempfile,unittest,zipfile,xml.etree.ElementTree as ET,hashlib
R=pathlib.Path(__file__).resolve().parents[1];O=R/'build/ghost-community-beta';ZIP=O/'dist/GHOST-2.4.2-mpc-armv7.zip';F='MPC-EURO - VST - GHOST';UID='47485354'
def sem(n):return n.tag,sorted(n.attrib.items()),(n.text or '').strip(),[sem(c) for c in n]
def files(p):return {str(x.relative_to(p)):x.read_bytes() for x in p.rglob('*') if x.is_file()}
class Community(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='ghost-community-test-');self.root=pathlib.Path(self.temp.name)
  with zipfile.ZipFile(ZIP) as z:z.extractall(self.root)
  self.pkg=self.root/'GHOST-2.4.2';self.synths=self.root/'Synths with spaces';self.synths.mkdir();self.target=self.synths/F;self.settings=self.root/'MPC.settings';self.log=self.root/'service.log';self.tools=self.root/'bin';self.tools.mkdir()
  self.settings.write_text('<PROPERTIES><VALUE name="Hardware.EthernetIPv4DNS" val="keep"/><VALUE name="AudioRecorder.input" val="current"/><VALUE name="pluginList-arm"><KNOWNPLUGINS>\n'+''.join('<PLUGIN name="Foreign%d" uid="%08x" file="/foreign/%d.so"/>\n'%(i,i+1,i) for i in range(80))+'</KNOWNPLUGINS></VALUE></PROPERTIES>\n')
  self.before=self.settings.read_bytes();self.foreign=self.synths/'Foreign plug';self.foreign.mkdir();(self.foreign/'foreign.so').write_bytes(b'PD LAB/MPC-CORE and all other plugins are untouchable')
  for tool in ('awk','grep','sed','head','cp','mv','rm','mkdir','ls','date','dirname','df','cat','id','uname'):
   p=shutil.which(tool);self.assertTrue(p,tool);(self.tools/tool).symlink_to(p)
  # A local SHA utility stand-in because macOS lacks sha256sum. Shell templates remain unchanged.
  (self.tools/'sha256sum').write_text('#!'+str(R/'build/venv/bin/python')+'\nimport sys,pathlib,hashlib\nok=True\nfor line in pathlib.Path(sys.argv[-1]).read_text().splitlines():\n h,n=line.split("  ",1);p=pathlib.Path(n);good=p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==h;ok=ok and good\nsys.exit(0 if ok else 1)\n');(self.tools/'sha256sum').chmod(0o755)
  (self.tools/'sync').write_text('#!/bin/sh\nexit 0\n');(self.tools/'sync').chmod(0o755)
  self.env=dict(os.environ,PATH=str(self.tools),MPC_INSTALL_TEST='1',MPC_TEST_LOG=str(self.log),MPC_SETTINGS=str(self.settings),MPC_LEGACY_ROOT=str(self.root/'legacy'))
 def tearDown(self):self.temp.cleanup()
 def run_script(self,name='install.sh'):
  return subprocess.run(['/bin/sh',str(self.pkg/name),'-y','-t',str(self.synths)],env=self.env,capture_output=True,text=True,timeout=30)
 def check_foreign(self):
  a=ET.fromstring(self.before);b=ET.fromstring(self.settings.read_bytes());ar=a.find('.//KNOWNPLUGINS');br=b.find('.//KNOWNPLUGINS')
  for n in list(br):
   if n.get('uid')==UID:br.remove(n)
  self.assertEqual(sem(a),sem(b));self.assertEqual((self.foreign/'foreign.so').read_bytes(),b'PD LAB/MPC-CORE and all other plugins are untouchable')
 def test_clean_install_no_remote_python_base64_timeout(self):
  for t in ('python3','base64','timeout'):self.assertFalse((self.tools/t).exists())
  p=self.run_script();self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.check_foreign();self.assertEqual(len(ET.fromstring(self.settings.read_bytes()).findall('.//PLUGIN')),81);self.assertEqual(self.log.read_text().splitlines(),['stop','start'])
 def test_update_preserves_uid_and_unrelated_settings(self):
  self.assertEqual(self.run_script().returncode,0);(self.target/'ghost.so').write_bytes(b'old revision');p=self.run_script();self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertEqual(hashlib.sha256((self.target/'ghost.so').read_bytes()).hexdigest(),'588019130b31ced7077f7e4afe35bd23b0753df7a2959e2af39fa825e1b81afd');self.check_foreign();self.assertEqual(len([n for n in ET.fromstring(self.settings.read_bytes()).findall('.//PLUGIN') if n.get('uid')==UID]),1)
 def test_uninstall_and_repeated_uninstall(self):
  self.assertEqual(self.run_script().returncode,0)
  for _ in range(2):
   p=self.run_script('uninstall.sh');self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertFalse(self.target.exists());self.check_foreign();self.assertEqual(len(ET.fromstring(self.settings.read_bytes()).findall('.//PLUGIN')),80)
 def test_checksum_failure_precedes_service_stop(self):
  (self.pkg/'portable'/F/'ghost.so').write_bytes(b'corruption');p=self.run_script();self.assertNotEqual(p.returncode,0);self.assertFalse(self.log.exists());self.assertEqual(self.settings.read_bytes(),self.before);self.assertFalse(self.target.exists())
 def test_rollback_exact_prior_folder_preserves_new_preferences(self):
  self.assertEqual(self.run_script().returncode,0);(self.target/'ghost.so').write_bytes(b'prior working binary');old=files(self.target);backup=self.root/'independent-backup';shutil.copytree(self.target,backup);saved=self.settings.read_bytes();self.assertEqual(self.run_script().returncode,0)
  self.settings.write_bytes(self.settings.read_bytes().replace(b'val="current"',b'val="new-value"'))
  # Same GHOST identity/path in upgrade: registry already valid, so rollback replaces GHOST only, never settings.
  shutil.rmtree(self.target);shutil.copytree(backup,self.target);self.assertEqual(files(self.target),old);self.assertIn(b'val="new-value"',self.settings.read_bytes());self.assertEqual(ET.fromstring(saved).find('.//PLUGIN[@uid="47485354"]').attrib,ET.fromstring(self.settings.read_bytes()).find('.//PLUGIN[@uid="47485354"]').attrib)
 def test_failure_after_activation_restores_service_but_not_old_plugin(self):
  self.assertEqual(self.run_script().returncode,0);saved=self.settings.read_bytes();(self.target/'ghost.so').write_bytes(b'prior working binary');(self.tools/'awk').unlink();(self.tools/'awk').write_text('#!/bin/sh\nexit 9\n');(self.tools/'awk').chmod(0o755)
  p=self.run_script();self.assertNotEqual(p.returncode,0);self.assertEqual(self.log.read_text().splitlines()[-2:],['stop','start']);self.assertEqual(self.settings.read_bytes(),saved);self.assertNotEqual((self.target/'ghost.so').read_bytes(),b'prior working binary')
  # Deliberate limitation: standard upstream script has EXIT restart but no independent watchdog/automatic rollback.
