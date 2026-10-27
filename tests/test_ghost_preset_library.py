"""Offline artifact contract, no MPC access."""
import hashlib,json,pathlib,struct,unittest,zipfile
R=pathlib.Path(__file__).resolve().parents[1];B=R/'build/ghost-preset-library'
class Library(unittest.TestCase):
 def test_library_contract(self):
  d=json.loads((B/'validation.json').read_text());self.assertEqual(len(d['new']),32);self.assertEqual(len(d['original']),16)
  self.assertEqual(len({x['name'] for x in d['new']}),32)
  for x in d['new']:
   raw=(B/x['file']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),x['sha256']);self.assertEqual(raw[:4],b'CcnK');self.assertEqual(raw[8:12],b'FPCh');self.assertEqual(struct.unpack_from('>I',raw,16)[0],1195922260);self.assertEqual(raw[60:64],b'PEF1');self.assertEqual(struct.unpack_from('<I',raw,64)[0],2);self.assertEqual(len(x['audio']),6)
 def test_binary_gui_and_historical_presets_unchanged(self):
  with zipfile.ZipFile(B/'REFERENCE-armv7.zip') as a,zipfile.ZipFile(B/'ghost-performance-preset-library-armv7-TRIAL.zip') as b:
   for n in a.namelist():
    if not n.endswith(('manifest.json','SHA256SUMS')):self.assertEqual(a.read(n),b.read(n),n)
   for n in b.namelist():
    if n.endswith('manifest.json'):
     root=n[:-len('manifest.json')];m=json.loads(b.read(n))
     for p,h in m['files'].items():self.assertEqual(hashlib.sha256(b.read(root+p)).hexdigest(),h)
if __name__=='__main__':unittest.main()
