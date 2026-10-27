# GHOST 2.4.2 - community beta

Save your project and back up your music first. Gen1 ARMv7 only, root shell/SSH, existing BusyBox tools and systemctl. The audio binary was physically tested on original MPC One / Hakai 3.9.1. This NEW device-side installer has only offline simulation validation. Other devices/firmware and catalog batch installation have not been physically verified.

Extract this folder, transfer it whole to the device, and run from its root shell:

    sh install.sh -t /YOUR/Synths

The official default is /sdcard/Synths. Select your actual writable executable Synths path. No automatic download or remote Python. Uninstall:

    sh uninstall.sh -t /YOUR/Synths

-y skips confirmation. -n is for catalog batch callers ONLY: the caller must already have stopped MPC and must restart it even on error. Our transaction does not take over that service ownership.

The operation retains complete plugin/settings snapshots in Synths/.ghost-recovery/community-SESSION, including prior-active, backup, rollback.sh and logs/checkpoints. No backup is deleted automatically. Only GHOST's registry token and directory are changed. Unknown/modified user data are preserved; conflicting modified runtime files refuse before service stop. Backup and free storage are required. A custom matching runtime file cannot be distinguished from a package byte-identical copy; it has identical content and is covered by the retained full backup.

Errors restore the exact known pre-operation registry and original directory, then restart the host unless -n. An independent detached watchdog detects worker loss/deadline; it cannot operate without power or repair failed storage. Recovery from an authorized root SSH shell:

    sh /YOUR/Synths/.ghost-recovery/community-EXACT_SESSION/rollback.sh /YOUR/Synths/.ghost-recovery/community-EXACT_SESSION

Do not use another transaction's snapshot. Unexpected concurrent settings changes cause refusal/review rather than overwriting preferences. No projects or external FXP are converted. RRF1 project states may not load in older binaries; use copies. Published Quick Start and PDF describe existing controls. The separately named desktop recovery ZIP is the original computer-side package, not this device-shell installer.
