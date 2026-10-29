> Historical preparation report. See GHOST_HARDWARE_TEST_RESULTS.md for the completed 29 October 2026 hardware sequence and owner confirmations.

# GHOST 2.4.2 installer2-rc3 — full legacy compatibility review

29 October 2026 (Australia/Brisbane). Installer-only work. No installation or service operation authorized/performed in this investigation.

## Complete existing-installation audit

Fresh actual filesystem snapshot:366 regular files,12 directories,52 FXP; no missing payload files and no unknown extra files. All original regular files are mode0644, numeric owner501:20; directories0755 root:root. These are observations, not reasons to reject a valid readable shared library. No symlink/special file or nested filesystem was found. The source binary remains ARMv7 EABI5 hard-float, SHA256 `588019130b31ced7077f7e4afe35bd23b0753df7a2959e2af39fa825e1b81afd`.

Every file was compared, not only the first metadata collision. Exactly two byte differences exist versus the community portable payload:

| File/condition | Actual predecessor | Resolution |
|---|---|---|
| plugin-meta.xml | Valid exact template with `%payload-path%` expanded to `/storage/Synths`; SHA2560d8bc796…54149 versus template89e0f860…edf7 | Accept only exact expansion for the current canonical target, plus the pinned template; other attributes/paths still refuse |
| mpc-plugin.json | Pinned desktop manifest SHA2562ba63403…6d04; only `about` and `requires` descriptive fields differ from portable manifest47ed6069…aa36 | Existing shipped legacy manifest already pins these bytes; shared adoption recognizes that exact known predecessor, not arbitrary JSON edits |
| .ghost-owned.sha256 | Absent in desktop predecessor | Bootstrap using shipped trusted manifests and exact expanded metadata; generate package ownership only after safe staging |
| Existing ownership record | Previously could claim arbitrary paths if syntactically valid | Require exact match to a recognized shipped manifest; unknown claims refuse before a transaction |
| Presets and indexes |52 FXP +3 indexes, byte-identical; user variants also supported | Retain all55 files in place in the stage during install/update/uninstall; preserve unknown/edited files everywhere |
| Permissions/ownership | Legacy files0644 owner501:20 | User/preset metadata retained by cp-a; recognized replaced runtime can normalize to package/root ownership. Backups retain original modes/owners for restoration. No runtime executable-bit assumption introduced |
| Generated files | No existing ownership record; prior completed aborted recovery packet exists outside discovery | New ownership record is installer metadata, not a new runtime/DSP file; old packet retained until explicitly authorized verified export |
| Registry | One GHOST UID47485354 / decimal1195922260, targetghost.so,83 total | Existing valid entry preserved/replaced only as GHOST; early guard refuses duplicate UID at another path or a foreign entry inside the target |

The registry's inherited version string2.0.0 matches plugin-meta.xml and the previous installation. It is not a binary version mismatch. The source-approved binary/package is GHOST2.4.2. The other364 runtime bytes, all FXP, GUI, UID, programs and automation are unchanged. After adoption the two known metadata files use the community payload; registry paths are expanded, as required by the existing community model. No generic normalization or user-content overwrite is performed.

## Corrections and remaining workflow audit

`adoption.sh` is one read-only classifier used both before transaction allocation and after the verified before-image is copied. It emits explicit dispositions for every expected package file. Only recognized owned bytes are removed from the stage for replacement/uninstall; unknown non-colliding files and every preset/index survive. Unknown runtime modifications, metadata identity/path edits, directories where files should be, special files and forged ownership records still refuse. Post-copy concurrent-change checks, settings boundary, atomic swap, serialized watchdog/rollback and stale-lock protections remain enabled.

The original desktop fixture is reconstructed from the exact approved runtime, sanitized metadata templates and observed366-file layout/modes;82 anonymized foreign registrations and the numeric-entity content-location case are included. Its ownership manifests are pinned to shipped predecessors, not regenerated from whatever happens to be installed. Tests exercise existing52 FXP, edited and root-level user files, real predecessor adoption and subsequent community-owned states.

