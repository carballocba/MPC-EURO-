# Draft only - do not post without owner approval and complete evidence

Thanks for the detailed review. We have prepared an installer-only hardening candidate; the published v2.4.2 ZIP/tag and GHOST audio/GUI payload remain unchanged.

- The authoritative settings backup is now taken after confirmed host shutdown and a stable read. Preference-only shutdown saves are preserved, the plugin registry is compared across shutdown, and later concurrent writes still refuse.
- Recovery uses one atomic mkdir lease with atomically published boot/PID/start ownership. Worker, guardian and manual recovery cannot run folder/registry restoration concurrently; the watchdog waits for an active recovery child, including delayed service calls.
- Recovery/work roots are explicit and validated outside every configured content path. Same-filesystem work preserves atomic activation; verified backups can live on a different filesystem. Accumulation is bounded by quota/three-slot refusal, with explicit verified export-before-cleanup and protection for newest/incomplete recovery.
- Stale global locks are tied to exact process/boot/TX state. Incomplete recovery must finish before a dead lock is released. Unknown ownership fails for review, not blind rmdir.
- DEFER= is declared and -n leaves all service ownership to the caller. Production test-mode bypasses are rejected. Mount/space/architecture/privilege/path/package checks run before shutdown.

Offline evidence covers clean/update/reinstall/uninstall, preserved unknown and edited files, shutdown rewrites, concurrent settings, TERM/INT/KILL, watchdog/races, dead/reused-PID/boot locks, capacity/mounts, cleanup and cross-filesystem constraints. Exact final count/checksums are in the candidate engineering report. The catalog still reports the two expected custom-script warnings.

**New community installer physical install/update/uninstall: NOT TESTED.** Read-only inspection confirmed the expected active plugin and verified an independent Mac backup; the proposed external roots are absent, so provisioning/installation is blocked pending owner approval. No installer or service-control operation was performed. We will supply redacted terminal output, exact exit codes, service/settings observations, Synths/recovery listings and disk usage only after owner-authorized hardware tests. The earlier musical test validates the same audio binary, not this installer. Please keep the PR pending until that evidence and your installer review are complete.
