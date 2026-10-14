# First port: a small _core zero-crossing beat-repeat effect

Recommendation date: 14 October 2026. **Status: research and design complete; implementation has not begun and requires the project owner's approval.** This recommendation does not authorize physical-MPC installation, settings changes, overwriting plugins or merging PRs.

## Decision and three best opportunities

1. **_core BeatRepeat component:** best first host-integration proof. Licensed, small, separable C DSP; no sample manager, SD reader or large persistent loop media. Working concept name: *Crossing Repeat*, requiring an independent product-name check.
2. **Repetita/Wreath:** best substantive Versio stereo live-looper port. MIT source and separated engine; buffer ownership, large clears and captured-media recall are the main work.
3. **_core shared desktop sample engine:** best larger sampling/glitch instrument. Reuse the existing CoreEngine and VCV desktop boundary rather than extracting hardware main.c. Main blockers are bank memory, 441-frame render bursts, sample selection, new MIDI mappings and project media.

Capicola is the strongest additional granular/time-stretch candidate with a ready portable layer; Smack is a strong seeded glitch/capture candidate. Both belong after a validated shared-host foundation. Plateau already has an MPC port (PlateauXXL), and Mutable ports already exist; use them as references instead of repeating them.

## Why this first

Primary source: [beatrepeat.h at _core 10b4bf7…](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/beatrepeat.h), with [fixedpoint.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/fixedpoint.h), [crossfade4.py](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/crossfade4.py) and [existing component audition](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/test/beatrepeat/main.c).

**Source verified:** BeatRepeat owns a 22,050-sample int16 ring and 1,000 crossing indices. It has allocate/process/repeat/free functions, does not access GPIO or files, and allocates only at creation. Core state is roughly 46.1 KB mono plus scalars and fade table. The repeated segment is chosen from zero crossings; history freezes while repeating. This makes a useful glitch effect with little integration machinery.

It is a component port, not a faithful Ectocore/Zeptocore device emulation. Keeping that distinction makes the first deliverable honest and small. It proves independent identity, effect audio, parameters/Q-Links, state, ARM build, packaging and source-distribution plumbing. It avoids CRCLTR's missing permission, Gen runtime restrictions, Wreath's ~61 MB shared buffers and _core sampler storage/render concerns.

Licensing is GPLv3; proposed combined plugin GPL-3.0-only with MIT wrapper notices retained. Use original names/graphics; the _core README prohibits Infinite Digits/Ectocore names on derivatives. The VST2 ABI/host legal gate remains before public binary release, even though source-level DSP permission is present.

This is not already a working MPC plugin: no code has been adapted, compiled or tested here. Its expected low CPU is an inference from bounded processing, not a measured promise.

## Bounded first-plugin behavior

**Two host inputs and two outputs, mono processed wet path, stereo float dry path.** Downmix source to `(L+R)/2` before int16 conversion and BeatRepeat; center its wet output into L/R, then mix with untouched stereo dry. Explain that wet collapses the image and opposite-phase stereo can cancel in the mono feed. Do not call it stereo-linked repetition. Independent L/R BeatRepeat instances are a possible later dual-mono mode but may choose different boundaries; a truly linked-stereo detector requires an explicitly tested DSP extension.

Initial parameter design, indices finalized only after auditing the wrapper's parameter-0 restore behavior:

| Control | Proposed behavior | Save / automation |
| --- | --- | --- |
| Mix | 0–100%; simple bounded crossfade, initially dry | Saved, automatable, smoothed |
| Length | 5–450 ms requested crossing span | Saved, automatable; repeat length is approximate and depends on crossings |
| Repeat gate | Press/hold enables selected repeat; release calls source repeat(..., 0) | Momentary, not restored held; gate automation requires tested edges |
| Bypass | Dry output; release active repeat; history may stay primed | Saved; click-free transition |
| Input trim | Bounded gain for wet feed, with clear clipping behavior | Saved, smoothed; no alteration of dry bypass |
| Output trim | Bounded final gain | Saved, smoothed |
| Sync / division | Optional second milestone, host-tempo duration within available history | Saved; free-ms fallback if host timing unavailable; out-of-range indication |
| Status | Idle / primed / repeating / unsupported length / failure | Read-only snapshot, not host automation |

