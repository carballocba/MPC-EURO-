/* SPDX-License-Identifier: GPL-3.0-only. One registry for DSP and GUI. */
#include "c1.h"
#include <math.h>
#define Q(k,n,a,b,d) {k,n,a,b,d,0}
#define R(k,n,a,b) {k,n,a,b,0,1}
const C1Param c1_params[P_COUNT]={
 Q("ghost","Ghost",0,1,0),Q("gate","Gate",0,1,0),Q("length","Length",5,450,100),Q("break","Break",0,1,0),Q("mix","Mix",0,1,1),
 Q("motion","Motion",0,1,0),Q("chaos","Chaos",0,1,0),Q("clean","Clean",0,1,0),Q("buffer","Buffer",0,1,1),Q("bufdice","BufDice",0,1,0),Q("motdice","MotDice",0,1,0),
 Q("dest","Dest",0,11,0),Q("random","Random",0,1,0),Q("minimum","Min",-24,2000,5),Q("maximum","Max",-24,2000,450),Q("depth","Depth",0,1,1),Q("prob","Prob",0,1,1),Q("interval","Intvl",1,64,1),Q("lock","Lock",0,1,0),
 Q("type","Type",0,7,0),Q("rate","Rate",.015625f,60000,1000),Q("mdepth","MDepth",0,1,1),Q("mmin","MMin",0,1,0),Q("mmax","MMax",0,1,1),Q("sync","Sync",0,1,0),Q("hold","Hold",0,1,0),Q("seed","Seed",0,65535,1),
 Q("density","Density",0,16,4),Q("chance","Chance",0,1,.75f),Q("distance","Dist",.015625f,60000,.25f),Q("duration","Dur",.1f,60000,60),Q("rest","Rest",0,60000,15),Q("reset","Reset",0,1,0),
 Q("capture","Capture",0,1,0),Q("freeze","Freeze",0,1,0),Q("position","Pos",0,1,0),Q("size","Size",50,2000,1000),Q("reverse","Reverse",0,1,0),Q("bend","Bend",-24,24,0),Q("pitch","Pitch",-12,12,0),Q("corrupt","Corrupt",0,1,0),
 Q("mdest","MDest",0,11,0),Q("route","Route",0,1,0),Q("listen","Listen",0,1,0),Q("sens","Sens",1,10,3),Q("spacing","Spacing",10,2000,100),Q("lprob","LProb",0,1,1),Q("lcap","LCap",0,1,1),Q("lrepeat","LRepeat",0,1,1),
 R("status","Status",0,7),R("active","Active",0,1),R("energy","Energy",0,1),R("take","Take",0,1),Q("clock","Clock",0,1,1),Q("timing","Timing",0,1,0),Q("chaoson","ChaosOn",0,1,0),Q("source","Source",0,7,0),Q("dice","Dice",0,1,0),
 Q("r0min","Len Min",5,450,15),Q("r0max","Len Max",5,450,125),
 Q("r1min","Brk Min",0,1,0),Q("r1max","Brk Max",0,1,1),
 Q("r4min","Pos Min",0,1,0),Q("r4max","Pos Max",0,1,1),
 Q("r5min","Buf Min",50,2000,50),Q("r5max","Buf Max",50,2000,2000),
 Q("r7min","Bnd Min",-24,24,-24),Q("r7max","Bnd Max",-24,24,24),
 Q("r8min","Pit Min",-12,12,-12),Q("r8max","Pit Max",-12,12,12),
 Q("r9min","Crp Min",0,1,0),Q("r9max","Crp Max",0,1,1),
 Q("r10min","Mix Min",0,1,0),Q("r10max","Mix Max",0,1,1),R("edit","Edit",0,5)
};
static const unsigned range_dest[]={0,1,4,5,7,8,9,10};
static int manual_id(unsigned p){switch(p){case P_GATE:return C1_GATE;case P_LENGTH:return C1_LENGTH;case P_BREAK:return C1_BREAK;case P_MIX:return C1_MIX;case P_FREEZE:return C1_FREEZE;case P_POSITION:return C1_POSITION;case P_SIZE:return C1_SIZE;case P_REVERSE:return C1_REVERSE;case P_BEND:return C1_BEND;case P_PITCH:return C1_PITCH;case P_CORRUPT:return C1_CORRUPT;default:return -1;}}
float c1_get(const C1 *c,unsigned p){
 if(p>=P_COUNT)return 0;if(p==P_EDIT)return c->edit_feedback;if(p>=P_R0MIN&&p<P_EDIT){unsigned d=range_dest[(p-P_R0MIN)/2];return (p-P_R0MIN)&1?c->state.random[d].maximum:c->state.random[d].minimum;}const C1State *s=&c->state;const GDestination *d=&s->random[s->destination];const MConfig *m=&s->source[s->source_selected];
 int id=manual_id(p);if(id>=0)return s->manual[id];
 switch(p){case P_GHOST:return s->event.enabled;case P_MOTION:return s->motion;case P_CHAOS:return s->chaos;case P_BUFFER:return s->buffer;
 case P_DEST:return s->destination;case P_RANDOM:return d->enabled;case P_MIN:return d->minimum;case P_MAX:return d->maximum;case P_DEPTH:return d->depth;case P_PROB:return d->probability;case P_INTERVAL:return d->interval;case P_LOCK:return s->locked[s->destination];
 case P_TYPE:return m->type;case P_RATE:return m->rate;case P_MDEPTH:return m->depth;case P_MMIN:return m->minimum;case P_MMAX:return m->maximum;case P_SYNC:return m->sync;case P_HOLD:return m->hold;case P_SEED:return s->event.seed;
 case P_DENSITY:return s->event.density;case P_CHANCE:return s->event.probability;case P_DISTANCE:return s->event.distance;case P_DURATION:return s->event.duration_ms;case P_REST:return s->event.rest_ms;
 case P_MDEST:return s->motion_destination;case P_ROUTE:return s->route[s->motion_destination].enabled;case P_LISTEN:return s->listen;case P_SENS:return s->sensitivity;case P_SPACING:return s->spacing;case P_LPROB:return s->listen_probability;case P_LCAP:return s->listen_capture;case P_LREPEAT:return s->listen_repeat;
 case P_STATUS:return c->status;case P_ACTIVE:return c->active;case P_ENERGY:return c->energy;case P_TAKE:return c->engine&&c->engine->r.captured>=0;case P_CLOCK:return s->event.beat_sync;case P_TIMING:return s->quantized;case P_CHAOS_ON:return s->chaos_on;case P_SOURCE:return s->source_selected;default:return 0;}
}
int c1_set(C1 *c,unsigned p,float v){
 if(p>=P_COUNT||c1_params[p].readonly||!isfinite(v)||v<c1_params[p].minimum||v>c1_params[p].maximum)return 0;
 if(p==P_CLEAN||p==P_RESET||p==P_CAPTURE||p==P_BUFFER_DICE||p==P_MOTION_DICE||p==P_PARAM_DICE){if(v<=0)return 1;
  if(p==P_CLEAN)c->commands|=1;else if(p==P_RESET)c->commands|=2;else if(p==P_CAPTURE)c->commands|=4;else c1_dice(c,p==P_BUFFER_DICE?1:p==P_MOTION_DICE?2:0);return 1;}
 int manual=manual_id(p);if(manual>=0)return c1_manual(c,(unsigned)manual,v);
 if(p>=P_R0MIN&&p<P_EDIT){C1State s=c->state;unsigned d=range_dest[(p-P_R0MIN)/2];GDestination *r=&s.random[d];c->edit_feedback=0;
  if((p-P_R0MIN)&1){r->maximum=v;if(r->minimum>v){r->minimum=v;c->edit_feedback=1;}}
  else {r->minimum=v;if(r->maximum<v){r->maximum=v;c->edit_feedback=1;}}
  s.route[d].minimum=r->minimum;s.route[d].maximum=r->maximum;return c1_apply(c,&s);
 }
 C1State s=c->state;GDestination *d=&s.random[s.destination];MConfig *m=&s.source[s.source_selected];int id=manual_id(p);
 if(id>=0){s.manual[id]=v;if(id==C1_GATE||id==C1_FREEZE||id==C1_REVERSE)s.manual[id]=v>=.5f;}
 else switch(p){
 case P_GHOST:s.event.enabled=v>=.5f;break;case P_MOTION:s.motion=v>=.5f;break;case P_CHAOS:s.chaos=v;break;case P_BUFFER:s.buffer=v>=.5f;break;
 case P_DEST:c->edit_feedback=(v==2||v==3||v==6||v==11)?2:0;s.destination=(unsigned)lroundf(v);s.motion_destination=s.destination;s.source_selected=s.route[s.destination].source;break;case P_RANDOM:d->enabled=v>=.5f;break;case P_MIN:d->minimum=v;s.route[s.destination].minimum=v;break;case P_MAX:d->maximum=v;s.route[s.destination].maximum=v;break;case P_DEPTH:d->depth=v;break;case P_PROB:d->probability=v;break;case P_INTERVAL:d->interval=(unsigned)lroundf(v);break;case P_LOCK:s.locked[s.destination]=v>=.5f;break;
 case P_TYPE:m->type=(unsigned)lroundf(v);break;case P_RATE:m->rate=v;break;case P_MDEPTH:m->depth=v;break;case P_MMIN:m->minimum=v;if(m->maximum<v){m->maximum=v;c->edit_feedback=1;}break;case P_MMAX:m->maximum=v;if(m->minimum>v){m->minimum=v;c->edit_feedback=1;}break;case P_SYNC:m->sync=v>=.5f;if(m->sync&&m->rate>64)m->rate=1;if(!m->sync&&m->rate<5)m->rate=1000;break;case P_HOLD:m->hold=v>=.5f;break;case P_SEED:s.event.seed=(unsigned)lroundf(v);break;
 case P_DENSITY:s.event.density=(unsigned)lroundf(v);break;case P_CHANCE:s.event.probability=v;break;case P_DISTANCE:s.event.distance=v;break;case P_DURATION:s.event.duration_ms=v;break;case P_REST:s.event.rest_ms=v;break;
 case P_MDEST:s.motion_destination=(unsigned)lroundf(v);s.destination=s.motion_destination;s.source_selected=s.route[s.destination].source;break;case P_ROUTE:s.route[s.motion_destination].enabled=v>=.5f;break;case P_LISTEN:s.listen=v>=.5f;break;case P_SENS:s.sensitivity=v;break;case P_SPACING:s.spacing=v;break;case P_LPROB:s.listen_probability=v;break;case P_LCAP:s.listen_capture=v>=.5f;break;case P_LREPEAT:s.listen_repeat=v>=.5f;break;
 case P_CLOCK:s.event.beat_sync=v>=.5f;s.event.distance=s.event.beat_sync?.25:125;break;case P_TIMING:s.quantized=v>=.5f;break;case P_CHAOS_ON:s.chaos_on=v>=.5f;break;case P_SOURCE:s.source_selected=(unsigned)lroundf(v);s.route[s.motion_destination].source=s.source_selected;break;default:return 0;}
 if(!c1_apply(c,&s))return 0;
 if(id>=0){if((id==C1_GATE||id==C1_FREEZE)&&v>=.5f)c->clean_latched=0;c->manual_mask|=1u<<id;unsigned mask=id<4?1u<<id:id==C1_GATE?G_GATE_OVERRIDE:0;EConfig b=c->clock.manual;
  if(id==C1_LENGTH)b.ms=v;if(id==C1_BREAK)b.fracture=v;if(id==C1_FREEZE)b.freeze=v>=.5f;if(id==C1_GATE)b.gate=v>=.5f;ghost_manual(&c->clock,&b,mask);}
 return 1;
}
