# Separately approved original MPC One test

This is a plan only. No MPC has been accessed, connected, installed to or changed by this proof. There is no release. The candidate is ready for **review and a separately approved controlled hardware trial**, not for a live-performance compatibility claim.

## Before a device trial

- Review GPL/source/notices and the actual binary distribution/install arrangement; do not treat SDK-free as blanket legal clearance.
- Confirm original MPC One CPU/VFP/NEON, ARM hard-float userspace and available glibc/libm/libpthread versions/symbols without assuming all Hakai versions are identical.
- Confirm Hakai 3.9.1 accepts VSTPluginMain, effect classification, EuBr UID, chosen native skin version and the community Synths/effect package layout. Check UID/path collisions before any copying.
- Obtain explicit approval for exact device files and the host's actual registration workflow. Keep existing plugins and MPC.settings unchanged; use the independent directory and retain a rollback copy of any separately authorized registration artifact.
- Start with a disposable project and low monitoring level, no live performance dependency. Archive the matching source/package hashes and record device/firmware/audio settings.

## Trial sequence

1. Scan/load/unload repeatedly; verify classification as a stereo effect, stable identity and no scanner crash.
2. Verify native GUI occupies the expected host area, labels and overlays are legible, all six controls accept touch, and physical Q-Link banks correspond to the JSON slots.
3. Confirm touch → getParameter/display, Q-Link → GUI, automation → GUI and project restore → GUI synchronization. Check notifier callbacks do not deadlock/crash; exercise reload and fast unload while status is changing. If background-thread status notifications are rejected, stop that functionality and design a supported host polling alternative before approval for performance use.
4. At 44.1 kHz/128 frames, test silence, DC, drum transients, stereo/anti-phase audio, held Gate, Punch/retrigger/cancel, mix sweeps, output headroom and bypass. Listen for clicks at loop edges, release, project/rate changes and repeated switching.
5. Save/reload a disposable project: Length/Mix/Output/Bypass return, Gate/Punch/history do not restart a captured loop. Verify whether the MPC actually consumes VST chunks rather than overriding transient values through scalar recall.
6. Test host play/stop, suspend/resume, supported block sizes and rates that the device can negotiate. Length is free-running milliseconds; no MIDI/tempo behavior should be expected.
7. Measure one and several instances under realistic project load: callback deadline misses, peak CPU, memory growth, notifier overhead and long-running stability. Test for at least one hour before considering performance approval.
8. Record reproducible results and failures in a follow-up issue/PR; do not merge/release from this proof automatically.

## Explicit outstanding limits

ARM code has been cross-compiled/static-validated but not executed under QEMU or real ARM. CPU deadline headroom on the MPC is unknown. Native automated UI tests validate actual exported actions/assets/parameter bindings; they cannot validate Akai's renderer, host threading or registration. No press-and-hold gesture, sample-accurate GUI indicator, transport sync, MIDI triggering, true stereo wet or captured-audio recall is promised. The MPC's eight CV/Gate outputs are not exposed by this proof, and no direct plugin API for them has been verified. External MIDI/CV routing would be a separate approved capability investigation.
