# Eurorack DSP → independent MPC plugins: ecosystem research

Research date: 14 October 2026. Target: **original MPC One, Hakai 3.9.1, Linux ARMv7**, as specified by the project owner. This repository is an independent research project. It has no dependency on MPC-PD-LAB.

## Reading order and evidence standard

1. [Portability matrix](PORTABILITY_MATRIX.md): shortlist and comparative effort.
2. [Versio analysis](VERSIO_ANALYSIS.md): individual community firmwares and excluded binaries.
3. [Infinite Digits analysis](INFINITE_DIGITS_ANALYSIS.md): component extraction and existing desktop work.
4. [VST2 architecture](VST2_ARCHITECTURE.md): host integration, packaging and licensing gates.
5. [First-port recommendation](FIRST_PORT_RECOMMENDATION.md): a bounded proof of concept and acceptance criteria.

Evidence labels used throughout:

- **Source verified:** repository files, license texts or executable code inspected at the revisions listed below. This does not mean the code has been run.
- **Upstream reported:** a maintainer's README, test record or community account. Hardware claims remain attributed to that source.
- **Proposed/inferred:** engineering assessment, resource arithmetic or a future design choice.
- **Unverified:** needs additional licensing evidence, runtime measurement or testing on the user's actual MPC One.

Public GitHub repository search, README links, source inspection and license inspection were used. Source checkouts are temporary research material outside this project. No firmware or plugins were built, compiled, executed, installed or downloaded to the MPC. No MPC.settings changes, PRs, merges or plugin replacements were performed. No MPC-PD-LAB files were read or changed.

Direct retrieval of api.github.com, noiseengineering.us, helpcenter.steinberg.de and gnu.org was denied by the research machine's outbound proxy. GitHub web search and authenticated read-only Git worked. Official NE and Steinberg links below are follow-up references, not pages verified during this research. GitHub-hosted primary license texts were inspected instead. Discovery is substantial but not an exhaustive enumeration of either ecosystem.

## Versio: platform access is not DSP permission

