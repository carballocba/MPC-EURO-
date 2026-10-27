"""Build a reproducible ARMv7 C1.2 GUI package without touching C1.1 outputs."""
import hashlib
import json
import pathlib
import runpy
import shutil
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "build/ghost-c12-prototype"
sys.path.insert(0, str(ROOT / "experiments/ghost-c1"))
import bindings

bindings.OUT = OUT
shutil.rmtree(OUT / "package", ignore_errors=True)
for artifact in (OUT / "beatrepeat-ghost-c11-armv7-OFFLINE.zip", OUT / "beatrepeat-ghost-c12-armv7-OFFLINE.zip", OUT / "package-manifest.json"):
    artifact.unlink(missing_ok=True)
baseline_include = ROOT / "build/ghost-c11-demo/base-render.inc"
if not baseline_include.is_file():
    raise SystemExit("Missing validated C1.1 base-render.inc; refusing to regenerate or overwrite it")
before = hashlib.sha256(baseline_include.read_bytes()).hexdigest()
source = (ROOT / "experiments/ghost-c1/arm.py").read_text()
prepare = "subprocess.run(['python3',str(ROOT/'experiments/ghost-c1/prepare.py')],check=True)"
if source.count(prepare) != 1:
    raise SystemExit("arm.py prepare anchor changed; refusing to execute an unsafe build")
source = source.replace(prepare, "# Reuse the validated, read-only C1.1 base-render include.")
exec(compile(source, str(ROOT / "experiments/ghost-c1/arm.py"), "exec"), {"__name__": "__main__"})
after = hashlib.sha256(baseline_include.read_bytes()).hexdigest()
if before != after:
    raise SystemExit("C1.1 base-render include changed during C1.2 build")

manifest_path = OUT / "package-manifest.json"
manifest = json.loads(manifest_path.read_text())
manifest["candidate"] = "GHOST C1.2 Balanced native PERFORM GUI prototype, offline only"
manifest["reference_commit"] = "16cb679"
manifest["branch"] = "codex/ghost-c12-living-v2"
manifest["uid"] = "45754272"
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
old_zip = OUT / "beatrepeat-ghost-c11-armv7-OFFLINE.zip"
new_zip = OUT / "beatrepeat-ghost-c12-armv7-OFFLINE.zip"
if old_zip.exists():
    old_zip.rename(new_zip)
print(f"C1.1 base-render preserved: sha256 {after}")
print(f"Offline C1.2 ARMv7 package: {new_zip}")
expected = {"MPC-EURO - VST - BeatRepeat/" + name for name in manifest["files"]}
with zipfile.ZipFile(new_zip) as archive:
    if archive.testzip() is not None:
        raise SystemExit("Packaged ZIP failed its CRC check")
    if set(archive.namelist()) != expected:
        raise SystemExit("Packaged ZIP entries differ from the verified manifest")
    for name, digest in manifest["files"].items():
        if hashlib.sha256(archive.read("MPC-EURO - VST - BeatRepeat/" + name)).hexdigest() != digest:
            raise SystemExit(f"Packaged file hash mismatch: {name}")
    version = archive.read("MPC-EURO - VST - BeatRepeat/version.xml").decode()
    if "MPC-EURO.vst.beatrepeat" not in version or manifest["uid"] != "45754272":
        raise SystemExit("Package identity check failed")
print(f"Package verified: {len(expected)} files, ZIP CRC and SHA-256 entries pass, UID 45754272")
