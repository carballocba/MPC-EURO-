#!/usr/bin/env python3
"""Build one offline GHOST integration trial, preserving historical artifacts.

No device access. Same engine/parameters; fixes VST name buffer and JUCE XML UID,
reuses the hardware-visible C1.2.2 PLAY graph, adds existing Gate/Punch actions.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import io
import json
import pathlib
import re
import tarfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "build/ghost-integration-recovery/candidate"
VST_UID = 0x47485354
XML_UID = "47485354"
WRONG_XML_UID = "1195922260"
FOLDER = "MPC-EURO - VST - GHOST"
TARGET = "/storage/Synths/" + FOLDER
C122 = ROOT / "build/ghost-c12-2/beatrepeat-ghost-c12-2-native-compatibility-diagnostic-armv7.zip"
ARCHIVED = ROOT / "build/ghost-final-development/independent-ghost/ghost-balanced-v2-independent-armv7-OFFLINE.zip"
ORIGINAL = ROOT / "build/ghost-c12-1-trial/sessions/20261016T120503Z-68045/installed-plugin.before.tar"

def sha(b): return hashlib.sha256(b).hexdigest()

def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def zip_files(path, prefix):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip(): raise ValueError("ZIP CRC failure")
        return {n[len(prefix):]: archive.read(n) for n in archive.namelist() if n.startswith(prefix) and not n.endswith("/")}

def repair_identity(raw):
    """Only repair the UID encoding of the exact existing GHOST registration."""
    root = ET.fromstring(raw)
    sections = list(root.iter("KNOWNPLUGINS"))
    if len(sections) != 1: raise ValueError("Expected one KNOWNPLUGINS section")
    entries = list(sections[0].iter("PLUGIN"))
    if len(entries) != 79: raise ValueError("Expected 79 registrations")
    matches = [p for p in entries if p.get("file") == TARGET + "/ghost.so" and p.get("name") == "GHOST"]
    if len(matches) != 1 or matches[0].get("uid") not in (WRONG_XML_UID, XML_UID):
        raise ValueError("Unexpected GHOST registration")
    for p in entries:
        if p is not matches[0] and (int(p.get("uid", "0"), 16) & 0xffffffff) == VST_UID:
            raise ValueError("A different plugin has the actual GHOST UID")
        if p.get("uid") == "45754272": raise ValueError("Unexpected BeatRepeat registration")
    hits = []
    for hit in re.finditer(rb"<PLUGIN\b[^>]*?/>", raw):
        node = ET.fromstring(hit.group())
        if node.get("file") == TARGET + "/ghost.so" and node.get("name") == "GHOST": hits.append(hit)
    if len(hits) != 1: raise ValueError("Cannot isolate GHOST registration bytes")
    hit = hits[0]
    old = hit.group()
    new = old.replace(('uid="' + WRONG_XML_UID + '"').encode(), ('uid="' + XML_UID + '"').encode())
    result = raw[:hit.start()] + new + raw[hit.end():]
    if result[:hit.start()] != raw[:hit.start()] or result[hit.start()+len(new):] != raw[hit.end():]:
        raise ValueError("Unrelated settings bytes changed")
    parsed = ET.fromstring(result)
    corrected = [p for p in parsed.iter("PLUGIN") if p.get("file") == TARGET + "/ghost.so"]
    if len(corrected) != 1 or int(corrected[0].get("uid"), 16) != VST_UID: raise ValueError("UID round-trip failed")
    return result

def original_files():
    if sha(ORIGINAL.read_bytes()) != "02553c412edf20f33e4567cf280a3647eea14b7a2741826194a813e9c2fa3f76":
        raise ValueError("Original backup changed")
    with tarfile.open(ORIGINAL) as archive:
        return {m.name.removeprefix("./"): archive.extractfile(m).read() for m in archive if m.isfile()}

def minimal_skin(reference, original):
    tui = json.loads(reference["Plugin Skins/TUI.json"])
    old = json.loads(original["Plugin Skins/TUI.json"])
    defs = {x["key"]: x["value"] for x in old["pageData"]["componentDefinitions"]["localComponentDefinitions"]}
    current_defs = tui["pageData"]["componentDefinitions"]["localComponentDefinitions"]
    play = next(x["value"] for x in current_defs if x["key"] == "PLAY|PLAY")
    original_play = defs["PLAY|PLAY"]["componentsData"]
    specs = [("gate OFF", "shSeg_gate_0", "380 460 95 56"),
             ("gate ON", "shSeg_gate_1", "477 460 95 56"),
             ("PUNCH / CANCEL", "shTrig_punch_PUNCH___CANCEL", "670 460 205 56")]
    for name, key, bounds in specs:
        control = copy.deepcopy(next(c for c in original_play if c["componentData"]["name"] == name))
        control["bounds"]["bounds"] = bounds
        control["bounds"]["acceptsHWFocus"] = "No"
        play["componentsData"].append(control)
        current_defs.insert(-1, {"key": key, "value": copy.deepcopy(defs[key])})
    # Keep the exact C1.2.2 knob/tab/Q-Link geometry. Only the static background changes.
    background = next(c for c in play["componentsData"] if c["componentData"]["type"] == "Image")
    background["componentData"]["data"]["image"] = "integration-recovery-background.png"
    from PIL import Image, ImageDraw, ImageFont
    image = Image.open(io.BytesIO(reference["Plugin Skins/c122-background.png"])).convert("RGB")
    draw = ImageDraw.Draw(image)
    font_path = str(ROOT / "vendor/fonts/DejaVuSansMono.ttf")
    title = ImageFont.truetype(font_path, 26)
    small = ImageFont.truetype(font_path, 18)
    draw.rectangle((0, 0, 1279, 95), fill="#121a23")
    draw.text((30, 17), "GHOST / INTEGRATION RECOVERY", font=title, fill="#e6f6fa")
    draw.text((30, 58), "PLAY reference skin / four Screen Mode Q-Links", font=small, fill="#8ba6b1")
    draw.rectangle((0, 395, 1279, 627), fill="#0b1016")
    draw.text((380, 423), "REPEAT / GATE", font=small, fill="#8ba6b1")
    draw.text((670, 423), "BOUNDED ONE-SHOT", font=small, fill="#8ba6b1")
    draw.text((30, 557), "Play a drum loop, then touch Gate ON or PUNCH. No MIDI required.", font=small, fill="#e6f6fa")
    draw.text((30, 589), "Gate OFF restores live capture. Initial bypass is OFF; Repeat is OFF.", font=small, fill="#8ba6b1")
    stream = io.BytesIO(); image.save(stream, format="PNG", optimize=True)
    return tui, stream.getvalue()

def referenced_images(tui):
    found = set()
    def walk(v):
        if isinstance(v, dict):
            for key, x in v.items():
                if key in ("image", "onImage", "offImage", "filmStrip") and isinstance(x, str) and x.endswith(".png"): found.add("Plugin Skins/" + x)
                walk(x)
        elif isinstance(v, list):
            for x in v: walk(x)
    walk(tui)
    return found

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=OUT)
    output = parser.parse_args().out.resolve()
    if output.exists(): raise SystemExit("Refusing to overwrite an existing candidate or backup: " + str(output))
    if sha(ARCHIVED.read_bytes()) != "db0034c72c3ea0d1bfe89a7eb2bfd61b969db009d9fdbafefeca28cd62d1facf": raise ValueError("Historical independent ZIP changed")
    if sha(C122.read_bytes()) != "eae234676244916484daaaead6eac8a0fce2fc832e5b7c1911952c024aa18cba": raise ValueError("Historical C1.2.2 ZIP changed")
    original = original_files()
    reference = zip_files(C122, "MPC-EURO - VST - BeatRepeat/")
    archived = zip_files(ARCHIVED, FOLDER + "/")
    output.mkdir(parents=True)
    build = module(ROOT / "experiments/ghost-c12-2/build_independent_ghost.py", "ghost_independent_builder")
    build.OUT = output / "engine"
    build.OUT.mkdir()
    binary, abi = build.compile_arm(diagnostics=True)
    native = build.compile_native_identity_test(diagnostics=True)
    files = {n: b for n, b in reference.items() if n not in ("beatrepeat.so", "manifest.json", "SHA256SUMS")}
    files["ghost.so"] = binary.read_bytes()
    tui, background = minimal_skin(reference, original)
    files["Plugin Skins/TUI.json"] = (json.dumps(tui, separators=(",", ":")) + "\n").encode()
    files["Plugin Skins/integration-recovery-background.png"] = background
    for name in referenced_images(tui):
        if name not in files: files[name] = original[name]
    meta = ET.fromstring(archived["plugin-meta.xml"])
    meta.set("uid", XML_UID)
    files["plugin-meta.xml"] = ET.tostring(meta, encoding="utf-8", xml_declaration=True) + b"\n"
    version = ET.fromstring(archived["version.xml"])
    version.find("version").text = "2.2.0.1"
    files["version.xml"] = ET.tostring(version, encoding="utf-8", xml_declaration=True) + b"\n"
    # Program Mode stays byte-for-byte compatible. Screen Mode uses the visible four controls.
    for name in ("Plugin Skins/Q-Links.json", "Plugin Skins/Q-Links - 8by1.json"):
        q = json.loads(reference[name])
        q["Program Mode Q-Links"] = json.loads(archived[name])["Program Mode Q-Links"]
        files[name] = (json.dumps(q, indent=2) + "\n").encode()
    if not referenced_images(tui) <= files.keys(): raise ValueError("Missing native skin asset")
    manifest = {"candidate": "GHOST integration recovery; single controlled hardware trial; OFFLINE ONLY",
        "vst_uid_decimal": VST_UID, "registration_uid_hex": XML_UID, "identifier": "MPC-EURO.vst.ghost",
        "binary_sha256": sha(files["ghost.so"]), "abi": abi, "parameters": 124,
        "audio_engine_changes": False, "diagnostic_counters": "atomic counters; stderr from notifier thread at most once/second; no RT file I/O",
        "hardware_validation": "pending", "device_modified": False,
        "files": {n: sha(b) for n, b in sorted(files.items())}}
    files["manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    files["SHA256SUMS"] = "".join(f"{sha(b)}  {n}\n" for n, b in sorted(files.items())).encode()
    folder = output / "package" / FOLDER
    for n, b in files.items():
        p = folder / n; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b)
    archive_path = output / "ghost-integration-recovery-armv7-OFFLINE.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for n, b in sorted(files.items()):
            info = zipfile.ZipInfo(FOLDER + "/" + n, (2026, 10, 18, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            archive.writestr(info, b)
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip(): raise ValueError("Candidate ZIP CRC failure")
    report = {"zip": str(archive_path), "zip_sha256": sha(archive_path.read_bytes()), "binary_sha256": sha(files["ghost.so"]),
        "files": len(files), "vst_uid_decimal": VST_UID, "registration_uid_hex": XML_UID, "native_test_binary": str(native),
        "tabs": tui["pageData"]["tabs"], "device_access": False, "hardware_validation": "PENDING"}
    (output / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))

if __name__ == "__main__": main()
