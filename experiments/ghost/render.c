/* SPDX-License-Identifier: GPL-3.0-only. Original synthetic input, offline I/O only. */
#define _POSIX_C_SOURCE 200809L
#include "audio.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/utsname.h>
static const double pi=3.14159265358979323846;
static void put16(FILE *f,unsigned x){fputc(x&255,f);fputc((x>>8)&255,f);}
static void put32(FILE *f,unsigned x){put16(f,x);put16(f,x>>16);}
static FILE *open_file(const char *folder,const char *name){char path[2048];int n=snprintf(path,sizeof path,"%s/%s",folder,name);if(n<0||(size_t)n>=sizeof path){fprintf(stderr,"output path too long\n");exit(1);}FILE *f=fopen(path,"wb");if(!f){perror(path);exit(1);}return f;}
static FILE *wave(const char *folder,const char *name,unsigned rate,unsigned frames){FILE *f=open_file(folder,name);fwrite("RIFF",1,4,f);put32(f,36+frames*4);fwrite("WAVEfmt ",1,8,f);put32(f,16);put16(f,1);put16(f,2);put32(f,rate);put32(f,rate*4);put16(f,4);put16(f,16);fwrite("data",1,4,f);put32(f,frames*4);return f;}
static float input(unsigned k,unsigned ch,double rate) {
 double t=k/rate,p=fmod(t,.5),h=fmod(t,.125),sn=fmod(t+.5,1);
 double kick=.24*exp(-p*30)*sin(2*pi*(52*p+2*(1-exp(-p*40))));
 double noise=(ghost_random(777,k,99+ch)>>8)*(2./16777216)-1;
 double hat=.025*noise*exp(-h*140),snare=.085*noise*exp(-sn*28);
 double pad=.035*(sin(2*pi*130.8128*t+ch*.8)+sin(2*pi*164.8138*t+ch*.3));
 return (float)(kick+hat+snare+pad);
}
static GConfig scenario(unsigned which) {
 GConfig c=ghost_defaults();c.enabled=which!=0;c.density=8;c.probability=.85f;c.duration_ms=65;c.rest_ms=20;c.seed=47321;c.capture_cooldown_ms=200;
 if(which==1||which==3){c.destination[0]=(GDestination){1,1,1,8,110,1,0};c.destination[1]=(GDestination){1,1,.85f,0,.8f,1,3};}
 if(which==2||which==3){c.destination[2]=(GDestination){1,1,.4f,0,1,1,0};c.destination[3]=(GDestination){1,1,.35f,0,1,1,0};}
 return c;
}
static void write_samples(FILE *f,float *l,float *r,unsigned n){unsigned char data[512*4];for(unsigned k=0;k<n;++k){float v[2]={l[k],r[k]};for(unsigned c=0;c<2;++c){int x=(int)lroundf(fmaxf(-1,fminf(1,v[c]))*32767);data[k*4+c*2]=(unsigned)x&255;data[k*4+c*2+1]=((unsigned)x>>8)&255;}}if(fwrite(data,4,n,f)!=n){fprintf(stderr,"WAV write failed\n");exit(1);}}
static void render(const char *folder) {
 const unsigned rate=44100,total=rate*12;GAudio *a=calloc(1,sizeof(*a));if(!a)exit(1);
 for(unsigned mode=0;mode<3;++mode){const char *name=mode==0?"input.wav":mode==1?"manual.wav":"ghost.wav";
  ghost_audio_init(a,rate);ghost_audio_mix(a,.65f);
  FILE *f=wave(folder,name,rate,total),*trace=NULL;
  if(mode==2){trace=open_file(folder,"events.csv");fprintf(trace,"sample,seconds,opportunity,generation,flags,event_active,auto_freeze,capture_result,captured_frames,length_ms,break\n");}
  unsigned offset=0;float l[512],r[512],ol[512],or[512];GTrace events[64];
  while(offset<total){unsigned n=128;if(n>total-offset)n=total-offset;
   /* Scripted commands land on exact sample boundaries, independent of block size. */
   unsigned boundary=(offset/rate+1)*rate;if(n>boundary-offset)n=boundary-offset;
   if(offset%rate==0){unsigned second=offset/rate;EConfig m=a->ghost.manual;
    if(mode==1){
     if(second==1)m.gate=1;
     if(second==3){m.ms=30;m.fracture=.3f;}
     if(second==4)m.gate=0;
     if(second==5){ghost_capture(&a->ghost);m.freeze=1;}
     if(second==7)m.freeze=0;
     if(second==8)m.gate=1;
     if(second==9)m.gate=0;
     if(!ghost_manual(&a->ghost,&m,0))exit(1);
    }
    if(mode==2&&second==1){GConfig c=scenario(3);if(!ghost_configure(&a->ghost,&c))exit(1);}
    if(mode&&second==10)ghost_clean(&a->ghost);
   }
   for(unsigned k=0;k<n;++k){l[k]=input(offset+k,0,rate);r[k]=input(offset+k,1,rate);}
   unsigned count=ghost_audio_process(a,l,r,ol,or,n,events,64);
   if(trace)for(unsigned i=0;i<count;++i){GTrace *e=&events[i];fprintf(trace,"%llu,%.9f,%llu,%llu,%u,%u,%u,%u,%u,%.7g,%.7g\n",(unsigned long long)e->sample,e->sample/(double)rate,(unsigned long long)e->opportunity,(unsigned long long)e->generation,e->flags,e->active,e->freeze,e->capture_result,e->captured_frames,e->length_ms,e->fracture);}
   write_samples(f,ol,or,n);offset+=n;
  }
  if(fclose(f))exit(1);if(trace&&fclose(trace))exit(1);if(a->trace_dropped){fprintf(stderr,"trace overflow\n");exit(1);}printf("Rendered %s (12 s, original stereo input)\n",name);
 }
 free(a);
}
static double now(void){struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))exit(1);return t.tv_sec+t.tv_nsec/1e9;}
static int compare(const void *a,const void *b){double x=*(const double*)a,y=*(const double*)b;return (x>y)-(x<y);}
static void benchmark(const char *folder) {
 const unsigned rates[]={16000,44100,48000,96000},blocks[]={32,128,512},runs=1000;
 GAudio *a=calloc(1,sizeof(*a));double *times=malloc(runs*sizeof(double));if(!a||!times)exit(1);
 FILE *f=open_file(folder,"benchmark-native.json");struct utsname u;uname(&u);
 fprintf(f,"{\n  \"scope\": \"native offline adapter; not ARM or physical MPC performance\",\n  \"platform\": \"%s %s %s\",\n  \"ghost_bytes\": %zu, \"audio_adapter_bytes\": %zu, \"runs_per_case\": %u,\n  \"cases\": [\n",u.sysname,u.release,u.machine,sizeof(Ghost),sizeof(GAudio),runs);
 unsigned row=0;float l[512],r[512],ol[512],or[512];
 for(unsigned s=0;s<4;++s)for(unsigned b=0;b<3;++b)for(unsigned mode=0;mode<4;++mode){unsigned n=blocks[b],rate=rates[s];
  ghost_audio_init(a,rate);EConfig m=a->ghost.manual;m.gate=1;ghost_manual(&a->ghost,&m,0);
  GConfig c=scenario(mode);if(!ghost_configure(&a->ghost,&c))exit(1);
  for(unsigned k=0;k<n;++k){l[k]=input(k,0,rate);r[k]=input(k,1,rate);}
  for(unsigned k=0;k<200;++k)ghost_audio_process(a,l,r,ol,or,n,NULL,0);
  double total=0;for(unsigned k=0;k<runs;++k){double start=now();ghost_audio_process(a,l,r,ol,or,n,NULL,0);times[k]=(now()-start)*1000;total+=times[k];}
  qsort(times,runs,sizeof(double),compare);double deadline=n*1000./rate;
  fprintf(f,"%s    {\"sample_rate\": %u, \"block\": %u, \"scenario\": %u, \"mean_ms\": %.9f, \"p99_ms\": %.9f, \"p999_ms\": %.9f, \"max_ms\": %.9f, \"deadline_ms\": %.9f, \"max_deadline_fraction\": %.6f}",row++?",\n":"",rate,n,mode,total/runs,times[989],times[998],times[999],deadline,times[999]/deadline);
 }
 fprintf(f,"\n  ]\n}\n");if(fclose(f))exit(1);free(a);free(times);puts("Native benchmark written; no ARM/MPC conclusions.");
}
int main(int argc,char **argv){if(argc<2||argc>3){fprintf(stderr,"usage: render OUTPUT_DIRECTORY [--benchmark]\n");return 2;}if(argc==3){if(strcmp(argv[2],"--benchmark"))return 2;benchmark(argv[1]);}else render(argv[1]);return 0;}
