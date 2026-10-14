# Phase 2: speed versus musical value

Research date: 14 October 2026. These are engineering/feature-fit judgments from source and publisher descriptions, **not listening tests or MPC CPU measurements**. Candidate categories and rights gates: [source/license matrix](VERSIO_SOURCE_LICENSE_MATRIX.md). A high musical ranking does not authorize copying unavailable DSP.

## Ranking 1 — fastest safe proof of concept

“Safe” here means an auditable source grant, small dependency scope and bounded host-integration work. It does not mean a crash-proof or legally certified VST2 release. Estimates are focused engineer-weeks for an experienced C/C++ audio developer **after** a shared wrapper baseline; add roughly **1–3 weeks** for necessary float/realtime/state/build infrastructure, with device access/legal review additional calendar dependencies. No implementation begins under this task.

| Rank | Candidate | Why / effort / essential gate |
| --- | --- | --- |
| 1 | **_core BeatRepeat** (extra non-Versio comparator) | Small C mono effect, ~46KB state, no storage worker or large captured-media persistence. ~1–2 weeks adapter/DSP hardening. Resolve fixed-point undefined behavior/creation failure, document approximate crossings and mono wet image. |
| 2 | **Resilio core** / A | Native stereo C++17 engine, existing prepare/process/tempo/gate/parameter table, MIT core separable from JUCE. ~2–4 weeks. Profile coefficient transitions and verify chosen core version/sound, memory and sample-rate parity. |
| 3 | **Capicola portable core** / A | Existing rate/block/instance adapter and fidelity-test design. ~2–4 weeks. AGPL source closure, ~48MiB rings and worst keyframe cost. More musical novelty than a second generic granular cloud. |
| 4 | **Smack core** / A | Existing stereo C engine and Move host API; many original performance effects. ~3–5 weeks for a bounded proof, more for faithful media recall. Reconcile48k/44.1k, recorder protection, source/tag drift and control cost. |
| 5 | **Proteus internal voice** / A | Small sequence/voice; related VCV sequencer reference. ~2–4 weeks. Instance RNG/preallocation; internal sound avoids outgoing-MIDI host limitation. |
| 6 | **Repetita/Wreath** / A | Reusable stereo engine, MIT, rich loop behavior. ~3–5 weeks proof, longer for recorded-media recall. Four global buffers, large clears and rate capacity are more work than they look. |
| 7 | **Audrey II** / A | Separable feedback/string Engine. ~3–5 weeks. Allocator, DSP dependencies and feedback extremes need qualification. |
| Reference | **Acidus/Open303**, **Plateau**, **Rings** / E(core) | Existing MPC DSP implementations make another baseline port unnecessary. Evaluate a distinctive control/sonic gap first, then reuse appropriately licensed working code. |
| Not eligible yet | **WTF!**, **FRGMNTS**, **Multi**, **Hillside**, **Pulsar**, **CRCLTR**, **Cithara**, restricted Gen/binary projects | Source/license/runtime gates prevent a sound delivery estimate. Cithara has a project GPL grant but unknown generation/runtime closure. No “two-day binary port” guesses. |

BeatRepeat is first by **integration speed**, not by breadth of stereo performance. Acidus could be technically easy from original Open303, but duplicating an existing playable MPC engine is not an efficient proof for this project's creative goal.

## Ranking 2 — highest potential musical value for experimental live performance

Criteria: immediate punch-in/capture gestures, rhythmic destruction, variation with controllable seed/probability, reverse/varispeed, stereo texture, clock/tempo relevance and expressive Q-Link macros. Published feature scope is ranked separately from source eligibility. Numbering is a **subjective feature-fit order**, not a finding that a blocked processor sounds better than a tested one. Unavailable internals and lack of audition reduce confidence.

| Rank | Candidate | Musical fit / qualification |
| --- | --- | --- |
| 1 | **Smack** / A | Continuous retrospective capture + seed/order/density and per-slice effects including repeats, tape stop/start, reverse, freeze/scatter/pitch. Closest licensed engine to live break destruction. Source lineage and recorder/clock semantics must be preserved. |
| 2 | **WTF!** / C — conditional only | Official stereo Granular/Repeat/Cloud, probabilistic punch-in, VAR and contextual position/pitch/amplitude controls. Extremely relevant, but no DSP source or reuse license; not an authorized build recommendation. |
| 3 | **Repetita/Wreath** / A | Stereo loop start/length, reverse/varispeed, freeze/overdub and feedback coloration offer a coherent performance instrument, not just isolated effects. Requires proper buffer/media handling. |
| 4 | **Capicola** / A | Transient-driven stretch/pitch keeps rhythmic anchors while deforming audio; internal followers drive modulation. Distinct from ordinary granular clouds; source layer already host-friendly. |
| 5 | **FRGMNTS** / D — conditional only | Serial stutter, stop/reverse tape motion, DJ filter and wash are highly performable. Source unavailable and redistribution explicitly restricted. Seek a separate grant; don't replicate published DSP from a binary. |
| 6 | **Hillside** / B — conditional | Slots, slices, independent stretch/pitch, gate/crossfader, overdub and merge provide strong sample-performance scope. Source license absent and96k/48k version inconsistency needs resolution. |
| 7 | **MultiVersio** / B — conditional | Lo-fi, microloop, asymmetric delay and spectral modes could yield a distinctive bank of manipulations. Main-program license and tightly coupled firmware architecture prevent immediate reuse. |
| 8 | **Resilio** / A | Dub spring throws, worn clocked tape echo, tone/hold/duck and drive fit live resampling/hip-hop. Less direct slicing than the leaders, but strong stereo musical value and a much smaller persistence scope. |
| 9 | **BeatRepeat** / licensed comparator | Direct glitch gesture with predictable small resource footprint. Narrower, mono wet algorithm and zero-crossing approximate timing are real creative limits. Useful proof and eventual focused effect. |
| 10 | **Acidus/Open303** / E(core) | Expressive acid bass via slide/accent/resonance/envelopes; useful complement to manipulated breaks. The core plus Devilfish already exists for MPC; range-mode automation alone needs a differentiation case. |
| 11 | **Proteus** / A | Seeded evolving melodies with internal synthesis, good generative counterpart; less central to the user's incoming-sample manipulation priorities. |
| 12 | **Audrey II** / A | Noisy feedback/string texture and resonant drones; potentially strong transitions, but feedback safety and less direct rhythm control reduce first-port priority. |

