# LOCAL DRAFT - not opened, not pushed

Target repository: carballocba/MPC-EURO-
Base: codex/ghost-v2.4.2-release (published v2.4.2 source)
Head: codex/ghost-installer-hardening
Title: installer: harden GHOST 2.4.2 recovery and shutdown sequencing (offline RC)

Installer-only changes addressing sd88me/mpc-vst-plugins #571: authoritative post-stop settings baseline; atomic single-owner rollback; process-identity tracked/cancelled service commands; external validated recovery/work roots; bounded retention/export cleanup; safe stale-lock recovery; actual DEFER support; production test bypass refusal and filesystem/package gates.

56 expanded offline tests pass, including native local signals/concurrency and full payload checks. Existing 23 simulations against the unchanged public ZIP are retained separately as a baseline. The 366 runtime files remain byte-identical; approved audio SHA256 588019130b31ced7077f7e4afe35bd23b0753df7a2959e2af39fa825e1b81afd. Catalog validation passes with two expected custom-script warnings, now defer=true. ShellCheck warning-level analysis and POSIX syntax checks pass.

Read-only MPC preflight confirmed the existing 366-file plugin and stable observed acvs with 83 registrations; independent Mac backup was verified against every file. NO-GO for mutation: proposed external recovery/work roots do not exist. No directory provisioning, installer/update/uninstall/rollback, service restart or fresh audio test has been executed. Physical acceptance and owner publication approval remain pending.

Public v2.4.2 assets/tag and catalog PR remain untouched. This candidate is local/unpublished. No maintainer response may be posted until evidence and owner approval are complete. See the engineering report, physical guide and NOT TESTED result table. This draft is not evidence of maintainer/catalog approval.
