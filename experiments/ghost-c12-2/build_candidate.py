#!/usr/bin/env python3
"""Build a one-page GHOST C1.2.2 native-skin diagnostic; never contacts a device."""
from __future__ import annotations

import hashlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tarfile
import zipfile
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "build/ghost-final-development"
BASELINE = ROOT / "build/ghost-c12-1-trial/sessions/20261016T120503Z-68045/installed-plugin.before.tar"
SOURCE_ZIP = ROOT / "build/ghost-c12-prototype/beatrepeat-ghost-c12-armv7-OFFLINE.zip"
REFERENCE_C122_ZIP = ROOT / "build/ghost-c12-2/beatrepeat-ghost-c12-2-native-compatibility-diagnostic-armv7.zip"
REFERENCE_NATIVE = ROOT / "build/ghost-c12-prototype/beatrepeat-ghost-c1.so"
EXPECTED_C121_ARM = "3dc0d0db800f40fa7a9e99b4fd8b8efa49265c8e8e0f1d7e92e2d02ae22a903f"
EXPECTED_C122_ARM = "3ead48e181c1ea979bce3862737a1215dcff4e360c052a9cde8de35a1b616118"
EXPECTED_UID = "45754272"
EXPECTED_IDENT = "MPC-EURO.vst.beatrepeat"
FOLDER = "MPC-EURO - VST - BeatRepeat"
PREFIX = FOLDER + "/"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def c121_package() -> dict[str, bytes]:
    with zipfile.ZipFile(SOURCE_ZIP) as z:
        if z.testzip() is not None:
            raise RuntimeError("C1.2.1 source ZIP CRC check failed")
        result = {}
        for name in z.namelist():
            if not name.startswith(PREFIX) or name.endswith("/"):
                continue
            relative = name[len(PREFIX):]
            if not relative or ".." in pathlib.PurePosixPath(relative).parts:
                raise RuntimeError("Unsafe C1.2.1 package member: " + name)
            result[relative] = z.read(name)
    if sha(result.get("beatrepeat.so", b"")) != EXPECTED_C121_ARM:
        raise RuntimeError("C1.2.1 ARM candidate SHA mismatch")
    return result


def original_backup() -> dict[str, bytes]:
    with tarfile.open(BASELINE, "r:") as archive:
        files = {}
        for member in archive:
            if not member.isfile():
                continue
            name = member.name.removeprefix("./")
            if name.startswith(PREFIX):
                name = name[len(PREFIX):]
            stream = archive.extractfile(member)
            if stream is None:
                raise RuntimeError("Cannot read original backup member " + member.name)
            files[name] = stream.read()
    return files


