#!/usr/bin/env python3
"""Anonymized physical refusal regression; no network or device writes."""
import os, subprocess, tempfile, pathlib, unittest, xml.etree.ElementTree as ET
R=pathlib.Path(__file__).resolve().parents[2]
class XMLPaths(unittest.TestCase):
 def parse(self,text):
  raw=('<PROPERTIES><SynthContentLocations><Location>'+text+'</Location></SynthContentLocations></PROPERTIES>').encode()
  p=subprocess.run(['awk','-v','report=locations','-f',str(R/'package-template/xml_contract.awk')],input=raw,capture_output=True,env=dict(os.environ,LC_ALL='C'))
  return p,raw
 def test_real_decimal_hex_and_literal(self):
  for text in ['/media/VOLUME&#61480;/Synths','/media/VOLUME&#xF028;/Synths','/media/VOLUME\uf028/Synths']:
   p,raw=self.parse(text);self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(p.stdout,(ET.fromstring(raw).find('.//Location').text+'\n').encode())
 def test_unicode_boundaries(self):
  for n in [32,128,2047,2048,55295,57344,65533,65536,1114111]:
   for entity in [f'&#{n};',f'&#x{n:X};']:
    p,_=self.parse('/media/'+entity+'/Synths');self.assertEqual(p.returncode,0);self.assertEqual(p.stdout,('/media/'+chr(n)+'/Synths\n').encode())
 def test_standard_and_single_decode(self):
  p,_=self.parse('/x/&amp;#61480;&lt;&gt;&quot;&apos;');self.assertEqual(p.stdout,b'/x/&#61480;<>"\'\n')
 def test_invalid_entities(self):
  for e in ['&#0;','&#31;','&#55296;','&#xDFFF;','&#65534;','&#x110000;','&#999999999999999;','&#x;','&#-1;','&#X20;','&unknown;','&amp','&#12z;']:
   self.assertNotEqual(self.parse('/media/'+e)[0].returncode,0,e)
 def guard(self,root,location):
  p,_=self.parse(location)
  if p.returncode:return p
  with tempfile.NamedTemporaryFile() as f:
   f.write(p.stdout);f.flush()
   return subprocess.run(['sh','-c','. "$1"; CONTENT=$2; checked=$(resolve_path "$3"); outside_content "$checked"','sh',str(R/'package-template/common.sh'),f.name,root],capture_output=True)
 def test_distinct_unicode_paths(self):
  self.assertEqual(self.guard('/media/VOLUME/Synths','/media/VOLUME&#61480;/Synths').returncode,0)
 def test_actual_overlap(self):
  for loc in ['/media/VOLUME&#61480;/Synths','/media/VOLUME&#xF028;/Synths/sub']:
   self.assertNotEqual(self.guard('/media/VOLUME\uf028/Synths',loc).returncode,0)
 def test_encoded_separators_and_traversal(self):
  for loc in ['/storage/GHOST&#47;Recovery/sub','/storage/GHOST-Recovery/&#46;&#46;/Synths','/storage/&#92;evil','/storage/&#10;evil','/storage/&amp;#47;evil']:
   self.assertNotEqual(self.guard('/storage/GHOST/Recovery',loc).returncode,0,loc)
 def test_encoded_line_injection(self):
  for e in ["&#10;", "&#13;", "&#9;", "&#127;"]:
   self.assertNotEqual(self.parse("/safe"+e+"/other")[0].returncode,0)
 def test_canonical_alias(self):
  with tempfile.TemporaryDirectory() as t:
   p=pathlib.Path(t);(p/'real').mkdir();(p/'alias').symlink_to(p/'real',target_is_directory=True)
   self.assertNotEqual(self.guard(str(p/'real'),str(p/'alias')).returncode,0)
class TransactionRegression(unittest.TestCase):
 def test_encoded_mount_complete_install(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location('hardening_harness',R/'tests/installer-hardening/run.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  f=m.Fixture()
  try:
   f.settings.write_text(f.settings.read_text().replace('</SynthContentLocations>', '<Location>/media/ANON&#61480;/Synths</Location></SynthContentLocations>'))
   rc,out=f.run();self.assertEqual(rc,0,out);f.check_foreign()
  finally:f.close()
if __name__=='__main__':unittest.main(verbosity=2)
