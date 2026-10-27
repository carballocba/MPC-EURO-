# Minimal installer differences from upstream

Pinned template reference: sd88me/mpc-vst-plugins 7d3ba63e8ae29b8392b34b83274d7235175f8afb. Official portable layout and unmodified plugin_list.awk retained; -y, -n, -t interfaces retained. Custom scripts therefore generate expected catalog warnings requiring human review.

The old directory is retained outside the target, not deleted before registration. Full snapshot/hash checks, staging, registry foreign-content comparison, adjacent atomic settings rename, automatic rollback and detached worker watchdog are added. -n never starts/stops the host; the batch caller retains that responsibility. No project, foreign plugin, or arbitrary historic settings snapshot is a target.

A .ghost-owned.sha256 records package file hashes. For the exact prior community package, legacy-owned.sha256 supplies its frozen path/hash ownership. Only unchanged known-owned files are removed. Unknown files and modified presets survive update and uninstall; modified runtime collisions refuse rather than overwrite. Previously unrecognized legacy releases may require review and are not blindly adopted. Backups stay outside GHOST and are never deleted automatically.

Runtime/skin/binary/FXP bytes are unchanged. This device-side installer has simulation evidence only. The prior physical test covers the same audio binary and previous desktop installation method, not this new transaction.
