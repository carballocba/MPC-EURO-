/* SPDX-License-Identifier: GPL-3.0-only. Diagnostic, never loaded into the plugin. */
#define _POSIX_C_SOURCE 200809L
#include "c1.h"
#include "vst2_abi.h"
#include <time.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <dlfcn.h>
#include <string.h>
#include <errno.h>
static _Atomic unsigned quit;
static double stamp(clockid_t id){struct timespec t;if(clock_gettime(id,&t)){perror("clock_gettime");exit(2);}return t.tv_sec+t.tv_nsec*1e-9;}
static void *load(void *p){(void)p;volatile double x=.1;while(!atomic_load(&quit))for(unsigned i=0;i<1000;++i)x=x*1.000001+.000001;return NULL;}
static intptr_t host(AEffect *f,int32_t op,int32_t i,intptr_t n,void *p,float x){(void)f;(void)op;(void)i;(void)n;(void)p;(void)x;return 0;}
typedef struct {double wall,cpu;unsigned invalid;} Row;
int main(int argc,char **argv){if(argc!=3)return 2;unsigned workers=(unsigned)atoi(argv[2]);if(workers>8)return 2;pthread_t threads[8];for(unsigned i=0;i<workers;++i)if(pthread_create(&threads[i],NULL,load,NULL))return 2;
 void *lib=dlopen(argv[1],RTLD_NOW);if(!lib){fprintf(stderr,"%s\n",dlerror());return 2;}AEffect *(*entry)(audioMasterCallback)=dlsym(lib,"VSTPluginMain");if(!entry)return 2;
 unsigned count=10000;Row *rows=calloc(count,sizeof(*rows));if(!rows)return 2;
 puts("case,workers,iteration,callback_wall_us,thread_cpu_envelope_us,deadline_us,invalid");
 const char *cases[]={"empty-bracket","injected-sleep-shim","injected-cpu-shim","inactive","buffer-dice","dense-512","recall"};
 for(unsigned scenario=0;scenario<7;++scenario){AEffect *fx=NULL;float l[128],r[128],a[128],b[128];float *in[2]={l,r},*out[2]={a,b};for(unsigned i=0;i<128;++i){l[i]=.2f*sinf(i*.07f);r[i]=.2f*cosf(i*.09f);}
  unsigned runs=scenario==1||scenario==2?3:count;
  struct {int32_t n;intptr_t reserved;VstEvent *events[512];} batch={0};VstMidiEvent midi[512]={0};batch.n=512;
  unsigned char preset[8192];intptr_t pn=0;
  if(scenario>=3){fx=entry(host);if(!fx)return 2;fx->dispatcher(fx,effOpen,0,0,NULL,0);fx->dispatcher(fx,effSetSampleRate,0,0,NULL,48000);fx->dispatcher(fx,effMainsChanged,0,1,NULL,0);fx->setParameter(fx,1,1);
   if(scenario>=4){fx->setParameter(fx,49+P_GHOST,1);fx->setParameter(fx,49+P_CHAOS_ON,1);fx->setParameter(fx,49+P_CHAOS,1);}
   if(scenario==5){fx->setParameter(fx,49+P_MDEST,1.f/11);fx->setParameter(fx,49+P_ROUTE,1);fx->setParameter(fx,49+P_MOTION,1);fx->setParameter(fx,49+P_RATE,(5.f-.015625f)/(60000.f-.015625f));}
   fx->processReplacing(fx,in,out,128);void *p=NULL;pn=fx->dispatcher(fx,effGetChunk,0,0,&p,0);if(pn<=0||pn>8192)return 2;memcpy(preset,p,(size_t)pn);
   if(fx->numParams<124)batch.n=63;
   for(unsigned i=0;i<(unsigned)batch.n;++i){midi[i].type=1;midi[i].byteSize=sizeof(VstMidiEvent);midi[i].deltaFrames=(511-i)%128;midi[i].midiData[0]=0xb0;midi[i].midiData[1]=(unsigned char[]){22,25,28,29,31}[i%5];midi[i].midiData[2]=i%128;batch.events[i]=(VstEvent*)&midi[i];}
  }
  for(unsigned k=0;k<runs;++k){
   if(scenario==4)fx->setParameter(fx,49+P_BUFFER_DICE,1);
   /* Dispatcher costs excluded deliberately: callback attribution is the question. */
   if(scenario==5&&fx->dispatcher(fx,effProcessEvents,0,0,&batch,0)!=1)return 2;
   if(scenario==6&&fx->dispatcher(fx,effSetChunk,0,pn,preset,0)!=1)return 2;
   double c0=stamp(CLOCK_THREAD_CPUTIME_ID),w0=stamp(CLOCK_MONOTONIC);
   if(scenario==1){struct timespec delay={0,10000000};while(nanosleep(&delay,&delay)&&errno==EINTR){}}
   else if(scenario==2){volatile double x=.1;double target=stamp(CLOCK_THREAD_CPUTIME_ID)+.004;while(stamp(CLOCK_THREAD_CPUTIME_ID)<target)x=x*1.000001+.000001;}
   else if(scenario>=3)fx->processReplacing(fx,in,out,128);
   double w1=stamp(CLOCK_MONOTONIC),c1=stamp(CLOCK_THREAD_CPUTIME_ID);if(w1<w0||c1<c0)return 2;
   rows[k]=(Row){(w1-w0)*1e6,(c1-c0)*1e6,0};if(scenario>=3)for(unsigned i=0;i<128;++i)if(!isfinite(a[i])||!isfinite(b[i]))++rows[k].invalid;
  }
  /* No logging, sample allocation or sorting in any measured interval. */
  for(unsigned k=0;k<runs;++k)printf("%s,%u,%u,%.3f,%.3f,2666.667,%u\n",cases[scenario],workers,k,rows[k].wall,rows[k].cpu,rows[k].invalid);
  if(fx)fx->dispatcher(fx,effClose,0,0,NULL,0);
 }
 atomic_store(&quit,1);for(unsigned i=0;i<workers;++i)pthread_join(threads[i],NULL);free(rows);dlclose(lib);return 0;
}
