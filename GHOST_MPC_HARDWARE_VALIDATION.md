# GHOST 2.4.2 installer2-rc1 - supervised hardware guide

No device operation has been executed for this candidate. Public v2.4.2 and PR #571 remain unchanged. This is a proposed procedure, not permission to run it. SSH was used in earlier trials; the current host, connectivity/model/Hakai/paths must be freshly confirmed. Do not treat os-release as proof of Hakai version.

## 1. Read-only authorization checkpoint

After the owner explicitly authorizes read-only inspection, run on the Mac from this source checkout (replace the host if changed):

```sh
python3 tools/ghost_hardware_preflight.py --host root@DEVICE_IP --out /private/tmp/ghost-hardware-PREFLIGHT-UNIQUE --synths /storage/Synths --settings /data/Settings/MPC/MPC.settings --recovery /storage/GHOST-Recovery --work /storage/GHOST-Work --candidate ../dist/GHOST-2.4.2-installer2-rc1-mpc-armv7.zip
```

Choose a NEW local output path. The script reads via SSH only. It records model/architecture, OS information, service PID/restarts/boot identity/journal, settings twice, all plugin registrations/foreign hashes, mounts/tools/free space/RAM, listings/disk usage, and an independently inspectable tar backup of current GHOST on the Mac. It never starts/stops a service, edits settings, uploads files or executes installer/recovery code. Empty SSH data is a transport/read failure, not invalid-XML evidence. Settings, logs and inventories are private; output directory is 0700, files 0600.

Expected: stable active/running host with unchanged PID/restarts/boot and settings bytes during observation; one correct GHOST UID 47485354, expected binary reviewed against current installation, BeatRepeat absent, unrelated registrations intact. Check PD LAB and MPC-CORE dynamically; do not assume historical plugin counts/hashes. Review journal anomalies, missing plugin paths and actual Hakai version. A crash or changed baseline needs review, never an automatic PASS.

The two /storage roots above are proposals, NOT verified destinations. If absent, the read-only inspection must report NO-GO for installation. Do not create them during the read-only phase. Both must be outside EVERY current SynthContentLocations path (including aliases) and root-owned without group/world write access. Work must share the target filesystem; recovery may be on another filesystem. Validate writable mounts, executable Synths mount, capacity, and that there are no existing unowned namespaces or interrupted recovery locks. If paths cannot be verified, stop.

## 2. Device-modification authorization checkpoint

Present the fresh evidence, candidate SHA256, exact original backup hashes/counts and proposed roots to the owner. Obtain explicit permission for provisioning named roots/upload plus one install/update/uninstall/restore test sequence. No destructive fault injection, crash or forced power-off on the MPC.

Only after that authorization, the following is a provisioning example for absent approved paths (do not reuse/alter pre-existing paths without review):

```sh
ssh root@DEVICE_IP 'test ! -e /storage/GHOST-Recovery && test ! -e /storage/GHOST-Work && mkdir /storage/GHOST-Recovery /storage/GHOST-Work && chmod 700 /storage/GHOST-Recovery /storage/GHOST-Work'
```

Repeat read-only preflight into a new local session. Require GO by human review of all evidence. Verify two independent exact backup copies: Mac tar plus a second approved external backup destination on the MPC, outside discovery paths. Keep the original desktop recovery ZIP separately. Verify tar contents/hashes locally; never extract into the live target as an improvised restore. Test a second SSH connection using read-only commands and keep it available. If unavailable or any root/layout/hash/service check differs unexpectedly, stop before installation.

## 3. Transfer and verify (authorized only)

Verify the candidate against dist/SHA256SUMS on the Mac. Extract into a new local directory. Use an explicit new destination; no ambiguous scp directory nesting:

```sh
ssh root@DEVICE_IP 'test ! -e /tmp/ghost-installer2-rc1 && mkdir /tmp/ghost-installer2-rc1'
tar -cf - -C /YOUR/EXTRACTED/GHOST-2.4.2 . | ssh root@DEVICE_IP 'tar -xf - -C /tmp/ghost-installer2-rc1'
ssh root@DEVICE_IP 'cd /tmp/ghost-installer2-rc1 && sha256sum -c SHA256SUMS'
```

Stop on any nonzero exit. Never overwrite a historical package/backup. Save projects; do not open original musical projects. Use a new throwaway Drum Program for audible tests. Do not infer safety from the screen deliberately going black during host stop.

## 4. Install, then update, then uninstall (separate checkpoints)

From the Mac, the exact proposed install command is:

