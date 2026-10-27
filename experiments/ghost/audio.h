/* SPDX-License-Identifier: GPL-3.0-only. Offline adapter, not a VST wrapper. */
#pragma once
#include "ghost.h"
typedef struct {
    uint64_t sample,opportunity,generation;
    unsigned flags,active,freeze,capture_result,captured_frames;
    float length_ms,fracture;
} GTrace;
typedef struct {
    Ghost ghost;
    Engine engine;
    float mix,target_mix,depth,release[2],depth_step,mix_step;
    uint64_t pending_generation,trace_dropped;
    unsigned pending_capture,pending_manual;
} GAudio;
/* Caller allocates storage before render. No runtime heap or thread activity. */
int ghost_audio_init(GAudio *,double sample_rate);
int ghost_audio_mix(GAudio *,float normalized);
unsigned ghost_audio_process(GAudio *,const float *left,const float *right,float *out_left,float *out_right,
                            unsigned frames,GTrace *trace,unsigned trace_capacity);
