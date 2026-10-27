"""Run the established C1 VST regression suite against the isolated C1.2 binary."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments/ghost-c1"))
import bindings
bindings.OUT = ROOT / "build/ghost-c12-prototype"
import test_vst as vst_tests

suite = unittest.defaultTestLoader.loadTestsFromModule(vst_tests)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