450 ms leaves margin below the 500 ms ring; tests must establish the actual valid range and behavior at sparse crossings. This is not proof of a mathematical guarantee for every input. Preserve source-selected spans rather than labeling the control as exact quantized slicing.

Minimum proof uses parameter gates, so it does not depend on unverified MIDI-to-effect routing. Optional note-on/off and CC gates can be added after host event tests, with note-off/all-notes-off guaranteed. No MIDI output, CV/Gate access, sample import, captured-media export, network service or fancy live waveform UI in the initial scope.

Project/preset recall saves scalar controls and schema version. Live ring contents and held repeat are **transient and reset on restore**. This is intentional documented effect state, not a promise to preserve recorded audio. Preset/project restore must never re-trigger a held gate or start recording.

## Implementation plan, only after approval

### Phase A — provenance, architecture and independent identity

- Pin _core `10b4bf7d8c0da43098ac64bbde96cdb06fa02905` and MPC kit `4a8a25fb6fd41d51c9a4eaa4aeb7338df4070042`; keep imported source plus license/change ledger in this project. Audit only required dependency closure rather than copying the whole firmware repo.
- Choose original vendor/product/UID, append-only parameter registry, package ID and separate content directory. Check collisions in the community catalog and on the intended target later; never reuse another plugin identity.
- Adopt existing SDK-free MIT ABI/build/skin/test/package code with attribution. Design a bounded audio-owned parameter/state handoff; **don't use its current audio-path mutex unchanged**.
- Review independent ABI provenance, GPL notices and host-linkage/distribution issues. Source-only development can proceed within applicable grants; no public binary release until the release gate is resolved.

Acceptance: approved source bill of materials, exact dependency pins and independent identity; no proprietary SDK, unexplained source file or branded copied skin.

### Phase B — preserve and harden the small DSP

- Place needed header implementations in one C translation unit with standard headers and a shim for `__not_in_flash_func`. Generate the 128-sample crossfade table with the existing generator; preserve inputs/hash/tool versions in reproducible build metadata.
- Allocate/check/zero BeatRepeat at creation, with safe failure handling. The source allocator dereferences malloc without checking; adapt that rather than assuming allocation always succeeds.
- Resolve signed-negative left shifts in fixedpoint.h and any overflow/narrowing/index hazards using defined bit-equivalent arithmetic. Don't claim `-fwrapv` cures everything. Keep the original source reference and mark targeted modifications.
- Keep the source's ring size and mono algorithm; use a preallocated scratch span and sample conversion. No per-callback allocation/free, disk/logging or locks. Bound commands and validate repeat lengths against actual history.
- Define how edits to Length while held take effect (e.g. next gate), release/reset/bypass behavior and repeated press semantics; document them and test them.

Acceptance: sample/state equivalence to the intended reference under normal valid inputs; deliberate, documented corrections for undefined/error cases. No generic DSP rewrite or unexplained sonic changes.

### Phase C — host adapter, UI and state

- Float processReplacing handles arbitrary tested frame counts with small slices; internal fixed table controls fade duration, not host allocation. True bypass preserves float stereo audio without quantizing it.
- Convert normalized host parameters into bounded numeric targets off the DSP core; audio applies/smooths them with bounded work. Record/capture/release commands require ordered events, not a scalar race.
- Versioned compact chunk snapshots with validation, restore ordering and no held gate. Keep small parameter state independent from history buffers. Test host's immediate restore/readback sequence and the inherited parameter-0 quirk.
- Generate an original one-page skin and MPC One Q-Link banks with tested enums/buttons; no native combobox dependency or copied branded panels. Presets are a small set of useful scalar settings, not audio assets.
- Optional host-sync milestone checks tempo flags, computes requested duration and displays unavailable divisions. For example, an eighth note at 60 BPM is 500 ms and exceeds the proposed 450 ms range; don't silently claim that division works. Clamp with explicit indication or restrict choices based on tempo.

Acceptance: source effect is audible in an offline host, full dry/mix/gate behavior is correct, two instances isolate state, and parameter/chunk tests demonstrate real round-trip behavior.

### Phase D — software validation and ARM package

These are **planned checks, not executed results**:

