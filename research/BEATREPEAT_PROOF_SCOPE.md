# BeatRepeat ARMv7 proof — approved scope

Target: original Akai MPC One, Hakai 3.9.1, ARMv7/armhf. This branch is separate from the Phase 1 and Phase 2 research PRs and does not change existing plugins or `main`.

## Goal

Build a minimal, auditable, SDK-free VST2 effect around the GPLv3 BeatRepeat DSP from `schollz/_core` (pin `66ee010f822c915adb893c8c03279e30a52bd839`, inspect `lib/beatrepeat.h`). Verify native behavior and cross-compile an ARMv7 artifact **without installing or accessing the MPC**. No assertion of device compatibility until separate approved hardware tests.

## Implementation gates

1. Review the pinned DSP and its dependency/license closure. Preserve copyright notices, GPLv3 terms and corresponding source/build scripts. Do not use proprietary VST2 SDK files or branded assets. Review final distribution rights separately.
2. Reuse the pinned community SDK-free VST2 ABI/wrapper only after auditing the actual interfaces and any locking in the audio path. Do not change Delay, Granular Freezer, PD-LAB, PR #1, PR #2 or default branch.
3. Implement deterministic mono wet BeatRepeat processing with documented stereo dry/wet mapping, rate-aware buffer sizing (44.1 kHz target), parameter smoothing and safe gate/length/mix/gain controls. Do not promise true stereo wet processing.
4. Keep the realtime callback free from allocation, file I/O, mutex locking and blocking waits; initialize buffers outside render, bound all loops and check errors. Handle invalid host sample rates, transport changes and bypass safely.
5. Save and restore versioned scalar parameters; document that captured audio/history and transient gates are not preserved. Validate malformed state and parameter ranges.
6. Add Linux native DSP/wrapper tests (silence, impulses, repeated toggles, stereo dry integrity, automation, recall, sanitizer runs) and reproducible ARMv7 cross-build plus ELF/ABI/dependency inspection. Report any unverified conditions honestly.
7. Only after passing tests, commit code and open a **draft PR** targeting `main`, including exact commit, test commands/results, license notes and remaining physical-device checks.

## Safety boundary

No MPC access, installer execution, `MPC.settings` edits, host registration, physical-device claims, merge or public release. Stop and report any unresolved licensing, build or realtime safety issue rather than bypassing it.

## Current status

DSP adaptation, SDK-free wrapper, functional native skin/Q-Links, native/sanitizer tests and ARMv7 cross-build are completed for an experimental proof. See [validation](../docs/VALIDATION.md) and [hardware test plan](../docs/HARDWARE_TEST_PLAN.md). Device compatibility and final binary-distribution review remain open; no MPC installation or release has occurred. The implementation is submitted for draft-PR review.
