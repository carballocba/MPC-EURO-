> Historical preparation report. See GHOST_HARDWARE_TEST_RESULTS.md for the completed 29 October 2026 hardware sequence and owner confirmations.

# Proposed single-authorization sequence — not executed

Use only `GHOST-2.4.2-installer2-rc3-mpc-armv7.zip` with the SHA256 in dist-rc3/SHA256SUMS. No binary rebuild. Desired final state:the original366 regular files/52 FXP and current legitimate preferences, GHOST once, other82 plugins unchanged, acvs stable, all recovery evidence retained.

1. Repeat complete read-only preflight, native compatibility dry run, all83 current hashes, registry/critical paths, space/quota and independent Mac backup. Changes from unrelated verified development or a clean previous reboot are reportable; genuine concurrent changes within the current transaction window or unresolved GHOST conflicts stop. No project originals opened. Keep independent recovery SSH available.
2. After explicit authorization only, upload verified rc3 to a new exact `/storage/GHOST-Work/incoming-rc3-validation-20261029`, with TMPDIR `/storage/GHOST-Work/tmp-rc3-validation-20261029`. Never overwrite historical candidates. If included in the same authorization, add a single absent, known-hash user-content canary at the GHOST root; preserve original366 independently first. Verify staged package checksum/syntax. No modifications to an original FXP are needed:all52 are checked before/after, and offline edited-preset tests already cover customization.
3. Execute once (actual installation over a desktop predecessor, not a fresh-empty install claim):

```sh
ssh root@DEVICE_IP 'cd /storage/GHOST-Work/incoming-rc3-validation-20261029 && GHOST_RECOVERY_ROOT=/storage/GHOST-Recovery GHOST_WORK_ROOT=/storage/GHOST-Work MPC_SETTINGS=/data/Settings/MPC/MPC.settings TMPDIR=/storage/GHOST-Work/tmp-rc3-validation-20261029 sh install.sh -y -t /storage/Synths'
```

Save exactTX1, full terminal output/SSH exit, files.before/after, adoption.plan, stable post-stop settings snapshots, watchdog/lock states and journal cursor/delta. Require verified second backup before stop, commit/worker.done and guardian exit, no active lease, original52FXP and user content intact, approved binary, one GHOST+82 foreign records, unchanged foreign hashes and current preferences. Expect367 files without canary (366+ownership record),368 with it, unless separately preserved user content exists.
4. Owner opens GHOST in a disposable Drum Program for actual GUI/touch/Q-Link/basic audio confirmation, then closes the instance. A mapped library or shell PASS is not audio evidence. This is a human observation checkpoint, not another installation permission. If unavailable, leave PENDING and do not uninstall an instrument currently in use. Stable-host musical failure stops for review; genuine host failure invokes only validated transaction recovery.
5. **Required retention checkpoint:** after TX1 is committed and newer than the completed old packet, export/verify that exact older rc2 packet with its checksum-verified shipped cleanup.sh:

```sh
ssh root@DEVICE_IP 'sh /storage/GHOST-Recovery/ghost-community-v2/tx-20261028T125618Z-10574/cleanup.sh /storage/GHOST-Recovery/ghost-community-v2/tx-20261028T125618Z-10574 --export /storage/GHOST-Recovery/export-rc2-aborted-20261028T125618Z-10574 --confirm'
```

The export destination must not exist. This copies/verifies transaction+work before removing only those exact old self-owned source trees. Export plus independent Mac packet/backup remains, newestTX1 is protected. No wildcard cleanup or quota bypass. This precise export/cleanup must be included in the future owner authorization. If the state/destination differs, do not improvise; stop. Without the checkpoint the three-operation trial is NO-GO by design.
6. Refresh the current phase snapshot and invoke the same install.sh command once to perform the actual same-version community update/reinstall (TX2). Verify all52 FXP, user file metadata/content, exact after-image, foreign registry/binaries, settings, service/journal and storage. This does not claim a cross-version update.
7. With the disposable instance closed and all checks passed, perform the actual uninstall (TX3):

```sh
ssh root@DEVICE_IP 'cd /storage/GHOST-Work/incoming-rc3-validation-20261029 && GHOST_RECOVERY_ROOT=/storage/GHOST-Recovery GHOST_WORK_ROOT=/storage/GHOST-Work MPC_SETTINGS=/data/Settings/MPC/MPC.settings TMPDIR=/storage/GHOST-Work/tmp-rc3-validation-20261029 sh uninstall.sh -y -t /storage/Synths'
```

Require82 unchanged foreign entries, no GHOST entry/binary, preserved55 preset/index files plus any unknown/user files, no active lease, stable acvs and preserved preferences. A retained GHOST folder containing presets is intentional, not an orphaned active plugin. Capture actual menu observation if available; do not claim it from XML alone.
8. Restore preferred working GHOST using TX3's shipped rollback.sh with exactTX3 argument. If the full resulting tree equals TX1/files.after, undo TX1 using its rollback.sh; otherwise undo knownTX2 thenTX1 after verifying each before/after-image. No new frontend transaction is needed. These are separately logged controlled stop/start cycles covered only by the future full authorization. Preserve current legitimate preferences via the validated GHOST-only inverse; never restore an old whole-system snapshot. Remove only the exact authorized canary after hash verification. Verify final original366 file contents/basic metadata,52FXP, GHOST registration, other82 hashes and service stability. Retain all3 completed packet backups and the exported old packet.

On any frontend/activation/start/hash/conflict failure:no retry. Let worker/watchdog perform serialized validated rollback; check restored image and service. For a dead interrupted worker/guardian use only the exact packet's recover.sh after identity/context verification; for a committed known after-image, its rollback.sh. Unknown ownership/corrupt backup/conflicting data or failed recovery:stop and request specific instructions. Intentional black screen while acvs is stopped is not a crash. No destructive fault injection or long stress test on the MPC.

Per-phase evidence:full stdout/stderr and real return code, exact package/TX, private settings and redacted structural diffs, registry counts/UIDs, all foreign file hashes, GHOST full inventory/modes/presets/canary, watchdog/lease/recovery states, PID/restarts/journal, `ls -la /storage/Synths`, `du -sh /storage/Synths`, root/packet listings+usage and df. No pre-created PASS logs for unperformed phases. Do not publish response/assets or update PR571 without separate authorization.
