/* SPDX-License-Identifier: GPL-3.0-only. Native VST callback timing, no Python in measurements. */
#define _POSIX_C_SOURCE 200809L
#include "c1.h"
#include "vst2_abi.h"
#include <dlfcn.h>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
static VstTimeInfo clock_info;
static intptr_t host(AEffect *f,int32_t op,int32_t idx,intptr_t n,void *p,float x){(void)f;(void)idx;(void)n;(void)p;(void)x;return op==audioMasterGetTime?(intptr_t)&clock_info:0;}
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
static double cpu_now(void){struct timespec t;clock_gettime(CLOCK_THREAD_CPUTIME_ID,&t);return t.tv_sec+t.tv_nsec*1e-9;}
static int order(const void *a,const void *b){double x=*(const double*)a,y=*(const double*)b;return (x>y)-(x<y);}
static void set(AEffect *f,unsigned p,float x){f->setParameter(f,49+(int)p,x);}
int main(int argc,char **argv){if(argc!=2)return 1;void *lib=dlopen(argv[1],RTLD_NOW);if(!lib){fprintf(stderr,"%s\n",dlerror());return 1;}AEffect *(*entry)(audioMasterCallback)=dlsym(lib,"VSTPluginMain");size_t (*bytes)(void)=dlsym(lib,"ghost_c1_wrapper_bytes");if(!entry)return 1;
 puts("scenario,rate,block,runs,mean_us,p95_us,p99_us,max_us,overruns,invalid,persistent_bytes,mean_cpu_us,max_cpu_us,cpu_overruns,wall_only_overruns");
 for(unsigned scenario=0;scenario<19;++scenario){AEffect *f=entry(host);if(!f)return 1;f->dispatcher(f,effOpen,0,0,NULL,0);f->dispatcher(f,effSetSampleRate,0,0,NULL,48000);f->dispatcher(f,effMainsChanged,0,1,NULL,0);f->setParameter(f,1,1);
  clock_info=(VstTimeInfo){0};clock_info.tempo=120;clock_info.flags=kVstTempoValid|kVstPpqPosValid|kVstTransportPlaying;
  if(scenario>0)set(f,P_GHOST,1);if(scenario==2||scenario==6||scenario==14||scenario>=16){set(f,P_MDEST,4.f/11);set(f,P_ROUTE,1);set(f,P_MOTION,1);}if(scenario==15||scenario==17)set(f,P_LISTEN,1);
  if(scenario>=3){for(unsigned d=0;d<(scenario==3?4:12);++d){set(f,P_DEST,d/11.f);set(f,P_RANDOM,1);float a[1]={0},b[1]={0};float *i[2]={a,a},*o[2]={b,b};f->processReplacing(f,i,o,1);}}
  if(scenario>=7&&scenario<=10){set(f,P_CHAOS_ON,1);set(f,P_CHAOS,scenario==7?.25f:scenario==8?.5f:1);}
  if(scenario>=16){set(f,P_CHAOS_ON,1);set(f,P_CHAOS,1);set(f,P_RATE,(5.f-.015625f)/(60000.f-.015625f));}
  struct {int32_t numEvents;intptr_t reserved;VstEvent *events[512];} batch={0};VstMidiEvent midi[512]={0};batch.numEvents=scenario==17?512:63;
  for(unsigned j=0;j<(unsigned)batch.numEvents;++j){midi[j].type=1;midi[j].byteSize=sizeof(VstMidiEvent);midi[j].deltaFrames=(511-j)%128;midi[j].midiData[0]=0xb0;midi[j].midiData[1]=scenario==17?(unsigned char[]){22,25,28,29,31}[j%5]:1;midi[j].midiData[2]=j%128;batch.events[j]=(VstEvent*)&midi[j];}
  float l[128],r[128],a[128],b[128];float *in[2]={l,r},*out[2]={a,b};for(unsigned j=0;j<128;++j){l[j]=.2f*sinf(j*.1f);r[j]=.2f*cosf(j*.1f);}f->processReplacing(f,in,out,128);void *ptr=NULL;intptr_t size=f->dispatcher(f,effGetChunk,0,0,&ptr,0);unsigned char preset[8192];if(size>8192||size<=0)return 1;for(intptr_t j=0;j<size;++j)preset[j]=((unsigned char*)ptr)[j];
  double t[2000],sum=0,cpu_sum=0,cpu_max=0;unsigned over=0,invalid=0,cpu_over=0,wall_only=0;
  for(unsigned k=0;k<2000;++k){if(scenario==5||scenario==14)set(f,P_BUFFER_DICE,1);if(scenario==6||scenario==14)set(f,P_MOTION_DICE,1);if(scenario==10&&k==1000)set(f,P_CLEAN,1);if(scenario==11)clock_info.tempo=60+k%200;if(scenario==12)clock_info.flags=kVstTempoValid|kVstPpqPosValid|((k/30)&1?kVstTransportPlaying:0);if(scenario==13)f->dispatcher(f,effSetChunk,0,size,preset,0);
   double cpu_start=cpu_now(),start=now();if(scenario==16||scenario==17)f->dispatcher(f,effProcessEvents,0,0,&batch,0);f->processReplacing(f,in,out,128);t[k]=now()-start;double cpu=cpu_now()-cpu_start;cpu_sum+=cpu;if(cpu>cpu_max)cpu_max=cpu;sum+=t[k];if(cpu>128./48000)++cpu_over;if(t[k]>128./48000){++over;if(cpu<=128./48000)++wall_only;}for(unsigned j=0;j<128;++j)if(!isfinite(a[j])||!isfinite(b[j]))++invalid;clock_info.samplePos+=128;clock_info.ppqPos+=128./48000*clock_info.tempo/60;
  }
  qsort(t,2000,sizeof(double),order);printf("%u,48000,128,2000,%.3f,%.3f,%.3f,%.3f,%u,%u,%zu,%.3f,%.3f,%u,%u\n",scenario,sum*500,t[1899]*1e6,t[1979]*1e6,t[1999]*1e6,over,invalid,bytes?bytes():0,cpu_sum*500,cpu_max*1e6,cpu_over,wall_only);unsigned count=f->numParams;f->dispatcher(f,effClose,0,0,NULL,0);if(count==49)break;
 }
 dlclose(lib);return 0;
}
