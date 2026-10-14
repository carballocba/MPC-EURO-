# Hakai 3.9.1 installation evidence and confirmation checklist

This is a source-based preparation review. **Exact installation compatibility on the user's original MPC One has not been verified.** No device was contacted, no installer was run and MPC.settings was not changed.

Reference snapshot: `sd88me/mpc-vst-plugins` at **e18a0a1da84515096d354f399dd4cd7f9c079fb5**. It is an installation reference only; the proof's DSP/ABI/skin dependency pins remain unchanged.

## What the inspected community sources establish

| Item | Evidence | Consequence for this trial |
| --- | --- | --- |
| Native folder | [Catalog specification](https://github.com/sd88me/mpc-vst-plugins/blob/e18a0a1da84515096d354f399dd4cd7f9c079fb5/docs/CATALOG_SPEC.md#plugin-folder) requires the .so, version.xml, Plugin Skins and plugin-meta.xml in one folder. Metadata uses `%payload-path%/<folder>/<so>`. | Our ZIP includes a complete independent folder and this portable metadata; copy the folder as a unit. |
| Registration | [README device details](https://github.com/sd88me/mpc-vst-plugins/blob/e18a0a1da84515096d354f399dd4cd7f9c079fb5/README.md#device-details) and [release guide](https://github.com/sd88me/mpc-vst-plugins/blob/e18a0a1da84515096d354f399dd4cd7f9c079fb5/docs/RELEASING.md#what-the-installer-does) describe a VST entry in `pluginList-arm` / `KNOWNPLUGINS`, read at host startup. | Folder copying alone is insufficient. Actual registration is a separately approved MPC.settings change, outside this task. Do not assume an ordinary plugin rescan imports arbitrary folders. |
| Settings discovery | [Installer line 46](https://github.com/sd88me/mpc-vst-plugins/blob/e18a0a1da84515096d354f399dd4cd7f9c079fb5/tools/release/install.sh#L46) checks `/media/az01-internal/Settings/*/MPC.settings` and `/data/Settings/*/MPC.settings`, or an explicit MPC_SETTINGS override. | These are discovery candidates, not verified paths for this MPC. If several files exist, first-match selection is not proof of the active profile. |
| Hakai service | [Installer lines 66–71](https://github.com/sd88me/mpc-vst-plugins/blob/e18a0a1da84515096d354f399dd4cd7f9c079fb5/tools/release/install.sh#L66) describe acvs on stock firmware and inmusic-mpc on Hakai-enabled systems; choose an existing service. | Confirm the **active host service**, not merely that a service file exists; never blindly stop acvs or use the script's fallback when discovery fails. |
| Storage / skin search | Installer checks mount `noexec` and whether the Synths path is present in content settings. The [installation guide](https://github.com/sd88me/mpc-vst-plugins/blob/e18a0a1da84515096d354f399dd4cd7f9c079fb5/catalog/pages/install.md) documents drive/content-location issues. | Determine the actual executable storage and SynthContentLocations. `/sdcard/Synths` is the community default, not a guarantee that this path is mounted, executable or searched on this device. Do not remount or apply drive patches for this trial. |
| Architecture / libraries | README reports ARM32 Gen1, VSTPluginMain and glibc-based OS-version differences; reference hardware includes Force 3.9.1 and MPC OS 2.x units. | This is community evidence, not an original-One/Hakai 3.9.1 test. Our binary is hard-float ARMv7, VFPv3/NEON, requires libc/libm/libpthread and GLIBC ≤2.27 symbols. Confirm actual userland and libraries. |
| UI versions | README describes newer native skin versions on OS 3.x and different OS 2.x shapes. | Our existing 3.x-shaped skin is preserved. Its eight bindings/six Q-Links pass native checks, but One/Hakai drawing, touch/bank behavior and notifier threading remain device tests. |
| Installer app | [Desktop README](https://github.com/sd88me/mpc-vst-plugins/blob/e18a0a1da84515096d354f399dd4cd7f9c079fb5/tools/desktop/README.md) consumes standard release ZIPs with install.sh/portable layout; registering folders is also a device-changing action. | Our artifact is a **manual trial payload**, not that app's canonical installer ZIP. Do not drop it into the app and assume automatic installation. No installer/uninstaller is shipped or run. |

## Read-only device confirmation required before installation approval

The musician should first record the model and exact displayed OS/Hakai versions. An experienced helper may then inspect the existing device environment **only with separate approval for device access**. These example commands are documentation, not commands run by this task:

```sh
uname -m
getconf LONG_BIT
getconf GNU_LIBC_VERSION
systemctl show acvs inmusic-mpc -p Id -p ActiveState -p FragmentPath
systemctl cat acvs
systemctl cat inmusic-mpc
ls -l /media/az01-internal/Settings/*/MPC.settings /data/Settings/*/MPC.settings
cat /proc/mounts
```

Some tools/paths may be absent; report that instead of installing utilities or changing services. Verify hard-float/VFP/NEON userland and the required libraries using existing tools. A version string alone is not a complete loader check. Inspect **only relevant existing settings fields** for the active profile: pluginList-arm, SynthContentLocations and the existing known-plugin entries. Do not send complete MPC.settings publicly; it can contain unrelated preferences and paths.

Check for both the UID `45754272` and name/path collisions, including `MPC-EURO - VST - BeatRepeat` and beatrepeat.so. Confirm which file the running host actually uses; if ambiguous, stop. Read-only mount/content/service confirmation establishes a proposed install plan, not permission to apply it.

Record the confirmed active service, exact settings file, chosen Synths directory, executable mount, content search location and backup destination in INSTALL.md. A safe later registration is a **targeted addition of this single UID**, with the host stopped, backup retained, existing plugin entries preserved and edited XML validated before replacement. Do not use whole-list scanners, sync/prune, patches, firmware changes or a guessed path.

## Readiness conclusion

The binary, native UI and matching-source package are verified in Linux/cross-build tests. The community registration mechanism and Hakai service distinction are verified **in the inspected source**. Exact original-One/Hakai 3.9.1 paths, registration behavior, loader and UI compatibility are **pending device confirmation**. Installation/registration and rollback are future, separately approved operations. The artifact is not a verified Hakai installer and must not be represented as one.
