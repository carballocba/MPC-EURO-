/* SPDX-License-Identifier: GPL-3.0-only -- original MPC-EURO stereo engine. */
#pragma once
#include <stdint.h>
#ifdef GHOST_BUFFER_ENGINE
#define E_CAPACITY 768000u
#define E_BANKS 4
#else
#define E_BANKS 2
#define E_CAPACITY 192000u /* two seconds at the supported maximum 96 kHz */
#endif
#define E_STATES 8
#define E_FIELDS 10
/* Scene: ms-normalized, position, bend, break, corrupt, reverse, probability,
 * duration-grid, enabled, pitch. Parameter/state communication lives in plugin. */
typedef struct { float v[E_FIELDS]; } EScene;
typedef struct {
    float ms, position, buffer_ms, bend, pitch, fracture, corrupt, chance, density, mutation;
    unsigned grid, time_grid, quantized, reverse, freeze, gate, run, random, state_div, seed;
} EConfig;
typedef struct { int bank; unsigned start,length; double phase; } EVoice;
typedef struct {
    unsigned write[E_BANKS],count[E_BANKS],live,cap_start,cap_count,capacity,fade,fade_left;
    int captured,playing,step,scene_on,cycle_allowed;
    EVoice voice,old;
    float rate,last[2],held[2],effective_ms,speed,cycle_rate;
    unsigned cycle_reverse;
    unsigned rng,cycle,hold_left,overrides;
    float mutation_offset[3];
    double beat,next_beat;
    EConfig base,effective;
#ifdef GHOST_BUFFER_ENGINE
    int held_bank,record_bank;unsigned held_start,held_count,record_count,record_limit,configured_limit;
    unsigned recording,full,source_held,repeat,clean,initialized,suspended;
    uint64_t total[E_BANKS],voice_origin;float fade_from[2];
#endif
} ERuntime;
typedef struct { float ring[E_BANKS][2][E_CAPACITY]; EScene scene[E_STATES]; ERuntime r; } Engine;
void engine_reset(Engine *,float rate,unsigned seed);
int engine_capture(Engine *);
void engine_control(Engine *,const EConfig *);
void engine_select(Engine *,unsigned state);
void engine_tick(Engine *,float l,float r,float tempo,float *wl,float *wr);
float engine_division(unsigned index);

#ifdef GHOST_BUFFER_ENGINE
void ghost_buffer_record(Engine *,unsigned);
void ghost_buffer_limit(Engine *,float);
void ghost_buffer_clean(Engine *);
void ghost_buffer_rearm(Engine *);
#endif
