#define _POSIX_C_SOURCE 200809L
#include "vst2_abi.h"
#include "repeat.h"
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
enum { LENGTH,GATE,MIX,GAIN,PUNCH,BYPASS,ACTIVE,STATUS };
static _Thread_local int audio;
static atomic_uint violations, notices, display_updates;
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
    GUARD();
    if(op==audioMasterAutomate) atomic_fetch_add(&notices,1);
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
    assert(e->magic==0x56737450 && e->numInputs==2 && e->numOutputs==2 && e->numParams==8);
    assert(e->uniqueID==0x45754272 && !(e->flags&effFlagsIsSynth));
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
    unsigned h=2166136261u;for(int i=0;i<44;++i) h=(h^b[i])*16777619u;
    for(int i=0;i<4;++i)b[44+i]=(unsigned char)(h>>(8*i));
}
static void test_state(void) {
    AEffect *e=create();prime(e);scalar(e,LENGTH,0.8);scalar(e,MIX,0.4);scalar(e,GAIN,0.7);scalar(e,GATE,1);block(e,128);
    unsigned char saved[48];void *ptr=NULL;
    assert(e->dispatcher(e,effGetChunk,0,0,&ptr,0)==48);memcpy(saved,ptr,48);
    scalar(e,LENGTH,0.1);scalar(e,MIX,1);scalar(e,GAIN,0);
    assert(e->dispatcher(e,effSetChunk,0,48,saved,0)==1);
    NEAR(e->getParameter(e,LENGTH),0.8f,0);NEAR(e->getParameter(e,MIX),0.4f,0);NEAR(e->getParameter(e,GAIN),0.7f,0);
    assert(e->getParameter(e,GATE)==0&&e->getParameter(e,PUNCH)==0);
    block(e,4096);assert(e->getParameter(e,ACTIVE)==0);
    for(int i=0;i<48;++i) {saved[i]^=0xff;assert(!e->dispatcher(e,effSetChunk,0,48,saved,0));saved[i]^=0xff;}
    /* Valid checksum but invalid semantic payloads must also be rejected. */
    unsigned bad[]={0x7fc00000u,0x7f800000u,0xbf800000u,0x40000000u};
    for(unsigned j=0;j<4;++j) {
        unsigned char b[48];memcpy(b,saved,48);
        for(int i=0;i<4;++i)b[12+i]=(unsigned char)(bad[j]>>(8*i));
        seal_state(b);assert(!e->dispatcher(e,effSetChunk,0,48,b,0));
    }
    unsigned char b[48];memcpy(b,saved,48);b[19]=0x3f;b[18]=0x80; /* gate=1 forbidden */
    seal_state(b);assert(!e->dispatcher(e,effSetChunk,0,48,b,0));
    assert(!e->dispatcher(e,effSetChunk,0,-1,saved,0));assert(!e->dispatcher(e,effSetChunk,0,49,saved,0));
    assert(!e->dispatcher(e,effSetChunk,0,48,NULL,0));
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
int main(void) {
    /* Prove that guard instrumentation is armed, then reset the expected probe. */
    audio=1;void *p=__wrap_malloc(1);__wrap_free(p);audio=0;
    assert(atomic_load(&violations)==2);atomic_store(&violations,0);
    test_oracle();test_core_boundaries();test_silence_impulse();test_stereo_and_repeat();
    test_gain_bypass_smoothing();test_invalid_and_rates();test_state();test_punch_and_notifier();
    test_stress_lifecycle();test_alias_suspend();test_clicks_instances();
    assert(atomic_load(&violations)==0);
    DONE("zero wrapped RT allocation/mutex/file/join/host-callback violations");
    printf("PASS %u native cases; realtime guard violations: %u\n",cases,atomic_load(&violations));
    return 0;
}
