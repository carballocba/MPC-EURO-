# Installer hardening development candidate - LOCAL / UNPUBLISHED

This branch prepares GHOST 2.4.2 installer2-rc1 in response to PR #571. The published v2.4.2 release/tag/assets are unchanged. No MPC modification or public update was executed. A read-only preflight was completed; installation is blocked until the owner authorizes recovery-root provisioning and revalidation.

Start with GHOST_INSTALLER_HARDENING_REPORT.md, GHOST_MPC_HARDWARE_VALIDATION.md and GHOST_HARDWARE_TEST_RESULTS.md. package-template is the canonical new runtime installer; community/device-ghost retains the historical v2.4.2 implementation for comparison. Use rebuild.py only to reproduce the already approved binary, then package.py --out dist to generate the clearly named installer candidate. No new audio build is required if the exact approved binary is supplied in rebuild/ghost.so.

---

# GHOST 2.4.2 - Community beta

A stereo buffer glitch effect: live repeat/stutter, reverse and generative rhythmic interventions. Original MPC One / Hakai 3.9.1 audio is user-tested. Same BOTH FIX binary, UID and controls. No new DSP, GUI, parameters or presets.

- [Quick Start](docs/GHOST_QUICK_START.md)
- [Five-page User Manual](docs/GHOST_2.4.2_User_Manual.pdf)
- [Downloads](https://github.com/carballocba/MPC-EURO-/releases/tag/v2.4.2)

## Install / remove

Save your project. Extract GHOST-2.4.2-mpc-armv7.zip and transfer the complete folder to your Gen1 MPC. From the device root shell run `sh install.sh -t /YOUR/Synths`. Remove with `sh uninstall.sh -t /YOUR/Synths`. Follow INSTALL.md; the official default is /sdcard/Synths, which may not be your actual content location. Root SSH, writable executable storage, existing BusyBox and systemctl are required. No remote Python or package installation.

New device-side installer: clean/update/reinstall/remove and injected-failure recovery are tested offline only, not on physical MPC. Audio binary is identical to the previously tested BOTH FIX. This is a prerelease, not a new hardware certification. Custom scripts follow -y/-n/-t, but differ from upstream templates; catalog maintainers still need to review them. -n leaves service restart to the catalog batch caller. Backups and rollback.sh persist outside GHOST under Synths/.ghost-recovery. Unknown and modified user files survive; runtime collisions refuse before host stop. Concurrent unexpected settings changes refuse rather than overwrite preferences. A watchdog cannot run without power or repair failed storage.

The separate GHOST-2.4.2-desktop-recovery.zip is the unchanged original computer-side controller, not the new device installer. Do not substitute their commands or transaction snapshots.

## Source and license

GPL-3.0-only. Retained MIT framework/ABI/tool, DejaVu/Bitstream and stb notices are in resources/Licenses and docs/community-release/CREDITS.md. Original pixel ghost and knob artwork have independent regeneration evidence. No proprietary SDK or firmware artwork is bundled. Unofficial; no Akai/inMusic endorsement.

Build exact audio: install Zig 0.13.0, set ZIG to its executable, then `python3 rebuild.py`. Expected binary SHA256: 588019130b31ced7077f7e4afe35bd23b0753df7a2959e2af39fa825e1b81afd. Package with `python3 package.py --out dist`; validate with `python3 community-tools/tools/catalog_check.py dist/GHOST-2.4.2-mpc-armv7.zip --catalog`. No access to a physical MPC is needed. package-template and community/device-ghost contain the final device installer; community/ghost retains the independent original desktop controller. Historical developer generators are reference material; use rebuild.py/package.py for this exact release.

RRF1 projects may not open in older binaries. Use project copies; rollback does not convert projects. 16 programs and 52 FXP are unchanged. Automatic external FXP browser import is not established.
