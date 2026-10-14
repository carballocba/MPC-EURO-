# Build and local review package

## Native prerequisites

Linux x86_64, a C11 compiler with lock-free 32-bit atomics, make, Python 3, binutils (readelf/nm), pthread/libm, and Pillow. Validated with gcc 14.2.0, Python 3.12.14 and Pillow 12.3.0. Install Python dependencies in a workspace-local virtual environment if needed:

```sh
python3 -m venv build/venv
. build/venv/bin/activate
python3 -m pip install -r tools/python-requirements.txt
make test
make sanitize
make skin
```

The production native library is `build/beatrepeat-native.so`. Test executables directly link the same source to interpose prohibited realtime calls; the separate ctypes host loads the actual shared library. `make skin` builds the offline community renderer, generates native TUI/Q-Links/images and validates them against the real native plugin.

All generated registry/skin artifacts are reproducible from ui/ and the pinned vendor subset. The fallback glyph data is committed, with its reproducible `python3 tools/gen_font.py` generator and font. The renderer is a build-time program only.

## ARMv7/armhf cross-build

```sh
make arm
```

This automatically obtains the **hash-pinned Zig 0.13.0 x86_64 Linux wheel** into ignored build/toolchain, using TLS and pip --require-hashes --no-deps. A compatible Python package resolver/network connection is needed on the first run. The pinned wheel hash targets this validated x86_64 build environment; other build hosts require a separately verified wheel/hash or explicit toolchain path.

To use a previously obtained Zig 0.13.0:

```sh
ZIG_BIN=/absolute/path/to/zig make arm
```

`tools/build_arm.sh` compiles each C unit for `arm-linux-gnueabihf.2.31`, Cortex-A9/ARMv7-A code generation (VFPv3/NEON), with -O2, -fPIC, hidden visibility, -ffp-contract=off and warnings as errors. The linker strips debug data, removes unused sections, disables build IDs and applies `src/exports.map` so only VSTPluginMain is visible. No proprietary SDK, embedded SDK, C++/JUCE runtime or libatomic is needed.

The result is `build/arm/beatrepeat.so`; `tools/validate_arm.py` writes validation.json/readelf.txt and fails on wrong architecture, float ABI, exports, dependencies or glibc ceiling. Zig's compiler-runtime merge omits the final Tag_ABI_VFP_args attribute; validation checks **both source objects' VFP-register ABI tags** plus the linked hard-float ELF flag and ARMv7 attributes. This is documented rather than silently patching ELF tags. Highest actual required glibc is 2.27; 2.31 is the selected build ceiling, **not a verified MPC libc version**. ARMv7-A VFPv3/NEON and those system-library symbols must exist on the target.

The community's Docker route was inspected and an ARM gcc image was obtained, but this cloud host lacks ARM binfmt/QEMU support (exec format error). The working cross-build uses Zig and does not require running an ARM container. Neither QEMU nor physical ARM runtime tests have been performed.

## Full check capture and package

```sh
# ZIG_BIN is optional when using the automatic pinned installation.
ZIG_BIN=/absolute/path/to/zig python3 tools/capture_validation.py
make package
```

The first command stops on any failed native/sanitizer/skin/ARM check and keeps exact logs in build/validation. Run it before accepting a package. Packaging requires its passing input/binary fingerprints and fails if validated files have changed. `make package` rebuilds/validates native skin and ARM ELF, then creates and checks the actual archive, identities, checksums and matching source:

```text
build/package/
  MPC-EURO - VST - BeatRepeat/
    beatrepeat.so
    version.xml, plugin-meta.xml
    Plugin Skins/  (TUI.json, Q-Links.json, original PNGs)
    manifest.json
    LICENSE, NOTICE.md, LICENSES/, SHA256SUMS
  MPC-EURO-beatrepeat-source.zip
  pluginlist-entry.xml, INSTALL.md, ROLLBACK.md, SHA256SUMS
  documentation/
  MPC-EURO-BeatRepeat-armv7-proof.zip
```

The UID is `45754272` / EuBr, native identifier MPC-EURO.vst.beatrepeat, independent directory MPC-EURO - VST - BeatRepeat. The inspect-only XML entry follows the community `/sdcard/Synths/.../beatrepeat.so` effect convention. Its placement/path/scanning behavior on this MPC still needs approval and device validation. **No script installs files, edits plugin lists/MPC.settings or overwrites another plugin.** A separately approved installation can use Hakai's existing community workflow once its exact registration behavior is verified.

Packages include source and notices, not a release or installer. ZIP entries are ordered, use fixed 1980 timestamps and fixed modes. Repeating builds of unchanged source with the pinned tools is expected to be byte-identical and is checked during this proof; source commit/dirty metadata legitimately changes the package if the checkout state changes. Dependencies and generated binaries stay out of git. For clean-checkout reproduction, check out the recorded implementation commit, install the pinned prerequisites, run the check capture, then make package.

The hardware-trial workflow runs every required check, rejects DSP/ABI/UI drift from implementation commit 60f2b25, and uploads the ZIP, its SHA256 sidecar and validation evidence for 30 days. The source archive includes that workflow. See INSTALL.md: this is a manual native-folder package, **not** the community app's canonical installer ZIP. Portable plugin-meta.xml supports a confirmed content location without assuming /sdcard/Synths; actual targeted registration modifies the host settings and requires separate approval. The package includes no installer.
