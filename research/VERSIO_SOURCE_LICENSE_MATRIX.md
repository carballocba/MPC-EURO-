# Versio source and license matrix

Research date: 14 October 2026. Categories describe the **specific inspected firmware/reuse route**, not a GitHub owner's whole catalog. No plugin release has legal clearance from this research alone. Repository snapshots and evidence labels are in [the catalog](VERSIO_PHASE2_CATALOG.md).

## Categories and accounting

| Category | Meaning | Count |
| --- | --- | --- |
| A | Source available, adaptation license present, technically promising | 6 |
| B | Source available, substantial technical/license questions remain | 5 |
| C | Binary/download available or advertised, source/permission not established | 8 |
| D | Expressly restricted, conflicting terms or unsuitable reuse route | 7 |
| E | Already-ported DSP family; useful primarily as reference | 3 |
| Total | Distinct third-party Versio firmwares; engines/versions not double-counted | **29** |

**9 publish source with an adaptation-permitting project grant** (6 A, Cithara B, Acidus/Plateau E). All still require review of the actual imported dependency closure. **19 need new or clarified firmware-reuse permission**; **1 further candidate, Clackotron, needs source access despite its MIT license**. Requests must be specific: permission, source access and technical clarification are different questions. Rings' existing MIT Mutable engine does not license the uninspected Versio adapter. BeatRepeat is an extra GPL-licensed non-Versio comparator, outside these counts.

## Per-firmware rights evidence

