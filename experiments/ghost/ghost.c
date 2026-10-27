/* SPDX-License-Identifier: GPL-3.0-only. No third-party script code imported. */
#include "ghost.h"
#include <math.h>
#include <string.h>
static float clamp(float x,float lo,float hi) {return fmaxf(lo,fminf(hi,x));}
/* Counter-based domain-separated mixer: no shared mutable random stream. */
uint32_t ghost_random(unsigned seed,uint64_t index,unsigned domain) {
    uint64_t x=index ^ ((uint64_t)seed<<32) ^ ((uint64_t)(domain+1)*UINT64_C(0x9e3779b97f4a7c15));
    x=(x^(x>>30))*UINT64_C(0xbf58476d1ce4e5b9);
    x=(x^(x>>27))*UINT64_C(0x94d049bb133111eb);
    return (uint32_t)((x^(x>>31))>>32);
}
static float random_f(const Ghost *g,uint64_t n,unsigned d) {return (ghost_random(g->config.seed,n,d)>>8)*(1.f/16777216.f);}
static int finite_range(double x,double lo,double hi) {return isfinite(x)&&x>=lo&&x<=hi;}
static double position(const Ghost *g) {return g->config.beat_sync?g->beat:(double)g->sample;}
static double samples(const Ghost *g,double ms) {return ms*g->rate/1000;}
GConfig ghost_defaults(void) {
    GConfig c={0};c.beat_sync=1;c.density=4;c.seed=1;c.distance=.25;c.probability=.75f;
    c.duration_ms=60;c.rest_ms=15;c.capture_cooldown_ms=100;
    for(unsigned d=0;d<G_DESTINATIONS;++d)c.destination[d]=(GDestination){0,1,1,0,1,1,0};
    c.destination[G_LENGTH].minimum=15;c.destination[G_LENGTH].maximum=125;
    return c;
}
EConfig ghost_manual_defaults(void) {
    EConfig c={0};c.ms=100;c.buffer_ms=1000;c.chance=1;c.density=.25f;c.seed=1;return c;
}
int ghost_init(Ghost *g,double rate) {
    if(!g||!finite_range(rate,16000,96000))return 0;
    memset(g,0,sizeof(*g));g->rate=rate;g->tempo=120;g->beat_step=120/(60*rate);g->playing=1;
    g->config=ghost_defaults();g->manual=ghost_manual_defaults();return 1;
}
static void cancel(Ghost *g) {
    if(g->active)g->pending|=G_END;
    g->active=g->freeze=g->destinations=0;
}
void ghost_reset(Ghost *g) {
    cancel(g);g->opportunity=0;g->next=position(g);g->rest_until=(double)g->sample;
    g->have_capture=0;g->pending|=G_RECONFIGURE;
}
static int valid_config(const GConfig *c) {
    if(!c||c->enabled>1||c->beat_sync>1||c->density>16||c->rotation>15||
       !finite_range(c->distance,c->beat_sync?1./64:5,c->beat_sync?64:60000)||
       !finite_range(c->probability,0,1)||!finite_range(c->duration_ms,.1,60000)||
       !finite_range(c->rest_ms,0,60000)||!finite_range(c->jitter,0,.4f)||
       !finite_range(c->capture_cooldown_ms,5,60000))return 0;
    for(unsigned d=0;d<G_DESTINATIONS;++d) {
        const GDestination *r=&c->destination[d];float lo=d==G_LENGTH?5:0,hi=d==G_LENGTH?450:1;
        if(r->enabled>1||r->interval<1||r->interval>64||!finite_range(r->probability,0,1)||
           !finite_range(r->minimum,lo,hi)||!finite_range(r->maximum,r->minimum,hi)||
           !finite_range(r->depth,0,1)||!finite_range(r->smooth_ms,0,2000))return 0;
        /* Discrete actions do not pretend to have continuous depth/ranges. */
        if(d>=G_CAPTURE&&(r->minimum!=0||r->maximum!=1||r->depth!=1||r->smooth_ms!=0))return 0;
    }
    return 1;
}
int ghost_configure(Ghost *g,const GConfig *c) {
    if(!g||!valid_config(c))return 0;
    int timing=g->config.beat_sync!=c->beat_sync||g->config.distance!=c->distance;
    int restart=g->config.seed!=c->seed||(!g->config.enabled&&c->enabled);
    cancel(g);g->config=*c;g->pending|=G_RECONFIGURE;
    if(timing||restart)ghost_reset(g);
    return 1;
}
static int valid_manual(const EConfig *c) {
    return c&&finite_range(c->ms,5,450)&&finite_range(c->position,0,1)&&
      finite_range(c->buffer_ms,50,2000)&&finite_range(c->bend,-24,24)&&finite_range(c->pitch,-12,12)&&
      finite_range(c->fracture,0,1)&&finite_range(c->corrupt,0,1)&&finite_range(c->chance,0,1)&&
      finite_range(c->density,0,1)&&finite_range(c->mutation,0,1)&&c->grid<=10&&c->time_grid<=1&&
      c->quantized<=1&&c->reverse<=1&&c->freeze<=1&&c->gate<=1&&c->run<=1&&c->random<=1&&c->state_div<=10;
}
int ghost_manual(Ghost *g,const EConfig *c,unsigned mask) {
    if(!g||!valid_manual(c)||(mask&~(15u|G_GATE_OVERRIDE)))return 0;
    g->manual=*c;g->overrides|=mask;g->pending|=G_MANUAL;return 1;
}
void ghost_release_override(Ghost *g,unsigned mask) {g->overrides&=~mask;g->pending|=G_MANUAL;}
void ghost_capture(Ghost *g) {g->capture_manual=1;}
void ghost_clean(Ghost *g) {
    cancel(g);g->config.enabled=0;g->manual.gate=g->manual.freeze=g->manual.run=0;
    g->capture_manual=0;g->overrides=0;g->pending|=G_CLEAN;
}
int ghost_clock(Ghost *g,double tempo,unsigned playing,unsigned seek,double ppq) {
    if(!g||playing>1||seek>1||(seek&&!finite_range(ppq,0,1e9)))return 0;
    g->fallback=!finite_range(tempo,20,400);g->tempo=g->fallback?120:tempo;g->beat_step=g->tempo/(60*g->rate);
    if(seek)g->beat=ppq;
    if(seek||!playing||(playing&&!g->playing)) {
        cancel(g);g->next=position(g);g->rest_until=(double)g->sample;g->pending|=G_RECONFIGURE;
    }
    g->playing=playing;return 1;
}
static void start(Ghost *g,GFrame *f,uint64_t n,double interval) {
    g->active=1;g->freeze=0;g->destinations=0;g->overrides=0;++g->generation;
    double sample_interval=g->config.beat_sync?interval*60*g->rate/g->tempo:interval;
    double duration=fmin(samples(g,g->config.duration_ms),sample_interval*.85);
    g->until=(double)g->sample+duration;g->rest_until=g->until+samples(g,g->config.rest_ms);
    f->flags|=G_START;
    for(unsigned d=0;d<G_DESTINATIONS;++d) {
        const GDestination *r=&g->config.destination[d];
        if(!r->enabled||n%r->interval||r->probability<=0||(r->probability<1&&random_f(g,n,16+4*d)>=r->probability))continue;
        if(d<2) {
            if(r->depth<=0||(d==G_LENGTH&&g->manual.time_grid))continue;
            float base=d==G_LENGTH?g->manual.ms:g->manual.fracture;
            float initial=clamp(base,r->minimum,r->maximum);
            float chosen=r->minimum+(r->maximum-r->minimum)*random_f(g,n,17+4*d);
            g->target[d]=clamp(initial+r->depth*(chosen-initial),r->minimum,r->maximum);
            g->value[d]=r->smooth_ms>0?initial:g->target[d];
            g->increment[d]=r->smooth_ms>0?(g->target[d]-initial)/(r->smooth_ms*g->rate/1000):0;
            g->destinations|=1u<<d;
        } else if(d==G_CAPTURE) {
            uint64_t cooldown=(uint64_t)ceil(g->config.capture_cooldown_ms*g->rate/1000);
            if(!g->have_capture||g->sample-g->last_capture>=cooldown) {
                f->flags|=G_CAPTURE_PULSE;g->last_capture=g->sample;g->have_capture=1;
            }
        } else {g->freeze=1;g->destinations|=1u<<d;}
    }
}
void ghost_tick(Ghost *g,GFrame *f) {
    if(g->pending&G_CLEAN)ghost_clean(g);
    memset(f,0,sizeof(*f));f->sample=g->sample;f->flags=g->pending;g->pending=0;
    double now=position(g);
    if(g->active&&(double)g->sample+1e-9>=g->until) {cancel(g);f->flags|=g->pending;g->pending=0;}
    if(g->config.enabled&&g->playing&&now+1e-12>=g->next) {
        uint64_t n=g->opportunity++;f->opportunity=n;f->flags|=G_OPPORTUNITY;
        double interval=g->config.beat_sync?g->config.distance:g->config.distance*g->rate/1000;
        if(g->config.jitter>0)interval*=1+g->config.jitter*(2*random_f(g,n,1)-1);
        /* Absolute phase accumulation; no sample-rounded repeated intervals. */
        g->next+=interval;
        unsigned slot=(unsigned)((n+g->config.rotation)%16);
        f->eligible=(slot*g->config.density)%16<g->config.density;
        f->accepted=f->eligible&&!g->active&&(double)g->sample+1e-9>=g->rest_until&&
          g->config.probability>0&&(g->config.probability>=1||random_f(g,n,0)<g->config.probability);
        if(f->accepted)start(g,f,n,interval);
    }
    if(g->capture_manual) {f->flags|=G_CAPTURE_PULSE|G_CAPTURE_MANUAL;g->capture_manual=0;}
    f->effective=g->manual;
    if(g->active) {
        for(unsigned d=0;d<2;++d) {
            float next=g->value[d]+g->increment[d];
            g->value[d]=g->increment[d]>=0?fminf(next,g->target[d]):fmaxf(next,g->target[d]);
            if((g->destinations&(1u<<d))&&!(g->overrides&(1u<<d))) {
                if(d==G_LENGTH) {
                    f->effective.ms=g->value[d];
                } else f->effective.fracture=g->value[d];
            }
        }
        if(!(g->overrides&G_GATE_OVERRIDE))f->effective.gate=1;
        if(g->freeze&&!(g->overrides&(1u<<G_FREEZE)))f->effective.freeze=1;
    }
    f->active=g->active;f->automatic_freeze=g->active&&g->freeze&&!(g->overrides&(1u<<G_FREEZE));
    f->generation=g->generation;
    ++g->sample;if(g->playing)g->beat+=g->beat_step;
}
