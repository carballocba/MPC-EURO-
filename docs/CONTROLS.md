# Performance controls and Q-Links

Feed BeatRepeat audio for at least a few waveform cycles before triggering. Start with modest monitor level; gain is not limited. For short glitches, leave Gate OFF and tap Punch. For sustained stutter, latch Gate ON, adjust mix/output, then release Gate. Turn Length while repeating to prepare the **next** window; it does not resize the current loop.

| Index / stable key | Control | Behavior / default | Q-Link JSON slot |
| --- | --- | --- | --- |
| 0 / length | Length | Approximate 5–450 ms; default 100 ms; next repeat entry | 13 |
| 1 / gate | Gate / LATCH | OFF/ON latch; default OFF; releases with core fade | 9 |
| 2 / mix | Dry/Wet | 0–100%; default 100%; smoothed | 5 |
| 3 / gain | Output | −24 to +12 dB; default 0 dB; smoothed | 1 |
| 4 / punch | PUNCH 450MS | ON fires a 450 ms audio-time request; OFF cancels; auto returns to READY | 14 |
| 5 / bypass | Bypass | Smooth unity stereo dry; default OFF | 10 |
| 6 / active | Repeat status | Read-only CAPTURE/REPEAT | none |
| 7 / status | Engine status | Read-only CAPTURE/REPEAT/PRIMING/BYPASS/RATE! | none |

The Q-Link **slot numbers** follow the community's bottom-up column ordering; the original MPC One has four physical knobs and host bank selection. Exact bank navigation/labels must be checked on hardware. Parameters 0–5 are automatable; 6–7 are not. UI, Q-Link and automation target the same VST parameters. Names, display values and read-only bindings are tested against the compiled native library.

Gate and Punch combine with OR. Canceling Punch while Gate is ON leaves the latch active. Punch duration measures processed audio time; it is neither host-beat quantized nor a press-and-hold button. After its timer expires, core/wrapper fades take a few more milliseconds. Fast pre-render commands coalesce, with the latest command winning. While silence/DC has insufficient crossings, Gate/Punch remains requested and status shows PRIMING; a timed Punch can expire without creating a loop.

Touch knobs have 230×170 component areas, with vertical drag and the community's numeric-overlay gestures. Punch is a 370×68 native toggle button, Gate has 170×65 OFF/ON segments, and Bypass 112×65 segments. Device gesture behavior is host-defined. A dedicated Active readout and conditional cyan/magenta text show capture/repeat; Engine distinguishes priming, bypass and invalid rate. Readouts have no touch actions.

Only Length, Dry/Wet, Output and Bypass survive **plugin chunk** recall. Gate/Punch and captured audio reset for safe project loading. Host-side per-parameter project handling must still be tested. There is no MIDI, beat-clock/transport synchronization, external CV/Gate mapping or direct access to the MPC's CV outputs. Those would require a separately scoped host capability investigation.