- Use the existing BeatRepeat component audition as a behavioral fixture, but turn assumptions into assertions. Existing generic _core DSP-loop tests cover delay/filter paths and are not a substitute for BeatRepeat-specific tests.
- Deterministic positive/negative sine, impulse, noise, DC, silence, sparse crossings, full-scale and anti-phase stereo input. Verify repeat changes output, release returns to input, boundaries remain finite and sentinel buffers are intact.
- Drive ring/crossing wrap, repeated trigger/release, held Length edits, bypass/restore, empty/priming states, allocation failure, NaN/Inf parameters and malformed/oversized chunks.
- Test native ASan/UBSan and intended fixed-point semantics at multiple optimization levels; retain the original output oracle. Don't disable assertions/sanitizers to make unsafe arithmetic appear correct.
- Host block sizes including 1, 64, 127, 128, 129, 256 and a bounded larger value; null input during scanner calls, input/output aliasing where supported, repeated suspend/resume and unload.
- Multiple instances with interleaved/threaded host parameter access and state changes; prove no mutable global DSP history. Audit the audio call tree and allocation/locking instrumentation.
- Build armhf using the pinned community-compatible toolchain; inspect ELF32/ARMv7/hard-float/export/GLIBC/dependency metadata; run ARM software tests under QEMU where supported. Generate skin/layout/checksum/source package without invoking any installer.

Acceptance: meaningful tests execute and pass with reported counts; package has unique identity/path, matching source and notice files, valid skin metadata and no unmet dynamic dependency. No physical-MPC claim is made from these checks.

### Phase E — separately approved hardware qualification

First establish the exact One/Hakai host, ABI/libraries, audio rate/block behavior, content/settings location and existing installation workflow using read-only checks. Hardware access/testing is not assumed available from this research environment.

Installation is a **separate permission boundary** because the current request prohibits MPC.settings changes and plugin installation. Do not execute generated installers after merely receiving code-implementation approval. Present the exact non-conflicting package and deployment action for approval when that phase is requested.

On an approved test device: instantiate as an effect, verify stereo dry/mono wet behavior and gain, Q-Links/touch/automation, project close/reopen, multiple instances, transport fallback, optional MIDI/sync routing and long playback. Measure actual callback latency/worst CPU, RSS and stress behavior within a real project. Suggested first budget: p99 ≤15% and worst ≤50% of the ~2.90 ms block, with no allocation, lock waits, glitches or crash; these are proposed limits, not guaranteed performance.

Acceptance: a recorded test on **original MPC One + exact Hakai 3.9.1 build**, complete behavior/recall evidence, and source/license/release audit. Force-only results should be published as Force-only results. Do not overwrite existing plugins to satisfy the test.

## Effort and stop conditions

Estimated initial source/adapter/skin work: **1–2 engineer-weeks**, plus **1–3 weeks shared wrapper/build/realtime work** where required. Hardware qualification and release legal review are additional calendar dependencies. A simpler offline-only proof may finish sooner; it is not a qualified MPC release.

Stop/reconsider before binaries if independent VST2 distribution/host terms cannot be resolved. Stop before hardware if no separately approved device/install path exists. If BeatRepeat cannot pass defined-arithmetic/reference tests without major DSP changes, reassess the scope; Wreath is the next permissively licensed candidate but needs substantially more memory/realtime work. If the MPC cannot provide effect parameters/skin/state as expected, investigate host registration first rather than rewriting DSP.

## Major blockers across the project

- **Target evidence:** community Force/MPC results are useful, but exact Hakai 3.9.1 One compatibility is not verified here.
- **Realtime host kit:** mutexes, string housekeeping, fixed-rate handling and 16-bit effect conversions need careful adaptation.
- **Licenses:** missing grants for CRCLTR/Tapeo/fpfx, Triwalkma's restricted runtime, binary-only Archivist/official NE DSP, GPL/AGPL source obligations, trademarks and VST2/host release review.
- **Later engines:** global large buffers, expensive clear/voice lifecycle operations, 441-frame bursts, bank/media memory and reliable recorded-audio recall.
- **Routing:** ordinary VST MIDI output is reportedly ignored; physical CV access and effect MIDI routing are unverified optional extensions.

The next action is project-owner review and approval of the first-port scope. Until then this repository contains research documents only.
