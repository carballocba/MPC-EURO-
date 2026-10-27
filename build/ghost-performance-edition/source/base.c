/* SPDX-License-Identifier: GPL-3.0-only. Include unchanged base implementation.
 * Canonical audio overlays deliberately leave Q-Link gesture cursors untouched.
 */
#define _POSIX_C_SOURCE 200809L
#define VSTPluginMain BRPluginMain
#include "c1.h"
#include "vst2_abi.h"
extern void ghost_c11_punch(AEffect *);
extern void ghost_c11_capture_result(AEffect *,unsigned);
extern unsigned ghost_c11_capture_request(AEffect *);
extern unsigned ghost_c11_tick(AEffect *,float,float,unsigned,unsigned);
extern void ghost_c11_config(AEffect *,EConfig *);
extern float ghost_c11_mix(AEffect *,float);
extern void ghost_pe_wet(AEffect *,float *,float *);
#include "performance-base.inc"
float ghost_br_peek(AEffect *fx,int id){return load((Plugin*)fx->object,id);}
void ghost_br_overlay(AEffect *fx,int id,float x){Plugin *p=fx->object;atomic_store_explicit(&p->target[id],bits(x),memory_order_relaxed);}
void ghost_br_cursor(AEffect *fx,int id,float x){Plugin *p=fx->object;if(id==MIX_LIVE)atomic_store(&p->live_input,bits(x));else if(id>=0&&id<NPARAMS&&(PARAMS[id].nopts||id==LENGTH))atomic_store(&p->enum_input[id],bits(x));}
size_t ghost_br_bytes(void){return sizeof(Plugin);}
/* Persist manual targets, never a temporary generative overlay observed mid-block. */
void ghost_br_persist(unsigned char *blob,const float *manual){
    for(unsigned i=0;i<NPARAMS;++i)u32(blob+12+4*i,bits(PARAMS[i].saved?manual[i]:0));
    u32(blob+STATE_SIZE-4,checksum(blob,STATE_SIZE-4));
}
/* Audio-owner telemetry; do not call from GUI threads. */
unsigned ghost_br_captured(AEffect *fx){Plugin *p=fx->object;return load(p,LEGACY)<.5f&&p->engine.r.captured>=0;}

Engine *ghost_br_engine(AEffect *fx){return &((Plugin*)fx->object)->engine;}

void ghost_br_clean(AEffect *fx){Plugin *p=fx->object;atomic_fetch_or(&p->commands,DO_PANIC);store(p,GATE,0);store(p,FREEZE,0);store(p,SEQ_RUN,0);}
