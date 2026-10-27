#!/usr/bin/env python3
"""Build a separately identified, offline-only GHOST ARMv7 package.

The audio implementation is the tested C1.2.2 wrapper. Only the VST identity
and catalog metadata differ; no installer or device access is performed.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / "build/ghost-final-development"
SOURCE_ZIP = BASE / "balanced-v2/beatrepeat-ghost-final-balanced-v2-offline-armv7.zip"
OUT = BASE / "independent-ghost"
PREFIX = "MPC-EURO - VST - BeatRepeat/"
FOLDER = "MPC-EURO - VST - GHOST"
UID_HEX = 0x47485354  # FourCC "GHST"; local collision checks live in tests.
UID = str(UID_HEX)
XML_UID = f"{UID_HEX:08x}"  # JUCE PluginDescription XML uses hexadecimal, not decimal.
IDENTIFIER = "MPC-EURO.vst.ghost"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_arm(diagnostics: bool = False, strip_debug: bool = False, final_product: bool = False, buffer_engine: bool = False) -> tuple[pathlib.Path, dict]:
    zig = ROOT / "build/venv/lib/python3.13/site-packages/ziglang/zig"
    if not zig.is_file():
        raise SystemExit("Offline Zig compiler missing; no network/download attempted")
    prep = ROOT / "build/ghost-c11-demo/base-render.inc"
    if not prep.is_file():
        raise SystemExit("Missing validated base-render include; refusing implicit regeneration")
    arm = OUT / "arm-build"
    arm.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, ZIG_GLOBAL_CACHE_DIR=str(arm / "zig-global"), ZIG_LOCAL_CACHE_DIR=str(arm / "zig-local"))
    common = [str(zig), "cc", "-target", "arm-linux-gnueabihf.2.31", "-mcpu=cortex_a9",
              "-DGHOST_STANDALONE_UID=0x47485354", "-std=c11", "-O2", "-ffp-contract=off",
              "-fPIC", "-fvisibility=hidden", "-I" + str(ROOT / "build"), "-I" + str(ROOT / "src")]
    if diagnostics:
        common.append("-DGHOST_INTEGRATION_PROBE=1")
    if final_product:
        common.append("-DGHOST_FINAL_PRODUCT=1")
    if buffer_engine:
        common.append("-DGHOST_BUFFER_ENGINE=1")
    link_flags = ["-Wl,--strip-debug"] if strip_debug else []
    sources = ["core.c", "motion.c", "params.c", "state.c", "vst.c", "base.c",
               "../ghost/ghost.c", "engine.c", "../../src/repeat.c"]
    objects = []
    for index, source in enumerate(sources):
        obj = arm / f"unit-{index}.o"
        subprocess.run([*common, "-c", str(ROOT / "experiments/ghost-c1" / source), "-o", str(obj)], env=env, check=True)
        objects.append(str(obj))
    binary = arm / "ghost.so"
    subprocess.run([*common, "-shared", *objects, *link_flags, "-lm", "-pthread", "-Wl,--no-undefined",
                    "-Wl,--version-script=" + str(ROOT / "src/exports.map"), "-o", str(binary)], env=env, check=True)
    from elftools.elf.elffile import ELFFile
    with binary.open("rb") as stream:
        elf = ELFFile(stream)
        if elf.elfclass != 32 or elf["e_machine"] != "EM_ARM" or not elf["e_flags"] & 0x400:
            raise RuntimeError("Candidate is not ARM32 hard-float")
        exports = [s.name for s in elf.get_section_by_name(".dynsym").iter_symbols()
                   if s["st_shndx"] != "SHN_UNDEF" and s["st_info"]["bind"] == "STB_GLOBAL"]
        needed = sorted({tag.needed for tag in elf.get_section_by_name(".dynamic").iter_tags()
                         if tag.entry.d_tag == "DT_NEEDED"})
        versions = elf.get_section_by_name(".gnu.version_r")
        glibc = sorted({aux.name for _, auxes in versions.iter_versions() for aux in auxes
                        if aux.name.startswith("GLIBC_")}) if versions else []
    if exports != ["VSTPluginMain"] or set(needed) - {"libc.so.6", "libm.so.6", "libpthread.so.0", "ld-linux-armhf.so.3"}:
        raise RuntimeError(f"Unexpected ARM ABI: exports={exports}, dependencies={needed}")
    if any(tuple(map(int, version[6:].split("."))) > (2, 31) for version in glibc):
        raise RuntimeError(f"glibc requirement exceeds Hakai target: {glibc}")
    report = {"elf_bits": 32, "machine": "ARM", "hard_float": True, "exports": exports,
              "needed": needed, "glibc_versions": glibc, "uid_hex": hex(UID_HEX),
              "sha256": sha(binary.read_bytes()), "bytes": binary.stat().st_size,
              "executed_on_arm": False, "hardware_validation": "pending"}
    return binary, report


def compile_native_identity_test(diagnostics: bool = False, final_product: bool = False, buffer_engine: bool = False) -> pathlib.Path:
    cc = shutil.which("cc")
    if not cc:
        raise SystemExit("A native C compiler is required for the offline identity check")
    work = ROOT / "experiments/ghost-c1"
    flags = ["-std=c11", "-Wall", "-Wextra", "-Werror", "-ffp-contract=off", "-DGHOST_STANDALONE_UID=0x47485354",
             "-I../../src", "-I../ghost", "-I.", "-I../../build", "-O2", "-fPIC"]
    if diagnostics:
        flags.append("-DGHOST_INTEGRATION_PROBE=1")
    if final_product:
        flags.append("-DGHOST_FINAL_PRODUCT=1")
    if buffer_engine:
        flags.append("-DGHOST_BUFFER_ENGINE=1")
    obj = OUT / "native-base.o"
    subprocess.run([cc, *flags, "-c", "base.c", "-o", str(obj)], cwd=work, check=True)
    native = OUT / "ghost-identity-test.so"
    subprocess.run([cc, *flags, "-shared", "core.c", "motion.c", "params.c", "state.c", "../ghost/ghost.c",
                    "engine.c", "vst.c", str(obj), "../../src/repeat.c", "-lm", "-pthread", "-o", str(native)],
                   cwd=work, check=True)
    return native


def main() -> None:
    global OUT
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=OUT)
    OUT = parser.parse_args().out.resolve()
    if not SOURCE_ZIP.is_file():
        raise SystemExit("Balanced V2 offline package missing; build and verify it first")
    if OUT.exists():
        raise SystemExit("Output already exists; choose a new --out. Historical packages, sessions and backups are never deleted.")
    OUT.mkdir(parents=True)
    binary, abi = compile_arm()
    native_identity = compile_native_identity_test()
    with zipfile.ZipFile(SOURCE_ZIP) as archive:
        if archive.testzip():
            raise RuntimeError("Source Balanced V2 ZIP has a CRC error")
        files = {name[len(PREFIX):]: archive.read(name) for name in archive.namelist()
                 if name.startswith(PREFIX) and not name.endswith("/")}
    files.pop("manifest.json", None)
    files.pop("SHA256SUMS", None)
    files.pop("beatrepeat.so", None)
    files["ghost.so"] = binary.read_bytes()
    meta = ET.fromstring(files["plugin-meta.xml"])
    meta.set("name", "GHOST")
    meta.set("descriptiveName", "GHOST / Living Instrument")
    meta.set("uid", XML_UID)
    meta.set("file", f"%payload-path%/{FOLDER}/ghost.so")
    files["plugin-meta.xml"] = ET.tostring(meta, encoding="utf-8", xml_declaration=True) + b"\n"
    version = ET.Element("plugincontent", {"version": "1.0"})
    ET.SubElement(version, "identifier").text = IDENTIFIER
    ET.SubElement(version, "version").text = "2.2.0.0"
    files["version.xml"] = ET.tostring(version, encoding="utf-8", xml_declaration=True) + b"\n"
    manifest = {"candidate": "GHOST Balanced V2, independent VST identity, offline only",
                "product": "GHOST", "uid": UID, "uid_hex": hex(UID_HEX), "registration_uid": XML_UID, "identifier": IDENTIFIER,
                "folder": FOLDER, "binary_sha256": sha(files["ghost.so"]), "abi": abi,
                "physical_uid_collision_check": "required before registration",
                "hardware_validation": "pending", "device_accessed": False,
                "install_authorized": False,
                "files": {name: sha(data) for name, data in sorted(files.items())}}
    files["manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    files["SHA256SUMS"] = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(files.items())).encode()
    package = OUT / "package" / FOLDER
    package.mkdir(parents=True)
    for name, data in files.items():
        target = package / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    zip_path = OUT / "ghost-balanced-v2-independent-armv7-OFFLINE.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(FOLDER + "/" + name, (2026, 10, 17, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, files[name])
    report = {"zip": str(zip_path), "zip_sha256": sha(zip_path.read_bytes()),
              "binary_sha256": sha(files["ghost.so"]), "files": len(files), "uid": UID,
              "identity": IDENTIFIER, "native_identity_test": str(native_identity),
              "device_accessed": False, "install_authorized": False}
    (OUT / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    (OUT / "abi-report.json").write_text(json.dumps(abi, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