One predictable future blocker was identified: the retained rc2 aborted attempt occupies1/3 recovery slots. Three new frontend transactions would fill the quota before uninstall. Do not raise or disable the limit. The prepared sequence explicitly exports/verifies the older completed rc2 packet after a successful first rc3 install, when it is no longer newest; the independent export and Mac evidence remain. This checkpoint is tested offline and requires explicit physical authorization. No cleanup was performed here.

A local test-harness race was also corrected: concurrently running suites used to recompile the same macOS SHA adapter. Each process now compiles into its own temporary directory, and the adapter supports stdin like BusyBox. The initial failure is retained as evidence; final passing runs are authoritative. No production test bypass or DSP build was introduced.

## Real read-only dry run

The exact classifier and shared shell functions are sent over SSH stdin. Existing retained rc2 package resources are used only as read-only inputs after checking their bytes against current manifests/templates. The community installer itself has no dependency on that historical directory. Nothing is uploaded or staged, and no installer/recovery/service entry point is invoked.

Actual result:311 recognized owned runtime files,55 preserved preset/index files,0 unexpected runtime conflicts. Native add/remove registry predictions are83/82 entries; all foreign entries and non-GHOST preferences are structurally identical. Before/after real tree contents/modes/owners, settings bytes and host state are stable. The seven discovery paths, mounts, root permissions, lease boot/PID/start identities and old packet script checksums are verified read-only.

Current service:active/running PID337, NRestarts0, new boot identity compared with yesterday; stable during inspection, no fresh crash flags. Current settings SHA2563e63a9f31411b983c4a6b7ce5d698d0d5fccfaecc67d0548eef9db27098a21b1; the only structural preference difference from the prior inspection is SixteenLevelsType. All83 binary inventory lines are unchanged, including verified MPC-CORE and PD LAB. No historical settings file is installed or baseline silently applied. Current independent Mac backup SHA256544c4702b0822eda8ca721cda60b8156f3a1a38c08281e715b61d0540326cb32; archive changes include prior authorized directory-timestamp changes, not new runtime bytes.

Current free storage481864KiB (~470MiB), MemAvailable1204720KiB (~1.15GiB); sufficient for the measured copies. One aborted completed packet, no active global lease/worker/guardian; root ownership0700, same target filesystem and rw/exec requirements pass. Values require a fresh check before any future authorized write.

## Qualification and decision

Final test totals, checksum, catalog result and runtime identity are in VALIDATION.json and evidence/rc3. The candidate packager refuses to create rc3 unless all18 full legacy migration tests pass. The366 portable runtime files must match rc2 byte-for-byte. No published asset or PR571 change is permitted.

**GO for review and a newly authorized supervised hardware sequence, conditional on fresh preflight and the explicit old-packet export checkpoint.** This is not a release-publication GO. Actual rc3 host shutdown/start, activation, watchdog failure recovery, loading, GUI/audio, update and uninstall remain NOT TESTED. No new physical installation may be inferred or performed from this investigation.

## Final results

-18 complete legacy migration/adoption tests PASS, including real366/52FXP format, install/update/reinstall/uninstall, direct legacy uninstall, exact rollback, interrupted install/update/uninstall, injected copy/registration failures, modified metadata/runtime refusal, forged ownership, file/directory collisions, duplicate/foreign registry conflicts and verified older-packet export.
-56 transactional regressions PASS;10 XML/path regressions PASS;84 relevant offline tests total. The historical23 tests of the unchanged public ZIP were not needlessly repeated and are not counted in this total.
-Shell syntax PASS; ShellCheck v0.11.0 has0 warnings/errors at warning severity. Catalog checker pinned a09c6e6b…:0 errors,2 custom-script warnings, DEFER=true.
-ZIP/internal hashes PASS; all366 portable runtime files byte-identical to rc2, approved binary58801913…81afd. A second independent package build reproduced the identical ZIP.
-Final exact-candidate native read-only dry run PASS and seven-route gate PASS. All predicted registry changes preserve82 foreign entries and unrelated preferences; no actual registry change occurred.

Candidate SHA256: `0920fde1c908e9a3dcdde5182dffeb206b63b8e706e16c7fb46839a9b0be0b7e`.
