#define _POSIX_C_SOURCE 200809L
#include "vst2_abi.h"
#include "repeat.h"
#include "controls.h"
#include "engine.h"
#include <assert.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <pthread.h>
#include <time.h>
#include <stdarg.h>
#include <fcntl.h>
#include <unistd.h>
#include "oracle.h"
extern AEffect *VSTPluginMain(audioMasterCallback);
enum { CHUNK_BYTES=16+4*CONTROL_COUNT+4*E_STATES*E_FIELDS };
static _Thread_local int audio;
static atomic_uint violations, notices, display_updates, control_echoes;
#define GUARD() do { if(audio) atomic_fetch_add(&violations,1); } while(0)
void *__real_malloc(size_t); void *__wrap_malloc(size_t n) { GUARD(); return __real_malloc(n); }
void *__real_calloc(size_t,size_t); void *__wrap_calloc(size_t n,size_t s) { GUARD(); return __real_calloc(n,s); }
void *__real_realloc(void*,size_t); void *__wrap_realloc(void *p,size_t n) { GUARD(); return __real_realloc(p,n); }
void __real_free(void*); void __wrap_free(void *p) { GUARD(); __real_free(p); }
int __real_pthread_mutex_lock(pthread_mutex_t*); int __wrap_pthread_mutex_lock(pthread_mutex_t *p) { GUARD(); return __real_pthread_mutex_lock(p); }
int __real_pthread_mutex_trylock(pthread_mutex_t*); int __wrap_pthread_mutex_trylock(pthread_mutex_t *p) { GUARD(); return __real_pthread_mutex_trylock(p); }
int __real_pthread_mutex_unlock(pthread_mutex_t*); int __wrap_pthread_mutex_unlock(pthread_mutex_t *p) { GUARD(); return __real_pthread_mutex_unlock(p); }
int __real_pthread_join(pthread_t,void**); int __wrap_pthread_join(pthread_t p,void **r) { GUARD(); return __real_pthread_join(p,r); }
int __real_open(const char*,int,...); int __wrap_open(const char *s,int f,...) { GUARD(); if(f&O_CREAT) { va_list a;va_start(a,f);int m=va_arg(a,int);va_end(a);return __real_open(s,f,m); } return __real_open(s,f); }
FILE *__real_fopen(const char*,const char*); FILE *__wrap_fopen(const char *s,const char *m) { GUARD();return __real_fopen(s,m); }
ssize_t __real_read(int,void*,size_t); ssize_t __wrap_read(int f,void *b,size_t n) { GUARD();return __real_read(f,b,n); }
ssize_t __real_write(int,const void*,size_t); ssize_t __wrap_write(int f,const void *b,size_t n) { GUARD();return __real_write(f,b,n); }
static intptr_t host(AEffect *e,int32_t op,int32_t i,intptr_t v,void *p,float x) {
    (void)e;(void)i;(void)v;(void)p;(void)x;
    if(op==audioMasterGetTime)return 0;
    GUARD();
    if(op==audioMasterAutomate) atomic_fetch_add(&notices,1);
    if(op==audioMasterAutomate && (i<=GAIN || i==BYPASS || i==MIX_LIVE)) atomic_fetch_add(&control_echoes,1);
    if(op==audioMasterUpdateDisplay) atomic_fetch_add(&display_updates,1);
    return 1;
}
static unsigned cases;
#define DONE(s) do { ++cases; printf("PASS %s\n",s); } while(0)
#define NEAR(a,b,t) assert(fabs((double)(a)-(double)(b))<=(t))
static float l[4096],r[4096],ol[4096],or_[4096];
static void block(AEffect *e,int n) {
    float *in[]={l,r},*out[]={ol,or_}; audio=1;
    e->processReplacing(e,in,out,n); audio=0;
    for(int i=0;i<n;++i) assert(isfinite(ol[i]) && isfinite(or_[i]));
}
static AEffect *create(void) {
    AEffect *e=VSTPluginMain(host);assert(e);
    assert(e->magic==0x56737450 && e->numInputs==2 && e->numOutputs==2 && e->numParams==CONTROL_COUNT);
    assert(e->uniqueID==0x45754272 && !(e->flags&effFlagsIsSynth));
    e->setParameter(e,LEGACY,1);
    e->dispatcher(e,effOpen,0,0,NULL,0);
    assert(e->dispatcher(e,effSetSampleRate,0,0,NULL,44100)==1);
    e->dispatcher(e,effMainsChanged,0,1,NULL,0);
    return e;
}
static void close_fx(AEffect *e) { e->dispatcher(e,effClose,0,0,NULL,0); }
static void fill(unsigned offset,int n) {
    for(int i=0;i<n;++i) {
        double t=(i+offset)/44100.0;
        l[i]=(float)(0.4*sin(2*3.141592653589793*173*t));
        r[i]=(float)(0.2*sin(2*3.141592653589793*317*t));
    }
}
static void prime(AEffect *e) { for(unsigned k=0;k<400;++k) { fill(k*128,128);block(e,128); } }
static void scalar(AEffect *e,int i,float v) { e->setParameter(e,i,v); }
static void test_oracle(void) {
    Repeat *b=calloc(1,sizeof(*b)); LegacyRepeat *old=legacy_create(); assert(b&&old);
    br_reset(b,22050,128);
    for(int i=0;i<12000;++i) {
        int16_t x=(int16_t)(16000*sin(2*3.141592653589793*i/347.0)),y=x;
        legacy_process(old,&y,1); int16_t got=br_sample(b,x); if(got!=y) fprintf(stderr,"oracle i=%d got=%d want=%d in=%d fade=%u/%u old=%d/%d read=%u oldread=%d\n",i,got,y,x,b->fade_in,b->fade_out,old->crossfade_in,old->crossfade_out,b->read,old->repeat_index); assert(got==y);
    }
    assert(br_start(b,3150));legacy_trigger(old,3150);
    for(int i=0;i<4096;++i) {
        if(i==2500) { br_release(b); legacy_trigger(old,0); }
        int16_t x=(int16_t)(14000*sin(2*3.141592653589793*i/253.0)),y=x;
        legacy_process(old,&y,1); int16_t got=br_sample(b,x); if(got!=y) fprintf(stderr,"oracle i=%d got=%d want=%d in=%d fade=%u/%u old=%d/%d read=%u oldread=%d\n",i,got,y,x,b->fade_in,b->fade_out,old->crossfade_in,old->crossfade_out,b->read,old->repeat_index); assert(got==y);
    }
    free(b);legacy_free(old);DONE("bit-exact original DSP oracle (normal capture/repeat/release)");
}
static void test_core_boundaries(void) {
    Repeat *b=calloc(1,sizeof(*b)); assert(b);br_reset(b,22050,128);
    assert(!br_start(b,200));
    for(unsigned i=0;i<200000;++i) br_sample(b,(i%32)<16 ? -30000 : 30000);
    assert(br_start(b,400)); /* source cursor-wrap refusal corrected */
    for(int i=0;i<500;++i) br_sample(b,0);
    br_release(b);for(int i=0;i<128;++i) br_sample(b,0);
    assert(!b->active);
    for(unsigned i=0;i<22060;++i) br_sample(b,1);
    assert(!br_start(b,400)); /* no stale history after DC */
    /* A long DC section across sample-clock wrap cannot revive old stamps. */
    b->clock=UINT32_MAX-10;
    for(int i=0;i<30;++i) br_sample(b,1);
    assert(b->crossing_count==0 && !br_start(b,400));
    br_reset(b,48000,279);assert(!br_start(b,400));
    for(unsigned i=0;i<100000;++i) br_sample(b,(int16_t)((i&1)?32767:-32768));
    assert(br_start(b,43200));
    for(int i=0;i<70000;++i) br_sample(b,-32768);
    br_release(b);for(int i=0;i<279;++i) br_sample(b,32767);
    assert(!b->active);free(b);DONE("crossing expiry/wrap, zero history and widened 96k indices");
}
static void test_silence_impulse(void) {
    AEffect *e=create();memset(l,0,sizeof l);memset(r,0,sizeof r);
    for(int k=0;k<100;++k) { scalar(e,GATE,k%2);block(e,128);for(int i=0;i<128;++i) assert(ol[i]==0&&or_[i]==0); }
    scalar(e,GATE,0);l[0]=1;r[0]=0.25;block(e,128);
    for(int i=0;i<128;++i) { NEAR(ol[i],l[i],0);NEAR(or_[i],r[i],0); }
    close_fx(e);DONE("silence / impulses / no crossings do not invent a loop");
}
static void test_stereo_and_repeat(void) {
    AEffect *e=create();prime(e);
    fill(51200,4096);block(e,4096);
    for(int i=0;i<4096;++i) {NEAR(ol[i],l[i],0);NEAR(or_[i],r[i],0);}
    scalar(e,MIX,0);scalar(e,GATE,1);block(e,4096);
    assert(e->getParameter(e,ACTIVE)==1);
    for(int i=256;i<4096;++i) {NEAR(ol[i],l[i],0);NEAR(or_[i],r[i],0);}
    scalar(e,MIX,1);block(e,4096);
    double changed=0;
    for(int i=256;i<4096;++i) {NEAR(ol[i],or_[i],0);changed+=fabs(ol[i]-(l[i]+r[i])*0.5f);}
    assert(changed>20); /* audible repeat, not a trivial dry-only pass */
    scalar(e,GATE,0);block(e,4096);
    for(int i=1024;i<4096;++i) {NEAR(ol[i],l[i],0);NEAR(or_[i],r[i],0);}
    assert(e->getParameter(e,ACTIVE)==0);
    close_fx(e);DONE("float stereo dry / mono centered wet / audible repeat / release");
}
static void test_gain_bypass_smoothing(void) {
    AEffect *e=create();prime(e);scalar(e,GATE,1);
    for(int i=0;i<4096;++i) l[i]=r[i]=0.25;
    block(e,4096);scalar(e,GATE,0);block(e,4096);
    scalar(e,GAIN,1);block(e,4096);
    NEAR(ol[4095],0.25f*powf(10,12.f/20),0.00001f);
    for(int i=1;i<4096;++i) assert(fabsf(ol[i]-ol[i-1])<0.02f);
    e->dispatcher(e,effSetBypass,0,1,NULL,0);block(e,4096);
    NEAR(ol[4095],0.25,0);NEAR(or_[4095],0.25,0);
    e->dispatcher(e,effSetBypass,0,0,NULL,0);scalar(e,GAIN,0);block(e,4096);
    NEAR(ol[4095],0.25f*powf(10,-24.f/20),0.00001f);
    close_fx(e);DONE("gain endpoints, smooth automation and unity bypass");
}
static void test_mix_response(void) {
    const float rates[]={16000,44100,48000,96000};
    const int sizes[]={1,17,31,64,127,128,129,256};
    for(unsigned q=0;q<sizeof(rates)/sizeof(rates[0]);++q) {
        AEffect *e=create();
        e->dispatcher(e,effSetSampleRate,0,0,NULL,rates[q]);
        prime(e);scalar(e,GATE,1);block(e,4096);
        assert(e->getParameter(e,ACTIVE)==1);
        for(int i=0;i<4096;++i) { l[i]=0.25f;r[i]=-0.25f; }
        /* Centered mono wet cancels in L-R. Thus L-R measures the actual mix
         * envelope, independent of loop phase/content, without test-only DSP. */
        for(int turn=0;turn<12;++turn) {
            float target=(turn&1) ? 1 : 0;
            scalar(e,MIX,target);NEAR(e->getParameter(e,MIX),target,0);
            float previous=1-target;
            unsigned elapsed=0, deadline=(unsigned)ceilf(rates[q]*0.005f)+1;
            for(unsigned b=0;elapsed<deadline+256;++b) {
                int n=sizes[b%8];block(e,n);
                for(int i=0;i<n;++i) {
                    float mix=1-(ol[i]-or_[i])*2;
                    assert(mix>=-0.000001f && mix<=1.000001f);
                    assert(fabsf(mix-previous)<=1/(rates[q]*0.005f)+0.000002f);
                    if(target==0) assert(mix<=previous+0.000002f);
                    else assert(mix>=previous-0.000002f);
                    ++elapsed;
                    if(elapsed>=deadline) NEAR(mix,target,0.000002f);
                    previous=mix;
                }
            }
        }
        /* Absolute values keep their established meaning; no encoder-delta
         * guessing that could alter automation or old saved mix percentages. */
        const float positions[]={0,0.01f,0.25f,0.5f,0.75f,0.99f,1};
        for(unsigned i=0;i<7;++i) {
            scalar(e,MIX,positions[i]);block(e,1024);
            NEAR(e->getParameter(e,MIX),positions[i],0);
            NEAR(1-(ol[1023]-or_[1023])*2,positions[i],0.000002f);
        }
        close_fx(e);
    }
    DONE("legacy 5ms monotonic mix slew, rapid reversals, absolute normalization, 16-96k and irregular buffers");
}
static void test_live_mix(void) {
    AEffect *e=create();
    assert(!e->dispatcher(e,effCanBeAutomated,MIX_LIVE,0,NULL,0));
    /* Read-back-relative encoders: 32 slow 1/128 nudges cover the full range. */
    scalar(e,MIX,0);
    for(int direction=0;direction<2;++direction) {
        for(int step=1;step<=32;++step) {
            float current=e->getParameter(e,MIX_LIVE);
            scalar(e,MIX_LIVE,current+(direction ? -1 : 1)/128.f);
            NEAR(e->getParameter(e,MIX),direction ? 1-step/32.f : step/32.f,0.000001f);
        }
    }
    /* Gesture-relative streams with no readback between events, including
     * reversal before a new gesture. The plugin must not fight the host. */
    scalar(e,MIX,0.25f);NEAR(e->getParameter(e,MIX_LIVE),0.25f,0);
    for(int step=1;step<=16;++step) {
        scalar(e,MIX_LIVE,0.25f+step/128.f);
        NEAR(e->getParameter(e,MIX),0.25f+step/32.f,0.000001f);
    }
    for(int step=15;step>=0;--step) {
        scalar(e,MIX_LIVE,0.25f+step/128.f);
        NEAR(e->getParameter(e,MIX),0.25f+step/32.f,0.000001f);
    }
    scalar(e,MIX_LIVE,1);NEAR(e->getParameter(e,MIX),1,0);
    scalar(e,MIX_LIVE,0);NEAR(e->getParameter(e,MIX),0,0);
    scalar(e,MIX,0.4f);NEAR(e->getParameter(e,MIX),0.4f,0);
    scalar(e,MIX_LIVE,0.4f);NEAR(e->getParameter(e,MIX),0.4f,0);
    /* Old 48-byte chunks retain original absolute MIX, not the alias cursor. */
    void *ptr=NULL;unsigned char saved[CHUNK_BYTES];
    assert(e->dispatcher(e,effGetChunk,0,0,&ptr,0)==CHUNK_BYTES);memcpy(saved,ptr,CHUNK_BYTES);
    scalar(e,MIX_LIVE,1);
    assert(e->dispatcher(e,effSetChunk,0,CHUNK_BYTES,saved,0));
    NEAR(e->getParameter(e,MIX),0.4f,0);
    scalar(e,MIX_LIVE,0.4f+1/128.f);
    NEAR(e->getParameter(e,MIX),0.4f+1/32.f,0.000001f);
    scalar(e,MIX_LIVE,NAN);scalar(e,MIX_LIVE,INFINITY);
    NEAR(e->getParameter(e,MIX),0.4f+1/32.f,0.000001f);
    close_fx(e);
    DONE("4x live Q-Link alias, both host gesture styles, reversals, endpoints and legacy 48-byte recall");
}
static void test_display_responsiveness(void) {
    AEffect *e=create();
    struct timespec tick={0,1000000},settle={0,50000000};
    unsigned initial=atomic_load(&display_updates);
    for(int k=0;k<500 && atomic_load(&display_updates)==initial;++k) nanosleep(&tick,NULL);
    assert(atomic_load(&display_updates)>initial);
    nanosleep(&settle,NULL);
    unsigned idle=atomic_load(&display_updates);
    nanosleep(&settle,NULL);assert(atomic_load(&display_updates)==idle);
    unsigned echoes=atomic_load(&control_echoes);
    /* A normal host-owned control change used to get no visual invalidation. */
    scalar(e,MIX,0.25f);scalar(e,MIX,0.75f);
    for(int k=0;k<80 && atomic_load(&display_updates)==idle;++k) nanosleep(&tick,NULL);
    assert(atomic_load(&display_updates)>idle);
    NEAR(e->getParameter(e,MIX),0.75f,0);
    assert(atomic_load(&control_echoes)==echoes);
    nanosleep(&settle,NULL);idle=atomic_load(&display_updates);
    nanosleep(&settle,NULL);assert(atomic_load(&display_updates)==idle);
    close_fx(e);
    DONE("prompt coalesced control redraws, no writable automation echoes, no idle display flooding");
}
static void test_invalid_and_rates(void) {
    AEffect *e=create();float old=e->getParameter(e,LENGTH);
    scalar(e,LENGTH,NAN);scalar(e,LENGTH,INFINITY);NEAR(e->getParameter(e,LENGTH),old,0);
    scalar(e,-1,1);scalar(e,99,1);scalar(e,ACTIVE,1);assert(e->getParameter(e,ACTIVE)==0);
    scalar(e,MIX,-4);assert(e->getParameter(e,MIX)==0);scalar(e,MIX,4);assert(e->getParameter(e,MIX)==1);
    float rates[]={16000,32000,44100,48000,96000};int sizes[]={1,64,127,128,129,256,4096};
    for(unsigned q=0;q<5;++q) {
        assert(e->dispatcher(e,effSetSampleRate,0,0,NULL,rates[q]));
        for(unsigned j=0;j<7;++j) {fill(0,sizes[j]);block(e,sizes[j]);}
    }
    float bad[]={0,-1,NAN,INFINITY,8000,192000};
    for(unsigned j=0;j<6;++j) {
        assert(!e->dispatcher(e,effSetSampleRate,0,0,NULL,bad[j]));scalar(e,GATE,1);
        fill(0,128);block(e,128);assert(e->getParameter(e,STATUS)==1);
        for(int k=0;k<128;++k) {NEAR(ol[k],l[k],0);NEAR(or_[k],r[k],0);}
    }
    e->dispatcher(e,effSetSampleRate,0,0,NULL,44100);scalar(e,GATE,0);block(e,128);
    l[0]=NAN;r[1]=INFINITY;block(e,128);
    assert(e->getParameter(e,STATUS)==0);
    close_fx(e);DONE("invalid parameters/input, 16-96k, arbitrary buffers, bad-rate dry fallback");
}
static void seal_state(unsigned char *b) {
    unsigned h=2166136261u;for(int i=0;i<CHUNK_BYTES-4;++i) h=(h^b[i])*16777619u;
    for(int i=0;i<4;++i)b[CHUNK_BYTES-4+i]=(unsigned char)(h>>(8*i));
}
static void test_state(void) {
    AEffect *e=create();prime(e);scalar(e,LENGTH,0.8);scalar(e,MIX,0.4);scalar(e,GAIN,0.7);scalar(e,GATE,1);block(e,128);
    unsigned char saved[CHUNK_BYTES];void *ptr=NULL;
    assert(e->dispatcher(e,effGetChunk,0,0,&ptr,0)==CHUNK_BYTES);memcpy(saved,ptr,CHUNK_BYTES);
    scalar(e,LENGTH,0.1);scalar(e,MIX,1);scalar(e,GAIN,0);
    assert(e->dispatcher(e,effSetChunk,0,CHUNK_BYTES,saved,0)==1);
    NEAR(e->getParameter(e,LENGTH),0.8f,0);NEAR(e->getParameter(e,MIX),0.4f,0);NEAR(e->getParameter(e,GAIN),0.7f,0);
    assert(e->getParameter(e,GATE)==0&&e->getParameter(e,PUNCH)==0);
    block(e,4096);assert(e->getParameter(e,ACTIVE)==0);
    for(int i=0;i<48;++i) {saved[i]^=0xff;assert(!e->dispatcher(e,effSetChunk,0,CHUNK_BYTES,saved,0));saved[i]^=0xff;}
    /* Valid checksum but invalid semantic payloads must also be rejected. */
    unsigned bad[]={0x7fc00000u,0x7f800000u,0xbf800000u,0x40000000u};
    for(unsigned j=0;j<4;++j) {
        unsigned char b[CHUNK_BYTES];memcpy(b,saved,CHUNK_BYTES);
        for(int i=0;i<4;++i)b[12+i]=(unsigned char)(bad[j]>>(8*i));
        seal_state(b);assert(!e->dispatcher(e,effSetChunk,0,CHUNK_BYTES,b,0));
    }
    unsigned char b[CHUNK_BYTES];memcpy(b,saved,CHUNK_BYTES);b[19]=0x3f;b[18]=0x80; /* gate=1 forbidden */
    seal_state(b);assert(!e->dispatcher(e,effSetChunk,0,CHUNK_BYTES,b,0));
    assert(!e->dispatcher(e,effSetChunk,0,-1,saved,0));assert(!e->dispatcher(e,effSetChunk,0,49,saved,0));
    assert(!e->dispatcher(e,effSetChunk,0,CHUNK_BYTES,NULL,0));
    close_fx(e);DONE("versioned scalar recall; gates/history omitted; 48 corruption checks");
}
static void test_punch_and_notifier(void) {
    AEffect *e=create();prime(e);scalar(e,PUNCH,1);block(e,128);
    assert(e->getParameter(e,PUNCH)==1&&e->getParameter(e,ACTIVE)==1);
    struct timespec t={0,130000000};nanosleep(&t,NULL);
    assert(atomic_load(&notices)>0 && atomic_load(&display_updates)>0);
    for(int k=0;k<170;++k) {fill(k*128,128);block(e,128);}
    assert(e->getParameter(e,PUNCH)==0);assert(e->getParameter(e,ACTIVE)==0);
    scalar(e,PUNCH,1);block(e,128);scalar(e,PUNCH,0);block(e,4096);assert(e->getParameter(e,ACTIVE)==0);
    close_fx(e);DONE("450ms Punch/cancel/auto release and off-audio GUI notifications");
}
typedef struct {AEffect *e;atomic_uint stop;} Stress;
static void *automate(void *v) {
    Stress *s=v;unsigned x=17;
    while(!atomic_load(&s->stop)) {
        x=x*1664525u+1013904223u;scalar(s->e,LENGTH,(x&65535)/65535.f);
        scalar(s->e,MIX,((x>>16)&255)/255.f);scalar(s->e,GAIN,(x&1023)/1023.f);
        scalar(s->e,GATE,(float)(x&1));
    }return NULL;
}
static void test_stress_lifecycle(void) {
    AEffect *e=create();Stress s={.e=e};atomic_init(&s.stop,0);pthread_t th;
    assert(pthread_create(&th,NULL,automate,&s)==0);
    for(unsigned k=0;k<5000;++k) {fill(k*128,128);block(e,128);}
    atomic_store(&s.stop,1);pthread_join(th,NULL);
    scalar(e,GATE,0);block(e,4096);close_fx(e);
    for(int i=0;i<40;++i) {e=create();fill(0,128);block(e,128);close_fx(e);}
    DONE("concurrent automation + 640000 samples + 40 init/destruct cycles");
}
static void test_alias_suspend(void) {
    AEffect *e=create();float *in[]={l,r};fill(0,128);
    float origl[128],origr[128];memcpy(origl,l,sizeof origl);memcpy(origr,r,sizeof origr);
    audio=1;e->processReplacing(e,in,in,128);audio=0;
    for(int i=0;i<128;++i) {NEAR(l[i],origl[i],0);NEAR(r[i],origr[i],0);}
    float *out[]={ol,or_};audio=1;e->processReplacing(e,NULL,out,128);audio=0;
    for(int i=0;i<128;++i) assert(ol[i]==0&&or_[i]==0);
    scalar(e,GATE,1);e->dispatcher(e,effMainsChanged,0,0,NULL,0);assert(e->getParameter(e,GATE)==0);
    fill(0,128);block(e,128);for(int i=0;i<128;++i) NEAR(ol[i],l[i],0);
    audio=1;e->processReplacing(e,NULL,NULL,128);e->processReplacing(e,in,out,0);audio=0;
    close_fx(e);DONE("in-place stereo, null scanner buffers, suspend and zero frames");
}
static void test_clicks_instances(void) {
    AEffect *a=create(),*b=create();
    float previous=0;double biggest=0;
    for(unsigned k=0;k<1000;++k) {
        if(k%40==0) scalar(a,GATE,(float)((k/40)%2));
        for(int i=0;i<128;++i) l[i]=r[i]=(float)(0.2*sin(2*3.141592653589793*(k*128+i)/441));
        block(a,128);
        for(int i=0;i<128;++i) {double d=fabs(ol[i]-previous);if(d>biggest) {biggest=d; if(d>0.025) fprintf(stderr,"jump k=%u i=%d prev=%g out=%g gate=%g active=%g\n",k,i,previous,ol[i],a->getParameter(a,GATE),a->getParameter(a,ACTIVE));} previous=ol[i];}
        block(b,128);assert(b->getParameter(b,ACTIVE)==0);
        for(int i=0;i<128;++i) NEAR(ol[i],l[i],0);
    }
    assert(biggest<0.025);close_fx(a);close_fx(b);DONE("100Hz gate-switch discontinuities bounded; independent histories");
}
static void test_v2_mix_slew(void) {
    const float rates[]={16000,44100,96000};
    for(unsigned q=0;q<3;++q) {
        AEffect *e=create();scalar(e,LEGACY,0);e->dispatcher(e,effSetSampleRate,0,0,NULL,rates[q]);
        memset(l,0,sizeof l);memset(r,0,sizeof r);
        for(int k=0;k<64;++k)block(e,1024);
        scalar(e,GATE,1);block(e,4096);assert(e->getParameter(e,ACTIVE)==1);
        for(int i=0;i<4096;++i){l[i]=.25f;r[i]=-.25f;}
        for(int turn=0;turn<16;++turn) {
            float target=turn&1?1:0,prev=1-target;scalar(e,MIX,target);block(e,1024);
            unsigned deadline=(unsigned)ceilf(rates[q]*.002f)+1;
            for(int i=0;i<1024;++i) {
                float mix=1-(ol[i]-or_[i])*2;
                assert(fabsf(mix-prev)<=1/(rates[q]*.002f)+.000002f);
                if((unsigned)i>=deadline)NEAR(mix,target,.000002f);
                prev=mix;
            }
        }
        close_fx(e);
    }
    DONE("stereo v2 2ms mix transitions: bounded sample slope and settled endpoints at 16/44.1/96k");
}
static void test_quantized_recapture_ownership(void) {
    Engine *e=calloc(1,sizeof(*e));assert(e);engine_reset(e,44100,1);
    EConfig c={.ms=100,.buffer_ms=1000,.chance=1,.seed=1};engine_control(e,&c);
    float l,r;
    for(int i=0;i<10000;++i)engine_tick(e,.2f,.4f,120,&l,&r);
    assert(engine_capture(e));c.gate=1;c.quantized=1;engine_control(e,&c);
    for(int i=0;i<8820;++i)engine_tick(e,.7f,-.1f,120,&l,&r);
    assert(engine_capture(e));
    for(int i=0;i<500;++i) {
        engine_tick(e,-.4f,.9f,120,&l,&r);NEAR(l,.2f,.000001f);NEAR(r,.4f,.000001f);
        assert(e->r.count[e->r.live]==0);
    }
    for(int i=0;i<4200;++i)engine_tick(e,-.4f,.9f,120,&l,&r);
    NEAR(l,.7f,.000001f);NEAR(r,-.1f,.000001f);
    assert(e->r.count[e->r.live]>0);free(e);
    DONE("quantized recapture pins old audible bank until wrap, then resumes recording without source overwrite");
}
static void test_sequence_clock_drift(void) {
    Engine *e=calloc(1,sizeof(*e));assert(e);engine_reset(e,44100,1);
    EConfig c={.ms=100,.buffer_ms=1000,.chance=1,.seed=1,.run=1,.state_div=4};engine_control(e,&c);
    float l,r;
    for(int i=0;i<200000;++i)engine_tick(e,0,0,120,&l,&r);
    double ticks=e->r.next_beat/engine_division(4);
    NEAR(ticks,round(ticks),.00000001);
    assert(e->r.next_beat>=e->r.beat && e->r.next_beat-e->r.beat<=engine_division(4));
    free(e);DONE("sequencer fractional-sample clock stays on its beat grid without cumulative boundary drift");
}
static void test_v2_rt(void) {
    AEffect *e=create();scalar(e,LEGACY,0);prime(e);
    for(unsigned k=0;k<1500;++k) {
        if(!(k%16)) {
            scalar(e,LENGTH,(k%101)/100.f);scalar(e,BREAK,(k%73)/72.f);
            scalar(e,BEND,(k%29)/28.f);scalar(e,CORRUPT,(k%53)/52.f);
            scalar(e,REVERSE,(float)(k&1));scalar(e,MUTATION,.3f);
            scalar(e,SEQ_RUN,(float)((k/32)&1));scalar(e,GATE,1);
            scalar(e,CAPTURE_CMD,1);scalar(e,STORE_STATE,1);
        }
        fill(k*128,128);block(e,128);
    }
    VstMidiEvent note={.type=1,.byteSize=sizeof(VstMidiEvent),.midiData={0x90,38,100,0}};
    VstEvents ev={.numEvents=1,.events={(VstEvent *)&note,NULL}};
    e->dispatcher(e,effProcessEvents,0,0,&ev,0);fill(0,128);block(e,128);
    scalar(e,GATE,0);scalar(e,SEQ_RUN,0);block(e,4096);close_fx(e);
    DONE("stereo v2 macros/capture/sequencing/MIDI: zero prohibited RT calls, bounded memory and finite audio");
}
int main(void) {
    /* Prove that guard instrumentation is armed, then reset the expected probe. */
    audio=1;void *p=__wrap_malloc(1);__wrap_free(p);audio=0;
    assert(atomic_load(&violations)==2);atomic_store(&violations,0);
    test_oracle();test_core_boundaries();test_silence_impulse();test_stereo_and_repeat();
    test_gain_bypass_smoothing();test_mix_response();test_live_mix();test_display_responsiveness();
    test_invalid_and_rates();test_state();test_punch_and_notifier();
    test_stress_lifecycle();test_alias_suspend();test_clicks_instances();test_v2_mix_slew();test_quantized_recapture_ownership();test_sequence_clock_drift();test_v2_rt();
    assert(atomic_load(&violations)==0);
    DONE("zero wrapped RT allocation/mutex/file/join/host-callback violations");
    printf("PASS %u native cases; realtime guard violations: %u\n",cases,atomic_load(&violations));
    return 0;
}
