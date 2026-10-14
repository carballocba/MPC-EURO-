# BeatRepeat — first musical hardware trial

**This trial has not been performed.** Start only after the read-only compatibility check and a separately approved installation in INSTALL.md. It is an experimental effect for a disposable project, not a live-show tool yet. A successful Actions build proves the tested package, not Hakai operation.

## Prepare the room and project

Use low speaker/headphone volume; keep a physical volume control within reach. Save and back up your normal projects. Start an empty trial project with one drum loop or audio track and no other experimental effects. If the host lets you inspect the configuration, aim for 44.1 kHz/128 frames; record what it actually uses rather than forcing an unsupported option.

Have the computer's downloaded package/source/checksums and your recovery helper available. Record model, displayed OS/Hakai version, package commit/hash, service/settings/storage paths and trial start time. Do not change firmware or other plugins to make this test pass.

## Short trial, one step at a time

| Step | What to do | What should happen |
| --- | --- | --- |
| 1. Load | Insert BeatRepeat as an audio effect with playback stopped. | A readable dark native panel appears. No freeze/crash. Gate and Punch are off. |
| 2. Dry | Set Mix 0%, Output 0 dB, Gate OFF, Punch READY; start the loop quietly. | Audio remains stereo and behaves like the original signal. The repeat engine captures history. |
| 3. Punch | Set Length about 100 ms, Mix 50%; let audio play for a second, then tap PUNCH 450MS once. | A brief repeat, then return to live audio. Readouts change without freezing the UI; tap again during Punch to cancel. |
| 4. Latch | Turn Gate ON, then OFF. | Repeat stays active while latched and releases smoothly. Recording freezes during repeat. |
| 5. Length | While Gate is OFF, try 20 ms, 100 ms and 300 ms; trigger each separately. | Different window lengths. Values are approximate, selected at zero crossings. Changing Length during a repeat prepares the next trigger; it does not resize the running loop. |
| 6. Mix | During a latch, slowly sweep Mix from 0 to 100 and back. | Dry remains stereo; full wet is centered mono. Listen for abnormal clicks, pops or instability. |
| 7. Output/bypass | Keep monitoring low. Try Output below 0 dB; test Bypass. | Output changes smoothly. Settled Bypass returns to unity stereo dry, including ignoring plugin gain. Keep positive gain for later headroom checks. |
| 8. Q-Links | Use host Q-Link bank selection, adjust each mapped control and then touch it on-screen. | Length, Gate, Mix, Output, Punch and Bypass synchronize with labels. Four physical knobs use host banks; six JSON bindings do not mean six physical knobs. |
| 9. GUI/status | Check Capture, Repeat, Priming and Bypass on the actual device. | Status reflects processing with up to about 100 ms UI latency. Silence/DC may remain PRIMING instead of creating a loop. No sample-accurate flashing is promised. |
| 10. Automation | In the trial project, automate Mix/Output/Length slowly; observe playback and labels. | Smooth audio, correct displayed values. Do not automate status parameters. Punch is a timed toggle, not a held-down button. |
| 11. Recall | Save under a new trial filename with known Length/Mix/Output/Bypass values. Unload/reload or reopen the project. | Those four values return. Gate/Punch/history do not restart a captured loop. If the host restores transient gates, stop and report it. |
| 12. Lifecycle | Stop/start playback, bypass/re-enable, remove/reinsert several times. | No crash, stuck repeat, lost GUI or increasing resource problems. Transport play/stop alone is not a Gate release; turn Gate OFF yourself. |

Gate and Punch combine: canceling Punch while Gate remains ON still repeats. Anti-phase stereo can cancel in the mono wet input. There is no beat/tempo synchronization, MIDI trigger or direct CV/Gate-output integration in this proof.

## Broader trial only after the short trial passes

Try silence, a sharp drum transient, stereo material and dense audio. Use only rates/block sizes the device can negotiate normally. Check several instances under a realistic but expendable project, watching the device's CPU display and listening for dropouts. Keep a single-instance reference. Run for at least an hour and log repeated trigger/release behavior, memory/CPU trends where available and UI responsiveness. Record actual measurements; an x86 pass is not an MPC CPU benchmark.

If the plugin is listed but cannot load, the screen is blank, status notifications cause instability, Q-Link banks misbehave or recall differs, stop that test. Do not fix it by changing firmware, drive permissions or global settings. Have the helper inspect the **confirmed service's** read-only logs; loader failures can involve mount permissions/libraries, and GUI failures are a different problem. Follow ROLLBACK.md if needed.

## Report the result

Use a copy of this checklist:

```text
Model / OS / Hakai version:
Preparation commit / package SHA256:
Actual sample rate / buffer, if known:
One instance loaded and unloaded repeatedly: PASS / FAIL / not tested
GUI touch / Q-Link banks / parameter synchronization:
Punch / latch / length / mix / output / bypass:
Stereo dry / centered mono wet:
Project scalar recall / transient gate clearing:
Host play-stop / reload / notifier stability:
One-hour trial / peak CPU / audible dropouts:
Failure steps and timestamp / relevant read-only logs:
Rollback needed and result:
```

Do not include passwords, SSH keys, a complete MPC.settings file or unnecessary personal paths in a public report. Passing this checklist supports a future compatibility record; it does not automatically authorize a merge, release or live-performance use.
