"""Focused BOTH policy/reader regression tests, actual native stereo processing."""
import pathlib,sys,math,unittest
R=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'experiments/ghost-performance'),str(R/'tests')]
from both_fix_evidence import render
from test_ghost_live_repeat_fix import FX,process,source,probe,P
from test_ghost_random_repeat import setup,rrstats
class BothFix(unittest.TestCase):
 def test_factory_defaults_both_has_effective_fragment_changes(self):
  out,trace,s=render(P,1);self.assertGreater(s[0],3);self.assertGreater(s[1],2);self.assertGreater(len({r[4] for r in trace if r[2]}),2);self.assertTrue(all(math.isfinite(x) and abs(x)<1 for ch in out for x in ch))
 def test_redundant_both_mode_delivery_does_not_restart_rng(self):
  a,ta,sa=render(P,1,seconds=8);b,tb,sb=render(P,1,seconds=8,redundant=True);self.assertTrue(a==b,"Redundant BOTH changed audio");self.assertTrue(ta==tb,"Redundant BOTH changed trace");self.assertEqual(sa,sb);self.assertGreater(sa[5],20)
 def test_both_rolling_phrases_at_zero_evolution(self):
  _,trace,_=render(P,1,seconds=16);slots={}
  for _,step,on,ms,length in trace:slots.setdefault(step,(on,ms))
  phrases=[[slots[k] for k in range(start,start+16) if k in slots] for start in [1,17,33,49]]
  self.assertNotEqual(phrases[0],phrases[1]);self.assertNotEqual(phrases[1],phrases[2])
 def test_mode_switch_and_performance_toggle_preserve_rr_phase(self):
  f=setup(1/3)
  try:
   process(f,*source(22050));n=rrstats(f)[5];f.set(f.fx,148,1);process(f,*source(1024));self.assertGreaterEqual(rrstats(f)[5],n)
   for state in [0,1,0,1]:
    n=rrstats(f)[5];f.set(f.fx,131,state);process(f,*source(4096));self.assertGreaterEqual(rrstats(f)[5],n);self.assertAlmostEqual(f.get(f.fx,148),1 if state else 1/3,places=5)
   f.set(f.fx,148,2/3);process(f,*source(44100));n=rrstats(f)[0];process(f,*source(44100));self.assertEqual(rrstats(f)[0],n)
  finally:f.close()
 def test_repeat_reader_tracks_planned_fragment_in_both(self):
  f=setup(1)
  try:
   f.set(f.fx,24,0) # existing immediate timing mode; avoid deferring a length to next loop boundary
   seen=set()
   for k in range(3000):
    process(f,*source(128));s=rrstats(f);p=probe(f)
    if s[3] and p[5]>=2:
     self.assertAlmostEqual(p[5],min(round(s[4]*44.1),p[2]),delta=2);seen.add(p[5])
   self.assertGreater(len(seen),2)
  finally:f.close()
 def test_manual_priority_and_clean_both(self):
  f=setup(1)
  try:
   process(f,*source(44100));f.set(f.fx,128,1);f.set(f.fx,134,.2);process(f,*source(4410));self.assertAlmostEqual(probe(f)[5],round(44.1*8*50**.2),delta=2)
   f.set(f.fx,56,1);process(f,*source(44100));self.assertEqual(f.get(f.fx,148),0);self.assertEqual(f.get(f.fx,131),0);self.assertEqual(f.get(f.fx,128),0)
  finally:f.close()
 def test_dc_transitions_no_added_step(self):
  f=setup(1)
  try:
   for p,v in [(132,.2),(135,1),(136,0),(137,0),(139,0),(9,0),(17,0),(15,.5),(16,.5)]:f.set(f.fx,p,v)
   process(f,[.2]*88200,[.2]*88200);a=process(f,[.2]*176400,[.2]*176400)
   self.assertLess(max(abs(x-y) for ch in a for x,y in zip(ch,ch[1:])),.005)
  finally:f.close()
