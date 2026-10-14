# Infinite Digits / schollz: DSP reuse and standalone plugins

Research: 14 October 2026. Evidence and revisions: [ECOSYSTEM_RESEARCH.md](ECOSYSTEM_RESEARCH.md). Source was inspected; no build, plugin execution or device testing was performed. Proposed product names below are working names requiring an independent identity check, not releases.

## _core is the primary code source

[schollz/_core README](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/README.md) describes Zeptocore, Zeptoboard, Ectocore and Ezeptocore in one monorepo. Zack Scholl is the principal DSP author. Ectocore is described as the discontinued Toadstool Tech collaboration; Ezeptocore as the Maneco Labs Eurorack collaboration. Don't conflate their panel/control differences or assume each device exposes identical firmware features.

**Source verified:** main.c and many lib/*.h implementations contain Pico/RP2040 hardware glue and shared state. The device uses Cortex-M0+-class code with fixed-point DSP to avoid dependence on a hardware FPU, plus PIO/I2S, SD storage, GPIO/ADC, USB/MIDI and flash persistence. These hardware components do not belong inside the Linux plugin. Fixed-point musical DSP can remain fixed point on ARMv7; converting it wholesale to float would risk changing its saturation/rounding/sound.

The README describes Zeptocore stereo 16-bit playback at 44.1 kHz, 16 effects, 16 banks × 16 sample slots, sequencing and single-cycle synthesis. At this revision it also reports granular time stretch up to 16× and an 8× triggered effect. Those are current-source features, not assurances that older hardware exports/builds behave the same.

## Existing desktop engine: reuse before extraction

Primary sources: [core_engine.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/core_engine/core_engine.h), [prepare.py](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/core_engine/prepare.py), [host.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/core_engine/host.h), [Rack guide](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/rack/README.md).

**Source verified:** the existing desktop port exposes create/destroy, controls, catalogue/resident-bank binding, clock input, single-frame stereo output, state/display access and settings update. It declares `CORE_RATE=44100` and `CORE_BLOCK=441`. Its read callback is explicitly restricted to copying resident PCM with **no I/O or allocation on the audio thread**.

prepare.py expands shared firmware headers and uses Clang declaration/reference identities to move mutable globals and static locals into each CoreEngine. A scoped thread-local pointer selects the instance only during synchronous engine calls. This is preferable to wrapping firmware globals in one singleton: multiple plugin instances must have independent state. It still needs ARMv7 generation and concurrency tests, and calls for one engine must not overlap.

The Rack code supplies worker-backed sample loading, explicit state validation, read-only imported samples and asynchronous bank transition. Its UI, Rack SDK, NanoVG/Jansson/Speex paths and branded graphics are not required for the C DSP port. Reuse the standalone engine and media reader; treat Rack Storage.cpp/State.hpp as implementation references, adapting only the needed non-Rack code.

**Upstream reported:** Rack packages for macOS, Windows and Linux x64; existing standalone/integration suites exercise rate changes, engine isolation, storage validation and effect paths. **Not verified here:** those suites' current pass status, analog equivalence, Linux ARMv7 execution, or any MPC build. The Rack guide explicitly defers MIDI. Do not advertise its VCV implementation as proof of VST MIDI support.

Generation uses Python/NumPy and Clang. The generated C includes preprocessed target libc declarations; do not generate on x86 and blindly cross-compile that output as armhf. Preserve the existing `--target`/target-toolchain mechanism and validate sysroot/atomic/TLS choices against ARMv7. Lock-free 64-bit atomics are not guaranteed on 32-bit ARM; inspect actual generated calls and avoid relying on libatomic inside the audio path.

Although the public API returns one frame at a time, the original renderer works in **441-frame blocks**. A 10 ms render burst can exceed a 2.90 ms MPC callback budget even if average CPU looks good. Measure worst callbacks and adapt buffering/latency or the upstream render granularity with fidelity tests; never call it "128-frame ready" just because a per-frame facade exists.

## Component inventory

All links below point to the inspected _core revision. Licenses use _core's GPLv3 grant unless file-level third-party terms differ. These are reusable components, not a claim that they are all safe unchanged in a realtime plugin.

| Requirement | Existing source | What to reuse / host adaptation |
| --- | --- | --- |
| Sampling / playback | [audio_callback.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/audio_callback.h), [audio_media.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/audio_media.h), [CoreEngine](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/core_engine/core_engine.h) | Use the existing desktop engine/catalogue/read boundary and card_format parser. Replace FatFs/SD operations with a bounded worker-resident bank. Don't reimplement slice playback from scratch. |
| Resampling / stretch | [array_resample.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/array_resample.h), [audio_resample.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/audio_resample.h), [realtime_stretch.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/realtime_stretch.h) | Preserve current granular primary-only playback path; characterize interpolation, pitch/time ratio and boundaries. Full sampler integration is safer than presenting the firmware stretch function as a standalone live-input effect without input-storage redesign. |
| Beat repeat / glitch | [beatrepeat.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/beatrepeat.h) | Mono int16 zero-crossing ring, trigger/release fades; highly bounded first effect. Host duration/trigger/mix adapter; explicit mono or dual-mono semantics. |
| Lo-fi manipulation | [bitcrush.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/bitcrush.h), [fuzz.py](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/fuzz.py), [saturation.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/saturation.h), [shaper.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/shaper.h) | Build-time tables rather than runtime generation; preserve original transfer functions and scaling. Combine a small audited subset into a separate lo-fi effect after proof. |
| Delay / tape motion | [tapedelay.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/tapedelay.h), [delay.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/delay.h) | Existing interpolated feedback/rate movement. Tape stop in broader sampler is playback-rate behavior, not necessarily this header. Identify actual signal path before using a "tape" product claim. |
| Chaotic / tuned effects | [comb.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/comb.h), [resonantfilter.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/resonantfilter.h), [transfer.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/transfer.h) | Fixed-point feedback/filter/waveshaping; audit overflow, setter-time clears and LUT ranges. Useful small independent effects or sampler's original FX chain. |
| Reverb | [freeverb_fp.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/freeverb_fp.h), [freeverb_fp_mono.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/freeverb_fp_mono.h) | Existing stereo/mono fixed-point Freeverb-family implementation. Preserve notice chain and initialization; not a high-priority standalone MPC reverb because good ports already exist. |
| Sequence / probability / clock | [sequencer.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/sequencer.h), [sequencehandler.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/sequencehandler.h), [clockhandling.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/clockhandling.h), [random_seeded.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/random_seeded.h) | Keep rules and seed/state, replace hardware microseconds/GPIO with sample-time/host clock. First use internal sample sequencing; separate outgoing MIDI plugin would need ALSA routing proof. |
| Wavetable / bass | [wavetableosc.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/wavetableosc.h), [wavetablesyn.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/wavetablesyn.h), [wavetablebass.h](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/wavetablebass.h) | Single-cycle oscillator, envelopes and voice management. Preallocate voices; source WaveSyn_new allocates and WaveSyn_next frees completed voices. Establish MIDI pitch/velocity mapping and table provenance. |

## Specific pitfalls that affect the first port

### Beat repeat is zero-crossing driven, not a perfect clock slicer

The source ring is 22,050 int16 samples, with 1,000 int16 crossing indices. Positive-going zero crossings are recorded while not repeating; triggering searches backward for a crossing span exceeding the requested number of samples. During repetition the history stops updating. The selected length can differ from the requested duration. Sparse crossings/DC/silence and crossing-index wrap need characterization. Trigger search is bounded by the crossing array; don't enlarge history without widening int16 indices.

`BeatRepeat_malloc` allocates and initializes buffers once but does not check its malloc result before writing through the pointer. Add a checked creation path in an approved port. Processing uses fixedpoint.h; `q16_16_int16_to_fp` left-shifts signed negative values. That is a C undefined-behavior hazard, not a proven MPC crash. Preserve bit-exact intended arithmetic with a defined operation and oracle tests. `-fwrapv` addresses signed overflow under supported compilers but is not a blanket cure for every invalid shift/cast/index.

Generated `crossfade4_128.h` can be produced from [crossfade4.py](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/crossfade4.py). Generation is future work; preserve the script, NumPy dependency/version, table hash and license provenance. Many header files contain function definitions and no complete standard-header include set; collect them in one implementation translation unit with a small platform shim, rather than including them from every adapter file.

### The tape-delay API is not finished standalone parameter design

At this revision Delay contains 10,000 int32 cells (~40 KB), smooths fractional reads and adds feedback. That is ~226.8 ms at 44.1 kHz. `Delay_setWet` and `Delay_setLength` are no-ops; `Delay_setActive(true)` clears the whole buffer. Processing is channel-specific over interleaved samples and also adds feedback to the right-channel slot. Two identical calls are not automatically a symmetric stereo effect. A truthful standalone design must choose original routing, adapter-owned wet/mix behavior and tested time bounds.

### Wavetable and sample assets

The GPL code grant does not prove every input waveform/sample/table is cleared for redistribution. Inspect wavetable_data.h and generators/input provenance, and ship only audited synthetic/authorized waves. The same restriction applies to Amen breaks, factory banks and hardware artwork. Users may prepare their own sample folders; the plugin should not bundle unlicensed demonstration samples.

## Potential standalone products

| Working concept | Reused code | Scope and host requirements | Sequence |
| --- | --- | --- | --- |
| Crossing Repeat | BeatRepeat + fixedpoint + generated fade table | Small insert effect; mono wet path, stereo dry passthrough, trigger/length/mix, optional host-sync length | **First proof**, 1–2 weeks DSP/adapter plus shared wrapper work. |
| Break-bank instrument | CoreEngine + card_format + worker resident-bank loading | Stereo sample instrument, prepared user banks, Break/Grimoire/probability controls, deterministic seed, internal sequence | Main _core follow-up, 4–8 weeks; PPQ, media/RAM and picker are key work. |
| Fixed-point patina | Bitcrush/saturation/fuzz/shaper/filter subset | Stereo routing explicitly audited; original per-effect transfers, no unnecessary sample manager or Pico SDK | 3–5 weeks suite; not a catch-all 16-effect first release. |
| Short magnetic delay | tapedelay path plus adapter mix | Explicit short range and channel mapping, smooth time/feedback; optional tempo divisions within range | 1–3 weeks; no claim of full physical tape model. |
| Single-cycle voice | WaveOsc/WaveSyn and cleared tables | MIDI input, voice pool, pitch/velocity/envelopes, small original UI | 2–4 weeks; pool/asset audit required. |
| Seeded sequence instrument | _core sequence/probability rules inside sample engine | Internal musical sequencing controlled by MPC tempo/transport | Prefer included instrument feature; postpone independent external MIDI sequencer. |

These products should have independent VST UIDs, manufacturer/name/path, parameters, state schema, package/source archive and release history. One plugin should not require another plugin or the entire device firmware tree at runtime.

## Broader ecosystem

### oooo-vst: strongest native tape-loop alternative

[README](https://github.com/schollz/oooo-vst/blob/d7e0d7dbf6841bff136c3ac6189982b0c597fa25/README.md), [Engine interface](https://github.com/schollz/oooo-vst/blob/d7e0d7dbf6841bff136c3ac6189982b0c597fa25/engine/modules/engine/include/oooo/Engine.h).

Public code contains modern C++ transport/voice/recording/filter/tape/scheduler/routing/editing modules. README describes lock-free SPSC scheduled commands and dual-head boundary crossfading. This is a better native DSP starting point than translating the old norns six-loop script. The Engine header includes std::optional, so a C++17-capable toolchain is needed; source isolation and allocations still require review.

Do not drag in live coding, WebSocket server, Lua, monome device polling or a proprietary JUCE wrapper for an initial MPC loop effect. Those are optional subsystems with separate dependencies. Cap loop count/storage; prepare/edit/export audio on workers; preserve scheduler sample offsets. The public repo expressly omits the complete commercial JUCE app. Existing desktop binaries do not give rights to redistribute that missing application.

README grants GPLv3; bundled components have separate terms (MIT, ISC-style, Boost, BSD/zlib-style and GPL norns adaptations). FVerbDSP.h carries BSD-2-Clause metadata and a generated Faust architecture section with GPL language; inspect the complete file/exception and metadata chain before choosing that reverb dependency. Omit optional FX bus if unresolved rather than asserting a root-license override. ~4–8 weeks for a limited tape port after infrastructure; full commercial-feature equivalence is much larger.

### fpfx

[Repository](https://github.com/schollz/fpfx) has fixed-point C effects and a desktop main.c, making it a useful historical comparison. No explicit project license or file-level grant was found in the inspected subset. **Do not copy its flanger/ringbuffer/other code by assuming the author's other GPL repository covers it.** Prefer _core implementations with explicit permission or seek a specific grant before reuse.

### Pikocore

[README/license](https://github.com/schollz/pikocore) establish a root MIT project and RP2040 sample-mangling workflow. The hardware build uses generated sample data and a documented max ~31 kHz rate. Extraction must separate GPIO/PIO/audio/timer logic and decide whether to preserve that lo-fi rate with resampling to 44.1 kHz. Whole-project embedded build commands are not the desired VST build. Good alternative if permissive source licensing is prioritized, but less already-separated than CoreEngine.

### Graintopia, oooooo and amenbreak

[Graintopia](https://github.com/schollz/graintopia) is MIT Lua/SuperCollider/norns code; its three lands × six grains and coupled-motion modulation are distinctive, but not an inspected native C engine. Embedding SC or reimplementing UGens would expand CPU/runtime/licensing scope. The README links standalone Ube and fverb, which are leads, not audited MPC ports.

[oooooo](https://github.com/schollz/oooooo) is MIT norns performance logic built around softcut. Reuse concepts or specific licensed control rules only with norns/softcut dependency rights accounted for; prefer the current oooo engine for native looping.

[amenbreak](https://github.com/schollz/amenbreak) is MIT control/engine script with sample-library dependencies. It reports loading over 200 breaks from Internet Archive. A website/archive download or MIT script license does not clear recording/composition rights. Do not bundle its sample bank in this project.

Further search leads—barcode, ouroboros-norns, zxcvbn, mx.samples, o-o-o, thirtythree and the JACK desktop looper oooooooo—are linked in the ecosystem report. Their complete licenses/dependencies were not audited; no implementation recommendation depends on unverified reuse rights.

## Licensing and naming

_core desktop adapter is explicitly GPL-3.0-only. Preserve matching source, generated-source inputs, changed-file notices and all retained dependency notices. PCG is Apache-2.0; code architecture/data bindings do not make hardware CC-BY-SA artwork reusable as unrestricted software assets. Use a file-level bill of materials for the actual compiled subset, not the full monorepo license summary.

_core README states Infinite Digits and Ectocore are registered marks and asks that derivatives not use those names. Use original working product/vendor names, with factual attribution in documentation and original graphics. The branded upstream Rack panels are not safe default MPC skins. Whether another device/project name can appear in a plugin title needs its own naming review.

MPC VST2 distribution also needs independent ABI provenance and host-linkage/SDK review; GPL permission for the DSP alone is insufficient to certify the whole artifact. See [VST2_ARCHITECTURE.md](VST2_ARCHITECTURE.md). Licensing does **not** prevent this research phase, but must be resolved before public binaries.

## Best reuse path

Prove one small effect first. Then adapt the **existing shared CoreEngine**, media parser, storage-worker design and explicit state fields into an independent sample instrument. Avoid restarting from main.c, creating a Pico emulation runtime, copying the branded Rack panel or inventing another DSP engine. New MIDI and host transport behavior must be documented as new adapter work rather than upstream-verified behavior.
