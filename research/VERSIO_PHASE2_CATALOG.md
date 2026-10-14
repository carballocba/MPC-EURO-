# Versio alternatives: Phase 2 catalog

Research date: 14 October 2026. Target: **original MPC One, Hakai 3.9.1, Linux ARMv7**. Research only; no implementation, builds, plugin execution, installation, settings edits, binary reverse engineering or outreach. This is independent of MPC-PD-LAB.

## Scope, evidence and counts

This catalog investigates **29 distinct third-party Versio firmwares**. Wreath is Repetita's engine, not an extra firmware; Campestria/PlateauNEVersio is one firmware; the index's Repetit entry points to the same forum thread associated with Repetita and is not counted again. Versions and FRGMNTS' four effects are not separate firmwares. `_core` BeatRepeat is an additional **non-Versio DSP comparator**, outside the 29. Official NE firmwares and development skeleton Nihil are contextual references, outside the candidate count.

**9 of 29 have published DSP/patch source with an adaptation-permitting project license**: Repetita, Smack, Capicola, Proteus, Audrey II, Resilio, Acidus, Plateau and Cithara. This is a source-grant count, not certification of the final binary/dependency closure. **6 are category A**; Cithara still needs a generated-runtime audit, and Acidus/Plateau have MPC DSP-family implementations already. **19 require a new or clarified permission grant for firmware-specific reuse**, including unavailable-source products and missing/conflicting licenses. **Clackotron is the remaining 1**: an MIT license is present, but DSP source is absent from the inspected repository; request source rather than presume extra permission is necessary. Rings' already-ported Mutable core does not clear an unidentified Versio adapter.

Evidence labels:

- **S — source inspected:** executable source/license text at a pinned revision; no claim it was run.
- **P — primary publisher report:** developer page/manual/changelog/API release record; independent hardware/audio behavior untested.
- **I — index/secondary lead:** identity/features/download mentioned elsewhere; not a source grant.
- **U — unknown/proposed:** unavailable source, numerical extrapolation or future MPC mapping.

