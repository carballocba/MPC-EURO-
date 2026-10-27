/* SPDX-License-Identifier: GPL-3.0-only
 * Copyright 2026 MPC-EURO contributors. SDK-free ABI derived from sd88me.
 * DSP is audio-owned. Only lock-free 32-bit scalar targets cross threads.
 * Lifecycle/state dispatch is host-serialized; close/prepare are not audio calls. */
#define _POSIX_C_SOURCE 200809L
#include "vst2_abi.h"
#include "repeat.h"
#include "params.h"
#include "controls.h"
#include "engine.h"
#include "factory.h"
#include <stdatomic.h>
#include <stddef.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <pthread.h>
#include <time.h>
_Static_assert(ATOMIC_INT_LOCK_FREE == 2, "Realtime path requires lock-free unsigned atomics");
_Static_assert(sizeof(float) == 4 && sizeof(unsigned) == 4, "32-bit float/unsigned required");
_Static_assert(NPARAMS == CONTROL_COUNT, "Parameter registry mismatch");
enum { CAPTURE, REPEATING, PRIMING, BYPASSED, BAD_RATE };
enum { UID=0x45754272, STATE_SIZE=16+4*NPARAMS+4*E_STATES*E_FIELDS, VERSION=200 };
enum { DO_CAPTURE=1, DO_STORE=2, DO_APPLY=4, DO_PANIC=8 };
typedef struct { int delta; unsigned char status,note,velocity; } Midi;
/* Stable fixed-storage radix sort, bounded O(4*(N+256)); no qsort/heap. */
static void ghost_c11_sort(Midi *events,unsigned n){
    if(n<2)return;Midi temporary[1024];
    for(unsigned shift=0;shift<32;shift+=8){unsigned count[256]={0},offset[256];
        for(unsigned i=0;i<n;++i)++count[((unsigned)events[i].delta>>shift)&255];
        unsigned sum=0;for(unsigned i=0;i<256;++i){offset[i]=sum;sum+=count[i];}
        for(unsigned i=0;i<n;++i)temporary[offset[((unsigned)events[i].delta>>shift)&255]++]=events[i];
        memcpy(events,temporary,n*sizeof(*events));
    }
}
typedef struct { atomic_uint revision,v[E_FIELDS]; } Scene;
typedef struct {
    AEffect fx;
    audioMasterCallback host;
    atomic_uint target[NPARAMS], enum_input[NPARAMS], rate, running, reset, punch_command, live_input;
    atomic_uint quit, opened;
    pthread_t notifier;
    Repeat repeat;
    Engine engine;
    Scene scenes[E_STATES];
    unsigned scene_seen[E_STATES];
    atomic_uint commands, midi_head, midi_tail, midi_dirty[2], host_tempo;
    Midi midi[1024];
    unsigned held_gate, held_freeze;
    int program, transport;
    float legacy_length,release_wet[2];

    float sample_rate, mix, gain, depth, last_wet;
    unsigned generation, punch_left, tail_left, retry;
    int wanted;
    unsigned char chunk[STATE_SIZE]; /* dispatcher-only, never touched by audio */
} Plugin;
static unsigned bits(float x) { unsigned u; memcpy(&u,&x,4); return u; }
static float value(unsigned u) { float x; memcpy(&x,&u,4); return x; }
static void store(Plugin *p, int i, float f) {
    atomic_store_explicit(&p->target[i],bits(f),memory_order_relaxed);
    if(i==LENGTH || (PARAMS[i].nopts && !PARAMS[i].readonly))
        atomic_store_explicit(&p->enum_input[i],bits(f),memory_order_relaxed);
}
static float load(Plugin *p, int i) { return value(atomic_load_explicit(&p->target[i==MIX_LIVE ? MIX : i],memory_order_relaxed)); }
static void set_parameter(AEffect *fx, int32_t i, float x) {
    Plugin *p=fx->object;
    if(i<0 || i>=NPARAMS || PARAMS[i].readonly || !isfinite(x)) return;
    x=fmaxf(0,fminf(1,x));float input=x,old_target=load(p,i);
    if(i==MIX_LIVE) {
        /* A dedicated Q-Link alias keeps original MIX's absolute automation and
         * preset semantics intact. Each relative move is 4x, in either direction.
         * Track the host's last input/readback: some hosts accumulate gestures,
         * others nudge from getParameter. Neither stream may reverse or stick. */
        float previous=value(atomic_exchange_explicit(&p->live_input,bits(x),memory_order_relaxed));
        float mix=x<=0 ? 0 : x>=1 ? 1 : fmaxf(0,fminf(1,load(p,MIX)+4*(x-previous)));
        store(p,MIX,mix);
        return;
    }
    if(i==PUNCH) {
        atomic_store_explicit(&p->punch_command,x>=.5f?1u:2u,memory_order_release);return;
    }
    if(i==CAPTURE_CMD || i==STORE_STATE || i==APPLY_STATE) {
        if(x>0)atomic_fetch_or(&p->commands,i==CAPTURE_CMD?DO_CAPTURE:i==STORE_STATE?DO_STORE:DO_APPLY);
        return;
    }
    if(i==TIME_MODE && (x>=.5f)!=(load(p,TIME_MODE)>=.5f)) {
        float tempo=load(p,CLOCK_STATUS)>=.5f?value(atomic_load(&p->host_tempo)):40+200*load(p,TEMPO);
        if(x>=.5f) {
            float ms=5+445*load(p,LENGTH),distance=1e9f;unsigned nearest=0;
            for(unsigned g=0;g<11;++g) {float d=fabsf(ms-60000/tempo*engine_division(g));if(d<distance){distance=d;nearest=g;}}
            store(p,GRID,nearest/10.f);store(p,LENGTH,nearest/10.f);
        } else {
            float ms=60000/tempo*engine_division((unsigned)lroundf(load(p,LENGTH)*10));
            store(p,LENGTH,fmaxf(0,fminf(1,(ms-5)/445)));
        }
    }
    unsigned steps=PARAMS[i].nopts?(unsigned)(PARAMS[i].nopts-1):0;
    int grid_length=i==LENGTH && load(p,TIME_MODE)>=.5f;
    if(grid_length)steps=10;
    if(steps) {
        float previous=load(p,i);
        float cursor=value(atomic_exchange_explicit(&p->enum_input[i],bits(input),memory_order_relaxed));
        float delta=input-cursor;
        int preserve_legacy=load(p,LEGACY)>=.5f && i<8;
        if(!preserve_legacy && x>0 && x<1 && fabsf(x-previous)>.000001f && delta!=0 && fabsf(delta)<.5f/steps)
            x=fmaxf(0,fminf(1,previous+(delta>0?1.f:-1.f)/steps));
        else x=roundf(x*steps)/steps;
    }
    if(grid_length)store(p,GRID,x);
    if(i==GRID)store(p,LENGTH,x);
    store(p,i,x);
    if(steps)atomic_store_explicit(&p->enum_input[i],bits(input),memory_order_relaxed);
    if(i==LEGACY)atomic_fetch_add(&p->reset,1);
    if(i==STATE_SELECT && x!=old_target)atomic_fetch_or(&p->commands,DO_APPLY);
    if(i==MIX) atomic_store_explicit(&p->live_input,bits(x),memory_order_relaxed);
}
static float get_parameter(AEffect *fx, int32_t i) {
    Plugin *p=fx->object;
    float x=i>=0 && i<NPARAMS ? load(p,i) : 0;
    if(i==MIX_LIVE) atomic_store_explicit(&p->live_input,bits(x),memory_order_relaxed);
    else if(i>=0 && i<NPARAMS && !PARAMS[i].readonly &&
            (PARAMS[i].nopts || (i==LENGTH && load(p,TIME_MODE)>=.5f)))
        atomic_store_explicit(&p->enum_input[i],bits(x),memory_order_relaxed);
    return x;
}
static float approach(float x,float target,float step) {
    if(x<target) return fminf(x+step,target);
    return fmaxf(x-step,target);
}
static float clean(float x) { return isfinite(x) ? x : 0; }
static int16_t pcm(float x) {
    x=fmaxf(-1,fminf(1,x));
    float z=x*32768.f;
    return z>=32767 ? 32767 : (int16_t)lrintf(z);
}
static void render_legacy(AEffect *fx,float **in,float **out,int32_t n,int add) {
    Plugin *p=fx->object;
    if(n<=0 || !out) return;
    /* Fixed control chunks, arbitrary host buffers, O(frames) bounded work.
     * No host callback, allocation, I/O, mutex, sleep or join in this call tree. */
    for(int32_t offset=0;offset<n;) {
        int32_t count=n-offset; if(count>128) count=128;
        float sr=value(atomic_load_explicit(&p->rate,memory_order_relaxed));
        unsigned gen=atomic_load_explicit(&p->reset,memory_order_acquire);
        int running=atomic_load_explicit(&p->running,memory_order_relaxed)!=0;
        int valid=isfinite(sr) && sr>=16000 && sr<=96000;
        if(sr!=p->sample_rate || gen!=p->generation) {
            float timing=valid ? sr : 44100;
            /* O(1) discard, smooth the last wet sample back to stereo dry.
             * Old ring bytes are inaccessible until newly recorded. */
            p->tail_left=(unsigned)ceilf(timing*0.005f);
            br_reset(&p->repeat,(unsigned)(timing*0.5f),(unsigned)lroundf(timing*128/44100));
            p->sample_rate=sr; p->generation=gen; p->wanted=0;
            p->punch_left=0; p->retry=0;
        }
        float timing=valid ? sr : 44100;
        float milliseconds=5+445*load(p,LENGTH);
        float mix_target=load(p,MIX);
        float db=-24+36*load(p,GAIN);
        int bypass=load(p,BYPASS)>=0.5f;
        int gate=load(p,GATE)>=0.5f;
        /* A bounded latest-command mailbox: FIRE or CANCEL. No mutex/queue.
         * UI messages arriving before a chunk coalesce; latest command wins. */
        unsigned command=atomic_exchange_explicit(&p->punch_command,0,memory_order_acquire);
        if(command==1) p->punch_left=(unsigned)ceilf(timing*0.45f);
        if(command==2) p->punch_left=0;
        if(bypass || !running || !valid) p->punch_left=0;
        float gain_target=bypass || !running || !valid || fabsf(db)<0.0001f ? 1 : powf(10,db/20);
        float smooth=1/(timing*0.005f), gain_step=4*smooth;
        /* Mix is a performance control. A 2 ms linear slew removes zipper steps
         * without the old 5 ms catch-up. Gate/reset/gain fades stay unchanged. */
        float mix_step=1/(timing*0.005f);
        for(int j=0;j<count;++j) {
            /* Only mix needs the faster mailbox cadence: no extra gain powf,
             * crossing search, callbacks or allocations in these sub-slices. */
            if(j && (j&31)==0) mix_target=load(p,MIX);
            int32_t k=offset+j;
            float l=clean(in && in[0] ? in[0][k] : 0);
            float r=clean(in && in[1] ? in[1][k] : l);
            /* Half-before-add prevents overflow for finite extreme input. */
            int16_t mono=pcm(l*0.5f+r*0.5f);
            int want=valid && running && !bypass && (gate || p->punch_left);
            if(!want && p->wanted) br_release(&p->repeat);
            if(want && !p->repeat.active && p->retry==0) {
                br_start(&p->repeat,(unsigned)lroundf(timing*milliseconds/1000));
                p->retry=128; /* bounded crossing search, at most once/128 frames */
            }
            if(p->repeat.active && milliseconds!=p->legacy_length &&
               (load(p,TIMING)<.5f || p->repeat.read==p->repeat.start)) {
                br_start(&p->repeat,(unsigned)lroundf(timing*milliseconds/1000));
                p->legacy_length=milliseconds;
            }
            if(p->retry) --p->retry;
            p->wanted=want;
            float wet=(float)br_sample(&p->repeat,mono)/32768;
            float depth_target=valid && running && !bypass && p->repeat.active ? 1 : 0;
            if(p->tail_left) { wet=p->last_wet; depth_target=0; --p->tail_left; }
            else p->last_wet=wet;
            p->depth=approach(p->depth,depth_target,smooth);
            p->mix=approach(p->mix,mix_target,mix_step);
            p->gain=approach(p->gain,gain_target,gain_step);
            float amount=p->depth*p->mix;
            /* Inactive / dry bypass stays float stereo; active wet is centered mono. */
            float ol=clean((l*(1-amount)+wet*amount)*p->gain);
            float or_=clean((r*(1-amount)+wet*amount)*p->gain);
            if(!valid || !running) { ol=l; or_=r; } /* explicit fail-safe dry */
            if(out[0]) { if(add) out[0][k]+=ol; else out[0][k]=ol; }
            if(out[1]) { if(add) out[1][k]+=or_; else out[1][k]=or_; }
            if(p->punch_left) --p->punch_left;
        }
        int active=p->repeat.active && valid && running && !bypass;
        int state=!valid ? BAD_RATE : bypass || !running ? BYPASSED : active ? REPEATING : p->wanted ? PRIMING : CAPTURE;
        store(p,ACTIVE,active ? 1 : 0); store(p,STATUS,(float)state/4);
        store(p,PUNCH,p->punch_left ? 1 : 0);
        offset+=count;
    }
}
static float unit(Plugin *p,int i) { return PARAMS[i].min+(PARAMS[i].max-PARAMS[i].min)*load(p,i); }
static unsigned option(Plugin *p,int i) { return (unsigned)lroundf(unit(p,i)); }
static void scene_store(Plugin *p,unsigned n) {
    Scene *s=&p->scenes[n%8];unsigned rev=atomic_load(&s->revision);
    if(rev&1 || !atomic_compare_exchange_strong(&s->revision,&rev,rev+1))return;
    int indices[E_FIELDS]={LENGTH,POSITION,BEND,BREAK,CORRUPT,REVERSE,STATE_PROB,STATE_DURATION,STATE_ENABLE,PITCH};
    for(int i=0;i<E_FIELDS;++i)atomic_store(&s->v[i],bits(load(p,indices[i])));
    atomic_store_explicit(&s->revision,rev+2,memory_order_release);
}
static void scene_sync(Plugin *p) {
    for(unsigned n=0;n<8;++n) {
        Scene *s=&p->scenes[n];unsigned rev=atomic_load_explicit(&s->revision,memory_order_acquire);
        if(rev==p->scene_seen[n] || rev&1)continue;
        EScene copy;for(int i=0;i<E_FIELDS;++i)copy.v[i]=value(atomic_load(&s->v[i]));
        if(atomic_load_explicit(&s->revision,memory_order_acquire)==rev) {
            p->engine.scene[n]=copy;p->scene_seen[n]=rev;
        }
    }
}
static void midi_set(Plugin *p,int i,float x) {
    /* MIDI CC values and note selections are absolute, not encoder gestures. */
    unsigned steps=PARAMS[i].nopts?(unsigned)(PARAMS[i].nopts-1):0;
    if(i==LENGTH && load(p,TIME_MODE)>=.5f)steps=10;
    if(steps) {x=roundf(x*steps)/steps;atomic_store(&p->enum_input[i],bits(load(p,i)));}
    set_parameter(&p->fx,i,x);atomic_fetch_or(&p->midi_dirty[i/32],1u<<(i%32));
}
static void midi_action(Plugin *p,Midi m) {
    if(!option(p,MIDI_ENABLE) || (m.status&15)+1!=option(p,MIDI_CHANNEL))return;
    unsigned type=m.status&0xf0;
    if(type==0xb0 && (m.note==120 || m.note==123)) {
        p->held_gate=p->held_freeze=0;midi_set(p,GATE,0);midi_set(p,FREEZE,0);
        atomic_store(&p->punch_command,2);return;
    }
    int on=type==0x90 && m.velocity;
    if(type==0xb0) {
        static const int cc[]={GATE,LENGTH,BREAK,MIX,FREEZE,POSITION,BUFFER,CAPTURE_CMD,BEND,CORRUPT,REVERSE,PITCH,CHANCE,DENSITY,MUTATION,STATE_SELECT};
        if(m.note>=20 && m.note<36)midi_set(p,cc[m.note-20],m.velocity/127.f);
        return;
    }
    if(type!=0x80 && type!=0x90)return;
    if(m.note<36 || m.note>99)return;
    unsigned n=m.note-36,row=n/8,col=n%8;
    int gate_note=(row==4 && col==2)||(row==7 && col==0);
    int freeze_note=(row==4 && col==1)||(row==7 && col==2);
    if(!on) {
        if(gate_note && option(p,GATE_MODE)) {p->held_gate&=~(1u<<row);if(!p->held_gate)midi_set(p,GATE,0);}
        if(freeze_note && option(p,FREEZE_MODE)) {p->held_freeze&=~(1u<<row);if(!p->held_freeze)midi_set(p,FREEZE,0);}
        if(row==7 && col==1)midi_set(p,PUNCH,0);
        return;
    }
    if(gate_note) {p->held_gate|=1u<<row;midi_set(p,GATE,option(p,GATE_MODE)?1:1-load(p,GATE));return;}
    if(freeze_note) {p->held_freeze|=1u<<row;midi_set(p,FREEZE,option(p,FREEZE_MODE)?1:1-load(p,FREEZE));return;}
    if(row==0) {midi_set(p,TIME_MODE,1);midi_set(p,GRID,col/10.f);}
    else if(row==1 || row==3) {midi_set(p,BREAK,col/7.f);if(row==3)midi_set(p,DENSITY,(7-col)/7.f);}
    else if(row==2) {static const float bend[]={-24,-12,-7,0,7,12,19,24};midi_set(p,BEND,(bend[col]+24)/48);}
    else if(row==4) {
        if(col==0)midi_set(p,CAPTURE_CMD,1);
        else if(col==3)midi_set(p,REVERSE,1-load(p,REVERSE));
        else if(col<7)midi_set(p,POSITION,(col-4)/2.f);
        else atomic_fetch_or(&p->commands,DO_PANIC);
    } else if(row==5) {static const float amounts[]={0,.05f,.1f,.2f,.35f,.5f,.75f,1};midi_set(p,CORRUPT,amounts[col]);}
    else if(row==6)midi_set(p,STATE_SELECT,col/7.f);
    else if(row==7) {
        if(col==1)midi_set(p,PUNCH,1);
        else if(col==3)midi_set(p,REVERSE,1-load(p,REVERSE));
        else if(col==4)midi_set(p,SEQ_RUN,1-load(p,SEQ_RUN));
        else if(col==5)midi_set(p,STORE_STATE,1);
        else if(col==6)midi_set(p,MUTATION,.5f);
        else atomic_fetch_or(&p->commands,DO_PANIC);
    }
}
static EConfig controls(Plugin *p) {
    return (EConfig){.ms=unit(p,LENGTH),.position=load(p,POSITION),.buffer_ms=unit(p,BUFFER),
        .bend=unit(p,BEND),.pitch=unit(p,PITCH),.fracture=load(p,BREAK),.corrupt=load(p,CORRUPT),
        .chance=load(p,CHANCE),.density=load(p,DENSITY),.mutation=load(p,MUTATION),
        .grid=(unsigned)lroundf(load(p,LENGTH)*10),.time_grid=option(p,TIME_MODE),.quantized=option(p,TIMING),
        .reverse=option(p,REVERSE),.freeze=option(p,FREEZE),.gate=option(p,GATE)||p->punch_left,
        .run=option(p,SEQ_RUN),.random=option(p,SEQ_MODE),.state_div=option(p,STATE_DIV),.seed=option(p,SEED)};
}
static void render(AEffect *fx,float **in,float **out,int32_t n,int add) {
    Plugin *p=fx->object;if(n<=0 || !out)return;
    if(load(p,LEGACY)>=.5f) {
        atomic_store(&p->commands,0);atomic_store(&p->midi_tail,atomic_load(&p->midi_head));
        render_legacy(fx,in,out,n,add);
        unsigned span=(p->repeat.end+p->repeat.capacity-p->repeat.start)%p->repeat.capacity;
        float legacy_rate=p->sample_rate>=16000&&p->sample_rate<=96000?p->sample_rate:44100;
        store(p,LENGTH_READ,span/(legacy_rate*2));
        store(p,PLAYHEAD,span?((p->repeat.read+p->repeat.capacity-p->repeat.start)%p->repeat.capacity)/(float)span:0);
        return;
    }
    float sr=value(atomic_load(&p->rate));int valid=isfinite(sr)&&sr>=16000&&sr<=96000;
    float rate=valid?sr:44100,tempo=unit(p,TEMPO);
    unsigned gen=atomic_load_explicit(&p->reset,memory_order_acquire);
    if(sr!=p->sample_rate || gen!=p->generation) {
        engine_reset(&p->engine,rate,option(p,SEED));p->sample_rate=sr;p->generation=gen;
        p->punch_left=0;p->held_gate=p->held_freeze=0;p->tail_left=(unsigned)ceilf(rate*.005f);
        for(int i=0;i<8;++i)p->scene_seen[i]=~0u;
    }
    scene_sync(p);
    int host_clock=0;
    /* The one standard time query is the sole permitted audio-thread host call.
     * Never retain the host pointer beyond this synchronous query. */
    if(option(p,SYNC_MODE) && p->host) {
        VstTimeInfo *t=(VstTimeInfo *)p->host(fx,audioMasterGetTime,0,kVstTempoValid|kVstPpqPosValid,NULL,0);
        if(t && (t->flags&kVstTempoValid) && isfinite(t->tempo) && t->tempo>=20 && t->tempo<=400) {
            tempo=(float)t->tempo;host_clock=1;
            if((t->flags&kVstPpqPosValid) && (t->flags&kVstTransportPlaying) && isfinite(t->ppqPos)) {
                if(!p->transport || fabs(p->engine.r.beat-t->ppqPos)>.25) {
                    p->engine.r.next_beat=t->ppqPos;p->engine.r.step=-1;
                }
                p->engine.r.beat=t->ppqPos;p->transport=1;
            } else p->transport=(t->flags&kVstTransportPlaying)!=0;
        }
    }
    atomic_store(&p->host_tempo,bits(tempo));
    Midi events[1024];unsigned ne=0,tail=atomic_load(&p->midi_tail),head=atomic_load_explicit(&p->midi_head,memory_order_acquire);
    while(tail!=head && ne<1024) {events[ne]=p->midi[tail];if(events[ne].delta>=n)events[ne].delta=n-1;++ne;tail=(tail+1)&1023;}
    atomic_store_explicit(&p->midi_tail,tail,memory_order_release);
    ghost_c11_sort(events,ne);
    unsigned event=0;float gain_target=1,mix_target=load(p,MIX),mix_step=1/(rate*.002f),drive=0,peak=0;
    int bypass=0,running=atomic_load(&p->running)!=0;
    for(int32_t k=0;k<n;++k) {
        int changed=0;
        while(event<ne && events[event].delta<=k) {midi_action(p,events[event++]);changed=1;}
        changed |= ghost_c11_tick(fx,clean(in&&in[0]?in[0][k]:0),clean(in&&in[1]?in[1][k]:in&&in[0]?in[0][k]:0),(unsigned)k,changed);
        if(ghost_c11_capture_request(fx))atomic_fetch_or(&p->commands,DO_CAPTURE);
        if(!(k&31) || changed) {
            unsigned cmd=atomic_exchange(&p->commands,0),punch=atomic_exchange(&p->punch_command,0);
            if(cmd&DO_PANIC) {store(p,GATE,0);store(p,FREEZE,0);store(p,SEQ_RUN,0);p->punch_left=0;p->held_gate=p->held_freeze=0;}
            if(punch==1){
                ghost_c11_punch(fx);
                p->punch_left=(unsigned)ceilf(rate*.45f);
                /* A new punch takes current live audio, not an old snapshot.
                 * Freeze intentionally keeps the held capture. O(1), no copies. */
#ifndef GHOST_BUFFER_ENGINE
                if(!option(p,FREEZE) && !p->engine.r.base.freeze && !(p->engine.r.playing && p->engine.r.voice.bank==(int)p->engine.r.live))
                    ghost_c11_capture_result(fx,engine_capture(&p->engine));
#endif
            }else if(punch==2)p->punch_left=0;
            bypass=load(p,BYPASS)>=.5f || !running || !valid;
            if(bypass)p->punch_left=0;
            if(cmd&DO_CAPTURE)ghost_c11_capture_result(fx,engine_capture(&p->engine));
            if(cmd&DO_STORE) {scene_store(p,option(p,STATE_SELECT));scene_sync(p);}
            if(cmd&DO_APPLY) {
                unsigned state=option(p,STATE_SELECT);int indices[E_FIELDS]={LENGTH,POSITION,BEND,BREAK,CORRUPT,REVERSE,STATE_PROB,STATE_DURATION,STATE_ENABLE,PITCH};
                for(int f=0;f<E_FIELDS;++f) {int i=indices[f];store(p,i,p->engine.scene[state].v[f]);atomic_fetch_or(&p->midi_dirty[i/32],1u<<(i%32));}
                if(option(p,TIME_MODE))store(p,GRID,roundf(load(p,LENGTH)*10)/10);
            }
            EConfig c=controls(p);ghost_c11_config(fx,&c);if(bypass || p->tail_left)c.gate=c.freeze=c.run=0;
            if(host_clock && !p->transport)c.run=0;
            engine_control(&p->engine,&c);
            if(cmd&DO_APPLY) {engine_select(&p->engine,option(p,STATE_SELECT));if(!c.run)p->engine.r.scene_on=0;}
            mix_target=ghost_c11_mix(fx,load(p,MIX));mix_step=1/(rate*unit(p,SMOOTH)/1000);
            float db=unit(p,GAIN);gain_target=bypass?1:fabsf(db)<.0001f?1:powf(10,db/20);
            drive=bypass?0:load(p,DRIVE);
        }
        float l=clean(in&&in[0]?in[0][k]:0),r=clean(in&&in[1]?in[1][k]:l),wl=l,wr=r;
        if(valid && running)engine_tick(&p->engine,l,r,tempo,&wl,&wr);ghost_pe_wet(fx,&wl,&wr);
        float depth_target=!bypass && !p->tail_left && p->engine.r.playing?1:0;
        if(p->tail_left || (!p->engine.r.playing && p->depth>0)) {wl=p->release_wet[0];wr=p->release_wet[1];}
        else if(p->engine.r.playing) {p->release_wet[0]=wl;p->release_wet[1]=wr;}
        if(p->tail_left)--p->tail_left;
        p->depth=approach(p->depth,depth_target,1/(rate*.005f));
        p->mix=approach(p->mix,mix_target,mix_step);p->gain=approach(p->gain,gain_target,4/(rate*.005f));
        if(drive>0) {float amount=1+drive*9;wl=wl*amount/(1+fabsf(wl*amount));wr=wr*amount/(1+fabsf(wr*amount));}
        float wet=p->depth*p->mix;
        float a=clean((l*(1-wet)+wl*wet)*p->gain),b=clean((r*(1-wet)+wr*wet)*p->gain);
        if(!valid || !running){a=l;b=r;}
        /* Only flush subnormal results, preserving ordinary exact stereo dry. */
        if(fabsf(a)<1e-30f)a=0;if(fabsf(b)<1e-30f)b=0;
        if(out[0]) {if(add)out[0][k]+=a;else out[0][k]=a;}
        if(out[1]) {if(add)out[1][k]+=b;else out[1][k]=b;}
        peak=fmaxf(peak,fmaxf(fabsf(a),fabsf(b)));
        if(p->punch_left)--p->punch_left;
    }
    int active=p->engine.r.playing && !bypass;
    store(p,ACTIVE,active?1:0);store(p,STATUS,!valid?1:bypass?.75f:active?.25f:(load(p,GATE)>=.5f||load(p,FREEZE)>=.5f||load(p,SEQ_RUN)>=.5f)?.5f:0);
    store(p,PUNCH,p->punch_left?1:0);
    store(p,BUFFER_STATE,p->engine.r.base.freeze&&p->engine.r.captured>=0?1:active?2/3.f:p->engine.r.captured>=0?1/3.f:0);
    store(p,PLAYHEAD,p->engine.r.voice.length?(float)(p->engine.r.voice.phase/p->engine.r.voice.length):0);
    store(p,LENGTH_READ,fminf(1,p->engine.r.voice.length/(rate*2)));
    store(p,SEQ_STEP,p->engine.r.step<0?0:p->engine.r.step/7.f);
    store(p,CLOCK_STATUS,host_clock?1:0);store(p,ACTIVITY,fminf(1,peak));
}
static void replacing(AEffect *e,float **in,float **out,int32_t n){render(e,in,out,n,0);}
static void accumulating(AEffect *e,float **in,float **out,int32_t n){render(e,in,out,n,1);}
static void text(void *d,const char *s,size_t n){if(d&&n){strncpy(d,s,n-1);((char*)d)[n-1]=0;}}
static void u32(unsigned char *b,unsigned v){for(int i=0;i<4;++i)b[i]=(unsigned char)(v>>(i*8));}
static unsigned read32(const unsigned char *b){return (unsigned)b[0]|(unsigned)b[1]<<8|(unsigned)b[2]<<16|(unsigned)b[3]<<24;}
static unsigned checksum(const unsigned char *b,size_t n){unsigned h=2166136261u;for(size_t i=0;i<n;++i)h=(h^b[i])*16777619u;return h;}
static void program(Plugin *p,unsigned n) {
    p->program=(int)n;
    for(int i=0;i<NPARAMS;++i)store(p,i,FACTORY[n].values[i]);
    atomic_store(&p->live_input,bits(load(p,MIX)));atomic_store(&p->punch_command,2);atomic_store(&p->commands,0);
    atomic_fetch_add(&p->reset,1);
}
static intptr_t dispatch(AEffect *fx,int32_t op,int32_t idx,intptr_t v,void *data,float opt) {
    Plugin *p=fx->object;
    switch(op) {
    case effOpen:atomic_store(&p->opened,1);return 1;
    case effClose:atomic_store(&p->quit,1);pthread_join(p->notifier,NULL);free(p);return 1;
    case effSetSampleRate:
        atomic_store(&p->rate,bits(isfinite(opt)&&opt>=16000&&opt<=96000?opt:0));atomic_fetch_add(&p->reset,1);
        return isfinite(opt)&&opt>=16000&&opt<=96000;
    case effSetBlockSize:return v>0&&v<=1048576;
    case effMainsChanged:
        store(p,GATE,0);store(p,FREEZE,0);store(p,SEQ_RUN,0);atomic_store(&p->punch_command,2);
        atomic_store(&p->running,v!=0);atomic_fetch_add(&p->reset,1);return 1;
    case effSetBypass:set_parameter(fx,BYPASS,v?1:0);return 1;
    case effGetPlugCategory:return 1;
    case effGetEffectName:case effGetProductString:text(data,"BeatRepeat",32);return 1;
    case effGetVendorString:text(data,"MPC-EURO",32);return 1;
    case effGetVendorVersion:return VERSION;
    case effGetVstVersion:return 2400;
    case effSetProgram:if(v<0||v>=NPROGRAMS)return 0;program(p,(unsigned)v);return 1;
    case effGetProgram:return p->program;
    case effGetProgramName:text(data,FACTORY[p->program].name,24);return 1;
    case effGetProgramNameIndexed:if(idx<0||idx>=NPROGRAMS)return 0;text(data,FACTORY[idx].name,24);return 1;
    case effCanDo:return data&&(!strcmp(data,"bypass")||!strcmp(data,"receiveVstEvents")||!strcmp(data,"receiveVstMidiEvent"))?1:-1;
    case effCanBeAutomated:return idx>=0&&idx<NPARAMS&&idx!=MIX_LIVE&&!PARAMS[idx].readonly;
    case effGetParamName:if(idx<0||idx>=NPARAMS)return 0;text(data,PARAMS[idx].name,8);return 1;
    case effGetParamLabel:if(idx<0||idx>=NPARAMS)return 0;text(data,idx==LENGTH&&load(p,TIME_MODE)>=.5f?"":PARAMS[idx].unit,8);return 1;
    case effGetParamDisplay:
        if(idx<0||idx>=NPARAMS||!data)return 0;
        if(idx==BUFFER_STATE&&load(p,LEGACY)>=.5f){text(data,"LEGACY",8);return 1;}
        if(idx==LENGTH&&load(p,TIME_MODE)>=.5f){text(data,PARAMS[GRID].opts[(unsigned)lroundf(load(p,LENGTH)*10)],8);return 1;}
        if(PARAMS[idx].nopts)text(data,PARAMS[idx].opts[(int)lroundf(load(p,idx)*(PARAMS[idx].nopts-1))],8);
        else snprintf(data,8,"%.1f",unit(p,idx));return 1;
    case effProcessEvents: {
        if(!data)return 0;VstEvents *list=data;
        if(list->numEvents<0||list->numEvents>1023)return 0;
        VstEvent **events=(VstEvent **)((unsigned char *)data+offsetof(VstEvents,events));
        unsigned head=atomic_load(&p->midi_head),tail=atomic_load_explicit(&p->midi_tail,memory_order_acquire),valid=0;
        for(int i=0;i<list->numEvents;++i){VstMidiEvent *m=(VstMidiEvent*)events[i];if(m&&m->type==1&&m->byteSize>=(int)sizeof(*m))++valid;}
        if(valid>1023-((head-tail)&1023))return 0;
        for(int i=0;i<list->numEvents;++i) {
            VstMidiEvent *m=(VstMidiEvent *)events[i];if(!m||m->type!=1||m->byteSize<(int)sizeof(*m))continue;
            unsigned next=(head+1)&1023;if(next==atomic_load_explicit(&p->midi_tail,memory_order_acquire))return 0;
            p->midi[head]=(Midi){m->deltaFrames<0?0:m->deltaFrames,m->midiData[0],m->midiData[1],m->midiData[2]};
            head=next;
        }atomic_store_explicit(&p->midi_head,head,memory_order_release);return 1;
    }
    case effGetChunk: {
        if(!data)return 0;unsigned char *b=p->chunk;memcpy(b,"EBR2",4);u32(b+4,2);u32(b+8,UID);
        unsigned offset=12;
        for(int i=0;i<NPARAMS;++i,offset+=4)u32(b+offset,bits(PARAMS[i].saved?load(p,i):0));
        for(int s=0;s<8;++s) {
            unsigned rev=atomic_load_explicit(&p->scenes[s].revision,memory_order_acquire);if(rev&1)return 0;
            for(int f=0;f<E_FIELDS;++f,offset+=4)u32(b+offset,atomic_load(&p->scenes[s].v[f]));
            if(atomic_load_explicit(&p->scenes[s].revision,memory_order_acquire)!=rev)return 0;
        }
        u32(b+offset,checksum(b,offset));*(void **)data=b;return STATE_SIZE;
    }
    case effSetChunk: {
        if(!data || (v!=48&&v!=STATE_SIZE))return 0;
        const unsigned char *b=data;int old=v==48;unsigned count=old?8:NPARAMS;
        if(memcmp(b,old?"EBR1":"EBR2",4)||read32(b+4)!=(old?1u:2u)||read32(b+8)!=UID||read32(b+v-4)!=checksum(b,(size_t)v-4))return 0;
        float vals[NPARAMS];for(int i=0;i<NPARAMS;++i)vals[i]=PARAMS[i].saved?PARAMS[i].def:0;
        for(unsigned i=0;i<count;++i) {
            float x=value(read32(b+12+4*i));if(!isfinite(x)||x<0||x>1||(!PARAMS[i].saved&&x!=0))return 0;
            if(PARAMS[i].saved&&PARAMS[i].nopts&&fabsf(x*(PARAMS[i].nopts-1)-roundf(x*(PARAMS[i].nopts-1)))>.00001f)return 0;
            vals[i]=x;
        }
        if(!old)for(unsigned i=12+4*NPARAMS;i<(unsigned)v-4;i+=4) {
            float x=value(read32(b+i));unsigned field=((i-12-4*NPARAMS)/4)%E_FIELDS;
            if(!isfinite(x)||x<0||x>1)return 0;
            if((field==5||field==8) && x!=0 && x!=1)return 0;
            if(field==7 && fabsf(x*10-roundf(x*10))>.00001f)return 0;
        }
        if(old)vals[LEGACY]=1;
        unsigned revisions[8];int acquired=0;
        if(!old) {
            for(int s=0;s<8;++s) {
                unsigned rev=atomic_load(&p->scenes[s].revision);revisions[s]=rev;
                if((rev&1)||!atomic_compare_exchange_strong(&p->scenes[s].revision,&rev,rev+1)) {
                    for(int j=0;j<acquired;++j)atomic_store(&p->scenes[j].revision,revisions[j]);
                    return 0;
                }
                ++acquired;
            }
        }
        for(int i=0;i<NPARAMS;++i)store(p,i,vals[i]);
        if(!old)for(int s=0;s<8;++s) {
            for(int f=0;f<E_FIELDS;++f)atomic_store(&p->scenes[s].v[f],read32(b+12+4*NPARAMS+4*(s*E_FIELDS+f)));
            atomic_store_explicit(&p->scenes[s].revision,revisions[s]+2,memory_order_release);
        }
        atomic_store(&p->live_input,bits(load(p,MIX)));atomic_store(&p->commands,0);atomic_store(&p->punch_command,2);
        atomic_fetch_add(&p->reset,1);return 1;
    }
    default:return 0;
    }
}
static void *notify(void *arg) {
    Plugin *p=arg;float seen[NPARAMS];for(int i=0;i<NPARAMS;++i)seen[i]=-1;
    const struct timespec pause={0,33333333};
    while(!atomic_load(&p->quit)) {
        nanosleep(&pause,NULL);if(atomic_load(&p->quit))break;
        if(!atomic_load(&p->opened)||!p->host)continue;
        unsigned dirty[2]={atomic_exchange(&p->midi_dirty[0],0),atomic_exchange(&p->midi_dirty[1],0)};
        int changed=0;
        for(int i=0;i<NPARAMS;++i) {
            /* Hidden level telemetry must not force repainting idle LIVE pages. */
            if(i==MIX_LIVE || i==ACTIVITY)continue;float x=load(p,i);
            if(x!=seen[i] || (dirty[i/32]&(1u<<(i%32)))) {
                seen[i]=x;changed=1;
                if(PARAMS[i].readonly||i==PUNCH||(dirty[i/32]&(1u<<(i%32))))p->host(&p->fx,audioMasterAutomate,i,0,NULL,x);
            }
        }
        if(changed)p->host(&p->fx,audioMasterUpdateDisplay,0,0,NULL,0);
    }return NULL;
}
__attribute__((visibility("default"))) AEffect *VSTPluginMain(audioMasterCallback host) {
    Plugin *p=calloc(1,sizeof(*p));if(!p)return NULL;
    /* Commit backing pages before audio begins, not on first capture. */
    for(size_t offset=0;offset<sizeof(*p);offset+=4096)((volatile unsigned char *)p)[offset]=0;
    p->host=host;p->sample_rate=44100;p->mix=p->gain=1;
    for(int i=0;i<NPARAMS;++i) {atomic_init(&p->target[i],bits(PARAMS[i].def));atomic_init(&p->enum_input[i],bits(PARAMS[i].def));}
    atomic_init(&p->rate,bits(44100));atomic_init(&p->running,0);atomic_init(&p->reset,0);atomic_init(&p->punch_command,0);
    atomic_init(&p->quit,0);atomic_init(&p->opened,0);atomic_init(&p->live_input,bits(PARAMS[MIX].def));
    atomic_init(&p->host_tempo,bits(120));
    atomic_init(&p->commands,0);atomic_init(&p->midi_head,0);atomic_init(&p->midi_tail,0);
    atomic_init(&p->midi_dirty[0],0);atomic_init(&p->midi_dirty[1],0);
    for(unsigned s=0;s<8;++s) {
        atomic_init(&p->scenes[s].revision,2);p->scene_seen[s]=~0u;
        float v[E_FIELDS]={PARAMS[LENGTH].def,s/14.f,.5f,s/35.f,0,0,1,0,1,.5f};
        for(int f=0;f<E_FIELDS;++f)atomic_init(&p->scenes[s].v[f],bits(v[f]));
    }
    engine_reset(&p->engine,44100,1);br_reset(&p->repeat,22050,128);
    p->fx=(AEffect){.magic=0x56737450,.dispatcher=dispatch,.process=accumulating,.setParameter=set_parameter,.getParameter=get_parameter,
        .numPrograms=NPROGRAMS,.numParams=NPARAMS,.numInputs=2,.numOutputs=2,.flags=effFlagsCanReplacing|effFlagsProgramChunks,
        .ioRatio=1,.object=p,.uniqueID=UID,.version=VERSION,.processReplacing=replacing};
    if(pthread_create(&p->notifier,NULL,notify,p)){free(p);return NULL;}return &p->fx;
}
