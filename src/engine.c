/* SPDX-License-Identifier: GPL-3.0-only. Fixed storage, O(1) capture, no RT I/O. */
#include "engine.h"
#include <math.h>
#include <string.h>
static float clamp(float x,float lo,float hi) { return fmaxf(lo,fminf(hi,x)); }
static unsigned random_u(Engine *e) {
    unsigned x=e->r.rng; x^=x<<13;x^=x>>17;x^=x<<5;e->r.rng=x;return x;
}
static float random_f(Engine *e) { return (random_u(e)>>8)*(1.f/16777216.f); }
float engine_division(unsigned n) {
    static const float beats[]={1,.5f,.25f,.125f,.0625f,1.f/3,1.f/6,1.f/12,.75f,.375f,.1875f};
    return beats[n<11?n:0];
}
void engine_reset(Engine *e,float rate,unsigned seed) {
    /* Never clear the megabyte arrays in render: validity counters exclude stale data. */
    memset(&e->r,0,sizeof(e->r));e->r.rate=rate;e->r.capacity=(unsigned)(rate*2);
    if(e->r.capacity>E_CAPACITY)e->r.capacity=E_CAPACITY;
    e->r.fade=(unsigned)ceilf(rate*.002f);e->r.captured=-1;e->r.voice.bank=-1;e->r.old.bank=-1;
    e->r.cycle_rate=1;e->r.rng=seed?seed:1;e->r.cycle_allowed=1;e->r.step=-1;
}
static void transition(Engine *e,EVoice v) {
    ERuntime *r=&e->r;
    /* Latest transition wins, blending from the actual preceding wet sample.
     * This avoids discontinuities even when gestures outrun the 2 ms fade. */
    r->old=r->voice;r->voice=v;r->fade_left=r->fade;
}
int engine_capture(Engine *e) {
    ERuntime *r=&e->r;unsigned b=r->live,n=r->count[b];
    if(n<2)return 0;
    r->captured=(int)b;r->cap_count=n;r->cap_start=(r->write[b]+r->capacity-n)%r->capacity;
    r->live=1-b;r->write[r->live]=r->count[r->live]=0;
    /* A new source is selected by the next control/tick; no bulk copying. */
    return 1;
}
static EConfig effective(Engine *e) {
    EConfig c=e->r.base;
    if(e->r.scene_on && e->r.step>=0) {
        float *v=e->scene[e->r.step].v;
        if(v[8]>=.5f) {
            unsigned mask=e->r.overrides;
            if(!(mask&1)) {c.ms=5+445*v[0];c.grid=(unsigned)lroundf(v[0]*10);}
            if(!(mask&2))c.position=clamp(v[1]+e->r.mutation_offset[0]*c.mutation,0,1);
            if(!(mask&4))c.bend=clamp(-24+48*v[2]+24*e->r.mutation_offset[1]*c.mutation,-24,24);
            if(!(mask&8))c.fracture=clamp(v[3]+e->r.mutation_offset[2]*c.mutation,0,1);
            if(!(mask&16))c.corrupt=v[4];
            if(!(mask&32))c.reverse=v[5]>=.5f;
            if(!(mask&512))c.pitch=-12+24*v[9];
        }
    }
    return c;
}
static void region(Engine *e,int force) {
    ERuntime *r=&e->r;
    if(r->captured<0)return;
    unsigned available=(unsigned)(r->effective.buffer_ms*r->rate/1000);
    if(available>r->cap_count)available=r->cap_count;
    if(available<2)available=2;
    unsigned length=(unsigned)lroundf(r->effective_ms*r->rate/1000);
    if(length<2)length=2;if(length>available)length=available;
    unsigned skip=r->cap_count-available+(unsigned)(clamp(r->effective.position,0,1)*(available-length));
    EVoice v={(int)r->captured,(r->cap_start+skip)%r->capacity,length,0};
    if(force || v.bank!=r->voice.bank || v.start!=r->voice.start || v.length!=r->voice.length) {
        if(r->playing && r->base.quantized && !force)return;
        transition(e,v);
    }
}
void engine_control(Engine *e,const EConfig *c) {
    ERuntime *r=&e->r;
    if(c->seed!=r->base.seed)r->rng=c->seed?c->seed:1;
    if(c->run && !r->base.run) { r->step=-1;r->next_beat=r->beat; }
    if(!c->run && r->base.run)r->scene_on=0;
    if(r->base.run && r->scene_on) {
        if(c->ms!=r->base.ms || c->grid!=r->base.grid)r->overrides|=1;
        if(c->position!=r->base.position)r->overrides|=2;
        if(c->bend!=r->base.bend)r->overrides|=4;
        if(c->fracture!=r->base.fracture)r->overrides|=8;
        if(c->corrupt!=r->base.corrupt)r->overrides|=16;
        if(c->reverse!=r->base.reverse)r->overrides|=32;
        if(c->pitch!=r->base.pitch)r->overrides|=512;
    }
    r->base=*c;r->effective=effective(e);r->speed=exp2f((r->effective.bend+r->effective.pitch)/12);
    if(!c->time_grid)r->effective_ms=r->effective.ms;
    region(e,0);
}
void engine_select(Engine *e,unsigned n) {
    e->r.step=(int)(n%8);e->r.scene_on=e->scene[n%8].v[8]>=.5f;
    e->r.next_beat=e->r.beat+engine_division(e->r.base.state_div)*engine_division((unsigned)lroundf(e->scene[n%8].v[7]*10));e->r.effective=effective(e);e->r.speed=exp2f((e->r.effective.bend+e->r.effective.pitch)/12);
    e->r.effective_ms=e->r.effective.ms;
    region(e,!e->r.base.quantized);
}
static float sample(const Engine *e,EVoice v,unsigned ch,double phase) {
    if(v.bank<0 || v.length<2)return 0;
    while(phase<0)phase+=v.length; /* phase range limited by max speed < 8 */
    while(phase>=v.length)phase-=v.length;
    unsigned k=(unsigned)phase,n=k+1==v.length?0:k+1;
    unsigned a=(v.start+k)%e->r.capacity,b=(v.start+n)%e->r.capacity;
    float f=(float)(phase-k);
    return e->ring[v.bank][ch][a]+(e->ring[v.bank][ch][b]-e->ring[v.bank][ch][a])*f;
}
static void sequence(Engine *e,float tempo) {
    ERuntime *r=&e->r;
    if(!r->base.run || r->beat<r->next_beat)return;
    r->step=r->base.random?(int)(random_u(e)%8):(r->step+1)%8;
    EScene *s=&e->scene[r->step];r->scene_on=s->v[8]>=.5f && (s->v[6]>=1 || random_f(e)<s->v[6]);
    r->overrides=0;
    for(int i=0;i<3;++i)r->mutation_offset[i]=r->base.mutation>0?random_f(e)-.5f:0;
    r->effective=effective(e);
    r->speed=exp2f((r->effective.bend+r->effective.pitch)/12);
    unsigned div=(unsigned)lroundf((s->v[7]>=0?s->v[7]:r->base.state_div/10.f)*10);
    r->next_beat+=engine_division(r->base.state_div)*engine_division(div);
    r->effective_ms=r->base.time_grid?60000.f/tempo*engine_division(r->effective.grid):r->effective.ms;
    region(e,!r->base.quantized);
}
void engine_tick(Engine *e,float l,float rr,float tempo,float *wl,float *wr) {
    ERuntime *r=&e->r;sequence(e,tempo);
    r->beat+=tempo/(60*r->rate);
    if(r->base.time_grid)r->effective_ms=60000.f/tempo*engine_division(r->effective.grid);
    int want=r->base.gate || r->base.freeze || (r->base.run && r->scene_on);
    if(want && !r->playing) {
        if(r->captured<0) {
            unsigned needed=(unsigned)lroundf(r->effective_ms*r->rate/1000);
            unsigned limit=(unsigned)(r->effective.buffer_ms*r->rate/1000);
            if(needed>limit)needed=limit;if(needed>r->capacity)needed=r->capacity;if(needed<2)needed=2;
            if(r->count[r->live]>=needed)engine_capture(e);
        }
        r->effective=effective(e);region(e,1);r->playing=r->captured>=0;
        r->cycle_allowed=r->effective.chance>=1 || random_f(e)<r->effective.chance;
    }
    if(!want)r->playing=0;
    /* Continuous capture on the other bank; freeze pauses only new recording.
     * Capture pins a snapshot while incoming audio continues into a fresh bank. */
    /* With two banks, quantized recapture temporarily pins BOTH sources.
     * Do not overwrite the old audible bank before its final loop completes. */
    if((!r->base.freeze || r->captured<0) && !(r->playing && r->voice.bank==(int)r->live)) {
        unsigned b=r->live,k=r->write[b];
        e->ring[b][0][k]=fabsf(l)<1e-30f?0:clamp(l,-4,4);
        e->ring[b][1][k]=fabsf(rr)<1e-30f?0:clamp(rr,-4,4);
        r->write[b]=(k+1)%r->capacity;if(r->count[b]<r->capacity)++r->count[b];
    }
    if(!r->playing || r->voice.bank<0) { *wl=l;*wr=rr;return; }
    double speed=r->speed*r->cycle_rate;
    /* Bend instability grows gradually; no modulation/random work at zero. */
    if(r->effective.bend!=0) {
        float depth=fabsf(r->effective.bend)/24;
        float phase=(float)(r->beat-floor(r->beat));
        speed*=1+.04*depth*(1-4*fabsf(phase-.5f));
        if(depth>.9f)speed*=clamp((1-depth)*10+.05f,.05f,1);
    }
    if(r->effective.reverse!=r->cycle_reverse)speed=-speed;
    float wet[2];
    for(unsigned c=0;c<2;++c) {
        wet[c]=sample(e,r->voice,c,r->voice.phase);
        if(r->fade_left) {
            float t=1-(float)r->fade_left/r->fade;
            wet[c]=r->last[c]+(wet[c]-r->last[c])*t;
        }
    }
    if(r->fade_left)--r->fade_left;
    r->voice.phase+=speed;
    int wrapped=r->voice.phase<0 || r->voice.phase>=r->voice.length;
    if(wrapped) {
        while(r->voice.phase<0)r->voice.phase+=r->voice.length;
        while(r->voice.phase>=r->voice.length)r->voice.phase-=r->voice.length;
        ++r->cycle;
        float bend_depth=fabsf(r->effective.bend)/24;
        r->cycle_rate=1;r->cycle_reverse=0;
        if(bend_depth>.25f && random_f(e)<bend_depth*r->effective.density) {
            static const float jumps[]={-12,-7,7,12};
            r->cycle_rate=exp2f(jumps[random_u(e)%4]/12);
            r->cycle_reverse=random_f(e)<bend_depth*.4f;
        }
        r->cycle_allowed=r->effective.chance>=1 || random_f(e)<r->effective.chance;
        region(e,1); /* commit pending length/position at this repeat boundary */
        r->fade_left=r->fade;
    }
    float fracture=r->effective.fracture;
    if(fracture>0) {
        unsigned pieces=2+(unsigned)(fracture*14);
        double cell=(double)r->voice.length/pieces;
        unsigned phase=(unsigned)(r->voice.phase/cell);
        float fraction=(float)(r->voice.phase/cell-phase);
        /* Retriggered micro-slices plus bounded skips/dropouts. */
        if(fraction<fracture*.5f)for(unsigned c=0;c<2;++c)
            wet[c]=sample(e,r->voice,c,fmod(r->voice.phase,cell));
        if(fracture>.5f && ((phase+r->cycle)%5)==0)wet[0]=wet[1]=0;
        if(wrapped && random_f(e)<r->effective.density*fracture)
            r->voice.phase=(random_u(e)%pieces)*cell;
    }
    float corrupt=r->effective.corrupt;
    if(corrupt>0) {
        unsigned hold=1+(unsigned)(corrupt*47),bits=16-(unsigned)(corrupt*12);
        float scale=(float)(1u<<(bits-1));
        if(!r->hold_left) { for(unsigned c=0;c<2;++c)r->held[c]=roundf(clamp(wet[c],-1,1)*scale)/scale;r->hold_left=hold; }
        --r->hold_left;
        for(unsigned c=0;c<2;++c)wet[c]=wet[c]*(1-corrupt)+r->held[c]*corrupt;
    }
    if(!r->cycle_allowed || (r->base.run && !r->scene_on)) { wet[0]=l;wet[1]=rr; }
    for(unsigned c=0;c<2;++c)r->last[c]=wet[c];
    *wl=wet[0];*wr=wet[1];
}
