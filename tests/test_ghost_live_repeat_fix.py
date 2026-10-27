"""Real native stereo repeat invariants. No hardware access."""
import ctypes as C,hashlib,json,math,pathlib,sys,unittest
R=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'experiments/ghost-c1'),str(R/'tests')]
from test_vst import FX
P=R/'build/ghost-performance-edition/native/ghost.so';OLD=R/'build/ghost-live-repeat-reference/native.so'
def probe(f):
 a=(C.c_double*16)();f.lib.ghost_buffer_probe.argtypes=[C.c_void_p,C.POINTER(C.c_double)];f.lib.ghost_buffer_probe(f.fx,a);return list(a)
def process(f,left,right,block=128):
 out=[[],[]]
 for k in range(0,len(left),block):
  n=min(block,len(left)-k);a=(C.c_float*n)(*left[k:k+n]);b=(C.c_float*n)(*right[k:k+n]);x=(C.c_float*n)();y=(C.c_float*n)();f.process(f.fx,(C.POINTER(C.c_float)*2)(a,b),(C.POINTER(C.c_float)*2)(x,y),n);out[0]+=x;out[1]+=y
 return out
def source(n):
 return ([.17*math.sin(i*.037+i*i*.000001)+(.18 if i%1703<7 else 0) for i in range(n)],[.13*math.cos(i*.061)+(.14 if i%1217<5 else 0) for i in range(n)])
def initialize(path=P,rate=44100,size=.4):
 f=FX(path);f.d(f.fx,10,0,0,None,rate);f.d(f.fx,2,0,0,None,0);f.block()
 for p,v in [(48,0),(131,0),(49,0),(54,0),(1,0),(11,0),(14,0),(9,0),(17,0),(15,.5),(16,.5),(18,1),(53,1),(134,size)]:f.set(f.fx,p,v)
 process(f,*source(int(rate*.7)));f.set(f.fx,128,1);return f
