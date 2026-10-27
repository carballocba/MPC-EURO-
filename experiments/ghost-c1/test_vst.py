import ctypes as C,sys,math,time,threading,unittest,pathlib,struct
from bindings import ROOT,OUT,IDS,Native
sys.path.insert(0,str(ROOT/'tests'))
from test_shared import Effect,Ptr,Dispatch,Set,Get,Process
class FX:
 def __init__(self,path):
  self.lib=C.CDLL(str(path));self.lib.VSTPluginMain.argtypes=[C.c_void_p];self.lib.VSTPluginMain.restype=Ptr;self.fx=self.lib.VSTPluginMain(None);assert self.fx
  self.d=Dispatch(self.fx.contents.dispatcher);self.set=Set(self.fx.contents.setParameter);self.get=Get(self.fx.contents.getParameter);self.process=Process(self.fx.contents.processReplacing)
  for op,v,opt in [(0,0,0),(10,0,44100),(12,1,0)]:self.d(self.fx,op,0,v,None,opt)
 def block(self,n=128,index=0):
  l=(C.c_float*n)(*[.2*math.sin((index+k)*.05) for k in range(n)]);r=(C.c_float*n)(*[.1*math.cos((index+k)*.07) for k in range(n)]);a=(C.c_float*n)();b=(C.c_float*n)();self.process(self.fx,(C.POINTER(C.c_float)*2)(l,r),(C.POINTER(C.c_float)*2)(a,b),n);return list(a),list(b)
 def chunk(self):
  p=C.c_void_p();n=self.d(self.fx,23,0,0,C.byref(p),0);return C.string_at(p,n) if n else b''
 def load(self,data):
  b=C.create_string_buffer(data);return self.d(self.fx,24,0,len(data),b,0)
 def close(self):self.d(self.fx,1,0,0,None,0)
class VSTTests(unittest.TestCase):
 def setUp(self):self.p=FX(OUT/'beatrepeat-ghost-c1.so')
 def tearDown(self):self.p.close()
 def test_identity_indices(self):
  self.assertEqual(self.p.fx.contents.uniqueID,0x45754272);self.assertEqual(self.p.fx.contents.numParams,49+len(IDS))
  for i in range(49):
   a=C.create_string_buffer(8);self.p.d(self.p.fx,8,i,0,a,0);self.assertTrue(a.value)
 def test_disabled_exact_reference(self):
  b=FX(ROOT/'build/beatrepeat-native.so')
  try:
   for k in range(100):
    if k in [1,40,70]:
     for fx in [b,self.p]:fx.set(fx.fx,1,1 if k!=70 else 0);fx.set(fx.fx,9,.3)
    self.assertEqual(b.block(index=k*128),self.p.block(index=k*128))
  finally:b.close()
 def test_extended_motion_and_chaos(self):
  self.p.set(self.p.fx,1,1);self.p.set(self.p.fx,49+IDS['P_GHOST'],1);self.p.set(self.p.fx,49+IDS['P_CHAOS_ON'],1);self.p.set(self.p.fx,49+IDS['P_CHAOS'],1)
  for k in range(100):self.assertTrue(all(math.isfinite(x) for ch in self.p.block(index=k*128) for x in ch))
  self.assertEqual(self.p.get(self.p.fx,49+IDS['P_GHOST']),1)
 def test_legacy_chunk_and_roundtrip(self):
  b=FX(ROOT/'build/beatrepeat-native.so')
  try:data=b.chunk()
  finally:b.close()
  self.assertEqual(data[:4],b'EBR2');self.assertEqual(self.p.load(data),1);self.p.block();chunk=self.p.chunk();self.assertEqual(chunk[:4],b'GCX1');self.assertEqual(self.p.load(chunk),1);self.p.block();self.assertEqual(self.p.chunk(),chunk)
 def test_recall_during_audio(self):
  data=self.p.chunk();fail=[]
  def audio():
   try:
    for k in range(100):self.p.block(index=k*128)
   except Exception as e:fail.append(str(e))
  t=threading.Thread(target=audio);t.start()
  for k in range(100):self.p.load(data)
  t.join();self.assertFalse(fail)
 def test_clean_overflow_priority(self):
  for k in range(100):self.p.set(self.p.fx,49+IDS['P_CHAOS'],k/100)
  self.p.set(self.p.fx,49+IDS['P_CLEAN'],1)
  for k in range(10):self.p.block()
  self.assertEqual(self.p.get(self.p.fx,49+IDS['P_GHOST']),0)
 def test_mix_qlink_base_readback(self):
  self.p.set(self.p.fx,2,.5);self.p.set(self.p.fx,8,.5+1/128);self.assertAlmostEqual(self.p.get(self.p.fx,2),.5+4/128)
 def test_fast_mix_multiple_turns(self):
  self.p.set(self.p.fx,2,.25)
  cursor=.25
  for k in range(6):
   cursor+=1/128;self.p.set(self.p.fx,8,cursor);self.p.block()
  self.assertAlmostEqual(self.p.get(self.p.fx,2),.25+24/128)
 def test_factory_program_resets_extension(self):
  self.p.set(self.p.fx,49+IDS['P_GHOST'],1);self.p.block()
  for program in range(8):
   self.p.d(self.p.fx,2,0,program,None,0);self.p.block();self.assertEqual(self.p.get(self.p.fx,49+IDS['P_GHOST']),0)
 def test_rate_preserves_motion_configuration(self):
  self.p.set(self.p.fx,49+IDS['P_CHAOS'],.63);self.p.block();self.p.d(self.p.fx,10,0,0,None,48000);self.p.block();self.assertAlmostEqual(self.p.get(self.p.fx,49+IDS['P_CHAOS']),.63,places=6)
 def test_malformed_chunk_atomic(self):
  data=self.p.chunk();bad=bytearray(data);bad[-1]^=1;self.assertEqual(self.p.load(bytes(bad)),0);self.p.block();self.assertEqual(self.p.chunk(),data)
 def test_accumulating(self):
  n=128;zero=(C.c_float*n)();a=(C.c_float*n)(*([.25]*n));b=(C.c_float*n)(*([-.25]*n));f=Process(self.p.fx.contents.process);f(self.p.fx,(C.POINTER(C.c_float)*2)(zero,zero),(C.POINTER(C.c_float)*2)(a,b),n);self.assertTrue(all(x==.25 for x in a));self.assertTrue(all(x==-.25 for x in b))
 def test_ebr1_legacy_import(self):
  b=FX(ROOT/'build/beatrepeat-native.so')
  try:source=b.chunk()
  finally:b.close()
  prefix=bytearray(source[:44]);prefix[:4]=b'EBR1';struct.pack_into('<I',prefix,4,1);h=2166136261
  for x in prefix:h=((h^x)*16777619)&0xffffffff
  data=bytes(prefix)+struct.pack('<I',h);self.assertEqual(self.p.load(data),1);self.p.block();self.assertEqual(self.p.get(self.p.fx,48),1)
  self.p.set(self.p.fx,49+IDS['P_GHOST'],1);self.p.block();self.assertEqual(self.p.get(self.p.fx,49+IDS['P_GHOST']),0)
 def test_ebr2_invalid_enum_rejected(self):
  b=FX(ROOT/'build/beatrepeat-native.so')
  try:prefix=bytearray(b.chunk()[:-4])
  finally:b.close()
  struct.pack_into('<f',prefix,12+14*4,.25);h=2166136261
  for x in prefix:h=((h^x)*16777619)&0xffffffff
  self.assertEqual(self.p.load(bytes(prefix)+struct.pack('<I',h)),0)
if __name__=='__main__':unittest.main(verbosity=2)
