"""Actual VST integration: dense MIDI, sample offsets, range editing and manual priority."""
import ctypes as C,unittest,math,json,struct
from bindings import ROOT,OUT,IDS,Native
from test_vst import FX
from test_v2 import Midi
INDEX={p['key']:i for i,p in enumerate(json.loads((ROOT/'ui/params.json').read_text()))}
def events(fx,rows):
 class Batch(C.Structure):_fields_=[('numEvents',C.c_int32),('reserved',C.c_ssize_t),('events',C.c_void_p*len(rows))]
 batch=Batch();batch.numEvents=len(rows);messages=[]
 for i,(status,note,velocity,delta) in enumerate(rows):
  m=Midi();m.type=1;m.byteSize=C.sizeof(Midi);m.delta=delta;m.data[:]=(status,note,velocity,0);messages.append(m);batch.events[i]=C.addressof(m)
 return fx.d(fx.fx,25,0,0,C.byref(batch),0)
def stats(fx):
 a=(C.c_uint*3)();fx.lib.ghost_c11_stats.argtypes=[C.c_void_p,C.POINTER(C.c_uint)];fx.lib.ghost_c11_stats(fx.fx,a);return list(a)
def alias(fx,name,x):fx.set(fx.fx,49+IDS[name],x)
class Hardening(unittest.TestCase):
 def setUp(self):self.p=FX(OUT/'beatrepeat-ghost-c1.so')
 def tearDown(self):self.p.close()
 def test_single_engine_memory(self):
  self.p.lib.ghost_c1_wrapper_bytes.restype=C.c_size_t;self.assertLess(self.p.lib.ghost_c1_wrapper_bytes(),3300000)
 def test_offsets_and_unsorted_events_exact_original(self):
  b=FX(ROOT/'build/beatrepeat-native.so')
  try:
   for f in [self.p,b]:f.set(f.fx,INDEX['midi_enable'],1)
   for k in range(30):self.assertEqual(self.p.block(index=k*128),b.block(index=k*128))
   rows=[(0xb0,22,99,91),(0xb0,20,127,13),(0xb0,23,57,63),(0xb0,24,127,110),(0xb0,27,127,45)]
   self.assertEqual(events(self.p,rows),1);self.assertEqual(events(b,rows),1)
   for k in range(30,50):self.assertEqual(self.p.block(index=k*128),b.block(index=k*128))
  finally:b.close()
 def test_dense_midi_does_not_suspend_motion(self):
  self.p.set(self.p.fx,INDEX['gate'],1);alias(self.p,'P_MDEST',1/11);alias(self.p,'P_ROUTE',1);alias(self.p,'P_TYPE',4/7);alias(self.p,'P_RATE',(5-.015625)/(60000-.015625));alias(self.p,'P_MOTION',1)
  changes=[]
  for k in range(200):
   self.assertEqual(events(self.p,[(0xb0,1,j%128,(511-j)%128) for j in range(512)]),1)
   audio=self.p.block(index=k*128);self.assertTrue(all(math.isfinite(x) for ch in audio for x in ch));probe=(C.c_float*2)();self.p.lib.ghost_c11_probe(self.p.fx,probe);changes.append(probe[0])
  self.assertGreater(max(changes)-min(changes),.1)
  self.assertEqual(self.p.get(self.p.fx,49+IDS['P_MOTION']),1);self.assertEqual(stats(self.p)[1:], [0,102400]);self.assertEqual(self.p.get(self.p.fx,INDEX['break']),0)
  # Counter/source state is not enough: compare rendered samples with modulation disabled.
  b=FX(OUT/'beatrepeat-ghost-c1.so')
  try:
   b.set(b.fx,INDEX['gate'],1);self.assertNotEqual(self.p.block(index=25600),b.block(index=25600))
  finally:b.close()
 def test_overflow_atomic_and_visible(self):
  self.assertEqual(events(self.p,[(0xb0,20,127,0)]*1024),0);self.p.block();self.assertEqual(self.p.get(self.p.fx,INDEX['gate']),0);self.assertEqual(stats(self.p)[1],1);self.assertEqual(self.p.get(self.p.fx,49+IDS['P_EDIT']),1)
  self.assertEqual(events(self.p,[(0xb0,1,0,0)]*900),1);self.assertEqual(events(self.p,[(0xb0,20,127,0)]*200),0);self.p.block();self.assertEqual(self.p.get(self.p.fx,INDEX['gate']),0)
 def test_range_crossing_feedback_and_recall(self):
  alias(self.p,'P_R7MIN',.9);self.p.block();self.assertAlmostEqual(self.p.get(self.p.fx,49+IDS['P_R7MIN']),.9,places=5);self.assertGreaterEqual(self.p.get(self.p.fx,49+IDS['P_R7MAX']),.9)
  alias(self.p,'P_R7MAX',.1);self.p.block();self.assertAlmostEqual(self.p.get(self.p.fx,49+IDS['P_R7MIN']),.1,places=5);self.assertAlmostEqual(self.p.get(self.p.fx,49+IDS['P_EDIT']),.2,places=5)
  data=self.p.chunk();self.assertTrue(data);alias(self.p,'P_R7MAX',1);self.p.block();self.assertEqual(self.p.load(data),1);self.p.block();self.assertAlmostEqual(self.p.get(self.p.fx,49+IDS['P_R7MAX']),.1,places=5)
 def test_range_identity_survives_selection_changes(self):
  alias(self.p,'P_DEST',0);alias(self.p,'P_R0MIN',.8);alias(self.p,'P_DEST',7/11);alias(self.p,'P_R0MAX',.9);self.p.block();self.assertAlmostEqual(self.p.get(self.p.fx,49+IDS['P_R0MIN']),.8,places=5);self.assertAlmostEqual(self.p.get(self.p.fx,49+IDS['P_R7MIN']),0,places=5)
 def test_clean_wins_same_block_midi(self):
  alias(self.p,'P_GHOST',1);alias(self.p,'P_MOTION',1);alias(self.p,'P_CHAOS_ON',1);alias(self.p,'P_CHAOS',1)
  for k in range(20):self.p.block(index=k*128)
  alias(self.p,'P_CLEAN',1);events(self.p,[(0xb0,20,127,j) for j in range(128)]);self.p.block();self.assertEqual(self.p.get(self.p.fx,INDEX['gate']),0);self.assertEqual(self.p.get(self.p.fx,49+IDS['P_GHOST']),0);self.assertEqual(self.p.get(self.p.fx,49+IDS['P_STATUS']),1)
 def test_sustained_mapped_midi_manual_qlink_and_chaos(self):
  for dest in [0,1,2,3]:alias(self.p,'P_DEST',dest/11);alias(self.p,'P_RANDOM',1);self.p.block()
  alias(self.p,'P_GHOST',1);alias(self.p,'P_CHAOS_ON',1);alias(self.p,'P_CHAOS',1)
  for k in range(500):
   self.p.set(self.p.fx,INDEX['mix'],.5);self.p.set(self.p.fx,INDEX['mix_live'],.5+1/128)
   self.assertEqual(events(self.p,[(0xb0,[22,25,28,29,31][j%5],j%128,j%128) for j in range(512)]),1)
   if k%71==0:alias(self.p,'P_CLEAN',1)
   if k%71==1:alias(self.p,'P_GHOST',1)
   self.assertTrue(all(math.isfinite(x) for ch in self.p.block(index=k*128) for x in ch));self.assertAlmostEqual(self.p.get(self.p.fx,INDEX['mix']),.5+4/128)
  self.assertEqual(stats(self.p)[0:2],[0,0])
 def test_suspended_range_save_without_audio(self):
  self.p.d(self.p.fx,12,0,0,None,0);alias(self.p,'P_R5MIN',.6);alias(self.p,'P_R5MAX',.8)
  data=self.p.chunk();self.assertTrue(data);self.assertEqual(self.p.load(data),1);self.p.chunk();self.assertAlmostEqual(self.p.get(self.p.fx,49+IDS['P_R5MIN']),.6,places=5)
 def test_all_range_domains_roundtrip(self):
  n=Native()
  try:
   for dest in [0,1,4,5,7,8,9,10]:
    lo=n.params[IDS[f'P_R{dest}MIN']].minimum;hi=n.params[IDS[f'P_R{dest}MAX']].maximum
    n.set(f'P_R{dest}MIN',lo+.3*(hi-lo));n.set(f'P_R{dest}MAX',lo+.7*(hi-lo))
   data=n.save();m=Native()
   try:self.assertTrue(m.load(data));self.assertEqual(m.save(),data)
   finally:m.close()
  finally:n.close()
 def test_midi_mix_then_qlink_manual_cursor(self):
  alias(self.p,'P_GHOST',1);self.p.block();self.p.set(self.p.fx,2,.5);self.p.set(self.p.fx,8,.5+1/128)
  self.assertEqual(events(self.p,[(0xb0,23,100,64)]),1);self.p.block();base=self.p.get(self.p.fx,2);self.assertAlmostEqual(base,100/127,places=6)
  self.p.set(self.p.fx,8,base+1/128);self.p.block();self.assertAlmostEqual(self.p.get(self.p.fx,2),base+4/128,places=6)
 def test_C1_chunk_compatibility(self):
  old=FX(OUT/'reference-products/beatrepeat-ghost-c1.so')
  try:
   alias(old,'P_DEST',8/11);alias(old,'P_RANDOM',1);old.block();data=old.chunk();self.assertTrue(data);self.assertEqual(self.p.load(data),1);self.p.block();self.assertEqual(self.p.get(self.p.fx,49+IDS['P_RANDOM']),1)
   modern=self.p.chunk();self.assertTrue(modern);self.assertEqual(old.load(modern),1);old.block()
  finally:old.close()
 def test_entire_C1_parameter_prefix_preserved(self):
  old=FX(OUT/'reference-products/beatrepeat-ghost-c1.so')
  try:
   self.assertEqual(self.p.fx.contents.uniqueID,old.fx.contents.uniqueID)
   for index in range(old.fx.contents.numParams):
    a=C.create_string_buffer(8);b=C.create_string_buffer(8);self.p.d(self.p.fx,8,index,0,a,0);old.d(old.fx,8,index,0,b,0);self.assertEqual(a.raw,b.raw)
  finally:old.close()
 def test_native_host_range_display_and_feedback(self):
  alias(self.p,'P_R1MIN',.5);self.p.block();label=C.create_string_buffer(8);value=C.create_string_buffer(8)
  self.p.d(self.p.fx,6,49+IDS['P_R1MIN'],0,label,0);self.p.d(self.p.fx,7,49+IDS['P_R1MIN'],0,value,0);self.assertEqual(label.value,b'%');self.assertAlmostEqual(float(value.value),50)
  self.p.d(self.p.fx,6,49+IDS['P_R0MIN'],0,label,0);self.assertEqual(label.value,b'ms')
  alias(self.p,'P_R1MAX',.1);self.p.block();self.p.d(self.p.fx,7,49+IDS['P_EDIT'],0,value,0);self.assertEqual(value.value,b'LINKED')
if __name__=='__main__':unittest.main(verbosity=2)
