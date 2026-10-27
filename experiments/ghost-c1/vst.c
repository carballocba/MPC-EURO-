/* SPDX-License-Identifier: GPL-3.0-only. Experimental same-UID offline VST adapter.
 * Original BeatRepeat implementation is compiled separately and remains unchanged.
 */
#define _POSIX_C_SOURCE 200809L
#include "c1.h"
#include "vst2_abi.h"
#include "controls.h"
#include <stdatomic.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <time.h>
#ifdef GHOST_FINAL_PRODUCT
#include "factory_product.h"
#endif
extern AEffect *BRPluginMain(audioMasterCallback);
extern void ghost_br_clean(AEffect *);
extern Engine *ghost_br_engine(AEffect *);
extern size_t ghost_br_bytes(void);
extern unsigned ghost_br_captured(AEffect *);
extern void ghost_br_persist(unsigned char *,const float *);
extern float ghost_br_peek(AEffect *,int);
extern void ghost_br_overlay(AEffect *,int,float);
extern void ghost_br_cursor(AEffect *,int,float);
_Static_assert(ATOMIC_INT_LOCK_FREE==2,"requires lock-free 32-bit atomics");
typedef struct {unsigned param;float value;unsigned epoch;} Command;
typedef struct {
 AEffect fx,*base;audioMasterCallback host;C1 instrument;
 _Atomic unsigned target[49],view[P_COUNT],head,tail,quit,opened,clean,dropped,recall,revision;
 _Atomic unsigned epoch,midi_rejected,midi_received;unsigned reported_drop,reported_midi;
 _Atomic unsigned latest_chaos,chaos_pending,chaos_epoch,running;unsigned clean_block;
 _Atomic unsigned probe[2];
#ifdef GHOST_BUFFER_ENGINE
 _Atomic unsigned buffer_view[5];unsigned buffer_pending;float buffer_value[3];unsigned was_recording;
#endif
 _Atomic unsigned last_control,last_before,last_requested,control_serial;atomic_flag diagnostic_writer;
#ifdef GHOST_FINAL_PRODUCT
 _Atomic unsigned product_program;
#endif
 _Atomic unsigned saved[1024];Command command[64];atomic_flag writer;
 unsigned char pending[4096],chunk[8192];unsigned pending_size;
 VstTimeInfo time;unsigned have_time,offset;_Atomic unsigned midi;double rate;pthread_t notifier;
#ifdef GHOST_INTEGRATION_PROBE
 atomic_uint diag_dispatch,diag_set,diag_get,diag_blocks,diag_frames,diag_open,diag_mains,diag_rate,diag_blocksize,diag_bypass;
#endif
} Wrapper;
#ifdef GHOST_INTEGRATION_PROBE
#define DIAG_ADD(w,field,n) atomic_fetch_add_explicit(&(w)->diag_##field,(unsigned)(n),memory_order_relaxed)
static void diagnostic_report(Wrapper *w){
 fprintf(stderr,"GHOST-INTEGRATION uid=47485354 dispatch=%u set=%u get=%u blocks=%u frames=%u open=%u mains=%u rate=%u blocksize=%u bypass_calls=%u running=%u gate=%.0f bypass=%.0f\n",
  atomic_load(&w->diag_dispatch),atomic_load(&w->diag_set),atomic_load(&w->diag_get),atomic_load(&w->diag_blocks),atomic_load(&w->diag_frames),atomic_load(&w->diag_open),atomic_load(&w->diag_mains),atomic_load(&w->diag_rate),atomic_load(&w->diag_blocksize),atomic_load(&w->diag_bypass),atomic_load(&w->running),ghost_br_peek(w->base,GATE),ghost_br_peek(w->base,BYPASS));
}
#else
#define DIAG_ADD(w,field,n) ((void)0)
#endif
static unsigned bits(float x){unsigned b;memcpy(&b,&x,4);return b;}
static float value(unsigned b){float x;memcpy(&x,&b,4);return x;}
static int base_id(unsigned p){switch(p){case P_GATE:return GATE;case P_LENGTH:return LENGTH;case P_BREAK:return BREAK;case P_MIX:return MIX;case P_CAPTURE:return CAPTURE_CMD;case P_FREEZE:return FREEZE;case P_POSITION:return POSITION;case P_SIZE:return BUFFER;case P_REVERSE:return REVERSE;case P_BEND:return BEND;case P_PITCH:return PITCH;case P_CORRUPT:return CORRUPT;case P_TIMING:return TIMING;default:return -1;}}
static float normalized(unsigned p,float unit){const C1Param *r=&c1_params[p];return (unit-r->minimum)/(r->maximum-r->minimum);}
#ifdef GHOST_FINAL_PRODUCT
/* Appended live-clock aliases preserve all existing indices and normalized automation. */
static float live_time(float x,unsigned sync){float lo=sync?1.f/64:5,hi=sync?64:60000;return lo*powf(hi/lo,x);}
static float live_normal(float unit,unsigned sync){float lo=sync?1.f/64:5,hi=sync?64:60000;return fmaxf(0,fminf(1,logf(fmaxf(lo,unit)/lo)/logf(hi/lo)));}
#endif
static float base_unit(int id,float x){switch(id){case LENGTH:return 5+445*x;case BUFFER:return 50+1950*x;case BEND:return -24+48*x;case PITCH:return -12+24*x;default:return x;}}
static float base_normalized(int id,float x){switch(id){case LENGTH:return (x-5)/445;case BUFFER:return (x-50)/1950;case BEND:return (x+24)/48;case PITCH:return (x+12)/24;default:return x;}}
static intptr_t proxy(AEffect *fx,int32_t op,int32_t i,intptr_t n,void *data,float v){(void)i;(void)n;(void)data;(void)v;Wrapper *w=(Wrapper*)fx->resvd1;
 if(op==audioMasterGetTime&&w&&w->have_time)return (intptr_t)&w->time;return 0;}
