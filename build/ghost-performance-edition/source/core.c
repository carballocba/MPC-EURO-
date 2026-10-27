/* SPDX-License-Identifier: GPL-3.0-only. Shared clock / temporary destinations. */
#include "c1.h"
#include <math.h>
#include <string.h>
static const float lows[C1_DESTS]={5,0,0,0,0,50,0,-24,-12,0,0,0};
static const float highs[C1_DESTS]={450,1,1,1,1,2000,1,24,12,1,1,1};
static float clamp(float x,float lo,float hi){return fmaxf(lo,fminf(hi,x));}
static float rnd(const C1 *c,uint64_t n,unsigned domain){return (ghost_random(c->performance_owner?c->modulation_seed:c->state.event.seed,n,domain)>>8)*(1.f/16777216.f);}
static int range(double x,double lo,double hi){return isfinite(x)&&x>=lo&&x<=hi;}
static int discrete(unsigned d){return d==C1_CAPTURE||d==C1_FREEZE||d==C1_REVERSE||d==C1_GATE;}
static int buffer_dest(unsigned d){return d==C1_CAPTURE||d==C1_FREEZE||(d>=C1_POSITION&&d<=C1_PITCH);}
C1State c1_defaults(void){C1State s={0};s.event=ghost_defaults();s.buffer=1;s.sensitivity=3;s.spacing=100;s.listen_probability=1;s.listen_capture=s.listen_repeat=1;
 s.manual[C1_LENGTH]=100;s.manual[C1_SIZE]=1000;s.manual[C1_MIX]=1;
 for(unsigned d=0;d<C1_DESTS;++d){s.random[d]=(GDestination){0,1,1,lows[d],highs[d],1,0};s.route[d]=(MRoute){0,d%8,1,lows[d],highs[d],1,5};}
 for(unsigned d=0;d<4;++d)s.random[d]=s.event.destination[d];
 for(unsigned i=0;i<C1_SOURCES;++i)s.source[i]=(MConfig){i,0,0,i+1,1000,1,0,1,1};return s;}
int c1_valid(const C1State *s){if(!s||(s->legacy_size&&s->legacy_size!=48&&s->legacy_size!=532)||s->motion>1||s->buffer>1||s->chaos_on>1||s->listen>1||s->listen_capture>1||s->listen_repeat>1||s->quantized>1||s->destination>=C1_DESTS||s->motion_destination>=C1_DESTS||s->source_selected>=8||s->event.seed>65535||!range(s->chaos,0,1)||!range(s->sensitivity,1,10)||!range(s->spacing,10,2000)||!range(s->listen_probability,0,1))return 0;
 Ghost g;ghost_init(&g,44100);GConfig e=s->event;for(unsigned i=0;i<4;++i)e.destination[i]=s->random[i];if(!ghost_configure(&g,&e))return 0;
 for(unsigned d=0;d<C1_DESTS;++d){const GDestination *r=&s->random[d];const MRoute *m=&s->route[d];
  if(s->locked[d]>1||!range(s->manual[d],lows[d],highs[d])||r->enabled>1||r->interval<1||r->interval>64||!range(r->probability,0,1)||!range(r->minimum,lows[d],highs[d])||!range(r->maximum,r->minimum,highs[d])||!range(r->depth,0,1)||!range(r->smooth_ms,0,2000)||m->enabled>1||m->source>=8||!range(m->depth,0,1)||!range(m->minimum,lows[d],highs[d])||!range(m->maximum,m->minimum,highs[d])||!range(m->probability,0,1)||!range(m->smooth_ms,0,2000))return 0;
  if(discrete(d)&&((s->manual[d]!=0&&s->manual[d]!=1)||r->minimum!=0||r->maximum!=1||r->depth!=1||r->smooth_ms!=0))return 0;
 }
 for(unsigned i=0;i<8;++i){const MConfig *m=&s->source[i];if(m->type>7||m->sync>1||m->hold>1||m->seed>65535||!range(m->rate,m->sync?1./64:5,m->sync?64:60000)||!range(m->depth,0,1)||!range(m->minimum,0,1)||!range(m->maximum,m->minimum,1)||!range(m->probability,0,1))return 0;}return 1;
}
static GConfig event_config(const C1State *s){GConfig e=s->event;for(unsigned d=0;d<4;++d){e.destination[d]=s->random[d];if(s->locked[d]||(!s->buffer&&buffer_dest(d)))e.destination[d].enabled=0;}
 if(s->chaos_on){float x=s->chaos;e.density=s->event.density?(unsigned)fmaxf(1,roundf(s->event.density*(.15f+.85f*sqrtf(x)))):0;e.probability*=.2f+.8f*x;e.duration_ms*=.5f+x;e.rest_ms=fmaxf(e.rest_ms,10+10*(1-x));
  for(unsigned d=0;d<2;++d)e.destination[d].depth*=.1f+.9f*x*x;
  e.destination[0].maximum=e.destination[0].minimum+(e.destination[0].maximum-e.destination[0].minimum)*(1-.8f*x);
 }
 return e;}
