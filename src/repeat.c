/* SPDX-License-Identifier: GPL-3.0-only
 * Derived from schollz/_core/lib/beatrepeat.h at 66ee010f...;
 * Copyright 2023-2025 Zack Scholl; modifications 2026 MPC-EURO contributors.
 * Widened/rate-aware indices, age-validated crossings, defined integer fades.
 * The original capture/freeze, crossing selection and linear fades are retained. */
#include "repeat.h"

void br_reset(Repeat *s, uint32_t capacity, uint32_t fade) {
    /* O(1) invalidation: only newly recorded positions/crossings can be read. */
    s->capacity = capacity; s->fade = fade;
    s->write = s->clock = s->crossing_write = s->crossing_count = 0;
    s->start = s->end = s->read = 0; s->active = 0; s->last = 0;
    s->fade_in = s->fade_out = fade; s->capture_fade = fade;
}
int br_start(Repeat *s, uint32_t requested) {
    if (s->crossing_count < 2 || requested == 0 || requested >= s->capacity) return 0;
    uint32_t newest = (s->crossing_write + BR_CROSSINGS - 1) % BR_CROSSINGS;
    if (s->clock - s->stamps[newest] >= s->capacity) return 0;
    uint32_t end = s->crossings[newest], start = end;
    for (uint32_t j = 1; j < s->crossing_count; ++j) {
        uint32_t k = (newest + BR_CROSSINGS - j) % BR_CROSSINGS;
        if (s->clock - s->stamps[k] >= s->capacity) break;
        uint32_t span = (end + s->capacity - s->crossings[k]) % s->capacity;
        if (span) start = s->crossings[k];
        if (span > requested) break; /* original first span exceeding request */
    }
    if (start == end) return 0;
    s->start = start; s->end = end; s->read = start;
    s->fade_in = 0; s->fade_out = s->fade; s->active = 1;
    return 1;
}
void br_release(Repeat *s) {
    /* Do not continually restart the fade on repeated OFF control updates. */
    if (s->active && s->fade_out == s->fade) {
        s->fade_in = s->fade; s->fade_out = 0;
    }
}
static int16_t blend(int16_t dry, int16_t wet, uint32_t dry_weight) {
    /* Q16 conversion via multiplication avoids the original negative shift UB.
     * Floor division matches the original arithmetic right shift on Linux. */
    int64_t x = (int64_t)dry_weight * dry + (int64_t)(65536u - dry_weight) * wet;
    int64_t q = x >= 0 ? x / 65536 : -((-x + 65535) / 65536);
    return (int16_t)q; /* convex mix stays in int16 range */
}
int16_t br_sample(Repeat *s, int16_t input) {
    if (s->active) {
        int16_t wet = s->ring[s->read], result = wet;
        if (s->fade_in < s->fade) {
            uint32_t w = (uint32_t)((uint64_t)65536 * (s->fade - 1 - s->fade_in) / (s->fade - 1));
            result = blend(input, wet, w); ++s->fade_in;
        } else if (s->fade_out < s->fade) {
            uint32_t w = 65536u - (uint32_t)((uint64_t)65536 * (s->fade - 1 - s->fade_out) / (s->fade - 1));
            result = blend(input, wet, w);
            if (++s->fade_out == s->fade) { s->active = 0; s->capture_fade = 0; }
        }
        if (++s->read == s->end) s->read = s->start;
        else if (s->read >= s->capacity) s->read = 0;
        return result;
    }
    /* A frozen ring resumes at an arbitrary incoming phase. Splice new
     * recording from the last recorded sample over one core fade, preventing
     * that seam from becoming a click on the next trigger. Dry output is exact. */
    int16_t captured = input;
    if (s->capture_fade < s->fade) {
        uint32_t w = (uint32_t)((uint64_t)65536 * (s->fade - 1 - s->capture_fade) / (s->fade - 1));
        captured = blend(s->last, input, w); ++s->capture_fade;
    }
    /* Expire a completely old crossing set during capture, before the 32-bit
     * sample clock can wrap and make ancient stamps look fresh again. O(1). */
    if (s->crossing_count && s->clock - s->stamps[(s->crossing_write + BR_CROSSINGS - 1) % BR_CROSSINGS] >= s->capacity)
        s->crossing_count = 0;
    if (s->last < 0 && captured >= 0) {
        s->crossings[s->crossing_write] = s->write;
        s->stamps[s->crossing_write] = s->clock;
        s->crossing_write = (s->crossing_write + 1) % BR_CROSSINGS;
        if (s->crossing_count < BR_CROSSINGS) ++s->crossing_count;
    }
    s->ring[s->write] = captured;
    s->write = (s->write + 1) % s->capacity;
    ++s->clock; s->last = captured;
    return input;
}