Discovery used the official DUB-Russell resources/WTF/contact pages, Acidclank product data and linked guide graphic, Modular Bias → Acidus repository/manual, GitHub web/API repository search, release records, source files and [the community index](https://github.com/Maxhodges/noise-engineering-firmware-index/blob/187dc43dcdaacb68420d32438a90096f87f29fba/README.md). Source repos were cloned into temporary research storage; their firmware/build artifacts were not analyzed or copied into this repository. The official WTF ZIP was held in memory only for directory metadata inspection; its single .bin entry was not extracted or decoded.

The YouTube URLs supplied for Multi/WTF returned proxy 403; Modwiggler and Reddit returned 403; broad GitHub web queries later returned 429; Google returned a JS redirect shell, not search results. GitHub API search, publisher pages and source Git reads supplied the usable evidence. Do not treat a failed search or absent source link as proof that no private source exists. No CAPTCHA, checkout, registration or access-control bypass was attempted.

## Catalog

Categories: **A** source/grant/technical promise; **B** source with substantial unresolved technical/license questions; **C** download/binary advertised, source or permission not established; **D** explicit restriction/conflict or unsuitable reuse; **E** already-ported DSP family/reference. E does **not** mean an exact Versio control adapter is already ported.

| ID | Firmware / developer | Category | Evidence and function | Source / next action |
| --- | --- | --- | --- | --- |
| V01 | WTF! / DUB-Russell | C | P: stereo Granular/Repeat/Cloud; ~90 s rolling buffer; v1.0.0 and v1.1 changelog | [Official manual](https://2020.dubrussell.com/resources/wtf/). ZIP contains only WTF-1.1.bin. Request licensed DSP source; see dedicated analysis. |
| V02 | FRGMNTS / Yota Mori (Acidclank) | D | P: Stutter, tape varispeed, DJ LP/HP filter, WASH delay/reverb; v1.2 dated 16 May 2026 | [Product page](https://acidclank.gumroad.com/l/frgmntsversio) prohibits unauthorized redistribution/commercial use. Request a separate source/reuse grant. |
| V03 | MultiVersio / Paolo Ingraito, fluffyaudio | B | S: 9 modes, including stereo lo-fi, microlooper, delay, spectral/resonator processing | [Original source](https://github.com/fluffyaudio/MultiVersio/tree/52839534fe5dbb36baa6fd864aa7eec5369de4ed), README names Paolo. No complete main-program license; ask before extracting. |
| V04 | Acidus / Blue Nautilus, abluenautilus | E (core) | S/P: mono Open303, slide/accent, Babyfish/Mommafish/Devil Fish ranges; no sequencer | [Source](https://github.com/abluenautilus/AcidusVersio/tree/ec8e429428b56da7afbd98e3a7ac29e6b6168ae6), MIT. [MPC Open303](https://github.com/saustin2010/mpc-vst-open303/tree/5b391de0961a7b92bc2a4b02ce828c041d0ab5e4) already covers core/Devilfish. Assess mode-specific differences first. |
| V05 | Campestria / PlateauNEVersio, digitalartifactmusic; DSP Dale Johnson | E (core) | S: stereo Plateau/Dattorro reverb with embedded gain/limiting changes | [Firmware](https://github.com/digitalartifactmusic/PlateauNEVersio/tree/4218b072e7420dd788cd3c98c36b3eba445f8886), GPLv3-or-later. [MPC PlateauXXL](https://github.com/sunskiefer/PlateauXXL/tree/4f2e739088af2ac96bd43bf5ca8630001388ccd7) exists; avoid duplicate DSP work. |
| V06 | Repetita / Roberto Noris, hirnlego | A | S: stereo varispeed loop/delay/freeze; Wreath engine | [Firmware](https://github.com/hirnlego/repetita-versio/tree/99b61f3f2227035671013bd11ebf607483434bee) + [Wreath](https://github.com/hirnlego/wreath/tree/710cd8b1704d97d1cb8a06fcf2f1c82be1caf134), MIT; per-instance buffers, bounded clears and media recall needed. |
| V07 | Smack / Tim Cox | A | S/P: quantized rolling capture, seeded slices, retrigger/reverse/tape stop/granular glitch | [Source](https://github.com/timncox/smack-versio/tree/f839b2ac64f813ec00b2220eee0b41d9d170b237), MIT; reconcile release lineage, stale hardware claims and 48 kHz constants. |
| V08 | Capicola / Heavy Light Industries, Versio port Tim Cox | A | S: transient-driven keyframe stretch/pitch and internal follower modulation | [Portable core](https://github.com/timncox/capicola-versio/blob/acafccc5c22b539b6d9843496c92151d613d1537/core/capicola_engine.h), AGPLv3; already rate/block/instance adapted. Profile worst keyframe density. |
| V09 | Proteus / Seaside Modular, abluenautilus | A | S: renewing/mutating melody plus formant/pluck voice | [Versio](https://github.com/abluenautilus/ProteusVersio/tree/4a3efe684e598b53880086ebdb05072315071a35), MIT; [related VCV sequencer](https://github.com/abluenautilus/SeasideModularVCV/blob/bf3ea150ffa2f3a753ef60bc27a4d7db8707561b/src/Proteus.cpp). Favor internal voice over external MIDI-only port. |
| V10 | Cithara / TricksterSam | B | S/P: sympathetic resonator, microtonal tuning; Pd patches with hv.* objects | [Source](https://github.com/TricksterSam/CitharaVersio/tree/01d920ae2eb79a4b614cfb32f4f5cc882e52e98b), root GPLv3. Resolve exact Heavy/hvcc/object/runtime chain before generation. |
| V11 | Audrey II Versio / Konstantin Svechtarov; Infrasonic Audio DSP | A | S: feedback/noise/string engine, reverb and echo; mono excitation → stereo | [Source](https://github.com/KoSv/DaisyVersio_Audrey_II/tree/4d20e49f94d3b9e63a965d765f3df502d041a7db), MIT; separate SDRAM allocator and exact DaisySP dependencies. |
| V12 | CRCLTR / s3g | B | S/P: Max/Gen/Oopsy dual stereo looper, crossfade/duck boundaries | [Patches](https://github.com/s3g/crcltr/tree/f7ccd030b9d36c47a00be81fb0b5f5b567961176); no project license. Permission plus lawful export/runtime required. |
| V13 | Tapeo / onoma2 | D | S: tape-like delay/fuzz/follower; generated C++/Gen | [Source](https://github.com/onoma2/TapeoVersio/tree/8f7883784c257f439406b6bb9156a614b63052a7); no project grant and bundled Gen runtime is non-commercial-only. |
| V14 | Triwalkma / onoma2 | D | S: three stereo varispeed loops and routed overdub | [Source](https://github.com/onoma2/TriwalkmaVersio/tree/38a6b291804f2ab0792d9207cd0fd99e98c3c0f4); root GPLv3 does not resolve non-commercial Gen runtime conflict. |
| V15 | BenderVersio / onoma2 | D | S: WIP DataBender-inspired Gen/generated C++ | [Source](https://github.com/onoma2/BenderVersio/tree/f0f9c1919fc7562ab59e3088bc0b0fb424a1f8c1); same GPL-root/non-commercial runtime conflict. Not proprietary Qu-Bit DSP evidence. |
| V16 | The Hillside Slicer / kuttor | B | S/P: stereo slots, slices, stretch/pitch, overdub, clock and gate | [Source](https://github.com/kuttor/Versio--The-Hillside-Slicer/tree/f474b5085f79424a91d895b1e09efb04d933cf46); no project reuse license; README 96 kHz disagrees with current 48 kHz / 256-frame setup. |
| V17 | Resilio / Jesse Bauer, jeffebauer | A | S/P: stereo physical spring/dub echo, throws, tone, hold/duck and wear | [Core](https://github.com/jeffebauer/resilio-versio/blob/2ab71a9be56b765bbc2f666527e44cfc278a511e/core/dsp/Tank.h), MIT; native renderer + macOS AU/VST3 exist. Reuse core without JUCE. |
| V18 | VNY404 / Acidclank | D | P: vinyl/cassette noise, wow/flutter, compressor/trigger ducking | [Product](https://acidclank.gumroad.com/l/VNY404), explicit redistribution/commercial restrictions. |
| V19 | Pyros / Audiority | C | P: nine distortions, bias/feedback/radio; v1.0 April 2026 | [Publisher](https://www.audiority.com/shop/pyros-versio/). Existing proprietary desktop product is not source availability. |
| V20 | Stray Drum / Jasmine & Olive Trees | C | P: FM/ring-mod macro drum/chord oscillator beta | [Publisher](https://jasmineandolivetrees.com/pages/stray-drum-versio-firmware); .bin offered, no source grant identified. Some controls/calibration explicitly incomplete. |
| V21 | Filterbank / ericxgao (index attribution) | C | I: filter-bank firmware, Drive download | [Index](https://github.com/Maxhodges/noise-engineering-firmware-index/blob/187dc43dcdaacb68420d32438a90096f87f29fba/README.md); linked Reddit denied. Author/source/license/contact require verification. |
| V22 | Megatron / joel.gilardini (index attribution) | C | I: Monotron-inspired delay, Drive download | [Index](https://github.com/Maxhodges/noise-engineering-firmware-index/blob/187dc43dcdaacb68420d32438a90096f87f29fba/README.md); linked [discussion](https://modwiggler.com/forum/viewtopic.php?t=282911) not inspected. |
| V23 | Reticulum / developer unresolved | C | I: asynchronous delay/looper | [Discussion](https://modwiggler.com/forum/viewtopic.php?t=280196) denied; verify developer/source rather than infer. |
| V24 | Praetereo / Negative Theology (index attribution) | C | I: drifting delayed looper | [Discussion](https://modwiggler.com/forum/viewtopic.php?t=276033) denied; no verified project grant. |
| V25 | The Archivist / Jason Hockman, Detuned Transmissions | D | P: tape/grains memory processor; mono audio + trigger → stereo | [Repository/license](https://github.com/jhockman/the-archivist/blob/752e48de23d5b795d6f69af087ccc6d12a2849f7/LICENSE): binary-only, modification/reverse engineering restricted. Exclude unless author grants a separate route. |
| V26 | Rings Versio / ericxgao (index attribution) | E (core) | I: Mutable Rings firmware; exact Versio adapter not inspected | [Index](https://github.com/Maxhodges/noise-engineering-firmware-index/blob/187dc43dcdaacb68420d32438a90096f87f29fba/README.md). Existing MPC Resonator/Rings is reference; do not assume adapter license. |
| V27 | PulsarVersio / vdo | B | S: native pulsar engine, masking/folding, sync/ring-mod input; distinct output roles | [Source](https://github.com/vdo/PulsarVersio/tree/1d019b5fa0dcdfccaf66ba9b6ca5160c1c43cbbe); no project grant found. Ask license; native engine makes it promising if cleared. |
| V28 | Clackotron / bionoid | C | P: stereo LPG, vactrol/ramp envelope, chorus/M-S/waveshaping | [Repo](https://github.com/bionoid/Clackotron/tree/7119dbc3e7af7a6f58f4939ad96955542f7b719b) contains README, MIT license and .bin, **no DSP source** despite build instructions. Request source. |
| V29 | Kickforce 2000 / wittysalt8451 | D | P: kick plus stereo sidechain/distortion; v2 adds triggered filter/VCA GT mode | [README](https://github.com/wittysalt8451/Kickforce2000-bin/blob/df88d597c39d60372012de7c6533f8b61203da56/README.md) says personal use only, no redistribution/commercial use. Binary-only; needs separate grant. |

## Important discoveries and corrections to earlier uncertainty

### DUB-Russell

The official resources page lists **one Versio firmware project: WTF!**, alongside two 2020 routing/tutorial resources. WTF!'s page says its granular engine originated in the developer's **2020 THE SEMI MODULAR BEAT-MACHINE**. The main 2020 product page is a desktop application description, not a source repo or permission grant. No additional DUB-Russell Versio firmware was identified in the inspected resources/navigation/repository searches. This bounded finding does not establish that no unpublished or historical work exists. Contact is the official [inquiry form](https://2020.dubrussell.com/contact/); social channels are linked there.

### FRGMNTS: verify the individual effects

The [publisher-linked guide graphic](https://public-files.gumroad.com/lvqc4jfizwykh8vdj0w3rhi1ihtu) was visually inspected; it shows serial **Stutter → Tape → Filter → WASH**, shared clock and bypass, with stereo jacks. Stutter latches/replays a segment with TIME; tape SPEED passes through stop into reverse/forward speeds; filter sweeps LP through neutral to HP; WASH selects DLY/RVB/D+R. These are publisher-documented behaviors, not source evidence of tape saturation, independent pitch/time stretch, filter topology or exact internal stereo treatment. Do not silently import typical effect implementations as if they were FRGMNTS' DSP.

v1.2's page explicitly says TAP became BYPASS and tap tempo was removed. The graphic retains external CLK and division ×2/=1/÷2. Older claims about a tap-tempo button should not be carried forward. The actual downloadable manual/version alignment is unverified because no Gumroad checkout was performed.

### MultiVersio: source found, license remains unresolved

[README](https://github.com/fluffyaudio/MultiVersio/blob/52839534fe5dbb36baa6fd864aa7eec5369de4ed/README.md) directly identifies Paolo Ingraito and the Modwiggler thread. The root program and Makefile are available; DSP headers contain individual Emilie Gillet MIT notices. The main program has no comparable broad grant, and README's “Feel free to update and improve the code!” does not specify redistribution/relicensing terms. Treat it as B, not binary-only C and not automatically A. Nine actual source modes are Reverb, Resonator, Filter, LO-FI, MicroLooper, Delay, Spectra, Spectrings and Natural Gate. Do not confuse FRGMNTS' four effects with this implementation.

### Acidus: real source, existing MPC DSP

[Author manual](https://github.com/abluenautilus/AcidusVersio/blob/ec8e429428b56da7afbd98e3a7ac29e6b6168ae6/docs/AcidusVersioManual.pdf) and source confirm a **mono voice duplicated into L/R, no built-in sequencer**, slide/accent and three range modes. Open303 uses sample-rate setters and note events rather than needing Versio ADC calibration on Linux. [MPC Open303 README/tested record](https://github.com/saustin2010/mpc-vst-open303/blob/5b391de0961a7b92bc2a4b02ce828c041d0ab5e4/README.md) reports Live II 3.9.1 tests, not Hakai One tests. Its upstream-derived MPC package is GPL, even though Acidus' embedded Open303 copy is MIT; one repo's license must not be applied to the other's additions.

### New reusable native core: Resilio

[CMake](https://github.com/jeffebauer/resilio-versio/blob/2ab71a9be56b765bbc2f666527e44cfc278a511e/CMakeLists.txt) builds the platform-independent core separately from JUCE and hardware; [NOTICE](https://github.com/jeffebauer/resilio-versio/blob/2ab71a9be56b765bbc2f666527e44cfc278a511e/NOTICE) expressly keeps original core source MIT while the JUCE-linked desktop binaries are AGPLv3. Tank exposes prepare/process, normalized parameters, host tempo and sample-offset gate/button/clock events. It can be reused without the desktop UI/runtime. Existing firmware CPU percentages and desktop listening claims are upstream reports, not MPC measurements. This is a stronger candidate than a generic “another reverb” description suggests: throws, worn echo, hold/duck and dub tone are performance tools.

## Release/revision notes

| Firmware | Verifiable version evidence | Limit |
| --- | --- | --- |
| WTF! | Official changelog v1.0.0 initial, v1.1 fewer enable/bypass pops and refined Repeat response; current ZIP names WTF-1.1.bin | No release dates stated there; index's April 2026 date is secondary, not a verified first-release timestamp. |
| FRGMNTS | Product lists v1.2, 16 May 2026; filter smoothing, fewer tape/WASH clicks, clearer reverb, startup LEDs and bypass change | No source revision; no complete earlier timeline. |
| Acidus | GitHub releases [v1.0.0](https://github.com/abluenautilus/AcidusVersio/releases/tag/v1.0.0) published 26 April 2024 (Brisbane); [v1.0.1](https://github.com/abluenautilus/AcidusVersio/releases/tag/v1.0.1) published 24 August 2024 (Brisbane), calibration tweaks | Publication timestamps, not necessarily original authoring date. Latest source HEAD differs from tag SHAs; pin intended revision. |
| Multi | Index links MultiEffect_0.2.bin; no GitHub releases returned | The linked binary was not fetched; no verified code ↔ binary/version correspondence. |
| CRCLTR | GitHub releases v1.0.0 25 January 2024 (Brisbane); v1.0.1 26 January 2024 (Brisbane) | Source-permission gate remains. |
| Smack | Latest [release record v0.4.1](https://github.com/timncox/smack-versio/releases/tag/v0.4.1), 21 August 2026 (Brisbane); release source tag `1964a27489f41c136e924b1bdc66210341a0e690` | Tagged README still claims “never run on hardware”, while engine comments and newer release descriptions imply hardware use. Source/release drift must be reconciled. |
| Hillside | Releases 0.1-Alpha, 0.5-Alpha, 0.7-Alpha; [latest 0.7-Alpha](https://github.com/kuttor/Versio--The-Hillside-Slicer/releases/tag/0.7-Alpha) published 25 March 2026 (Brisbane) | Current README still labels 0.6-alpha/96 kHz; actual current setup selects 48 kHz/256. Don't mix revisions. |
| Resilio | Latest [release record v2026.10.07-0671d22](https://github.com/jeffebauer/resilio-versio/releases/tag/v2026.10.07-0671d22), 7 October 2026 (Brisbane); source HEAD in ledger is later | Versioned current core must be compared with intended released sound. |
| Pyros | Publisher states v1.0 April 2026 | Desktop source rights not granted. |
| Kickforce | README changelog v1.0.0, v1.1.0, v2.0.0 | Dates/source unavailable; restrictive binary terms. |

GitHub publication dates above are converted from the API timestamps to Australia/Brisbane. Date-only publisher changelog labels retain the author's stated date; their timezone is not asserted. No other candidates' release history is inferred from a commit timestamp or file name.

## Source snapshot ledger

All code links resolve to these fetched revisions. They are inspection snapshots, not binary fingerprints or hardware-validation results.

| Repository | Inspected HEAD |
| --- | --- |
| [abluenautilus/AcidusVersio](https://github.com/abluenautilus/AcidusVersio/tree/ec8e429428b56da7afbd98e3a7ac29e6b6168ae6) | `ec8e429428b56da7afbd98e3a7ac29e6b6168ae6` |
| [abluenautilus/ProteusVersio](https://github.com/abluenautilus/ProteusVersio/tree/4a3efe684e598b53880086ebdb05072315071a35) | `4a3efe684e598b53880086ebdb05072315071a35` |
| [abluenautilus/SeasideModularVCV](https://github.com/abluenautilus/SeasideModularVCV/tree/bf3ea150ffa2f3a753ef60bc27a4d7db8707561b) | `bf3ea150ffa2f3a753ef60bc27a4d7db8707561b` |
| [bionoid/Clackotron](https://github.com/bionoid/Clackotron/tree/7119dbc3e7af7a6f58f4939ad96955542f7b719b) | `7119dbc3e7af7a6f58f4939ad96955542f7b719b` |
| [cubicvoid/NihilVersio](https://github.com/cubicvoid/NihilVersio/tree/8c830e2d994ccd6cce7a6e0e7fab5780163f3f12) | `8c830e2d994ccd6cce7a6e0e7fab5780163f3f12` |
| [digitalartifactmusic/PlateauNEVersio](https://github.com/digitalartifactmusic/PlateauNEVersio/tree/4218b072e7420dd788cd3c98c36b3eba445f8886) | `4218b072e7420dd788cd3c98c36b3eba445f8886` |
| [fluffyaudio/MultiVersio](https://github.com/fluffyaudio/MultiVersio/tree/52839534fe5dbb36baa6fd864aa7eec5369de4ed) | `52839534fe5dbb36baa6fd864aa7eec5369de4ed` |
| [hirnlego/repetita-versio](https://github.com/hirnlego/repetita-versio/tree/99b61f3f2227035671013bd11ebf607483434bee) | `99b61f3f2227035671013bd11ebf607483434bee` |
| [hirnlego/wreath](https://github.com/hirnlego/wreath/tree/710cd8b1704d97d1cb8a06fcf2f1c82be1caf134) | `710cd8b1704d97d1cb8a06fcf2f1c82be1caf134` |
| [jeffebauer/resilio-versio](https://github.com/jeffebauer/resilio-versio/tree/2ab71a9be56b765bbc2f666527e44cfc278a511e) | `2ab71a9be56b765bbc2f666527e44cfc278a511e` |
| [jhockman/the-archivist](https://github.com/jhockman/the-archivist/tree/752e48de23d5b795d6f69af087ccc6d12a2849f7) | `752e48de23d5b795d6f69af087ccc6d12a2849f7` |
| [KoSv/DaisyVersio_Audrey_II](https://github.com/KoSv/DaisyVersio_Audrey_II/tree/4d20e49f94d3b9e63a965d765f3df502d041a7db) | `4d20e49f94d3b9e63a965d765f3df502d041a7db` |
| [kuttor/Versio--The-Hillside-Slicer](https://github.com/kuttor/Versio--The-Hillside-Slicer/tree/f474b5085f79424a91d895b1e09efb04d933cf46) | `f474b5085f79424a91d895b1e09efb04d933cf46` |
| [Maxhodges/noise-engineering-firmware-index](https://github.com/Maxhodges/noise-engineering-firmware-index/tree/187dc43dcdaacb68420d32438a90096f87f29fba) | `187dc43dcdaacb68420d32438a90096f87f29fba` |
| [onoma2/BenderVersio](https://github.com/onoma2/BenderVersio/tree/f0f9c1919fc7562ab59e3088bc0b0fb424a1f8c1) | `f0f9c1919fc7562ab59e3088bc0b0fb424a1f8c1` |
| [onoma2/TapeoVersio](https://github.com/onoma2/TapeoVersio/tree/8f7883784c257f439406b6bb9156a614b63052a7) | `8f7883784c257f439406b6bb9156a614b63052a7` |
| [onoma2/TriwalkmaVersio](https://github.com/onoma2/TriwalkmaVersio/tree/38a6b291804f2ab0792d9207cd0fd99e98c3c0f4) | `38a6b291804f2ab0792d9207cd0fd99e98c3c0f4` |
| [s3g/crcltr](https://github.com/s3g/crcltr/tree/f7ccd030b9d36c47a00be81fb0b5f5b567961176) | `f7ccd030b9d36c47a00be81fb0b5f5b567961176` |
| [saustin2010/mpc-vst-open303](https://github.com/saustin2010/mpc-vst-open303/tree/5b391de0961a7b92bc2a4b02ce828c041d0ab5e4) | `5b391de0961a7b92bc2a4b02ce828c041d0ab5e4` |
| [schollz/_core](https://github.com/schollz/_core/tree/66ee010f822c915adb893c8c03279e30a52bd839) | `66ee010f822c915adb893c8c03279e30a52bd839` |
| [sd88me/mpc-vst-plugins](https://github.com/sd88me/mpc-vst-plugins/tree/ce6278d53091ba40127838020fc8a7887894551f) | `ce6278d53091ba40127838020fc8a7887894551f` |
| [sunskiefer/PlateauXXL](https://github.com/sunskiefer/PlateauXXL/tree/4f2e739088af2ac96bd43bf5ca8630001388ccd7) | `4f2e739088af2ac96bd43bf5ca8630001388ccd7` |
| [timncox/capicola-versio](https://github.com/timncox/capicola-versio/tree/acafccc5c22b539b6d9843496c92151d613d1537) | `acafccc5c22b539b6d9843496c92151d613d1537` |
| [timncox/smack-versio](https://github.com/timncox/smack-versio/tree/f839b2ac64f813ec00b2220eee0b41d9d170b237) | `f839b2ac64f813ec00b2220eee0b41d9d170b237` |
| [TricksterSam/CitharaVersio](https://github.com/TricksterSam/CitharaVersio/tree/01d920ae2eb79a4b614cfb32f4f5cc882e52e98b) | `01d920ae2eb79a4b614cfb32f4f5cc882e52e98b` |
| [vdo/PulsarVersio](https://github.com/vdo/PulsarVersio/tree/1d019b5fa0dcdfccaf66ba9b6ca5160c1c43cbbe) | `1d019b5fa0dcdfccaf66ba9b6ca5160c1c43cbbe` |
| [wittysalt8451/Kickforce2000-bin](https://github.com/wittysalt8451/Kickforce2000-bin/tree/df88d597c39d60372012de7c6533f8b61203da56) | `df88d597c39d60372012de7c6533f8b61203da56` |

Additional dependency evidence: Repetita pins Wreath `1662b8ccfad339f3d306fe2868b3c039698fad6c` (its buffer declarations were fetched/read); Capicola pins Heavy Light Industries upstream `f0fb61cfa7111067b4ec1a642d1b16a0910adb3b`. Full pinned dependency closure still needs audit before importing/building; a newer standalone Wreath checkout is not that pin. No repository's application source was modified.

## Follow-up documents and next actions

- [WTF detailed analysis](DUB_RUSSELL_WTF_ANALYSIS.md): archive evidence, controls and source-access gate.
- [Source/license matrix](VERSIO_SOURCE_LICENSE_MATRIX.md): permissions, counts and release obligations.
- [MPC portability](VERSIO_MPC_PORTABILITY.md): candidate-specific rate/memory/realtime/UI issues.
- [Two rankings](VERSIO_PHASE2_RANKING.md): fastest proof versus performance value and first full port.
- [Contact drafts](DEVELOPER_CONTACT_DRAFTS.md): verified channels and unsent requests.

Original Phase 1 files remain unchanged on [PR #1](https://github.com/carballocba/MPC-EURO-/pull/1). Phase 2 branches from the existing empty main base, so this PR adds only six research/ files and does not merge/copy Phase 1 into main or change the repository's default branch.
