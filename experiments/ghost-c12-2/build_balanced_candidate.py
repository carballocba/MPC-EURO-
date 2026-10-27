#!/usr/bin/env python3
"""Package the existing full Balanced V2 native skin for offline ARM trial."""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / "build/ghost-final-development"
SKIN = ROOT / "build/ghost-c12-prototype/native-skin/MPC-EURO - VST - BeatRepeat/Plugin Skins"
SOURCE_ZIP = BASE / "beatrepeat-ghost-final-development-offline-armv7.zip"
OUT = BASE / "balanced-v2"
PREFIX = "MPC-EURO - VST - BeatRepeat/"
UID = "45754272"
IDENT = "MPC-EURO.vst.beatrepeat"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def files_in_package() -> dict[str, bytes]:
    with zipfile.ZipFile(SOURCE_ZIP) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Base offline ZIP CRC failure")
        files = {name[len(PREFIX):]: archive.read(name) for name in archive.namelist()
                 if name.startswith(PREFIX) and not name.endswith("/")}
    files.pop("Plugin Skins/c122-background.png", None)
    files.pop("Plugin Skins/c122-ghost-on.png", None)
    files.pop("Plugin Skins/c122-ghost-off.png", None)
    files.pop("manifest.json", None)
    files.pop("SHA256SUMS", None)
    if sha(files.get("beatrepeat.so", b"")) != "5049f51646bede37f13c5bb31385b4d3c8a080dead2ca994e9ddfefb487e04b3":
        raise RuntimeError("Full skin must use the verified offline ARM build")
    for path in sorted(SKIN.rglob("*")):
        if path.is_file():
            files["Plugin Skins/" + path.relative_to(SKIN).as_posix()] = path.read_bytes()
    original = ROOT / "build/ghost-c12-1-trial/sessions/20261016T120503Z-68045/installed-plugin.before.tar"
    import tarfile
    with tarfile.open(original, "r:") as archive:
        meta_member = next(m for m in archive if m.name.endswith("plugin-meta.xml"))
        files["plugin-meta.xml"] = archive.extractfile(meta_member).read()

    tui = json.loads(files["Plugin Skins/TUI.json"])
    replaced = 0
    for definition in tui["pageData"]["componentDefinitions"]["localComponentDefinitions"]:
        name = definition["key"]
        value = definition["value"]
        for component in value.get("componentsData", []):
            if component.get("componentData", {}).get("name") != "mix_live":
                continue
            for remap in component.get("handle remapping", {}).get("map", []):
                if remap.get("value") == "Parameter 8":
                    remap["value"] = "Parameter 53"
                    replaced += 1
    if replaced != 5:
        raise RuntimeError(f"Expected five PERFORM Dry/Wet touch bindings; changed {replaced}")
    files["Plugin Skins/TUI.json"] = (json.dumps(tui, ensure_ascii=False, separators=(",", ":")) + "\n").encode()

    for name in ("Plugin Skins/Q-Links.json", "Plugin Skins/Q-Links - 8by1.json"):
        qlinks = json.loads((SKIN / pathlib.PurePosixPath(name).name).read_bytes())
        if qlinks["Program Mode Q-Links"].get("Q-Link 1") != 8:
            raise RuntimeError("Unexpected full-skin Program Mode map")
        qlinks["Program Mode Q-Links"]["Q-Link 1"] = 53
        rows = qlinks["Screen Mode Q-Links"]["map"]
        core = [row for row in rows if row["Tab"] == 1 and row["SubTab"] == 1]
        if len(core) != 1 or core[0]["Q-Links"].get("Q-Link 1") != 8:
            raise RuntimeError("Unexpected CORE Screen Mode map")
        core[0]["Q-Links"]["Q-Link 1"] = 53
        files[name] = (json.dumps(qlinks, ensure_ascii=False, indent=2) + "\n").encode()

    missing = sorted(name for name in referenced_images(files["Plugin Skins/TUI.json"])
                     if name not in files)
    if missing:
        raise RuntimeError("Balanced V2 references missing resources: " + repr(missing))
    meta = ET.fromstring(files["plugin-meta.xml"])
    version = ET.fromstring(files["version.xml"])
    if meta.get("uid") != UID or version.findtext("identifier") != IDENT:
        raise RuntimeError("Plugin metadata identity mismatch")
    return files


def referenced_images(tui_bytes: bytes) -> set[str]:
    tui = json.loads(tui_bytes)
    result: set[str] = set()
    def scan(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in ("image", "onImage", "offImage", "filmStrip") and isinstance(child, str) and child.lower().endswith(".png"):
                    result.add("Plugin Skins/" + child)
                scan(child)
        elif isinstance(value, list):
            for child in value:
                scan(child)
    scan(tui)
    return result


def main() -> None:
    files = files_in_package()
    digest_map = {name: sha(data) for name, data in sorted(files.items())}
    manifest = {
        "candidate": "GHOST final development: full Balanced V2 native GUI; offline only",
        "uid": UID,
        "identifier": IDENT,
        "gui": "4 PERFORM banks + BUFFER + MOTION + GENERATIVE + SETTINGS; 8 native views",
        "binary_sha256": digest_map["beatrepeat.so"],
        "physical_install_authorized": False,
        "hardware_validation": "pending; C1.2.1 full view had a grey-panel failure",
        "files": digest_map,
    }
    files["manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    files["SHA256SUMS"] = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(files.items())).encode()

    shutil.rmtree(OUT, ignore_errors=True)
    plugin_dir = OUT / "package/MPC-EURO - VST - BeatRepeat"
    plugin_dir.mkdir(parents=True)
    for name, data in files.items():
        target = plugin_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    zip_path = OUT / "beatrepeat-ghost-final-balanced-v2-offline-armv7.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(PREFIX + name, (2026, 10, 17, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, files[name])
    with zipfile.ZipFile(zip_path) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != {PREFIX + name for name in files}:
            raise RuntimeError("Balanced V2 ZIP verification failed")
        for name, data in files.items():
            if archive.read(PREFIX + name) != data:
                raise RuntimeError("Balanced V2 ZIP round-trip failed: " + name)
    report = {
        "candidate": manifest["candidate"],
        "zip": str(zip_path),
        "zip_sha256": sha(zip_path.read_bytes()),
        "binary_sha256": digest_map["beatrepeat.so"],
        "files": len(files),
        "views": 8,
        "plugin_uid": UID,
        "plugin_identifier": IDENT,
        "metadata_and_resources_valid": True,
        "device_accessed": False,
        "install_authorized": False,
    }
    (OUT / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
