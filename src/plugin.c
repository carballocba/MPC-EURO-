/* SPDX-License-Identifier: GPL-3.0-only
 * Copyright 2026 MPC-EURO contributors. SDK-free ABI derived from sd88me.
 * DSP is audio-owned. Only lock-free 32-bit scalar targets cross threads.
 * Lifecycle/state dispatch is host-serialized; close/prepare are not audio calls. */
#define _POSIX_C_SOURCE 200809L
#include "vst2_abi.h"
#include "repeat.h"
#include "params.h"
#include <stdatomic.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <pthread.h>
#include <time.h>
_Static_assert(ATOMIC_INT_LOCK_FREE == 2, "Realtime path requires lock-free unsigned atomics");
_Static_assert(sizeof(float) == 4 && sizeof(unsigned) == 4, "32-bit float/unsigned required");
_Static_assert(NPARAMS == 8, "Change state schema version when changing the registry");
enum { LENGTH, GATE, MIX, GAIN, PUNCH, BYPASS, ACTIVE, STATUS };
enum { CAPTURE, REPEATING, PRIMING, BYPASSED, BAD_RATE };
enum { UID = 0x45754272, STATE_SIZE = 48, VERSION = 100 }; /* EuBr */
typedef struct {
    AEffect fx;
    audioMasterCallback host;
    atomic_uint target[NPARAMS], rate, running, reset, punch_command;
    atomic_uint quit, opened;
    pthread_t notifier;
    Repeat repeat;
    float sample_rate, mix, gain, depth, last_wet;
    unsigned generation, punch_left, tail_left, retry;
    int wanted;
    unsigned char chunk[STATE_SIZE]; /* dispatcher-only, never touched by audio */
} Plugin;
static unsigned bits(float x) { unsigned u; memcpy(&u,&x,4); return u; }
static float value(unsigned u) { float x; memcpy(&x,&u,4); return x; }
static void store(Plugin *p, int i, float f) { atomic_store_explicit(&p->target[i],bits(f),memory_order_relaxed); }
static float load(Plugin *p, int i) { return value(atomic_load_explicit(&p->target[i],memory_order_relaxed)); }
static void set_parameter(AEffect *fx, int32_t i, float x) {
    Plugin *p=fx->object;
    if(i<0 || i>=NPARAMS || PARAMS[i].readonly || !isfinite(x)) return;
    x=fmaxf(0,fminf(1,x));
    if(i==PUNCH) {
        atomic_store_explicit(&p->punch_command,x>=0.5f ? 1u : 2u,memory_order_release);
        return;
    }
    if(PARAMS[i].nopts) x=x>=0.5f ? 1 : 0;
    store(p,i,x);
}
static float get_parameter(AEffect *fx, int32_t i) {
    return i>=0 && i<NPARAMS ? load(fx->object,i) : 0;
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
static void render(AEffect *fx,float **in,float **out,int32_t n,int add) {
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
        for(int j=0;j<count;++j) {
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
            if(p->retry) --p->retry;
            p->wanted=want;
            float wet=(float)br_sample(&p->repeat,mono)/32768;
            float depth_target=valid && running && !bypass && p->repeat.active ? 1 : 0;
            if(p->tail_left) { wet=p->last_wet; depth_target=0; --p->tail_left; }
            else p->last_wet=wet;
            p->depth=approach(p->depth,depth_target,smooth);
            p->mix=approach(p->mix,mix_target,smooth);
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
static void replacing(AEffect *e,float **in,float **out,int32_t n) { render(e,in,out,n,0); }
static void accumulating(AEffect *e,float **in,float **out,int32_t n) { render(e,in,out,n,1); }
static void text(void *dst,const char *s,size_t n) { if(dst && n) { strncpy(dst,s,n-1); ((char*)dst)[n-1]=0; } }
static void u32(unsigned char *b,unsigned v) { for(int i=0;i<4;++i) b[i]=(unsigned char)(v>>(i*8)); }
static unsigned read32(const unsigned char *b) { return (unsigned)b[0]|(unsigned)b[1]<<8|(unsigned)b[2]<<16|(unsigned)b[3]<<24; }
static unsigned checksum(const unsigned char *b,size_t n) { unsigned h=2166136261u; for(size_t i=0;i<n;++i) h=(h^b[i])*16777619u; return h; }
static intptr_t dispatch(AEffect *fx,int32_t op,int32_t idx,intptr_t v,void *data,float opt) {
    Plugin *p=fx->object;
    switch(op) {
    case effOpen: atomic_store(&p->opened,1); return 1;
    case effClose:
        atomic_store(&p->quit,1); pthread_join(p->notifier,NULL); free(p); return 1;
    case effSetSampleRate:
        atomic_store(&p->rate,bits(isfinite(opt) && opt>=16000 && opt<=96000 ? opt : 0));
        atomic_fetch_add_explicit(&p->reset,1,memory_order_release); return opt>=16000 && opt<=96000 && isfinite(opt);
    case effSetBlockSize: return v>0 && v<=1048576; /* process also accepts arbitrary smaller slices */
    case effMainsChanged:
        store(p,GATE,0); atomic_store(&p->punch_command,2); atomic_store(&p->running,v!=0);
        atomic_fetch_add_explicit(&p->reset,1,memory_order_release); return 1;
    case effSetBypass: set_parameter(fx,BYPASS,v ? 1 : 0); return 1;
    case effGetPlugCategory: return 1;
    case effGetEffectName: case effGetProductString: text(data,"BeatRepeat",32); return 1;
    case effGetVendorString: text(data,"MPC-EURO",32); return 1;
    case effGetVendorVersion: return VERSION;
    case effGetVstVersion: return 2400;
    case effSetProgram: return v==0;
    case effGetProgram: return 0;
    case effGetProgramName: text(data,"Default",24); return 1;
    case effGetProgramNameIndexed: if(idx!=0) return 0; text(data,"Default",24); return 1;
    case effCanDo: return data && (!strcmp(data,"bypass")) ? 1 : -1;
    case effCanBeAutomated: return idx>=0 && idx<NPARAMS && !PARAMS[idx].readonly;
    case effGetParamName: if(idx<0||idx>=NPARAMS) return 0; text(data,PARAMS[idx].name,8); return 1;
    case effGetParamLabel: if(idx<0||idx>=NPARAMS) return 0; text(data,PARAMS[idx].unit,8); return 1;
    case effGetParamDisplay: {
        if(idx<0||idx>=NPARAMS||!data) return 0;
        const Param *a=&PARAMS[idx]; float x=load(p,idx);
        if(a->nopts) text(data,a->opts[(int)lroundf(x*(a->nopts-1))],8);
        else snprintf(data,8,"%.1f",a->min+(a->max-a->min)*x);
        return 1;
    }
    case effGetChunk:
        if(!data) return 0;
        memcpy(p->chunk,"EBR1",4); u32(p->chunk+4,1); u32(p->chunk+8,UID);
        for(int i=0;i<NPARAMS;++i) u32(p->chunk+12+4*i,bits(PARAMS[i].saved ? load(p,i) : 0));
        u32(p->chunk+44,checksum(p->chunk,44)); *(void**)data=p->chunk; return STATE_SIZE;
    case effSetChunk: {
        if(!data || v!=STATE_SIZE) return 0;
        const unsigned char *b=data; float values[NPARAMS];
        if(memcmp(b,"EBR1",4)||read32(b+4)!=1||read32(b+8)!=UID||read32(b+44)!=checksum(b,44)) return 0;
        for(int i=0;i<NPARAMS;++i) {
            values[i]=value(read32(b+12+4*i));
            if(!isfinite(values[i])||values[i]<0||values[i]>1) return 0;
            if(!PARAMS[i].saved && values[i]!=0) return 0;
            if(PARAMS[i].saved && PARAMS[i].nopts && values[i]!=0 && values[i]!=1) return 0;
        }
        for(int i=0;i<NPARAMS;++i) if(!PARAMS[i].readonly) store(p,i,values[i]);
        atomic_store(&p->punch_command,2);
        atomic_fetch_add_explicit(&p->reset,1,memory_order_release); return 1;
    }
    default: return 0;
    }
}
static void *notify(void *arg) {
    Plugin *p=arg; float seen[NPARAMS]; for(int i=0;i<NPARAMS;++i) seen[i]=-1;
    const struct timespec pause={0,100000000};
    while(!atomic_load(&p->quit)) {
        nanosleep(&pause,NULL);
        if(atomic_load(&p->quit)) break;
        if(!atomic_load(&p->opened) || !p->host) continue;
        int changed=0;
        /* Notify autonomous status/Punch release at <=10Hz, never from audio.
         * Read-only controls ignore host echo setters and are not automatable. */
        for(int i=PUNCH;i<NPARAMS;++i) {
            if(i==BYPASS) continue;
            float x=load(p,i);
            if(x!=seen[i]) { seen[i]=x; p->host(&p->fx,audioMasterAutomate,i,0,NULL,x); changed=1; }
        }
        if(changed) p->host(&p->fx,audioMasterUpdateDisplay,0,0,NULL,0);
    }
    return NULL;
}
__attribute__((visibility("default"))) AEffect *VSTPluginMain(audioMasterCallback host) {
    Plugin *p=calloc(1,sizeof(*p)); if(!p) return NULL;
    p->host=host; p->sample_rate=44100; p->mix=1; p->gain=1;
    for(int i=0;i<NPARAMS;++i) atomic_init(&p->target[i],bits(PARAMS[i].def));
    atomic_init(&p->rate,bits(44100)); atomic_init(&p->running,0); atomic_init(&p->reset,0);
    atomic_init(&p->punch_command,0); atomic_init(&p->quit,0); atomic_init(&p->opened,0);
    br_reset(&p->repeat,22050,128);
    p->fx=(AEffect){.magic=0x56737450,.dispatcher=dispatch,.process=accumulating,
        .setParameter=set_parameter,.getParameter=get_parameter,.numPrograms=1,.numParams=NPARAMS,
        .numInputs=2,.numOutputs=2,.flags=effFlagsCanReplacing|effFlagsProgramChunks,
        .ioRatio=1,.object=p,.uniqueID=UID,.version=VERSION,.processReplacing=replacing};
    if(pthread_create(&p->notifier,NULL,notify,p)) { free(p); return NULL; }
    return &p->fx;
}
