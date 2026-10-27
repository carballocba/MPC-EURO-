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
/* Four preallocated banks: rolling history, held take, new take, spare.
 * Audio owner alone changes ownership. No copying, clearing, allocation or waits. */
void engine_reset(Engine *e,float rate,unsigned seed) {
    ERuntime old=e->r;
    memset(&e->r,0,sizeof(e->r));ERuntime *r=&e->r;
    r->rate=rate;r->capacity=(unsigned)(rate*8);if(r->capacity>E_CAPACITY)r->capacity=E_CAPACITY;
    r->fade=(unsigned)ceilf(rate*.005f);r->captured=r->voice.bank=r->old.bank=-1;
    r->held_bank=r->record_bank=-1;r->cycle_rate=1;r->rng=seed?seed:1;r->cycle_allowed=1;r->step=-1;
    r->record_limit=r->configured_limit=r->capacity;r->initialized=1;
    /* Preset/mains changes at the same rate preserve material and an already
     * latched recorder. A preset cannot start a recorder in a fresh instance.
     * Sample rate changes invalidate material; no resampling in the callback. */
    if(old.initialized && old.rate==rate){
        for(unsigned b=0;b<E_BANKS;++b){r->write[b]=old.write[b];r->count[b]=old.count[b];r->total[b]=old.total[b];}
        r->live=old.live;r->held_bank=old.held_bank;r->held_start=old.held_start;r->held_count=old.held_count;
        r->record_limit=old.record_limit;r->configured_limit=old.configured_limit;
        r->recording=old.recording;r->record_bank=old.record_bank;r->record_count=old.record_count;r->full=old.full;r->clean=old.clean;r->repeat=old.repeat;
    }
}
static void transition(Engine *e,EVoice v) {
    ERuntime *r=&e->r;r->old=r->voice;r->voice=v;r->fade_left=r->fade;
    r->fade_from[0]=r->last[0];r->fade_from[1]=r->last[1];
}
static int free_bank(Engine *e) {
    ERuntime *r=&e->r;
    for(unsigned b=0;b<E_BANKS;++b)if(b!=r->live && (int)b!=r->held_bank && (int)b!=r->record_bank && (!r->playing || (int)b!=r->voice.bank))return (int)b;
    return -1;
}
void ghost_buffer_limit(Engine *e,float seconds) {
    if(!isfinite(seconds))return;
    e->r.configured_limit=(unsigned)lroundf(clamp(seconds,.25f,8)*e->r.rate);
    if(e->r.configured_limit>e->r.capacity)e->r.configured_limit=e->r.capacity;
    if(!e->r.recording)e->r.record_limit=e->r.configured_limit;
}
void ghost_buffer_clean(Engine *e){e->r.clean=1;e->r.repeat=0;}
void ghost_buffer_rearm(Engine *e){e->r.clean=0;}
void ghost_buffer_record(Engine *e,unsigned on) {
    ERuntime *r=&e->r;
    if(on && !r->recording){
        int b=free_bank(e);if(b<0)return;
        r->record_bank=b;r->record_limit=r->configured_limit;r->record_count=0;r->write[b]=r->count[b]=0;r->total[b]=0;r->recording=1;r->full=0;
    }else if(!on && r->recording){
        r->recording=0;
        if(r->record_count>=2){
            r->held_bank=r->record_bank;r->held_start=0;r->held_count=r->record_count;
            r->source_held=1;r->base.freeze=r->effective.freeze=1;
            r->captured=-1;r->playing=0; /* next tick crossfades into new source */
            r->clean=0;
        }
        r->record_bank=-1;
    }
}
int engine_capture(Engine *e) {
    ERuntime *r=&e->r;
    /* Legacy/MIDI/generative snapshots remain one-shot. A held take is protected. */
    if(r->source_held || r->recording || r->count[r->live]<2)return 0;
    int next=free_bank(e);if(next<0)return 0;
    unsigned b=r->live;
    r->held_bank=(int)b;r->held_count=r->count[b];r->held_start=(r->write[b]+r->capacity-r->held_count)%r->capacity;
    r->live=(unsigned)next;r->write[next]=r->count[next]=0;r->total[next]=0;
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
    if(r->source_held && r->held_bank>=0){r->captured=r->held_bank;r->cap_start=r->held_start;r->cap_count=r->held_count;}
    else if(r->repeat && r->captured>=0 && r->captured!=(int)r->live){ /* pinned manual region; LIVE writer owns another bank */ }
    else if((force || r->captured<0 || r->voice.bank!=(int)r->live) && r->count[r->live]>=2){
        r->captured=(int)r->live;r->cap_count=r->count[r->live];r->cap_start=(r->write[r->live]+r->capacity-r->cap_count)%r->capacity;
    }
    if(r->captured<0 || r->cap_count<2)return;
    unsigned available=(unsigned)(r->effective.buffer_ms*r->rate/1000);
    if(available>r->cap_count)available=r->cap_count;
    if(available<2)available=2;
    unsigned length=(unsigned)lroundf(r->effective_ms*r->rate/1000);
    if(length<2)length=2;if(length>available)length=available;
    /* Position addresses the complete held take/history; Size limits window length. */
    unsigned skip=r->source_held?(unsigned)(clamp(r->effective.position,0,1)*(r->cap_count-length)):
        r->cap_count-available+(unsigned)(clamp(r->effective.position,0,1)*(available-length));
    EVoice v={(int)r->captured,(r->cap_start+skip)%r->capacity,length,(r->effective.reverse!=r->cycle_reverse)?(double)(length-1):0};
    if(force || v.bank!=r->voice.bank || v.start!=r->voice.start || v.length!=r->voice.length) {
        if(r->playing && r->base.quantized && !force)return;
        r->voice_origin=r->total[v.bank]-(r->cap_count-skip);
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
    unsigned held=c->freeze!=0;
    held=held && r->held_bank>=0;
    if(held!=r->source_held){r->source_held=held;r->captured=-1;r->playing=0;}
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
    /* A Freeze requested before any material waits for a complete region,
     * then pins it. Never label a still-moving history reader as HELD. */
    if(r->base.freeze && r->held_bank<0 && !r->recording){
        unsigned needed=(unsigned)lroundf(r->effective_ms*r->rate/1000);
        unsigned limit=(unsigned)(r->effective.buffer_ms*r->rate/1000);
        if(needed>limit)needed=limit;if(needed>r->capacity)needed=r->capacity;if(needed<2)needed=2;
        if(r->count[r->live]>=needed && engine_capture(e)){r->source_held=1;r->captured=-1;r->playing=0;}
    }
    /* Pin only after sufficient history; rotating writer is O(1), no copy/allocation.
    * A HELD take and an active recorder retain their own bank ownership. */
    if(r->repeat && !r->source_held && !r->clean && (r->captured<0 || r->captured==(int)r->live)){
        unsigned needed=(unsigned)lroundf(r->effective_ms*r->rate/1000);
        unsigned limit=(unsigned)(r->effective.buffer_ms*r->rate/1000);
        if(needed>limit)needed=limit;if(needed>r->capacity)needed=r->capacity;if(needed<2)needed=2;
        if(r->count[r->live]>=needed){int next=free_bank(e);if(next>=0){
            region(e,1);r->live=(unsigned)next;r->write[next]=r->count[next]=0;r->total[next]=0;
        }}
    }
    int want=!r->clean && !r->suspended && (r->base.gate || r->source_held || r->effective.reverse || r->repeat || (r->base.run && r->scene_on));
    if(want && !r->playing){
        r->effective=effective(e);region(e,1);r->playing=r->voice.bank>=0 && r->cap_count>=2;
        r->cycle_allowed=r->effective.chance>=1 || random_f(e)<r->effective.chance;
    }
    if(!want)r->playing=0;
    /* Never read overwritten history, even at very slow pitch or tempo.
     * Re-select current valid material before writer reaches the oldest sample. */
    if(r->playing && r->voice.bank==(int)r->live && r->total[r->live]-r->voice_origin>=r->capacity)region(e,1);
    unsigned b=r->live,k=r->write[b];
    e->ring[b][0][k]=fabsf(l)<1e-30f?0:clamp(l,-4,4);
    e->ring[b][1][k]=fabsf(rr)<1e-30f?0:clamp(rr,-4,4);
    r->write[b]=(k+1)%r->capacity;if(r->count[b]<r->capacity)++r->count[b];++r->total[b];
    if(r->recording){
        unsigned rb=(unsigned)r->record_bank,n=r->record_count;
        e->ring[rb][0][n]=clamp(l,-4,4);e->ring[rb][1][n]=clamp(rr,-4,4);
        ++r->record_count;r->write[rb]=r->count[rb]=r->record_count;r->total[rb]=r->record_count;
        if(r->record_count>=r->record_limit){unsigned clean=r->clean;r->full=1;ghost_buffer_record(e,0);r->clean=clean;region(e,1);r->playing=!r->clean && !r->suspended;}
    }
    if(!r->playing || r->voice.bank<0) {r->last[0]=l;r->last[1]=rr;*wl=l;*wr=rr;return;}
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
            wet[c]=r->fade_from[c]+(wet[c]-r->fade_from[c])*t;
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
    if(!r->repeat && (!r->cycle_allowed || (r->base.run && !r->scene_on))) { wet[0]=l;wet[1]=rr; }
    for(unsigned c=0;c<2;++c)r->last[c]=wet[c];
    *wl=wet[0];*wr=wet[1];
}
