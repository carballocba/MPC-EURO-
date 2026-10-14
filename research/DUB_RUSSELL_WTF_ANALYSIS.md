# DUB-Russell / WTF! Versio

Research date: 14 October 2026. **Category C: firmware binary available; DSP source and adaptation permission not established.** The user reports having WTF-1.1.bin. That possession is not a source license, and the user's copy was not uploaded or examined in this task.

## Authoritative sources and search outcome

Primary pages actually retrieved:

- [DUB-Russell resources](https://2020.dubrussell.com/resources/)
- [WTF! manual and download](https://2020.dubrussell.com/resources/wtf/)
- [2020 product](https://2020.dubrussell.com/)
- [Official inquiry form](https://2020.dubrussell.com/contact/)
- [Current firmware ZIP](https://2020.dubrussell.com/resources/WTF-versio-firmware-1.1.zip)

The resources page lists **one Versio firmware, WTF!**, plus “Playing 2020 with Modular” and “Routing 2020 Sounds into Ableton Live with Loopback”. Those other resources concern the desktop beat machine, not separate Versio firmwares. The inspected navigation and project page link no public source repository. GitHub repository searches for DUB Russell/WTF Versio did not identify a matching authoritative source project; broad search returned unrelated “version” repositories. Google returned a JS shell, and [the supplied YouTube video](https://www.youtube.com/watch?v=c-M2nF3q-fY) returned proxy 403. A sitemap.xml request returned 404. No historical archive was successfully verified.

This is a bounded search result, **not proof that the developer has no other/private/unpublished firmware**. Ask directly through the official channel whether there are other Versio releases, archives or development notes. Do not promote a mirror, search snippet or unverified GitHub name as the author's source.

## Firmware package evidence

The public ZIP was fetched into memory and its directory metadata inspected without extracting or examining any firmware payload:

| Item | Observed value |
| --- | --- |
| Archive URL | https://2020.dubrussell.com/resources/WTF-versio-firmware-1.1.zip |
| Archive size | 59,657 bytes |
| Archive SHA-256 | `bccf3a8b9b291f607521e6c4b609c02bb778016675c19725be65155cbe57c0b7` |
| Directory entries | One: `WTF-1.1.bin` |
| Entry's declared uncompressed size | 91,036 bytes |
| Source / LICENSE / README entries | None |

The hash identifies the fetched **ZIP**, not the user's .bin, the uncompressed firmware or a source revision. No comparison with the user's file was made. No binary was disassembled, strings-extracted, decompiled, decoded, run, installed or copied into MPC-EURO-. An archive's small compressed size says nothing useful about runtime RAM/CPU or rights.

## Versions

The official changelog verifies:

- **v1.0.0:** initial release.
- **v1.1:** reduced pops when enabling/bypassing effects; refined tuning/response of Repeat parameters.

The current installation section explicitly selects WTF-1.1.bin. The manual does not state release dates or a complete historical archive. The community index associates WTF! with April 2026, but that is secondary metadata and not used as a verified release date. No source commit, source tag or build-to-binary provenance is available.

## DSP behavior and controls: publisher-described, not source-verified

The developer says the engine originated in **2020 THE SEMI MODULAR BEAT-MACHINE**. WTF! continuously captures incoming **stereo audio** into an approximately **90-second** internal buffer, then reconstructs grains. This does not establish 90 seconds of simultaneously playable loop storage or a fixed format/rate.

| Control | Granular / Cloud | Repeat | Possible MPC mapping, if licensed source is obtained |
| --- | --- | --- | --- |
| Effect Mode | Granular is basic shifting grains; Cloud softer texture | Beat-repeat-focused mode | Enum parameter with explicit stable values |
| Grain Mode | Forward; PingPong reverses halfway; Reverse | Same selectable grain-direction family | Direction enum; do not equate PingPong with stereo ping-pong delay |
| SIZE | Grain size from detected BPM | Quantized grain size | Host-tempo division or free duration, with source-identical limits |
| DIST/HOLD | Grain spacing | Hold time | Separate contextual labels or named subparameters |
| PITCH | Grain pitch | Evolution of pitch over time | Pitch / pitch trajectory; ranges unknown |
| JIT/NUDGE | Grain-parameter randomization | Position nudge | Jitter / repeat position; update timing must be verified |
| SPD/AMP | Playback speed | Evolution of amplitude over time | Speed / amplitude trajectory, not assumed time-stretch |
| VAR | Randomizes grain mode and six preceding macro parameters | Same macro family | Variation depth with saved seed/version policy |
| PROB | Probability of activation at a trigger | Same | Chance parameter; manual trigger policy kept distinct |
| Button | Hold to enable effect manually | Same | Momentary performance gate; optional MIDI note-on/off |
| TRIG | Rising edge probabilistically enables effect and supplies timing | Same | Internal host-clock/trigger bridge; effect-slot MIDI routing is unverified |

The manual says trigger intervals estimate BPM and accepts nonuniform rhythm patterns. That is **not** proof of a particular tempo-detection algorithm, jitter tolerance, clock division, PPQ accuracy or sample-accurate events. The source might interpret intervals differently from a normal quarter-note clock. A port should offer a deliberate host-sync mode while preserving original trigger-derived behavior where useful.

No exact parameter ranges, maximum simultaneous grains, interpolation/window, stereo-linking, wet/dry/feedback topology, bypass fade curve or random-seed algorithm are exposed. Do not infer them from the seven knobs or invent replacements and call the result WTF!.

## Language/framework and desktop reuse

Noise Engineering's [official custom-firmware article](https://noiseengineering.us/blogs/loquelic-literitas-the-blog/create-your-own-firmware-on-a-versio-module/) confirms Versio uses Daisy Seed/libDaisy and supports independent C/C++ development. **WTF!'s actual authoring language, DSP framework and dependencies are unknown**. It might have a native or generated engine; no evidence establishes Gen/Oopsy, Faust, Pure Data/Heavy or a specific DaisySP subset.

The existence of a 2020 desktop application means the author has related desktop DSP, **not** that a licensed Linux/ARM engine, VST2 wrapper or exact WTF! desktop port is available. The 2020 page describes a macOS beat-machine product with many engines and controls; its full app/runtime is unsuitable as a presumed lightweight MPC dependency. Request the smallest DSP export/subset and its dependency rights instead.

## MPC feasibility if source and rights are supplied

Best form: independent stereo **insert effect**, with three modes, momentary punch-in, probability/variation and tempo-aware grain/repeat controls. The performance model fits experimental hip-hop much better than a generic reverb. That musical-fit judgment uses the manual; no comparative listening or CPU benchmark was performed.

Unknowns that prevent a credible effort estimate or build plan:

1. Lawful original DSP and export/runtime license; right to modify and redistribute source/binaries under a usable project license.
2. Native/generated dependencies, architecture intrinsics, embedded SDRAM/ADC/GPIO glue and instance ownership.
3. Internal sample rate/block size, active-grain limits, buffers, algorithmic latency, clock behavior and parameter-update cost.
4. Whether project recall includes captured audio, RNG/history or only knobs. Source ownership and a worker-backed media policy would be needed for persistent captures.
5. Compatible independent branding; permission to use WTF!/DUB-Russell names or graphics must not be assumed.

Illustrative PCM arithmetic **only**: 90 s stereo at 44.1 kHz would require 15.876 MB at int16 or 31.752 MB at float; at 48 kHz float it would require 34.56 MB. Those are possible representations, **not measured WTF! buffers**. Additional voices, staging, freeze copies and feedback memory could change requirements substantially. A 91 KB executable size cannot answer this.

A future adapter would preallocate instance-local buffers, replace hardware trigger/CV with parameters/internal events, preserve native stereo DSP, map BPM/PPQ only after checking valid host flags, and move file/state serialization off audio. Keep Q-Link controls simple and mode-aware. Do not assume access to the MPC's physical CV/Gate outputs. Existing community VST2 wrapper limitations—mutexes, int16 conversion and fixed sample rate—still need resolution.

**Estimate: unscopable before source.** If a clean native, instance-safe engine is supplied, a several-week adapter could be plausible; if proprietary generation/runtime or an entire app is required, the scope and permission path may be unsuitable. Neither is a current promise.

## Rights and next action

No open-source/adaptation license was found on the firmware page or in the archive. Copyright footer/product availability does not supply one. Marking this C rather than D means an explicit broad prohibition was not established here; it does **not** authorize porting. Obtain written permission and auditable source/dependency terms first. Do not reverse-engineer the downloaded .bin as a substitute.

The official contact is [the inquiry form](https://2020.dubrussell.com/contact/). The same site links [Instagram @_dubrussell](https://www.instagram.com/_dubrussell/), [YouTube @dubrussell](https://www.youtube.com/@dubrussell) and [X @dubrussell](https://x.com/dubrussell). No email address was invented. An unsent request asks for source, versions, reusable runtime/export rights, attribution and branding, and other Versio projects: [DEVELOPER_CONTACT_DRAFTS.md](DEVELOPER_CONTACT_DRAFTS.md#dub-russell--wtf-and-other-versio-work).

While waiting, use **Smack** for licensed seeded beat destruction, **Repetita/Wreath** for live varispeed/freeze, or **Capicola** for transient stretch. They are independently licensed alternatives, not replicas of the unpublished WTF! algorithm. A permission reply should trigger source audit and reclassification before any implementation proposal.
