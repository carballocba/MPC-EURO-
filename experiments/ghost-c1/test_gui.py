"""Offline checks of exported host GUI, state mapping and forward-compatible states."""
import unittest,json,sys,struct
from bindings import Native,ROOT,OUT,IDS
sys.path.insert(0,str(ROOT/'vendor/mpc/tools'))
import skin_check
SKIN=OUT/'native-skin/MPC-EURO - VST - BeatRepeat/Plugin Skins'
def digest(data):
 h=2166136261
 for b in data:h=((h^b)*16777619)&0xffffffff
 return struct.pack('<I',h)
class GUI(unittest.TestCase):
 def test_geometry(self):self.assertEqual(skin_check.check(str(SKIN)),[])
 def test_parameter_indices(self):
  p=json.loads((OUT/'parameters.json').read_text());self.assertEqual(p[:49],json.loads((ROOT/'ui/params.json').read_text()));n=Native()
  try:self.assertEqual([x['key'] for x in p[49:]],['g_'+x['key'] for x in n.registry()])
  finally:n.close()
 def test_five_pages_and_mascot_real_binding(self):
  t=json.loads((SKIN/'TUI.json').read_text());pages=list(skin_check.pages(t));self.assertEqual(len(pages),5)
  for tab,kids,_ in pages:
   mascot=[c for c in kids if c['componentData']['name'].startswith('Ghost ')]
   self.assertEqual(len(mascot),8)
   for i,c in enumerate(mascot):self.assertIn(f'IndexedEnabling/{i}/8/Parameter {49+IDS["P_STATUS"]}',c['bounds']['additionalInvalidatingHandles'])
 def test_program_qlinks_preserved(self):
  original=json.loads((ROOT/'build/skin/MPC-EURO - VST - BeatRepeat/Plugin Skins/Q-Links.json').read_text());new=json.loads((SKIN/'Q-Links.json').read_text());self.assertEqual(original['Program Mode Q-Links'],new['Program Mode Q-Links'])
 def test_unknown_tlv_and_duplicate_rejection(self):
  n=Native()
  try:
   data=n.save();prefix=bytearray(data[:-8]);prefix+=struct.pack('<II',99,4)+b'NEXT'+b'\0'*4;struct.pack_into('<I',prefix,8,len(prefix)+4);future=bytes(prefix)+digest(prefix);self.assertTrue(n.load(future));self.assertEqual(n.save(),data)
   prefix=bytearray(data[:-8]);prefix+=data[12:20+struct.unpack_from('<I',data,16)[0]]+b'\0'*4;struct.pack_into('<I',prefix,8,len(prefix)+4);self.assertFalse(n.load(bytes(prefix)+digest(prefix)));self.assertEqual(n.save(),data)
  finally:n.close()
 def test_status_clean_and_listen(self):
  n=Native()
  try:
   n.set('P_LISTEN',1);n.process([0]*128,[0]*128);self.assertEqual(n.get('P_STATUS'),1);n.set('P_CLEAN',1);n.process([0]*128,[0]*128);self.assertEqual(n.get('P_STATUS'),7)
  finally:n.close()
 def test_destination_range_controls(self):
  t=json.loads((SKIN/'TUI.json').read_text());bound={}
  for _,kids,_ in skin_check.pages(t):
   for c in kids:
    p=skin_check._param(c)
    if p is not None and 49+IDS['P_R0MIN']<=p<49+IDS['P_EDIT']:bound[p]=c['bounds']['additionalInvalidatingHandles']
  self.assertEqual(len(bound),16)
  params=json.loads((OUT/"parameters.json").read_text())
  for p in bound:self.assertNotIn("options",params[p])
  for p,handles in bound.items():self.assertTrue(any(h.startswith('IndexedEnabling/') and h.endswith(f'Parameter {49+IDS["P_DEST"]}') for h in handles))
 def test_mascot_assets_unchanged(self):
  import hashlib
  previous=ROOT/'build/ghost-c1-demo/native-skin/MPC-EURO - VST - BeatRepeat/Plugin Skins'
  for i in range(8):self.assertEqual(hashlib.sha256((SKIN/f'ghost-{i}.png').read_bytes()).digest(),hashlib.sha256((previous/f'ghost-{i}.png').read_bytes()).digest())
if __name__=='__main__':unittest.main(verbosity=2)
