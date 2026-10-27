"""Native audio/state tests of appended Random Repeat policy. No MPC/network."""
import pathlib,sys,ctypes as C,json,math,struct,hashlib,unittest
R=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tests'),str(R/'experiments/ghost-c1')]
from test_ghost_live_repeat_fix import FX,process,source,probe,P
from test_ghost_final_integration import stats

def setup(mode=1/3):
 f=FX(P);f.d(f.fx,2,0,0,None,0);f.block()
 for p,v in [(48,0),(131,0),(1,0),(11,0),(14,0),(9,0),(17,0),(15,.5),(16,.5),(18,1),(53,1),(32,0),(132,.8),(133,.6),(134,.5),(139,.7),(149,1),(150,1),(151,1),(152,.8),(153,.3),(75,.123)]:f.set(f.fx,p,v)
 process(f,*source(44100));f.set(f.fx,148,mode);return f

def rrstats(f):
 a=(C.c_double*6)();f.lib.ghost_rr_stats.argtypes=[C.c_void_p,C.POINTER(C.c_double)];f.lib.ghost_rr_stats(f.fx,a);return list(a)

def run(mode=1/3,seconds=8,block=128):
 f=setup(mode);a,b=source(int(seconds*44100));out=process(f,a,b,block);s=rrstats(f);p=stats(f);f.close();return out,s,p
class RandomRepeat(unittest.TestCase):
 def test_entries_exits_fragment_and_determinism(self):
  a,s,_=run();b,t,_=run();self.assertEqual(a,b);self.assertEqual(s,t);self.assertGreater(s[0],2);self.assertGreater(s[1],2);self.assertGreater(s[2],2);self.assertTrue(all(math.isfinite(x) and abs(x)<1 for ch in a for x in ch))
 def test_modes(self):
  for mode,performance,rr in [(1/3,False,True),(2/3,True,False),(1,True,True)]:
   a,s,p=run(mode);self.assertEqual(s[0]>0,rr);self.assertEqual(p[0]>0,performance)
 def test_no_base_writes_and_off_restores_manual(self):
  f=setup()
  try:
   before=[f.get(f.fx,p) for p in [128,134,0,11,126,149,150,151,152,153]];process(f,*source(44100*5));self.assertEqual(before,[f.get(f.fx,p) for p in [128,134,0,11,126,149,150,151,152,153]])
   f.set(f.fx,148,0);process(f,*source(44100));self.assertEqual(f.get(f.fx,128),0);self.assertEqual(probe(f)[0],probe(f)[3]);self.assertEqual(f.get(f.fx,134),.5)
  finally:f.close()
 def test_manual_gestures_and_clean(self):
  f=setup()
  try:
   process(f,*source(44100));f.set(f.fx,128,1);process(f,*source(4410));self.assertEqual(probe(f)[0]!=probe(f)[3],True)
   f.set(f.fx,134,.1);process(f,*source(4410));self.assertAlmostEqual(probe(f)[5],round(44100*.008*50**.1),delta=2)
   f.set(f.fx,56,1);process(f,*source(44100));self.assertEqual(f.get(f.fx,148),0);self.assertEqual(f.get(f.fx,128),0);self.assertEqual(f.get(f.fx,131),0)
  finally:f.close()
 def test_state_roundtrip_and_legacy_decoder(self):
  f=setup(1)
  try:
   process(f,*source(128));state=f.chunk();self.assertEqual(state[:4],b'RRF1');self.assertEqual(f.load(state),1);f.block();self.assertEqual(state,f.chunk())
   bad=bytearray(state);bad[-1]^=1;self.assertEqual(f.load(bytes(bad)),0);self.assertEqual(f.chunk(),state)
   f.d(f.fx,2,0,0,None,0);f.block();self.assertEqual(f.chunk()[:4],b'PEF1');self.assertEqual(f.get(f.fx,148),0)
  finally:f.close()
 def test_block_invariance(self):
  a,_,_=run(block=32);b,_,_=run(block=511);self.assertEqual(a,b)
 def test_no_automatic_capture_freeze_and_protected_take(self):
  f=setup(1)
  try:
   f.set(f.fx,126,1);process(f,*source(11025));f.set(f.fx,126,0);process(f,*source(1000));self.assertEqual(f.get(f.fx,11),1);start=probe(f);process(f,*source(44100*3));end=probe(f);self.assertEqual(start[10],1);self.assertEqual(end[10],1);self.assertEqual(start[1],end[1]);self.assertEqual(f.get(f.fx,126),0)
  finally:f.close()
 def test_disabled_settings_persist_and_suspend_preserves_mode(self):
  f=setup()
  try:
   f.d(f.fx,12,0,0,None,0);state=f.chunk();self.assertEqual(state[:4],b'RRF1');self.assertAlmostEqual(f.get(f.fx,148),1/3,places=5);self.assertEqual(f.load(state),1);self.assertEqual(f.chunk(),state)
   f.d(f.fx,12,0,1,None,0);f.set(f.fx,148,0);process(f,*source(1024));state=f.chunk();self.assertEqual(f.load(state),1);f.block();self.assertEqual(f.chunk(),state)
  finally:f.close()
 def test_mismatched_wrapper_rejected_without_mutation(self):
  f=setup(1)
  try:
   f.block();state=f.chunk();bad=bytearray(state);struct.pack_into('<f',bad,16,1/3);h=2166136261
   for x in bad[:-4]:h=((h^x)*16777619)&0xffffffff
   struct.pack_into('<I',bad,len(bad)-4,h);self.assertEqual(f.load(bytes(bad)),0);self.assertEqual(f.chunk(),state)
  finally:f.close()
 def test_rates_tempo_and_legacy_switch(self):
  f=setup()
  try:
   for rate in [16000,44100,96000]:
    f.d(f.fx,10,0,0,None,rate);f.set(f.fx,33,.9);a=process(f,*source(rate));self.assertTrue(all(math.isfinite(x) for ch in a for x in ch))
   f.set(f.fx,48,1);f.block();self.assertEqual(f.get(f.fx,148),0)
  finally:f.close()
 def test_fragment_gesture_in_both_and_zero_activity(self):
  f=setup(1)
  try:
   process(f,*source(22050));f.set(f.fx,128,1);f.set(f.fx,134,.1);process(f,*source(4410));self.assertAlmostEqual(probe(f)[5],round(44100*.008*50**.1),delta=2)
   f.set(f.fx,128,0);process(f,*source(44100));f.set(f.fx,132,0);process(f,*source(44100));self.assertEqual(rrstats(f)[3],0)
  finally:f.close()
 def test_public_contract(self):
  f=setup()
  try:
   self.assertEqual(f.fx.contents.numParams,156);self.assertEqual(f.fx.contents.uniqueID,1195922260);self.assertEqual(f.fx.contents.numPrograms,16)
   for p in range(148,156):self.assertEqual(f.d(f.fx,26,p,0,None,0),p<154)
  finally:f.close()
