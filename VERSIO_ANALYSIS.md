# Versio firmware assessment

Research: 14 October 2026. All ports would be independent MPC plugins. Evidence labels and revision ledger: [ECOSYSTEM_RESEARCH.md](ECOSYSTEM_RESEARCH.md). No firmware or plugin was compiled or run.

## Platform boundary

**Source verified:** [DaisyVersio](https://github.com/electro-smith/libDaisy/blob/08087203debc646d3710ec8caa35bac6cf20ab5e/src/daisy_versio.h) provides stereo audio, seven knobs/CV controls, two three-position switches, button/gate-style performance controls and LED feedback. [DaisyExamples/versio](https://github.com/electro-smith/DaisyExamples/tree/259ed82c7d4c0d7699f695945e6e111b7dc7cb27/versio) documents the control inventory. The inspected community firmwares use Daisy Seed / STM32H750 and an arm-none-eabi embedded build, rather than Linux/armhf.

The hardware adapter contains ADC, GPIO, audio codec/SAI, clocks, SDRAM placement and sometimes QSPI persistence. An MPC plugin instead receives audio from processReplacing, parameters from the host, MIDI from effProcessEvents, and timing from audioMasterGetTime where valid. Knob/CV values become normalized parameters plus optional internal modulation, not physical CV ports. Preserve switch/gate semantics with enums, momentary buttons and explicit trigger edges.

The seven controls are not necessarily independent "knob plus CV" software values; some hardware designs combine signals before digitization. Reproducing a firmware's response needs its actual mapping code. LEDs become lightweight status parameters/native text or static-image indicators. Firmware's single-instance global state and zeroed SDRAM assumptions must be removed or preserved explicitly on the heap.

Versio's audio sample rates and MPC's reported 44.1 kHz differ. Rescale time constants, oscillator rates, filters, fade lengths and bounds; do not simply feed 44.1 kHz frames into a hardcoded 48/32 kHz algorithm. Native Linux ARMv7 is Cortex-A application code with MMU/libc, not Cortex-M firmware binary compatibility.

## 1. CRCLTR — s3g

Sources: [README](https://github.com/s3g/crcltr/blob/f7ccd030b9d36c47a00be81fb0b5f5b567961176/README.md), [main Gen patch](https://github.com/s3g/crcltr/blob/f7ccd030b9d36c47a00be81fb0b5f5b567961176/crcltr101.gendsp).

**Source verified:** stereo dual looper made with Max → Gen → Oopsy. The repository contains .maxpat/.gendsp files and subpatches, not an inspected generated standalone C++ engine. README says Max and Oopsy are required for source use. There is no root license grant found.

Musical mapping is well specified: loop 1 uses crossfaded playback of the first half of the recording; maximum audible loop 16 seconds, requiring up to 32 seconds capture. Loop 2 plays up to 32 seconds with boundary ducking. Seven primary knobs cover two rates, crossfade mode/control, blend, input and output gain. Button/gate records while held; switches select the loop and input monitoring. Rates are 0.25–2.75×. Manual/sine/trapezoid crossfades and tanh gain coloration are existing behavior, not proposed replacements.

The Gen patch contains two `data ... samplerate*32 2` buffers. At 44.1 kHz, two 32-second stereo float buffers require ~22.58 MB; double storage would double that. Actual exported Gen data type and engine allocation must be verified. No MIDI or DAW transport adapter is present in the inspected project.

**Port plan, contingent on permission:** obtain a source license from the author; establish current Gen export/runtime licensing; use a lawful export with existing subpatches, replace Daisy/Oopsy controls with host parameters and audit buffer/state ownership. Max editing is not an existing VST port. Do not infer portability or distribution rights from a downloadable .bin.

**Decision:** blocked for this open-source project until a usable grant exists. Medium technical complexity after clearance; inappropriate first proof.

## 2. Campestria / PlateauNEVersio — digitalartifactmusic

Sources: [README](https://github.com/digitalartifactmusic/PlateauNEVersio/blob/4218b072e7420dd788cd3c98c36b3eba445f8886/README.md), [Dattorro class](https://github.com/digitalartifactmusic/PlateauNEVersio/blob/4218b072e7420dd788cd3c98c36b3eba445f8886/Dattorro.hpp), [delay implementation](https://github.com/digitalartifactmusic/PlateauNEVersio/blob/4218b072e7420dd788cd3c98c36b3eba445f8886/dsp/delays/InterpDelay.cpp), [LICENSE.md](https://github.com/digitalartifactmusic/PlateauNEVersio/blob/4218b072e7420dd788cd3c98c36b3eba445f8886/LICENSE.md).

**Source verified:** C++ reverb port derived from Dale Johnson's Valley Plateau / Jon Dattorro design; stereo tank, predelay, filters, diffusion, decay, modulation and freeze. PlateauTest.cpp combines controls, gain/scaling, clipping/limiting, LEDs and audio callback. Makefile expects external libDaisy and DaisySP. The Dattorro constructor in firmware is `(32000, 16, 4.0)`; delay/scaling must not be assumed safe at 44.1 kHz without recalculating capacity.

Important traps: `sdramData[50][144000]` is a **shared global 28.8 MB float pool**, a global buffer counter assigns slots, and clear/pop-control state is shared. Utilities.hpp pulls in Daisy headers. Defining DSY_SDRAM_BSS to nothing does not fix multi-instance isolation. README reports previous out-of-bounds bursts, startup noise and control-rate problems; these are upstream historical reports, not tests run here.

License grant is GPLv3-or-later in LICENSE.md; README's shorter GPLv3 summary is less precise. Included Signalsmith is MIT; ffft license file is WTFPL v2; LICENSE-dist.md carries BSD-3-Clause-style Rack and GPL Grids notices. Bogaudio-derived code and actual compiled dependency closure require notice tracing. The original paper's algorithm description does not erase implementation copyrights.

**Existing reuse route:** [ValleyRackFree](https://github.com/ValleyAudio/ValleyRackFree) already uses per-object desktop delay storage, and [PlateauXXL](https://github.com/sunskiefer/PlateauXXL) already ports Plateau into an MPC VST2 effect. Its tested.json records Force 3.9.1, not this Hakai One. Prefer those paths; retain Versio-specific coloration/limiter changes only if a sonic comparison shows value. PlateauXXL's NC artwork must not be copied into an unrestricted-artwork distribution.

Effect I/O is stereo in/out, MIDI optional; host-sync modulation can be added from existing MPC implementation. Needs all reverb parameters, freeze/clear and gain controls with safe smoothing. Tail buffers need not be in presets unless explicitly promised. CPU concerns: delay/filter work, double math, limiter latency and tail denormals. **Decision:** reference/reuse candidate, not a new first port.

## 3. Repetita / Wreath — hirnlego / Roberto Noris

Sources: [Repetita README](https://github.com/hirnlego/repetita-versio/blob/99b61f3f2227035671013bd11ebf607483434bee/README.md), [pinned Wreath buffer/interface](https://github.com/hirnlego/wreath/blob/1662b8ccfad339f3d306fe2868b3c039698fad6c/stereo_looper.h), [Wreath MIT license](https://github.com/hirnlego/wreath/blob/710cd8b1704d97d1cb8a06fcf2f1c82be1caf134/LICENSE).

**Source verified:** MIT C++ firmware with a Wreath submodule pinned to `1662b8c…`. Wreath's classes divide into StereoLooper, Looper and Head. Its README gives sample-rate initialization and per-sample stereo Process API, plus existing desktop tests. Initial implementation references 48 kHz/80 seconds and four global float buffers: left/right and freeze copies. Hardware and UI reside separately in Repetita.

Musical features: independent channel loop start/length/speed/record/freeze, forward/reverse varispeed, three trigger modes, feedback filter/degradation, stereo width and loop/delay/note behavior. This is a meaningful stereo performance effect beyond a generic reverb. Seven primary controls are blend, start, tone, size, decay, rate and freeze; switches choose channel and button behavior. Optional MPC note-trigger and tempo quantization are new host features.

Extraction: use exact pinned Wreath/DaisySP revisions, move buffers and shared random state per instance, replace SDRAM include/attribute with allocated storage and use only required DaisySP math/SVF components. `Init(sampleRate)` alone does not change the globally fixed sample capacity. Choose an explicit duration cap (e.g. 20 seconds initially) rather than silently inheriting ~58.6 MiB per instance. Repetita persistent hardware settings become versioned project state.

Realtime risks are concrete: StereoLooper::Process can invoke full buffer clearing/reset on a control transition; Looper initializes process-global srand(time()). Large clears must be scheduled in bounded work or use an inactive prepared buffer, and randomness must be instance-local. Existing test files are useful but were not executed here.

Project recall: scalar settings alone cannot recall captured audio. Define worker-backed, project-relative media persistence with checksums and missing-file behavior; never write from the audio callback. A first looper demo may explicitly reset media on reload, but cannot call that complete performance recall.

**Decision:** second-priority new port, ~3–5 engineer-weeks after shared infrastructure. It offers clear permissions and a useful stereo engine but requires real memory/realtime changes.

## 4. Smack Versio — Tim Cox

Sources: [README](https://github.com/timncox/smack-versio/blob/f839b2ac64f813ec00b2220eee0b41d9d170b237/README.md), [vendored engine header](https://github.com/timncox/smack-versio/blob/f839b2ac64f813ec00b2220eee0b41d9d170b237/firmware/vendor/smack_core.h), [license/provenance](https://github.com/timncox/smack-versio/blob/f839b2ac64f813ec00b2220eee0b41d9d170b237/LICENSE).

**Source verified:** MIT C engine with create/destroy, int16 stereo block processing, MIDI and string parameter API. Vendored origin is schwung-smack `169905d` with explicit local fixes; don't overwrite the divergent copy during porting. Features include live ring capture, seeded slice order, retrigger/reverse/pitch/speed/gate/crush, tape stop/start, scratch, granular freeze/pitch/scatter, filters, delays and reverb. Existing Ableton Move wrappers are real prior implementation paths, not MPC wrappers.

Versio engine hardcodes 48 kHz, 150 seconds ring capacity and a 105-sample edge fade. Its int16 ring is 28.8 MB, plus float delay/reverb lanes. Source already explains protection of playing-loop audio and a recorder-stall fix. A naive ring size reduction may recreate that failure. Host get_bpm callback, clock tick model and trigger ordering need an adapter for MPC PPQ/transport.

**Evidence conflict:** README prominently says the firmware has never run on hardware, while the current header says three fixes were found on Versio hardware. Neither is independent validation, and the sources contradict each other. Treat hardware maturity as unresolved and rely on runnable regression/fidelity tests only after implementation approval. The README's old status must not be quoted as conclusive either way.

Reuse the C engine, reconcile Move/Versio fixes, choose a runtime-rate or verified 44.1 kHz version, and examine synchronous auto-BPM analysis and expensive setters before allowing capture commands on the audio path. Preserve seed/version semantics: adding effects to a roll pool can alter old seeds' results. Recall needs capture media, not just seed/parameters.

**Decision:** strong glitch follow-on, ~2–4 weeks plus shared work and media persistence. More risk than the small beat-repeat proof.

## 5. Capicola Versio — Heavy Light Industries / Tim Cox

Sources: [original Capicola](https://github.com/heavylight-industries/capicola), [Versio README](https://github.com/timncox/capicola-versio/blob/acafccc5c22b539b6d9843496c92151d613d1537/README.md), [portable engine](https://github.com/timncox/capicola-versio/blob/acafccc5c22b539b6d9843496c92151d613d1537/core/capicola_engine.h), [AGPL license](https://github.com/timncox/capicola-versio/blob/acafccc5c22b539b6d9843496c92151d613d1537/LICENSE).

C++ transient-driven keyframe stretching/pitch shift. Unlike a generic grain cloud, a detected transient brings a lagging play head back to the present with a fade. The upstream DSP includes keyframe recorder, interpolated delay, filters/shapers and envelope/transient detector.

**Source verified:** the existing core/ port makes sample rate a parameter, chunks long host blocks, gives each desktop instance its own rings and removes Daisy includes via a platform layer. It exposes deinterleaved float and int16 interleaved processing, parameter setters and TriggerSlice. This is excellent DSP reuse; the Move and Versio layers share it. Two rings are ~48 MiB before ancillary state. Its source tests compare against unmodified upstream audio-engine code; the counts and sample equivalence are **upstream reported, not rerun here**.

Controls: stretch, pitch, threshold, grain size, quality, feedback, mix, drive, follower modulation and fade time. Stereo in/out; MIDI/clock not inherently required. Map forced splice to momentary parameter/optional MIDI and expose envelopes internally; don't claim physical MPC CV outputs. Main risks: dense-keyframe worst cases, unbounded/unstable feedback by design, memory limits and parameter extremes.

AGPLv3 source obligations apply. The pinned upstream dependency differs from current main; fidelity must be checked against the intended pin. README says builds but not heard on Versio. No MPC port was found in the bounded search. **Decision:** promising granular follow-on, ~2–4 weeks after infrastructure; prioritize if transient stretch is the desired sound.

## 6. Tapeo and Triwalkma — onoma2

Sources: [Tapeo](https://github.com/onoma2/TapeoVersio), [Triwalkma](https://github.com/onoma2/TriwalkmaVersio), [Tapeo bundled runtime license](https://github.com/onoma2/TapeoVersio/blob/8f7883784c257f439406b6bb9156a614b63052a7/gen_dsp/genlib.h), [Triwalkma bundled runtime license](https://github.com/onoma2/TriwalkmaVersio/blob/38a6b291804f2ab0792d9207cd0fd99e98c3c0f4/gen_dsp/genlib.h).

Both contain Max patches, generated C++ .cpp/.h, parameter JSON and gen_dsp support files. That existing generated DSP should be preferred over hand reimplementation **only after licensing is resolved**. A C++ Linux host adapter is technically plausible; existing exports do not remove runtime/data/memory obligations.

Tapeo: delay/fuzz with envelope follower, feedback tone, wobble, clock multiplier/divider, fuzz routing and follower polarity. README calls the beta too loud and clock division unstable. Root license absent. Bundled Cycling '74 runtime explicitly grants **non-commercial use only**, with commercial licensing by request.

Triwalkma: three continuously recording stereo loops, overdub, feedback, reverse varispeed, Wand recording destination and Y/parallel/serial routing. Root GPLv3 text exists, but the same non-commercial runtime remains. GPL redistribution freedoms cannot be reconciled merely by declaring the root GPL file authoritative over third-party code.

Both need commercial-use-capable runtime/export rights and an appropriate author grant for the original patch material. An alternative lawful runtime needs a demonstrated compatibility/provenance path; it is not a permission-free excuse to rewrite copyrighted DSP. Binary-for-free distribution does not make a non-commercial restriction compatible with open source. **Decision:** blocked, not first-port candidates.

## 7. Proteus — Seaside Modular / abluenautilus

Sources: [README](https://github.com/abluenautilus/ProteusVersio/blob/4a3efe684e598b53880086ebdb05072315071a35/README.md), [implementation](https://github.com/abluenautilus/ProteusVersio/blob/4a3efe684e598b53880086ebdb05072315071a35/ProteusVersio.cpp), [MIT license](https://github.com/abluenautilus/ProteusVersio/blob/4a3efe684e598b53880086ebdb05072315071a35/LICENSE).

Generates a melody, loops/mutates/transposes it and periodically replaces it. Source has 32-step storage, scale/note helpers, std::vector/string/random-related state and process-global rand/srand. It uses DaisySP Pluck and FormantOscillator. The README explains that Versio lacks CV/gate outputs and therefore renders a complete voice.

Best MPC form: **tempo-synced instrument with internal voice**, scale/root/mutation/repeat controls, seed and saved sequence. Replace ADC/gate/timer processing with host musical time and deterministic per-instance RNG; allocate scale/melody storage before audio. Optional played-note transposition is a new feature. Use independent branding and audit the exact DaisySP oscillator notices.

External MIDI sequence export is a separate feature needing the ALSA workaround and loop/echo safety testing described in the architecture. No VST MIDI-output guarantee. **Decision:** good lower-memory generative candidate, ~2–4 weeks for internal voice.

## 8. Cithara — TricksterSam

Sources: [repo](https://github.com/TricksterSam/CitharaVersio), [versio.pd](https://github.com/TricksterSam/CitharaVersio/blob/01d920ae2eb79a4b614cfb32f4f5cc882e52e98b/versio.pd), [license](https://github.com/TricksterSam/CitharaVersio/blob/01d920ae2eb79a4b614cfb32f4f5cc882e52e98b/LICENSE).

Source is Pure Data patches plus compiled firmware and a PDF manual. Discovery index describes a microtonal sympathetic-string resonator. hv.* objects in patches suggest Heavy-compatible compilation, but the exact generator/runtime version and license are not established. There is no inspected source-export C++ engine in the root.

Possible independent port routes: lawfully licensed hvcc-generated DSP, or embedding a reviewed libpd runtime; neither requires or permits any MPC-PD-LAB dependency. Heavy object support, DSP buffer size, resonator count, channel semantics and event scheduling must be proven. Root GPLv3 text does not license unknown compiler/runtime dependencies. **Decision:** higher-uncertainty resonator candidate, defer pending toolchain audit; ~4–8 weeks after clearance.

## 9. Audrey II Versio — Konstantin Svechtarov

Sources: [repo](https://github.com/KoSv/DaisyVersio_Audrey_II), [Engine](https://github.com/KoSv/DaisyVersio_Audrey_II/blob/4d20e49f94d3b9e63a965d765f3df502d041a7db/Source/FeedbackSynthEngine.cpp), [license](https://github.com/KoSv/DaisyVersio_Audrey_II/blob/4d20e49f94d3b9e63a965d765f3df502d041a7db/LICENSE.txt).

MIT notice credits Infrasonic Audio, LLC; the port author identifies himself in README. Source has FeedbackSynthEngine, KarplusString, filters, smoothing, echo and custom SDRAM allocation, alongside the Versio adapter. Engine processes mono excitation/noise into stereo feedback/string/reverb output and takes sample rate at Init.

Reuse Engine and DSP stages, replace the SDRAM allocator, audit exact DaisySP reverb/oscillator dependencies and bound feedback/gain. Prefer instrument identity with optional excitation mode; no conventional chromatic MIDI mapping is established by README. Expose frequency/body/filter/echo/reverb and output safely. **Decision:** interesting feedback-texture instrument, medium complexity (~3–5 weeks), needs profiling and crash/output-safety tests.

## 10. Listed firmware without an authorized open-source port path

These discoveries are not all open source. Their descriptions below are **index or repository reports**; source rights are not inferred.

| Firmware | Discovery source | Outcome |
| --- | --- | --- |
| Official Desmodus, Electus, Imitor, Melotus, Granulita, Ruina, Yester, Ampla, Fala, Lacrima, Polydactyl | [index / official links](https://github.com/Maxhodges/noise-engineering-firmware-index#official-firmware) | No redistributable official DSP source/license found. Product/firmware availability does not authorize a port. NE's separate desktop products are not source grants. |
| The Archivist — Detuned Transmissions / Jason Hockman | [repository and LICENSE](https://github.com/jhockman/the-archivist) | Inspected repo has only binary/README/license. Source absent; modification, reverse engineering and product bundling restricted. Exclude absent written permission. |
| WTF! — DUB-Russell | [linked site](https://2020.dubrussell.com/resources/wtf/), [index](https://github.com/Maxhodges/noise-engineering-firmware-index) | Granular/repeat/cloud lead; no audited source or license. Do not label open source. |
| FRGMNTS / VNY404 — Acidclank | [FRGMNTS](https://acidclank.gumroad.com/l/frgmntsversio), [VNY404](https://acidclank.gumroad.com/l/VNY404) | Glitch/tape/delay and vinyl/cassette leads; product/download pages, not verified reuse grants. |
| Pyros — Audiority | [product site](https://www.audiority.com/shop/pyros-versio/) | Distortion lead; no source license established. |
| Multi Versio — FluffyAudio; Megatron — joel.gilardini; Filterbank — ericxgao | [index](https://github.com/Maxhodges/noise-engineering-firmware-index#versio-third-party-firmware) | Binary/download/discussion leads. Source availability and license unresolved. |
| Reticulum; Praetereo — Negative Theology; Repetit | [index's looper section](https://github.com/Maxhodges/noise-engineering-firmware-index#loopers-and-delays) | Research leads, not independently identified/audited source repositories. Do not equate every similar name with Repetita. |
| Acidus; Stray Drum — Jasmine & Olive Trees | [index](https://github.com/Maxhodges/noise-engineering-firmware-index) | Synth/drum leads, not audited source. |
| Rings Versio — ericxgao | [index](https://github.com/Maxhodges/noise-engineering-firmware-index) | Mutable algorithm already has MPC implementations; no priority, and a downloadable Versio binary is not a new license grant. |

Official development follow-ups: [Versio development guide](https://noiseengineering.us/pages/versio-dev-guide), [create-your-own-firmware article](https://noiseengineering.us/blogs/loquelic-literitas-the-blog/create-your-own-firmware-on-a-versio-module/). These official pages could not be retrieved in this session. Platform facts above are supported by inspected Electro-Smith interfaces and community code instead.

## Recommendation

For a new Versio-derived plugin, start with **Repetita/Wreath** once the small shared-host proof is complete. Keep Capicola and Smack as stronger granular/glitch follow-ons. Use PlateauXXL as proven community prior art. Do not port official NE DSP, restricted binaries or unlicensed Max projects without a specific lawful source/reuse route.
