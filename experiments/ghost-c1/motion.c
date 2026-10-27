/* SPDX-License-Identifier: GPL-3.0-only. Shared eight-source clock; no per-route timer. */
#include "c1.h"
#include <math.h>
static float rnd(unsigned seed,uint64_t cycle,unsigned domain){return (ghost_random(seed,cycle,domain)>>8)*(1.f/16777216.f);}
float c1_motion(C1 *c,unsigned id,uint64_t sample,double beat,unsigned event) {
 MConfig *m=&c->state.source[id];MRuntime *r=&c->source[id];
 double time=m->sync?(beat-c->origin_beat)/m->rate:(sample-c->origin_sample)/(c->clock.rate*m->rate/1000);
 if(time<0)time=0;uint64_t cycle=(uint64_t)floor(time);float phase=(float)(time-cycle);
 if(!r->initialized){r->initialized=1;r->cycle=cycle;r->value=r->start=r->target=.5f;}
 if(m->hold)return m->minimum+(m->maximum-m->minimum)*r->value;
 int changed=r->cycle!=cycle;unsigned seed=m->seed^c->state.event.seed;
 if(changed||sample==c->origin_sample){
  r->cycle=cycle;
  if(rnd(seed,cycle,1024+id*4)<m->probability){
   r->start=r->value;
   if(m->type==M_WALK){float x=r->value+(rnd(seed,cycle,1025+id*4)-.5f)*.5f;x=fmodf(fabsf(x),2);r->target=x>1?2-x:x;}
   else r->target=rnd(seed,m->type==M_REPEAT?cycle%8:cycle,1025+id*4);
   if(m->type==M_STEP||m->type==M_WALK||m->type==M_REPEAT)r->value=r->target;
  }
 }
 switch(m->type){
 case M_SMOOTH:r->value=r->start+(r->target-r->start)*(phase*phase*(3-2*phase));break;
 case M_HOLD:if((changed||event)&&rnd(seed,cycle,1026+id*4)<m->probability)r->value=fminf(1,c->energy*4);break;
 case M_SINE:r->value=.5f+.5f*sinf(6.28318530718f*phase);break;
 case M_TRIANGLE:r->value=1-fabsf(2*phase-1);break;
 case M_GATE:r->value=rnd(seed,cycle,1027+id*4)<m->probability&&phase<.5f?1:0;break;
 default:break;
 }
 return m->minimum+(m->maximum-m->minimum)*r->value;
}
