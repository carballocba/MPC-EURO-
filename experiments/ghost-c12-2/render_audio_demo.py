#!/usr/bin/env python3
"""Render deterministic, synthetic drum-loop examples through the native VST."""
from __future__ import annotations

import ctypes as C
import hashlib
import json
import math
import pathlib
import random
import sys
import wave

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "build/ghost-final-development"
sys.path.insert(0, str(ROOT / "experiments/ghost-c1"))
sys.path.insert(0, str(ROOT / "tests"))
import bindings
bindings.OUT = OUT / "native"
from test_vst import FX


def drum_loop(rate: int = 44100, seconds: float = 4.0) -> tuple[list[float], list[float]]:
    total = int(rate * seconds)
    left = [0.0] * total
    right = [0.0] * total
    rng = random.Random(45754272)
    beats = [i * .5 for i in range(8)]
    snare = [.5, 1.5, 2.5, 3.5]
    hats = [i * .25 for i in range(16)]
    def burst(start: float, length: float, amplitude: float, colour: str) -> None:
        begin = int(start * rate)
        end = min(total, begin + int(length * rate))
        for n in range(begin, end):
            t = (n - begin) / rate
            if colour == "kick":
                env = math.exp(-t * 23)
                sample = amplitude * env * math.sin(2 * math.pi * (48 + 24 * env) * t)
            else:
                env = math.exp(-t * (28 if colour == "snare" else 75))
                noise = rng.uniform(-1, 1)
                tone = .18 * math.sin(2 * math.pi * 180 * t) if colour == "snare" else 0
                sample = amplitude * env * (noise + tone)
            left[n] += sample * .94
            right[n] += sample * 1.0
    for t in beats:
        burst(t, .18, .62, "kick")
    for t in snare:
        burst(t, .16, .25, "snare")
    for t in hats:
        burst(t, .035, .09, "hat")
    return left, right


def process(fx: FX, left: list[float], right: list[float], n: int = 128) -> tuple[list[float], list[float]]:
    out_l = [0.0] * len(left)
    out_r = [0.0] * len(right)
    for start in range(0, len(left), n):
        count = min(n, len(left) - start)
        il = (C.c_float * count)(*left[start:start + count])
        ir = (C.c_float * count)(*right[start:start + count])
        ol = (C.c_float * count)()
        or_ = (C.c_float * count)()
        inputs = (C.POINTER(C.c_float) * 2)(il, ir)
        outputs = (C.POINTER(C.c_float) * 2)(ol, or_)
        fx.process(fx.fx, inputs, outputs, count)
        out_l[start:start + count] = ol[:]
        out_r[start:start + count] = or_[:]
    return out_l, out_r


def write_wav(path: pathlib.Path, channels: tuple[list[float], list[float]], rate: int) -> None:
    import struct
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2); wav.setsampwidth(2); wav.setframerate(rate)
        frames = bytearray()
        for l, r in zip(*channels):
            for sample in (l, r):
                sample = max(-.999969, min(.999969, sample))
                frames.extend(struct.pack("<h", round(sample * 32767)))
        wav.writeframes(frames)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rate = 44100
    source = drum_loop(rate)
    dry_fx = FX(OUT / "native/beatrepeat-ghost-c12-2.so")
    wet_fx = FX(OUT / "native/beatrepeat-ghost-c12-2.so")
    try:
        for fx in (dry_fx, wet_fx):
            fx.set(fx.fx, 48, 0)  # modern engine; no legacy compatibility path
            fx.set(fx.fx, 53, 1)  # full wet when a repeat is active
        dry = process(dry_fx, *source)
        wet_fx.set(wet_fx.fx, 1, 1)  # exact touchscreen Repeat Gate binding
        wet = process(wet_fx, *source)
        active_at_end = wet_fx.get(wet_fx.fx, 6) >= .5
    finally:
        dry_fx.close(); wet_fx.close()
    path_dry = OUT / "demo-drum-loop-dry.wav"
    path_wet = OUT / "demo-drum-loop-repeat.wav"
    write_wav(path_dry, dry, rate); write_wav(path_wet, wet, rate)
    difference = max(abs(a-b) for a,b in zip(wet[0], dry[0]))
    rms_difference = math.sqrt(sum((a-b)**2 for a,b in zip(wet[0], dry[0])) / len(dry[0]))
    report = {
        "source": "synthetic deterministic stereo 120 BPM drum loop; no sample assets",
        "sample_rate": rate,
        "duration_seconds": 4,
        "frames": len(source[0]),
        "control_path": "VST parameter 1 Gate + parameter 53 Dry/Wet",
        "repeat_active_at_end": active_at_end,
        "peak_abs_output": max(max(abs(x) for x in channel) for channel in wet),
        "max_left_difference_from_dry": difference,
        "rms_left_difference_from_dry": rms_difference,
        "dry_wav_sha256": hashlib.sha256(path_dry.read_bytes()).hexdigest(),
        "repeat_wav_sha256": hashlib.sha256(path_wet.read_bytes()).hexdigest(),
        "files": [str(path_dry), str(path_wet)],
        "hardware_audio_validated": False,
    }
    (OUT / "audio-demo-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if difference < .05 or rms_difference < .005 or not active_at_end or report["peak_abs_output"] >= 1:
        raise SystemExit("Repeat render did not produce a clear signal difference")


if __name__ == "__main__":
    main()