static void snapshot(Wrapper *w){unsigned char b[4096]={0};size_t n=c1_save(&w->instrument,b,sizeof b);if(n>sizeof b)return;atomic_fetch_add(&w->revision,1);atomic_store(&w->saved[0],(unsigned)n);for(unsigned k=0;k<(n+3)/4;++k){unsigned x;memcpy(&x,b+4*k,4);atomic_store(&w->saved[k+1],x);}atomic_fetch_add(&w->revision,1);}
static void refresh(Wrapper *w){
#ifdef GHOST_BUFFER_ENGINE
 ERuntime *br=&ghost_br_engine(w->base)->r;
 atomic_store(&w->buffer_view[0],bits((float)br->recording));
 atomic_store(&w->buffer_view[2],bits((float)br->repeat));
 atomic_store(&w->buffer_view[3],bits(br->recording?.5f:br->full?1.f:0.f));
 atomic_store(&w->buffer_view[4],bits(br->record_limit?(float)br->record_count/br->record_limit:0));
#endif
atomic_store(&w->probe[0],bits(ghost_br_engine(w->base)->r.base.fracture));atomic_store(&w->probe[1],bits((float)w->instrument.accepted));unsigned drop=atomic_load(&w->dropped),midi=atomic_load(&w->midi_rejected);if(drop!=w->reported_drop){w->instrument.edit_feedback=4;w->reported_drop=drop;}if(midi!=w->reported_midi){w->instrument.edit_feedback=5;w->reported_midi=midi;}for(unsigned p=0;p<P_COUNT;++p){float x=c1_get(&w->instrument,p);if(p==P_TAKE)x=(float)ghost_br_captured(w->base);if(p==P_ACTIVE)x=w->base->getParameter(w->base,ACTIVE);if(p==P_STATUS){float active=w->base->getParameter(w->base,ACTIVE),buffer=w->base->getParameter(w->base,BUFFER_STATE);if(w->instrument.clean_latched)x=S_CLEAN;else if(x==S_CAPTURE&&ghost_br_captured(w->base)){}else if(buffer>=.99f&&active>=.5f)x=S_FREEZE;else if(active>=.5f)x=w->instrument.state.event.enabled&&w->instrument.clock.active&&w->instrument.state.chaos_on&&w->instrument.state.chaos>.7f?S_CHAOS:w->instrument.motion_active?S_MOTION:S_REPEAT;else if(x==S_REPEAT||x==S_FREEZE||x==S_CHAOS||x==S_CAPTURE)x=S_IDLE;}
#ifdef GHOST_BUFFER_ENGINE
 if(p==P_STATUS&&br->recording&&!w->instrument.clean_latched)x=S_CAPTURE;
#endif
 atomic_store(&w->view[p],bits(normalized(p,x)));}}
