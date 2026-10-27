/* GPL-3.0-only. Real final VST factory/control stress, offline only. */
#include "vst2_abi.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
extern AEffect *VSTPluginMain(audioMasterCallback);
static VstTimeInfo clock_info;
static intptr_t host(AEffect *f,int32_t op,int32_t i,intptr_t n,void *p,float x){(void)f;(void)i;(void)n;(void)p;(void)x;return op==audioMasterGetTime?(intptr_t)&clock_info:0;}
int main(void){
 AEffect *f=VSTPluginMain(host);assert(f&&f->numParams==126&&f->numPrograms==16&&f->uniqueID==0x47485354);
 f->dispatcher(f,effOpen,0,0,NULL,0);f->dispatcher(f,effSetSampleRate,0,0,NULL,44100);f->dispatcher(f,effMainsChanged,0,1,NULL,0);
 float l[128],r[128],a[128],b[128],*in[]={l,r},*out[]={a,b};
 for(unsigned k=0;k<3200;++k){
  clock_info.tempo=75+k%180;clock_info.flags=kVstTempoValid|kVstPpqPosValid|((k/71)%3?kVstTransportPlaying:0);clock_info.ppqPos+=128./44100*clock_info.tempo/60;
  if(!(k%80)){unsigned p=8+(k/80)%8;char name[33];assert(f->dispatcher(f,effSetProgram,0,p,NULL,0));assert(f->dispatcher(f,effGetProgram,0,0,NULL,0)==p);f->dispatcher(f,effGetProgramName,0,0,name,0);}
  f->setParameter(f,124,(k%100)/100.f);f->setParameter(f,125,(k%81)/80.f);
  f->setParameter(f,55,(k%101)/100.f);f->setParameter(f,70,(k%89)/88.f);
  if(k%31==0)f->setParameter(f,4,1);if(k%47==0)f->setParameter(f,4,0);
  if(k%59==0)f->setParameter(f,10,1);if(k%101==0)f->setParameter(f,11,1);if(k%103==0)f->setParameter(f,11,0);
  if(k%137==0)f->setParameter(f,56,1);
  for(unsigned i=0;i<128;++i){l[i]=.25f*sinf((k*128+i)*.021f);r[i]=.2f*cosf((k*128+i)*.027f);}
  f->processReplacing(f,in,out,128);for(unsigned i=0;i<128;++i)assert(isfinite(a[i])&&isfinite(b[i])&&fabsf(a[i])<1&&fabsf(b[i])<1);
 }
 f->dispatcher(f,effMainsChanged,0,0,NULL,0);f->dispatcher(f,effClose,0,0,NULL,0);
 puts("PASS final product: 3200 blocks / 409600 frames; programs, transport, tempo, Punch/Motion, Capture/Freeze, Clean, headroom");return 0;
}
