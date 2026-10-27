/* SPDX-License-Identifier: GPL-3.0-only. Original isolated GHOST C1. */
#pragma once
#include <stddef.h>
#include "../ghost/audio.h"
#define C1_DESTS 12
#define C1_SOURCES 8
#define C1_STATE_FLOATS 296
/* First four destination IDs are deliberately identical to C0. */
enum { C1_LENGTH,C1_BREAK,C1_CAPTURE,C1_FREEZE,C1_POSITION,C1_SIZE,C1_REVERSE,C1_BEND,C1_PITCH,C1_CORRUPT,C1_MIX,C1_GATE };
enum { M_STEP,M_SMOOTH,M_WALK,M_HOLD,M_SINE,M_TRIANGLE,M_GATE,M_REPEAT };
enum { S_IDLE,S_LISTEN,S_CAPTURE,S_REPEAT,S_FREEZE,S_MOTION,S_CHAOS,S_CLEAN };
/* Public UI control IDs; same IDs used by native skin and offline live UI. */
enum { P_GHOST,P_GATE,P_LENGTH,P_BREAK,P_MIX,P_MOTION,P_CHAOS,P_CLEAN,P_BUFFER,P_BUFFER_DICE,P_MOTION_DICE,
 P_DEST,P_RANDOM,P_MIN,P_MAX,P_DEPTH,P_PROB,P_INTERVAL,P_LOCK,P_TYPE,P_RATE,P_MDEPTH,P_MMIN,P_MMAX,P_SYNC,P_HOLD,P_SEED,
 P_DENSITY,P_CHANCE,P_DISTANCE,P_DURATION,P_REST,P_RESET,P_CAPTURE,P_FREEZE,P_POSITION,P_SIZE,P_REVERSE,P_BEND,P_PITCH,P_CORRUPT,
 P_MDEST,P_ROUTE,P_LISTEN,P_SENS,P_SPACING,P_LPROB,P_LCAP,P_LREPEAT,P_STATUS,P_ACTIVE,P_ENERGY,P_TAKE,P_CLOCK,P_TIMING,P_CHAOS_ON,P_SOURCE,P_PARAM_DICE,P_R0MIN,P_R0MAX,P_R1MIN,P_R1MAX,P_R4MIN,P_R4MAX,P_R5MIN,P_R5MAX,P_R7MIN,P_R7MAX,P_R8MIN,P_R8MAX,P_R9MIN,P_R9MAX,P_R10MIN,P_R10MAX,P_EDIT,P_COUNT };
typedef struct {unsigned type,sync,hold,seed;float rate,depth,minimum,maximum,probability;} MConfig;
typedef struct {unsigned enabled,source;float depth,minimum,maximum,probability,smooth_ms;} MRoute;
typedef struct {
 GConfig event;GDestination random[C1_DESTS];unsigned locked[C1_DESTS];
 MConfig source[C1_SOURCES];MRoute route[C1_DESTS];float manual[C1_DESTS];
 unsigned char legacy_blob[532];unsigned legacy_size;
 unsigned motion,buffer,chaos_on,listen,listen_capture,listen_repeat,quantized;
 float chaos,sensitivity,spacing,listen_probability;unsigned destination,motion_destination,source_selected;
} C1State;
typedef struct {uint64_t cycle;float value,start,target;unsigned initialized;} MRuntime;
typedef struct {
 Ghost clock;Engine *engine;unsigned render_audio;EConfig last_effective;float last_mix;unsigned capture_requested,control_dirty;C1State state;MRuntime source[C1_SOURCES];
 uint64_t origin_sample,dice_index,last_onset,lease_until,pending_until,visual_until,trace_dropped;
 double origin_beat;
 float auto_value[C1_DESTS],route_value[C1_DESTS],dice_value[C1_DESTS],motion_value[C1_SOURCES];
 float mix,depth,release[2],depth_step,mix_step,fast,slow,energy,fast_coefficient,slow_coefficient;
 unsigned random_mask,manual_mask,dice_mask,edge_mask,commands,pending_capture,pending_manual,onset_armed,status;
 unsigned edit_feedback,motion_active,active,actual_freeze,capture_acquired,onsets,accepted,selection_dirty,clean_latched;
} C1;
typedef struct {uint64_t sample;unsigned flags,status,active,capture;float length,fracture,position,mix,energy;} C1Trace;
typedef struct {const char *key,*name;float minimum,maximum,def;unsigned readonly;} C1Param;
extern const C1Param c1_params[P_COUNT];
C1State c1_defaults(void);
int c1_valid(const C1State *);
int c1_init(C1 *,double);
int c1_apply(C1 *,const C1State *); /* single audio owner, coherent validated state */
int c1_manual(C1 *,unsigned,float);
void c1_bind(C1 *,Engine *,unsigned render_audio);
typedef struct {C1 control;Engine engine;} C1Audio;
float c1_get(const C1 *,unsigned);
int c1_set(C1 *,unsigned,float); /* single owner; UI server serializes calls */
unsigned c1_commit_commands(C1 *);
unsigned c1_process(C1 *,const float *,const float *,float *,float *,unsigned,C1Trace *,unsigned);
void c1_dice(C1 *,unsigned family); /* 0 selected,1 buffer,2 motion; no auto enable */
float c1_motion(C1 *,unsigned,uint64_t,double,unsigned);
size_t c1_save(const C1 *,unsigned char *,size_t);
int c1_load(C1 *,const unsigned char *,size_t);
int c1_import_c0(C1 *,const GAudio *);
/* Stable native embedding ABI for offline UI/harness, not a VST entry point. */
void *ghost_c1_create(double);
void ghost_c1_destroy(void *);
int ghost_c1_set(void *,unsigned,float);
float ghost_c1_get(const void *,unsigned);
unsigned ghost_c1_process(void *,const float *,const float *,float *,float *,unsigned,C1Trace *,unsigned);
size_t ghost_c1_save(const void *,unsigned char *,size_t);
int ghost_c1_load(void *,const unsigned char *,size_t);
