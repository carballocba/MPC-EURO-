# Hardware preparation validation

The original proof remains `60f2b25502a25d619c99c04d07ac503cc452828f`. This preparation adds guides, portable folder metadata, checksums and an artifact-only CI workflow. It does not change the DSP, ABI, controls, skin sources, vendor dependencies or Makefile.

Rechecked with the existing project tools and workspace-local pinned Python/Zig setup:

- `python3 tools/capture_validation.py`: 12 native groups, actual shared-library host test, ASan/UBSan with leak detection, 8 GUI groups and ARM ELF/ABI/dependency/export checks pass.
- `python3 tools/verify_proof.py`: original source/control/ABI tree unchanged; ARM SHA256 remains `8cfbcc08935cb2f57208e57d8ff81c8a7d4259e4af93b99c6233302800139104`; all **18** exported native skin files are byte-identical to the original proof. The committed baseline records those exact hashes.
- `make package`: complete manual payload and matching source; portable plugin-meta.xml, whole-package/plugin-folder checksums, outer ZIP hash and guides pass archive tests. Repeated packaging without changing source/check-out metadata produces identical ZIP bytes.
- Workflow uses SHA-pinned checkout/upload actions, contents:read, only a development-branch push trigger and no release/deployment/device-access step. It reruns all required checks, rejects proof drift and requires a clean source tree with the exact run commit before upload. Its source is included in the source ZIP.

Packaging retains `installer_included: false` and `hakai_3_9_1_verified: false`. Portable metadata is a preparation addition; it does not modify the host plugin list. Exact original-One/Hakai paths, service, content-location and mount behavior remain read-only device-confirmation requirements. The community source reference is separately pinned in HAKAI_INSTALLATION_COMPATIBILITY.md.

An Actions artifact conveys a binary even though it is not a GitHub release. This package therefore supplies its matching GPLv3 source/build/UI/test/CI files together with the binary, license and third-party notices. It does not incorporate a proprietary VST2 SDK or proprietary graphics. This does not establish device compatibility or blanket proprietary-host/trademark legal clearance; the original broader distribution review gate remains documented in PROVENANCE.md.

Fresh run logs/fingerprints, proof comparison and ELF inspection are uploaded with each successful artifact. Use those run-specific records rather than assuming the previously committed implementation logs describe a new runner. Artifacts last 30 days and normally require GitHub sign-in. The download/verification guide distinguishes the actual trial ZIP's hash from GitHub's artifact-container digest.

No device connection, installer execution, MPC.settings edit, other-plugin/repository change, research-branch/PR change, merge or release was performed by preparation.
