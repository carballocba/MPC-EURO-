# GHOST2.4.2 — safe community beta candidate

The same GHOST BOTH FIX stereo glitch effect: unchanged DSP,156 public parameters, UID0x47485354 /1195922260, original PLAY GUI, all Screen/Program Q-Links,16 programs and52 FXP. No new audio features. ARMv7 hard-float, system libc/libm/libpthread, max required glibc2.27; skin3.x only.

## Status

Prepared offline. **Ready for review and a separately authorized supervised hardware trial, not for publication yet.** No device was connected during preparation. The exact community ZIP still needs CPU/dropout, touch, Q-Link and INDEPENDENT/BOTH tests. Historical owner-device installation is not a community-package certification.

## Safe installer

Python3 runs on your computer; the device requires only existing BusyBox/POSIX tools, tar, sha256sum, nohup, awk and systemctl. No remote Python, base64, GNU timeout, Homebrew or package installation. SSH host, Synths folder, settings path and service are explicit inputs; no owner's IP, personal hashes, fixed registry count or private backups are shipped.

Run a read-only preflight first, using YOUR paths (examples below are placeholders):

```sh
python3 manage.py preflight --host root@DEVICE_IP --synths /YOUR/Synths --settings /YOUR/Settings/MPC.settings --service acvs
```

Future separately authorized install/update:

```sh
python3 manage.py install --host root@DEVICE_IP --synths /YOUR/Synths --settings /YOUR/Settings/MPC.settings --service acvs --confirm
```

Uninstall uses the same command with `uninstall` instead of `install`. If the device uses `inmusic-mpc`, specify that service explicitly. Save your project before any mutation. A missing tool, unsupported registry/layout, UID/path collision, unexpected host/settings state or inadequate free space/RAM refuses before service stop. No firmware/library/runtime is downloaded or installed.

The controller makes a complete Mac/computer backup and an independent verified device backup OUTSIDE GHOST. A detached guardian is armed before stopping the host. Files are activated by directory rename; errors, lost SSH workers, SIGKILL and deadline expiry trigger GHOST-only recovery. The old original directory is retained, allowing recovery by rename even without another full copy. Backups are never deleted automatically.

Clean install/removal necessarily edits GHOST's own registry entry. All other plugin entries and preferences are validated unchanged locally. Updates with matching metadata preserve settings bytes/inode. Rollback never overwrites current preferences with a historical full settings snapshot: a full original file is used only if current bytes are still exactly the transaction's known after-image; otherwise a literal inverse of GHOST's own token preserves external changes. Unsupported concurrent changes to GHOST's own registration stop automatic registry repair and leave a review marker rather than erase user changes. The service recovery is attempted even in that case.

The root shell frontends invoke the desktop controller, not the former unsafe standard device scripts. Do not run them on the MPC. Do not use a catalog/app installation route that bypasses this controller; catalog integration requires maintainer review of the modified installer. The catalog checker accepts the payload with installer-difference warnings; these warnings are not a hardware safety certification.

## Compatibility

RRF1 states created by this version may not open in an older binary. Rollback restores files, not musical project conversion. Use project copies; preserve original projects. External FXP do not automatically appear in the Hakai browser; import must be tested separately. Updates preserve existing FXP edits and extra user files inside GHOST, in addition to the complete rollback backup. Keep an independent library outside the installation folder. A foreign plugin registered inside GHOST makes the installer refuse rather than move another plugin.

See CONTROLS.md, QLINKS.md, RECOVERY.md, LICENSE_AUDIT.md and HARDWARE_PROTOCOL.md. GPL-3.0-only with retained MIT/Zig/DejaVu notices. Unofficial; no Akai/inMusic/Steinberg endorsement.
