/* SPDX-License-Identifier: GPL-3.0-only. Offline original GHOST prototype. */
#pragma once
#include <stdint.h>
#include "engine.h"
enum { G_LENGTH, G_BREAK, G_CAPTURE, G_FREEZE, G_DESTINATIONS };
enum { G_START=1, G_END=2, G_CAPTURE_PULSE=4, G_MANUAL=8, G_CLEAN=16, G_RECONFIGURE=32, G_CAPTURE_MANUAL=64, G_OPPORTUNITY=128 };
enum { G_GATE_OVERRIDE=1u<<4 };
typedef struct {
    unsigned enabled, interval; /* destination opportunity divider, 1..64 */
    float probability, minimum, maximum, depth, smooth_ms;
} GDestination;
typedef struct {
    unsigned enabled, beat_sync, density, rotation, seed;
    double distance; /* beats if beat_sync, otherwise milliseconds */
    float probability, duration_ms, rest_ms, jitter, capture_cooldown_ms;
    GDestination destination[G_DESTINATIONS];
} GConfig;
typedef struct {
    EConfig effective;
    uint64_t sample, opportunity, generation;
    unsigned flags, active, automatic_freeze, eligible, accepted;
} GFrame;
typedef struct {
    GConfig config;
    EConfig manual;
    double rate, tempo, beat_step, beat, next, until, rest_until;
    uint64_t sample, opportunity, generation, last_capture;
    float target[2], value[2], increment[2];
    unsigned active, freeze, overrides, destinations, pending, capture_manual;
    unsigned playing, fallback, have_capture;
} Ghost;
GConfig ghost_defaults(void);
EConfig ghost_manual_defaults(void);
int ghost_init(Ghost *, double sample_rate);
/* All mutators are single-owner, called by the offline harness/audio owner. */
int ghost_configure(Ghost *, const GConfig *); /* all-or-nothing validation */
int ghost_manual(Ghost *, const EConfig *, unsigned override_mask);
void ghost_release_override(Ghost *, unsigned mask);
void ghost_capture(Ghost *);
void ghost_clean(Ghost *); /* highest priority; no buffer erasure */
void ghost_reset(Ghost *); /* replay seed/counter from current clock position */
int ghost_clock(Ghost *, double tempo, unsigned playing, unsigned seek, double ppq);
void ghost_tick(Ghost *, GFrame *); /* bounded, allocation/I/O/lock-free */
uint32_t ghost_random(unsigned seed, uint64_t opportunity, unsigned domain);
