/* SPDX-License-Identifier: GPL-3.0-only. Engine source remains unchanged. */
#include "audio.h"
#include <math.h>
#include <string.h>
static float clean(float x) {return isfinite(x)?(fabsf(x)<1e-30f?0:x):0;}
static float approach(float x,float y,float step) {return x<y?fminf(x+step,y):fmaxf(x-step,y);}
int ghost_audio_init(GAudio *a,double rate) {
    if(!a||!isfinite(rate)||rate<16000||rate>96000)return 0;
    memset(a,0,sizeof(*a));if(!ghost_init(&a->ghost,rate))return 0;
    engine_reset(&a->engine,(float)rate,1);a->mix=a->target_mix=1;a->depth_step=1.f/((float)rate*.005f);a->mix_step=1.f/((float)rate*.002f);return 1;
}
int ghost_audio_mix(GAudio *a,float x) {if(!isfinite(x)||x<0||x>1)return 0;a->target_mix=x;return 1;}
unsigned ghost_audio_process(GAudio *a,const float *l,const float *r,float *ol,float *or,unsigned frames,GTrace *trace,unsigned capacity) {
    unsigned written=0;
    for(unsigned k=0;k<frames;++k) {
        GFrame f;ghost_tick(&a->ghost,&f);
        unsigned captured=0;
        if(f.flags&G_CLEAN)a->pending_capture=a->pending_manual=0;
        if(f.flags&G_CAPTURE_PULSE) {
            a->pending_capture=1;a->pending_manual=(f.flags&G_CAPTURE_MANUAL)!=0;a->pending_generation=f.generation;
        }
        if(a->pending_capture&&!a->pending_manual&&(!f.active||f.generation!=a->pending_generation))a->pending_capture=0;
        /* A quantized recapture can pin both banks. Never flip again while live is audible. */
        if(a->pending_capture&&!(a->engine.r.playing&&a->engine.r.voice.bank==(int)a->engine.r.live)) {
            captured=engine_capture(&a->engine)?2:1; /* attempted vs acquired are distinct */
            a->pending_capture=a->pending_manual=0;
        }
        if(!(f.sample&31)||f.flags&(G_START|G_END|G_MANUAL|G_CLEAN|G_RECONFIGURE)||captured)
            engine_control(&a->engine,&f.effective);
        float il=clean(l?l[k]:0),ir=clean(r?r[k]:il),wl=il,wr=ir;
        engine_tick(&a->engine,il,ir,(float)a->ghost.tempo,&wl,&wr);
        if(a->engine.r.playing){a->release[0]=wl;a->release[1]=wr;}
        else if(a->depth>0){wl=a->release[0];wr=a->release[1];}
        a->depth=approach(a->depth,a->engine.r.playing?1:0,a->depth_step);
        a->mix=approach(a->mix,a->target_mix,a->mix_step);
        float wet=a->mix*a->depth;
        if(ol)ol[k]=clean(il*(1-wet)+wl*wet);
        if(or)or[k]=clean(ir*(1-wet)+wr*wet);
        if(f.flags||captured) {
            if(trace&&written<capacity)trace[written++]=(GTrace){f.sample,f.opportunity,f.generation,f.flags,f.active,f.automatic_freeze,captured,a->engine.r.cap_count,f.effective.ms,f.effective.fracture};
            else if(trace)++a->trace_dropped;
        }
    }
    return written;
}