def native_minimal_tui(original: dict[str, bytes]) -> bytes:
    """Use the actual pre-GHOST MPC One tab and native composite knob definition."""
    tui = json.loads(original["Plugin Skins/TUI.json"])
    page = tui["pageData"]
    tabs = page["tabs"]
    if not any(t["tabName"] == "PLAY" and t["fnKeyIndex"] == 0 and t["fnKeySubIndex"] == 0 for t in tabs):
        raise RuntimeError("Known-good PLAY page shape missing from original backup")
    definitions = page["componentDefinitions"]["localComponentDefinitions"]
    by_key = {item["key"]: item["value"] for item in definitions}
    page_key = "PLAY|PLAY"
    if page_key not in by_key:
        raise RuntimeError("Known-good PLAY component definition missing")
    play = by_key[page_key]
    children = play["componentsData"]
    background = next((c for c in children if c["componentData"].get("name") in ("Background", "Background Image")), None)
    if background is None:
        raise RuntimeError("Known-good PLAY background component missing")
    knob_key = "shKnob32_ls1.2_ns20_vs27_bw200"
    if knob_key not in by_key:
        raise RuntimeError("Known-good MPC One knob composite missing")
    template = next((c for c in children if c["componentData"].get("type") == knob_key), None)
    if template is None:
        raise RuntimeError("Known-good PLAY knob instance missing")

    # Four large, touch-friendly controls fit on a single native tab. The
    # confirmed C1.2.2 controls alone cannot start an effect: Density, Chaos,
    # Motion Depth and Mix are continuous settings, while repeat playback is
    # gated. Add the original native Gate/Capture/Freeze/Punch controls so a
    # performer can actually audition and use the existing DSP.
    controls = []
    x_positions = (30, 345, 660, 975)
    bindings = (("Density", 76), ("Chaos", 55), ("Motion Depth", 70), ("Dry/Wet", 53))
    for x, (label, parameter) in zip(x_positions, bindings):
        item = json.loads(json.dumps(template))
        item["componentData"]["name"] = label
        item["bounds"]["bounds"] = f"{x} 210 200 135"
        item["bounds"]["acceptsHWFocus"] = "Yes"
        item["handle remapping"]["map"] = [{"key": "Data", "value": f"Parameter {parameter}"}]
        controls.append(item)
    action_names = ("gate OFF", "gate ON", "GHOST OFF", "GHOST ON", "CAPTURE", "freeze LIVE", "freeze FROZEN", "PUNCH / CANCEL")
    action_keys = ("shSeg_gate_0", "shSeg_gate_1", "shSeg_ghost_0", "shSeg_ghost_1", "shTrig_capture_CAPTURE", "shSeg_freeze_0", "shSeg_freeze_1", "shTrig_punch_PUNCH___CANCEL")
    action_map = dict(zip(action_names, (1, 1, 49, 49, 10, 11, 11, 4)))
    actions = []
    action_definitions = []
    action_x = {"gate OFF": 70, "gate ON": 173, "GHOST OFF": 299, "GHOST ON": 402, "CAPTURE": 523, "freeze LIVE": 750, "freeze FROZEN": 853, "PUNCH / CANCEL": 976}
    action_template = {"GHOST OFF": "gate OFF", "GHOST ON": "gate ON"}
    for name, key in zip(action_names, action_keys):
        source_name = action_template.get(name, name)
        template_action = next((c for c in children if c["componentData"].get("name") == source_name), None)
        if template_action is None or key not in by_key:
            if name.startswith("GHOST ") and template_action is not None:
                definition = json.loads(json.dumps(by_key["shSeg_gate_" + ("1" if name.endswith("ON") else "0")]))
                button = definition["componentsData"][0]["componentData"]["data"]
                button["onImage"] = "c122-ghost-on.png"
                button["offImage"] = "c122-ghost-off.png"
                by_key[key] = definition
                action_definitions.append({"key": key, "value": definition})
            else:
                raise RuntimeError("Known-good native action control missing: " + name)
        item = json.loads(json.dumps(template_action))
        item["componentData"]["name"] = name
        item["componentData"]["type"] = key
        width = 95 if name in ("gate OFF", "gate ON", "GHOST OFF", "GHOST ON", "freeze LIVE", "freeze FROZEN") else 205
        item["bounds"]["bounds"] = f"{action_x[name]} 456 {width} 56"
        # These actions are touchscreen-only. Keep the four established Q-Link
        # knobs as the page's only hardware-focusable components.
        item["bounds"]["acceptsHWFocus"] = "No"
        item["handle remapping"]["map"] = [{"key": "Data", "value": f"Parameter {action_map[name]}"}]
        actions.append(item)
    # Include only composite definitions actually used by this page.
    action_definitions = [{"key": key, "value": by_key[key]} for key in action_keys if key in by_key]
    background["componentData"]["data"]["image"] = "c122-background.png"
    play["componentsData"] = [background, *controls, *actions]

    # Collapse the GUI to the exact one-tab navigation shape used by the original.
    page["tabs"] = [dict(tabs[0])]
    page["tabs"][0]["tabName"] = "PLAY"
    page["tabs"][0]["fnKeyIndex"] = 0
    page["tabs"][0]["fnKeySubIndex"] = 0
    page["tabs"][0]["componentName"] = page_key
    page["tabs"][0]["qlinkBoundsData"] = [f"{x} 210 200 135" for x in x_positions]
    page["componentDefinitions"]["localComponentDefinitions"] = [
        {"key": knob_key, "value": by_key[knob_key]},
        *action_definitions,
        {"key": page_key, "value": play},
    ]
    encoded = (json.dumps(tui, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    return encoded


def make_background() -> bytes:
    from PIL import Image, ImageDraw
    image = Image.new("RGB", (1280, 628), "#0b1016")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1279, 95), fill="#121a23")
    draw.line((28, 95, 1252, 95), fill="#31404b", width=2)
    for x in (24, 339, 654, 969):
        draw.rounded_rectangle((x, 188, x + 212, 368), radius=13, fill="#111a23", outline="#2b3a46", width=2)
        draw.line((x + 18, 359, x + 194, 359), fill="#24333e", width=1)
    stream = io.BytesIO()
    image.save(stream, format="PNG", optimize=True)
    return stream.getvalue()