static EConfig manual_config(const C1State *s){EConfig e=ghost_manual_defaults();e.ms=s->manual[0];e.fracture=s->manual[1];e.freeze=(unsigned)s->manual[3];e.position=s->manual[4];e.buffer_ms=s->manual[5];e.reverse=(unsigned)s->manual[6];e.bend=s->manual[7];e.pitch=s->manual[8];e.corrupt=s->manual[9];e.gate=(unsigned)s->manual[11];e.quantized=s->quantized;return e;}
int c1_manual(C1 *c,unsigned d,float value){
 if(d>=C1_DESTS||!range(value,lows[d],highs[d]))return 0;
 if(discrete(d))value=value>=.5f;
 c->state.manual[d]=value;c->manual_mask|=1u<<d;if(c->performance_owner)c->manual_until[d]=c->clock.sample+(uint64_t)(c->clock.rate*.5);
 if((d==C1_GATE||d==C1_FREEZE)&&value>=.5f)c->clean_latched=0;
 EConfig manual=manual_config(&c->state);unsigned mask=d<4?1u<<d:d==C1_GATE?G_GATE_OVERRIDE:0;
 return ghost_manual(&c->clock,&manual,mask);
}
int c1_init(C1 *c,double rate){if(!c||!range(rate,16000,96000))return 0;memset(c,0,sizeof(*c));ghost_init(&c->clock,rate);c->state=c1_defaults();c->mix=1;c->depth_step=1.f/((float)rate*.005f);c->mix_step=1.f/((float)rate*.002f);c->fast_coefficient=1-expf(-1.f/((float)rate*.002f));c->slow_coefficient=1-expf(-1.f/((float)rate*.05f));c->onset_armed=1;for(unsigned d=0;d<C1_DESTS;++d)c->route_value[d]=c->state.manual[d];return 1;}
void c1_bind(C1 *c,Engine *engine,unsigned render_audio){c->engine=engine;c->render_audio=render_audio;if(render_audio)engine_reset(engine,(float)c->clock.rate,1);}
int c1_apply(C1 *c,const C1State *s){if(!c1_valid(s))return 0;GConfig e=event_config(s);
 if(!c->performance_owner&&memcmp(&c->clock.config,&e,sizeof e)&&!ghost_configure(&c->clock,&e))return 0;
 for(unsigned i=0;i<8;++i)if(memcmp(&s->source[i],&c->state.source[i],sizeof(MConfig)))c->source[i].initialized=0;
 /* Explicitly re-arming Motion/one route releases its earlier manual lease.
  * Subsequent manual edits still win until the performer re-arms or an event. */
 for(unsigned d=0;d<C1_DESTS;++d)if(s->motion&&s->route[d].enabled&&
    (!c->state.motion||!c->state.route[d].enabled))c->manual_mask&=~(1u<<d);
 /* Listen re-arm is an explicit request to let onsets control Repeat again. */
 if(s->listen&&s->listen_repeat&&(!c->state.listen||!c->state.listen_repeat))c->manual_mask&=~(1u<<C1_GATE);
 c->state=*s;EConfig m=manual_config(s);if(memcmp(&m,&c->clock.manual,sizeof m))ghost_manual(&c->clock,&m,0);if(s->event.enabled||s->motion||s->listen)c->clean_latched=0;return 1;}
