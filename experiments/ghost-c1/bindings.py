"""Local native embedding, no network/device dependency."""
import ctypes as C, pathlib, re
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'build/ghost-c11-demo'
text=(ROOT/'experiments/ghost-c1/c1.h').read_text()
PARAM_NAMES=re.search(r'enum \{ (P_GHOST.*?) \};',text,re.S).group(1).replace('\n','').split(',')
PARAM_NAMES=[p.strip() for p in PARAM_NAMES if p.strip()!='P_COUNT']
IDS={p:i for i,p in enumerate(PARAM_NAMES)}
class Param(C.Structure):
    _fields_=[('key',C.c_char_p),('name',C.c_char_p),('minimum',C.c_float),('maximum',C.c_float),('default',C.c_float),('readonly',C.c_uint)]
class Trace(C.Structure):
    _fields_=[('sample',C.c_uint64),('flags',C.c_uint),('status',C.c_uint),('active',C.c_uint),('capture',C.c_uint),('length',C.c_float),('fracture',C.c_float),('position',C.c_float),('mix',C.c_float),('energy',C.c_float)]
class Native:
    def __init__(self,rate=44100):
        self.rate=rate;self.lib=C.CDLL(str(OUT/'libghost-c1.so'));l=self.lib
        l.ghost_c1_create.argtypes=[C.c_double];l.ghost_c1_create.restype=C.c_void_p
        l.ghost_c1_destroy.argtypes=[C.c_void_p]
        l.ghost_c1_set.argtypes=[C.c_void_p,C.c_uint,C.c_float];l.ghost_c1_set.restype=C.c_int
        l.ghost_c1_get.argtypes=[C.c_void_p,C.c_uint];l.ghost_c1_get.restype=C.c_float
        l.ghost_c1_process.argtypes=[C.c_void_p,*([C.POINTER(C.c_float)]*4),C.c_uint,C.POINTER(Trace),C.c_uint];l.ghost_c1_process.restype=C.c_uint
        l.ghost_c1_save.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t];l.ghost_c1_save.restype=C.c_size_t
        l.ghost_c1_load.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t];l.ghost_c1_load.restype=C.c_int
        self.handle=l.ghost_c1_create(rate);assert self.handle
        self.params=(Param*len(PARAM_NAMES)).in_dll(l,'c1_params')
    def set(self,name,value):
        p=IDS[name] if isinstance(name,str) else name
        if not self.lib.ghost_c1_set(self.handle,p,value):raise ValueError(f'Refused {name}={value}')
    def get(self,name):return self.lib.ghost_c1_get(self.handle,IDS[name] if isinstance(name,str) else name)
    def process(self,left,right,trace=True):
        n=len(left);l=(C.c_float*n)(*left);r=(C.c_float*n)(*right);a=(C.c_float*n)();b=(C.c_float*n)();t=(Trace*128)()
        count=self.lib.ghost_c1_process(self.handle,l,r,a,b,n,t if trace else None,128 if trace else 0)
        rows=[{k:getattr(t[i],k) for k,_ in Trace._fields_} for i in range(count)]
        return list(a),list(b),rows
    def save(self):
        n=self.lib.ghost_c1_save(self.handle,None,0);buf=C.create_string_buffer(n);assert self.lib.ghost_c1_save(self.handle,buf,n)==n;return buf.raw
    def load(self,data):
        b=C.create_string_buffer(data);return bool(self.lib.ghost_c1_load(self.handle,b,len(data)))
    def close(self):
        if self.handle:self.lib.ghost_c1_destroy(self.handle);self.handle=None
    def registry(self):return [{'id':i,'symbol':PARAM_NAMES[i],'key':p.key.decode(),'name':p.name.decode(),'min':p.minimum,'max':p.maximum,'default':p.default,'readonly':bool(p.readonly)} for i,p in enumerate(self.params)]
