# Remaining limitations

- The exact safe community ZIP and its guardian have not run on physical MPC hardware. No actual ARM CPU/dropout, host-focus, touchscreen or final INDEPENDENT/BOTH certification is claimed.
- Custom safe desktop install/uninstall scripts differ from community-standard device templates. The checker reports warnings; catalog/app installation paths must not bypass the guarded controller. Maintainer acceptance/integration remains pending, not silently treated as resolved.
- Independent recovery assumes functioning powered Linux, storage and SSH. Power-off recovery is durable/manual after reboot, not automatic boot-service recovery. No unconditional guarantee can cover dead disks/power or arbitrary root-level concurrent edits.
- A concurrent change to GHOST's own registry token is preserved for review rather than blindly overwritten; host recovery is attempted and backups remain available. Other preferences and plugins are never rollback targets.
- New RRF1 states may not load in older binaries; file rollback does not migrate projects. FXP browser import remains a separate hardware check.
- Only the original MPC One/Hakai3.9.1 historical integration target is known; other models/firmware/OS2/Gen2 are not physically supported by this candidate. Historical acvs exits retain unknown trigger; no cause is attributed to GHOST without evidence.
- Package version2.4.2/content2.4.2.0 and unchanged VST/plugin-meta2.0.0 are intentionally retained. No DSP or parameter-version rebuild was made.
