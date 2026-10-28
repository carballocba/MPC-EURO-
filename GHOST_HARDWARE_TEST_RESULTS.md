# GHOST installer2-rc1 - hardware evidence, 28 October 2026

## Read-only preflight actually performed

The full prompt authorized Phase 2 read-only inspection. Only SSH reads were executed; no directory/file was created or changed on the MPC, no installer/recovery was invoked, and no service was stopped/restarted. Private evidence stays in ../hardware-sessions/20261028-readonly, outside this source repository/archive. Listings and du are BEFORE any trial, not post-install evidence.

- Model read from device tree: Akai Professional MPC One; uname: armv7l.
- Hakai 3.9.1 is the owner-reported target. The base os-release is not independent Hakai-version proof; fresh physical/version confirmation remains pending.
- acvs active/running, PID 3426, NRestarts=0, unchanged between two snapshots. No crash/segfault/restart red flags in the collected last 200 current-boot service journal lines. This limited observation is not a long stability test or proof that the whole boot had no incidents.
- 83 registered plugins: one GHOST UID 47485354, BeatRepeat absent. PD LAB and MPC-CORE Prototype present. All 83 registered file paths hashed successfully, no missing paths. The 82 unrelated plugin records were inventoried, not modified or automatically reconciled with an old personal baseline.
- Installed GHOST binary SHA256: 588019130b31ced7077f7e4afe35bd23b0753df7a2959e2af39fa825e1b81afd. 366 regular plugin files in the independent Mac tar; every extracted member hash verified against current MPC files using read-only sha256sum -c stdin. Archive SHA256: 06b2ca8a11de75a14087819a5951a3deaa992defc741dee8f9335a4684648007.
- MPC.settings SHA256 0c87ff5883a40825824f78c7319edcde1fbb8c28acc06f690b4331ccd4969cb4, byte-identical before/after the inspection. Current preferences were not changed/adopted from a historical file. The inherited PLUGIN version attribute is 2.0.0, matching the approved package metadata; it is not a statement that the current approved audio binary changed version.
- /storage available: 595556 KiB (about 581 MiB). MemAvailable: 1177952 KiB (about 1.12 GiB). These are preflight observations, not callback CPU/latency measurements.
- Proposed /storage/GHOST-Recovery and /storage/GHOST-Work do NOT exist. They were not created. No physical recovery/work-root capability or cross-filesystem behavior can be marked PASS before provisioning and revalidation.

**Installation decision: NO-GO until explicitly authorized provisioning and fresh root/path/mount/capacity validation.** The current plugin remains installed and active. The Mac backup is verified; a new external MPC recovery copy and independent supervised recovery shell are still pending before any mutation transaction.

## Device trial not performed

| Check | Status |
|---|---|
| Installer2 physical install / update / uninstall / restoration | NOT TESTED |
| Actual settings rewrite during clean acvs shutdown | NOT TESTED |
| Guardian / lease / rollback behavior on real MPC | NOT TESTED |
| Scanner behavior / absence of duplicate plugins after trial | NOT TESTED |
| New GUI / touch / Q-Link / audio / CPU / dropout session | NOT TESTED |
| Post-test Synths/recovery listings and final service restoration | NOT TESTED |

Historical owner report remains distinct: same BOTH FIX audio was musical and stable using the earlier desktop-controlled installer, with about 16% whole-host CPU without plugins and 30% with GHOST. This is not validation of installer2 or callback deadline performance. Existing historical backups remain untouched; no cleanup was attempted.

Do not post private settings/project names, addresses, full inventories or raw logs to PR #571. Prepare redacted physical evidence only after actual authorized tests and owner approval.
