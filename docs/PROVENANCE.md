# Provenance, dependency closure and distribution policy

## Inspected inputs

| Input / author | Exact source | Terms / use |
| --- | --- | --- |
| BeatRepeat, Zack Scholl / Infinite Digits | [`_core/lib/beatrepeat.h`](https://github.com/schollz/_core/blob/66ee010f822c915adb893c8c03279e30a52bd839/lib/beatrepeat.h), [fixedpoint](https://github.com/schollz/_core/blob/66ee010f822c915adb893c8c03279e30a52bd839/lib/fixedpoint.h), [fade generator](https://github.com/schollz/_core/blob/66ee010f822c915adb893c8c03279e30a52bd839/lib/crossfade4.py), [LICENSE](https://github.com/schollz/_core/blob/66ee010f822c915adb893c8c03279e30a52bd839/LICENSE) | Headers explicitly Copyright 2023–2025 Zack Scholl, GPLv3.0; repository GNU GPL v3 text. Unmodified audit copies in vendor/core; GPL-3.0-only derivative in src/repeat.c. |
| SDK-free MPC ABI and skin tooling, sd88me | [`wrapper/vst2_wrap.c`](https://github.com/sd88me/mpc-vst-plugins/blob/ce6278d53091ba40127838020fc8a7887894551f/wrapper/vst2_wrap.c), [tools](https://github.com/sd88me/mpc-vst-plugins/tree/ce6278d53091ba40127838020fc8a7887894551f/tools), [LICENSE](https://github.com/sd88me/mpc-vst-plugins/blob/ce6278d53091ba40127838020fc8a7887894551f/LICENSE) | MIT, copyright 2026 sd88me. ABI extracted/adapted; shadow_skin.py, skin_assets.py, skin_check.py, shadow_art.c retained unchanged. Other catalog plugins/assets not imported. |
| Nested force-shadow renderer, sd88me | [community vendor README](https://github.com/sd88me/mpc-vst-plugins/blob/ce6278d53091ba40127838020fc8a7887894551f/tools/vendor/force-shadow/README.md) identifies upstream [`fa456fc90d07951723ab5f4e643d906cd2ac1bca`](https://github.com/sd88me/force-shadow/tree/fa456fc90d07951723ab5f4e643d906cd2ac1bca) | MIT notice retained. render_conf_preview.c unchanged. UPSTREAM.md is its original copy instructions, **not a claim that our glyph table is unchanged**. |
| stb_truetype v1.26, Sean Barrett | Header in nested renderer above | Explicit alternative MIT/public-domain notices retained verbatim at end of header. Offline font rasterization only; not linked into plugin. |
| DejaVuSansMono, DejaVu/Bitstream | [DejaVu project](https://dejavu-fonts.github.io/); unchanged TTF from Debian fonts-dejavu-core 2.37-8 | Bitstream Vera font license; DejaVu changes public domain. Full package copyright/grant retained in vendor/fonts/LICENSE. Baked typesetting and preview; no font installed on device. New fallback glyph table generated from this font by tools/gen_font.py. |
| Zig 0.13.0 compiler/runtime, Zig contributors | [tagged source](https://github.com/ziglang/zig/tree/0.13.0), [compiler_rt](https://github.com/ziglang/zig/tree/0.13.0/lib/compiler_rt), [license](https://github.com/ziglang/zig/blob/0.13.0/LICENSE), hash-pinned PyPI ziglang wheel | MIT notice retained in vendor/zig/LICENSE. Compiler runtime helpers may be linked; the wheel includes their source. Toolchain version/download hash fixed in tools/zig-requirements.txt. Compiler and ordinary system libraries are not plugin source or hardware dependencies. |
| glibc/libm/libpthread | Dynamic host system libraries | GNU libc LGPL/system-library terms; not shipped in this package. No private Akai or Hakai library is linked. |

The community bitmap font header did not identify the original typeface in its vendored subset. We replace its **glyph data** with a reproducible DejaVu-derived table, avoiding an unsupported asset-provenance assumption. MIT renderer code remains unchanged. All new layouts, colors, fragment patterns, source and documentation are original project contributions under GPL-3.0-only; the font keeps its own license. No Akai, Noise Engineering or third-party plugin panel/logo/assets are copied.

## Source integrity

These SHA256 values identify the unmodified pinned audit inputs:

```text
be901a9a53bad2efc1b153c503321498e51ec120814add9ed8413cb77cceadd4  vendor/core/beatrepeat.h
3a1e93768cd56365bc890417d21de4cdf10f8e3b5ccd7f57a079fa3abaf7500a  vendor/core/fixedpoint.h
13728f4794d5c2c743acc799249a406b0223d29ca339e6d356713e888cd4b32c  vendor/core/crossfade4.py
cd39062f678ab4e84711550c15b03453ad720bec796746670eb174a5cf8a0bcf  vendor/mpc/tools/shadow_skin.py
b3341728ae0a0d80b349a54494b621d88cb232966017aae4077517cdd9b0345c  vendor/mpc/tools/shadow_art.c
54bf827eb99404e8f430c330ad30f063334f637eba0109b6a18d4f566a8e9dd8  vendor/fonts/DejaVuSansMono.ttf
```

Adaptation changes are explicitly described in ARCHITECTURE.md and source headers. The original int16 ring size/indices assume 44.1 kHz and embedded buffer sizes; the proof widens them, validates freshness, removes arithmetic UB and adds a resumed-recording splice. The production dependency closure is C11 + the three system libraries. Daisy/STM32/RP2040 boards, `_core` firmware integration, sampling assets, sequencers and unrelated firmware licenses are excluded.

## GPL obligations and VST2 boundary

The combined DSP plugin is GPL-3.0-only, **not MIT simply because its wrapper is MIT**. MIT incorporation is compatible with GPLv3 when notices are retained. Modifications must remain available under GPLv3, include prominent modification/provenance notices and the license, and offer complete corresponding source using an appropriate GPLv3 §6 method when conveying binaries. Corresponding source includes this exact adapted DSP, wrapper, registry, native skin sources/generated reproducible assets, vendored dependencies and build/package scripts. `make package` supplies the local matching source archive alongside the binary and retained notices; its manifest hashes the source archive/tree and records whether the checkout is dirty. A source-only draft PR does not itself publish a binary release.

For a future binary distribution, deliver the exact matching source together or provide compliant equivalent access; preserve notices, do not add incompatible restrictions, and assess installation-information obligations if conveying a GPLv3 User Product (§6). Merely pointing to a moving upstream repository is insufficient. Preinstalled ordinary system libraries/compiler runtime fall within the GPL's system-library/toolchain analysis; the pinned toolchain and runtime source are available through the referenced wheel/source tree. No GPL firmware samples or external media are redistributed.

**No proprietary Steinberg VST2 SDK headers, libraries, samples or license agreement are used.** ABI declarations come from the explicitly MIT community source. SDK-free implementation avoids bundling that SDK; it does not establish blanket trademark, patent, interoperability or proprietary-host distribution clearance. The implications of distributing a GPL plugin used with a closed host must be reviewed for the actual distribution arrangement. The approved project scope reserves final binary-distribution review; no release, installer, device registration or claims of legal clearance are made here. This is a project review gate, not an additional restriction on GPL rights.

Names such as Akai MPC, Hakai, VST2 and Infinite Digits are descriptive source/target references, not endorsements. No trademark grant was identified in the selected `_core` files; GPL grants do not grant trademark rights. The plugin uses the independent MPC-EURO / BeatRepeat identity rather than an official Ectocore product identity. Official proprietary Noise Engineering DSP is not included.
