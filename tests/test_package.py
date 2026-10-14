#!/usr/bin/env python3
"""Inspect the actual delivery archive, identities, checksums and matching source."""
import hashlib,io,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(__file__).resolve().parents[1];base='MPC-EURO - VST - BeatRepeat/'
path=root/'build/package/MPC-EURO-BeatRepeat-armv7-proof.zip'
with zipfile.ZipFile(path) as z:
    assert z.testzip() is None
    names=z.namelist();assert len(names)==len(set(names))
    assert all(not s.startswith('/') and '..' not in Path(s).parts for s in names)
    assert not any('MPC.settings' in s or 'Delay' in s or 'Freezer' in s or '.git/' in s for s in names)
    for line in z.read(base+'SHA256SUMS').decode().splitlines():
        h,p=line.split('  ',1);assert hashlib.sha256(z.read(base+p)).hexdigest()==h
    manifest=json.loads(z.read(base+'manifest.json'));assert manifest['uid']=='45754272'
    assert manifest['inputs']==manifest['outputs']==2 and manifest['wet']=='mono centered'
    assert manifest['installer_included'] is False and manifest['hakai_3_9_1_verified'] is False
    meta=ET.fromstring(z.read('pluginlist-entry.xml'));assert meta.attrib['uid']==manifest['uid'] and meta.attrib['isInstrument']=='0'
    version=ET.fromstring(z.read(base+'version.xml'));assert version.find('identifier').text=='MPC-EURO.vst.beatrepeat'
    assert version.find('version').text=='0.1.0.0'
    assert z.read(base+'beatrepeat.so')==(root/'build/arm/beatrepeat.so').read_bytes()
    source=z.read(manifest['source_archive']);assert hashlib.sha256(source).hexdigest()==manifest['source_archive_sha256']
    with zipfile.ZipFile(io.BytesIO(source)) as src:
        for p in ['src/plugin.c','src/repeat.c','src/vst2_abi.h','ui/params.json','ui/layout.conf','Makefile','LICENSE','tools/build_arm.sh','vendor/core/beatrepeat.h']:
            assert src.read('MPC-EURO-beatrepeat/'+p)==(root/p).read_bytes()
    tui=json.loads(z.read(base+'Plugin Skins/TUI.json'))
    assert len(tui['pageData']['tabs'])==1
print('PASS delivery archive: complete assets/identity, checksums, isolated paths, exact ARM binary and matching source')
