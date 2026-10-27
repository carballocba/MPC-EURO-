# Recovery and backup contract

Every operation prints a transaction path and writes a local session directory. A device transaction lives at `<Synths>/.ghost-recovery/tx-...`, outside GHOST; its `backup/`, `settings.before`, manifests and logs are never deleted automatically. `prior-active/` holds the original directory before activation and is preferred for zero-extra-copy rollback. A separate computer `ghost.before.tar` and settings snapshot survive device-side failure.

## Repeatable GHOST-only rollback

```sh
python3 manage.py rollback --host root@DEVICE_IP --synths /YOUR/Synths --settings /YOUR/Settings/MPC.settings --transaction /YOUR/Synths/.ghost-recovery/tx-EXACT_SESSION --confirm
```

The transaction path must be copied from that operation's own report. Never use somebody else's snapshot. Same already-restored state returns idempotently without another host restart. Rollback restores only GHOST files and its exact old registry element (or absence). Other plugins, PD LAB/MPC-CORE, DNS, preferences and music are not rollback targets. A retained GHOST source/UID conflict is a review condition, not permission to overwrite it.

## Independent recovery if the controller dies

The detached nohup guardian reads its durable plan directly from the device and needs neither acvs nor the desktop Python process. PID plus process-start identity avoids killing a reused PID. It detects worker exit or a180-second deadline, requests termination, and takes over only after the exact worker is gone. The foreground waits for its guardian to finish before releasing the lock, preventing a stale guardian racing a subsequent rollback. A stale lock can be reclaimed ONLY by that same transaction when both exact worker and guardian are dead.

For authorized SSH recovery after power restoration, the self-contained device command is:

```sh
env ACTION=rollback TX='/YOUR/Synths/.ghost-recovery/tx-EXACT_SESSION' sh '/YOUR/Synths/.ghost-recovery/tx-EXACT_SESSION/transaction.sh'
```

Run that only on the device, from an explicitly authorized recovery shell. No current installer package is needed; the plan, backend and inverse token patch are preserved with the backup. Never delete the recovery directory while it could be needed.

## Honest failure boundary

A stopped acvs can make the MPC screen black; that does not prove a plugin crash. Successful installation requires stable active/running service/PID/restart checks and verified files/registry, then a person must test GUI/audio. A failed recovery/start leaves logs and a lock/review marker; it is never reported as success.

No software watchdog runs while power is off or can repair a failed disk/SSH/network/hardware. Backups and checkpoints are synced BEFORE host stop. After a power cut, recovery is persistent and manually executable when SSH returns; automatic boot-time recovery has NOT been added or claimed. The package does not change firmware, boot services or projects. If storage or the host cannot recover, preserve evidence and use the independent computer backup with a reviewed recovery procedure; do not try another installation.
