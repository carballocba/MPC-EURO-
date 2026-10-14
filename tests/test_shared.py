#!/usr/bin/env python3
"""Load the actual native .so through a small SDK-free VST2 host."""
import ctypes as C
from pathlib import Path
root=Path(__file__).resolve().parents[1]
class Effect(C.Structure):
    _fields_=[('magic',C.c_int32),('dispatcher',C.c_void_p),('process',C.c_void_p),
        ('setParameter',C.c_void_p),('getParameter',C.c_void_p),('numPrograms',C.c_int32),
        ('numParams',C.c_int32),('numInputs',C.c_int32),('numOutputs',C.c_int32),('flags',C.c_int32),
        ('resvd1',C.c_ssize_t),('resvd2',C.c_ssize_t),('initialDelay',C.c_int32),
        ('realQualities',C.c_int32),('offQualities',C.c_int32),('ioRatio',C.c_float),
        ('object',C.c_void_p),('user',C.c_void_p),('uniqueID',C.c_int32),('version',C.c_int32),
        ('processReplacing',C.c_void_p),('processDoubleReplacing',C.c_void_p),('future',C.c_char*56)]
Ptr=C.POINTER(Effect)
Dispatch=C.CFUNCTYPE(C.c_ssize_t,Ptr,C.c_int32,C.c_int32,C.c_ssize_t,C.c_void_p,C.c_float)
Set=C.CFUNCTYPE(None,Ptr,C.c_int32,C.c_float)
Get=C.CFUNCTYPE(C.c_float,Ptr,C.c_int32)
Process=C.CFUNCTYPE(None,Ptr,C.POINTER(C.POINTER(C.c_float)),C.POINTER(C.POINTER(C.c_float)),C.c_int32)
class Plugin:
    def __init__(self):
        self.lib=C.CDLL(str(root/'build/beatrepeat-native.so'))
        self.lib.VSTPluginMain.argtypes=[C.c_void_p];self.lib.VSTPluginMain.restype=Ptr
        self.fx=self.lib.VSTPluginMain(None)
        assert self.fx and self.fx.contents.magic==0x56737450
        self.d=Dispatch(self.fx.contents.dispatcher)
        self.set=Set(self.fx.contents.setParameter);self.get=Get(self.fx.contents.getParameter)
        self.process=Process(self.fx.contents.processReplacing)
        self.d(self.fx,0,0,0,None,0);self.d(self.fx,10,0,0,None,44100);self.d(self.fx,12,0,1,None,0)
    def display(self,i):
        b=C.create_string_buffer(8);self.d(self.fx,7,i,0,b,0);return b.value.decode()
    def close(self): self.d(self.fx,1,0,0,None,0)
if __name__=='__main__':
    p=Plugin();e=p.fx.contents
    assert C.sizeof(Effect)==192 and e.numParams==8 and e.numInputs==e.numOutputs==2
    assert e.initialDelay==0 and e.uniqueID==0x45754272
    for i in range(8): assert p.d(p.fx,26,i,0,None,0)==(i<6)
    p.set(p.fx,0,1);assert p.display(0)=='450.0'
    l=(C.c_float*128)(*[i/128 for i in range(128)])
    r=(C.c_float*128)(*[-i/256 for i in range(128)])
    a=(C.c_float*128)();b=(C.c_float*128)()
    ins=(C.POINTER(C.c_float)*2)(l,r);outs=(C.POINTER(C.c_float)*2)(a,b)
    p.process(p.fx,ins,outs,128)
    assert list(a)==list(l) and list(b)==list(r)
    p.close();print('PASS actual shared-library load, ABI metadata, controls and stereo audio')