```sh
ssh root@DEVICE_IP 'cd /tmp/ghost-installer2-rc1 && GHOST_RECOVERY_ROOT=/storage/GHOST-Recovery GHOST_WORK_ROOT=/storage/GHOST-Work MPC_SETTINGS=/data/Settings/MPC/MPC.settings sh install.sh -y -t /storage/Synths'
```

Capture complete stdout/stderr and the SSH exit code to a new local log (do not pipe through tee and accidentally report its exit status). Save the printed exact TX path. Collect status/PID/NRestarts and fresh settings/registry/plugin hashes before proceeding. The installation on an already-present GHOST is an update test, NOT evidence of a fresh install on empty hardware. No duplicate UID/skin, missing foreign plugin or unexpected host restart is acceptable. Have the owner open GHOST and check GUI, audio and controls. Do not mark those PASS from shell checks.

For the repeated update test use the same command once, after reviewing the first result. Verify settings/preferences/foreign plugins and any OWNER-AUTHORIZED temporary preset copy survive. Never edit an original preset for this test. Record the copy's exact path/hash and approval; preserve the original independently.

After the owner authorizes the uninstall checkpoint:

```sh
ssh root@DEVICE_IP 'cd /tmp/ghost-installer2-rc1 && GHOST_RECOVERY_ROOT=/storage/GHOST-Recovery GHOST_WORK_ROOT=/storage/GHOST-Work MPC_SETTINGS=/data/Settings/MPC/MPC.settings sh uninstall.sh -y -t /storage/Synths'
```

Expected: no GHOST registration/owned audio library; unknown/edited user files remain; foreign plugins/preferences remain intact; host returns active/stable. Preserve the uninstall TX. Collect full logs and registry/hashes immediately. Do not leave the device without the agreed preferred working GHOST.

## 5. Recovery and final preferred-state restoration

For a failed or interrupted operation, only the recorded transaction owns recovery. From the independent authorized SSH connection:

```sh
sh /APPROVED/RECOVERY/ghost-community-v2/tx-EXACT/recover.sh /APPROVED/RECOVERY/ghost-community-v2/tx-EXACT
```

recover.sh refuses active workers/guardians, completes interrupted rollback first, then releases its stale global lock. It never claims a dead PID alone proves recovery. Missing owner metadata or an interrupted reaper/takeover is a manual-review refusal: archive the exact lock/TX metadata and verify boot/PID/start identity; do not blindly rmdir it.

To undo a committed trial use its `rollback.sh` with that same TX argument. A successful manual rollback is idempotent. After uninstall, first restore its exact pre-uninstall state using the uninstall TX rollback. Verify original binary/GUI/audio with the owner. To return all the way to the initial preferred installation, use the first trial TX rollback ONLY after proving current tree is its known after-image. If authorized temporary test files exist, preserve them independently and remove only those exact approved fixture files with matching hashes before this comparison; otherwise refuse and review. Never force an old snapshot over unexpected current files/settings. All recovery copies remain outside content scanning paths.

If concurrent critical content-path/XML changes make recovery/work discoverable, automatic host startup is refused and the review lock is retained; do not force a restart or revert the user settings without review.

If recovery fails, stop: do not install another build or improvise a copy. Preserve logs/backups, keep SSH available, and seek reviewed recovery with the independent Mac backup. No software recovery operates during loss of power or repairs failed storage.

## 6. Evidence and acceptance

Collect before/after each operation: complete terminal output + exit code; private settings snapshots and structural diffs; service state/PID/restarts/journal; plugin UID/metadata/file hashes; exact root/work/TX ownership/lock state; free space; `ls -la /storage/Synths` and `du -sh /storage/Synths`; equivalent recovery/work listings and usage. Adapt only to freshly verified paths. Redact settings preferences/project paths/addresses before any public post.

PASS requires exact file/foreign-registry preservation, correct rollback, stable service, no duplicate discovery entries, retained edited presets, no orphan active locks, and owner-confirmed GUI/audio. A shell PASS is not musical validation. Record actual startup settings changes instead of assuming a shutdown rewrite. New dropouts/crashes/registry changes, hash discrepancies or recovery conflicts halt the trial. No long/destructive stress test is authorized by this guide.

Retention: max three TX slots and 512 MiB recovery quota; the next operation refuses instead of deleting backups. Only older completed/restored TXs can be explicitly exported and cleaned; newest is protected. `cleanup.sh /exact/old/TX --export /NEW/INDEPENDENT/OUTSIDE-CONTENT --confirm` verifies the complete export before deleting exact self-owned recovery/work trees. Never clean unfinished recovery or a live lock. This is not permission to delete historical backups.