static void *notify(void *arg){Wrapper *w=arg;unsigned seen[P_COUNT];for(unsigned p=0;p<P_COUNT;++p)seen[p]=~0u;const struct timespec wait={0,33333333};
#ifdef GHOST_BUFFER_ENGINE
 unsigned buffer_seen[5];for(unsigned b=0;b<5;++b)buffer_seen[b]=~0u;
#endif
#ifdef GHOST_INTEGRATION_PROBE
 unsigned diagnostic_tick=0;
#endif
 while(!atomic_load(&w->quit)){nanosleep(&wait,NULL);
#ifdef GHOST_INTEGRATION_PROBE
 if(++diagnostic_tick>=30){diagnostic_tick=0;diagnostic_report(w);}
#endif
 if(!w->host||!atomic_load(&w->opened))continue;int changed=0;
#ifdef GHOST_BUFFER_ENGINE
 for(unsigned b=0;b<5;++b){unsigned x=atomic_load(&w->buffer_view[b]);if(x!=buffer_seen[b]){
  buffer_seen[b]=x;changed=1;
  if(b==0||b>=3)w->host(&w->fx,audioMasterAutomate,126+(int)b,0,NULL,value(x));
 }}
#endif
for(unsigned p=0;p<P_COUNT;++p){unsigned x=atomic_load(&w->view[p]);if(x!=seen[p]){seen[p]=x;changed=1;if(c1_params[p].readonly||(p>=P_R0MIN&&p<P_EDIT))w->host(&w->fx,audioMasterAutomate,49+(int)p,0,NULL,value(x));}}if(changed)w->host(&w->fx,audioMasterUpdateDisplay,0,0,NULL,0);}return NULL;}
static int enqueue(Wrapper *w,unsigned p,float v){if(p==P_CHAOS){atomic_store(&w->latest_chaos,bits(v));atomic_store(&w->chaos_epoch,atomic_load(&w->epoch));atomic_store(&w->chaos_pending,1);return 1;}if(p==P_CLEAN&&v>0){atomic_store(&w->clean,1);return 1;}if(atomic_flag_test_and_set(&w->writer)){atomic_fetch_add(&w->dropped,1);return 0;}unsigned h=atomic_load(&w->head),next=(h+1)&63,t=atomic_load_explicit(&w->tail,memory_order_acquire);int ok=next!=t;if(ok){w->command[h]=(Command){p,v,atomic_load(&w->epoch)};atomic_store_explicit(&w->head,next,memory_order_release);}else atomic_fetch_add(&w->dropped,1);atomic_flag_clear(&w->writer);return ok;}
static float get(AEffect *,int32_t);
static float diagnostic_value(Wrapper *w,unsigned id){
 if(id<49)return ghost_br_peek(w->base,id==MIX_LIVE?MIX:(int)id);
 if(id<49+P_COUNT)return value(atomic_load(&w->view[id-49]));
 /* Appended aliases have no mutable gesture cursor. */
 return get(&w->fx,(int)id);
}
static void set(AEffect *fx,int32_t id,float x){Wrapper *w=fx->object;DIAG_ADD(w,set,1);if(id<0||id>=fx->numParams||!isfinite(x))return;x=fmaxf(0,fminf(1,x));
 /* Host gestures have no source tag: this records parameter requests, not touch events.
  * Nonblocking atomics only; the audio callback performs no diagnostic I/O. */
 if(!atomic_flag_test_and_set_explicit(&w->diagnostic_writer,memory_order_acquire)){
  atomic_store(&w->last_before,bits(diagnostic_value(w,(unsigned)id)));atomic_store(&w->last_requested,bits(x));atomic_store(&w->last_control,(unsigned)id);
  atomic_fetch_add(&w->control_serial,1);atomic_flag_clear_explicit(&w->diagnostic_writer,memory_order_release);
 }
#ifdef GHOST_BUFFER_ENGINE
 if(id>=126){
  if(id==126||id==128){float old=value(atomic_load(&w->buffer_view[id-126]));if(x>0&&x<1&&x!=old&&fabsf(x-old)<.5f)x=x>old?1:0;}
  if(id<129)enqueue(w,P_COUNT+2+(unsigned)id-126,x);return;}
#endif
#ifdef GHOST_FINAL_PRODUCT
 if(id>=49+P_COUNT){enqueue(w,P_COUNT+(unsigned)id-(49+P_COUNT),x);return;}
#endif
 if(id<49){
#ifdef GHOST_BUFFER_ENGINE
 if((id==GATE||id==REVERSE||id==FREEZE)&&x>=.5f&&(id==FREEZE||ghost_br_peek(w->base,id)<.5f))enqueue(w,P_COUNT+5,1);
#endif
 w->base->setParameter(w->base,id,x);x=ghost_br_peek(w->base,id);atomic_store(&w->target[id],bits(x));if(id==MIX_LIVE){float mix=ghost_br_peek(w->base,MIX);atomic_store(&w->target[MIX],bits(mix));}}
 else{unsigned p=(unsigned)id-49;if(c1_params[p].readonly)return;if((p==P_GHOST||p==P_MOTION)&&x>.5f&&ghost_br_peek(w->base,LEGACY)>=.5f)return;unsigned steps=p==P_DEST||p==P_MDEST?11:p==P_TYPE||p==P_SOURCE?7:p==P_DENSITY?16:(p==P_GHOST||p==P_GATE||p==P_MOTION||p==P_BUFFER||p==P_RANDOM||p==P_LOCK||p==P_SYNC||p==P_HOLD||p==P_FREEZE||p==P_REVERSE||p==P_ROUTE||p==P_LISTEN||p==P_LCAP||p==P_LREPEAT||p==P_CLOCK||p==P_TIMING||p==P_CHAOS_ON)?1:0;if(steps&&x>0&&x<1){float old=value(atomic_load(&w->view[p]));if(fabsf(x-old)<.5f/steps&&x!=old)x=fmaxf(0,fminf(1,old+(x>old?1.f:-1.f)/steps));}float unit=c1_params[p].minimum+x*(c1_params[p].maximum-c1_params[p].minimum);int original=base_id(p);if(original>=0){
#ifdef GHOST_BUFFER_ENGINE
 if((original==GATE||original==REVERSE||original==FREEZE)&&x>=.5f&&(original==FREEZE||ghost_br_peek(w->base,original)<.5f))enqueue(w,P_COUNT+5,1);
#endif
 float n=base_normalized(original,unit);w->base->setParameter(w->base,original,n);atomic_store(&w->target[original],bits(ghost_br_peek(w->base,original)));}else enqueue(w,p,unit);}}
static float get(AEffect *fx,int32_t id){Wrapper *w=fx->object;DIAG_ADD(w,get,1);if(id<0||id>=fx->numParams)return 0;
#ifdef GHOST_BUFFER_ENGINE
 if(id>=126)return value(atomic_load(&w->buffer_view[id-126]));
#endif
#ifdef GHOST_FINAL_PRODUCT
 if(id>=49+P_COUNT){unsigned rate=id==49+P_COUNT,p=rate?P_RATE:P_DISTANCE,clock=rate?P_SYNC:P_CLOCK;float n=value(atomic_load(&w->view[p]));float unit=c1_params[p].minimum+n*(c1_params[p].maximum-c1_params[p].minimum);return live_normal(unit,value(atomic_load(&w->view[clock]))>=.5f);}
#endif
 if(id<49){if(id==ACTIVE||id==STATUS||(id>=BUFFER_STATE&&id<=ACTIVITY))return w->base->getParameter(w->base,id);float x=ghost_br_peek(w->base,id==MIX_LIVE?MIX:id);ghost_br_cursor(w->base,id,x);return x;}return value(atomic_load(&w->view[id-49]));}