def make_ghost_button(active: bool) -> bytes:
    from PIL import Image, ImageDraw, ImageFont
    image = Image.new("RGBA", (95, 56), "#17232c")
    draw = ImageDraw.Draw(image)
    edge = "#65dbc6" if active else "#45535d"
    draw.rounded_rectangle((1, 1, 93, 54), radius=7, fill="#193b3b" if active else "#17232c", outline=edge, width=2)
    label = "ON" if active else "OFF"
    font = ImageFont.load_default(size=15)
    box = draw.textbbox((0, 0), label, font=font)
    draw.text(((95 - (box[2] - box[0])) / 2, (56 - (box[3] - box[1])) / 2 - box[1]), label, font=font, fill="#e6f6fa")
    stream = io.BytesIO(); image.save(stream, format="PNG", optimize=True)
    return stream.getvalue()


def qlink_files(package: dict[str, bytes]) -> None:
    # MIX_LIVE (VST parameter 8) is intentionally non-automatable. The canonical
    # GHOST Mix control (P_MIX, VST parameter 53) is the persistent, automatable
    # alias for the same Dry/Wet setting. Preserve all other existing assignments.
    for name in ("Plugin Skins/Q-Links.json", "Plugin Skins/Q-Links - 8by1.json"):
        q = json.loads(package[name])
        if q["Program Mode Q-Links"].get("Q-Link 1") != 8:
            raise RuntimeError(f"Unexpected C1.2.1 Q-Link 1 baseline in {name}")
        q["Program Mode Q-Links"]["Q-Link 1"] = 53
        screen = q["Screen Mode Q-Links"]["map"]
        core = [row for row in screen if row["Tab"] == 1 and row["SubTab"] == 1]
        if len(core) != 1 or core[0]["Q-Links"].get("Q-Link 1") != 8:
            raise RuntimeError(f"Unexpected C1.2.1 CORE Q-Link baseline in {name}")
        core[0]["Q-Links"]["Q-Link 1"] = 53
        q["Screen Mode Q-Links"]["map"] = core
        package[name] = (json.dumps(q, ensure_ascii=False, indent=2) + "\n").encode()


def compile_native() -> pathlib.Path:
    """Build a host test copy with only the public parameter display name changed."""
    out = OUT / "native"
    out.mkdir(parents=True, exist_ok=True)
    params = (ROOT / "experiments/ghost-c1/params.c").read_text()
    anchor = 'Q("mix","Mix",0,1,1)'
    if params.count(anchor) != 1:
        raise RuntimeError("Mix registry anchor changed; refusing metadata-only build")
    (out / "params.c").write_text(params.replace(anchor, 'Q("mix","Dry/Wet",0,1,1)'))
    cc = shutil.which("cc")
    if not cc:
        raise RuntimeError("C compiler not available for offline VST validation")
    cwd = ROOT / "experiments/ghost-c1"
    flags = ["-std=c11", "-Wall", "-Wextra", "-Werror", "-ffp-contract=off", "-I../../src", "-I../ghost", "-I.", "-I../../build", "-O2", "-fPIC"]
    sources = ["core.c", "motion.c", str(out / "params.c"), "state.c", "vst.c", "base.c", "../ghost/ghost.c", "../../src/engine.c", "../../src/repeat.c"]
    command = [cc, *flags, "-shared", *sources, "-lm", "-pthread", "-o", str(out / "beatrepeat-ghost-c12-2.so")]
    subprocess.run(command, cwd=cwd, check=True)
    return out / "beatrepeat-ghost-c12-2.so"


