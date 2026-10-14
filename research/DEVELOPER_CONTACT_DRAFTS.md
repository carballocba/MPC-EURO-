# Developer contact drafts — unsent

Research date: 14 October 2026. **No messages, forms, issues, DMs or emails were sent.** These are reviewable drafts, not outreach authorization. Send only after the project owner approves recipients and wording. Source access, reuse permission, third-party rights and technical clarification must remain separate.

## Channels and required follow-up

| Candidate / recipient | Channel evidence | What to ask |
| --- | --- | --- |
| WTF! / DUB-Russell | Official [inquiry form](https://2020.dubrussell.com/contact/), linked [Instagram](https://www.instagram.com/_dubrussell/) and [X](https://x.com/dubrussell) | Licensed native/generated source, runtime/dependencies, v1.0/v1.1 provenance, other Versio firmware/archives. No email invented. |
| FRGMNTS + VNY404 / Yota Mori (Acidclank) | [FRGMNTS page](https://acidclank.gumroad.com/l/frgmntsversio) explicitly asks for [Instagram DM](https://www.instagram.com/y0ta1993/) or its linked [feedback form](https://forms.gle/ngK24WChxN5HPPK97); [Linktree](https://linktr.ee/acidclank) | Separate open-source adaptation/redistribution grant and source/dependency access. Existing no-redistribution terms remain until changed. |
| MultiVersio / Paolo Ingraito, fluffyaudio | [Author README](https://github.com/fluffyaudio/MultiVersio/blob/52839534fe5dbb36baa6fd864aa7eec5369de4ed/README.md); [GitHub issues](https://github.com/fluffyaudio/MultiVersio/issues) enabled in repo metadata | Explicit main-program license, MIT-derived component provenance and matching release pin. |
| CRCLTR / s3g | [Project](https://github.com/s3g/crcltr), [issues](https://github.com/s3g/crcltr/issues) enabled | Original patch license, permitted source/binary redistribution and lawful export/runtime. |
| Tapeo/Triwalkma/Bender / onoma2 | Original [GitHub account](https://github.com/onoma2) and project issue pages | Author code/patch rights plus exact export/runtime terms; don't assume author controls Cycling '74 code. |
| Gen runtime / Cycling '74 | Bundled genlib.h names `licensing@cycling74.com`; [license evidence](https://github.com/onoma2/TriwalkmaVersio/blob/38a6b291804f2ab0792d9207cd0fd99e98c3c0f4/gen_dsp/genlib.h) | If Gen candidates proceed, obtain a suitable export/runtime rights path compatible with the intended open-source distribution. This is a separate owner. |
| Hillside / kuttor | [Original repo](https://github.com/kuttor/Versio--The-Hillside-Slicer); [issues](https://github.com/kuttor/Versio--The-Hillside-Slicer/issues) enabled | Source license and correct0.7-alpha code/rate/timer revision. |
| Pulsar / vdo | [Original repo](https://github.com/vdo/PulsarVersio); [issues](https://github.com/vdo/PulsarVersio/issues) enabled | Explicit engine/firmware source license and component provenance. |
| Clackotron / bionoid | [Repo](https://github.com/bionoid/Clackotron); [issues](https://github.com/bionoid/Clackotron/issues) enabled | DSP source corresponding to binary/manual; confirm supplied source falls under included MIT license. Not automatically a new permission request. |
| Kickforce 2000 / wittysalt8451 | [Repo](https://github.com/wittysalt8451/Kickforce2000-bin); [issues](https://github.com/wittysalt8451/Kickforce2000-bin/issues) enabled | Separate source/adaptation/redistribution grant beyond personal-use terms. |
| Archivist / Jason Hockman, Detuned Transmissions | [Author repo](https://github.com/jhockman/the-archivist) | Ask via author's published project contact/available GitHub channel after verifying it; no private address invented. Separate grant required. |
| Pyros / Audiority | Official [contact page](https://www.audiority.com/contact/) linked by [product](https://www.audiority.com/shop/pyros-versio/) | Whether a legitimately reusable licensed DSP subset is available; do not request a copy of the proprietary app as a shortcut. |
| Stray Drum / Jasmine & Olive Trees | [Firmware page](https://jasmineandolivetrees.com/pages/stray-drum-versio-firmware) links [contact form](https://jasmineandolivetrees.com/pages/contact) | Source access/license and current beta version/control status. |
| Filterbank/Rings / ericxgao, Megatron / joel.gilardini | [Index](https://github.com/Maxhodges/noise-engineering-firmware-index/blob/187dc43dcdaacb68420d32438a90096f87f29fba/README.md) supplies usernames and discussions; no official contact independently verified | Verify original identity/contact first. Do not create a guessed recipient or use a mirror's permission. Rings is low priority given existing MPC core. |
| Reticulum / unknown, Praetereo / Negative Theology | [Reticulum thread](https://modwiggler.com/forum/viewtopic.php?t=280196), [Praetereo thread](https://modwiggler.com/forum/viewtopic.php?t=276033); both denied retrieval | Obtain accessible author documentation/contact first; no correspondence can be prepared to a confirmed individual yet. |
| Smack / Tim Cox | [Source](https://github.com/timncox/smack-versio/tree/f839b2ac64f813ec00b2220eee0b41d9d170b237) and releases/issues | Optional clarification only: reconcile current source/v0.4.1 and stale “never on hardware” README. MIT port permission already exists. |
| Resilio / Jesse Bauer | [README](https://github.com/jeffebauer/resilio-versio/blob/2ab71a9be56b765bbc2f666527e44cfc278a511e/README.md) links issues and personal site | Optional version/voicing/timing advice and attribution. MIT core permission already exists; no redundant permission gate. |

The permission accounting is **19 requiring new/clarified reuse grants**, plus **1 source-only request (Clackotron)**. Cithara may need generator/runtime licensing clarification, not a new blanket grant for its GPL patches. Already-licensed A candidates do not require a courtesy reply to begin approved source-based work, but implementation approval from the project owner is still pending.

## DUB-Russell — WTF! and other Versio work

**To:** official inquiry form. **Subject:** Source/licensing inquiry: WTF! Versio and an independent MPC research project

Hello DUB-Russell,

I'm researching an independent open-source project, MPC-EURO-, for performance-oriented audio plugins on the original Akai MPC One running Hakai 3.9.1 (Linux ARMv7).

WTF!'s granular, repeat and cloud modes look especially relevant to live sample manipulation. We have read your official manual and the v1.1 notes, and one of us has downloaded WTF-1.1.bin. We understand that a firmware download does not grant source or adaptation rights. We have not reverse-engineered or ported it.

Would you be interested in making the WTF! DSP source, or a smaller reusable engine/export, available under an open-source license that permits modification and source/binary redistribution? If source is already public, could you point us to the authoritative repository and the revision corresponding to v1.1?

It would also help to understand the authoring framework, third-party/export runtime licenses, sample rate/block assumptions, buffer and grain limits, trigger/BPM behavior, and any changes needed to separate the engine from Versio hardware. We would use independent plugin branding, preserve required attribution, and keep VST2 host/distribution review as our responsibility. We won't reuse names, logos or proprietary parts without an appropriate grant.

Are there any other Versio firmwares, releases, archives or development notes you've published or would like us to include? At present we found only WTF! in your official resources section.

We are at research stage and will not implement anything unless both the project owner approves and a legitimate source/licensing route exists. No pressure if you prefer to keep the DSP private. Thank you for the clear manual and for considering the inquiry.

Best regards,
[Your name]
[Optional link to the research PR]

## Acidclank — FRGMNTS and VNY404

**To:** publisher-linked Instagram DM or approved feedback channel. **Subject:** Permission/source inquiry for an independent MPC DSP port

Hello Yota,

I'm researching an independent open-source MPC plugin project. FRGMNTS' Stutter, tape motion, DJ filter and WASH controls are a particularly good fit for our live sample-manipulation goals; VNY404's wow/flutter and ducking are interesting too.

We read the product pages and understand that unauthorized redistribution/commercial use is prohibited. We have not copied, reverse-engineered or ported either firmware. Would you consider a separate open-source license and source/engine access permitting independent adaptations and source/binary redistribution?

If so, could you identify the authoring framework, export/runtime/dependency terms, authoritative version/revision and required attribution? We would use independent names/artwork. For FRGMNTS, we'd also like to confirm the v1.2 clock/bypass behavior, since the page says tap tempo was removed.

There is no obligation to share private code. If such a license isn't suitable, we'll keep these as documented musical references rather than implement your DSP. Thank you for considering it.

Best regards,
[Your name]

## Paolo Ingraito / MultiVersio

**To:** original repository's issue channel after approval. **Subject:** MultiVersio main-program license and source provenance

Hello Paolo,

We found your MultiVersio repository while researching independently packaged audio plugins for the MPC One. Thank you for publishing the code. Your README welcomes improvements, and several DSP headers have explicit MIT notices, but we couldn't find a complete license governing MultiEffect.cpp and your integration/original algorithms.

Could you clarify whether the project may be adapted and redistributed as open-source source and plugin binaries, and add an explicit license if that is your intent? We would preserve all notices and independently audit any third-party components. It would help to know which source revision matches the MultiEffect_0.2 release, and whether any dependencies/algorithms have additional restrictions.

Our interest is particularly the lo-fi/microloop/rhythmic processing, not another port of already available Mutable modules. We have not compiled or implemented anything from your code. We would use original plugin branding and acknowledge your work as required.

Best regards,
[Your name]

## CRCLTR / onoma2 generated-code projects

Adapt this draft separately for s3g's CRCLTR or onoma2's Tapeo/Triwalkma/Bender; do not send an inaccurate shared description.

**Subject:** Source and export-runtime licensing for [project] adaptation

Hello [developer],

I'm researching an independent open-source audio plugin adaptation of [project]'s performance DSP for Linux ARMv7 on the MPC One. We would prefer to reuse your original patches/generated engine with proper attribution rather than rewrite the DSP.

For [CRCLTR/Tapeo], we couldn't find a complete project reuse license. For [Triwalkma/Bender], we found GPLv3 at the root but a non-commercial-only Cycling '74 notice in the bundled Gen runtime. Could you clarify the original patch/code grant and the exact lawful export/runtime path for a plugin permitting source and binary redistribution? Any third-party permissions would need to come from their respective owners.

If a suitable open-source path exists, please identify the source/export version, required notices and intended naming. We have not compiled, reverse-engineered or ported the firmware. If reuse rights are unavailable, we'll retain it only as a documented reference.

Best regards,
[Your name]

## Hillside / Pulsar — source available, license missing

**Subject:** Open-source adaptation license for [project]

Hello [developer],

We are researching [project] for an independent MPC ARMv7 audio-plugin project. The source is promising, but we couldn't find a license covering the main engine/firmware. Would you clarify whether modification and source/binary redistribution are permitted, and publish an explicit project license if so? We will preserve attribution and audit each dependency.

For Hillside specifically: which revision should be considered authoritative? The current README describes96k/0.6-alpha, while the source selects48k/256 and the release list has0.7-alpha. We'd like to understand the intended sample-rate/timer behavior without guessing or changing your code.

For Pulsar specifically: we'd appreciate confirmation of table/algorithm provenance, separate sync/ring-mod output behavior and any additional component licenses.

We are doing research only and have not built or ported it.

Best regards,
[Your name]

## Clackotron — request the missing source

**Subject:** Clackotron DSP source corresponding to the published firmware

Hello,

We found Clackotron's manual and MIT license while researching independent MPC plugins. The repository currently appears to contain the README, LICENSE and firmware binary but no DSP source, despite its source-build instructions.

Is there an authoritative source repository/archive for the current firmware? Could you identify the matching revision and confirm the included MIT grant applies to the supplied DSP code, along with any separate third-party notices? We are particularly interested in the LPG/envelope/stereo processing, but won't extract it from the binary.

This is a source-access question rather than an assumption that your existing MIT grant needs another permission. No implementation has begun.

Best regards,
[Your name]

## Other restricted or binary-only candidates

Use only after identifying a verified channel/owner. Applicable projects: Archivist, Kickforce, Pyros, Stray; later verified Filterbank, Megatron, Reticulum, Praetereo and any firmware-specific Rings adapter.

**Subject:** Licensed DSP/source-access inquiry for [firmware]

Hello [verified developer],

I'm researching [firmware] for an independent open-source MPC plugin project. We understand that public availability of a firmware binary does not authorize source extraction, modification or redistribution. [If applicable: We read your restrictions and will respect them.]

Do you offer, or would you consider, a DSP source subset under a license permitting independent adaptation and source/binary redistribution? If so, please identify authoritative source/version, original and third-party rights, required notices and any naming conditions. If not, we will document it as unavailable for reuse and pursue independently licensed alternatives. We have not reverse-engineered, compiled or ported the firmware.

Best regards,
[Your name]

## Reply checklist and next action

Record the actual grant/source revision, which rights the respondent controls, dependencies/export runtime, source and binary distribution terms, attribution/name/artwork requirements and any restrictions inconsistent with the open-source goal. Keep permission correspondence separate from source; publish a grant only with suitable authorization. Source delivered under confidentiality or non-commercial-only terms is not automatically suitable for this project.

Do not treat technical advice, a download link, a polite acknowledgement or silence as permission. Reclassify only after evidence supports it. No outreach is authorized by this document; no plugin coding is authorized by a developer reply without the project owner's separate implementation approval.