static void receive(Wrapper *w){if(atomic_load_explicit(&w->recall,memory_order_acquire)==1){c1_load(&w->instrument,w->pending,w->pending_size);
#ifdef GHOST_BUFFER_ENGINE
 w->buffer_pending=6;w->buffer_value[0]=0;w->buffer_value[1]=1;w->buffer_value[2]=0;
#endif
 atomic_store_explicit(&w->recall,0,memory_order_release);}
 if(atomic_exchange(&w->chaos_pending,0)&&atomic_load(&w->chaos_epoch)==atomic_load(&w->epoch))c1_set(&w->instrument,P_CHAOS,value(atomic_load(&w->latest_chaos)));
 unsigned t=atomic_load(&w->tail),h=atomic_load_explicit(&w->head,memory_order_acquire);unsigned count=0;while(t!=h&&count++<63){Command command=w->command[t];if(command.epoch==atomic_load(&w->epoch)){
#ifdef GHOST_BUFFER_ENGINE
 if(command.param>=P_COUNT+2){unsigned b=command.param-(P_COUNT+2);if(b<3){w->buffer_value[b]=command.value;w->buffer_pending|=1u<<b;}else if(b==3)w->buffer_pending|=8;}
 else
#endif
#ifdef GHOST_FINAL_PRODUCT
 if(command.param>=P_COUNT){unsigned rate=command.param==P_COUNT;unsigned sync=rate?w->instrument.state.source[w->instrument.state.source_selected].sync:w->instrument.state.event.beat_sync;c1_set(&w->instrument,rate?P_RATE:P_DISTANCE,live_time(command.value,sync));}
 else
#endif
 c1_set(&w->instrument,command.param,command.value);
 }t=(t+1)&63;}atomic_store_explicit(&w->tail,t,memory_order_release);
 if(atomic_exchange(&w->clean,0)){
#ifdef GHOST_BUFFER_ENGINE
 ghost_buffer_clean(ghost_br_engine(w->base));w->buffer_pending&=2;
#endif
 c1_set(&w->instrument,P_CLEAN,1);ghost_br_clean(w->base);for(unsigned i=0;i<3;++i){int id=i==0?GATE:i==1?FREEZE:SEQ_RUN;atomic_store(&w->target[id],bits(0));w->base->setParameter(w->base,id,0);}}
}
static void render(AEffect *fx,float **in,float **out,int32_t n,unsigned accumulate){Wrapper *w=fx->object;if(n<=0)return;DIAG_ADD(w,blocks,1);DIAG_ADD(w,frames,n);receive(w);w->clean_block=(w->instrument.commands&1)!=0;w->have_time=0;if(w->host){VstTimeInfo *t=(VstTimeInfo*)w->host(fx,audioMasterGetTime,0,kVstTempoValid|kVstPpqPosValid,NULL,0);if(t){w->time=*t;w->have_time=1;}}
 if(w->have_time&&(w->time.flags&kVstTempoValid)){unsigned playing=(w->time.flags&kVstTransportPlaying)!=0;unsigned seek=playing&&(w->time.flags&kVstPpqPosValid)&&fabs(w->instrument.clock.beat-w->time.ppqPos)>.25;ghost_clock(&w->instrument.clock,w->time.tempo,playing,seek,w->time.ppqPos);}
 if(accumulate)w->base->process(w->base,in,out,n);else w->base->processReplacing(w->base,in,out,n);
 refresh(w);snapshot(w);
}
/* Called only by the original stereo audio owner, after timestamped MIDI. */
static void sync_manual(Wrapper *w,unsigned all){
 AEffect *base=w->base;
 for(unsigned p=0;p<P_COUNT;++p){int id=base_id(p);if(id<0||p==P_CAPTURE)continue;float x=ghost_br_peek(base,id);atomic_store(&w->target[id],bits(x));float unit=base_unit(id,x);if(c1_get(&w->instrument,p)!=unit)c1_set(&w->instrument,p,unit);}
 if(all)for(unsigned id=0;id<49;++id)atomic_store(&w->target[id],bits(ghost_br_peek(base,id)));
}
#ifdef GHOST_BUFFER_ENGINE
static void buffer_apply(Wrapper *w){
 Engine *be=ghost_br_engine(w->base);
  unsigned pending=w->buffer_pending;w->buffer_pending=0;
  if(pending&8){ghost_buffer_rearm(be);w->instrument.clean_latched=0;}
  if(pending&2){ghost_buffer_limit(be,.25f+7.75f*w->buffer_value[1]);atomic_store(&w->buffer_view[1],bits(w->buffer_value[1]));}
  if(pending&4){be->r.repeat=w->buffer_value[2]>=.5f;if(be->r.repeat){ghost_buffer_rearm(be);w->instrument.clean_latched=0;}}
  if(pending&1)ghost_buffer_record(be,w->buffer_value[0]>=.5f);
}
#endif
unsigned ghost_c11_tick(AEffect *base,float l,float r,unsigned frame,unsigned midi_changed){
 Wrapper *w=(Wrapper*)base->resvd1;if(!w)return 0;
#ifdef GHOST_BUFFER_ENGINE
 Engine *be=ghost_br_engine(base);
 if(!frame)buffer_apply(w);
 if(w->was_recording && !be->r.recording && be->r.held_count>=2 && !w->clean_block){
  base->setParameter(base,FREEZE,1);atomic_store(&w->target[FREEZE],bits(1));
  /* Publish the automatic/manual commit coherently to both parameter owners.
   * Otherwise later manual sync would mistake auto-FULL for a user rearm. */
  unsigned keep_clean=be->r.clean;c1_set(&w->instrument,P_FREEZE,1);
  w->instrument.clean_latched=keep_clean;
 }
 w->was_recording=be->r.recording;
 if(w->clean_block)ghost_buffer_clean(be);
 /* An explicit Gate/Reverse/HELD gesture rearms through setParameter below. */
#endif
 if(w->clean_block)ghost_br_clean(base);
 if(!(frame&31)||midi_changed)sync_manual(w,midi_changed);
 unsigned commands=w->instrument.commands;c1_process(&w->instrument,&l,&r,NULL,NULL,1,NULL,0);
 return commands||w->instrument.capture_requested||w->instrument.control_dirty;
}
/* Audio-owner command rearm. Clean in the same callback retains priority. */
void ghost_c11_punch(AEffect *base){
#ifdef GHOST_BUFFER_ENGINE
 ghost_buffer_rearm(ghost_br_engine(base));
#endif
 Wrapper *w=(Wrapper*)base->resvd1;if(w&&!w->clean_block)w->instrument.clean_latched=0;}
