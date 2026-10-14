/* SPDX-License-Identifier: GPL-3.0-only
 * BeatRepeat adaptation: Copyright 2023-2025 Zack Scholl;
 * Copyright 2026 MPC-EURO contributors. See docs/PROVENANCE.md. */
#pragma once
#include <stdint.h>
#define BR_MAX_RING 48000u
#define BR_CROSSINGS 1000u
typedef struct {
    int16_t ring[BR_MAX_RING], last;
    uint32_t crossings[BR_CROSSINGS], stamps[BR_CROSSINGS];
    uint32_t capacity, write, clock, crossing_write, crossing_count;
    uint32_t start, end, read, fade, fade_in, fade_out, capture_fade;
    int active;
} Repeat;
void br_reset(Repeat *, uint32_t capacity, uint32_t fade);
int br_start(Repeat *, uint32_t requested);
void br_release(Repeat *);
int16_t br_sample(Repeat *, int16_t);
