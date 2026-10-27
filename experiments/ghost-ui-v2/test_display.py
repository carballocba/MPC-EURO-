"""Regression tests for C1.2's MPC-facing value labels and formatting."""
import ctypes
import pathlib
import sys
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments/ghost-c1"))
import bindings
bindings.OUT = ROOT / "build/ghost-c12-prototype"
from test_vst import FX


class DisplayRegression(unittest.TestCase):
    def setUp(self):
        self.fx = FX(bindings.OUT / "beatrepeat-ghost-c1.so")

    def tearDown(self):
        self.fx.close()

    def display(self, index, op=7):
        buf = ctypes.create_string_buffer(8)
        self.fx.d(self.fx.fx, op, index, 0, buf, 0)
        return buf.value.decode()

    def test_percent_length_density_and_capture_labels(self):
        self.fx.set(self.fx.fx, 2, .5)  # established absolute Dry/Wet parameter
        self.fx.set(self.fx.fx, 8, .5625)  # established relative Q-Link moves the value by 4x
        time.sleep(.05)  # wrapper publishes GUI display values on its 30 Hz notifier
        self.assertEqual(self.display(2), "75.0")
        self.assertEqual(self.display(49 + bindings.IDS["P_LENGTH"], 6), "ms")
        self.fx.set(self.fx.fx, 49 + bindings.IDS["P_DENSITY"], .25)
        time.sleep(.05)
        self.assertEqual(self.display(49 + bindings.IDS["P_DENSITY"]), "4")
        self.assertEqual(self.display(49 + bindings.IDS["P_TAKE"]), "EMPTY")


if __name__ == "__main__":
    unittest.main(verbosity=2)
