/* SPDX-License-Identifier: GPL-3.0-only. Concurrent production VST stress. */
#define _POSIX_C_SOURCE 200809L
#include "c1.h"
#include "vst2_abi.h"
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <assert.h>
#include <time.h>
extern AEffect *VSTPluginMain(audioMasterCallback);
static unsigned char preset[8192];static intptr_t preset_size;
static AEffect *fx;static _Atomic unsigned done;static VstTimeInfo clock_info;
static intptr_t host(AEffect *f,int32_t op,int32_t i,intptr_t n,void *p,float x){(void)f;(void)i;(void)n;(void)p;(void)x;return op==audioMasterGetTime?(intptr_t)&clock_info:0;}
static void *audio(void *unused){(void)unused;float a[128],b[128],l[128],r[128];float *in[2]={a,b},*out[2]={l,r};
 struct {int32_t numEvents;intptr_t reserved;VstEvent *events[512];} list={0};VstMidiEvent midi[512]={0};list.numEvents=512;
 for(unsigned i=0;i<512;++i){midi[i].type=1;midi[i].byteSize=sizeof(VstMidiEvent);midi[i].deltaFrames=(511-i)%128;midi[i].midiData[0]=0xb0;midi[i].midiData[1]=(unsigned char[]){22,25,28,29,31}[i%5];midi[i].midiData[2]=i%128;list.events[i]=(VstEvent*)&midi[i];}
 for(unsigned k=0;k<10000;++k){clock_info.tempo=60+k%241;clock_info.flags=kVstTempoValid|kVstPpqPosValid|((k/37)%3?kVstTransportPlaying:0);if(k%53==0)clock_info.ppqPos=0;
  for(unsigned i=0;i<128;++i){a[i]=.2f*sinf((k*128+i)*.13f);b[i]=.2f*cosf((k*128+i)*.11f);}
  assert(fx->dispatcher(fx,effProcessEvents,0,0,&list,0)==1);fx->processReplacing(fx,in,out,128);
  for(unsigned i=0;i<128;++i)assert(isfinite(l[i])&&isfinite(r[i]));clock_info.samplePos+=128;clock_info.ppqPos+=128./48000*clock_info.tempo/60;
 }
 atomic_store(&done,1);return NULL;}
int main(void){fx=VSTPluginMain(host);assert(fx);fx->dispatcher(fx,effOpen,0,0,NULL,0);fx->dispatcher(fx,effSetSampleRate,0,0,NULL,48000);fx->dispatcher(fx,effMainsChanged,0,1,NULL,0);
 fx->setParameter(fx,49+P_GHOST,1);fx->setParameter(fx,49+P_MOTION,1);fx->setParameter(fx,49+P_CHAOS_ON,1);fx->setParameter(fx,49+P_CHAOS,1);
 for(unsigned d=0;d<4;++d){fx->setParameter(fx,49+P_DEST,d/11.f);fx->setParameter(fx,49+P_RANDOM,1);}
 fx->setParameter(fx,49+P_MDEST,1.f/11);fx->setParameter(fx,49+P_ROUTE,1);fx->setParameter(fx,49+P_TYPE,4.f/7);fx->setParameter(fx,49+P_RATE,(5.f-.015625f)/(60000.f-.015625f));
 float zero[128]={0};float *buffers[2]={zero,zero};fx->processReplacing(fx,buffers,buffers,128);void *data=NULL;preset_size=fx->dispatcher(fx,effGetChunk,0,0,&data,0);assert(preset_size>0&&preset_size<=8192);for(intptr_t i=0;i<preset_size;++i)preset[i]=((unsigned char*)data)[i];
 pthread_t thread;assert(!pthread_create(&thread,NULL,audio,NULL));unsigned attempts=0,accepted=0;const struct timespec wait={0,100000};
 while(!atomic_load(&done)){
  fx->setParameter(fx,2,.5f);fx->setParameter(fx,8,.5f+1.f/128);fx->setParameter(fx,49+P_R0MIN,(attempts%30)/100.f);fx->setParameter(fx,49+P_R0MAX,.3f+(attempts%70)/100.f);
  fx->setParameter(fx,49+P_CHAOS,1);if(attempts%13==0)fx->setParameter(fx,49+P_CLEAN,1);if(attempts%13==1){fx->setParameter(fx,49+P_GHOST,1);fx->setParameter(fx,49+P_MOTION,1);}
  if(attempts%7==0){void *p=NULL;intptr_t n=fx->dispatcher(fx,effGetChunk,0,0,&p,0);(void)n;accepted+=fx->dispatcher(fx,effSetChunk,0,preset_size,preset,0)!=0;}
  fx->getParameter(fx,49+P_STATUS);++attempts;nanosleep(&wait,NULL);
 }
 pthread_join(thread,NULL);assert(accepted>0);fx->dispatcher(fx,effClose,0,0,NULL,0);printf("10000 blocks, 5120000 MIDI events, %u GUI gestures, %u recalls; finite output\n",attempts,accepted);return 0;}