unsigned ghost_c11_capture_request(AEffect *base){Wrapper *w=(Wrapper*)base->resvd1;return w?w->instrument.capture_requested:0;}
void ghost_c11_capture_result(AEffect *base,unsigned success){Wrapper *w=(Wrapper*)base->resvd1;if(w&&success)w->instrument.visual_until=w->instrument.clock.sample+(uint64_t)(w->rate*.12);}
static int generated(Wrapper *w){return w->instrument.state.event.enabled||w->instrument.state.motion||w->instrument.state.listen||w->instrument.dice_mask;}
void ghost_c11_config(AEffect *base,EConfig *config){
 Wrapper *w=(Wrapper*)base->resvd1;if(!w)return;C1 *c=&w->instrument;
#ifdef GHOST_BUFFER_ENGINE
 ghost_br_engine(base)->r.suspended=ghost_br_peek(base,BYPASS)>=.5f || !atomic_load(&w->running);
 /* C1 is the single Clean/rearm owner, including explicit Ghost/Motion/presets. */
 ghost_br_engine(base)->r.clean=c->clean_latched!=0;
#endif
 if(c->clean_latched){config->gate=config->freeze=config->run=0;return;}
#ifdef GHOST_BUFFER_ENGINE
 if(ghost_br_engine(base)->r.source_held)config->freeze=ghost_br_peek(base,FREEZE)>=.5f;
#endif
 if(!generated(w))return;EConfig *e=&c->last_effective;
 /* Generative leases may add Repeat, never erase a live manual Gate/Punch. */
 config->ms=e->ms;config->fracture=e->fracture;config->freeze=e->freeze;
#ifdef GHOST_BUFFER_ENGINE
 config->freeze|=ghost_br_peek(base,FREEZE)>=.5f;
#endif
config->position=e->position;config->buffer_ms=e->buffer_ms;config->reverse=e->reverse;config->bend=e->bend;config->pitch=e->pitch;config->corrupt=e->corrupt;config->gate|=e->gate;
 if(config->time_grid){
  unsigned length_generated=(c->clock.active&&(c->clock.destinations&1))||(c->state.motion&&c->state.route[0].enabled&&!(c->manual_mask&1))||(c->dice_mask&1);
  if(length_generated){float lo=c->state.random[0].minimum,hi=c->state.random[0].maximum,error=INFINITY;unsigned best=0;
   if(c->clock.active&&(c->clock.destinations&1)){lo=c->clock.config.destination[0].minimum;hi=c->clock.config.destination[0].maximum;}else if(c->state.motion&&c->state.route[0].enabled){lo=c->state.route[0].minimum;hi=c->state.route[0].maximum;}if(c->dice_mask&1){lo=c->state.random[0].minimum;hi=c->state.random[0].maximum;}
   for(unsigned g=0;g<11;++g){float ms=60000.f/(float)c->clock.tempo*engine_division(g),delta=fabsf(ms-e->ms);if(ms>=lo&&ms<=hi&&delta<error){error=delta;best=g;}}
   if(isfinite(error)){config->grid=best;if(c->edit_feedback==3)c->edit_feedback=0;}else c->edit_feedback=3;
  }
 }
}
float ghost_c11_mix(AEffect *base,float manual){Wrapper *w=(Wrapper*)base->resvd1;return w&&generated(w)?w->instrument.last_mix:manual;}
static void process(AEffect *f,float **i,float **o,int32_t n){render(f,i,o,n,0);}
static void accumulating(AEffect *f,float **i,float **o,int32_t n){render(f,i,o,n,1);}
static void text(void *p,const char *s,unsigned size){if(p&&size){strncpy(p,s,size-1);((char*)p)[size-1]=0;}}
static void display(Wrapper *w,unsigned p,void *data,unsigned label){
 float x=value(atomic_load(&w->view[p]))*(c1_params[p].maximum-c1_params[p].minimum)+c1_params[p].minimum;
 const char *unit="",*shown=NULL;
 static const char *states[]={"IDLE","LISTEN","CAPTURE","REPEAT","FREEZE","MOTION","CHAOS","CLEAN"};
 static const char *feedback[]={"OK","LINKED","FIXED","NO GRID","Q FULL","MIDIERR"};
 static const char *types[]={"STEP","SMOOTH","WALK","S/H","SINE","TRI","GATE","REPEAT"};
 static const char *dest[]={"LENGTH","BREAK","CAPTURE","FREEZE","POS","SIZE","REVERSE","BEND","PITCH","CORRUPT","MIX","GATE"};
 if(p==P_STATUS)shown=states[(unsigned)lroundf(x)%8];
 if(p==P_TAKE)shown=x>=.5f?"TAKE":"EMPTY";
 if(p==P_DENSITY){static char density[8];snprintf(density,sizeof density,"%.0f",x);shown=density;}
 if(p==P_BREAK||p==P_CHAOS||p==P_MDEPTH||p==P_CHANCE||p==P_ENERGY){unit="%";x*=100;}
 #ifdef GHOST_FINAL_PRODUCT
 if(p==P_MIX){unit="%";x*=100;}
#endif
 if(p==P_LENGTH)unit="ms";
 if(p==P_EDIT)shown=feedback[(unsigned)lroundf(x)%6];
 if(p==P_TYPE)shown=types[(unsigned)lroundf(x)%8];
 if(p==P_DEST||p==P_MDEST)shown=dest[(unsigned)lroundf(x)%12];
 if(p==P_SOURCE)x+=1;
 if(p>=P_R0MIN&&p<P_EDIT){unsigned d=(p-P_R0MIN)/2;if(d==0||d==3)unit="ms";else if(d==4||d==5)unit="st";else {unit="%";x*=100;}}
 if(p==P_RATE)unit=value(atomic_load(&w->view[P_SYNC]))>=.5f?"beats":"ms";
 if(p==P_DISTANCE)unit=value(atomic_load(&w->view[P_CLOCK]))>=.5f?"beats":"ms";
 if(p==P_DURATION||p==P_REST||p==P_SPACING)unit="ms";
 if(p==P_CLOCK||p==P_SYNC)shown=x>=.5f?"BEATS":"FREE";
 if(label)text(data,unit,8);else if(shown)text(data,shown,8);else snprintf(data,8,"%.2f",x);
}
static intptr_t dispatch(AEffect *fx,int32_t op,int32_t idx,intptr_t n,void *data,float v){Wrapper *w=fx->object;
 DIAG_ADD(w,dispatch,1);
 if(op==effOpen)DIAG_ADD(w,open,1);
 if(op==effMainsChanged)DIAG_ADD(w,mains,1);
 if(op==effSetSampleRate)DIAG_ADD(w,rate,1);
 if(op==effSetBlockSize)DIAG_ADD(w,blocksize,1);
 if(op==effSetBypass)DIAG_ADD(w,bypass,1);
#ifdef GHOST_STANDALONE_UID
 if(op==effGetEffectName){text(data,"GHOST",32);return 1;}
 if(op==effGetProductString){text(data,"GHOST",64);return 1;}
 if(op==effGetVendorString){text(data,"MPC-EURO",64);return 1;}
#endif
#ifdef GHOST_BUFFER_ENGINE
 if(idx>=126&&idx<131){
  static const char *names[]={"Capture","Rec max","Repeat","RecState","RecFill"};
  if(op==effCanBeAutomated)return idx<129;
  if(op==effGetParamName){text(data,names[idx-126],8);return 1;}
  if(op==effGetParamLabel){text(data,idx==127?"s":"",8);return 1;}
  if(op==effGetParamDisplay){float x=get(fx,idx);char b[16];
   if(idx==129)text(data,x>=1?"FULL":x>.1f?"REC":"READY",8);
   else if(idx==126||idx==128)text(data,x>=.5f?"ON":"OFF",8);
   else {snprintf(b,sizeof b,"%.2f",idx==127?.25f+7.75f*x:100*x);text(data,b,8);}return 1;}
 }
#endif
 #ifdef GHOST_FINAL_PRODUCT
 if(idx>=49+P_COUNT&&idx<fx->numParams){unsigned p=idx==49+P_COUNT?P_RATE:P_DISTANCE;
  if(op==effCanBeAutomated)return 1;
  if(op==effGetParamName){text(data,p==P_RATE?"Rate":"Distance",8);return 1;}
  if(op==effGetParamLabel||op==effGetParamDisplay){display(w,p,data,op==effGetParamLabel);return 1;}
 }
#endif
 /* Vendor-specific read-only diagnostic snapshot: GH D1, eight uint32 words.
  * Queried by an authorized host helper; no file logging, no parameter added. */
 if(op==50&&idx==0x47484431&&n==32&&data){
  if(atomic_flag_test_and_set_explicit(&w->diagnostic_writer,memory_order_acquire))return 0;
  unsigned *d=data,p=atomic_load(&w->last_control);d[0]=1;d[1]=atomic_load(&w->control_serial);d[2]=p;
  d[3]=atomic_load(&w->last_before);d[4]=atomic_load(&w->last_requested);d[5]=bits(diagnostic_value(w,p));
  d[6]=atomic_load(&w->dropped);d[7]=atomic_load(&w->midi_rejected);
  atomic_flag_clear_explicit(&w->diagnostic_writer,memory_order_release);return 1;
 }
 switch(op){case effProcessEvents:{intptr_t result=w->base->dispatcher(w->base,op,idx,n,data,v);if(!result)atomic_fetch_add(&w->midi_rejected,1);else if(data)atomic_fetch_add(&w->midi_received,(unsigned)((VstEvents*)data)->numEvents);return result;}case effOpen:atomic_store(&w->opened,1);return 1;case effClose:atomic_store(&w->quit,1);pthread_join(w->notifier,NULL);w->base->dispatcher(w->base,effClose,0,0,NULL,0);free(w);return 1;
 case effSetSampleRate:if(!isfinite(v)||v<16000||v>96000)return 0;{unsigned char saved[4096];size_t size=c1_save(&w->instrument,saved,sizeof saved);w->rate=v;/* VST contract: suspended rate change. */c1_init(&w->instrument,v);c1_bind(&w->instrument,ghost_br_engine(w->base),0);if(size)c1_load(&w->instrument,saved,size);refresh(w);snapshot(w);return w->base->dispatcher(w->base,op,idx,n,data,v);}
#ifdef GHOST_FINAL_PRODUCT
 case effGetProgram:return atomic_load(&w->product_program);
 case effGetProgramName:{unsigned selected=atomic_load(&w->product_program);if(selected>=8){text(data,product_names[selected-8],24);return 1;}return w->base->dispatcher(w->base,effGetProgramNameIndexed,(int32_t)selected,0,data,0);}
 case effGetProgramNameIndexed:if(idx>=8&&idx<16){text(data,product_names[idx-8],24);return 1;}return w->base->dispatcher(w->base,op,idx,n,data,v);
 case effSetProgram:{
  if(n<0||n>=16)return 0;
  /* Keep the VST2 integer value contract; original programs remain 0..7. */
  if(!w->base->dispatcher(w->base,op,0,n<8?n:0,NULL,0))return 0;
  void *base=NULL;intptr_t bn=w->base->dispatcher(w->base,effGetChunk,0,0,&base,0);if(bn<=0||bn>532)return 0;
  C1 *tmp=calloc(1,sizeof(*tmp));if(!tmp)return 0;c1_init(tmp,w->rate);
  if(!c1_load(tmp,base,(size_t)bn)){free(tmp);return 0;}
  if(n>=8)product_preset(tmp,(unsigned)n-8);
  unsigned char preset[8192];memcpy(preset,"GCX1",4);unsigned bsize=(unsigned)bn,cs=(unsigned)c1_save(tmp,preset+12+bn,sizeof(preset)-12-(size_t)bn);
  if(!cs){free(tmp);return 0;}memcpy(preset+4,&bsize,4);memcpy(preset+8,&cs,4);memcpy(preset+12,base,(size_t)bn);
  if(n>=8){float manual[49];for(unsigned i=0;i<49;++i)manual[i]=ghost_br_peek(w->base,(int)i);
   for(unsigned p=0;p<P_COUNT;++p){int id=base_id(p);if(id>=0&&p!=P_CAPTURE)manual[id]=base_normalized(id,c1_get(tmp,p));}
   manual[TIME_MODE]=0;manual[LEGACY]=0;ghost_br_persist(preset+12,manual);
  }free(tmp);
  intptr_t result=dispatch(fx,effSetChunk,0,12+bn+cs,preset,0);if(result)atomic_store(&w->product_program,(unsigned)n);return result;
 }
#else
 case effSetProgram:{intptr_t result=w->base->dispatcher(w->base,op,idx,n,data,v);void *preset=NULL;intptr_t size=w->base->dispatcher(w->base,effGetChunk,0,0,&preset,0);if(size>0&&!dispatch(fx,effSetChunk,0,size,preset,0))return 0;return result;}
#endif
 case effMainsChanged:atomic_store(&w->running,n!=0);if(!n)atomic_store(&w->clean,1);{intptr_t result=w->base->dispatcher(w->base,op,idx,n,data,v);for(unsigned i=0;i<49;++i)atomic_store(&w->target[i],bits(w->base->getParameter(w->base,i)));return result;}
 case effGetParamName:case effGetParamLabel:case effGetParamDisplay:if(idx<49)return w->base->dispatcher(w->base,op,idx,n,data,v);if(idx>=49+P_COUNT)return 0;if(op==effGetParamName)text(data,c1_params[idx-49].name,8);else display(w,(unsigned)idx-49,data,op==effGetParamLabel);return 1;
 case effCanBeAutomated:return idx>=49&&idx<49+P_COUNT?!c1_params[idx-49].readonly:w->base->dispatcher(w->base,op,idx,n,data,v);
 case effGetChunk:{if(!atomic_load(&w->running)){receive(w);
#ifdef GHOST_BUFFER_ENGINE
 buffer_apply(w);
#endif
 sync_manual(w,0);c1_commit_commands(&w->instrument);refresh(w);snapshot(w);}if(atomic_load(&w->chaos_pending)||atomic_load(&w->head)!=atomic_load(&w->tail)||atomic_load(&w->recall)||atomic_load(&w->clean))return 0;void *base=NULL;intptr_t bn=w->base->dispatcher(w->base,effGetChunk,0,0,&base,0);unsigned rev=atomic_load_explicit(&w->revision,memory_order_acquire),cn=atomic_load(&w->saved[0]);if(!data||bn<=0||bn>532||(rev&1)||cn>4096||cn==0)return 0;memcpy(w->chunk,"GCX1",4);memcpy(w->chunk+4,&bn,4);memcpy(w->chunk+8,&cn,4);memcpy(w->chunk+12,base,(size_t)bn);if(bn==532){float manual[49];for(unsigned i=0;i<49;++i)manual[i]=ghost_br_peek(w->base,(int)i);ghost_br_persist(w->chunk+12,manual);}for(unsigned k=0;k<(cn+3)/4;++k){unsigned x=atomic_load(&w->saved[k+1]);memcpy(w->chunk+12+bn+k*4,&x,4);}if(atomic_load_explicit(&w->revision,memory_order_acquire)!=rev)return 0;
#ifdef GHOST_BUFFER_ENGINE
 unsigned size=12+bn+cn;memmove(w->chunk+16,w->chunk,size);memcpy(w->chunk,"GBF1",4);
 float extra[3]={get(fx,127),get(fx,128),0};memcpy(w->chunk+4,extra,12);*(void**)data=w->chunk;return size+16;
#else
 *(void**)data=w->chunk;return 12+bn+cn;
#endif
}
 case effSetChunk:{
#ifdef GHOST_BUFFER_ENGINE
 if(data&&n>=16&&n<=8192&&!memcmp(data,"GBF1",4)){
  if(!memcmp((unsigned char*)data+16,"GBF1",4))return 0;
  float extra[3];memcpy(extra,(unsigned char*)data+4,12);
  if(!isfinite(extra[0])||extra[0]<0||extra[0]>1||!isfinite(extra[1])||extra[1]<0||extra[1]>1||extra[2]!=0)return 0;
  intptr_t ok=dispatch(fx,effSetChunk,idx,n-16,(unsigned char*)data+16,v);
  if(ok){enqueue(w,P_COUNT+3,extra[0]);enqueue(w,P_COUNT+4,extra[1]);}return ok;
 }
#endif
 if(!data||n<4||n>8192)return 0;unsigned cn=0,bn=0;unsigned char *b=data;if(!memcmp(b,"GCX1",4)){if(n<12)return 0;memcpy(&bn,b+4,4);memcpy(&cn,b+8,4);if((bn!=48&&bn!=532)||cn>4096||12+(uint64_t)bn+cn!=(uint64_t)n)return 0;}else if(!memcmp(b,"EBR1",4)||!memcmp(b,"EBR2",4))bn=(unsigned)n;else return 0;
  C1 *temporary=calloc(1,sizeof(*temporary));if(!temporary)return 0;c1_init(temporary,w->rate);int valid=cn?c1_load(temporary,b+12+bn,cn):c1_load(temporary,b,bn);if(!valid){free(temporary);return 0;}unsigned expected=0;if(!atomic_compare_exchange_strong(&w->recall,&expected,2)){free(temporary);return 0;}if(!w->base->dispatcher(w->base,effSetChunk,0,bn,cn?b+12:b,0)){atomic_store(&w->recall,0);free(temporary);return 0;}
  for(unsigned i=0;i<49;++i)atomic_store(&w->target[i],bits(w->base->getParameter(w->base,i)));atomic_fetch_add(&w->epoch,1);
w->pending_size=(unsigned)c1_save(temporary,w->pending,sizeof w->pending);free(temporary);atomic_store_explicit(&w->recall,1,memory_order_release);return 1;}
 default:return w->base->dispatcher(w->base,op,idx,n,data,v);}
}
__attribute__((visibility("default"))) AEffect *VSTPluginMain(audioMasterCallback host){Wrapper *w=calloc(1,sizeof(*w));if(!w)return NULL;w->base=BRPluginMain(proxy);if(!w->base){free(w);return NULL;}w->base->resvd1=(intptr_t)w;
#ifdef GHOST_BUFFER_ENGINE
 /* Fault in every storage page while instantiating, never from audio. Counts
  * remain zero: these page touches do not constitute captured material. */
 volatile unsigned char *pages=(volatile unsigned char*)ghost_br_engine(w->base)->ring;
 size_t storage=sizeof(ghost_br_engine(w->base)->ring);
 for(size_t i=0;i<storage;i+=4096)pages[i]=0;
 pages[storage-1]=0;
#endif
 w->host=host;w->rate=44100;c1_init(&w->instrument,44100);c1_bind(&w->instrument,ghost_br_engine(w->base),0);atomic_flag_clear(&w->writer);atomic_flag_clear(&w->diagnostic_writer);for(unsigned i=0;i<49;++i)atomic_store(&w->target[i],bits(w->base->getParameter(w->base,i)));w->fx=*w->base;w->fx.object=w;w->fx.dispatcher=dispatch;w->fx.setParameter=set;w->fx.getParameter=get;w->fx.processReplacing=process;w->fx.process=accumulating;w->fx.numParams=49+P_COUNT;
#ifdef GHOST_STANDALONE_UID
 w->fx.uniqueID=(int32_t)GHOST_STANDALONE_UID;
#ifdef GHOST_FINAL_PRODUCT
 w->fx.numParams=49+P_COUNT+2;
#ifdef GHOST_BUFFER_ENGINE
 w->fx.numParams=131;atomic_store(&w->buffer_view[1],bits(1));
#endif
 w->fx.numPrograms=16;atomic_init(&w->product_program,0);
#endif
#endif
#ifdef GHOST_INTEGRATION_PROBE
 atomic_init(&w->diag_dispatch,0);atomic_init(&w->diag_set,0);atomic_init(&w->diag_get,0);atomic_init(&w->diag_blocks,0);atomic_init(&w->diag_frames,0);atomic_init(&w->diag_open,0);atomic_init(&w->diag_mains,0);atomic_init(&w->diag_rate,0);atomic_init(&w->diag_blocksize,0);atomic_init(&w->diag_bypass,0);
#endif
 refresh(w);snapshot(w);if(pthread_create(&w->notifier,NULL,notify,w)){w->base->dispatcher(w->base,effClose,0,0,NULL,0);free(w);return NULL;}return &w->fx;}
