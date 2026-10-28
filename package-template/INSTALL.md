# GHOST 2.4.2 / installer2-rc1 (UNPUBLISHED)

Same approved GHOST audio/GUI/UID/parameters/presets. This is an installer-only candidate, not a replacement of the public v2.4.2 assets. Hardware validation of this installer: NOT TESTED. Root Gen1 ARMv7, existing BusyBox/POSIX tools and systemctl are required. Production refuses MPC_INSTALL_TEST and GHOST_FAILPOINT.

Save projects and keep an independent backup. Before the first device write, explicitly authorize read-only preflight, verify model/Hakai/version, paths, host stability, current plugin/settings hashes, other plugins, mount options, storage and recovery. See GHOST_MPC_HARDWARE_VALIDATION.md in the source candidate.

## Required recovery configuration

Set GHOST_RECOVERY_ROOT and (when different) GHOST_WORK_ROOT to EXISTING root-owned directories without group/world write access. No automatic default destination is assumed. Both must be outside ALL current SynthContentLocations (not merely hidden in Synths). Work must share the target filesystem for atomic rename; recovery may be on another filesystem and uses verified copies. Missing/unsupported/noexec/readonly/space/path conditions refuse before service shutdown. Proposed paths require actual hardware verification, not a historical assumption.

From the extracted package on the device, AFTER authorization and fresh preflight:

    GHOST_RECOVERY_ROOT=/APPROVED/Recovery GHOST_WORK_ROOT=/APPROVED/Work sh install.sh -t /ACTUAL/Synths

Uninstall with uninstall.sh and the same roots/target. -y skips confirmation. -n is declared to catalog clients and requires the caller already stopped MPC; only that caller restarts it, including after failure. Standalone mode owns service stop/start. Do not use -n manually on a running host.

The initial settings copy is an observation only. After confirmed clean shutdown, a stable settings snapshot becomes the transaction baseline; shutdown preference writes are preserved. Plugin registry changes across shutdown refuse. Later concurrent settings changes are checked before each write. Recovery before registration does not restore old preferences; after registration it reverses only the known GHOST token when unrelated preferences changed. Conflicts never authorize a historical full-settings overwrite.

Only byte-identical known package-owned files are replaced/removed. Unknown files and edited presets survive update/uninstall; modified runtime collisions refuse. Root-owned .ghost-owned.sha256 records ownership; the frozen prior-release list supports the exact earlier package. Missing/invalid ownership is not blindly inferred. Full current plugin backup is verified before shutdown. No projects or FXP state are converted; RRF1 downgrade compatibility is not automatic.

## Recovery

Every transaction prints its exact external TX path. Packet metadata, verified backup, authoritative settings baseline, expected after-image, worker/guardian boot/PID/start identity and state checkpoints are retained. A single atomic recovery lease serializes worker, guardian and manual rollback. An active recovery owner is waited for, not raced. Unknown/corrupt lock ownership refuses for review. PID reuse and another boot do not masquerade as the original owner.

For an authorized independent SSH shell after worker/guardian exit:

    sh /APPROVED/Recovery/ghost-community-v2/tx-EXACT/recover.sh /APPROVED/Recovery/ghost-community-v2/tx-EXACT

This completes an interrupted operation before releasing its stale global lock. To undo a committed trial, invoke its rollback.sh with the exact same TX. Never force a different transaction's snapshot over current data. Missing owner metadata, stale takeover/reaper or conflicting live files require manual inspection; do not blindly rmdir active locks.

No guardian runs during power loss, repairs failed storage or proves GUI/audio health. Recovery persists for after SSH returns. Keep the original independent Mac backup and known-working desktop recovery package. Unexpected service/load failure: stop the trial, recover once, preserve evidence; no automatic second installation.

## Retention and cleanup

Backups live under Recovery/ghost-community-v2, transient same-filesystem trees under Work/ghost-work-v2, never under discovery roots. The old work tree is removed only after verified activation/host startup and an intact independent backup. Failed candidate trees may be retained in the work namespace for review.

Limit: THREE retained transactions and 512 MiB recovery quota; a new operation refuses at the limit. No automatic deletion of user-containing recovery copies. Only older completed/restored TXs may be explicitly exported using cleanup.sh TX --export /NEW/INDEPENDENT/OUTSIDE-CONTENT --confirm; export bytes are verified before deleting exact self-owned TX/work trees. The newest recovery state and any incomplete/active transaction are protected. Do not delete historical backups without separate approval.
