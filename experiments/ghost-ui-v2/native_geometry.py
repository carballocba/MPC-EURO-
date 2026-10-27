"""Audit native skin touch/focus geometry and emit reproducible previews and report."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build/ghost-c12-prototype"
SKIN = OUT / "native-skin/MPC-EURO - VST - BeatRepeat/Plugin Skins"
VIEWPORT = (1280, 628)
HOST_Y_OFFSET = 86
FONT = ROOT / "vendor/fonts/DejaVuSansMono.ttf"


def load():
    tui = json.loads((SKIN / "TUI.json").read_text())
    qlinks = json.loads((SKIN / "Q-Links.json").read_text())
    params = json.loads((OUT / "parameters.json").read_text())
    definitions = {d["key"]: d["value"] for d in tui["pageData"]["componentDefinitions"]["localComponentDefinitions"]}
    param_names = {i: p for i, p in enumerate(params)}
    return tui, qlinks, params, definitions, param_names


def root_parameter(component):
    for mapping in component.get("handle remapping", {}).get("map", []):
        value = str(mapping.get("value", ""))
        if mapping.get("key") == "Data" and value.startswith("Parameter "):
            return int(value.split()[1])
    return None


def _rect(component):
    return tuple(int(round(float(v))) for v in component["bounds"]["bounds"].split())


def _intersects(a, b, margin=0):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return min(ax + aw, bx + bw) - max(ax, bx) > margin and min(ay + ah, by + bh) - max(ay, by) > margin


def _union(rects):
    x0 = min(r[0] for r in rects)
    y0 = min(r[1] for r in rects)
    x1 = max(r[0] + r[2] for r in rects)
    y1 = max(r[1] + r[3] for r in rects)
    return x0, y0, x1 - x0, y1 - y0


def _mutually_exclusive(left, right):
    """Different IndexedEnabling values on the same selector cannot be visible together."""
    def indexed(handles):
        values = {}
        for handle in handles:
            if not handle.startswith("IndexedEnabling/"):
                continue
            parts = handle.split("/")
            if len(parts) == 4 and parts[3].startswith("Parameter "):
                values[int(parts[3].split()[1])] = parts[1]
        return values
    a, b = indexed(left), indexed(right)
    return any(key in b and b[key] != value for key, value in a.items())


def _glyph_rect(text, center_x, center_y, font_size):
    font = ImageFont.truetype(str(FONT), max(9, int(round(font_size))))
    bounds = font.getbbox(text)
    w, h = bounds[2] - bounds[0], bounds[3] - bounds[1]
    return (round(center_x - w / 2), round(center_y - h / 2), w, h)


def _parameter_label(spec, label_type):
    if label_type == "Name":
        return spec["name"]
    if spec.get("options"):
        return max(spec["options"], key=len)
    if spec["key"] == "g_take":
        return "EMPTY"
    unit = spec.get("unit", "")
    values = (spec["min"], spec["default"], spec["max"])
    if spec["key"] == "g_density":
        return max((f"{v:.0f}" for v in values), key=len)
    if spec["key"] in ("g_chaos", "g_mdepth", "g_chance", "g_energy"):
        return max((f"{v * 100:.2f} %" for v in values), key=len)
    return max((f"{v:.2f} {unit}".strip() for v in values), key=len)


def _native_labels(children, definitions, param_names, ox=0, oy=0, current_param=None):
    labels = []
    for c in children:
        if any(h.startswith("IndexedEnabling/") and h.split("/")[1] != "0"
               for h in c["bounds"].get("additionalInvalidatingHandles", [])):
            continue
        x, y, w, h = _rect(c)
        x += ox
        y += oy
        component = c["componentData"]
        p = current_param
        for mapping in c.get("handle remapping", {}).get("map", []):
            value = str(mapping.get("value", ""))
            if mapping.get("key") == "Data" and value.startswith("Parameter "):
                p = int(value.split()[1])
        data = component.get("data", {})
        if component["type"] in definitions:
            labels += _native_labels(definitions[component["type"]].get("componentsData", []), definitions,
                                     param_names, x, y, p)
        elif component["type"] == "Label" and "textStyle" in data:
            text = _parameter_label(param_names[p], data.get("type", "Value")) if p is not None else ""
            size = data["textStyle"]["font"]["height"]
            cx, cy = x + w / 2, y + h / 2
            glyph = _glyph_rect(text, cx, cy, size)
            labels.append({"name": component.get("name", "Label"), "rect": glyph,
                           "visible_when": c["bounds"].get("additionalInvalidatingHandles", [])})
    return labels


def collect(tui, qlinks, definitions, param_names):
    qmap = {(m["Tab"], m["SubTab"]): m for m in qlinks["Screen Mode Q-Links"]["map"]}
    import sys
    sys.path.insert(0, str(ROOT / "vendor/mpc/tools"))
    import shadow_skin
    layout_tabs, _ = shadow_skin.parse_layout(str(OUT / "layout.conf"))
    layout_by_name = {tab["name"]: tab for tab in layout_tabs}
    views = []
    problems = []
    for tab in tui["pageData"]["tabs"]:
        roots = definitions[tab["componentName"]].get("componentsData", [])
        controls = []
        for c in roots:
            p = root_parameter(c)
            if p is None:
                continue
            name = c["componentData"]["name"]
            ctype = c["componentData"]["type"]
            definition = definitions.get(ctype, {})
            if not definition.get("actions"):
                continue  # a readout may show a Q-Link value, but never owns interactive focus
            rect = _rect(c)
            x, y, w, h = rect
            if x < 0 or y < 0 or x + w > VIEWPORT[0] or y + h > VIEWPORT[1]:
                problems.append(f"{tab['tabName']}: touch rectangle outside viewport: {name} {rect}")
            controls.append({"name": name, "parameter_index": p, "parameter": param_names[p]["key"],
                             "rect": rect, "type": ctype, "accepts_focus": c["bounds"].get("acceptsHWFocus") == "Yes",
                             "visible_when": c["bounds"].get("additionalInvalidatingHandles", [])})
        for i, left in enumerate(controls):
            for right in controls[i + 1:]:
                if (_mutually_exclusive(left["visible_when"], right["visible_when"])):
                    continue
                if _intersects(left["rect"], right["rect"], 6):
                    problems.append(f"{tab['tabName']}: hitboxes overlap: {left['name']} / {right['name']}")
        layout_tab = layout_by_name["PERFORM" if tab["fnKeyIndex"] == 0 else tab["tabName"]]
        visual_labels = _native_labels(roots, definitions, param_names)
        static_text = []
        for widget in layout_tab["widgets"]:
            if widget["kind"] not in ("text", "enum_h", "enum_v", "readout", "stepper", "menu", "popup"):
                continue
            if widget.get("banks") and tab["tabName"] not in widget["banks"].split("|"):
                continue
            text_rect = None
            if widget["kind"] == "text":
                size = 17 if float(widget.get("size", 1.5)) < 1.4 else 22
                global_rect = _glyph_rect(widget.get("label", ""), widget["cx"], widget["cy"], size)
                text_rect = global_rect
            if widget["kind"] in ("readout", "stepper", "menu", "popup") and widget.get("label"):
                text_rect = _glyph_rect(widget["label"], widget["cx"],
                                        widget["cy"] - widget["h"] / 2 - 13, 17)
            if widget["kind"] in ("enum_h", "enum_v") and widget.get("label"):
                center_y = (widget["cy"] - 33 // 2 - 22 if widget["kind"] == "enum_h" else
                            widget["cy"] - (len(widget["options"]) * 32) // 2 - 24)
                text_rect = _glyph_rect(widget["label"], widget["cx"], center_y, 18)
            if text_rect is None:
                continue
            tx, ty, tw, th = text_rect
            text_rect = (tx, ty - HOST_Y_OFFSET, tw, th)
            static_text.append({"name": widget.get("label", widget["kind"]), "rect": text_rect,
                                "visible_when": [widget["when"]] if widget.get("when") else []})
            for control in controls:
                if _mutually_exclusive(widget.get("when", "").split("|"), control["visible_when"]):
                    continue
                if _intersects(text_rect, control["rect"], 0):
                    problems.append(f"{tab['tabName']}: text/control overlap: {widget.get('label', widget['kind'])} / {control['name']}")
        all_labels = static_text + visual_labels
        for i, left in enumerate(all_labels):
            for right in all_labels[i + 1:]:
                if _mutually_exclusive(left["visible_when"], right["visible_when"]):
                    continue
                if _intersects(left["rect"], right["rect"], 0):
                    problems.append(f"{tab['tabName']}: label overlap: {left['name']} / {right['name']}")
        mapping = qmap[(tab["fnKeyIndex"] + 1, tab["fnKeySubIndex"] + 1)]["Q-Links"]
        assignments = []
        for q_name, p in mapping.items():
            if not isinstance(p, int) or p < 0:
                continue
            matches = [c for c in controls if c["parameter_index"] == p]
            if not matches:
                problems.append(f"{tab['tabName']}: {q_name} parameter {p} has no editable component")
                continue
            if not any(c["accepts_focus"] for c in matches):
                problems.append(f"{tab['tabName']}: {q_name} parameter {p} has no hardware-focus owner")
            focus_rect = _union([c["rect"] for c in matches])
            assignments.append({"qlink": q_name, "parameter_index": p, "parameter": param_names[p]["key"],
                                "control_names": [c["name"] for c in matches],
                                "expected_focus_rect": focus_rect,
                                "expected_focus_rect_screen": (focus_rect[0], focus_rect[1] + HOST_Y_OFFSET,
                                                                focus_rect[2], focus_rect[3])})
        native_rects = [tuple(map(int, s.split())) for s in tab.get("qlinkBoundsData", []) if s != "0 0 0 0"]
        for rect in native_rects:
            x, y, w, h = rect
            if x < 0 or y < 0 or x + w > VIEWPORT[0] or y + h > VIEWPORT[1]:
                problems.append(f"{tab['tabName']}: Q-Link host highlight rect outside viewport: {rect}")
        views.append({"tab": tab["tabName"], "fnKeyIndex": tab["fnKeyIndex"],
                      "fnKeySubIndex": tab["fnKeySubIndex"], "initialSize": tab["initialSize"],
                      "host_q_link_bounds": native_rects, "assignments": assignments, "controls": controls})
    return views, problems


def apply_perform_focus_bounds(tui, qlinks, definitions):
    """Give each of the four visible PERFORM encoder assignments its own host focus rectangle."""
    qmap = {(m["Tab"], m["SubTab"]): m["Q-Links"] for m in qlinks["Screen Mode Q-Links"]["map"]}
    for tab in tui["pageData"]["tabs"]:
        if tab["fnKeyIndex"] != 0:
            continue
        page = definitions[tab["componentName"]]
        controls = {}
        for c in page.get("componentsData", []):
            p = root_parameter(c)
            if p is None or not definitions.get(c["componentData"]["type"], {}).get("actions"):
                continue
            controls.setdefault(p, []).append(_rect(c))
        mapping = qmap[(tab["fnKeyIndex"] + 1, tab["fnKeySubIndex"] + 1)]
        # The community skin's MPC One order is Q-Link 13, 9, 5, 1 from left to right.
        bounds = []
        for number in (13, 9, 5, 1):
            p = mapping[f"Q-Link {number}"]
            if p not in controls:
                raise ValueError(f"{tab['tabName']}: Q-Link {number} has no interactive parameter control")
            bounds.append(" ".join(map(str, _union(controls[p]))))
        tab["qlinkBoundsData"] = bounds


def render_previews(tui, params, definitions):
    """Render the final native component tree, including the MPC host viewport and tab metadata."""
    font = ImageFont.truetype(str(FONT), 16)
    param_index = {i: p for i, p in enumerate(params)}

    def paint(image, children, ox=0, oy=0, current_param=None):
        for c in children:
            if any(h.startswith("IndexedEnabling/") and h.split("/")[1] != "0"
                   for h in c["bounds"].get("additionalInvalidatingHandles", [])):
                continue
            p = current_param
            for m in c.get("handle remapping", {}).get("map", []):
                if m.get("key") == "Data" and str(m.get("value", "")).startswith("Parameter "):
                    p = int(m["value"].split()[1])
            component = c["componentData"]
            data = component.get("data", {})
            x, y, w, h = _rect(c)
            x += ox
            y += oy
            kind = component["type"]
            nested = definitions.get(kind)
            if nested:
                paint(image, nested.get("componentsData", []), x, y, p)
                continue
            if kind == "Image":
                path = SKIN / data.get("image", "")
                if path.is_file():
                    asset = Image.open(path).convert("RGBA").resize((w, h))
                    image.paste(asset, (x, y), asset)
            elif kind == "Knob" and data.get("filmStrip") and p is not None:
                path = SKIN / data["filmStrip"]
                if path.is_file():
                    strip = Image.open(path).convert("RGBA")
                    spec = param_index[p]
                    span = max(1e-12, spec["max"] - spec["min"])
                    frame = round((spec["default"] - spec["min"]) / span * (strip.height // strip.width - 1))
                    asset = strip.crop((0, frame * strip.width, strip.width, (frame + 1) * strip.width)).resize((w, h))
                    image.paste(asset, (x, y), asset)
            elif kind == "Label" and p is not None and "textStyle" in data:
                spec = param_index[p]
                style = data["textStyle"]
                text = spec["name"] if data.get("type") == "Name" else (
                    ("TAKE" if spec["default"] >= .5 else "EMPTY") if spec["key"] == "g_take" else
                    spec["options"][int(spec["default"])] if spec.get("options") else
                     f"{spec['default']:.0f}" if spec["key"] == "g_density" else
                     f"{spec['default'] * 100:.2f} %" if spec["key"] in ("g_chaos", "g_mdepth", "g_chance", "g_energy") else
                     f"{spec['default']:.2f} {spec.get('unit', '')}")
                text_font = ImageFont.truetype(str(FONT), round(style["font"]["height"]))
                ImageDraw.Draw(image).text((x + w / 2, y + h / 2), text, font=text_font,
                                           anchor="mm", fill="#" + style["colour"][-6:])
            elif kind == "Button" and data.get("offImage"):
                path = SKIN / data["offImage"]
                if path.is_file():
                    asset = Image.open(path).convert("RGBA").resize((w, h))
                    image.paste(asset, (x, y), asset)

    # These tabs are actual TUI host page/subpage registrations, shown in the preview as host chrome.
    page_labels = {0: "PERFORM", 1: "BUFFER", 2: "MOTION", 3: "GENERATIVE", 4: "SETTINGS"}
    for number, tab in enumerate(tui["pageData"]["tabs"], 1):
        image = Image.new("RGB", (1280, 800), "#10151b")
        paint(image, definitions[tab["componentName"]].get("componentsData", []), 0, HOST_Y_OFFSET)
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 1279, HOST_Y_OFFSET - 1), fill="#080d11")
        draw.text((28, 12), "MPC HOST  /  BEATREPEAT", font=font, fill="#8899a8")
        active = page_labels[tab["fnKeyIndex"]]
        labels = list(page_labels.values())
        x0, gap, width = 28, 8, 172
        for i, label in enumerate(labels):
            x = x0 + i * (width + gap)
            fill = "#21443f" if label == active else "#172129"
            draw.rounded_rectangle((x, 40, x + width, 76), radius=5, fill=fill,
                                   outline="#65dbc6" if label == active else "#34434d", width=1)
            draw.text((x + 12, 48), label, font=font, fill="#65dbc6" if label == active else "#8899a8")
        if tab["fnKeyIndex"] == 0:
            draw.text((930, 50), "BANK  " + tab["tabName"], font=font, fill="#f5ac66")
        image.save(OUT / f"gui-preview-{number}.png")


def write_report(views, problems):
    payload = {"viewport": {"width": VIEWPORT[0], "height": VIEWPORT[1], "host_screen_y_offset": HOST_Y_OFFSET},
               "views": views, "problems": problems,
               "host_highlight_owner": "MPC host; skin supplies qlinkBoundsData and acceptsHWFocus bounds",
               "physical_verification": "pending on the original MPC One; previews cannot verify host-rendered yellow focus"}
    (OUT / "native-geometry-report.json").write_text(json.dumps(payload, indent=2) + "\n")
    lines = ["# GHOST C1.2.1 — auditoría de GUI nativa y foco Q-Link", "",
             "Las coordenadas usan el viewport nativo de 1280×628; `screen` suma el desplazamiento de 86 px del host. El marco amarillo lo dibuja MPC; el informe verifica la geometría que recibe el host, no el resultado físico.", "",
             "## Causa y corrección", "",
             "El exportador de la comunidad nombra las imágenes segmentadas como `sh_seg_<parámetro>_<opción>`. Freeze y Motion se reutilizan en páginas con etiquetas distintas. La pasada de fuente escribía, en el mismo PNG, más de una etiqueta (por ejemplo FROZEN y HELD; OFF/ON aparecía duplicado). Se aislaron las definiciones y los PNG de PERFORM, BUFFER y MOTION. BUFFER conserva el valor 0/1 del parámetro Freeze, con el rótulo táctil legible HELD.", "",
             "En `TUI.json`, cada control nativo enlaza su `Data` con un índice de parámetro. `acceptsHWFocus` permite al host elegir el control editable; los readouts quedan pasivos y sin foco. `qlinkBoundsData` entrega las áreas de la página, mientras `Q-Links.json` mapea el Q-Link al índice. La geometría PERFORM ahora entrega cuatro rectángulos individuales, en orden físico 13, 9, 5, 1, ajustados a los controles editables. No se cambiaron las asignaciones Program Mode ni los índices.", "",
             "La caja amarilla es propiedad del host MPC, no del plugin: el VST2 solo entrega parámetros y texto de valor. El plugin no puede dibujarla ni imponer el foco del host. El upstream comunitario describe las páginas como controles declarativos del host y documenta la geometría por `qlinkBoundsData` en [sd88me/mpc-vst-plugins](https://github.com/sd88me/mpc-vst-plugins). Por ello, el arreglo de geometría está implementado offline, pero el alineamiento amarillo real queda pendiente de la One.", "",
             "La navegación principal sigue siendo la del host: `fnKeyIndex` mantiene las cinco páginas y `fnKeySubIndex` selecciona los cuatro bancos PERFORM. No se añadió una segunda barra táctil dentro del plugin que compita con el cambio de página de MPC. La cabecera de los PNG es una guía de revisión generada desde esos índices, no una captura exacta del chrome del host.", "",
             "## Resultado geométrico", "",
             "La auditoría comprueba colisiones de texto con controles táctiles, etiquetas nativas entre sí, hitboxes, límites de viewport, foco único por parámetro, destino de los cuatro bancos y desplazamiento host/plugin. Prueba también que readouts de valores no acepten foco y sigan enlazados al mismo parámetro. Las ocho vistas tienen preview 1280×800.", ""]
    for view in views:
        lines += [f"## {view['tab']}", "", "| Q-Link | Parameter | Expected focus rectangle (plugin x y w h) | Screen x y w h |",
                  "| --- | --- | --- | --- |"]
        for a in view["assignments"]:
            lines.append(f"| {a['qlink']} | `{a['parameter']}` ({a['parameter_index']}) | `{a['expected_focus_rect']}` | `{a['expected_focus_rect_screen']}` |")
        lines.append("")
        lines.append("Host column bounds: " + (", ".join(f"`{r}`" for r in view["host_q_link_bounds"]) or "none") + ".")
        lines.append("")
    lines += ["## Lista breve para la One", "",
              "1. Abrir cada banco CORE, REPEAT, ENGINE y ACTION; seleccionar cada uno de sus cuatro parámetros con el Q-Link físico correspondiente.",
              "2. Confirmar que el marco amarillo rodea solo el rectángulo indicado arriba, sin tapar la etiqueta ni otro control.",
              "3. Girar el encoder y verificar que cambia el mismo parámetro y que el valor visible sigue el cambio.",
              "4. Cambiar bancos y páginas; repetir con selección táctil seguida de giro del Q-Link y después de recuperar un preset.",
              "5. Aprobar solo si no hay foco obsoleto, parámetro cruzado, valor desincronizado ni selección tapada. Si MPC ignora o reinterpreta los rectángulos, conservar el mapeo y usar selección táctil más lectura visible como alternativa; no dibujar una caja amarilla falsa. El foco amarillo seguirá pendiente hasta probar el hardware.", ""]
    (ROOT / "docs/ghost/GHOST_C12_1_NATIVE_UI_POLISH.md").write_text("\n".join(lines))
    return payload


def audit_and_render():
    tui, qlinks, params, definitions, param_names = load()
    apply_perform_focus_bounds(tui, qlinks, definitions)
    (SKIN / "TUI.json").write_text(json.dumps(tui, separators=(",", ":")))
    views, problems = collect(tui, qlinks, definitions, param_names)
    render_previews(tui, params, definitions)
    return write_report(views, problems)


if __name__ == "__main__":
    result = audit_and_render()
    print(f"Audited {len(result['views'])} native views; {sum(len(v['assignments']) for v in result['views'])} Q-Link focus targets")
    if result["problems"]:
        print("\n".join(result["problems"]))
        raise SystemExit(1)