/* Native benchmark only; ARM export map retains only VSTPluginMain. */
size_t ghost_c1_wrapper_bytes(void){return sizeof(Wrapper)+ghost_br_bytes();}

/* Read-only native harness diagnostics; not exported by the ARM VST map. */
void ghost_c11_stats(AEffect *fx,unsigned *stats){Wrapper *w=fx->object;stats[0]=atomic_load(&w->dropped);stats[1]=atomic_load(&w->midi_rejected);stats[2]=atomic_load(&w->midi_received);}

void ghost_c11_probe(AEffect *fx,float *values){Wrapper *w=fx->object;for(unsigned i=0;i<2;++i)values[i]=value(atomic_load(&w->probe[i]));}

/* Offline single-thread host only, called between audio callbacks. Hidden on ARM. */
void ghost_control_probe(AEffect *fx,float *v){Wrapper *w=fx->object;C1 *c=&w->instrument;Engine *e=ghost_br_engine(w->base);
 v[0]=(float)c->accepted;v[1]=c->last_effective.ms;v[2]=(float)c->manual_mask;
 v[3]=(float)e->r.playing;v[4]=(float)e->r.cap_count;v[5]=c->state.source[c->state.source_selected].depth;
 v[6]=(float)c->state.event.density;v[7]=c->state.chaos;v[8]=(float)c->clock.config.density;
}

