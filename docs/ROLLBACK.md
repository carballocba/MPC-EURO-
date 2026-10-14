# BeatRepeat — stop and roll back a future trial

This is a recovery plan for a **separately approved** installation. No rollback or device changes have been performed during preparation. Keep the settings/project backups before beginning any trial.

## Sound is wrong but the MPC interface still works

1. Lower the physical monitor/headphone volume first. Stop playback.
2. Set Gate OFF and cancel Punch. Set plugin Bypass ON if the UI responds.
3. Remove BeatRepeat from the trial project's effect insert. Keep other effects unchanged. Do not save over your original project.
4. Record what happened, the settings and elapsed time. Stop testing rather than repeatedly triggering a suspected crash. Bypass cannot protect against a crashed host; physical volume control comes first.

## Remove the experimental installation

Have the same helper who registered it perform this targeted reversal after approval:

1. Save evidence. Stop the confirmed MPC service and verify the host has exited.
2. Back up the current settings again so the pre-rollback state is preserved.
3. In a temporary copy of the confirmed active settings, remove only the VST entry with UID **45754272** and the exact installed BeatRepeat library path. Validate XML and verify all other plugin entries/preferences are unchanged before applying it.
4. Move only the newly installed `MPC-EURO - VST - BeatRepeat` folder to an off-device archive, outside any searched Synths directory. Keep logs, matching source and backups. Do not delete Delay, Granular Freezer, other plugin folders or shared infrastructure.
5. Start the same confirmed service. Verify previous plugins/preferences and open an existing project that did not use BeatRepeat. Trial projects that referenced it may show a missing plugin; that is expected after removal.

There is no uninstall.sh in this package. Do not use a whole-list rebuild or an unrelated uninstaller to remove it.

## Host will not start or preferences reset

Lower monitor volume and stop the trial. Have the helper stop the confirmed service, preserve the failed settings/logs, and restore the **exact pre-trial backup of the confirmed active file** while the host is stopped. Restart the same service and check the original setup. Restoring a full backup also restores preferences from that backup time, so use this for recovery, not routine selective removal after unrelated later changes.

If the service/profile/backup is uncertain, the backup is missing, or recovery fails, stop and obtain experienced help. Do not factory reset, delete settings, reinstall Hakai, repeatedly power-cycle or change unrelated files as a troubleshooting shortcut. Log access must be read-only; use the service actually confirmed on this device.
