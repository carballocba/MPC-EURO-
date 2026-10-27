"""Bounded adapter additions. Existing codecs and public indices remain intact."""
def apply(v):
 def change(a,b):
  nonlocal v
  assert v.count(a)==1,a[:90]
  v=v.replace(a,b)
 change('#include "performance.h"','#include "performance.h"\n#include "random_repeat.h"')
 change('Performance performance;','Performance performance;RandomRepeat rr;_Atomic unsigned rr_view[RR_COUNT],rr_saved[RR_CONTROLS],rr_requested;float rr_pending[RR_CONTROLS];')
 change('static void snapshot(Wrapper *w){','static void snapshot(Wrapper *w){for(unsigned k=0;k<RR_CONTROLS;++k)atomic_store(&w->rr_saved[k],bits(w->rr.p[k]));')
 change('static void refresh(Wrapper *w){','static void refresh(Wrapper *w){for(unsigned k=0;k<RR_COUNT;++k)atomic_store(&w->rr_view[k],bits(k<RR_CONTROLS?w->rr.p[k]:k==6?(float)w->rr.actual:(ghost_br_engine(w->base)->r.playing?fminf(1,ghost_br_engine(w->base)->r.voice.length*1000.f/(w->rate*450)):0)));')
 change('static void set(AEffect *fx,int32_t id,float x){','static void set(AEffect *fx,int32_t id,float x){if(id>=(int)RR_FIRST&&id<(int)RR_PARAMS){Wrapper *w=fx->object;if(id<(int)(RR_FIRST+RR_CONTROLS)&&isfinite(x)){if(id==(int)RR_FIRST)atomic_store(&w->rr_requested,1);enqueue(w,2000+(unsigned)id-RR_FIRST,fmaxf(0,fminf(1,x)));}return;}')
 change('static float get(AEffect *fx,int32_t id){Wrapper *w=fx->object;','static float get(AEffect *fx,int32_t id){Wrapper *w=fx->object;if(id>=(int)RR_FIRST&&id<(int)RR_PARAMS)return value(atomic_load(&w->rr_view[id-RR_FIRST]));')
 # Gestures use the same SPSC command path; no GUI thread writes audio-owned state.
 change('if(id==LEGACY&&x>=.5f)','if(id==LEGACY&&x>=.5f)enqueue(w,2000,0);if(id==128)enqueue(w,2006,0);if(id==134)enqueue(w,2007,0);if(id==LEGACY&&x>=.5f)')
 change('if(command.param>=1000&&command.param<1000+PE_CONTROLS){','''if(command.param>=2000&&command.param<2008){unsigned k=command.param-2000;
 if(k<6){unsigned previous_mode=rr_mode(&w->rr);if(k==0&&previous_mode==3&&roundf(command.value*3)==3){atomic_store(&w->rr_requested,0);}else{w->rr.p[k]=k==0?roundf(command.value*3)/3:command.value;w->rr.config_dirty=1;
  if(k==0){atomic_store(&w->rr_requested,0);unsigned mode=rr_mode(&w->rr);pe_set(&w->performance,PE_MODE,mode>=2?1:0);w->instrument.performance_owner=mode>=2;if(!((mode==3&&(previous_mode==1||previous_mode==3))||(mode==1&&previous_mode==3))){w->rr.initialized=0;w->rr.on=0;}if(mode){w->base->setParameter(w->base,LEGACY,0);atomic_store(&w->target[LEGACY],bits(0));w->instrument.clean_latched=0;ghost_buffer_rearm(ghost_br_engine(w->base));}}}}
 else if(k==6)w->rr.manual_until=w->instrument.clock.sample+(uint64_t)(w->rate*.5);
 else w->rr.fragment_until=w->instrument.clock.sample+(uint64_t)(w->rate*.5);
 }
 else if(command.param>=1000&&command.param<1000+PE_CONTROLS){''')
 change('pe_set(&w->performance,i,command.value);','pe_set(&w->performance,i,command.value);if(i==PE_MODE){unsigned rr=rr_enabled(&w->rr);w->rr.p[0]=(command.value>=.5f?(rr?3.f:2.f):(rr?1.f:0.f))/3;}')
 change('pe_clean(&w->performance);w->instrument.performance_owner=0;','pe_clean(&w->performance);w->rr.p[0]=0;w->rr.on=w->rr.applied=0;w->instrument.performance_owner=0;')
 change('atomic_store(&w->buffer_view[2],bits((float)br->repeat));','atomic_store(&w->buffer_view[2],bits(w->buffer_value[2]));')
 change(' return commands||w->instrument.capture_requested||w->instrument.control_dirty;',' if(w->instrument.clean_latched)w->buffer_value[2]=0;rr_tick(&w->rr,&w->instrument,&w->performance,be,w->buffer_value[2]>=.5f);unsigned rr_dirty=w->rr.config_dirty;w->rr.config_dirty=0;\n return rr_dirty||commands||w->instrument.capture_requested||w->instrument.control_dirty;')
 change('pe_config(&w->performance,c,config);return;','pe_config(&w->performance,c,config);rr_config(&w->rr,c,&w->performance,config);return;')
 change(' if(!generated(w))return;EConfig *e=', ' if(!generated(w)){rr_config(&w->rr,c,&w->performance,config);return;}EConfig *e=')
 change('\n}\nfloat ghost_c11_mix','\n rr_config(&w->rr,c,&w->performance,config);\n}\nfloat ghost_c11_mix')
 v=v.replace('w->performance.p[PE_MODE]<.5f||ghost_br_peek(w->base,SYNC_MODE)>=.5f','(w->performance.p[PE_MODE]<.5f&&!rr_enabled(&w->rr))||ghost_br_peek(w->base,SYNC_MODE)>=.5f')
 change('&&w->performance.p[PE_MODE]>=.5f)ghost_clock','&&(w->performance.p[PE_MODE]>=.5f||rr_enabled(&w->rr)))ghost_clock')
 change('C1 *temporary=calloc(1,sizeof(*temporary));','if(rr_outer&&((rr_values[0]>=.5f)!=(pe_values[PE_MODE]>=.5f)))return 0;C1 *temporary=calloc(1,sizeof(*temporary));')
 change('unsigned pe_seen[PE_COUNT];','unsigned rr_seen[RR_COUNT];for(unsigned k=0;k<RR_COUNT;++k)rr_seen[k]=~0u;unsigned pe_seen[PE_COUNT];')
 change('if(changed)w->host(&w->fx,audioMasterUpdateDisplay','for(unsigned k=0;k<RR_COUNT;++k){unsigned x=atomic_load(&w->rr_view[k]);if(x!=rr_seen[k]){rr_seen[k]=x;changed=1;}}if(changed)w->host(&w->fx,audioMasterUpdateDisplay')
 change('if(!n&&value(atomic_load(&w->pe_view[PE_MODE]))<.5f)atomic_store','if(!n&&value(atomic_load(&w->pe_view[PE_MODE]))<.5f&&!(value(atomic_load(&w->rr_view[0]))>0)&&!atomic_load(&w->rr_requested))atomic_store')
 # Restore/init only at existing audio-owner recall boundaries.
 v=v.replace('pe_init(&w->performance,0);','pe_init(&w->performance,0);rr_init(&w->rr,0);')
 change('memcpy(w->performance.p,w->pe_pending,sizeof(w->pe_pending));','memcpy(w->performance.p,w->pe_pending,sizeof(w->pe_pending));memcpy(w->rr.p,w->rr_pending,sizeof(w->rr.p));')
 change('pe_init(&w->performance,1);','pe_init(&w->performance,1);rr_init(&w->rr,1);')
 change('w->fx.numParams=PE_PARAMS;','w->fx.numParams=RR_PARAMS;')
 change(' DIAG_ADD(w,dispatch,1);',''' DIAG_ADD(w,dispatch,1);
 if(idx>=(int)RR_FIRST&&idx<(int)RR_PARAMS){unsigned k=(unsigned)idx-RR_FIRST;static const char *names[]={"RR MODE","RR INT","RR PROB","RR VAR","RR RATE","RR HOLD","RR LIVE","RR MS"};
  if(op==effCanBeAutomated)return k<6;
  if(op==effGetParamName){text(data,names[k],8);return 1;}
  if(op==effGetParamLabel){text(data,k==7?"ms":k==4?"beats":k==5?"steps":k==0||k==6?"":"%",8);return 1;}
  if(op==effGetParamDisplay){float x=get(fx,idx);char b[24];if(k==0){static const char *mode[]={"MANUAL","INDEP","PERFORM","BOTH"};text(data,mode[(unsigned)lroundf(x*3)%4],8);}else if(k==6)text(data,x>=.5f?"REPEAT":"REST",8);else{snprintf(b,sizeof b,"%.2f",k==7?x*450:k==4?2/powf(2,roundf(x*5)):k==5?1+floorf(x*7):x*100);text(data,b,8);}return 1;}
 }
''')
 change('float pe_values[PE_CONTROLS];Performance initial;','''float rr_values[RR_CONTROLS];unsigned rr_outer=0;RandomRepeat rr_default;rr_init(&rr_default,0);memcpy(rr_values,rr_default.p,sizeof rr_values);
 if(data&&n>=4&&!memcmp(data,"RRF1",4)){unsigned version,total,inner,check;if(n<44||n>8192)return 0;memcpy(&version,(char*)data+4,4);memcpy(&total,(char*)data+8,4);memcpy(&inner,(char*)data+12,4);memcpy(&check,(char*)data+n-4,4);if(version!=1||total!=(unsigned)n||inner>total||inner+44!=total||check!=pe_checksum(data,total-4))return 0;memcpy(rr_values,(char*)data+16,sizeof rr_values);if(!rr_valid(rr_values)||inner<4||memcmp((char*)data+40,"PEF1",4))return 0;rr_outer=1;data=(char*)data+40;n=inner;}
 float pe_values[PE_CONTROLS];Performance initial;''')
 change('memcpy(w->pe_pending,pe_values,sizeof(pe_values));','''if(!rr_outer)rr_values[0]=pe_values[PE_MODE]>=.5f?2.f/3:0;
 
 memcpy(w->rr_pending,rr_values,sizeof rr_values);memcpy(w->pe_pending,pe_values,sizeof(pe_values));''')
 change('*(void**)data=w->chunk;return total;','''RandomRepeat defaults;rr_init(&defaults,0);unsigned needs=0;float rr_values[6];for(unsigned k=0;k<6;++k){rr_values[k]=value(atomic_load(&w->rr_saved[k]));if(k?rr_values[k]!=defaults.p[k]:(rr_values[k]>0&&rr_values[k]<.5f)||rr_values[k]>.99f)needs=1;}
 if(needs){unsigned inner=total;total+=44;if(total>sizeof(w->chunk))return 0;memmove(w->chunk+40,w->chunk,inner);memcpy(w->chunk,"RRF1",4);unsigned version=1;memcpy(w->chunk+4,&version,4);memcpy(w->chunk+8,&total,4);memcpy(w->chunk+12,&inner,4);memcpy(w->chunk+16,rr_values,sizeof rr_values);unsigned check=pe_checksum(w->chunk,total-4);memcpy(w->chunk+total-4,&check,4);}if(atomic_load(&w->revision)!=rev)return 0;*(void**)data=w->chunk;return total;''')
 v+='\nvoid ghost_rr_stats(AEffect *fx,double *v){Wrapper *w=fx->object;v[0]=w->rr.starts;v[1]=w->rr.ends;v[2]=w->rr.changes;v[3]=w->rr.actual;v[4]=w->rr.fragment_ms;v[5]=w->rr.step;}\n'
 return v