Pulsar and Cithara are interesting texture/synthesis leads, but rights/runtime gates and lesser direct break-manipulation fit keep them outside this performance shortlist. Plateau is a proven reference rather than another necessary reverb. VNY404/Pyros/Stray/Clackotron/Kickforce could be appealing effects/instruments, but no executable source path is established for this project; their names are not evidence of implementable DSP.

## Explicit eight-candidate comparison

| Candidate | Fast proof | Live-performance value | Source/permission | Decision now |
| --- | --- | --- | --- | --- |
| BeatRepeat | #1; small mono C core | #9; focused stutter, limited stereo/metrical precision | GPLv3 source; matching-source and VST2 review | Best small host calibration proof; not the richest product. |
| WTF! | Not scoped | #2, conditional; three-mode stereo probability/grains/repeat | C; binary-only archive, no grant | Draft source request; no coding from binary. |
| FRGMNTS | Not scoped | #5, conditional; four serial immediate effects | D; explicit restriction | Seek a separate grant; no “free firmware means open” shortcut. |
| Smack | #4; medium work | #1; richest licensed rhythmic-destruction candidate | A; MIT | Flagship sample/glitch port after a bounded host proof. |
| Capicola | #3; existing portable layer | #4; transient-preserving stretch novelty | A; AGPLv3 | Strong granular follow-on; profile memory/complexity and fulfill source terms. |
| Repetita/Wreath | #6; buffer/realtime/media work | #3; coherent stereo live looping | A; MIT | High-value stereo looper; don't underestimate state persistence. |
| Acidus | Existing core reference | #10; bass-synth complement | E(core); MIT Acidus, GPL MPC derivative | Reuse existing Open303; only new range/gesture differentiation merits work. |
| Multi | Not scoped until full grant | #7, conditional; nine-mode source exists | B; main-program license incomplete | Request license; select a distinctive subset instead of porting whole tangled firmware. |

## Top five actionable port recommendations

In performance-first order, with the fastest proof included as a concrete foundation:

1. **Smack:** seeded break destruction/capture.
2. **Repetita/Wreath:** stereo varispeed/freeze/overdub looper.
3. **Capicola:** transient-keyframe stretch/pitch effect.
4. **Resilio:** standalone stereo dub spring/tape-echo performance effect.
5. **BeatRepeat:** focused small glitch processor and host validation proof.

These are source-authorized directions, not measured-ready MPC products. WTF!/FRGMNTS remain high-value outreach targets outside the actionable list. Don't trade away source legitimacy for musical appeal, but don't confuse the first passing host proof with the best eventual plugin either.

## First complete plugin: proposed Phase 2 decision

**Resilio is the recommended first full stereo performance port if the owner wants a meaningful product rather than only the smallest technical proof.** Its existing native core, tempo/gate API, MIT boundary and relatively small memory avoid the main loopers' capture persistence and _core's mono limitation. It still offers substantive musical controls—throws, worn echo, hold/duck and tone—worth the moderate extra work. Smack remains the best flagship break-manipulation target once the host layer is qualified.

This complements the unchanged Phase 1 BeatRepeat recommendation: BeatRepeat remains the quickest host-only proof; the newly discovered Resilio route makes a stronger first complete stereo-effect case. The owner should explicitly choose/approve scope before any coding.

Proposed Resilio implementation milestones, **not executed**:

1. Pin intended source/release voicing; audit core/ParamSpec/license closure and independent naming. Compare HEAD with the intended released sound and dependency pin.
2. Reuse Tank + ParamSpec directly; omit JUCE, offline file helpers and firmware. Prepare at actual host rate; check allocations and full pool/tape sizing.
3. Adapt the existing MPC ABI to audio-owned float DSP, stable parameters/readback and bounded event queues. Preserve smoothed32-sample control behavior; avoid wrapper mutex/int16 dry quantization.
4. Map host BPM plus validity/fallback, sample-offset throw/button/gate and optional MIDI; generate original One Q-Link skin. Save scalar state; document transient tails and unheld restore.
5. After coding approval, run existing/native reference tests plus wrapper tests and ARM ABI checks. Before any device install, obtain separate approval for non-conflicting package/registration. Record exact One/Hakai load, stereo/automation/recall and worst CPU/RSS evidence.

If source qualification exposes excessive coefficient spikes or incompatibility, reassess instead of silently changing the original sound. No missing source/runtime case should be “solved” by reverse engineering or rewriting proprietary DSP.