def compile_arm() -> tuple[pathlib.Path, dict]:
    zig = ROOT / "build/venv/lib/python3.13/site-packages/ziglang/zig"
    if not zig.is_file():
        raise RuntimeError("Pinned offline Zig toolchain unavailable")
    out = OUT / "arm"
    out.mkdir(parents=True, exist_ok=True)
    params = (ROOT / "experiments/ghost-c1/params.c").read_text()
    anchor = 'Q("mix","Mix",0,1,1)'
    if params.count(anchor) != 1:
        raise RuntimeError("Mix registry anchor changed; refusing metadata-only build")
    isolated_params = out / "params.c"
    isolated_params.write_text(params.replace(anchor, 'Q("mix","Dry/Wet",0,1,1)'))
    common = [str(zig), "cc", "-target", "arm-linux-gnueabihf.2.31", "-mcpu=cortex_a9", "-std=c11", "-O2", "-ffp-contract=off", "-fPIC", "-fvisibility=hidden", "-I" + str(ROOT / "experiments/ghost-c1"), "-I" + str(ROOT / "build"), "-I" + str(ROOT / "src")]
    env = dict(os.environ, ZIG_GLOBAL_CACHE_DIR=str(out / "zig-global-cache"), ZIG_LOCAL_CACHE_DIR=str(out / "zig-local-cache"))
    sources = ["core.c", "motion.c", isolated_params, "state.c", "vst.c", "base.c", "../ghost/ghost.c", "../../src/engine.c", "../../src/repeat.c"]
    objects = []
    cwd = ROOT / "experiments/ghost-c1"
    for i, source in enumerate(sources):
        obj = out / f"unit-{i}.o"
        subprocess.run([*common, "-c", str(source), "-o", str(obj)], cwd=cwd, env=env, check=True)
        objects.append(str(obj))
    binary = out / "beatrepeat.so"
    subprocess.run([*common, "-shared", *objects, "-lm", "-pthread", "-Wl,--no-undefined", "-Wl,--version-script=" + str(ROOT / "src/exports.map"), "-o", str(binary)], env=env, check=True)
    sys.path.insert(0, str(ROOT / "build/venv/lib/python3.13/site-packages"))
    from elftools.elf.elffile import ELFFile
    with binary.open("rb") as f:
        elf = ELFFile(f)
        if elf.elfclass != 32 or elf["e_machine"] != "EM_ARM" or not (elf["e_flags"] & 0x400):
            raise RuntimeError("Diagnostic binary is not ARM hard-float ELF32")
        dyn = elf.get_section_by_name(".dynsym")
        exports = [s.name for s in dyn.iter_symbols() if s["st_shndx"] != "SHN_UNDEF" and s["st_info"]["bind"] == "STB_GLOBAL"]
        if exports != ["VSTPluginMain"]:
            raise RuntimeError("Unexpected ARM exports: " + repr(exports))
        tags = [t for t in elf.get_section_by_name(".dynamic").iter_tags() if t.entry.d_tag == "DT_NEEDED"]
        needed = sorted(t.needed for t in tags)
        if not set(needed) <= {"libc.so.6", "libm.so.6", "libpthread.so.0", "ld-linux-armhf.so.3"}:
            raise RuntimeError("Unexpected ARM shared-library dependencies: " + repr(needed))
        req = elf.get_section_by_name(".gnu.version_r")
        glibc = sorted({aux.name for _, auxes in req.iter_versions() for aux in auxes if aux.name.startswith("GLIBC_")}) if req else []
        if any(tuple(map(int, v[6:].split("."))) > (2, 31) for v in glibc):
            raise RuntimeError("ARM candidate exceeds glibc 2.31: " + repr(glibc))
        current_sections = {section.name: section.data() for section in elf.iter_sections()}
    with zipfile.ZipFile(REFERENCE_C122_ZIP) as archive:
        reference_data = archive.read(PREFIX + "beatrepeat.so")
    if sha(reference_data) != EXPECTED_C122_ARM:
        raise RuntimeError("Hardware-tested C1.2.2 reference binary checksum changed")
    from elftools.elf.elffile import ELFFile as _ELFFile
    import io as _io
    with _io.BytesIO(reference_data) as stream:
        reference = _ELFFile(stream)
        reference_sections = {section.name: section.data() for section in reference.iter_sections()}
    debug_path_sections = {".debug_info", ".debug_line", ".debug_str"}
    changed_sections = sorted(name for name in set(current_sections) | set(reference_sections)
                              if name not in debug_path_sections and current_sections.get(name) != reference_sections.get(name))
    if changed_sections:
        raise RuntimeError("Executable/ABI sections differ from hardware-tested C1.2.2 binary: " + repr(changed_sections))
    return binary, {"elf_bits": 32, "machine": "ARM", "hard_float": True, "exports": exports, "needed": needed, "glibc_versions": glibc, "sha256": sha(binary.read_bytes()), "bytes": binary.stat().st_size, "executed_on_arm": False, "reference_c122_sha256": EXPECTED_C122_ARM, "all_non_debug_sections_match_hardware_c122": True, "debug_path_sections_differ": sorted(name for name in debug_path_sections if current_sections.get(name) != reference_sections.get(name))}


