#!/usr/bin/env python3
"""Generate isolated integration copies with counted anchors; never edits baseline sources."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'build/ghost-performance-edition';SRC=OUT/'source'
def generate():
 SRC.mkdir(parents=True,exist_ok=True);e=ROOT/'experiments/ghost-c1';inputs={}
 def read(p):
  b=p.read_bytes();inputs[str(p.relative_to(ROOT))]=hashlib.sha256(b).hexdigest();return b.decode()
 def change(s,a,b):
  if s.count(a)!=1:raise RuntimeError('Integration anchor changed: '+a[:90])
  return s.replace(a,b)
 h=read(e/'c1.h').replace('"../ghost/audio.h"','"'+str(ROOT/'experiments/ghost/audio.h')+'"')
 h=change(h,'unsigned edit_feedback,motion_active,active,actual_freeze,capture_acquired,onsets,accepted,selection_dirty,clean_latched;','unsigned edit_feedback,motion_active,active,actual_freeze,capture_acquired,onsets,accepted,selection_dirty,clean_latched; unsigned performance_owner; uint64_t manual_until[C1_DESTS]; unsigned modulation_seed,automation_mask;')
 (SRC/'c1.h').write_text(h)
 for name in ['motion.c','params.c','state.c','factory_product.h']:(SRC/name).write_text(read(e/name))
 core=read(e/'core.c');core=change(core,'if(memcmp(&c->clock.config,&e,sizeof e)&&!ghost_configure(&c->clock,&e))return 0;','if(!c->performance_owner&&memcmp(&c->clock.config,&e,sizeof e)&&!ghost_configure(&c->clock,&e))return 0;')
 core=change(core,'c->state.manual[d]=value;c->manual_mask|=1u<<d;','c->state.manual[d]=value;c->manual_mask|=1u<<d;if(c->performance_owner)c->manual_until[d]=c->clock.sample+(uint64_t)(c->clock.rate*.5);')
 # Extract the SAME routing stage once; COMPAT and Performance share sources/smoothing.
 begin=core.index('if(f.flags&G_START){c->manual_mask=0;')
 end=core.index('  if(f.flags&G_CAPTURE_PULSE)',begin)
 body=core[begin:end]
 body=body.replace('c->manual_mask=0;c->random_mask=0;', 'if(!c->performance_owner)c->manual_mask=0;c->random_mask=0;')
 body=body.replace('for(unsigned d=4;d<C1_DESTS;++d)', 'for(unsigned d=c->performance_owner?0:4;d<C1_DESTS;++d)')
 body=body.replace('if(!q->enabled||q->depth<=0', 'if((c->performance_owner&&(d==C1_CAPTURE||d==C1_FREEZE||d==C1_GATE))||!q->enabled||q->depth<=0')
 body=body.replace('float target_mix=c->state.manual[C1_MIX];EConfig effective=f.effective;', 'float target_mix=c->state.manual[C1_MIX];EConfig effective=*config;')
 body=body.replace('c->edge_mask&=~(1u<<d);continue;}', 'c->edge_mask&=~(1u<<d);if(c->performance_owner){c->automation_mask&=~(1u<<d);c->route_value[d]=mod_value(config,c->state.manual[C1_MIX],d);}continue;}')
 body=body.replace('if(c->state.locked[d]||(c->manual_mask&(1u<<d))', 'if((c->performance_owner&&(d==C1_CAPTURE||d==C1_FREEZE||d==C1_GATE))||c->state.locked[d]||(c->manual_mask&(1u<<d))')
 old='if(!use){c->edge_mask&=~(1u<<d);if(q->enabled&&!discrete(d)&&'
 new='if(!use){c->edge_mask&=~(1u<<d);if(c->performance_owner){if((c->automation_mask&(1u<<d))&&!discrete(d)){float target=mod_value(config,c->state.manual[C1_MIX],d);float step=(highs[d]-lows[d])/((float)c->clock.rate*.005f);c->route_value[d]=approach(c->route_value[d],target,step);set_value(&effective,&target_mix,d,c->route_value[d]);if(c->route_value[d]==target)c->automation_mask&=~(1u<<d);}continue;}if(q->enabled&&!discrete(d)&&'
 assert old in body;body=body.replace(old,new)
 body=body.replace('if(discrete(d)){unsigned high=', 'if(c->performance_owner)c->automation_mask|=1u<<d;\n   if(discrete(d)){unsigned high=')
 prefix='static float mod_value(const EConfig *e,float mix,unsigned d){const float v[]={e->ms,e->fracture,0,(float)e->freeze,e->position,e->buffer_ms,(float)e->reverse,e->bend,e->pitch,e->corrupt,mix,(float)e->gate};return v[d];}\n'
 helper=prefix+'float c1_modulate(C1 *c,const GFrame *f,unsigned onset,EConfig *config){\n if(c->performance_owner)for(unsigned d=0;d<C1_DESTS;++d)if(!c->state.random[d].enabled)c->random_mask&=~(1u<<d);\n'+body.replace('f.','f->')+'\n *config=effective;return target_mix;\n}\n'
 core=core[:begin]+'EConfig effective=f.effective;float target_mix=c1_modulate(c,&f,onset,&effective);\n'+core[end:]
 pos=core.index('unsigned c1_process(');core=core[:pos]+helper+core[pos:]
 core=core.replace('ghost_random(c->state.event.seed,n,domain)','ghost_random(c->performance_owner?c->modulation_seed:c->state.event.seed,n,domain)')
 (SRC/'core.c').write_text(core)
 motion=read(e/'motion.c').replace('m->seed^c->state.event.seed','m->seed^(c->performance_owner?c->modulation_seed:c->state.event.seed)')
 (SRC/'motion.c').write_text(motion)
 state=read(e/'state.c').replace('c->dice_mask=c->manual_mask=c->pending_capture=0;','c->dice_mask=c->manual_mask=c->pending_capture=0;c->automation_mask=0;memset(c->manual_until,0,sizeof c->manual_until);')
 (SRC/'state.c').write_text(state)

 base=read(e/'base.c').replace('"../../build/ghost-c11-demo/base-render.inc"','"'+str(ROOT/'build/ghost-c11-demo/base-render.inc')+'"')
 base=change(base,'#include "'+str(ROOT/'build/ghost-c11-demo/base-render.inc')+'"','extern void ghost_pe_wet(AEffect *,float *,float *);\n#include "performance-base.inc"')
 (SRC/'base.c').write_text(base)
 inc=read(ROOT/'build/ghost-c11-demo/base-render.inc');inc=change(inc,'if(valid && running)engine_tick(&p->engine,l,r,tempo,&wl,&wr);','if(valid && running)engine_tick(&p->engine,l,r,tempo,&wl,&wr);ghost_pe_wet(fx,&wl,&wr);')
 (SRC/'performance-base.inc').write_text(inc)
 # Private engine already selected by Buffer Engine; no changes to its algorithms/storage.
 engine=read(ROOT/'experiments/ghost-buffer/engine.inc')
 engine=change(engine,'else if((force || r->captured<0 || r->voice.bank!=(int)r->live)', 'else if(r->repeat && r->captured>=0 && r->captured!=(int)r->live){ /* pinned manual region; LIVE writer owns another bank */ }\n    else if((force || r->captured<0 || r->voice.bank!=(int)r->live)')
 engine=change(engine,'    int want=!r->clean', """    /* Pin only after sufficient history; rotating writer is O(1), no copy/allocation.
    * A HELD take and an active recorder retain their own bank ownership. */
    if(r->repeat && !r->source_held && !r->clean && (r->captured<0 || r->captured==(int)r->live)){
        unsigned needed=(unsigned)lroundf(r->effective_ms*r->rate/1000);
        unsigned limit=(unsigned)(r->effective.buffer_ms*r->rate/1000);
        if(needed>limit)needed=limit;if(needed>r->capacity)needed=r->capacity;if(needed<2)needed=2;
        if(r->count[r->live]>=needed){int next=free_bank(e);if(next>=0){
            region(e,1);r->live=(unsigned)next;r->write[next]=r->count[next]=0;r->total[next]=0;
        }}
    }
    int want=!r->clean""")
 engine=change(engine,'if(!r->cycle_allowed || (r->base.run && !r->scene_on))','if(!r->repeat && (!r->cycle_allowed || (r->base.run && !r->scene_on)))')
 (SRC/'engine.c').write_text(engine)
 v=read(e/'vst.c');v=change(v,'#include "controls.h"','#include "controls.h"\n#include "performance.h"')
 v=change(v,' AEffect fx,*base;audioMasterCallback host;C1 instrument;',''' AEffect fx,*base;audioMasterCallback host;C1 instrument;
 Performance performance;_Atomic unsigned pe_view[PE_COUNT],pe_saved[PE_CONTROLS],pe_saved_variant,pe_saved_revision,pe_nominal,pe_had_event;
 float pe_pending[PE_CONTROLS],pe_pending_buffer[2];unsigned pe_pending_variant,pe_pending_revision,pe_pending_has_program;
 unsigned char pe_factory_base[16][532],pe_factory_c1[16][4096];unsigned pe_factory_bn[16],pe_factory_cn[16];_Atomic unsigned pe_preset_request;''')
 v=change(v,'static void snapshot(Wrapper *w){','static void snapshot(Wrapper *w){') # counted snapshot below
 v=change(v,'atomic_fetch_add(&w->revision,1);}\nstatic void refresh', '''for(unsigned k=0;k<PE_CONTROLS;++k)atomic_store(&w->pe_saved[k],bits(k==PE_DICE||k==PE_EDITOR?0:k==PE_PRESET?atomic_load(&w->product_program)/15.f:w->performance.p[k]));atomic_store(&w->pe_saved_variant,w->performance.variant);atomic_store(&w->pe_saved_revision,w->performance.modern);atomic_fetch_add(&w->revision,1);}
static void refresh''')
 v=change(v,'static void refresh(Wrapper *w){','''static void refresh(Wrapper *w){
 atomic_store(&w->pe_had_event,w->performance.events>0);atomic_store(&w->pe_nominal,bits(w->performance.p[PE_MODE]<.5f&&ghost_br_engine(w->base)->r.repeat?ghost_br_engine(w->base)->r.effective_ms:w->performance.nominal));
 for(unsigned i=0;i<PE_COUNT;++i)atomic_store(&w->pe_view[i],bits(i==PE_PRESET?atomic_load(&w->product_program)/15.f:pe_read(&w->performance,i)));''')
 v=change(v,' if(w->host||',' if(w->host||') if ' if(w->host||' in v else v
 # notifier reads published atomics, never Performance mutable state
 v=change(v,'if(changed)w->host(&w->fx,audioMasterUpdateDisplay,0,0,NULL,0);','''static_unused: ;
 for(unsigned i=0;i<PE_COUNT;++i){unsigned x=atomic_load(&w->pe_view[i]);if(x!=pe_seen[i]){pe_seen[i]=x;changed=1;}}
 if(changed)w->host(&w->fx,audioMasterUpdateDisplay,0,0,NULL,0);''').replace('static_unused: ;','')
 v=change(v,'static void *notify(void *arg){Wrapper *w=arg;','static void *notify(void *arg){Wrapper *w=arg;unsigned pe_seen[PE_COUNT];for(unsigned i=0;i<PE_COUNT;++i)pe_seen[i]=~0u;')
 v=change(v,'static void set(AEffect *fx,int32_t id,float x){','static intptr_t dispatch(AEffect *,int32_t,int32_t,intptr_t,void *,float);\nstatic void set(AEffect *fx,int32_t id,float x){')
 v=change(v,' /* Host gestures have no source tag:', ''' if(id==LEGACY&&x>=.5f)enqueue(w,1000+PE_MODE,0);
 if(id>=(int)PE_FIRST){unsigned i=(unsigned)id-PE_FIRST;if(i==PE_PRESET){float old=atomic_load(&w->product_program)/15.f;if(x>0&&x<1&&x!=old&&fabsf(x-old)<.5f/15)x=fmaxf(0,fminf(1,old+(x>old?1.f:-1.f)/15));atomic_store(&w->pe_preset_request,(unsigned)lroundf(x*15)+1);return;}if(i<PE_CONTROLS)enqueue(w,1000+i,x);return;}
 /* Host gestures have no source tag:''')
 v=change(v,'static float get(AEffect *fx,int32_t id){Wrapper *w=fx->object;','static float get(AEffect *fx,int32_t id){Wrapper *w=fx->object;if(id>=(int)PE_FIRST&&id<(int)PE_PARAMS)return value(atomic_load(&w->pe_view[id-PE_FIRST]));')
 v=change(v,'if(be->r.repeat){ghost_buffer_rearm(be);','if(be->r.repeat){if(w->performance.p[PE_MODE]<.5f){float x=(8*powf(50,w->performance.p[PE_SIZE])-5)/445;w->base->setParameter(w->base,TIME_MODE,0);atomic_store(&w->target[TIME_MODE],bits(0));w->base->setParameter(w->base,0,x);atomic_store(&w->target[0],bits(x));}ghost_buffer_rearm(be);')
 v=change(v,'c1_load(&w->instrument,w->pending,w->pending_size);','''c1_load(&w->instrument,w->pending,w->pending_size);
 pe_init(&w->performance,0);memcpy(w->performance.p,w->pe_pending,sizeof(w->pe_pending));w->performance.variant=w->pe_pending_variant;w->performance.modern=w->pe_pending_revision;if(w->pe_pending_has_program)atomic_store(&w->product_program,(unsigned)lroundf(w->pe_pending[PE_PRESET]*15));w->instrument.performance_owner=w->performance.p[PE_MODE]>=.5f;''')
 v=change(v,'if(command.epoch==atomic_load(&w->epoch)){','''if(command.epoch==atomic_load(&w->epoch)){
 if(command.param>=1000&&command.param<1000+PE_CONTROLS){unsigned i=command.param-1000;pe_set(&w->performance,i,command.value);if(i==PE_SIZE&&w->performance.p[PE_MODE]<.5f&&ghost_br_engine(w->base)->r.repeat){float x=(8*powf(50,command.value)-5)/445;w->base->setParameter(w->base,TIME_MODE,0);atomic_store(&w->target[TIME_MODE],bits(0));w->base->setParameter(w->base,0,x);atomic_store(&w->target[0],bits(x));}w->instrument.performance_owner=w->performance.p[PE_MODE]>=.5f;if(i==PE_MODE&&command.value>=.5f){w->base->setParameter(w->base,LEGACY,0);atomic_store(&w->target[LEGACY],bits(0));w->instrument.clean_latched=0;ghost_buffer_rearm(ghost_br_engine(w->base));}}
 else''')
 v=change(v,'if(atomic_exchange(&w->clean,0)){','if(atomic_exchange(&w->clean,0)){pe_clean(&w->performance);w->instrument.performance_owner=0;')
 v=change(v,'unsigned commands=w->instrument.commands;c1_process(&w->instrument,&l,&r,NULL,NULL,1,NULL,0);','''unsigned commands=w->instrument.commands;
 if(w->performance.p[PE_MODE]>=.5f){C1 *c=&w->instrument;float energy=fmaxf(fabsf(l),fabsf(r));c->fast+=(energy-c->fast)*c->fast_coefficient;c->slow+=(energy-c->slow)*c->slow_coefficient;if(fabsf(c->fast)<1e-25f)c->fast=0;if(fabsf(c->slow)<1e-25f)c->slow=0;c->energy=fmaxf(0,fminf(1,c->fast));pe_tick(&w->performance,c);}
 else{if(w->performance.was_mode){w->instrument.performance_owner=0;w->performance.was_mode=0;c1_apply(&w->instrument,&w->instrument.state);}c1_process(&w->instrument,&l,&r,NULL,NULL,1,NULL,0);}''')
 v=change(v,' if(!generated(w))return;EConfig *e=', ' if(w->performance.p[PE_MODE]>=.5f){pe_config(&w->performance,c,config);return;}\n if(ghost_br_engine(base)->r.repeat)config->time_grid=0;\n if(!generated(w))return;EConfig *e=')
 v=change(v,'\n}\nfloat ghost_c11_mix','\n if(ghost_br_engine(base)->r.repeat)config->time_grid=0;\n}\nfloat ghost_c11_mix')
 v=change(v,'float ghost_c11_mix(AEffect *base,float manual){Wrapper *w=(Wrapper*)base->resvd1;return w&&generated(w)?w->instrument.last_mix:manual;}','''float ghost_c11_mix(AEffect *base,float manual){Wrapper *w=(Wrapper*)base->resvd1;return w&&((w->performance.p[PE_MODE]<.5f&&generated(w))||(w->performance.modern&&w->performance.p[PE_MODE]>=.5f&&(w->instrument.automation_mask&(1u<<C1_MIX))))?w->instrument.last_mix:manual;}
void ghost_pe_wet(AEffect *base,float *l,float *r){Wrapper *w=(Wrapper*)base->resvd1;if(w&&w->performance.p[PE_MODE]>=.5f){*l*=w->performance.wet_gain;*r*=w->performance.wet_gain;}}''')
 # A host suspend must not rewrite the musical mode; COMPAT retains the baseline behavior.
 v=change(v,'if(!n)atomic_store(&w->clean,1);','if(!n&&value(atomic_load(&w->pe_view[PE_MODE]))<.5f)atomic_store(&w->clean,1);')
 v=change(v,'ghost_clock(&w->instrument.clock,w->time.tempo,playing,seek,w->time.ppqPos);','ghost_clock(&w->instrument.clock,w->time.tempo,playing,seek,w->time.ppqPos);if(seek||w->performance.was_playing!=playing){w->performance.was_mode=0;w->performance.was_playing=playing;}')
 v=change(v,'if(w->have_time&&(w->time.flags&kVstTempoValid)){','if(w->have_time&&(w->time.flags&kVstTempoValid)&&(w->performance.p[PE_MODE]<.5f||ghost_br_peek(w->base,SYNC_MODE)>=.5f)){')
 v=change(v,' if(accumulate)w->base->process',' if((!w->have_time||!(w->time.flags&kVstTempoValid)||ghost_br_peek(w->base,SYNC_MODE)<.5f)&&w->performance.p[PE_MODE]>=.5f)ghost_clock(&w->instrument.clock,40+200*ghost_br_peek(w->base,TEMPO),1,0,0);\n if(accumulate)w->base->process')
 v=change(v,'refresh(w);snapshot(w);if(pthread_create','''refresh(w);snapshot(w);
 {void *initial=NULL;intptr_t initial_n=dispatch(&w->fx,effGetChunk,0,0,&initial,0);unsigned char initial_bytes[8192];
  if(initial_n<=0||initial_n>(intptr_t)sizeof(initial_bytes)){w->base->dispatcher(w->base,effClose,0,0,NULL,0);free(w);return NULL;}
  memcpy(initial_bytes,initial,(size_t)initial_n);
  for(unsigned n=0;n<16;++n){
   if(!dispatch(&w->fx,effSetProgram,0,n,NULL,0)){w->base->dispatcher(w->base,effClose,0,0,NULL,0);free(w);return NULL;}
   receive(w);buffer_apply(w);sync_manual(w,0);c1_commit_commands(&w->instrument);refresh(w);snapshot(w);
   void *base=NULL;intptr_t bn=w->base->dispatcher(w->base,effGetChunk,0,0,&base,0);
   if(bn<=0||bn>532){w->base->dispatcher(w->base,effClose,0,0,NULL,0);free(w);return NULL;}
   w->pe_factory_bn[n]=(unsigned)bn;memcpy(w->pe_factory_base[n],base,(size_t)bn);
   w->pe_factory_cn[n]=(unsigned)c1_save(&w->instrument,w->pe_factory_c1[n],4096);
  }
  if(!dispatch(&w->fx,effSetChunk,0,initial_n,initial_bytes,0)){w->base->dispatcher(w->base,effClose,0,0,NULL,0);free(w);return NULL;}
  receive(w);buffer_apply(w);sync_manual(w,0);c1_commit_commands(&w->instrument);atomic_store(&w->product_program,0);refresh(w);snapshot(w);
 }
 if(pthread_create''')
 # New metadata before old range clauses so no new ID can fall into old buffer aliases.
 v=change(v,' DIAG_ADD(w,dispatch,1);',''' DIAG_ADD(w,dispatch,1);
 if(idx>=(int)PE_FIRST&&idx<(int)PE_PARAMS){
  unsigned i=(unsigned)idx-PE_FIRST;static const char *names[]={"PERFORM","GLITCH","CHAOS","SIZE","REPEAT","REVERSE","CUT","REST","MOTION","RATE","DICE","EDIT","PRESET","EVENT","VARIANT","FRAG ms","BUDGET"};
  if(op==effCanBeAutomated)return i<PE_CONTROLS&&i!=PE_EDITOR;
  if(op==effGetParamName){text(data,names[i],8);return 1;}
  if(op==effGetParamLabel){text(data,i==PE_SIZE||i==PE_LENGTH?"ms":i==PE_RATE?"beats":"",8);return 1;}
  if(op==effGetParamDisplay){if(i==PE_LENGTH&&!atomic_load(&w->pe_had_event)){text(data,"--",8);return 1;}float x=get(fx,idx);char b[32];
   if(i==PE_MODE)text(data,x>=.5f?"RUN":"COMPAT",8);
   else if(i==PE_ACTIVITY){static const char *events[]={"REST","REPEAT","REVERSE","CUT"};text(data,events[(unsigned)lroundf(x*3)%4],8);}
   else if(i==PE_EDITOR){static const char *sections[]={"BUFFER","MOTION","RANDOM","TIMING","GLOBAL","MIDI","SCENES","LEGACY"};text(data,sections[(unsigned)lroundf(x*7)%8],8);}
   else{if(i==PE_SIZE)x=value(atomic_load(&w->pe_nominal));else if(i==PE_LENGTH)x=5+445*x;else if(i==PE_VARIANT)x=roundf(x*65535);else if(i==PE_RATE)x=powf(1024,x)/64;else if(i==PE_PRESET)x=roundf(x*15)+1;else x*=100;snprintf(b,sizeof b,"%.2f",x);text(data,b,8);}return 1;}
 }
''')
 # Wrap GBF1 only at effGetChunk. All original chunk readers retained.
 v=change(v,'*(void**)data=w->chunk;return size+16;','''unsigned revision=atomic_load(&w->pe_saved_revision),inner=size+16,pe_extra=20+4*PE_CONTROLS+4+(revision?4:0),total=inner+pe_extra+4;if(total>sizeof(w->chunk))return 0;
 memmove(w->chunk+pe_extra,w->chunk,inner);memcpy(w->chunk,"PEF1",4);unsigned version=revision?2:1,count=PE_CONTROLS;memcpy(w->chunk+4,&version,4);memcpy(w->chunk+8,&total,4);memcpy(w->chunk+12,&inner,4);memcpy(w->chunk+16,&count,4);
 for(unsigned k=0;k<PE_CONTROLS;++k){unsigned x=atomic_load(&w->pe_saved[k]);memcpy(w->chunk+20+4*k,&x,4);}unsigned variant=atomic_load(&w->pe_saved_variant);memcpy(w->chunk+20+4*PE_CONTROLS,&variant,4);if(revision)memcpy(w->chunk+24+4*PE_CONTROLS,&revision,4);
 if(atomic_load(&w->revision)!=rev)return 0;unsigned check=pe_checksum(w->chunk,total-4);memcpy(w->chunk+total-4,&check,4);*(void**)data=w->chunk;return total;''')
 # Strip the outer header in the same dispatch frame, before original validation or mutation.
 v=change(v,' case effSetChunk:{',''' case effSetChunk:{
 float pe_values[PE_CONTROLS];Performance initial;pe_init(&initial,0);memcpy(pe_values,initial.p,sizeof(pe_values));unsigned pe_variant=0,pe_revision=0,pe_has_program=0;
 if(data&&n>=4&&!memcmp(data,"PEF1",4)){
  unsigned version,total,inner,count,check;unsigned extra=20+4*PE_CONTROLS+4;
  if(n<(intptr_t)(extra+4)||n>8192)return 0;
  memcpy(&version,(char*)data+4,4);memcpy(&total,(char*)data+8,4);memcpy(&inner,(char*)data+12,4);memcpy(&count,(char*)data+16,4);memcpy(&check,(char*)data+n-4,4);
  if(version==2){extra+=4;if(n<(intptr_t)(extra+4))return 0;memcpy(&pe_revision,(char*)data+24+4*PE_CONTROLS,4);if(pe_revision!=1)return 0;}\n  if((version!=1&&version!=2)||total!=(unsigned)n||count!=PE_CONTROLS||inner>total||inner+extra+4!=total||check!=pe_checksum(data,total-4))return 0;
  memcpy(pe_values,(char*)data+20,sizeof(pe_values));memcpy(&pe_variant,(char*)data+20+sizeof(pe_values),4);
  if(!pe_valid(pe_values,pe_variant)||pe_values[PE_DICE]!=0||pe_values[PE_EDITOR]!=0||fabsf(pe_values[PE_PRESET]*15-roundf(pe_values[PE_PRESET]*15))>.00001f||inner<4||memcmp((char*)data+extra,"GBF1",4))return 0;
  pe_has_program=1;data=(char*)data+extra;n=inner;
 }
''')
 # Existing GBF recursion would lose decoded PE fields. Decode its extras inline and apply at atomic recall publish.
 start=v.index(' if(data&&n>=16&&n<=8192&&!memcmp(data,"GBF1",4)){',v.index(' case effSetChunk:{'))
 end=v.index('\n#endif',start)
 v=v[:start]+''' float buffer_extra[3]={1,0,0};
 if(data&&n>=16&&n<=8192&&!memcmp(data,"GBF1",4)){
  memcpy(buffer_extra,(char*)data+4,12);if(!isfinite(buffer_extra[0])||buffer_extra[0]<0||buffer_extra[0]>1||!isfinite(buffer_extra[1])||buffer_extra[1]<0||buffer_extra[1]>1||buffer_extra[2]!=0)return 0;
  data=(char*)data+16;n-=16;
 }'''+v[end:]
 v=change(v,'w->pending_size=(unsigned)c1_save(temporary,w->pending,sizeof w->pending);','''memcpy(w->pe_pending,pe_values,sizeof(pe_values));w->pe_pending_variant=pe_variant;w->pe_pending_revision=pe_revision;w->pe_pending_has_program=pe_has_program;
 w->pe_pending_buffer[0]=buffer_extra[0];w->pe_pending_buffer[1]=buffer_extra[1];
 w->pending_size=(unsigned)c1_save(temporary,w->pending,sizeof w->pending);''')
 # Native preset gestures coalesce to one bounded cached recall per callback. No heap/host/UI callbacks.
 v=change(v,' if(atomic_exchange(&w->chaos_pending,0)',''' unsigned selected=atomic_exchange(&w->pe_preset_request,0);
 if(selected){unsigned expected=0,n=selected-1;
  if(n<16&&atomic_compare_exchange_strong(&w->recall,&expected,2)){
   if(w->base->dispatcher(w->base,effSetChunk,0,w->pe_factory_bn[n],w->pe_factory_base[n],0)){
    w->instrument.performance_owner=0;c1_load(&w->instrument,w->pe_factory_c1[n],w->pe_factory_cn[n]);pe_init(&w->performance,0);
    w->buffer_pending=6;w->buffer_value[1]=1;w->buffer_value[2]=0;atomic_store(&w->product_program,n);
    for(unsigned i=0;i<49;++i)atomic_store(&w->target[i],bits(ghost_br_peek(w->base,(int)i)));
   }else{unsigned empty=0;atomic_compare_exchange_strong(&w->pe_preset_request,&empty,selected);}
   atomic_store_explicit(&w->recall,0,memory_order_release);
  }else{unsigned empty=0;atomic_compare_exchange_strong(&w->pe_preset_request,&empty,selected);}
 }
 if(atomic_exchange(&w->chaos_pending,0)''')
 v=change(v,'if(atomic_load(&w->chaos_pending)||','if(atomic_load(&w->pe_preset_request)||atomic_load(&w->chaos_pending)||')
 # Receive initializes default buffer flags but must preserve verified recalled extra values.
 v=change(v,'w->buffer_pending=6;w->buffer_value[0]=0;w->buffer_value[1]=1;w->buffer_value[2]=0;','w->buffer_pending=6;w->buffer_value[0]=0;w->buffer_value[1]=w->pe_pending_buffer[0];w->buffer_value[2]=w->pe_pending_buffer[1];')
 v=change(v,'w->fx.numParams=131;atomic_store(&w->buffer_view[1],bits(1));','w->fx.numParams=PE_PARAMS;pe_init(&w->performance,1);w->instrument.performance_owner=1;atomic_store(&w->buffer_view[1],bits(1));')
 # New metadata gets uint8 names; preserve original diagnostics and export visibility.
 v+='''\nvoid ghost_pe_stats(AEffect *fx,uint64_t *stats){Wrapper *w=fx->object;Performance *p=&w->performance;stats[0]=p->events;stats[1]=p->active_samples;stats[2]=p->elapsed_samples;for(unsigned i=0;i<3;++i)stats[3+i]=p->families[i];}\n'''
 from random_repeat_patch import apply
 v=apply(v)
 (SRC/'vst.c').write_text(v)
 # Copy local policy sources so they resolve the isolated C1 struct, never a parent header.
 for name in ['performance.h','performance.c','random_repeat.h']:(SRC/name).write_text(read(ROOT/'experiments/ghost-performance'/name))
 (OUT/'integration-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
 return SRC
if __name__=='__main__':print(generate())