| ID / candidate | Class | Inspected grant / restriction | Reuse outcome |
| --- | --- | --- | --- |
| V01 WTF! | C | [Official page](https://2020.dubrussell.com/resources/wtf/) + single-bin archive; no source/adaptation license | Request source plus permission. No binary reverse engineering. |
| V02 FRGMNTS | D | [Publisher](https://acidclank.gumroad.com/l/frgmntsversio): “Unauthorized redistribution or commercial use is strictly prohibited.” | Separate source/adaptation/redistribution grant required, even for an independently named free plugin. |
| V03 MultiVersio | B | [README](https://github.com/fluffyaudio/MultiVersio/blob/52839534fe5dbb36baa6fd864aa7eec5369de4ed/README.md) invites improvements; no root LICENSE/main-program grant found. [Filter header](https://github.com/fluffyaudio/MultiVersio/blob/52839534fe5dbb36baa6fd864aa7eec5369de4ed/dsp/filter.h) has Emilie Gillet MIT notice | Partial dependency notices don't clear Paolo's integration/DSP additions. Ask for an explicit project license and provenance. |
| V04 Acidus | E (core) | [Firmware LICENSE.txt](https://github.com/abluenautilus/AcidusVersio/blob/ec8e429428b56da7afbd98e3a7ac29e6b6168ae6/LICENSE.txt) and [Open303 License.txt](https://github.com/abluenautilus/AcidusVersio/blob/ec8e429428b56da7afbd98e3a7ac29e6b6168ae6/open303/License.txt) explicitly MIT | MIT source can be adapted with notices. Existing MPC Open303 additions are GPL; don't relabel those MIT. Exact Acidus controls not claimed already ported. |
| V05 Plateau/Campestria | E (core) | [LICENSE.md](https://github.com/digitalartifactmusic/PlateauNEVersio/blob/4218b072e7420dd788cd3c98c36b3eba445f8886/LICENSE.md) says GPLv3-or-later; Signalsmith MIT and other notices retained | Existing PlateauXXL is GPLv3-or-later with separate NC artwork. Prefer cleared core/reference; do not copy NC assets into unrestricted-artwork package. |
| V06 Repetita/Wreath | A | [Repetita LICENSE](https://github.com/hirnlego/repetita-versio/blob/99b61f3f2227035671013bd11ebf607483434bee/LICENSE), [Wreath LICENSE](https://github.com/hirnlego/wreath/blob/710cd8b1704d97d1cb8a06fcf2f1c82be1caf134/LICENSE): MIT | Preserve Roberto Noris notices and exact pinned DaisySP dependency notices. Source-based ownership/RNG fixes allowed. |
| V07 Smack | A | [LICENSE](https://github.com/timncox/smack-versio/blob/f839b2ac64f813ec00b2220eee0b41d9d170b237/LICENSE): MIT, with explicit vendored Tim Cox/Schwung provenance | License permits port; reconcile divergent code and any retained engine/API dependencies. Unverified maturity is a technical gate, not missing permission. |
| V08 Capicola | A | [LICENSE](https://github.com/timncox/capicola-versio/blob/acafccc5c22b539b6d9843496c92151d613d1537/LICENSE): AGPLv3; original Heavy Light Industries core carries that obligation | Matching source required for modified distributions; network interaction provisions if applicable. MIT shim doesn't relicense core. |
| V09 Proteus | A | [LICENSE](https://github.com/abluenautilus/ProteusVersio/blob/4a3efe684e598b53880086ebdb05072315071a35/LICENSE): MIT, Seaside Modular | Keep oscillator/library notices. Related [Seaside VCV license](https://github.com/abluenautilus/SeasideModularVCV/blob/bf3ea150ffa2f3a753ef60bc27a4d7db8707561b/LICENSE) is independently MIT; Rack runtime is separate. |
| V10 Cithara | B | [Root LICENSE](https://github.com/TricksterSam/CitharaVersio/blob/01d920ae2eb79a4b614cfb32f4f5cc882e52e98b/LICENSE): GPLv3 text; [Pd patch](https://github.com/TricksterSam/CitharaVersio/blob/01d920ae2eb79a4b614cfb32f4f5cc882e52e98b/versio.pd) contains hv.* objects | Adaptation licensed at project level; exact compiled object/runtime/Heavy version and notices not established. Don't certify a binary dependency closure yet. |
| V11 Audrey II | A | [LICENSE.txt](https://github.com/KoSv/DaisyVersio_Audrey_II/blob/4d20e49f94d3b9e63a965d765f3df502d041a7db/LICENSE.txt): MIT, Infrasonic Audio, LLC | Audit port additions and DaisySP/allocator dependencies; preserve original and port-author attribution. |
| V12 CRCLTR | B | [Repo](https://github.com/s3g/crcltr/tree/f7ccd030b9d36c47a00be81fb0b5f5b567961176): public patches, no explicit project license found | GitHub viewing/forking is not a source/binary distribution grant. Ask s3g and audit lawful Gen export/runtime. |
| V13 Tapeo | D | No project grant; [genlib.h](https://github.com/onoma2/TapeoVersio/blob/8f7883784c257f439406b6bb9156a614b63052a7/gen_dsp/genlib.h) restricts commercial use | Original patch/code permission **and** runtime rights required. Gratis distribution doesn't make this unrestricted open source. |
| V14 Triwalkma | D | Root GPLv3 text; [genlib.h](https://github.com/onoma2/TriwalkmaVersio/blob/38a6b291804f2ab0792d9207cd0fd99e98c3c0f4/gen_dsp/genlib.h) non-commercial-only | Resolve incompatible runtime terms before a GPL/open-source binary route. Author cannot erase third-party restrictions without authority. |
| V15 BenderVersio | D | Root GPLv3 text; [genlib.h](https://github.com/onoma2/BenderVersio/blob/f0f9c1919fc7562ab59e3088bc0b0fb424a1f8c1/gen_dsp/genlib.h) same non-commercial export restriction | Same gate as Triwalkma, plus WIP source qualification. Not permission to use Data Bender's proprietary firmware/name/art. |
| V16 Hillside | B | [Repo](https://github.com/kuttor/Versio--The-Hillside-Slicer/tree/f474b5085f79424a91d895b1e09efb04d933cf46): no project LICENSE/main DSP grant found; individual shy_fft MIT notice | Obtain author grant for slicer/stretch/pitch code; dependency license alone is insufficient. |
| V17 Resilio | A | [LICENSE](https://github.com/jeffebauer/resilio-versio/blob/2ab71a9be56b765bbc2f666527e44cfc278a511e/LICENSE): MIT. [NOTICE](https://github.com/jeffebauer/resilio-versio/blob/2ab71a9be56b765bbc2f666527e44cfc278a511e/NOTICE) distinguishes MIT original core from AGPL JUCE binaries | Reuse the standalone core/parameter definitions without JUCE. Retain needed notices; importing the desktop JUCE plugin changes license/dependency obligations. |
| V18 VNY404 | D | [Publisher](https://acidclank.gumroad.com/l/VNY404) has same no-unauthorized-redistribution/commercial-use language | Request separate grant/source, not another user's download. |
| V19 Pyros | C | [Publisher](https://www.audiority.com/shop/pyros-versio/) offers free firmware; no source/adaptation grant established | Existing desktop product doesn't establish source rights. No registration/download required to research public page; request author permission if pursued. |
| V20 Stray Drum | C | [Publisher](https://jasmineandolivetrees.com/pages/stray-drum-versio-firmware) offers .bin, no inspected source/license | Source + adaptation grant needed. |
| V21 Filterbank | C | [Index](https://github.com/Maxhodges/noise-engineering-firmware-index/blob/187dc43dcdaacb68420d32438a90096f87f29fba/README.md) points to Drive/Reddit; primary discussion inaccessible | Identity/contact/license unverified. Request only after identifying original developer; never use mirror permissions. |
| V22 Megatron | C | [Index](https://github.com/Maxhodges/noise-engineering-firmware-index/blob/187dc43dcdaacb68420d32438a90096f87f29fba/README.md) points to Drive/discussion | Source/grant not established; verify author identity first. |
| V23 Reticulum | C | [Discussion lead](https://modwiggler.com/forum/viewtopic.php?t=280196) inaccessible | No invented grant/developer; source/permission required. |
| V24 Praetereo | C | [Index](https://github.com/Maxhodges/noise-engineering-firmware-index/blob/187dc43dcdaacb68420d32438a90096f87f29fba/README.md) credits Negative Theology; primary thread inaccessible | Source/permission/contact verification required. |
| V25 Archivist | D | [LICENSE](https://github.com/jhockman/the-archivist/blob/752e48de23d5b795d6f69af087ccc6d12a2849f7/LICENSE) reserves rights, prohibits modification/reverse engineering/product bundling without permission | Excluded until specific written source/reuse grant. Respect user's no-reverse-engineering rule regardless. |
| V26 Rings Versio | E (core) | Versio adapter binary lead only; original Mutable core has separate MIT path and existing MPC ports | Reuse only clearly licensed original/desktop core if needed, not unidentified adapter. No priority for another Mutable port. |
| V27 PulsarVersio | B | [Repo](https://github.com/vdo/PulsarVersio/tree/1d019b5fa0dcdfccaf66ba9b6ca5160c1c43cbbe) contains engine/source/manual but no project license found | Ask for complete author grant; technique described in a paper does not license this implementation. |
| V28 Clackotron | C | [LICENSE](https://github.com/bionoid/Clackotron/blob/7119dbc3e7af7a6f58f4939ad96955542f7b719b/LICENSE) MIT; repository contains only README/LICENSE/.bin | No source extraction from binary. Ask for corresponding authored DSP source and ensure that license covers it; extra permission is not presumed necessary. |
| V29 Kickforce 2000 | D | [README](https://github.com/wittysalt8451/Kickforce2000-bin/blob/df88d597c39d60372012de7c6533f8b61203da56/README.md): “free to use for personal use. Redistribution or commercial use not permitted.” | Separate source/license grant required. No source or permission inferred from rich manual/build concepts. |

## Distribution audit: what applies to the eventual plugin

### Source availability is not one boolean

Distinguish executable DSP source, parameter/control wrapper, generated-source inputs, runtime/support libraries, panel artwork, samples and final binary. All can have different copyright holders/licenses. A .bin plus manual is not DSP source. A root license cannot relicense third-party restrictions. A README build command may describe unpublished code, as Clackotron demonstrates. “No source found” is a search result, not a claim about every private repository.

For each approved port, build a file-level bill of materials: original path/author, exact commit or release tag, license version, modifications, retained dependencies/notices, generator/runtime version, external sample/artwork rights and reproducible build/install inputs. No binaries or third-party source are imported into this Phase 2 PR.

### GPLv3 and AGPLv3

For modified GPL binaries, retain attribution/license text, mark changes, and supply exact Corresponding Source with the linked covered plugin, dependency pins and scripts needed to build/install it. A source archive alongside the same binary release is the clearest practical route. Original project GPL-3.0-only versus GPL-3.0-or-later must be preserved; a bare GPLv3 license text is not sufficient to invent an “or later” election. MIT wrapper/DSP contributions retain notices inside a GPL/AGPL combined artifact.

AGPLv3 adds section 13 obligations for modified programs supporting remote network interaction. A local-only audio processor is not automatically a network service; adding web control/live coding/API access changes the assessment. Capicola should stay audio-local initially. Resilio's original core is MIT, so reusing it without JUCE does not inherit the JUCE-linked desktop binary's AGPL just because that binary exists.

GPL permits commercial distribution; don't copy non-commercial prose into a GPL code license. Separate NC graphics may constrain the package containing them—PlateauXXL's VCV component graphics are an example—so use original cleared MPC artwork instead. Root GPL cannot resolve Gen runtime's non-commercial terms. A free download is not the same thing as a freedom-respecting license.

GPL section 6's Installation Information obligations have a specific User Product/transaction trigger; not every plugin download automatically triggers them. A shipped locked/configured device needs separate review. Publish reproducible source/install instructions regardless. Do not distribute Akai firmware, secrets or patches to create a workaround.

### Independent VST2 boundary

The community [wrapper](https://github.com/sd88me/mpc-vst-plugins/blob/ce6278d53091ba40127838020fc8a7887894551f/wrapper/vst2_wrap.c) states its ABI declarations are hand-written and SDK-free; [kit LICENSE](https://github.com/sd88me/mpc-vst-plugins/blob/ce6278d53091ba40127838020fc8a7887894551f/LICENSE) is MIT for its own code, with third-party exceptions. This is the preferred route for an independent project. Do not download/copy Steinberg's discontinued proprietary VST2 SDK from an unofficial mirror, assume VST3 licensing authorizes VST2, or copy closed DSP.

The SDK-free implementation still needs provenance/contract/trademark review before public VST2 binary distribution. A GPL plugin's relationship with the proprietary host is a separate-work/linkage question to evaluate, not automatically cleared by an ABI name and not proof that Akai must release its host. No applicable blanket exception or Steinberg certification was established. Keep source licensing and final distribution clearance separate.

### Names, skins and assets

Use original vendor/plugin identities, UIDs, directories and original skins. Do not reuse DUB-Russell/WTF!/Acidclank/FRGMNTS logos or suggest endorsement. _core's README says Infinite Digits/Ectocore names must not be used on derivatives. Factual attribution/source links are different from naming/marketing permission. “Versio-compatible source reference” does not license Noise Engineering's official algorithms or marks.

No factory sound banks, commercial app binaries, sample packs, firmware copies or branded panel graphics belong in this PR. MIT/GPL code licenses do not automatically cover recording/composition rights or every artwork/font. Performance recordings are optional comparison inputs only when lawfully supplied later.

## Permission workflow

Drafts and verified/unverified channels: [DEVELOPER_CONTACT_DRAFTS.md](DEVELOPER_CONTACT_DRAFTS.md). Nothing was sent. User approval is required before outreach. An informal “yes, port it” without terms may be insufficient for a reusable open-source binary project; ask for a specific license/redistribution scope, rights to generated code/runtime, required attribution, permitted naming and dependency notices. No response is not permission.

After a reply, inspect source at an immutable revision, resolve the license closure and update the classification. Until then use already-licensed alternatives for design exploration. No plugin coding begins without separate explicit approval.