def build_package(original: dict[str, bytes], package: dict[str, bytes], tui: bytes, arm_binary: pathlib.Path, background: bytes) -> tuple[pathlib.Path, dict]:
    package["Plugin Skins/TUI.json"] = tui
    package["Plugin Skins/c122-background.png"] = background
    package["Plugin Skins/c122-ghost-on.png"] = make_ghost_button(True)
    package["Plugin Skins/c122-ghost-off.png"] = make_ghost_button(False)
    package["Plugin Skins/sh_knob_r32.png"] = original["Plugin Skins/sh_knob_r32.png"]
    # Reuse the hardware-proven source skin's button art where a component
    # was absent from the C1.2.1 package but is now reintroduced on PLAY.
    parsed_tui = json.loads(tui)
    referenced = set()
    def scan_resources(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in ("image", "onImage", "offImage", "filmStrip") and isinstance(child, str) and child.lower().endswith(".png"):
                    referenced.add("Plugin Skins/" + child)
                scan_resources(child)
        elif isinstance(value, list):
            for child in value:
                scan_resources(child)
    scan_resources(parsed_tui)
    for name in referenced:
        if name not in package and name in original:
            package[name] = original[name]
    missing_resources = sorted(name for name in referenced if name not in package)
    if missing_resources:
        raise RuntimeError("Native skin resources missing from package: " + repr(missing_resources))
    package["plugin-meta.xml"] = original["plugin-meta.xml"]
    package["beatrepeat.so"] = arm_binary.read_bytes()
    meta = ET.fromstring(package["plugin-meta.xml"])
    if meta.get("uid") != EXPECTED_UID or meta.get("file") != "%payload-path%/" + PREFIX + "beatrepeat.so":
        raise RuntimeError("plugin-meta.xml identity/path mismatch")
    version = ET.fromstring(package["version.xml"])
    if version.findtext("identifier") != EXPECTED_IDENT:
        raise RuntimeError("Version identity mismatch")
    hashes = {name: sha(data) for name, data in sorted(package.items())}
    manifest = {"candidate": "GHOST final development: C1.2.2 native skin with accessible audio actions; offline only", "uid": EXPECTED_UID, "identifier": EXPECTED_IDENT, "reference": "Hardware-confirmed C1.2.2 skin structure + unchanged C1.2.2 audio wrapper", "binary_sha256": hashes["beatrepeat.so"], "files": hashes}
    package["manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    package["SHA256SUMS"] = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(package.items())).encode()

    folder = OUT / "package" / FOLDER
    shutil.rmtree(folder.parent, ignore_errors=True)
    folder.mkdir(parents=True)
    for name, data in package.items():
        target = folder / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    zip_path = OUT / "beatrepeat-ghost-final-development-offline-armv7.zip"
    OUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in sorted(package):
            info = zipfile.ZipInfo(PREFIX + name, (2026, 10, 16, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, package[name])
    with zipfile.ZipFile(zip_path) as z:
        if z.testzip() is not None or set(z.namelist()) != {PREFIX + n for n in package}:
            raise RuntimeError("Diagnostic ZIP structure/CRC check failed")
        for name, data in package.items():
            if z.read(PREFIX + name) != data:
                raise RuntimeError("Diagnostic ZIP round-trip mismatch: " + name)
    report = {"candidate": manifest["candidate"], "zip_sha256": sha(zip_path.read_bytes()), "binary_sha256": hashes["beatrepeat.so"], "reference_c121_binary_sha256": EXPECTED_C121_ARM, "file_count": len(package), "metadata_included": True, "plugin_identity": EXPECTED_IDENT, "uid": EXPECTED_UID, "remote_or_device_access": False, "touch_actions": {"Repeat": 50, "Ghost": 49, "Capture": 81, "Freeze": 82, "Punch": 4}}
    return zip_path, report


def render_preview(original: dict[str, bytes], background: bytes, out: pathlib.Path) -> None:
    sys.path.insert(0, str(ROOT / "build/venv/lib/python3.13/site-packages"))
    from PIL import Image, ImageDraw, ImageFont
    bg = Image.open(io.BytesIO(background)).convert("RGB")
    canvas = Image.new("RGB", (1280, 800), "#0b1016")
    canvas.paste(bg, (0, 86))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=27)
    small = ImageFont.load_default(size=18)
    draw.rectangle((0, 0, 1279, 85), fill="#151c23")
    draw.text((30, 18), "GHOST  /  PLAY + NATIVE AUDIO ACTIONS", font=font, fill="#e6f6fa")
    draw.text((30, 57), "Offline preview · C1.2.2-compatible PLAY tab · no hardware renderer", font=small, fill="#8ba6b1")
    knob = Image.open(io.BytesIO(original["Plugin Skins/sh_knob_r32.png"])).convert("RGBA")
    if knob.height >= knob.width * 20:
        frame_h = knob.height // 127
        knob = knob.crop((0, (63 * frame_h), knob.width, (63 * frame_h) + frame_h))
    elif knob.width >= knob.height * 20:
        frame_w = knob.width // 127
        knob = knob.crop((63 * frame_w, 0, 64 * frame_w, knob.height))
    else:
        knob = knob.resize((74, 74))
    if knob.size != (74, 74):
        knob = knob.resize((74, 74))
    labels = ["DENSITY", "CHAOS", "MOTION DEPTH", "DRY / WET"]
    values = ["4", "0 %", "100 %", "100 %"]
    for x, label, value in zip((30, 345, 660, 975), labels, values):
        canvas.paste(knob, (x + 63, 296), knob)
        box = draw.textbbox((0, 0), label, font=font)
        draw.text((x + (200 - (box[2] - box[0])) / 2, 388), label, font=font, fill="#e6f6fa")
        box = draw.textbbox((0, 0), value, font=font)
        draw.text((x + (200 - (box[2] - box[0])) / 2, 424), value, font=font, fill="#65dbc6")
    # Native action-strip facsimile for offline layout review. The actual
    # plugin uses the known-good MPC segmented and trigger composites above.
    for x, width, label in ((70, 198, "REPEAT"), (299, 198, "GHOST"), (523, 205, "CAPTURE"), (750, 198, "FREEZE"), (976, 205, "PUNCH / CANCEL")):
        draw.text((x + 2, 520), label, font=small, fill="#8ba6b1")
    for x, width, label in ((70, 95, "OFF"), (173, 95, "ON"), (299, 95, "OFF"), (402, 95, "ON"), (523, 205, "CAPTURE"), (750, 95, "LIVE"), (853, 95, "HELD"), (976, 205, "PUNCH / CANCEL")):
        draw.rounded_rectangle((x, 542, x + width, 598), radius=10, fill="#16232c", outline="#65dbc6", width=2)
        box = draw.textbbox((0, 0), label, font=small)
        draw.text((x + (width - box[2] + box[0]) / 2, 560), label, font=small, fill="#e6f6fa")
    draw.text((30, 720), "Touch actions start and capture the existing Repeat engine; PUNCH is a bounded one-shot.", font=small, fill="#8ba6b1")
    canvas.save(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    baseline = original_backup()
    package = c121_package()
    if "plugin-meta.xml" not in baseline or "Plugin Skins/sh_knob_r32.png" not in baseline:
        raise RuntimeError("Original backup is missing required native metadata/assets")
    qlink_files(package)
    native_tui = native_minimal_tui(baseline)
    background = make_background()
    native_plugin = compile_native()
    arm_plugin, arm_report = compile_arm()
    zip_path, report = build_package(baseline, package, native_tui, arm_plugin, background)
    render_preview(baseline, background, OUT / "ghost-final-development-preview.png")
    report["arm_validation"] = arm_report
    report["native_test_plugin"] = str(native_plugin)
    report["reference_c121_package"] = str(SOURCE_ZIP)
    report["original_backup_sha256"] = sha(BASELINE.read_bytes())
    (OUT / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print("ZIP:", zip_path)
    print("PREVIEW:", OUT / "ghost-final-development-preview.png")


if __name__ == "__main__":
    main()