#ifdef GHOST_INTEGRATION_PROBE
/* Native test access only; the ARM export map still exports VSTPluginMain alone. */
void ghost_integration_counts(AEffect *fx,unsigned *v){Wrapper *w=fx->object;v[0]=atomic_load(&w->diag_dispatch);v[1]=atomic_load(&w->diag_set);v[2]=atomic_load(&w->diag_get);v[3]=atomic_load(&w->diag_blocks);v[4]=atomic_load(&w->diag_frames);v[5]=atomic_load(&w->diag_open);v[6]=atomic_load(&w->diag_mains);v[7]=atomic_load(&w->diag_rate);v[8]=atomic_load(&w->diag_blocksize);v[9]=atomic_load(&w->diag_bypass);}
#endif

#ifdef GHOST_FINAL_PRODUCT
/* Offline single-audio-owner introspection only; excluded by ARM export map. */
void ghost_product_probe(AEffect *fx,float *v){Wrapper *w=fx->object;Engine *e=ghost_br_engine(w->base);
 v[0]=(float)e->r.base.freeze;v[1]=(float)e->r.captured;v[2]=(float)e->r.cap_count;v[3]=(float)w->instrument.motion_active;v[4]=(float)w->instrument.clock.active;v[5]=(float)e->r.base.gate;
}
#endif
#ifdef GHOST_BUFFER_ENGINE
/* Offline audio-owner probe. Hidden by ARM export map. */
void ghost_buffer_probe(AEffect *fx,double *v){Wrapper *w=fx->object;Engine *e=ghost_br_engine(w->base);ERuntime *r=&e->r;
 v[0]=r->live;v[1]=r->captured;v[2]=r->cap_count;v[3]=r->voice.bank;v[4]=r->voice.start;v[5]=r->voice.length;v[6]=r->voice.phase;
 v[7]=r->count[r->live];v[8]=(double)r->total[r->live];v[9]=r->last[0];v[10]=r->source_held;v[11]=r->clean;
 v[12]=r->voice.bank>=0?e->ring[r->voice.bank][0][r->voice.start]:-10;v[13]=r->base.chance;v[14]=r->cycle_allowed;v[15]=sizeof(*e);
}
#endif
