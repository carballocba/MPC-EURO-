/* SPDX-License-Identifier: GPL-3.0-only. Bounded generative policy on the existing Ghost clock. */
#include "performance.h"
#include <math.h>
#include <string.h>
static float clip(float x,float a,float b){return fmaxf(a,fminf(b,x));}
static float random_unit(unsigned seed,uint64_t n,unsigned domain){return (ghost_random(seed,n,domain)>>8)*(1.f/16777216.f);}
void pe_init(Performance *p,unsigned enabled){memset(p,0,sizeof(*p));const float defaults[PE_CONTROLS]={0,.25f,.3f,.5256f,.7f,.25f,.05f,.4f,0,.5f,0,0,0};memcpy(p->p,defaults,sizeof(defaults));p->p[0]=enabled!=0;p->modern=enabled!=0;p->wet_gain=1;p->nominal=62.5f;p->window=UINT64_MAX;}
int pe_valid(const float *v,uint32_t variant){if(variant>65535)return 0;for(unsigned i=0;i<PE_CONTROLS;++i)if(!isfinite(v[i])||v[i]<0||v[i]>1)return 0;return v[0]==0||v[0]==1;}
void pe_set(Performance *p,unsigned i,float v){if(i>=PE_CONTROLS||!isfinite(v))return;v=clip(v,0,1);if(i==PE_DICE){if(v>=.5f){p->variant=(p->variant+1)&65535u;p->dirty=1;}p->dice_high=v>=.5f;return;}if(i==PE_MODE){v=v>=.5f;if(v){if(p->p[PE_MODE]<.5f)p->modern=1;p->stopped=0;}}if(i==PE_EDITOR)v=roundf(v*7)/7;p->p[i]=v;p->dirty=1;}
void pe_clean(Performance *p){p->p[PE_MODE]=0;p->was_mode=0;p->active=0;p->stopped=1;p->wet_gain=1;p->dirty=1;}
uint32_t pe_checksum(const unsigned char *b,size_t n){uint32_t h=2166136261u;for(size_t k=0;k<n;++k)h=(h^b[k])*16777619u;return h;}
/* Each event reserves its actual duration in at most two adjacent 16-slot windows. */
static void budget_window(Performance *p,uint64_t window){if(p->window==window)return;if(p->window!=UINT64_MAX&&window==p->window+1){p->used[0]=p->used[1];p->used[1]=0;}else p->used[0]=p->used[1]=0;p->window=window;}
static void event_config(Performance *,C1 *,EConfig *);
void pe_tick(Performance *p,C1 *c){
 Ghost *g=&c->clock;p->dirty=0;c->performance_owner=1;
 if(c1_commit_commands(c)&1){pe_clean(p);return;}
 if(p->p[PE_MODE]<.5f)return;
 if(!p->was_mode||p->rate!=g->rate){ghost_reset(g);p->origin=g->beat;p->window=UINT64_MAX;p->used[0]=p->used[1]=0;p->generation=0;p->was_mode=1;p->rate=g->rate;}
 if(c->clean_latched||p->stopped){p->wet_gain=1;return;}
 float intensity=p->p[PE_GLITCH],chaos=p->p[PE_CHAOS];
 if(intensity<=0&&g->active&&g->until>g->sample+g->rate*.005){g->until=g->sample+g->rate*.005;g->rest_until=g->until+g->rate*.01;p->dirty=1;}
 double now=g->config.beat_sync?g->beat:(double)g->sample;
 float evo=p->modern?p->p[PE_MOTION]:0;
 uint64_t epoch=g->opportunity/(16u*(1u+(unsigned)(7*(1-evo))));
 float drift=evo*(2*random_unit(c->state.event.seed,(uint64_t)p->variant*65536+epoch,8100)-1);
 float nominal=p->length,weight=p->p[PE_REPEAT]+p->p[PE_REVERSE]+p->p[PE_CUT];double duration=0,first=0;unsigned seed=c->state.event.seed;
 uint64_t opportunity=g->opportunity,window=opportunity/16,key=(uint64_t)p->variant*65536+(opportunity%16);
 if(g->playing&&now+1e-12>=g->next){
 GConfig config=ghost_defaults();config.enabled=1;config.beat_sync=c->state.event.beat_sync;config.density=intensity>0?(unsigned)fmaxf(1,roundf(16*powf(intensity,.65f))):0;config.seed=c->state.event.seed;config.distance=config.beat_sync?.25:125;config.jitter=0;
 double delta=config.beat_sync?60/g->tempo*.25:.125;double window_seconds=delta*16;
 budget_window(p,window);
 /* Acceptance is intentionally independent of CHAOS. Random decisions are motif/slot based. */
 seed=config.seed;
 float probability=c->state.event.probability*(.25f+.75f*intensity);

 config.probability=weight>0&&random_unit(seed,key,7100)<probability&&random_unit(seed,key,7101)>=.5f*p->p[PE_REST]?1:0;
 nominal=8*powf(50,p->p[PE_SIZE])*powf(2,drift*1.5f);
 if(config.beat_sync){float wanted=nominal,best=INFINITY;for(unsigned i=0;i<6;++i){float t=(float)(60000/g->tempo)*((1u<<i)/32.f);if(t<5||t>450)continue;float d=fabsf(logf(t/wanted));if(d<best){best=d;nominal=t;}}}
 p->nominal=nominal;
 double limit=window_seconds*.85*intensity;
 double remain=fmax(0,limit-p->used[0]);
 double available_next=fmax(0,limit-p->used[1]);
 double offset=(opportunity%16)*delta;first=window_seconds-offset;
 double available=fmin(first,remain);if(remain>=first)available+=available_next;
 duration=fmin(c->state.event.duration_ms/1000.,fmin((1+3*intensity)*nominal/1000.*powf(2,drift),fmin(2*60/g->tempo,available)));
 if(duration<.011)config.probability=0;
 config.duration_ms=(float)fmax(.1,duration*1000);config.rest_ms=(float)fmax(10,delta*1000*(.25+2*p->p[PE_REST])*(1-.5*intensity));
 /* Do not reconfigure/cancel an event on each macro movement. Phase remains owned by Ghost. */
 unsigned clock_changed=g->config.beat_sync!=config.beat_sync;g->config=config;if(clock_changed){ghost_reset(g);p->window=UINT64_MAX;}
 }
 GFrame f;ghost_tick(g,&f);p->dirty=(f.flags&(G_START|G_END|G_RECONFIGURE))!=0;
 if(f.flags&G_START){
  p->planned_ms=g->config.duration_ms;
  /* Extend only this Performance lease; compatible mode keeps the original 85%-interval cap. */
  g->until=(double)f.sample+duration*g->rate;g->rest_until=g->until+g->config.rest_ms*g->rate/1000;
  double here=fmin(duration,first);p->used[0]+=here;p->used[1]+=duration-here;
  uint64_t choice=key;if(random_unit(seed,key+window*16,7102)<chaos*.5f)choice+=window*16;
  float weights[3];for(unsigned i=0;i<3;++i)weights[i]=p->p[PE_REPEAT+i]*(1+evo*(2*random_unit(seed,(uint64_t)p->variant*65536+epoch,8110+i)-1)*.8f);
  float family=random_unit(seed,choice+(evo>0?epoch*16:0),7103)*(weights[0]+weights[1]+weights[2]);
  p->active_family=family<weights[0]?0:family<weights[0]+weights[1]?1:2;
  p->evolution_position=drift*.15f;
  float draw=random_unit(seed,choice,7104);int octave=0;
  if(draw<chaos/8)octave=-2;else if(draw<3*chaos/8)octave=-1;else if(draw>1-chaos/8)octave=2;else if(draw>1-3*chaos/8)octave=1;
  static const int pitch_steps[]={-7,0,7};p->pitch_offset=roundf(pitch_steps[ghost_random(seed,choice,7105)%3]*p->p[PE_MOTION]*chaos);
  p->length=clip(nominal*powf(2,(float)octave),5,450);p->generation=f.generation;++p->events;++p->families[p->active_family];
 }
 /* Keep effective envelopes in the audio owner; no host calls or rendering here. */
 float target=1;
 if(g->active&&p->active_family==2){double left=(g->until-g->sample)/g->rate;double age=p->planned_ms/1000.-left;double period=.015+.025*(1-intensity);double phase=fmod(fmax(0,age),period);float gate=phase<period*.5?0:1;
  if(age<.005||left<.005)gate=1;target=gate;}
 float step=1/(float)(g->rate*.005);p->wet_gain=p->wet_gain<target?fminf(target,p->wet_gain+step):fmaxf(target,p->wet_gain-step);
 if(!(g->sample&31)){
  double window_seconds=(g->config.beat_sync?60/g->tempo*.25:.125)*16;
  double limit=window_seconds*.85*intensity;p->effective_budget=limit>0?(float)clip((float)(p->used[0]/limit),0,1):0;
  for(unsigned d=0;d<C1_DESTS;++d)if(c->manual_until[d]&&g->sample>=c->manual_until[d]){c->manual_mask&=~(1u<<d);c->manual_until[d]=0;}
 }
 if(!(g->sample&31)){p->motion=0;if(p->p[PE_MOTION]>0&&g->active){double beats=pow(1024,p->p[PE_RATE])/64.;double phase=fmax(0,(g->beat-p->origin)/beats);p->motion=(float)(1-4*fabs((phase-floor(phase))-.5))*p->p[PE_MOTION];}
 }
 if(p->modern){
  unsigned mod=c->state.motion;for(unsigned d=0;d<C1_DESTS;++d)mod|=c->state.random[d].enabled;
  if(mod)p->mod_tail=(unsigned)(g->rate*.02);else if(p->mod_tail)--p->mod_tail;
  if(mod||p->mod_tail){c->modulation_seed=ghost_random(c->state.event.seed,p->variant,8120);EConfig effective=g->manual;event_config(p,c,&effective);c->last_mix=c1_modulate(c,&f,0,&effective);p->mod_config=effective;}
  else{c->automation_mask=0;c->last_mix=c->state.manual[C1_MIX];}
 }else c->last_mix=c->state.manual[C1_MIX];
 p->active=g->active;c->last_effective=f.effective;c->active=g->active;c->status=g->active?S_REPEAT:S_IDLE;c->control_dirty=p->dirty||!(f.sample&31);c->capture_requested=0;
 ++p->elapsed_samples;if(g->active)++p->active_samples;
}
static void event_config(Performance *p,C1 *c,EConfig *e){if(p->p[PE_MODE]<.5f||c->clean_latched)return;Ghost *g=&c->clock;
 if(!g->active)return;e->gate=1;e->time_grid=0;
 if(!c->state.locked[C1_LENGTH]&&!(c->manual_mask&(1u<<C1_LENGTH)))e->ms=clip(p->length*powf(2,p->motion*.25f),5,450);
 if(!c->state.locked[C1_POSITION]&&!(c->manual_mask&(1u<<C1_POSITION)))e->position=clip(e->position+p->motion*.15f+(p->modern?p->evolution_position:0),0,1);
 if(!c->state.locked[C1_PITCH]&&!(c->manual_mask&(1u<<C1_PITCH)))e->pitch=clip(e->pitch+p->pitch_offset,-12,12);
 if(p->active_family==0&&!c->state.locked[C1_BREAK]&&!(c->manual_mask&(1u<<C1_BREAK)))e->fracture=clip(e->fracture+.6f*p->p[PE_GLITCH],0,1);
 if(p->active_family==1&&!c->state.locked[C1_REVERSE]&&!(c->manual_mask&(1u<<C1_REVERSE)))e->reverse=1;
}
void pe_config(Performance *p,C1 *c,EConfig *e){
 event_config(p,c,e);
 if(!p->modern||p->p[PE_MODE]<.5f||c->clean_latched)return;
 unsigned m=c->automation_mask;EConfig *a=&p->mod_config;
 if(m&(1u<<C1_LENGTH)){e->ms=a->ms;e->time_grid=0;}if(m&(1u<<C1_BREAK))e->fracture=a->fracture;
 if(m&(1u<<C1_POSITION))e->position=a->position;if(m&(1u<<C1_SIZE))e->buffer_ms=a->buffer_ms;
 if(m&(1u<<C1_REVERSE))e->reverse|=a->reverse;if(m&(1u<<C1_BEND))e->bend=a->bend;
 if(m&(1u<<C1_PITCH))e->pitch=a->pitch;if(m&(1u<<C1_CORRUPT))e->corrupt=a->corrupt;
}
float pe_read(const Performance *p,unsigned i){if(i<PE_CONTROLS)return i==PE_DICE?0:p->p[i];if(i==PE_ACTIVITY)return p->was_mode&&p->p[PE_MODE]>=.5f&&p->active?(float)(p->active_family+1)/3:0;if(i==PE_VARIANT)return p->variant/65535.f;if(i==PE_LENGTH)return clip((p->length-5)/445,0,1);if(i==PE_BUDGET)return p->effective_budget;return 0;}
