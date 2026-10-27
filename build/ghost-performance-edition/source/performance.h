/* SPDX-License-Identifier: GPL-3.0-only. GHOST Performance policy; no audio storage or second clock. */
#pragma once
#include "c1.h"
#define PE_FIRST 131u
#define PE_CONTROLS 13u
#define PE_COUNT 17u
#define PE_PARAMS (PE_FIRST+PE_COUNT)
enum { PE_MODE,PE_GLITCH,PE_CHAOS,PE_SIZE,PE_REPEAT,PE_REVERSE,PE_CUT,PE_REST,PE_MOTION,PE_RATE,PE_DICE,PE_EDITOR,PE_PRESET,PE_ACTIVITY,PE_VARIANT,PE_LENGTH,PE_BUDGET };
typedef struct {
 float p[PE_CONTROLS];uint32_t variant;
 uint64_t generation,window,events,families[3],active_samples,elapsed_samples;
 double used[2],reserve_window,rate,origin;float length,nominal,motion,pitch_offset,wet_gain,planned_ms;
 unsigned modern,mod_tail;float evolution_position;EConfig mod_config;
 unsigned active,active_family,was_mode,dice_high,dirty,stopped,was_playing;float effective_budget;
} Performance;
void pe_init(Performance *,unsigned);
int pe_valid(const float *,uint32_t);
void pe_set(Performance *,unsigned,float);
void pe_clean(Performance *);
void pe_tick(Performance *,C1 *);
void pe_config(Performance *,C1 *,EConfig *);
float pe_read(const Performance *,unsigned);
uint32_t pe_checksum(const unsigned char *,size_t);

float c1_modulate(C1 *,const GFrame *,unsigned,EConfig *);
