"""Offline tests for native touch geometry, Q-Link focus ownership and page navigation."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments/ghost-ui-v2"))
import native_geometry as geometry


class NativeGeometryRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tui, cls.qlinks, cls.params, cls.defs, cls.param_names = geometry.load()
        cls.views, cls.problems = geometry.collect(cls.tui, cls.qlinks, cls.defs, cls.param_names)
        cls.report = json.loads((geometry.OUT / "native-geometry-report.json").read_text())

    def test_all_eight_views_have_clean_geometry_and_viewport(self):
        self.assertEqual(len(self.views), 8)
        self.assertEqual(self.problems, [])
        self.assertTrue(all(v["initialSize"] == "0 0 1280 628" for v in self.views))
        for number in range(1, 9):
            from PIL import Image
            with Image.open(geometry.OUT / f"gui-preview-{number}.png") as image:
                self.assertEqual(image.size, (1280, 800))

    def test_perform_maps_touch_q_links_and_focus_to_same_parameter(self):
        perform = self.views[:4]
        self.assertEqual([v["fnKeySubIndex"] for v in perform], [0, 1, 2, 3])
        expected = [
            {"mix_live", "g_mdepth", "g_chaos", "g_density"},
            {"g_ghost", "g_chance", "break", "length"},
            {"capture", "g_chaoson", "g_motion", "gate"},
            {"g_clean", "g_motdice", "g_bufdice", "freeze"},
        ]
        for view, keys in zip(perform, expected):
            assignments = view["assignments"]
            self.assertEqual({a["parameter"] for a in assignments}, keys)
            self.assertEqual(len(assignments), 4)
            self.assertEqual(len({a["parameter_index"] for a in assignments}), 4)
            for assignment in assignments:
                candidates = [c for c in view["controls"] if c["parameter_index"] == assignment["parameter_index"]]
                self.assertTrue(candidates)
                self.assertEqual(sum(c["accepts_focus"] for c in candidates), 1,
                                 (view["tab"], assignment["parameter"], "focus must have one owner"))
                expected_count = 2 if assignment["parameter"] in {"freeze", "gate", "g_ghost", "g_motion", "g_chaoson"} else 1
                self.assertEqual(len(candidates), expected_count,
                                 (view["tab"], assignment["parameter"], "duplicate/hidden editable binding"))
                self.assertEqual(assignment["expected_focus_rect"], geometry._union([c["rect"] for c in candidates]))
                x, y, _, _ = assignment["expected_focus_rect_screen"]
                self.assertEqual(y - geometry.HOST_Y_OFFSET, assignment["expected_focus_rect"][1])

    def test_perform_host_outline_rectangles_are_individual_controls(self):
        for view in self.views[:4]:
            assignment_by_id = {a["qlink"]: a for a in view["assignments"]}
            ordered = [assignment_by_id[f"Q-Link {n}"]["expected_focus_rect"] for n in (13, 9, 5, 1)]
            self.assertEqual(view["host_q_link_bounds"], ordered)
            for i, left in enumerate(ordered):
                for right in ordered[i + 1:]:
                    self.assertFalse(geometry._intersects(left, right), (view["tab"], left, right))

    def test_value_readouts_are_passive_and_follow_the_mapped_parameter(self):
        trigger_parameters = {"capture", "g_bufdice", "g_motdice", "g_clean"}
        for tab in self.tui["pageData"]["tabs"][:4]:
            view = next(v for v in self.views if v["tab"] == tab["tabName"])
            children = self.defs[tab["componentName"]]["componentsData"]
            qmap = next(m["Q-Links"] for m in self.qlinks["Screen Mode Q-Links"]["map"]
                        if m["Tab"] == 1 and m["SubTab"] == tab["fnKeySubIndex"] + 1)
            for parameter in (p for p in qmap.values() if isinstance(p, int) and p >= 0):
                readouts = []
                for child in children:
                    if geometry.root_parameter(child) != parameter:
                        continue
                    definition = self.defs.get(child["componentData"]["type"], {})
                    if not definition.get("actions"):
                        readouts.append(child)
                if self.param_names[parameter]["key"] in trigger_parameters:
                    self.assertTrue(any(c["parameter_index"] == parameter for c in view["controls"]),
                                    (tab["tabName"], parameter, "trigger action is missing"))
                    self.assertTrue(all(r["bounds"]["acceptsHWFocus"] == "No" for r in readouts))
                    continue
                self.assertTrue(readouts, (tab["tabName"], parameter))
                for readout in readouts:
                    self.assertEqual(readout["bounds"]["acceptsHWFocus"], "No")
                    nested = self.defs[readout["componentData"]["type"]]
                    self.assertTrue(any(c["componentData"]["type"] == "Label" and
                                        c["componentData"].get("data", {}).get("handleName") == "Data"
                                        for c in nested.get("componentsData", [])))

    def test_report_records_host_ownership_and_pending_physical_validation(self):
        self.assertIn("MPC host", self.report["host_highlight_owner"])
        self.assertIn("pending", self.report["physical_verification"])
        self.assertEqual(sum(len(v["assignments"]) for v in self.report["views"]), 66)


if __name__ == "__main__":
    unittest.main(verbosity=2)
