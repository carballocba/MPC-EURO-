# Validation record

Validated in this Linux x86_64 cloud workspace on 14 October 2026. These are **native and cross-build findings**, not MPC compatibility results.

## Linux DSP / VST2

`make test`: **12 native case groups pass**, zero prohibited audio-callback calls observed, plus actual shared-library loading/metadata/control/stereo processing through a ctypes VST2 host.

| Coverage | Verified result |
| --- | --- |
| Original DSP oracle | Representative capture/first repeat/release is bit-exact against the pinned original at 44.1k/128, with initialized allocator and defined arithmetic helpers. |
| Core bounds | Empty history, crossing cursor wrap, expired/DC crossings, sample-clock wrap, int16 extremes and widened 96k ring indices pass. |
| Silence / impulses | Finite silence; no manufactured repeat without crossings; exact stereo dry impulse response. |
| Repeated switching | Audible repeat verified rather than dry-only output; repeated latch/Punch/cancel/release paths pass. A 100Hz, 0.2-amplitude waveform test bounds adjacent-sample changes below 0.025 across repeated gate switching. This is not a guarantee of artifact-free output for every signal. |
| Mix / stereo | Exact float stereo dry/settled mix=0; active settled mix=1 yields identical centered wet L/R; release returns to exact stereo dry. |
| Gain / bypass | −24/+12dB endpoints; smoothing bounds on constant input; settled plugin bypass gives unity dry. |
| Automation | Concurrent parameter writes while processing 640,000 samples; finite output; independent instances. |
| Invalid input / negotiation | Out-of-range/NaN/Inf parameters, read-only/out-of-range IDs, nonfinite audio; 16/32/44.1/48/96k and 1/64/127/128/129/256/4096 frames; invalid-rate unity dry with RATE!. |
| Project state | EBR1 scalar restore; transient gates/history cleared; every chunk byte corruption rejected; semantic invalid floats/transient payloads rejected even with correct checksum; bad sizes/null rejected. |
| Lifecycle / host boundary | 40 repeated create/open/process/close cycles; in-place/null buffers, suspend, zero frames; Punch timer/GUI notifications and independent histories. |
| Realtime instrumentation | Armed linker-wrap guard checks malloc/calloc/realloc/free, mutex lock/trylock/unlock, join, open/fopen/read/write and mock host callbacks while inside processReplacing: **0 violations**. |

`make sanitize`: the same 12 groups pass with **AddressSanitizer + UndefinedBehaviorSanitizer**, leak detection enabled, halt-on-error, no reported findings. Concurrent automation is exercised; ThreadSanitizer and an ARM runtime sanitizer have not been run. The guard covers the listed symbols in the exercised native path; bounded call-tree inspection complements it and it is not an OS-level proof against every possible libc/host behavior.

## Functional native GUI

`make skin`: community bounds/overlap checks and **8 GUI check groups pass**: geometry, touch actions, image integrity, eight real parameter bindings, six Q-Link mappings, read-only status, host metadata and parameter actions against the actual native library. Knobs, enum segments and Punch use actual native actions, not an image mockup. The 1280×800 preview is generated from exported assets, approximating host-drawn initial text; device fonts/rendering can differ.

On-device touch, Q-Link bank navigation, host overlays, notification-thread acceptance, read-only live redraw and host project consumption of chunks remain unverified.

## ARMv7 artifact

`make arm`: successful hash-pinned Zig 0.13.0 cross-build and static validation.

| Check | Result |
| --- | --- |
| ELF | ELF32, little endian, ARMv7-A, EABI5 hard float, shared object |
| Code generation | Cortex-A9 / VFPv3 / NEON; intended original MPC One ARMv7 userspace, target CPU features not queried on device |
| Float calling convention | Both source objects have VFP-register ABI attributes; linked ELF has hard-float flag. Zig's merged runtime omits final VFP-args tag; this fact is retained in validation output. |
| Entry point | Exactly one defined dynamic export: VSTPluginMain |
| Dynamic dependencies | libm.so.6, libpthread.so.0, libc.so.6; no libatomic, C++/JUCE or private host library |
| Symbol floor | Highest actual required glibc symbol version 2.27; chosen cross-target ceiling 2.31 |
| Binary size | 12,852 bytes, stripped |
| SHA256 | `8cfbcc08935cb2f57208e57d8ff81c8a7d4259e4af93b99c6233302800139104` |
| Execution | No QEMU, ARM hardware or Hakai runtime execution |

The cloud host could not execute an ARM Docker container (exec format error), so the successful build uses an open-source cross compiler directly. Static architecture/symbol checks do not establish loader, CPU deadline or host GUI compatibility.

## Package / reproducibility

`make package` builds the independent native-skin/ARM package with manifest, inspect-only metadata entry, notices/checksums, documentation and matching source ZIP. The archive test verifies checksums, safe/isolated paths, correct identity/classification, exact ARM binary and corresponding source. Fixed ZIP timestamps/order/modes permit repeatability; no installer runs. A clean rebuild from the matching-source archive reproduced the ARM/native libraries and every exported skin file byte for byte. Repeated package generation with unchanged source/check-out metadata was also byte-identical. Logs and fingerprints are retained under build/validation; copied native/sanitizer/skin/ARM logs and ELF inspection are in docs/validation.

## Acceptance boundary

All required Linux tests, GUI export checks and ARM static checks pass. The proof is ready for **a separately approved controlled MPC trial after host/runtime/license review**. It is not verified for Hakai 3.9.1, suitable for an untested live show, or approved for binary release. See HARDWARE_TEST_PLAN.md for exact remaining checks. No MPC was accessed and no existing plugins, MPC.settings, research branches/PRs or other repositories were modified.
