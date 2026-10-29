# GHOST 2.4.2 installer2-rc2 — targeted XML path repair

## Demonstrated cause

The retained `20261028-first-install/HARDWARE_INSTALL_REPORT.md`, `install.log` and `COMMAND_RESULTS.json` show one rc1 invocation refused before creating a transaction or stopping acvs. The numeric entity `&#61480;` was accepted syntactically but not decoded by `xml_contract.awk`. Its residual ampersand failed `safe_path`; the generic error incorrectly asserted overlap.

61480 decimal = 0xF028 = U+F028, a Unicode private-use character, UTF-8 EF 80 A8. It is not slash, whitespace or a filesystem separator. Its visual glyph has no bearing on path identity. Decimal, hexadecimal and literal representations of the same scalar are equivalent after exactly one XML decoding pass. U+F028 and an absent character, a space, slash or another private-use scalar are NOT equivalent. No Unicode normalization, case folding or glyph-based aliasing is performed.

## Changes from rc1

- Decode XML decimal/hex references and the five named entities once, in order, using portable AWK arithmetic and UTF-8 byte emission under LC_ALL=C. No remote Python, base64, GNU timeout or new dependencies.
- Reject malformed/unknown references, overflow, NUL, forbidden XML controls, surrogate code points and XML-disallowed FFFE/FFFF. Reject decoded Location controls before line-oriented path comparison, preventing injected extra path records.
- Preserve strict `safe_path`, actual filesystem canonicalization and bidirectional discovery/root containment checks. Encoded separators become actual separators and are checked as such; encoded traversal/unsafe characters still refuse. No double decoding.
- Differentiate unsupported path characters from demonstrated containment in diagnostics.
- New read-only path preflight sends only parser/function definitions through SSH stdin. It reads settings twice, compares native AWK output byte-for-byte with local ElementTree, then runs exact candidate canonical containment checks. No installer entry point, remote temp file, copy, settings edit or service operation.
- Package revision is installer2-rc2; public product version remains 2.4.2.

The six changed package members are SHA256SUMS, xml_contract.awk, common.sh, transaction.sh, cleanup.sh and mpc-plugin.json. All 366 portable runtime members match rc1 byte-for-byte, including audio binary, UID, GUI, parameter mappings and presets. Published v2.4.2 and PR #571 are untouched. rc1 and its failed physical evidence are retained.

## Reproduce read-only gate

From this source directory, with a NEW local output directory:

```sh
python3 tools/ghost_path_preflight.py \
  --candidate ../dist-rc2/GHOST-2.4.2-installer2-rc2-mpc-armv7.zip \
  --host root@DEVICE_IP \
  --recovery /storage/GHOST-Recovery --work /storage/GHOST-Work \
  --out ../hardware-sessions/rc2-fresh-path-preflight
```

To inspect saved settings without any SSH, substitute `--settings-file /path/to/private/MPC.settings` for `--host`. Output contains hashes/counts, not volume names or XML. Keep full historical settings private.

This gate is not the whole installation preflight. Before any separately authorized attempt, rerun the general read-only service/registry/backup/mount/capacity checks, verify exact candidate SHA, verify all 366 installed files and independent backup, and check that previous rc1 incoming files are retained and no transaction/lock is active. Do not adopt unexpected settings or registry changes automatically. No update/uninstall/rollback tests on physical hardware are authorized here.

## Remaining boundaries

The rc2 route gate passed against all seven real content locations using the MPC's own AWK and filesystem resolution, without device writes. Settings SHA stayed 0c87ff5883a40825824f78c7319edcde1fbb8c28acc06f690b4331ccd4969cb4. This is not a physical installation or proof of service shutdown/recovery, GUI, audio or Q-Link operation. Existing conservative path restrictions intentionally refuse unsupported names (including literal ampersands/quotes) rather than guessing. A new discovery location or concurrent settings change must be reviewed.

Decision: GO for a separately authorized supervised second installation attempt, conditional on fresh complete preflight. Installation, update and uninstall of rc2 remain NOT TESTED on hardware. STOP pending explicit authorization.

## Final validation results

- Existing 79: 56 hardened transactional tests PASS on final rc2 source; 23 historical simulations PASS on unchanged published v2.4.2 ZIP with its documented desktop-recovery predecessor. These 23 are historical baseline coverage, not claims of testing old production hooks in rc2.
- New: 10 regression tests PASS, including the anonymized real entity, decimal/hex/literal equivalence, UTF-8 boundaries, malformed/XML-invalid scalars, single-pass named entities, distinct Unicode names, real containment, encoded separators/traversal/control injection, canonical filesystem aliases, and a full simulated transaction with the encoded mount name.
- Shell syntax PASS; ShellCheck 0 warnings/errors at warning severity. Catalog errors 0; the same 2 custom install/uninstall warnings require maintainer review.
- ZIP integrity and every internal checksum PASS. All 366 runtime members unchanged; audio binary SHA256 588019130b31ced7077f7e4afe35bd23b0753df7a2959e2af39fa825e1b81afd.
- Real read-only path gate PASS against final ZIP; no remote temporary file, settings mutation or service command was used.
- Initial local runs with sandbox-denied ps or the wrong historical predecessor fixture were corrected at the harness invocation level; they are not product PASS evidence. Final logs in dist-rc2 are the authoritative successful runs. No production safety checks were bypassed.

Final candidate SHA256: `618957908dc7dc9778a7686346ba8a01a3b7d483259b6f798b7fc35516111b2c`.