void c1_dice(C1 *c,unsigned family){uint64_t n=++c->dice_index;
 if(family==2){for(unsigned i=0;i<8;++i){int unlocked=0;for(unsigned d=0;d<C1_DESTS;++d)if(c->state.route[d].source==i&&!c->state.locked[d])unlocked=1;
   /* Do not change a shared source if any locked route refers to it. */
   int protected=0;for(unsigned d=0;d<C1_DESTS;++d)if(c->state.route[d].source==i&&c->state.locked[d])protected=1;
   if(!unlocked||protected)continue;MConfig *m=&c->state.source[i];m->type=ghost_random(c->state.event.seed,n,3000+i)%8;m->sync=1;m->rate=.25f*(1u<<(ghost_random(c->state.event.seed,n,3100+i)%5));m->depth=.2f+.6f*rnd(c,n,3200+i);c->source[i].initialized=0;}return;}
 for(unsigned d=0;d<C1_DESTS;++d){if((family==0&&d!=c->state.destination)||(family==1&&!buffer_dest(d))||c->state.locked[d]||(!c->state.buffer&&buffer_dest(d)))continue;
  const GDestination *r=&c->state.random[d];float x=rnd(c,n,3300+d);
  if(discrete(d))c->dice_value[d]=d==C1_CAPTURE?1:x>.5f;else c->dice_value[d]=r->minimum+(r->maximum-r->minimum)*x;
  c->dice_mask|=1u<<d;
 }
 c->lease_until=c->clock.sample+(uint64_t)ceil(fmaxf(1,c->state.event.duration_ms)*c->clock.rate/1000);
}
static void set_value(EConfig *e,float *mix,unsigned d,float x){switch(d){case C1_LENGTH:e->ms=x;break;case C1_BREAK:e->fracture=x;break;case C1_FREEZE:e->freeze=x>=.5f;break;case C1_POSITION:e->position=x;break;case C1_SIZE:e->buffer_ms=x;break;case C1_REVERSE:e->reverse=x>=.5f;break;case C1_BEND:e->bend=x;break;case C1_PITCH:e->pitch=x;break;case C1_CORRUPT:e->corrupt=x;break;case C1_MIX:*mix=x;break;case C1_GATE:e->gate=x>=.5f;break;default:break;}}
static float approach(float x,float y,float step){return x<y?fminf(x+step,y):fmaxf(x-step,y);}
unsigned c1_commit_commands(C1 *c){unsigned commands=c->commands;c->commands=0;
  if(commands&1){ghost_clean(&c->clock);c->state.event.enabled=c->state.motion=c->state.listen=0;c->state.manual[3]=c->state.manual[11]=0;c->dice_mask=c->random_mask=c->pending_capture=c->manual_mask=0;c->clean_latched=1;}
  else {if(commands&2){ghost_reset(&c->clock);memset(c->source,0,sizeof c->source);c->origin_sample=c->clock.sample;c->origin_beat=c->clock.beat;c->manual_mask=0;}if(commands&4)ghost_capture(&c->clock);}
return commands;}
static float mod_value(const EConfig *e,float mix,unsigned d){const float v[]={e->ms,e->fracture,0,(float)e->freeze,e->position,e->buffer_ms,(float)e->reverse,e->bend,e->pitch,e->corrupt,mix,(float)e->gate};return v[d];}
float c1_modulate(C1 *c,const GFrame *f,unsigned onset,EConfig *config){
 if(c->performance_owner)for(unsigned d=0;d<C1_DESTS;++d)if(!c->state.random[d].enabled)c->random_mask&=~(1u<<d);
if(f->flags&G_START){if(!c->performance_owner)c->manual_mask=0;c->random_mask=0;++c->accepted;
   for(unsigned d=c->performance_owner?0:4;d<C1_DESTS;++d){GDestination *q=&c->state.random[d];if((c->performance_owner&&(d==C1_CAPTURE||d==C1_FREEZE||d==C1_GATE))||!q->enabled||q->depth<=0||c->state.locked[d]||(!c->state.buffer&&buffer_dest(d))||f->opportunity%q->interval||rnd(c,f->opportunity,5000+d)>=q->probability)continue;
    float x=discrete(d)?(rnd(c,f->opportunity,5100+d)>.5f):q->minimum+(q->maximum-q->minimum)*rnd(c,f->opportunity,5100+d);
    float depth=q->depth*(c->state.chaos_on?.1f+.9f*c->state.chaos*c->state.chaos:1);
    c->auto_value[d]=discrete(d)?x:clamp(clamp(c->state.manual[d],q->minimum,q->maximum)+depth*(x-clamp(c->state.manual[d],q->minimum,q->maximum)),q->minimum,q->maximum);c->random_mask|=1u<<d;
   }}
  if(!f->active)c->random_mask=0;if(c->clock.sample>c->lease_until)c->dice_mask=0;
  if(c->state.motion&&(!(f->sample&31)||(f->flags&G_START)||onset))for(unsigned i=0;i<8;++i)c->motion_value[i]=c1_motion(c,i,f->sample,c->clock.beat,(f->flags&G_START)||onset);
  float target_mix=c->state.manual[C1_MIX];EConfig effective=*config;c->motion_active=0;
  for(unsigned d=0;d<C1_DESTS;++d){if((c->performance_owner&&(d==C1_CAPTURE||d==C1_FREEZE||d==C1_GATE))||c->state.locked[d]||(c->manual_mask&(1u<<d))||(!c->state.buffer&&buffer_dest(d))){c->edge_mask&=~(1u<<d);if(c->performance_owner){c->automation_mask&=~(1u<<d);c->route_value[d]=mod_value(config,c->state.manual[C1_MIX],d);}continue;}
   MRoute *q=&c->state.route[d];float x=c->state.manual[d],lo=q->minimum,hi=q->maximum,smoothing=q->smooth_ms;unsigned use=0;
   if(c->state.motion&&q->enabled&&rnd(c,c->source[q->source].cycle,6000+d)<q->probability){float value=clamp(c->motion_value[q->source],0,1);float proposed=q->minimum+(q->maximum-q->minimum)*value;
    float depth=q->depth*c->state.source[q->source].depth;x=clamp(clamp(x,q->minimum,q->maximum)+depth*(proposed-clamp(x,q->minimum,q->maximum)),q->minimum,q->maximum);use=1;c->motion_active=1;}
   if(f->active&&d<4&&(c->clock.destinations&(1u<<d)))use=0; /* event > Motion */
   if(c->random_mask&(1u<<d)){x=c->auto_value[d];use=1;lo=c->state.random[d].minimum;hi=c->state.random[d].maximum;smoothing=c->state.random[d].smooth_ms;}
   if(c->dice_mask&(1u<<d)){x=c->dice_value[d];use=1;lo=c->state.random[d].minimum;hi=c->state.random[d].maximum;smoothing=5;}
   if(!use){c->edge_mask&=~(1u<<d);if(c->performance_owner){if((c->automation_mask&(1u<<d))&&!discrete(d)){float target=mod_value(config,c->state.manual[C1_MIX],d);float step=(highs[d]-lows[d])/((float)c->clock.rate*.005f);c->route_value[d]=approach(c->route_value[d],target,step);set_value(&effective,&target_mix,d,c->route_value[d]);if(c->route_value[d]==target)c->automation_mask&=~(1u<<d);}continue;}if(q->enabled&&!discrete(d)&&!(f->active&&d<4&&(c->clock.destinations&(1u<<d)))){float step=(highs[d]-lows[d])/((float)c->clock.rate*.005f);c->route_value[d]=approach(c->route_value[d],c->state.manual[d],step);set_value(&effective,&target_mix,d,c->route_value[d]);}continue;}
   if(c->performance_owner)c->automation_mask|=1u<<d;
   if(discrete(d)){unsigned high=x>=.5f,old=(c->edge_mask>>d)&1u;if(d==C1_CAPTURE){if(high&&!old){c->pending_capture=1;c->pending_manual=0;c->pending_until=c->clock.sample+(uint64_t)(c->state.event.duration_ms*c->clock.rate/1000);}}else {if(d==C1_FREEZE||d==C1_GATE)high|=c->state.manual[d]>=.5f;set_value(&effective,&target_mix,d,(float)high);}if(high)c->edge_mask|=1u<<d;else c->edge_mask&=~(1u<<d);}
   else {float milliseconds=smoothing;float step=milliseconds>0?(hi-lo)/((float)c->clock.rate*milliseconds/1000):INFINITY;
    c->route_value[d]=clamp(approach(clamp(c->route_value[d],lo,hi),x,step),lo,hi);set_value(&effective,&target_mix,d,clamp(c->route_value[d],lows[d],highs[d]));}
  }

 *config=effective;return target_mix;
}
unsigned c1_process(C1 *c,const float *l,const float *r,float *ol,float *or,unsigned frames,C1Trace *trace,unsigned capacity){unsigned written=0;c->capture_requested=c->control_dirty=0;
 for(unsigned k=0;k<frames;++k){unsigned commands=c1_commit_commands(c);
  float il=l&&isfinite(l[k])?l[k]:0,ir=r&&isfinite(r[k])?r[k]:il;
  float energy=fmaxf(fabsf(il),fabsf(ir));c->fast+= (energy-c->fast)*c->fast_coefficient;c->slow+=(energy-c->slow)*c->slow_coefficient;if(fabsf(c->fast)<1e-25f)c->fast=0;if(fabsf(c->slow)<1e-25f)c->slow=0;c->energy=clamp(c->fast,0,1);
  unsigned onset=0;
  if(c->state.listen){if(c->fast<c->slow*1.2f+.002f)c->onset_armed=1;
   if(c->onset_armed&&c->fast>c->slow*(1.2f+.4f*c->state.sensitivity)+.004f&&c->clock.sample-c->last_onset>=(uint64_t)(c->state.spacing*c->clock.rate/1000)){
    c->last_onset=c->clock.sample;c->onset_armed=0;++c->onsets;
    if(rnd(c,c->onsets,4000)<c->state.listen_probability){onset=1;if(c->state.listen_capture&&c->state.buffer)c->pending_capture=1;c->pending_manual=0;c->pending_until=c->clock.sample+(uint64_t)(c->state.event.duration_ms*c->clock.rate/1000);
     if(c->state.listen_repeat){c->dice_mask|=1u<<C1_GATE;c->dice_value[C1_GATE]=1;c->lease_until=c->clock.sample+(uint64_t)(c->state.event.duration_ms*c->clock.rate/1000);}}
   }
  }
  GFrame f;ghost_tick(&c->clock,&f);if(f.flags&(G_START|G_END|G_MANUAL|G_CLEAN|G_RECONFIGURE)||commands||onset)c->control_dirty=1;EConfig effective=f.effective;float target_mix=c1_modulate(c,&f,onset,&effective);
  if(f.flags&G_CAPTURE_PULSE){c->pending_capture=1;c->pending_manual=(f.flags&G_CAPTURE_MANUAL)!=0;c->pending_until=c->clock.sample+(uint64_t)(c->state.event.duration_ms*c->clock.rate/1000);}
  if((commands&1)||(c->pending_capture&&!c->pending_manual&&c->clock.sample>c->pending_until))c->pending_capture=0;
  unsigned acquired=0;
  if(!c->engine){c->last_effective=effective;c->last_mix=target_mix;continue;}
  if(c->pending_capture&&!(c->engine->r.playing&&c->engine->r.voice.bank==(int)c->engine->r.live)){acquired=c->render_audio?(engine_capture(c->engine)?2:1):1;c->pending_capture=0;}
  if(acquired)c->capture_requested=1;c->last_effective=effective;c->last_mix=target_mix;
  if(c->render_audio){
  if((!(f.sample&31)||f.flags&(G_START|G_END|G_MANUAL|G_CLEAN|G_RECONFIGURE)||commands||acquired||onset))engine_control(c->engine,&effective);
  float wl=il,wr=ir;engine_tick(c->engine,il,ir,(float)c->clock.tempo,&wl,&wr);
  if(c->engine->r.playing){c->release[0]=wl;c->release[1]=wr;}else if(c->depth>0){wl=c->release[0];wr=c->release[1];}
  c->depth=approach(c->depth,c->engine->r.playing?1:0,c->depth_step);c->mix=approach(c->mix,target_mix,c->mix_step);
  float wet=c->mix*c->depth,a=il*(1-wet)+wl*wet,b=ir*(1-wet)+wr*wet;
  if(ol)ol[k]=isfinite(a)&&fabsf(a)>1e-30f?a:0;if(or)or[k]=isfinite(b)&&fabsf(b)>1e-30f?b:0;
  }
  c->active=c->engine->r.playing;c->actual_freeze=c->engine->r.captured>=0&&effective.freeze;c->capture_acquired=acquired==2;
  if(acquired==2)c->visual_until=c->clock.sample+(uint64_t)(c->clock.rate*.12);
  c->status=c->clean_latched?S_CLEAN:c->clock.sample<c->visual_until?S_CAPTURE:c->actual_freeze?S_FREEZE:c->active?(c->state.event.enabled&&c->clock.active&&c->state.chaos_on&&c->state.chaos>.7f?S_CHAOS:c->motion_active?S_MOTION:S_REPEAT):c->motion_active?S_MOTION:c->state.listen?S_LISTEN:S_IDLE;
  if(trace&&(f.flags||commands||onset||acquired)){if(written<capacity)trace[written++]=(C1Trace){f.sample,f.flags|commands<<8,c->status,c->active,acquired,effective.ms,effective.fracture,effective.position,c->mix,c->energy};else ++c->trace_dropped;}
 }
 return written;
}
