# Controls and performance workflow

## PLAY

- **ACTIVITY (132)** reuses GLITCH: how much the Performance engine intervenes. Low Activity does not promise continuous destruction even with Character high. In BOTH, Activity zero explicitly cancels automatic RR; nonzero Activity no longer scales away RR density.
- **CHARACTER (133)** reuses CHAOS: event variety/unpredictability, not another gain/intensity control.
- **FRAGMENT (134)** reuses SIZE: fragment duration, nominal8–400ms in the RR policy. Manual changes take priority for the existing override window; generation can resume after it.
- **EVOLUTION (139)** uses the existing Motion policy/routes; its effect depends on enabled routing. No new modulation algorithm is added.
- **POSITION (12)** is buffer read position; it is not reverb, stereo spread or spatial processing.
- **MIX (53)** blends dry and processed audio. Start low when learning a preset.
- BREAK9, CORRUPT17, Repeat Weight135, Reverse Weight136, Cut Weight137, Rest Bias138, Rate140, Chance77, Duration Max79 and Window13 provide secondary adjustment. See QLINKS.md for exact assignments.

## Random Repeat

IDs148–153 are RR MODE, INT, PROB, VAR, RATE and HOLD.154 and155 publish RR LIVE/MS diagnostics. MODE choices are MANUAL, INDEPENDENT, PERFORMANCE, BOTH (normalized0,1/3,2/3,1). INDEPENDENT retains the validated manual-repeat reader and fragment changes. BOTH FIX prevents Performance from cancelling RR length decisions and avoids restarting phrase RNG on duplicate mode delivery. RATE sets rhythmic decision spacing; HOLD controls repeated stability before a new decision. Variation and Evolution influence fragment changes. A fixed seed makes an equivalent clock/control sequence deterministic; transport seeks/reset can intentionally restart a sequence.

## Buffer and actions

LIVE maintains circular incoming history. LIVE REPEAT pins a region; changing FRAGMENT changes the read length, and the pinned material can keep repeating after input stops. LIVE REVERSE acts on available history. CAPTURE is a toggle: start a take, then finish into HELD; up to8seconds are configurable, with automatic FULL confirmation. FREEZE/HELD protects captured material. CLEAN stops processing without erasing the take and turns generation off. PUNCH/CANCEL is the existing immediate manual intervention; it is not permission to overwrite a frozen take. DICE produces a seeded variation of configured targets, preserving the established protected states. Performance/Random Repeat do not automate CAPTURE or FREEZE destructively.

## Advanced pages

PLAY, BUFFER, EVENTS, MOTION, RANDOM, TIMING, GLOBAL, MIDI and SCENES are preserved. Motion requires enabled source/route/depth; Random requires an eligible unlocked destination. Some readouts and parameter aliases are deliberately not independent writable controls. PARAMETERS.csv reports all156 actual exported IDs/names and automation flags from the native wrapper; QLINKS.json is the unchanged full host mapping.

## Presets/projects

The16 programs remain in the plugin.52 FXP files are shipped unchanged (48library plus4Performance examples); they do not contain a captured musical phrase. Buffer-dependent sounds need incoming/captured material. Loading a preset is not evidence of a working FXP import browser. New RRF1 states load in this candidate and may not load in older binaries. Keep original projects untouched, test with copies, and export a compatible old-state copy before any downgrade; there is no automatic reverse conversion.
