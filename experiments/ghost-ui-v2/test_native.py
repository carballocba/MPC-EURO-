"""Offline structure/regression checks for the isolated C1.2 native GUI build."""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
C11 = ROOT / "build/ghost-c11-demo/native-skin/MPC-EURO - VST - BeatRepeat/Plugin Skins"
C12 = ROOT / "build/ghost-c12-prototype/native-skin/MPC-EURO - VST - BeatRepeat/Plugin Skins"
OUT = ROOT / "build/ghost-c12-prototype"


def read_json(path):
    return json.loads(path.read_text())


def defs(path):
    tui = read_json(path / "TUI.json")
    return tui, {d["key"]: d["value"] for d in tui["pageData"]["componentDefinitions"]["localComponentDefinitions"]}


class NativeGuiRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_tui, cls.old_defs = defs(C11)
        cls.new_tui, cls.new_defs = defs(C12)

    def test_only_perform_page_graph_changed(self):
        old_tabs = self.old_tui["pageData"]["tabs"]
        new_tabs = self.new_tui["pageData"]["tabs"]
        self.assertEqual([t["tabName"] for t in new_tabs[4:]], ["BUFFER", "MOTION", "GENERATIVE", "SETTINGS"])
        for name in ("BUFFER", "MOTION", "GENERATIVE", "SETTINGS"):
            old = next(t for t in old_tabs if t["tabName"] == name)
            new = next(t for t in new_tabs if t["tabName"] == name)
            old_kids = self.old_defs[old["componentName"]]["componentsData"]
            new_kids = self.new_defs[new["componentName"]]["componentsData"]
            old_controls = sorted((c["componentData"]["name"].split()[0], skin_param(c, self.old_defs))
                                  for c in old_kids if skin_param(c, self.old_defs) is not None
                                  and self.old_defs.get(c["componentData"]["type"], {}).get("actions"))
            new_controls = sorted((c["componentData"]["name"].split()[0], skin_param(c, self.new_defs))
                                  for c in new_kids if skin_param(c, self.new_defs) is not None
                                  and self.new_defs.get(c["componentData"]["type"], {}).get("actions"))
            self.assertEqual(old_controls, new_controls, name + " bindings")
            old_q = read_json(C11 / "Q-Links.json")["Screen Mode Q-Links"]["map"]
            new_q = read_json(C12 / "Q-Links.json")["Screen Mode Q-Links"]["map"]
            self.assertEqual([x for x in old_q if x["Tab"] == old["fnKeyIndex"] + 1],
                             [x for x in new_q if x["Tab"] == new["fnKeyIndex"] + 1], name + " Q-Link map")
        self.assertEqual((OUT / "parameters.json").read_bytes(), (ROOT / "build/ghost-c11-demo/parameters.json").read_bytes())

    def test_perform_controls_are_bound_and_touchable(self):
        required = {"g_density", "g_chaos", "g_mdepth", "mix_live", "length", "break", "g_chance", "gate",
                    "g_ghost", "g_motion", "capture", "freeze", "g_bufdice", "g_motdice", "g_clean", "g_chaoson", "punch"}
        text = (ROOT / "experiments/ghost-ui-v2/perform.layout").read_text()
        used = {line.split("key=", 1)[1].split()[0] for line in text.splitlines() if "key=" in line}
        self.assertTrue(required <= used, sorted(required - used))
        self.assertIn('key=g_motdice label="MOT DICE"', text)
        self.assertIn('key=g_bufdice label="BUF DICE"', text)
        for bank in ("01 / CORE", "02 / REPEAT", "03 / ENGINE", "04 / ACTION"):
            self.assertIn(f'qlinks "{bank}"', text)
        names = [t["tabName"] for t in self.new_tui["pageData"]["tabs"][:4]]
        self.assertEqual(names, ["01 / CORE", "02 / REPEAT", "03 / ENGINE", "04 / ACTION"])
        page_indices = {t["fnKeyIndex"] for t in self.new_tui["pageData"]["tabs"]}
        self.assertEqual(page_indices, {0, 1, 2, 3, 4}, "five top-level MPC pages remain available")
        self.assertEqual([t["fnKeySubIndex"] for t in self.new_tui["pageData"]["tabs"] if t["fnKeyIndex"] == 0], [0, 1, 2, 3])
        # Freeze and Motion get private assets to avoid cross-page enum filename collisions.
        self.assertEqual(ImageSize(C12 / "c12-perform-freeze-live-off.png"), (70, 56))
        self.assertEqual(ImageSize(C12 / "c12-perform-freeze-held-on.png"), (70, 56))
        self.assertEqual(ImageSize(C12 / "c12-perform-motion-off-off.png"), (62, 56))
        self.assertEqual(ImageSize(C12 / "c12-perform-motion-on-on.png"), (62, 56))
        self.assertEqual(ImageSize(C12 / "c12-buffer-freeze-held-off.png"), (95, 56))
        self.assertEqual(ImageSize(C12 / "c12-motion-page-off-off.png"), (98, 44))
        for tab in self.new_tui["pageData"]["tabs"][:4]:
            children = self.new_defs[tab["componentName"]]["componentsData"]
            freeze_types = {c["componentData"]["type"] for c in children if c["componentData"]["name"].startswith("freeze ")}
            self.assertEqual(freeze_types, {"c12PerformFreeze_live", "c12PerformFreeze_held"})
            motion_types = {c["componentData"]["type"] for c in children if c["componentData"]["name"] in ("g_motion OFF", "g_motion ON")}
            self.assertEqual(motion_types, {"c12PerformMotion_off", "c12PerformMotion_on"})
        buffer = next(t for t in self.new_tui["pageData"]["tabs"] if t["tabName"] == "BUFFER")
        self.assertEqual({c["componentData"]["type"] for c in self.new_defs[buffer["componentName"]]["componentsData"]
                          if c["componentData"]["name"].startswith("freeze ")},
                         {"c12BufferFreeze_live", "c12BufferFreeze_held"})
        motion = next(t for t in self.new_tui["pageData"]["tabs"] if t["tabName"] == "MOTION")
        self.assertEqual({c["componentData"]["type"] for c in self.new_defs[motion["componentName"]]["componentsData"]
                          if c["componentData"]["name"].startswith("g_motion ")},
                         {"c12MotionPage_off", "c12MotionPage_on"})

    def test_program_mode_and_sixteen_legacy_qlinks_are_unchanged(self):
        old = read_json(C11 / "Q-Links.json")
        new = read_json(C12 / "Q-Links.json")
        self.assertEqual(new["Program Mode Q-Links"], old["Program Mode Q-Links"])
        self.assertEqual(set(new["Program Mode Q-Links"]), {f"Q-Link {i}" for i in range(1, 17)})
        screen = new["Screen Mode Q-Links"]["map"]
        perform = [m for m in screen if m["Tab"] == 1]
        self.assertEqual([m["SubTab"] for m in perform], [1, 2, 3, 4])
        for mapping in perform:
            active = [v for v in mapping["Q-Links"].values() if v >= 0]
            self.assertEqual(len(active), 4)
            self.assertEqual(len(set(active)), 4)
        params = read_json(OUT / "parameters.json")
        index = {p["key"]: i for i, p in enumerate(params)}
        expected = [
            ["g_density", "g_chaos", "g_mdepth", "mix_live"],
            ["length", "break", "g_chance", "g_ghost"],
            ["gate", "g_motion", "g_chaoson", "capture"],
            ["freeze", "g_bufdice", "g_motdice", "g_clean"],
        ]
        # MPC's established physical order is Q-Link 13, 9, 5, 1 from left to right.
        for row, keys in zip(perform, expected):
            self.assertEqual([row["Q-Links"][f"Q-Link {n}"] for n in (13, 9, 5, 1)], [index[k] for k in keys])

    def test_truthful_energy_and_mascot_indicators_are_native(self):
        children = self.new_defs[self.new_tui["pageData"]["tabs"][0]["componentName"]]["componentsData"]
        energy = [c for c in children if c["componentData"]["name"].startswith("Energy level")]
        mascot = [c for c in children if c["componentData"]["name"].startswith("Ghost ")]
        self.assertEqual(len(energy), 8)
        self.assertEqual(len(mascot), 8)
        self.assertTrue(all("IndexedEnabling/" in " ".join(c["bounds"]["additionalInvalidatingHandles"]) for c in energy + mascot))
        self.assertFalse(any(c["componentData"]["name"].lower().find("wave") >= 0 for c in children))


def ImageSize(path):
    from PIL import Image
    with Image.open(path) as im:
        return im.size


def skin_param(component, definitions):
    for mapping in component.get("handle remapping", {}).get("map", []):
        value = str(mapping.get("value", ""))
        if mapping.get("key") == "Data" and value.startswith("Parameter "):
            return int(value.split()[1])
    return None


if __name__ == "__main__":
    unittest.main(verbosity=2)