[libDaisy's Versio interface](https://github.com/electro-smith/libDaisy/blob/08087203debc646d3710ec8caa35bac6cf20ab5e/src/daisy_versio.h) and [DaisyExamples](https://github.com/electro-smith/DaisyExamples/tree/259ed82c7d4c0d7699f695945e6e111b7dc7cb27/versio) verify stereo input/output, seven knob/CV controls, two three-position switches, one button and four RGB LEDs. Community source targets Daisy Seed / STM32H750, not a Linux process. The open development route permits independent firmware development; it does not grant rights to Noise Engineering's official algorithm implementations.

Discovery index: [Maxhodges/noise-engineering-firmware-index](https://github.com/Maxhodges/noise-engineering-firmware-index). It lists both official and third-party releases, including binary-only and commercial releases. Its MIT license covers the index, **not the listed firmwares**.

The most useful source-backed discoveries are:

| Project / author | Function and implementation | License evidence / existing adaptation |
| --- | --- | --- |
| [CRCLTR — s3g](https://github.com/s3g/crcltr) | Dual stereo looper; Max/Gen/Oopsy patches | No explicit project license found. Max patches are an existing desktop editing environment, not a redistributable Linux plugin. |
| [Campestria / PlateauNEVersio — digitalartifactmusic; original DSP Dale Johnson](https://github.com/digitalartifactmusic/PlateauNEVersio) | C++ Dattorro/Plateau reverb plus embedded adaptations and limiter | GPLv3-or-later grant in LICENSE.md; original [ValleyRackFree](https://github.com/ValleyAudio/ValleyRackFree) is a VCV Rack implementation. An MPC port already exists: [PlateauXXL](https://github.com/sunskiefer/PlateauXXL). |
| [Repetita — hirnlego / Roberto Noris](https://github.com/hirnlego/repetita-versio) and [Wreath](https://github.com/hirnlego/wreath) | Stereo varispeed looper, delay, freeze and feedback coloration; C++ | Both MIT. Wreath has a separated engine and desktop test source; still has shared global SDRAM buffers. |
| [Smack Versio — Tim Cox](https://github.com/timncox/smack-versio) | Seeded loop slicing, beat repeat, tape stop, reverse, granular freeze and other glitches; C | MIT; engine from [schwung-smack](https://github.com/timncox/schwung-smack), an Ableton Move implementation. Versio copy diverges and hardcodes 48 kHz. |
| [Capicola Versio — Tim Cox; upstream Heavy Light Industries](https://github.com/timncox/capicola-versio) | Transient-driven keyframe time stretch / pitch shift; C++ | AGPLv3. Existing hardware-free port layer with runtime sample rate and per-instance rings; [Move port](https://github.com/timncox/capicola-move). |
| [Tapeo — onoma2](https://github.com/onoma2/TapeoVersio) | Tape-like delay/fuzz/envelope follower; Max/Gen with generated C++ | No project license found; bundled Gen export runtime says non-commercial use only. |
| [Triwalkma — onoma2](https://github.com/onoma2/TriwalkmaVersio) | Three stereo varispeed loopers; Max/Gen with generated C++ | Root GPLv3 license; bundled Gen runtime has non-commercial restriction. Licensing conflict requires resolution. |
| [Proteus — abluenautilus / Seaside Modular](https://github.com/abluenautilus/ProteusVersio) | Generative melody plus formant/plucked voice; C++/DaisySP | MIT. Internal voice is more tractable than an external-MIDI-only sequencer. |
| [Cithara — TricksterSam](https://github.com/TricksterSam/CitharaVersio) | Sympathetic resonator; Pure Data patch with hv.* objects | Root GPLv3 text. Needs Heavy/hvcc runtime and object provenance audit; no generated C++ in inspected root. |
| [Audrey II Versio — Konstantin Svechtarov](https://github.com/KoSv/DaisyVersio_Audrey_II) | Feedback/string/noise synthesis with reverb and echo; C++ | MIT notice credits Infrasonic Audio, LLC. Separable Engine class, but SDRAM allocator and DaisySP remain. |
| [The Archivist — Jason Hockman / Detuned Transmissions](https://github.com/jhockman/the-archivist) | Tape/granular memory processor | **Binary-only restricted license**; no source, modification/reverse engineering prohibited by provided terms. Excluded. |

Official Desmodus, Electus, Imitor, Melotus, Granulita, Ruina, Yester, Ampla, Fala, Lacrima and Polydactyl are discovery-index entries, not proven open-source DSP. Third-party WTF!, FRGMNTS, VNY404, Pyros, Multi Versio, Megatron, Reticulum and the index's Praetereo/Repetit entries likewise do not acquire an open-source license merely by being listed. Firmware-specific status is in [VERSIO_ANALYSIS.md](VERSIO_ANALYSIS.md).

## Infinite Digits: reuse the current desktop boundary

[schollz/_core](https://github.com/schollz/_core) is a C firmware/tooling monorepo for Zeptocore, Zeptoboard, Ectocore and Ezeptocore. At the inspected revision it contains a **VCV Rack 2 port and a shared, instance-oriented desktop engine**, not just embedded RP2040 firmware. That is a major reduction in the effort needed for a sampler port.

| Project / author | Useful material | Scope / licensing |
| --- | --- | --- |
| [_core — Zack Scholl](https://github.com/schollz/_core) | Fixed-point effects, sampling, granular stretch, clock/sequence behavior, wavetable engine; [desktop C API](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/lib/core_engine/core_engine.h) | _core code GPLv3; desktop adapter explicitly GPL-3.0-only. Rack SDK/UI are unnecessary for the VST. No sample-pack rights implied. |
| [oooo-vst — Zack Scholl](https://github.com/schollz/oooo-vst) | Modern C++ tape-loop Engine, dual heads, scheduler, routing, tape stage, loop editing | README explicitly grants GPLv3 to public project. The commercial JUCE application is **not in this repository**. Engine can be investigated independently; don't claim the complete commercial plugin is open source. |
| [fpfx — Zack Scholl](https://github.com/schollz/fpfx) | Standalone fixed-point effect experiments / desktop C entry point | No explicit license found in inspected root/files. Prefer licensed _core equivalents; do not assume _core's license automatically applies here. |
| [pikocore — Zack Scholl](https://github.com/schollz/pikocore) | RP2040 lo-fi sample mangler and generation tools | Root MIT; per-file/dependency audit still required. Sample assets must be independently cleared. |
| [graintopia — Zack Scholl](https://github.com/schollz/graintopia) | 18 generative grains with coupled-motion behavior; Lua/SuperCollider | MIT for this project. norns, SC extensions and [fverb](https://github.com/jpcima/fverb) are separate dependencies. Interesting later design, substantial native port. |
| [oooooo — Zack Scholl](https://github.com/schollz/oooooo) | Six-loop norns performance logic, probability, chord layering | MIT script; relies on norns/softcut rather than containing all audio DSP. Prefer oooo-vst for modern native tape DSP. |
| [amenbreak — Zack Scholl](https://github.com/schollz/amenbreak) | Probability controls, slice performance, stutter/tape-stop ideas | MIT script; SuperCollider/norns requirements. Included/downloaded Amen material has independent recording/composition rights. |

Further search leads: [barcode](https://github.com/schollz/barcode), [ouroboros-norns](https://github.com/schollz/ouroboros-norns), [oooooooo](https://github.com/schollz/oooooooo), [zxcvbn](https://github.com/schollz/zxcvbn), [mx.samples](https://github.com/schollz/mx.samples), [o-o-o](https://github.com/schollz/o-o-o), and [thirtythree](https://github.com/schollz/thirtythree). These are discovery leads, not fully audited candidates. No license or performance ranking is assigned to an uninspected project.

## Existing MPC community work

The principal inspected framework is [sd88me/mpc-vst-plugins](https://github.com/sd88me/mpc-vst-plugins). Its own wrapper/tools license is MIT; vendored assets and listed plugins retain separate licenses. Its [hardware notes](https://github.com/sd88me/mpc-vst-plugins/blob/4a8a25fb6fd41d51c9a4eaa4aeb7338df4070042/docs/NOTES.md) provide attributed Force measurements and some MPC One/Live reports. They must not be generalized into a claim that this project's plugins work on the user's Hakai One.

Source-backed references:

- [Boris Granular](https://github.com/sd88me/mpc-vst-boris): stereo insert effect with a plain C engine, freeze, tempo sync, presets and Q-Link skin. GPLv3; tested.json records Force, MPC OS 3.9.1, 10 October 2026. Excellent effect adapter/reference, already covers a generic granular effect.
- [PlateauXXL](https://github.com/sunskiefer/PlateauXXL): C++ Plateau port, limiter, modulators, state and custom presets. GPLv3-or-later code; some included knob artwork is CC BY-NC 4.0. tested.json records Force 3.9.1, 9 October 2026. Reuse appropriate code and original artwork rather than copying non-commercial artwork into an unrestricted package.
- [MPC Plaits](https://github.com/poloq-instruments/mpc-vst-plaits), [Resonator](https://github.com/saustin2010/mpc-vst-resonator) and [Verglas](https://github.com/saustin2010/mpc-vst-verglas): catalog-confirmed Mutable DSP ports. Reference only; not new-port priorities.
- [NAM](https://github.com/jacob-sabella/mpc-vst-nam): catalog-discovered effect integration and asynchronous file handling reference. Not independently source/license-audited here.
- [Euclidier](https://github.com/sd88me/mpc-vst-euclidier): sequencer reference; account for the host ignoring normal VST MIDI output.
- Catalog includes many Airwindows and Dragonfly effects. Existing availability reduces the value of another generic delay or reverb port; catalog listing alone is not a hardware certification.

Confirmed from framework source: hand-written VST2 ABI, ARMv7/armhf builds, generated skins and plugin-list XML, parameter/chunk support, effect processing. **Also confirmed:** per-instance pthread mutex around engine calls, 16-bit internal effect conversion, 8 KiB chunk storage, fixed 44.1 kHz assumptions and sample-rate dispatcher accepting rather than adapting rate changes. These are design limitations to address deliberately.

Community-reported integration: 44.1 kHz / 128-frame audio, ARMv7, host tempo/PPQ and state chunks, native Q-Link skins, installation using a settings entry and content folder. Force 3.9.1 is the main tested platform. Hakai service names and path behavior need separate verification; the notes mention Hakai 2.15.1 reports and service-detection fixes, not this user's exact 3.9.1 setup.

## License audit and release policy

License conclusions are component-specific, not GitHub visibility-based. Preserve original author notices, license versions, exact revisions, local modifications and build instructions for every imported file.

### GPLv3 and AGPLv3

The inspected [_core LICENSE](https://github.com/schollz/_core/blob/10b4bf7d8c0da43098ac64bbde96cdb06fa02905/LICENSE) is the GPLv3 text. Its desktop engine files and Rack license explicitly specify GPL-3.0-only; other headers say GPLv3. Use GPL-3.0-only for the proposed combined _core plugin unless a specific broader grant is established. Plateau's LICENSE.md expressly grants version 3 **or later**. A bare GPL text alone does not prove an "or later" election for every file.

For distributed modified GPL binaries, provide the exact Corresponding Source, modifications, interfaces, generated-source inputs and scripts needed to build/install them; keep notices, mark changed files and distribute the combined covered plugin under compatible GPL terms. The simplest release is binary plus matching source archive and a durable source link from the same release. GPL allows commercial distribution; "free download only" is not a GPL obligation. MIT wrapper code can be combined into the GPL plugin while retaining its notice.

GPL section 6's Installation Information requirement has a particular trigger: conveyance in/with/specifically for a User Product as part of a transaction transferring possession/use of that product. It is **not automatically triggered by every downloadable plugin**, but must be evaluated if shipping a configured device or locked appliance. Document reproducible installation regardless. Do not distribute Akai firmware, keys or patches as a shortcut.

AGPL Capicola also requires review of section 13 for a **modified program that supports remote network interaction**. A local audio plugin is not automatically a network service; adding remote control/web service changes that assessment. Preserve the AGPL source-offer path if that feature is introduced.

Loading a GPL plugin into a proprietary host is a separate legal question from using a proprietary SDK. Do not assert that merely using VST means Akai must publish its host, or that every host/plugin combination is automatically permitted. Assess whether the specific plugin and host form separate works, any applicable exceptions and actual dependencies before a binary release. No exception covering the proposed _core/MPC combination was found in this audit; this remains a release review item.

### Third-party rights and names

_core credits Apache-2.0 FatFs integration/PCG, MIT SdFat/TinyUSB components and CC-BY-SA-3.0 hardware. Use only the needed desktop/DSP subset. The header/table provenance still matters even if hardware drivers are omitted. CC hardware terms do not replace firmware GPL terms. No bundled samples are authorized by a code license.

_core's README states **Infinite Digits and Ectocore are registered trademarks and must not be used as names on derivative works**. Respect that explicit request: use original plugin names/vendor identity and original skins; give accurate source attribution in documentation. Do not reuse Infinite Digits logos, hardware panel art or branded Rack assets. Other product names—including Noise Engineering, Versio, Akai and third-party project names—are references, not endorsements or permission to brand a new plugin. Verify specific naming rights before release.

CRCLTR/Tapeo/fpfx lack sufficient permission for this project's reuse. Triwalkma's bundled runtime restriction cannot be erased by its root GPL file. Archivist's binary terms explicitly forbid modification and reverse engineering. These are **blocked candidates**, not merely inconvenient license badges.

### VST2

Do not obtain or redistribute an unlicensed copy of Steinberg's discontinued VST2 SDK. Existing SDK agreements, dates, licensees and distribution permissions must be checked against the actual agreement; VST3 rights do not provide VST2 rights. [Steinberg's discontinuation page](https://helpcenter.steinberg.de/hc/en-us/articles/4409561018258-VST-2-Discontinued) was not retrievable here and is a required current-terms follow-up.

Preferred technical route: the inspected community wrapper's independent ABI declarations under MIT, **no Steinberg SDK and no copied Steinberg header files**. This avoids relying on an unavailable SDK grant and the usual proprietary-SDK/GPL combination issue. It does not by itself settle all copyright, trademark, contract or host-linkage questions. Audit declaration provenance; don't advertise Steinberg certification or use VST logos without permission. Binary distribution remains contingent on the legal review described in [VST2_ARCHITECTURE.md](VST2_ARCHITECTURE.md).

## Snapshot ledger

These revisions were fetched and inspected. Claims referring to moving main branches should be interpreted against this ledger. Repository tests were **not run** in this design-only phase. Source timestamps are not proof of release dates, quality or compatibility.

| Repository | Inspected revision |
| --- | --- |
| [abluenautilus/ProteusVersio](https://github.com/abluenautilus/ProteusVersio/tree/4a3efe684e598b53880086ebdb05072315071a35) | `4a3efe684e598b53880086ebdb05072315071a35` |
| [digitalartifactmusic/PlateauNEVersio](https://github.com/digitalartifactmusic/PlateauNEVersio/tree/4218b072e7420dd788cd3c98c36b3eba445f8886) | `4218b072e7420dd788cd3c98c36b3eba445f8886` |
| [electro-smith/DaisyExamples](https://github.com/electro-smith/DaisyExamples/tree/259ed82c7d4c0d7699f695945e6e111b7dc7cb27) | `259ed82c7d4c0d7699f695945e6e111b7dc7cb27` |
| [electro-smith/DaisySP](https://github.com/electro-smith/DaisySP/tree/2c72eaf9eac5fc0dca1919d65d606da907832618) | `2c72eaf9eac5fc0dca1919d65d606da907832618` |
| [electro-smith/libDaisy](https://github.com/electro-smith/libDaisy/tree/08087203debc646d3710ec8caa35bac6cf20ab5e) | `08087203debc646d3710ec8caa35bac6cf20ab5e` |
| [heavylight-industries/capicola](https://github.com/heavylight-industries/capicola/tree/8c64e855fac64054fdb38451db00866ea682d0d8) | `8c64e855fac64054fdb38451db00866ea682d0d8` |
| [hirnlego/repetita-versio](https://github.com/hirnlego/repetita-versio/tree/99b61f3f2227035671013bd11ebf607483434bee) | `99b61f3f2227035671013bd11ebf607483434bee` |
| [hirnlego/wreath](https://github.com/hirnlego/wreath/tree/710cd8b1704d97d1cb8a06fcf2f1c82be1caf134) | `710cd8b1704d97d1cb8a06fcf2f1c82be1caf134` |
| [jhockman/the-archivist](https://github.com/jhockman/the-archivist/tree/752e48de23d5b795d6f69af087ccc6d12a2849f7) | `752e48de23d5b795d6f69af087ccc6d12a2849f7` |
| [KoSv/DaisyVersio_Audrey_II](https://github.com/KoSv/DaisyVersio_Audrey_II/tree/4d20e49f94d3b9e63a965d765f3df502d041a7db) | `4d20e49f94d3b9e63a965d765f3df502d041a7db` |
| [Maxhodges/noise-engineering-firmware-index](https://github.com/Maxhodges/noise-engineering-firmware-index/tree/187dc43dcdaacb68420d32438a90096f87f29fba) | `187dc43dcdaacb68420d32438a90096f87f29fba` |
| [onoma2/TapeoVersio](https://github.com/onoma2/TapeoVersio/tree/8f7883784c257f439406b6bb9156a614b63052a7) | `8f7883784c257f439406b6bb9156a614b63052a7` |
| [onoma2/TriwalkmaVersio](https://github.com/onoma2/TriwalkmaVersio/tree/38a6b291804f2ab0792d9207cd0fd99e98c3c0f4) | `38a6b291804f2ab0792d9207cd0fd99e98c3c0f4` |
| [s3g/crcltr](https://github.com/s3g/crcltr/tree/f7ccd030b9d36c47a00be81fb0b5f5b567961176) | `f7ccd030b9d36c47a00be81fb0b5f5b567961176` |
| [schollz/_core](https://github.com/schollz/_core/tree/10b4bf7d8c0da43098ac64bbde96cdb06fa02905) | `10b4bf7d8c0da43098ac64bbde96cdb06fa02905` |
| [schollz/amenbreak](https://github.com/schollz/amenbreak/tree/14f591bfb0dee0cdc6eb65adf75866b03280072b) | `14f591bfb0dee0cdc6eb65adf75866b03280072b` |
| [schollz/fpfx](https://github.com/schollz/fpfx/tree/d746e73bec112034c9285a0a55b52d8242c0ed43) | `d746e73bec112034c9285a0a55b52d8242c0ed43` |
| [schollz/graintopia](https://github.com/schollz/graintopia/tree/2c7efd88adf1b847cdff00cfdb166fdeb8b6953c) | `2c7efd88adf1b847cdff00cfdb166fdeb8b6953c` |
| [schollz/oooo-vst](https://github.com/schollz/oooo-vst/tree/d7e0d7dbf6841bff136c3ac6189982b0c597fa25) | `d7e0d7dbf6841bff136c3ac6189982b0c597fa25` |
| [schollz/oooooo](https://github.com/schollz/oooooo/tree/67c29d3a3d8eb53e95fe47a20c00b954df2e0023) | `67c29d3a3d8eb53e95fe47a20c00b954df2e0023` |
| [schollz/pikocore](https://github.com/schollz/pikocore/tree/1af735ed294ac50db24c54e7f5e26601e3dc3aa5) | `1af735ed294ac50db24c54e7f5e26601e3dc3aa5` |
| [sd88me/mpc-vst-boris](https://github.com/sd88me/mpc-vst-boris/tree/5a63228303f24f7647df94d59d016b9248e62e23) | `5a63228303f24f7647df94d59d016b9248e62e23` |
| [sd88me/mpc-vst-plugins](https://github.com/sd88me/mpc-vst-plugins/tree/4a8a25fb6fd41d51c9a4eaa4aeb7338df4070042) | `4a8a25fb6fd41d51c9a4eaa4aeb7338df4070042` |
| [sunskiefer/PlateauXXL](https://github.com/sunskiefer/PlateauXXL/tree/4f2e739088af2ac96bd43bf5ca8630001388ccd7) | `4f2e739088af2ac96bd43bf5ca8630001388ccd7` |
| [timncox/capicola-versio](https://github.com/timncox/capicola-versio/tree/acafccc5c22b539b6d9843496c92151d613d1537) | `acafccc5c22b539b6d9843496c92151d613d1537` |
| [timncox/smack-versio](https://github.com/timncox/smack-versio/tree/f839b2ac64f813ec00b2220eee0b41d9d170b237) | `f839b2ac64f813ec00b2220eee0b41d9d170b237` |
| [TricksterSam/CitharaVersio](https://github.com/TricksterSam/CitharaVersio/tree/01d920ae2eb79a4b614cfb32f4f5cc882e52e98b) | `01d920ae2eb79a4b614cfb32f4f5cc882e52e98b` |
| [ValleyAudio/ValleyRackFree](https://github.com/ValleyAudio/ValleyRackFree/tree/86f02e431136a7f5c96a872b99b7115b7e133e05) | `86f02e431136a7f5c96a872b99b7115b7e133e05` |

Dependency pins additionally checked: Repetita records Wreath `1662b8ccfad339f3d306fe2868b3c039698fad6c`; Capicola Versio records upstream `f0fb61cfa7111067b4ec1a642d1b16a0910adb3b`. Both objects were fetched; the Wreath buffer declarations and pinned upstream Capicola license were inspected. Separate current checkouts in the ledger are not substitutes for these dependency pins. Before implementation, audit the exact pinned dependency trees and imported files.

## Research outcome

Prioritize a small _core beat-repeat port to prove host integration, Repetita/Wreath for a distinctive stereo live looper, and the existing _core desktop engine for a richer sample instrument. Capicola and Smack are promising follow-ons. Reuse PlateauXXL/Boris and the MPC tooling as references; do not spend the first port duplicating already available Mutable or Plateau DSP.

Still required before release: exact MPC One/Hakai runtime confirmation, source-level realtime hardening, measured ARM performance, component-level notices for the final dependency closure and VST2/host legal review. Research and design are complete; implementation is pending explicit approval.