class LiveRepeat(unittest.TestCase):
 def test_fixed_region_stereo_and_stopped_input(self):
  for rate in [16000,44100,48000,96000]:
   for size in [0,.5,1]:
    f=initialize(rate=rate,size=size)
    try:
     process(f,*source(int(rate*.3)));p=probe(f);a=process(f,[0.]*(int(rate*.4)+int(p[5])*4),[0.]*(int(rate*.4)+int(p[5])*4));q=probe(f);n=int(q[5]);self.assertEqual(p[3:6],q[3:6]);self.assertNotEqual(q[0],q[3]);self.assertGreater(n,1)
     for ch in a:
      end=ch[-n:];prev=ch[-2*n:-n];self.assertGreater(sum(x*x for x in end),.0001);self.assertLess(max(abs(x-y) for x,y in zip(end,prev)),2e-5)
     self.assertNotEqual(a[0][-n:],a[1][-n:])
    finally:f.close()
 def test_pinned_for_longer_than_circular_capacity(self):
  f=initialize()
  try:
   process(f,[0.]*1000,[0.]*1000);p=probe(f);a=process(f,[0.]*(44100*9),[0.]*(44100*9));q=probe(f);self.assertEqual(p[3:6],q[3:6]);self.assertGreater(sum(x*x for x in a[0][-10000:]),.01)
  finally:f.close()
 def test_fragment_resize_and_toggle_then_reverse_freeze_capture_clean(self):
  f=initialize()
  try:
   for size in [0,.5,1,.2]:
    f.set(f.fx,134,size);a=process(f,[0.]*22050,[0.]*22050);self.assertTrue(all(math.isfinite(x) and abs(x)<1 for ch in a for x in ch));self.assertAlmostEqual(probe(f)[5],round(44100*.008*50**size),delta=2);display=C.create_string_buffer(16);f.d(f.fx,7,134,0,display,0);self.assertAlmostEqual(float(display.value),.008*50**size*1000,delta=.02)
   for _ in range(4):
    f.set(f.fx,128,0);process(f,*source(22050));f.set(f.fx,128,1);process(f,*source(1000))
   f.set(f.fx,128,0);f.set(f.fx,14,1);process(f,*source(10000));f.set(f.fx,126,1);process(f,*source(10000));f.set(f.fx,126,0);process(f,*source(1000));self.assertEqual(f.get(f.fx,11),1);f.set(f.fx,56,1);process(f,[0.]*1000,[0.]*1000);self.assertEqual(f.get(f.fx,128),0)
  finally:f.close()
 def test_cold_start_and_preset_recall(self):
  f=FX(P)
  try:
   for p,v in [(131,0),(48,0),(53,1),(128,1)]:f.set(f.fx,p,v)
   a=process(f,[0.]*20000,[0.]*20000);self.assertTrue(all(x==0 for ch in a for x in ch));process(f,*source(22050));f.d(f.fx,2,0,0,None,0);f.block();self.assertEqual(f.get(f.fx,128),0)
  finally:f.close()
 def test_classic_repeat_without_advanced_setup(self):
  f=FX(P)
  try:
   f.d(f.fx,2,0,0,None,0);f.block();f.set(f.fx,131,0);f.set(f.fx,53,1);process(f,*source(44100));f.set(f.fx,128,1);a=process(f,[0.]*132300,[0.]*132300);n=int(probe(f)[5]);self.assertGreater(sum(x*x for x in a[0][-n:]),.001);self.assertLess(max(abs(x-y) for x,y in zip(a[0][-n:],a[0][-2*n:-n])),2e-5)
  finally:f.close()
 def test_activation_release_fades_bounded_on_dc(self):
  f=FX(P)
  try:
   for p,v in [(48,0),(131,0),(53,1),(9,0),(17,0),(15,.5),(16,.5),(18,1)]:f.set(f.fx,p,v)
   process(f,[.2]*44100,[.1]*44100);f.set(f.fx,128,1);a=process(f,[0.]*22050,[0.]*22050);f.set(f.fx,128,0);b=process(f,[0.]*1000,[0.]*1000);self.assertLess(max(abs(x-y) for x,y in zip(b[0],b[0][1:])),.005);self.assertLess(abs(b[0][0]-a[0][-1]),.005)
  finally:f.close()
 def test_block_invariance(self):
  streams=[]
  for block in [32,128,511]:
   f=initialize()
   try:streams.append(process(f,[0.]*44100,[0.]*44100,block))
   finally:f.close()
  self.assertEqual(streams[0],streams[1]);self.assertEqual(streams[1],streams[2])
if __name__=='__main__':unittest.main(verbosity=2)

class QLinkFix(unittest.TestCase):
 def test_exact_mapping_labels_and_touch_bindings(self):
  import zipfile
  root=R/'build/ghost-performance-edition/gui/MPC-EURO - VST - GHOST/Plugin Skins'
  q=json.loads((root/'Q-Links.json').read_text());graph=json.loads((R/'build/ghost-performance-edition/control-graph.json').read_text());expected=[132,133,53,139,12,134,9,17,135,136,137,138,140,77,79,13];slots=[13,9,5,1,14,10,6,2,15,11,7,3,16,12,8,4];row=q['Screen Mode Q-Links']['map'][0]['Q-Links'];self.assertEqual([row['Q-Link '+str(s)] for s in slots],expected)
  for i,p in enumerate(expected):
   owners=[c for c in graph if c['view']=='PLAY' and c['parameter']==p and c.get('rotary')];self.assertEqual(len(owners),1);self.assertEqual((owners[0]['bank'],owners[0]['bank_position'],owners[0]['slot']),('ABCD'[i//4],i%4+1,slots[i]))
  with zipfile.ZipFile(R/'build/ghost-live-repeat-reference/previous-armv7.zip') as z:old=json.loads(z.read('MPC-EURO - VST - GHOST/Plugin Skins/Q-Links.json'))
  self.assertEqual(q['Program Mode Q-Links'],old['Program Mode Q-Links'])
  for slot in slots[8:]:self.assertEqual(row['Q-Link '+str(slot)],old['Screen Mode Q-Links']['map'][0]['Q-Links']['Q-Link '+str(slot)])
