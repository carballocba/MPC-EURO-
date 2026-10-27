/* SPDX-License-Identifier: GPL-3.0-only. Wall time measured outside DSP. */
#define _POSIX_C_SOURCE 200809L
#include "c1.h"
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
static C1 c;static Engine audio;static GAudio c0;static Engine baseline;
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
static int order(const void *a,const void *b){double x=*(const double*)a,y=*(const double*)b;return (x>y)-(x<y);}
static const char *names[]={"BeatRepeat-engine","C0","Motion","four-random","all-random","Buffer-Dice","Motion-Dice","Chaos25","Chaos50","Chaos100","Clean-max","tempo","transport","recall","simultaneous","Listen"};
int main(void){puts("scenario,rate,block,runs,mean_us,p95_us,p99_us,max_us,overruns,invalid,persistent_bytes,audio_callback_allocations");
 for(unsigned rate_id=0;rate_id<3;++rate_id)for(unsigned block_id=0;block_id<3;++block_id)for(unsigned scenario=0;scenario<16;++scenario){
  unsigned rate=(unsigned[]){44100,48000,96000}[rate_id],block=(unsigned[]){32,128,512}[block_id];float l[512],r[512],ol[512],or[512];double times[1000],sum=0;unsigned invalid=0,overruns=0;unsigned char preset[4096];
  c1_init(&c,rate);c1_bind(&c,&audio,1);ghost_audio_init(&c0,rate);engine_reset(&baseline,(float)rate,1);EConfig cfg=ghost_manual_defaults();cfg.gate=1;engine_control(&baseline,&cfg);C1State s=c.state;s.manual[C1_GATE]=1;
  if(scenario>=3){s.event.enabled=1;for(unsigned d=0;d<(scenario==3?4:C1_DESTS);++d)s.random[d].enabled=1;}
  if(scenario==2||scenario==6||scenario==14){s.motion=1;for(unsigned d=0;d<C1_DESTS;++d)s.route[d].enabled=1;}
  if(scenario>=7&&scenario<=10){s.chaos_on=1;s.chaos=scenario==7?.25f:scenario==8?.5f:1;}
  if(scenario==15)s.listen=1;
  c1_apply(&c,&s);size_t pn=c1_save(&c,preset,sizeof preset);
  GConfig g=ghost_defaults();g.enabled=1;ghost_configure(&c0.ghost,&g);
  for(unsigned k=0;k<1000;++k){for(unsigned j=0;j<block;++j){l[j]=.18f*sinf((k*block+j)*.07f);r[j]=.15f*cosf((k*block+j)*.09f);}
   double start=now();
   if(scenario==5||scenario==6)c1_dice(&c,scenario==5?1:2);
   if(scenario==10&&k==500)c1_set(&c,P_CLEAN,1);
   if(scenario==11)ghost_clock(&c.clock,60+(k%200),1,0,c.clock.beat);
   if(scenario==12)ghost_clock(&c.clock,120,(k/30)&1,k%30==0,0);
   if(scenario==13)c1_load(&c,preset,pn);
   if(scenario==14){c1_dice(&c,1);c1_dice(&c,2);c1_set(&c,P_CAPTURE,1);}
   if(scenario==0){for(unsigned j=0;j<block;++j){engine_tick(&baseline,l[j],r[j],120,&ol[j],&or[j]);}}
   else if(scenario==1)ghost_audio_process(&c0,l,r,ol,or,block,NULL,0);
   else c1_process(&c,l,r,ol,or,block,NULL,0);
   double dt=now()-start;times[k]=dt;sum+=dt;if(dt>block/(double)rate)++overruns;
   for(unsigned j=0;j<block;++j)if(!isfinite(ol[j])||!isfinite(or[j]))++invalid;
  }
  qsort(times,1000,sizeof(double),order);
  printf("%s,%u,%u,1000,%.3f,%.3f,%.3f,%.3f,%u,%u,%zu,0\n",names[scenario],rate,block,sum*1000,times[949]*1e6,times[989]*1e6,times[999]*1e6,overruns,invalid,scenario==0?sizeof(Engine):scenario==1?sizeof(GAudio):sizeof(C1Audio));
 }
 return 0;
}
