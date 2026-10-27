/* SPDX-License-Identifier: GPL-3.0-only. Phrase policy on C1's existing clock. */
#pragma once
#include "performance.h"
#include <string.h>
#include <math.h>
#define RR_FIRST 148u
#define RR_CONTROLS 6u
#define RR_COUNT 8u
#define RR_PARAMS 156u
/* mode: MANUAL, INDEPENDENT, PERFORMANCE, BOTH. Appended IDs only. */
typedef struct {
 float p[6],fragment_ms;double next_beat,last_beat,sample_rate;uint64_t step,manual_until,fragment_until,starts,ends,changes;
 unsigned initialized,on,remaining,applied,playing,actual,config_dirty;
} RandomRepeat;
static inline unsigned rr_mode(const RandomRepeat *r){return (unsigned)(r->p[0]*3+.5f);}
static inline unsigned rr_enabled(const RandomRepeat *r){unsigned m=rr_mode(r);return m==1||m==3;}
static inline void rr_init(RandomRepeat *r,unsigned performance){memset(r,0,sizeof(*r));const float p[6]={0,.55f,.8f,.6f,.4f,.5f};memcpy(r->p,p,sizeof p);r->p[0]=performance?2.f/3:0;r->fragment_ms=62.5f;}
static inline int rr_valid(const float *p){for(unsigned i=0;i<6;++i)if(!isfinite(p[i])||p[i]<0||p[i]>1)return 0;return fabsf(p[0]*3-roundf(p[0]*3))<.00001f;}
static inline float rr_draw(unsigned seed,uint64_t step,unsigned domain){return (ghost_random(seed,step,domain)>>8)*(1.f/16777216.f);}
static inline void rr_tick(RandomRepeat *r,C1 *c,Performance *p,Engine *e,unsigned manual){
 Ghost *g=&c->clock;if(r->sample_rate!=g->rate){if(r->sample_rate>0)r->manual_until=r->fragment_until=0;r->sample_rate=g->rate;r->initialized=0;}if(c->clean_latched){r->p[0]=0;p->p[PE_MODE]=0;}unsigned enabled=rr_enabled(r)&&!c->clean_latched&&!e->r.recording&&g->playing;
 if(!enabled){if(r->on)++r->ends;r->on=r->applied=r->initialized=0;e->r.repeat=manual;r->actual=manual;r->last_beat=g->beat;return;}
 if(!r->initialized||g->beat<r->last_beat||g->beat-r->last_beat>1){r->next_beat=g->beat;r->step=0;r->remaining=0;r->on=0;r->initialized=1;}
 r->last_beat=g->beat;/* BOTH retains RR density; ACTIVITY shapes Performance, zero still cancels RR. */
 float intensity=r->p[1]*(p->p[PE_MODE]>=.5f?(p->p[PE_GLITCH]>0?1:0):1);if(intensity<=0){if(r->on)++r->ends;r->on=r->remaining=0;}
 if(g->beat+1e-12>=r->next_beat){
  static const double divisions[6]={2,1,.5,.25,.125,.0625};double interval=divisions[(unsigned)lroundf(r->p[4]*5)];r->next_beat+=interval;
  /* Bounded catch-up after a seek; never iterate over missed events. */
  if(r->next_beat<g->beat)r->next_beat=g->beat+interval;
  uint64_t slot=r->step++%16,phrase=(r->step-1)/16;float evolution=p->p[PE_MOTION];unsigned seed=ghost_random(c->state.event.seed,p->variant,9200);
  uint64_t motif=rr_draw(seed,phrase,9201)<evolution?phrase:0;
  /* BOTH advances phrase keys even at zero evolution; INDEPENDENT is unchanged. */
  if(rr_mode(r)==3)motif=phrase;
  uint64_t key=motif*16+slot;

  if(r->remaining)--r->remaining;
  else if(r->on){r->on=0;++r->ends;r->remaining=(unsigned)(rr_draw(seed,key,9202)*(1+3*(1-intensity)));}
  else if(intensity>0&&rr_draw(seed,key,9203)<r->p[2]*(.25f+.75f*intensity)&&((slot*(1+(unsigned)(15*intensity)))%16)<(unsigned)ceilf(16*intensity)){
   r->on=1;++r->starts;r->remaining=(unsigned)(rr_draw(seed,key,9204)*(1+floorf(7*r->p[5])));
   float base=8*powf(50,p->p[PE_SIZE]),v=r->p[3]*(.5f+.5f*evolution);int jump=(int)lroundf((2*rr_draw(seed,key,9205)-1)*3);
   r->fragment_ms=fmaxf(8,fminf(400,base*powf(2,jump*v)));++r->changes;
  }
  if(r->on&&r->remaining>0&&r->p[3]>0&&rr_draw(seed,key,9206)<r->p[3]*evolution*.4f){
   float multiplier=rr_draw(seed,key,9207)<.5f?.5f:2;r->fragment_ms=fmaxf(8,fminf(400,r->fragment_ms*multiplier));++r->changes;
  }
  r->config_dirty=1;
 }
 r->applied=g->sample>=r->manual_until;e->r.repeat=r->applied?r->on:manual;r->actual=e->r.repeat;
}
static inline void rr_config(const RandomRepeat *r,const C1 *c,const Performance *p,EConfig *e){if(rr_enabled(r)&&c->clock.sample<r->fragment_until&&!c->clean_latched){e->ms=8*powf(50,p->p[PE_SIZE]);e->time_grid=0;return;}if(rr_enabled(r)&&r->applied&&r->on&&c->clock.sample>=r->fragment_until&&!c->clean_latched){e->ms=r->fragment_ms;e->time_grid=0;}}
