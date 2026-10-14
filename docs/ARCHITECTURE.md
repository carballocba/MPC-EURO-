# Architecture and realtime audit

## Source and host boundary

`src/repeat.c` adapts the pinned GPLv3 `_core/lib/beatrepeat.h`; `vendor/core/` preserves originals for audit and the test oracle. Production builds do not include the old allocation helpers or undefined signed-shift fixed-point code. The DSP has no embedded dependencies.

`src/vst2_abi.h` derives ABI declarations from the inspected MIT community wrapper. Its AEffect layout is checked at compile time (144 bytes on ARM32, 192 on x86_64). Only `VSTPluginMain` is exported. Two inputs, two outputs, one Default program, float replacing/legacy accumulating processing and program chunks are supported. No synth/editor, double precision, MIDI or host tempo features are advertised. The native skin is host-rendered, rather than a plugin-owned GUI window.

The original community wrapper locks an engine mutex during render, converts effects to/from int16, fixes its processing rate and reserves a large general-purpose state chunk. Reusing that render path would violate this proof's realtime requirements and lose exact stereo dry. We retain the community ABI and unmodified native skin tooling, while replacing that narrow render/state boundary with `src/plugin.c`. No unrelated infrastructure is rewritten.

## Audio path

1. Acquire atomic scalar targets in fixed chunks of at most 128 frames. Handle negotiated rate/reset/suspend without clearing large buffers.
2. Read/sanitize float stereo; average `0.5*L + 0.5*R`, saturate and quantize the wet input to int16.
3. Capture a rate-aware half-second mono ring while idle. Gate/Punch starts a loop from recent positive zero crossings. Capture freezes while repeating, matching the original behavior.
4. Original core entry/exit fades blend incoming mono with the loop. A resumed-recording splice prevents a phase discontinuity in frozen history from becoming a later repeat click.
5. Smooth wet depth and mix over approximately 5 ms, blend the centered mono wet with each channel's original dry, then apply smoothed output gain. Inactive unity-gain dry is bit-exact float stereo; a 100% active wet is identical L/R. No limiter is provided; positive gain needs headroom.

Length is latched on successful repeat entry. Crossing selection chooses the first span strictly exceeding the requested length, or the oldest valid span if history is shorter. The 1,000-crossing cap can shorten available history on high-frequency material. Anti-phase stereo can cancel in the mono wet input. DC/silence without two fresh crossings remains dry and displays PRIMING while a gate is requested.

Original DSP corrections: initialize `last`; use unsigned/widened rate-aware indices; allow crossing-cursor wrap; reject expired crossings; avoid negative signed shifts; make repeated OFF messages idempotent. Fade-out weights use the **complement of the original floored descending Q16 table**, preserving its one-LSB convention. The test oracle verifies representative first capture/repeat/release output exactly, using initialized original storage and defined versions of its arithmetic. Subsequent recordings deliberately differ at the splice.

## Realtime ownership and bounds

All ring, crossing, fade, smoother and playback state belongs to one audio thread per instance. Plugin creation allocates zeroed storage and starts the notifier **outside render**. Maximum ring storage is 48,000 int16 samples (96,000 bytes), plus 8,000 crossing/stamp bytes and small scalar state: roughly 105 KB per instance, excluding the notifier stack. No files or sample assets are loaded.

The render call tree is `render -> br_start/br_release/br_sample`, scalar helpers and bounded libc math/memory intrinsics. It contains no allocation/free, mutex, file access, thread creation/join, sleep or host callback. A failed history search is capped at 1,000 entries and retried at most once per 128 samples. Work is O(frames), with fixed work per frame/chunk; the host-provided frame count bounds the outer loop. Buffers are read-before-write, supporting ordinary stereo in-place operation. Null channel buffers are handled; nonfinite input samples become zero. Pathological finite inputs are kept finite at output.

Parameter exchange uses lock-free 32-bit C11 atomics, enforced at compile time on both builds; no libatomic dependency is accepted. Punch uses a bounded latest-command mailbox, rather than a queue; commands before the next chunk coalesce. Automation/control changes are observed within at most 128 processed samples (about 2.9 ms at 44.1 kHz). A single audio caller per instance and host-serialized lifecycle/dispatcher calls are required.

GUI, Q-Links and host setters share the same targets. Gate/bypass enum setters normalize to OFF/ON, other controls clamp 0..1, NaN/Inf are ignored, read-only status writes are ignored. Audio publishes Punch/Active/Status atomically. A separate notifier checks these at ≤10 Hz and calls community-used audioMasterAutomate/UpdateDisplay outside render. effClose stops and joins it outside render before freeing memory. **The host must not close/reenter lifecycle from inside the notifier callback or destroy an instance while render is running.** Whether Hakai accepts these background-thread notifications and redraws read-only handles needs hardware validation; this proof does not establish that host behavior.

## Rate, suspend, bypass and state

44.1 kHz / 128 frames is the primary target. Negotiated 16–96 kHz rates use a half-second logical ring and scale the original 128-sample fade duration. Buffers of any nonnegative negotiated size are sliced into bounded chunks; block-size dispatch accepts 1..1,048,576. Invalid rates explicitly produce unity stereo dry with RATE! status. Suspend produces unity dry, resets history/gates and reports BYPASS; resume starts new capture. Rate/state reset invalidates indices in O(1) and fades a held last wet sample back to dry. Host song transport is not consumed; transport play/stop does not itself clear a latch.

Bypass releases repeating, returns to stereo dry and unity gain smoothly. This is a plugin bypass, distinct from any immediate hard bypass imposed by the host.

State is a 48-byte little-endian EBR1 schema: magic, version 1, UID, eight normalized float slots and FNV-1a checksum. Length/Mix/Gain/Bypass are saved; all transient slots must be zero. Restore validates length, identity, checksum, finite ranges and enum values before writes, then clears gates/history. Checksums detect corruption, not malicious intent. State dispatch owns its return buffer and never touches audio storage. Concurrent scalar automation may produce a mixed-time snapshot; hosts should serialize preset loading/saving with their own automation for consistent snapshots. Actual MPC project chunk consumption remains unverified.

## GUI and packaging

`ui/params.json` is the append-only source of parameter indices for the generated C registry and native skin. `ui/layout.conf` uses the pinned community native TUI generator. `tools/build_skin.py` adds original colors, fragmentation marks and readable typesetting; no proprietary panel assets are included. Device fonts are host-provided; the open DejaVu font is used only for baked graphics/preview.

The 1280×800 screen reserves host chrome; the plugin area is 1280×628 at y=86..714. Knob filmstrips are 94×12032, within the community's observed 12288-pixel strip limit. Gate and Punch use supported toggle gestures; press/hold/mouse-up triggering and audio-synchronous LEDs are not claimed. Status bindings and conditional art are functional native components, with ≤10 Hz notification latency. Packaging keeps an independent identity/directory, metadata, notices and matching source. There is no installer or host registration operation.
