# BeatRepeat — download and later manual installation

**Preparation package only.** You can download, extract and check it on your computer now. Installing it on the MPC is a later step requiring separate approval and the compatibility checks below. This task has not accessed your MPC.

This is an experimental stereo effect with **mono wet repeats**. It is intended for the original ARMv7 MPC One/Hakai 3.9.1; actual device operation is untested. Use a disposable project, low monitor volume and no live-show dependency for the first trial. Keep your current firmware and other plugins unchanged.

## 1. Download on your computer

1. Open the successful **BeatRepeat hardware trial package** run on GitHub Actions for `dev/beatrepeat-armv7-proof`. Check the run's commit matches the preparation commit reported with the artifact.
2. At the bottom, click the **BeatRepeat-ARMv7-trial-<commit>** artifact. GitHub generally requires signing in. Artifacts expire after 30 days; a run page remaining visible does not mean its download is still retained.
3. Extract GitHub's download once. It contains the actual `MPC-EURO-BeatRepeat-armv7-proof.zip`, its `.sha256` text file and validation evidence. Keep the source ZIP and licenses, not just the .so.
4. Compare the complete 64-character SHA256 of the actual trial ZIP against the `.sha256` file. Do not compare GitHub's transport ZIP to the inner ZIP's hash.

On Windows PowerShell, in the folder with the actual trial ZIP:

```powershell
Get-FileHash .\MPC-EURO-BeatRepeat-armv7-proof.zip -Algorithm SHA256
Get-Content .\MPC-EURO-BeatRepeat-armv7-proof.zip.sha256
```

On macOS:

```sh
shasum -a 256 MPC-EURO-BeatRepeat-armv7-proof.zip
cat MPC-EURO-BeatRepeat-armv7-proof.zip.sha256
```

On Linux:

```sh
sha256sum -c MPC-EURO-BeatRepeat-armv7-proof.zip.sha256
```

A mismatch means stop and download again. The run also displays a GitHub artifact digest; that is a separate integrity value for GitHub's artifact container.

## 2. Open the actual trial ZIP

It contains:

- `MPC-EURO - VST - BeatRepeat/`: beatrepeat.so, version.xml, plugin-meta.xml, Plugin Skins/TUI.json, Q-Links.json, original images, manifest and license notices.
- `MPC-EURO-beatrepeat-source.zip`: matching source/build/UI/test/CI files.
- `SHA256SUMS`: all package contents; the plugin folder also has its own checksums.
- `INSTALL.md`, `ROLLBACK.md`, `documentation/`: this guide, recovery steps and the hardware trial checklist.
- `pluginlist-entry.xml`: an inspect-only `/sdcard/Synths` example. Do not paste this if your confirmed location differs.

The manifest records the original implementation commit, packaging source commit and whether the checkout was dirty. Accept only a successful run's clean package. Identity: **BeatRepeat / MPC-EURO**, UID **45754272** (EuBr).

The ZIP is a manual payload, not a canonical community installer-app ZIP. There is no install.sh. Do not use the installer app's ZIP-drop feature, run scripts found online, or assume copying automatically registers it.

## 3. Stop before copying anything to the MPC

Read HAKAI_INSTALLATION_COMPATIBILITY.md in documentation/. Confirm these items through a separately approved read-only check, with a helper if needed:

| Required fact | Write the confirmed value |
| --- | --- |
| Original MPC One, exact OS/Hakai version | __________ |
| ARM32 hard-float/VFP/NEON and required libraries | __________ |
| Active MPC host service (acvs or inmusic-mpc) | __________ |
| Exact active MPC.settings file | __________ |
| Chosen executable Synths folder, included in content locations | __________ |
| Existing BeatRepeat UID/folder/library collision? Must be none | __________ |
| Off-device backup location and recovery helper | __________ |
| Separate approval for the precise install/registration changes | __________ |

The community default is `/sdcard/Synths`; **your confirmed value takes precedence**. Hakai may use inmusic-mpc rather than acvs. Multiple settings files, missing pluginList-arm, a noexec drive, a missing content location or an existing UID/folder mean stop and review; do not patch/remount, create guessed settings fields or overwrite anything.

Registration normally changes MPC.settings. If that change remains prohibited, **installation cannot proceed**: copying the folder alone is not a working registration procedure.

## 4. Later approved installation — helper-assisted

These steps are a future procedure, not an instruction to install during preparation:

1. Save your current project and make an off-device project backup. Use a new empty trial project later.
2. Have the helper stop the **confirmed active host service** and verify that the MPC application has exited. Never edit its settings while it is running.
3. Copy the exact active settings file to a uniquely named backup on the device **and to your computer**. Record the paths. Preserve existing plugins and preferences.
4. Copy only the complete `MPC-EURO - VST - BeatRepeat` folder into the **confirmed Synths directory**, using SFTP/file transfer. Do not copy the source ZIP, documentation or entire outer ZIP into Synths. Refuse any replacement/overwrite prompt.
5. Verify the copied folder's checksums using an existing device tool, or read it back and compare on your computer. Confirm its content path is already searched; adding a new content location is a separate change, not an automatic workaround.
6. The helper expands `%payload-path%` in plugin-meta.xml to that confirmed Synths directory and adds **only this single VST entry** inside the confirmed pluginList-arm/KNOWNPLUGINS section of a temporary copy of the active settings. Retain every other entry. Validate XML and review the complete before/after difference before replacing the active file. Missing/ambiguous structure means stop, not rebuild the entire list.
7. With the host still stopped, apply only the reviewed settings addition, then start the **same service** that was stopped. Retain the backup. If any step fails, preserve evidence and follow ROLLBACK.md before retrying.
8. In an empty trial project, find BeatRepeat in an **audio effect insert**, not as an instrument. Follow HARDWARE_TRIAL_GUIDE.md. It is not verified merely because its name appears in the browser.

No scanner/sync/prune, service patch, firmware update, drive-exec patch, other plugin replacement or release publication is part of this trial. Prefer an experienced helper for registration; the guide does not ask a musician to experiment with system XML.
