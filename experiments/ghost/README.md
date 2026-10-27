# GHOST C0 — isolated offline event prototype

Original C11 prototype on `codex/ghost-discovery`, approved after Phase A. It links the **unchanged** `src/engine.c` into an offline harness. It is not a VST, does not register a UID, and never loads or writes MPC.settings. No SSH, deployment, GUI rebuild, ARM payload, preset format or BeatRepeat parameter changes.

Run the complete local validation and demo generation with one command from anywhere:

```sh
"./experiments/ghost/run.command"
```

Needs local C compiler, make, Python3 and nm; uses existing native BeatRepeat validation binaries, so this checkout must already contain the validated RC1 build. Output is only `build/ghost-prototype/`. It refuses a changed protected baseline instead of rebuilding it. macOS ASan/UBSan run with LeakSanitizer disabled; no claim of leak or thread-race coverage on unsupported configurations.

## Listen first

- `input.wav`: 12seconds of original synthetic stereo drums/tonal audio, no processing.
- `manual.wav`: same input with scripted manual repeat, active Length/Break changes, Capture/Freeze and Clean.
- `ghost.wav`: same input; Ghost starts at1s, autonomously chooses bounded Length/Break, Capture/Freeze and repeat leases; Clean at10s. First second and last second equal the input exactly after16-bit rendering.
- `events.csv`: opportunity timestamps, accepted events, parameter values, freeze leases and actual capture results. An active event is a scheduling decision, **not a claim that a take is already audible**.
- `validation.json`, `tests.txt`, `sanitizers.txt`, `benchmark-native.json` and baseline regression logs: actual evidence.

All WAVs are44.1kHz/16-bit/stereo, identical source and seed, conservative levels with no full-scale samples. No captured audio is persisted as a plugin preset. These files demonstrate an offline experiment; neither the sound nor gestures have been tested on physical MPC hardware.

## Implemented in this block

| Component | Contract |
| --- | --- |
| Ghost ON/OFF | OFF removes only automatic leases, preserves manual Gate/Freeze and values. ON starts a new deterministic opportunity sequence at current clock position. |
| Distance | Beat divisions/multiples1/64..64beats or free5..60000ms; optional bounded jitter≤40%. Absolute accumulation avoids per-interval sample rounding. |
| Density | 0..16 distributed opportunities in a16-cell Euclidean-style cycle, with rotation. Independent of acceptance probability. |
| Probability | Global acceptance chance0..1 plus per-destination chance. Probability1/0 are exact endpoints. |
| Duration / Rest | Duration in milliseconds, capped at85% of next nominal/jittered interval at event start. Rest in milliseconds excludes subsequent auto events; it does not mute manual processing. Tempo changes leave current ms duration/rest intact. |
| Random Length | MS5..450, user min/max/depth/probability/divider and optional ramp. Effective region still clamped by existing buffer engine. |
| Random Break | 0..1, user min/max/depth/probability/divider and optional ramp. Does not alter manual/base Break. |
| Random Capture | One impulse per selected event, cooldown≥5ms (default100ms). Attempt/acquisition reported separately; no repeated per-sample trigger. |
| Random Freeze | Temporary automatic request; expiration never writes the manual Freeze parameter. |
| Manual override | Length/Break/manual-OFF requests win for the remainder of the current event; cleared at next **accepted** event, not a skipped opportunity. A manual Freeze ON remains ON because it is a separate base request. Explicit release API also provided. |
| Clean | Highest priority at a shared boundary; disables Ghost, clears manual Gate/Freeze/Run and pending capture, returns dry through existing5ms tail. Preserves take, Mix and other base values. |
| Seed / Reset | Counter-based, destination/domain-separated decisions; Reset replays decisions from current position while preserving audio/manual values. Generation tokens remain monotonic to invalidate deferred old captures. |
| Transport | Simulated clock API: stop cancels autonomous processing and freezes its beat clock; resume/seek starts from new position without catch-up bursts. Seek keeps decision index; explicit Reset repeats it. Invalid tempo falls back to120BPM visibly. No VST clock hookup yet. |
| Audio bridge | Existing raw Engine plus stereo dry/wet,2ms Mix and5ms activation/release ramps. No new effect algorithm or voice. |

MS randomization does **not** relabel or override existing Grid Length: in Grid mode Random Length is skipped, while the manual Grid remains intact. Grid-destination selection/range UI is a later integration task. Boolean actions reject meaningless smoothing/depth/ranges. A base value outside a continuous random range is clamped only for that temporary event; Depth0 leaves base unchanged.

Every mutator validates the complete candidate before writing state. This API is **single-owner**, not a cross-thread mailbox. GUI/MIDI/host snapshots and preset serialization remain future work. No claim of thread safety for concurrent calls.

## Timing and resource bounds

`ghost_tick` advances once per sample, schedules at most one opportunity and four destination decisions. Continuous ramps are applied by the existing engine at its32-frame control cadence; event start/end/manual commands force an immediate control update. The adapter uses an absolute sample cadence, so changing process block sizes does not move control polling. Trace storage is caller-supplied and bounded; excess telemetry increments a counter and never changes musical decisions.

Capture defers if the two-bank quantized-recapture path still pins the live bank as an audible source. One pending command maximum; automatic pending commands expire with their event/generation; Clean drops pending commands. A manual empty-history Capture may fail to acquire and reports that fact; Repeat/Freeze priming still follows the original engine. Continuous live recording continues through dry/rest.

DSP objects import no heap, filesystem, network, thread, logging or locking functions; the validation runner audits their symbol imports. Initialization allocates/zeros storage before render; the harness owns allocation, synthetic input, timing calls, CSV and WAV I/O outside `ghost_audio_process`. There is no Motion matrix, Chaos macro, Dice, Lock memory, LISTEN, feedback, granular or new GUI in C0.

The scheduler is400bytes in the tested macOS build; the complete raw-Engine adapter is3,073,128bytes. It excludes the legacy VST core/notifier and is **not** a new estimate of the complete plugin's RAM. See validation JSON for exact build sizes.

## Validation and limits

21 native acceptance groups cover malformed configurations, endpoints/statistical chance, independent streams/ranges/depth, cooldown/rest, manual ownership, Clean priority, clock fallback/seek/tempo, reset, manual Grid,30minute drift, block-size invariance, reference transparency, capture/freeze priming, quantized-bank protection, aliasing and bounded telemetry. ASan/UBSan pass the same groups. Existing prebuilt BeatRepeat tests are rerun:19Cgroups, ABI smoke and28functional VST tests.

OFF transparency is exact against the unchanged **raw Engine + equivalent adapter ramps**. It is not a claim that a new VST wrapper has been compared: none was built. DSP/state/plugin source, skin assets, ARM binary, native RC1 library, package and rollback hashes are checked before/after.

48 native timing cases cover16/44.1/48/96kHz,32/128/512frames and four scenarios (OFF+manual repeat; Length/Break; Capture/Freeze; combined). They include desktop scheduling and timer overhead. Any observed maximum exceeding a nominal deadline remains reported, including the OFF baseline; never discard outliers or claim ARM headroom from Mac results. No formal WCET, XRUN count, real CPU utilization, TSan, ARM timing or physical test is established.

An earlier exploratory native run observed a2.016ms maximum in the Ghost-OFF baseline at44.1kHz/32frames (nominal deadline0.7256ms). Its observed summary is retained in `benchmark-observations.json`; the full earlier table was superseded by the final validation run. Cause was not isolated; wall time includes desktop scheduling. The later run does not erase that observation or establish real-time guarantees.
