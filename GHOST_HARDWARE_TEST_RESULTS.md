# GHOST 2.4.2 installer2-rc3 — consolidated real hardware validation

29 October 2026; Akai MPC One Gen1, Hakai 3.9.1 (owner-confirmed target). No public GitHub or release changes performed.

## Results

| Actual operation | Exit | Result |
|---|---:|---|
| A: community installation over desktop predecessor | 0 | PASS technical; owner GUI/touch/Q-Link/audio/MIX/basic stability PASS |
| Export/verify older aborted rc2 recovery packet | 0 | PASS; full export and independent Mac evidence retained |
| Restore true legacy predecessor through TX_A rollback | 0 | PASS, original metadata and files restored |
| B: legacy-to-community package-format update | 0 | PASS, actual non-idempotent metadata/ownership migration |
| C: community uninstall | 0 | PASS, only recognized runtime/ownership and GHOST registration removed |
| D1: restore community before-image through TX_C rollback | 0 | PASS |
| D2: restore original desktop before-image through TX_B rollback | 0 | PASS technical; final owner GUI/controls/audio confirmation PASS |

The update kept audio/product version 2.4.2. It is not a semantic-version upgrade or proof of catalog-client version notification. It started from the verified real legacy preimage, not an identical community reinstall.

## Preserved data and final state

- Original366 regular GHOST files restored with identical hashes, modes, numeric ownership and mtimes. All52 FXP likewise preserved throughout.
- During install/update:368 files =366 package files +ownership manifest +authorized root-level preservation canary. During uninstall:56 files =55 preset/index files +canary; no GHOST binary/registry entry. Canary survived both migration and uninstall, then only that exact hash-verified fixture was removed after final restoration.
- Final83 registry entries: one GHOST UID47485354 (numeric1195922260),82 foreign entries unchanged. All82 foreign plugin binary hashes unchanged at every phase. No other plugin resources, projects or libraries were targeted; this is not a claim of recursively hashing all unrelated libraries/projects.
- Final settings SHA2563e63a9f31411b983c4a6b7ce5d698d0d5fccfaecc67d0548eef9db27098a21b1, exactly the original baseline bytes. Registry edits during the tests preserved non-GHOST settings structurally. No historical global configuration was installed.
- Final service active/running, PID6232, NRestarts0, same boot. No new SIGSEGV/segfault/core-dump/scheduled restart in captured journal deltas. Six intended stop/start cycles in the complete A–D plan; not crashes.
- No active global installer lock or residual rollback lock found. All three rc3 transaction states are restored. Recovery packets/backups retained.

## Recovery/storage

Exact transaction packets under /storage/GHOST-Recovery/ghost-community-v2/:
- A:tx-20261029T051548Z-433
- B:tx-20261029T073707Z-22766
- C:tx-20261029T073833Z-29781

Old rc2 completed packet was exported with its checksum-verified cleanup.sh to /storage/GHOST-Recovery/export-rc2-aborted-20261028T125618Z-10574 before freeing only its verified source transaction/work trees. The export and independently recorded Mac backups remain. The newest/incomplete recovery points were not deleted. All current rollback.done markers are complete; invoking those scripts again is an idempotent no-op, not a new restoration mechanism for arbitrary future edits.

Final storage:346992 KiB free; recovery root18600 KiB, work root16488 KiB. Fresh pre-remaining-sequence free361740 KiB; retained additional evidence accounts for bounded growth. Recovery remains outside plugin discovery; three retained transaction slots are now occupied. A future frontend requires explicit verified export/cleanup of an eligible older completed packet; no automatic deletion or quota bypass is proposed.

## Evidence

Private complete evidence root:hardware-sessions/20261029-final-authorized/.
- install/install.log and install/COMMAND_RESULTS.json — actual A operation.
- remaining-resumed/migration_B/terminal.log — actual B.
- remaining-resumed/uninstall_C/terminal.log — actual C.
- remaining-resumed/predecessor_restore_A/terminal.log, restore_D_community/terminal.log, restore_D_original/terminal.log — actual restores.
- remaining-resumed/COMMAND_RESULTS.json and RESULT.json — all subsequent return codes/status.
- per-stage settings, full GHOST tar/inventory, foreign hashes, journal deltas, ls-la/du/df, service, lock and backup evidence.
- OWNER_PHYSICAL_CONFIRMATION.json — explicit basic owner functional PASS after A.

One preliminary read-only evidence copy failed because the local supervisor assumed ghost-community-v2 for the work namespace; the saved context correctly specified ghost-work-v2. No device mutation or frontend invocation occurred in that attempt. Both logs are retained in remaining/; only the local read path was corrected from saved context before execution in remaining-resumed/. This was not an installer retry or hidden hardware failure.

## Review coverage and limits

1. Settings sequencing: authoritative stable baseline after confirmed host stop. Actual A/B/C succeeded; no clean-shutdown rewrite was observed in these runs. Rewrite/concurrent-edit scenarios passed offline; do not claim a real rewrite occurred.
2. Real Gen1 install/migration-update/uninstall/restore: executed and logged as above; final restored GUI/audio still awaits owner confirmation.
3. Worker/watchdog rollback ownership: atomic filesystem lease tested offline; actual frontends show ready guardian, verified commit, worker completion and guardian exit. Planned manual rollback executed successfully. No physical timeout/race/crash injection was performed.
4. Recovery outside discovery: actual /storage/GHOST-Recovery and /storage/GHOST-Work used; bounded retention and export verified on hardware. All full backup copies outside Synths.
5. Stale locks: boot/PID/start identity and interruption cases passed offline; no residual active locks after real operations. No physical power-loss/SIGKILL test performed.
Minor DEFER, test-mode isolation, noexec/privilege/path/package checks covered by the84 offline tests/ShellCheck. Actual sequence used normal-y community mode, not deferred batching.

## Artifact and decision

Same immutable rc3 ZIP actually used; no regeneration after hardware testing. SHA2560920fde1c908e9a3dcdde5182dffeb206b63b8e706e16c7fb46839a9b0be0b7e. DSP588019130b31ced7077f7e4afe35bd23b0753df7a2959e2af39fa825e1b81afd unchanged. Offline84 tests PASS; ShellCheck PASS; latest catalog checker0 errors/two custom-installer warnings.

Technical installer sequence:PASS. Final restored owner GUI/controls/audio:PASS (explicit owner confirmation; basic smoke test only). Prepare evidence for maintainer review; do not claim catalog acceptance or publish the candidate/response without authorization. Current public PR/release are unchanged. Immutable published rc3 URL and live catalog resolution remain pending separate publication authorization.

## Final owner confirmation

Owner explicitly confirmed restored GUI, touchscreen/Q-Links and audio/MIX without unexpected cuts: PASS. All authorized physical operations and both basic functional owner checkpoints are complete. GO to submit the prepared evidence for maintainer review, subject to separate publication authorization. No physical fault injection or exhaustive musical/parameter coverage is claimed.
