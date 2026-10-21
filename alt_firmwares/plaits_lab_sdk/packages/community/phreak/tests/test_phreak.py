#!/usr/bin/env python3
# Copyright 2026 Matt Policastro.
# SPDX-License-Identifier: MIT
"""Package gates; generated build output lives only in temporary directories."""

import importlib.util
from array import array
from decimal import Decimal
import json
import math
import os
from pathlib import Path
import shlex
import struct
import subprocess
import sys
import tempfile
import unittest
import wave


PACKAGE = Path(__file__).resolve().parents[1]
SDK_DIR = PACKAGE.parents[2]
REPO_ROOT = SDK_DIR.parents[1]

# Loading the SDK must not leave bytecode in the source tree.
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("plaits_lab", SDK_DIR / "plaits_lab.py")
SDK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SDK)


# Independent references in normative index order; do not derive from C++ data.
TONE_CASES = [
    ("phreak-tones/north-american-tone-table/dial-tone", "dial", (350, 440)),
    ("phreak-tones/north-american-tone-table/key-1", "key-1", (697, 1209)),
    ("phreak-tones/north-american-tone-table/key-2", "key-2", (697, 1336)),
    ("phreak-tones/north-american-tone-table/key-3", "key-3", (697, 1477)),
    ("phreak-tones/north-american-tone-table/key-4", "key-4", (770, 1209)),
    ("phreak-tones/north-american-tone-table/key-5", "key-5", (770, 1336)),
    ("phreak-tones/north-american-tone-table/key-6", "key-6", (770, 1477)),
    ("phreak-tones/north-american-tone-table/key-7", "key-7", (852, 1209)),
    ("phreak-tones/north-american-tone-table/key-8", "key-8", (852, 1336)),
    ("phreak-tones/north-american-tone-table/key-9", "key-9", (852, 1477)),
    ("phreak-tones/north-american-tone-table/key-0", "key-0", (941, 1336)),
    ("phreak-tones/north-american-tone-table/hash-key", "hash", (941, 1477)),
    ("phreak-tones/north-american-tone-table/star-key", "star", (941, 1209)),
    ("phreak-tones/north-american-tone-table/busy-tone", "busy", (480, 620)),
    ("phreak-tones/north-american-tone-table/ringback-tone", "ring", (440, 480)),
    ("phreak-tones/north-american-tone-table/key-a", "key-a", (697, 1633)),
    ("phreak-tones/north-american-tone-table/key-b", "key-b", (770, 1633)),
    ("phreak-tones/north-american-tone-table/key-c", "key-c", (852, 1633)),
    ("phreak-tones/north-american-tone-table/key-d", "key-d", (941, 1633)),
    ("phreak-tones/north-american-tone-table/fsk-space", "fsk-space", (2200,)),
    ("phreak-tones/north-american-tone-table/fsk-mark", "fsk-mark", (1200,)),
]

# Independent task 6.2 settings: seconds, MIDI note, trigger Hz, HARMONICS,
# TIMBRE. Scalars must be repeated at both SDK range endpoints.
ADDITIONAL_AUDITIONS = {
    "keypress": (3, 60, 2, 11 / 42, 0),
    "busy-keypress": (3, 60, 2, 27 / 42, 0),
    "ring-keypress": (3, 60, 2, 29 / 42, 0),
    "dial-low": (2, 48, 0, 1 / 42, 0),
    "dial-high": (2, 72, 0, 1 / 42, 0),
    "dtmf-high": (2, 72, 0, 11 / 42, 0),
    "fsk-high": (2, 72, 0, 39 / 42, 0),
    "band-low": (2, 24, 0, 41 / 42, 1 / 3),
    "band-high": (2, 84, 0, 39 / 42, 1 / 3),
    "band-pass": (2, 60, 0, 41 / 42, 1 / 3),
    "saturated": (2, 60, 0, 41 / 42, 2 / 3),
    "crushed": (2, 60, 0, 41 / 42, 1),
    "bad-line-sweep": (6, 60, 0, 11 / 42, [0, 1]),
    "bad-line-return": (6, 60, 0, 11 / 42, [1, 0]),
    "selection-sweep": (21, 60, 0, [0, 1], 0),
}


def float32(value):
    """Round each operation as the engine's float control arithmetic does."""
    return struct.unpack("=f", struct.pack("=f", value))[0]


def adjacent_float32(value, direction):
    """Adjacent positive float, for the internal selection thresholds."""
    bits = struct.unpack("=I", struct.pack("=f", value))[0]
    return struct.unpack("=f", struct.pack("=I", bits + direction))[0]


def reference_fade(outgoing, incoming):
    """Independent 5 ms mixture of separately rendered, free-running voices."""
    assert len(outgoing) == len(incoming) == 240
    return [(1 - n / 239) * outgoing[n] + (n / 239) * incoming[n]
            for n in range(240)]


def rms(samples):
    return math.sqrt(sum(x * x for x in samples) / len(samples))


def sine_fit(samples, frequencies):
    """Least squares at reference Hz, allowing arbitrary component phases.

    Solve the small Gram system so noninteger-cycle windows do not leak one
    component into another. Residual includes ALL unexplained signal, not only
    selected FFT bins; a wrong frequency, extra oscillator or harmonics fails.
    """
    basis = [[function(2 * math.pi * hz * n / 48000)
              for n in range(len(samples))]
             for hz in frequencies for function in (math.sin, math.cos)]
    def dot(a, b):
        return sum(x * y for x, y in zip(a, b))
    matrix = [[dot(a, b) for b in basis] + [dot(a, samples)] for a in basis]
    for i in range(len(basis)):
        pivot = matrix[i][i]
        matrix[i] = [value / pivot for value in matrix[i]]
        for j in range(len(basis)):
            if i != j:
                factor = matrix[j][i]
                matrix[j] = [a - factor * b for a, b in zip(matrix[j], matrix[i])]
    weights = [row[-1] for row in matrix]
    amplitudes = [math.hypot(weights[i], weights[i + 1])
                  for i in range(0, len(weights), 2)]
    residual = math.sqrt(sum(
        (sample - sum(w * b[n] for w, b in zip(weights, basis))) ** 2
        for n, sample in enumerate(samples)) / len(samples))
    return amplitudes, residual


class ToneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = tempfile.TemporaryDirectory(prefix="phreak-tones-")
        cls.addClassCleanup(directory.cleanup)
        cls.directory = Path(directory.name)
        cls.driver = cls.directory / ("render_cases.exe" if os.name == "nt" else "render_cases")
        compiler = shlex.split(os.environ.get("CXX", "c++"))
        # The shared resource file has a zero-length array extension. Compile it
        # separately; package code and the driver retain strict C++98 checks.
        resources = cls.directory / "resources.o"
        subprocess.run([
            *compiler, "-std=c++98", "-DTEST", "-O2", "-I", str(REPO_ROOT),
            "-c", str(REPO_ROOT / "plaits/resources.cc"), "-o", str(resources),
        ], check=True, cwd=REPO_ROOT)
        command = [
            *compiler,
            "-std=c++98", "-pedantic-errors", "-DTEST", "-D_USE_MATH_DEFINES",
            "-O2", "-Wall", "-Werror", "-isystem", str(REPO_ROOT),
            "-I", str(PACKAGE / "src"), str(PACKAGE / "tests/render_cases.cc"),
            str(PACKAGE / "src/phreak_engine.cc"),
            str(REPO_ROOT / "stmlib/dsp/units.cc"),
            str(resources), "-o", str(cls.driver),
        ]
        subprocess.run(command, check=True, cwd=REPO_ROOT)

    def render(self, harmonics, seconds):
        output = self.directory / "samples.f32"
        subprocess.run([str(self.driver), str(harmonics), str(seconds), str(output)],
                       check=True)
        return self.read_aux(output, int(seconds * 48000))

    def render_steps(self, harmonics, seconds=0.020):
        output = self.directory / "steps.f32"
        subprocess.run([str(self.driver), "steps", str(seconds), str(output),
                        *map(str, harmonics)], check=True)
        frames = int(seconds * 48000)
        count = sum(value != "reset" for value in harmonics)
        aux = self.read_aux(output, count * frames)
        return [aux[start:start + frames] for start in range(0, len(aux), frames)]

    def render_timeline(self, events, block_size=12, note=60, main_peak=0.500001):
        """Sample-timed (HARMONICS, frames), reset and trigger=STATE events."""
        output = self.directory / "timeline.f32"
        arguments = [f"note={note}"]
        frames = 0
        for event in events:
            if isinstance(event, str):
                arguments.append(event)
            else:
                harmonics, count = event
                arguments.extend((str(harmonics), str(count)))
                frames += count
        subprocess.run([str(self.driver), "timeline", str(block_size), str(output),
                        *arguments], check=True)
        return self.read_channels(output, frames, main_peak)

    def read_channels(self, output, frames, main_peak=0.500001):
        samples = array("f")
        samples.frombytes(output.read_bytes())
        self.assertEqual(len(samples), 2 * frames)
        self.assertTrue(all(math.isfinite(x) and abs(x) <= main_peak for x in samples[0::2]))
        self.assertTrue(all(math.isfinite(x) and abs(x) <= 0.500001 for x in samples[1::2]))
        return samples[0::2], samples[1::2]

    def read_aux(self, output, frames):
        return self.read_channels(output, frames)[1]

    def assert_reference(self, channels, reference):
        for label, samples in zip(("MAIN", "AUX"), channels):
            with self.subTest(channel=label):
                self.assertEqual(len(samples), len(reference))
                self.assertLessEqual(max(abs(a - b) for a, b in zip(samples, reference)),
                                     1e-6)

    def assert_tone(self, samples, index, ratio=1):
        frequencies = tuple(hz * ratio for hz in TONE_CASES[index][2])
        amplitudes, residual = sine_fit(samples, frequencies)
        level = 0.25 if len(frequencies) == 2 else 0.5
        for amplitude in amplitudes:
            self.assertAlmostEqual(amplitude, level, delta=0.001)
        self.assertLessEqual(20 * math.log10(max(amplitudes) / min(amplitudes)), 0.5)
        self.assertLess(residual / (min(amplitudes) / math.sqrt(2)), 0.01)

    def assert_clean_channels(self, channels):
        main, aux = channels
        self.assertGreater(rms(aux), 0.01)  # Silence cannot satisfy this gate.
        self.assertLessEqual(max(abs(m - a) for m, a in zip(main, aux)), 1e-6)

    def render_treatment(self, events, **kwargs):
        # Filter onset can overshoot the oscillator's 0.5 peak. The bad-line
        # contract permits MAIN up to full scale; AUX and all pre-existing
        # callers keep the original 0.500001 bound.
        return self.render_timeline(events, main_peak=1.0, **kwargs)

    def test_bad_line_true_clean_endpoint(self):
        """phreak-bad-line/clean-endpoint-and-band-limitation/true-clean-endpoint"""
        h = 41 / 42
        clean = self.render_treatment([(h, 192000)])
        recovered = self.render_treatment([
            "timbre=1", (h, 96000), "timbre=0", (h, 96000),
        ])
        # Treatment must actually have run before testing recovery, and AUX
        # must match the untreated reference for the entire control history.
        self.assertGreater(rms([m - a for m, a in
                                zip(recovered[0][960:96000], recovered[1][960:96000])]),
                           0.05)
        self.assertEqual(recovered[1], clean[1])
        for label, channels in (("reset", [x[:96000] for x in clean]),
                                ("recovery", [x[96000:] for x in recovered])):
            with self.subTest(history=label):
                steady = [x[960:] for x in channels]
                self.assert_clean_channels(steady)
                # Total non-sine residual rejects colour, quantization, holds,
                # extra oscillators and harmonics, not just a few selected bins.
                for samples in steady:
                    self.assert_tone(samples, 20)

        # Reset must discard treatment mix/filter history as well as voices.
        for timbre in (0, 1 / 3, 2 / 3, 1):
            with self.subTest(reset_timbre=timbre):
                fresh = self.render_treatment([f"timbre={timbre}", (h, 96000)])
                reset = self.render_treatment([
                    "timbre=1", (h, 4813), "reset",
                    f"timbre={timbre}", (h, 96000),
                ])
                for actual, expected in zip(reset, fresh):
                    self.assertEqual(actual[4813:], expected)

    def test_bad_line_crushed_endpoint(self):
        """phreak-bad-line/upper-range-digital-reduction/crushed-endpoint"""
        h = 41 / 42
        saturated, clean = self.render_treatment([f"timbre={2 / 3}", (h, 96000)])
        baseline = None
        for block in (1, 7, 12, 24):
            with self.subTest(block=block):
                main, aux = self.render_treatment(["timbre=1", (h, 96000)],
                                                   block_size=block)
                self.assertEqual(aux, clean)
                self.assert_tone(aux[960:], 20)
                steady = main[960:]
                self.assertLessEqual(max(abs(x - round(x * 31 / 2) * 2 / 31)
                                         for x in steady), 1 / 32768)
                changes = [n for n in range(961, len(main)) if main[n] != main[n - 1]]
                self.assertGreater(len(changes), 5000)  # Reject frozen output.
                self.assertEqual({n % 8 for n in changes}, {0})
                for n in range(960, len(main), 8):
                    self.assertEqual(len(set(main[n:n + 8])), 1)
                    # Correct grid value comes from the filtered/saturated input
                    # at the update, not a reduced clean tone or a moving average.
                    expected = round(saturated[n] * 31 / 2) * 2 / 31
                    self.assertAlmostEqual(main[n], expected, delta=1e-6)
                if baseline is not None:
                    self.assertEqual(main, baseline)
                baseline = main
        self.assertTrue(all(len(set(saturated[n:n + 8])) > 1
                            for n in range(960, 96000, 8)))
        # 6 kHz update images around the 1200 Hz tone are absent from the
        # saturation-only comparison; these are not just its odd harmonics.
        crushed_images, _ = sine_fit(baseline[960:], (1200, 4800, 7200))
        saturated_images, _ = sine_fit(saturated[960:], (1200, 4800, 7200))
        for image, reference in zip(crushed_images[1:], saturated_images[1:]):
            self.assertGreater(image, 0.01)
            self.assertGreater(image, 10 * reference)

    def test_bad_line_signed_quantization(self):
        """phreak-bad-line/upper-range-digital-reduction/crushed-endpoint"""
        rows = subprocess.check_output([str(self.driver), "quantization-grid"],
                                       text=True).splitlines()
        self.assertEqual(len(rows), 8 * 4801)
        values = {}
        for row in rows:
            bits, x, y = map(float, row.split())
            step = 2 / (2 ** int(bits) - 1)
            magnitude = math.floor(min(abs(x), 1) / step + 0.5) * step
            expected = math.copysign(min(magnitude, 1), x)
            self.assertAlmostEqual(y, expected, delta=1e-6)
            self.assertLessEqual(abs(y), 1)
            values[bits, x] = y
        for (bits, x), y in values.items():
            self.assertEqual(y, -values[bits, -x])

    def test_bad_line_reduction_mix_hold_and_reset(self):
        """phreak-bad-line/upper-range-digital-reduction/crushed-endpoint
        phreak-bad-line/clean-endpoint-and-band-limitation/true-clean-endpoint
        """
        h = 41 / 42
        # Visit every resolution, then interrupt ramps and reverse to the exact
        # saturation-only endpoint. Event positions do not align to hold clocks.
        amounts = [(i + 0.5) / 7 for i in range(7)] + [1]
        segments = [(2 / 3, 1200)] + [((2 + v) / 3, 481) for v in amounts]
        segments += [(1, 73), (0.8, 317), (1, 480), (2 / 3, 480),
                     (1, 29), (2 / 3, 400)]
        frames = sum(count for _, count in segments)
        saturated, clean = self.render_treatment([f"timbre={2 / 3}", (h, frames)])
        expected, events = [], []
        position, mix, target, held, remaining, length = 0, 0.0, 0.0, 0.0, 0, 1
        for timbre, count in segments:
            events.extend([f"timbre={timbre}", (h, count)])
            next_target = max(0, min(1, float32(float32(3 * float32(timbre)) - 2)))
            changed = next_target != target
            target = next_target
            resolution = int(float32(7 * target))
            next_length = 1 + resolution
            if next_length != length:
                remaining = 0
            length = next_length
            step = 2 / (2 ** (12 - resolution) - 1)
            start = mix
            for n in range(count):
                if changed:
                    mix = start + (target - start) * min((n + 1) / 240, 1)
                x = saturated[position]
                if mix == 0:
                    remaining, held = 0, 0.0
                else:
                    if remaining == 0:
                        held = math.copysign(math.floor(abs(x) / step + 0.5) * step, x)
                        remaining = length
                    remaining -= 1
                expected.append(x + mix * (held - x))
                position += 1
        baseline = None
        for block in (1, 7, 12, 24):
            with self.subTest(block=block):
                main, aux = self.render_treatment(events, block_size=block)
                self.assertEqual(aux, clean)
                self.assertLessEqual(max(abs(a - b) for a, b in zip(main, expected)), 1e-6)
                self.assertEqual(main[-160:], saturated[-160:])
                if baseline is not None:
                    self.assertEqual(main, baseline)
                baseline = main
                # Reset while a hold and mix ramp are both unfinished.
                fresh = self.render_treatment(["timbre=1", (h, 1200)], block_size=block)
                reset = self.render_treatment([
                    "timbre=0.9", (h, 73), "reset", "timbre=1", (h, 1200),
                ], block_size=block)
                for actual, reference in zip(reset, fresh):
                    self.assertEqual(actual[73:], reference)

    def assert_treated_burst_schedule(self, channels):
        # Treatment can change levels/spectra, but never the shared deadline.
        for samples in channels:
            for edge in range(0, len(samples), 24000):
                burst = samples[edge:edge + 24000]
                threshold = 0.1 * rms(burst[960:4320])
                self.assertGreater(threshold, 0.005)
                active = [n for n in range(0, len(burst), 240)
                          if rms(burst[n:n + 240]) > threshold]
                self.assertEqual(active[0], 0)
                self.assertAlmostEqual((active[-1] + 240) / 48000, 0.100, delta=0.010)
                self.assertEqual(active, list(range(0, active[-1] + 240, 240)))
                for n in range(5280, len(burst), 240):
                    self.assertLess(rms(burst[n:n + 240]), 1e-4)

    def test_bad_line_aux_independence_at_stage_checkpoints(self):
        """phreak-pitch-outputs/clean-and-processed-routing/aux-independence"""
        h = 11 / 42
        for patched in (False, True):
            events = []
            for _ in range(4):
                events.extend(["trigger=rise" if patched else "trigger=unpatched",
                               (h, 6000),
                               "trigger=low" if patched else "trigger=unpatched",
                               (h, 18000)])
            reference, outputs = None, []
            for timbre in (0, 1 / 3, 2 / 3, 1):
                with self.subTest(patched=patched, timbre=timbre):
                    main, aux = self.render_treatment([f"timbre={timbre}"] + events)
                    if reference is None:
                        reference = aux
                        self.assert_clean_channels((main, aux))
                    self.assertEqual(aux, reference)
                    if patched:
                        self.assert_bursts((aux,), 5)
                        self.assert_treated_burst_schedule((main, aux))
                    else:
                        for start in range(960, 96000 - 4800, 4800):
                            self.assert_tone(aux[start:start + 4800], 5)
                    for previous in outputs:
                        self.assertGreater(rms([a - b for a, b in
                                                zip(main, previous)]), 0.01)
                    outputs.append(main)

    def test_bad_line_ordered_sweep_and_recovery(self):
        """phreak-bad-line/stable-treatment-sweep/ordered-sweep-and-recovery
        phreak-pitch-outputs/clean-and-processed-routing/aux-independence
        phreak-bad-line/clean-endpoint-and-band-limitation/true-clean-endpoint
        """
        frames = 12 * 48000 + 4800
        output = self.directory / "sweep.f32"
        for mode in ("unpatched", "triggered"):
            channels = []
            for control in ("clean", "sweep"):
                subprocess.run([str(self.driver), "treatment-sweep", control, mode,
                                str(output)], check=True)
                channels.append(self.read_channels(output, frames, main_peak=1.0))
            clean, (main, aux) = channels
            self.assertEqual(aux, clean[1])
            self.assertLessEqual(max(abs(m - a) for m, a in zip(main[-960:], aux[-960:])),
                                 1 / 32768)
            if mode == "triggered":
                self.assert_treated_burst_schedule((main, aux))
                self.assert_bursts((aux[:12 * 48000],), 5)
                continue
            # AUX has the pair throughout both legs, including the return tail.
            for start in range(960, frames - 4800, 4800):
                self.assert_tone(aux[start:start + 4800], 5)
            filtered, _ = self.render_treatment([
                f"timbre={1 / 3}", (11 / 42, 12 * 48000), (11 / 42, 4800),
            ])
            # Reconstruct the continuous stage amounts from the documented 5 ms
            # ramps and block-timed control sweep, independently of DSP state.
            mixes = [array("f"), array("f"), array("f")]
            current, targets, starts, ages = [0.0] * 3, [0.0] * 3, [0.0] * 3, [240] * 3
            for block in range(0, frames, 12):
                t = (float32(block / (288000 - 12)) if block < 288000
                     else float32(1 - float32((block - 288000) / (288000 - 12)))
                     if block < 576000 else 0)
                for stage in range(3):
                    target = max(0, min(1, float32(float32(3 * t) - stage)))
                    if target != targets[stage]:
                        starts[stage], targets[stage], ages[stage] = current[stage], target, 0
                    for _ in range(12):
                        ages[stage] = min(240, ages[stage] + 1)
                        current[stage] = starts[stage] + (targets[stage] - starts[stage]) * ages[stage] / 240
                        mixes[stage].append(current[stage])
            # Interior windows in each third on both legs establish the order,
            # not merely a difference between clean and the crushed endpoint.
            for seconds in (0.5, 1.5, 2.5, 3.5, 4.5, 5.5,
                            6.5, 7.5, 8.5, 9.5, 10.5, 11.5):
                start = int(seconds * 48000)
                recovered_hold = []
                for n in range(start, start + 2400):
                    band, saturation, reduction = (mix[n] for mix in mixes)
                    x = aux[n] + band * (filtered[n] - aux[n])
                    driven = (1 + 7 * saturation) * x
                    x += saturation * (0.8 * driven / (1 + abs(driven)) - x)
                    if reduction == 0:
                        self.assertAlmostEqual(main[n], x, delta=1e-5)
                    else:
                        recovered_hold.append((main[n] - (1 - reduction) * x) / reduction)
                if recovered_hold:
                    # These windows stay within one discrete resolution step.
                    v = 3 * (seconds / 6 if seconds < 6 else 2 - seconds / 6) - 2
                    resolution = math.floor(7 * v)
                    step, hold = 2 / (2 ** (12 - resolution) - 1), 1 + resolution
                    levels = [round(x / step) for x in recovered_hold]
                    self.assertLess(max(abs(x - k * step) for x, k in
                                        zip(recovered_hold, levels)), 1 / 32768)
                    changes = [n for n in range(1, len(levels)) if levels[n] != levels[n - 1]]
                    self.assertGreater(len(changes), 100)
                    self.assertEqual(len({n % hold for n in changes}), 1)

    def test_bad_line_telephone_bandpass(self):
        """phreak-bad-line/clean-endpoint-and-band-limitation/telephone-band-pass"""
        for index, note, hz in ((20, 24, 150), (20, 60, 1200), (19, 84, 8800)):
            with self.subTest(hz=hz):
                h = (index + 0.5) / 21
                main, aux = self.render_treatment([
                    f"timbre={1 / 3}", (h, 96000),
                ], note=note)
                clean = self.render_treatment([(h, 96000)], note=note)
                self.assertEqual(aux, clean[1])
                self.assert_tone(aux[960:], index, 2 ** ((note - 60) / 12))
                wet_amplitude, residual = sine_fit(main[960:], (hz,))
                dry_amplitude, _ = sine_fit(aux[960:], (hz,))
                gain_db = 20 * math.log10(wet_amplitude[0] / dry_amplitude[0])
                if hz == 1200:
                    self.assertGreater(gain_db, -3)
                    self.assertLessEqual(gain_db, 0.1)
                else:
                    self.assertLessEqual(gain_db, -10)
                self.assertLess(residual / (wet_amplitude[0] / math.sqrt(2)), 0.01)

    def test_bad_line_helper_cutoffs(self):
        """phreak-bad-line/clean-endpoint-and-band-limitation/telephone-band-pass"""
        # Independent helper sine sweep: locate BOTH edges relative to the
        # measured peak, rather than assuming unity gain or testing constants.
        frequencies = list(range(100, 5001, 20))
        output = self.directory / "bandpass.f32"
        subprocess.run([str(self.driver), "bandpass", str(output),
                        *map(str, frequencies)], check=True)
        wet, dry = self.read_channels(output, len(frequencies) * 12000)
        gains = []
        for i in range(len(frequencies)):
            # 50 ms settle, then 200 ms containing whole sine periods.
            start, end = i * 12000 + 2400, (i + 1) * 12000
            gains.append(20 * math.log10(rms(wet[start:end]) / rms(dry[start:end])))
        peak = max(gains)
        self.assertGreater(peak, -0.2)
        threshold = peak - 3
        crossings = []
        for i in range(1, len(gains)):
            a, b = gains[i - 1], gains[i]
            if (a < threshold) != (b < threshold):
                fraction = (threshold - a) / (b - a)
                crossings.append(frequencies[i - 1] + 20 * fraction)
        self.assertEqual(len(crossings), 2)
        self.assertAlmostEqual(crossings[0], 300, delta=30)
        self.assertAlmostEqual(crossings[1], 3400, delta=340)

    def test_bad_line_progressive_mix_and_bypass_ramp(self):
        """phreak-bad-line/clean-endpoint-and-band-limitation/true-clean-endpoint
        phreak-bad-line/clean-endpoint-and-band-limitation/telephone-band-pass
        """
        h = 41 / 42
        wet, dry = self.render_treatment([f"timbre={1 / 3}", (h, 9600)])
        for timbre in (1 / 12, 1 / 6, 1 / 4):
            with self.subTest(timbre=timbre):
                main, aux = self.render_treatment([f"timbre={timbre}", (h, 9600)])
                self.assertEqual(aux, dry)
                expected = [d + 3 * timbre * (w - d)
                            for w, d in zip(wet[960:], dry[960:])]
                self.assertLessEqual(max(abs(m - e) for m, e in
                                         zip(main[960:], expected)), 1e-6)
        for block in (1, 7, 12, 24):
            with self.subTest(block=block):
                main, aux = self.render_treatment([
                    f"timbre={1 / 3}", (h, 4800), "timbre=0", (h, 4800),
                ], block_size=block)
                self.assertEqual(aux, dry)
                expected = [d + (1 - (i + 1) / 240) * (w - d)
                            for i, (w, d) in enumerate(zip(
                                wet[4800:5040], dry[4800:5040]))]
                self.assertLessEqual(max(abs(m - e) for m, e in
                                         zip(main[4800:5040], expected)), 1e-6)
                self.assertEqual(main[5040:], aux[5040:])
        # Clamp out-of-range controls before computing the band-pass mix.
        maximum, _ = self.render_treatment(["timbre=1", (h, 9600)])
        for timbre, expected in ((-1, dry), (2, maximum)):
            main, aux = self.render_treatment([f"timbre={timbre}", (h, 9600)])
            self.assertEqual(main, expected)
            self.assertEqual(aux, dry)

    def test_soft_saturation_curve(self):
        """phreak-bad-line/progressive-soft-saturation/saturation-after-filtering"""
        result = subprocess.run([str(self.driver), "saturation-curve"],
                                check=True, text=True, capture_output=True)
        values = {}
        for row in result.stdout.splitlines():
            x, drive, y = map(float, row.split())
            self.assertTrue(math.isfinite(y))
            self.assertLessEqual(abs(y), 0.8)
            expected = 0.8 * (drive * x) / (1 + abs(drive * x))
            self.assertAlmostEqual(y, expected, delta=1e-6)
            values[x, drive] = y
        self.assertEqual(len(values), 403 * 5)
        for (x, drive), y in values.items():
            self.assertAlmostEqual(y, -values[-x, drive], delta=1e-6)
        for drive in (1, 2.75, 4.5, 6.25, 8):
            self.assertEqual(values[0, drive], 0)
            positive = sorted((x, y) for (x, d), y in values.items()
                              if d == drive and x >= 0)
            self.assertTrue(all(a[1] < b[1] for a, b in zip(positive, positive[1:])))

    def test_saturation_harmonics_dc_and_level(self):
        """phreak-bad-line/progressive-soft-saturation/saturation-after-filtering"""
        h = 41 / 42
        clean = self.render_treatment([(h, 96000)])
        ratios = []
        for timbre in (1 / 3, 2 / 3):
            with self.subTest(timbre=timbre):
                main, aux = self.render_treatment([f"timbre={timbre}", (h, 96000)])
                self.assertEqual(aux, clean[1])
                self.assert_tone(aux[960:], 20)
                steady = main[960:]
                self.assertLess(abs(sum(steady) / len(steady)), 0.01)
                self.assertLess(max(abs(x) for x in main), 1.0)
                amplitudes, _ = sine_fit(steady, (1200, 2400, 3600))
                self.assertGreater(amplitudes[0], 0.3)  # Fundamental retained.
                self.assertLess(amplitudes[1] / amplitudes[0], 0.01)
                ratios.append(amplitudes[2] / amplitudes[0])
                if timbre == 2 / 3:
                    self.assertLess(max(abs(x) for x in steady), 0.8)
                    # Every eight-sample window changes internally: no upper-
                    # third hold or quantization is part of this stage.
                    self.assertTrue(all(len(set(steady[n:n + 8])) > 1
                                        for n in range(0, len(steady) - 7, 8)))
        self.assertGreaterEqual(20 * math.log10(ratios[1] / max(ratios[0], 1e-12)), 6)

    def test_saturation_filter_before_drive_reference(self):
        """phreak-bad-line/progressive-soft-saturation/saturation-after-filtering"""
        for timbre in (5 / 12, 0.5, 7 / 12, 2 / 3):
            with self.subTest(timbre=timbre):
                main, _ = self.render_treatment([
                    f"timbre={timbre}", (41 / 42, 96000),
                ])
                output = self.directory / "saturation-reference.f32"
                subprocess.run([str(self.driver), "saturation-reference", str(timbre),
                                str(self.directory / "timeline.f32"), str(output)],
                               check=True)
                reference = array("f")
                reference.frombytes(output.read_bytes())
                self.assertEqual(len(reference), 192000)
                ordered, reversed_order = reference[0::2], reference[1::2]
                self.assertLessEqual(max(abs(m - r) for m, r in
                                         zip(main[960:], ordered[960:])), 1e-6)
                # Ensure the oracle discriminates saturation before filtering.
                self.assertGreater(rms([a - b for a, b in
                                        zip(ordered[960:], reversed_order[960:])]), 0.001)

    def test_saturation_mix_and_drive_smoothing(self):
        """phreak-bad-line/progressive-soft-saturation/saturation-after-filtering"""
        h = 41 / 42
        # Include reversals during a ramp, intermediate/full amounts, repeated
        # control blocks, and exact recovery to a purely filtered endpoint.
        segments = [(1 / 3, 1200), (2 / 3, 73), (0.5, 317), (2 / 3, 480),
                    (1 / 3, 480), (2 / 3, 29), (1 / 3, 400)]
        frames = sum(count for _, count in segments)
        filtered, clean = self.render_treatment([f"timbre={1 / 3}", (h, frames)])
        expected, events = [], []
        position, mix = 0, 0.0
        for timbre, count in segments:
            events.extend([f"timbre={timbre}", (h, count)])
            target = max(0, min(1, float32(float32(3 * float32(timbre)) - 1)))
            start = mix
            for n in range(count):
                mix = start + (target - start) * min((n + 1) / 240, 1)
                x = filtered[position]
                driven = (1 + 7 * mix) * x
                expected.append(x + mix * (0.8 * driven / (1 + abs(driven)) - x))
                position += 1
        baseline = None
        for block in (1, 7, 12, 24):
            with self.subTest(block=block):
                main, aux = self.render_treatment(events, block_size=block)
                self.assertEqual(aux, clean)
                self.assertLessEqual(max(abs(a - b) for a, b in zip(main, expected)), 1e-6)
                self.assertEqual(main[-160:], filtered[-160:])
                if baseline is not None:
                    self.assertEqual(main, baseline)
                baseline = main
                fresh = self.render_treatment(["timbre=0.5", (h, 1200)], block_size=block)
                reset = self.render_treatment([
                    f"timbre={2 / 3}", (h, 73), "reset", "timbre=0.5", (h, 1200),
                ], block_size=block)
                for actual, reference in zip(reset, fresh):
                    self.assertEqual(actual[73:], reference)

    def test_all_entry_clean_channel_equality(self):
        """phreak-pitch-outputs/clean-and-processed-routing/clean-endpoint-equality"""
        for index in range(21):
            h = (index + 0.5) / 21
            # Ringback must include its closing AND reopening cadence edges.
            frames = 312000 if index == 14 else 96000
            with self.subTest(index=index, trigger="unpatched"):
                channels = self.render_timeline([(h, frames)])
                self.assert_clean_channels(channels)
                if index in (13, 14):
                    self.assert_cadence(channels[1], 0.5 if index == 13 else 2,
                                        0.5 if index == 13 else 4)
            events = []
            for _ in range(4):
                events.extend(["trigger=rise", (h, 6000),
                               "trigger=low", (h, 18000)])
            with self.subTest(index=index, trigger="2 Hz"):
                channels = self.render_timeline(events)
                self.assert_clean_channels(channels)
                # Check that all four LPG-shaped bursts actually occurred,
                # including the single-component FSK entries.
                for edge in range(0, 96000, 24000):
                    self.assertGreater(rms(channels[1][edge + 960:edge + 4320]), 0.1)
                    self.assertLess(max(abs(x) for x in
                                        channels[1][edge + 5280:edge + 24000]), 1e-4)

    def test_clean_channel_equality_during_all_entry_crossfades(self):
        """phreak-pitch-outputs/clean-and-processed-routing/clean-endpoint-equality"""
        for index in range(21):
            previous = ((index - 1) % 21 + 0.5) / 21
            h = (index + 0.5) / 21
            for patched in (False, True):
                with self.subTest(index=index, patched=patched):
                    # Change at 50 ms during the keypress hold. Repeated
                    # periods exercise both fade directions at 2 Hz.
                    events = []
                    for _ in range(2):
                        events.extend([
                            "trigger=rise" if patched else "trigger=unpatched",
                            (previous, 2400), (h, 3600),
                            "trigger=low" if patched else "trigger=unpatched",
                            (h, 18000),
                        ])
                    channels = self.render_timeline(events)
                    self.assert_clean_channels(channels)
                    for edge in (2400, 26400):
                        self.assertGreater(rms(channels[1][edge:edge + 240]), 0.1)

    def test_neutral_control_sweeps(self):
        """phreak-pitch-outputs/neutral-unused-controls/neutral-control-sweeps"""
        output = self.directory / "neutral.f32"
        for mode in ("unpatched", "triggered"):
            baseline = None
            for control in ("baseline", "morph", "macro"):
                with self.subTest(mode=mode, control=control):
                    subprocess.run([str(self.driver), "neutral", control, mode,
                                    str(output)], check=True)
                    # At TIMBRE 0.5 the specified drive can exceed the clean
                    # oscillator's 0.5 peak. Keep the full-scale MAIN bound,
                    # clean AUX bound, and unchanged neutrality comparisons.
                    channels = self.read_channels(output, 96000, main_peak=1.0)
                    if baseline is None:
                        baseline = channels
                        for samples in baseline:
                            self.assertGreater(rms(samples), 0.01)
                    else:
                        # Compare corresponding paths, allowing MAIN and AUX
                        # to differ once TIMBRE treatment is implemented.
                        for samples, reference in zip(channels, baseline):
                            self.assertLessEqual(max(abs(a - b) for a, b in
                                                     zip(samples, reference)), 1e-6)

    def test_octave_transposition(self):
        """phreak-pitch-outputs/common-pitch-ratio/octave-transposition"""
        for note, ratio in ((48, 0.5), (60, 1), (72, 2)):
            with self.subTest(note=note):
                channels = self.render_timeline([(1 / 42, 24000)], note=note)
                for samples in channels:
                    self.assert_tone(samples[960:], 0, ratio)

    def test_dtmf_and_fsk_transposition(self):
        """phreak-pitch-outputs/common-pitch-ratio/dtmf-and-fsk-transposition"""
        for index, note, ratio in ((5, 72, 2), (19, 72, 2), (20, 48, 0.5),
                                   (5, 60.5, 2 ** (0.5 / 12))):
            with self.subTest(index=index, note=note):
                channels = self.render_timeline([((index + 0.5) / 21, 24000)], note=note)
                for samples in channels:
                    # The full residual also rejects extra FSK components and
                    # independent quantization of either DTMF frequency.
                    self.assert_tone(samples[960:], index, ratio)

    def test_high_pitch_ceiling_preserves_pairs(self):
        """phreak-pitch-outputs/common-pitch-ratio/high-pitch-ceiling-preserves-pairs"""
        for index, note, ratio in ((18, 120, 21600 / 1633),
                                   (18, 127, 21600 / 1633),
                                   (19, 120, 21600 / 2200),
                                   (20, 120, 21600 / 1200), (0, 0, 1 / 32)):
            with self.subTest(index=index, note=note):
                channels = self.render_timeline([((index + 0.5) / 21, 24000)], note=note)
                # read_channels checks every sample for finiteness and bounds;
                # fitting both expected Hz with <1% residual is tighter than
                # the 0.1% frequency tolerance, and rejects separate clamps.
                for samples in channels:
                    self.assert_tone(samples[960:], index, ratio)

    def test_common_ceiling_during_queued_crossfades(self):
        """phreak-pitch-outputs/common-pitch-ratio/high-pitch-ceiling-preserves-pairs"""
        def voice(frequencies):
            phases = [0.0] * len(frequencies)
            age = 0

            def render(frames, ratio):
                nonlocal age
                result = []
                for _ in range(frames):
                    for i, hz in enumerate(frequencies):
                        phases[i] = (phases[i] + hz * ratio / 48000) % 1
                    result.append(0.5 / len(frequencies) * min(age / 48, 1)
                                  * sum(math.sin(2 * math.pi * p) for p in phases))
                    age += 1
                return result
            return render

        # Independent sample timeline: an early FSK request stays pending
        # until key D's fade finishes. Then returning to dial must retain the
        # outgoing FSK ceiling until its weight reaches zero.
        dial, key_d, space = voice((350, 440)), voice((941, 1633)), voice((2200,))
        expected = dial(173, 32)
        expected += reference_fade(dial(240, 21600 / 1633), key_d(240, 21600 / 1633))
        expected += reference_fade(key_d(240, 21600 / 2200), space(240, 21600 / 2200))
        expected += space(53, 21600 / 2200)
        new_dial = voice((350, 440))
        expected += reference_fade(space(240, 21600 / 2200), new_dial(240, 21600 / 2200))
        expected += new_dial(1000, 32)
        baseline = None
        for block in (1, 7, 12, 24):
            with self.subTest(block=block):
                channels = self.render_timeline([
                    (1 / 42, 173), (37 / 42, 7), (39 / 42, 233 + 240 + 53),
                    (1 / 42, 1240),
                ], block, note=120)
                for samples in channels:
                    self.assertEqual(len(samples), len(expected))
                    # Allow float phase accumulation and sine-LUT rounding
                    # against the independent double-precision reference.
                    self.assertLess(max(abs(a - b) for a, b in zip(samples, expected)),
                                    0.0003)
                if baseline is None:
                    baseline = channels
                self.assertEqual(channels, baseline)

    def assert_cadence(self, samples, on, off):
        """10 ms RMS windows, 10% threshold; also require silent off samples."""
        on_frames, period = round(on * 48000), round((on + off) * 48000)
        threshold = 0.1 * rms(samples[960:5760])
        self.assertGreater(threshold, 0.01)
        for start in range(0, len(samples) - 479, 480):
            expected_on = start % period < on_frames
            self.assertEqual(rms(samples[start:start + 480]) > threshold,
                             expected_on, f"cadence window at sample {start}")
        for start in range(on_frames, len(samples), period):
            self.assertLessEqual(max(abs(x) for x in samples[start:start + period - on_frames]),
                                 1e-7)

    def render_helper(self, entry, seconds):
        output = self.directory / "helper.f32"
        subprocess.run([str(self.driver), "helper", str(entry), str(seconds), str(output)],
                       check=True)
        return self.read_channels(output, round(seconds * 48000))

    def render_bursts(self, index, seconds, block_size=12, reference=False):
        output = self.directory / "bursts.f32"
        subprocess.run([str(self.driver), "lpg-reference" if reference else "bursts",
                        str(index), str(seconds), str(output), str(block_size)], check=True)
        return self.read_channels(output, seconds * 48000)

    def assert_bursts(self, channels, index):
        for samples in channels:
            for edge in range(0, len(samples), 24000):
                burst = samples[edge:edge + 24000]
                # Fit the steady hold separately from the LPG's opening/release.
                amplitudes, residual = sine_fit(burst[960:4320], TONE_CASES[index][2])
                self.assertTrue(all(0.20 < a < 0.26 for a in amplitudes))
                self.assertLessEqual(20 * math.log10(max(amplitudes) / min(amplitudes)), 0.5)
                self.assertLess(residual / (min(amplitudes) / math.sqrt(2)), 0.01)
                threshold = 0.1 * rms(burst[960:4320])
                active = [n for n in range(0, 24000, 240)
                          if rms(burst[n:n + 240]) > threshold]
                self.assertEqual(active[0], 0)
                self.assertAlmostEqual((active[-1] + 240) / 48000, 0.100, delta=0.010)
                self.assertEqual(active, list(range(0, active[-1] + 240, 240)))
                for n in range(5280, 24000, 240):
                    self.assertLess(rms(burst[n:n + 240]), 1e-4)  # -80 dBFS

    def test_periodic_keypresses_through_the_lpg(self):
        """phreak-articulation/patched-keypress-bursts/periodic-keypresses-through-the-lpg"""
        reference, amplitude_only = self.render_bursts(5, 2, reference=True)
        for block_size in (1, 7, 12, 24):
            with self.subTest(block_size=block_size):
                channels = self.render_bursts(5, 2, block_size)
                self.assert_bursts(channels, 5)
                # Includes every opening/release sample, deadline and idle gap;
                # RenderAudio also requires already_enveloped on every call.
                self.assert_reference(channels, reference)
                self.assertEqual(channels[0], channels[1])
        # Ensure the oracle distinguishes the closing filter from gain alone.
        self.assertGreater(rms([a - b for a, b in
                                zip(reference[4608:4800], amplitude_only[4608:4800])]), 0.01)
        post = json.loads((PACKAGE / "plaits-engine.json").read_text())["postProcessing"]
        self.assertIs(post["alreadyEnveloped"], True)
        self.assertEqual((post["outGain"], post["auxGain"]), (1.0, 1.0))

    def test_busy_and_ring_become_keypresses(self):
        """phreak-articulation/patched-keypress-bursts/busy-and-ring-become-keypresses"""
        for index in (13, 14):
            with self.subTest(index=index):
                channels = self.render_bursts(index, 3)
                # All six edges must sound, including busy's odd half-seconds
                # and ring's 2.0/2.5 s edges in its normal off interval.
                self.assert_bursts(channels, index)
                reference, _ = self.render_bursts(index, 3, reference=True)
                self.assert_reference(channels, reference)

    def test_patched_idle_and_gate_length(self):
        """phreak-articulation/patched-keypress-bursts/patched-idle-and-gate-length"""
        idle = 7 * 48000
        baseline = None
        for block in (1, 7, 12, 24):
            for gate in (48, 48000):
                with self.subTest(block=block, gate=gate):
                    channels = self.render_timeline([
                        "trigger=low", (3 / 42, idle), "trigger=rise",
                        (3 / 42, gate), "trigger=low", (3 / 42, 8 * 48000 - gate),
                    ], block)
                    self.assertEqual(channels[0], channels[1])
                    for samples in channels:
                        self.assertEqual(max(map(abs, samples[:idle])), 0)
                        self.assertEqual(max(map(abs, samples[idle + 4800:])), 0)
                    burst = channels[1][idle:idle + 24000]
                    self.assert_bursts((burst,), 1)
                    if baseline is None:
                        baseline = burst
                    # Falling at 1 ms, staying high for 1 s, and host block
                    # partitioning must all produce identical burst samples.
                    self.assertEqual(burst, baseline)

    def test_retrigger_and_live_selection(self):
        """phreak-articulation/patched-keypress-bursts/retrigger-and-live-selection"""
        for edge in (24, 2400, 4704):  # Retrigger during attack, hold and release.
            output = self.directory / "retrigger-reference.f32"
            subprocess.run([str(self.driver), "retrigger-reference", str(edge), str(output)],
                           check=True)
            reference = self.read_aux(output, 24000)
            for block in (1, 7, 12, 24):
                with self.subTest(edge=edge, block=block):
                    # Change to key 2 at 70 ms; hold high across all later
                    # control blocks to detect accidental repeated edges.
                    events = ["trigger=rise"]
                    position = 0
                    harmonics = 3 / 42
                    for when, event in sorted(((edge, "trigger=rise"), (3360, "select"))):
                        events.append((harmonics, when - position))
                        if event == "select":
                            harmonics = 5 / 42
                        else:
                            events.append(event)
                        position = when
                    events.append((harmonics, 24000 - position))
                    channels = self.render_timeline(events, block)
                    # Exact LPG oracle checks the preserved oscillator phase,
                    # current-level reattack and 240-sample linear crossfade.
                    self.assert_reference(channels, reference)
                    for samples in channels:
                        self.assertEqual(max(map(abs, samples[edge + 4800:])), 0)
                        if edge == 2400:
                            for start, end, frequencies in (
                                (960, 3200, (697, 1209)), (3840, 6720, (697, 1336))):
                                amplitudes, residual = sine_fit(samples[start:end], frequencies)
                                self.assertTrue(all(0.20 < a < 0.26 for a in amplitudes))
                                self.assertLess(residual, 0.001)
                            threshold = 0.1 * rms(samples[960:3200])
                            active = [n for n in range(0, 24000, 240)
                                      if rms(samples[n:n + 240]) > threshold]
                            self.assertEqual(active, list(range(0, active[-1] + 240, 240)))
                            self.assertAlmostEqual((active[-1] + 240) / 48000, 0.150,
                                                   delta=0.010)

    def test_connection_transitions(self):
        """phreak-articulation/patched-keypress-bursts/connection-transitions"""
        for block in (1, 7, 12, 24):
            # The normative half-second wait and a seven-second patched wait
            # both restart the full ring cadence when the cable is removed.
            for wait in (24000, 7 * 48000):
                with self.subTest(block=block, wait=wait):
                    channels = self.render_timeline([
                        (29 / 42, 24000), "trigger=low", (29 / 42, wait),
                        "trigger=unpatched", (29 / 42, 8 * 48000),
                    ], block)
                    self.assertEqual(channels[0], channels[1])
                    for samples in channels:
                        self.assert_tone(samples[960:20160], 14)
                        self.assertLessEqual(max(map(abs, samples[24240:24000 + wait])), 1e-7)
                        resumed = samples[24000 + wait:]
                        self.assert_cadence(resumed, 2, 4)
                        self.assert_tone(resumed[960:20160], 14)
                        self.assert_tone(resumed[6 * 48000 + 960:6 * 48000 + 20160], 14)

    def test_connection_transitions_discard_old_burst(self):
        """phreak-articulation/patched-keypress-bursts/connection-transitions"""
        for block in (1, 7, 12, 24):
            channels = self.render_timeline([
                "trigger=rise", (3 / 42, 2400), "trigger=unpatched", (3 / 42, 48),
                "trigger=high", (3 / 42, 24000), "trigger=rise", (3 / 42, 24000),
            ], block)
            for samples in channels:
                self.assertGreater(rms(samples[2448 - 24:2448]), 0.01)
                self.assertEqual(max(map(abs, samples[2448:2448 + 24000])), 0)
            self.assert_bursts(tuple(s[2448 + 24000:] for s in channels), 1)

    def test_reset_clears_pending_burst_and_lpg_state(self):
        """phreak-articulation/patched-keypress-bursts/retrigger-and-live-selection
        phreak-articulation/patched-keypress-bursts/connection-transitions
        """
        for block in (1, 7, 12, 24):
            for age in (24, 2400, 4704):
                # Both voices and a pending selection are live at Reset, with
                # the contour in attack, hold or release and nonempty LPGs.
                prefix = ["trigger=rise", (3 / 42, age), (5 / 42, 7), (7 / 42, 7)]
                for state in ("low", "high", "rise", "unpatched"):
                    with self.subTest(block=block, age=age, state=state):
                        replay = [f"trigger={state}", (29 / 42, 7200),
                                  "trigger=rise", (3 / 42, 24000)]
                        fresh = self.render_timeline(replay, block)
                        reset = self.render_timeline(prefix + ["reset"] + replay, block)
                        for samples, expected in zip(reset, fresh):
                            self.assertEqual(samples[age + 14:], expected)

    def test_continuous_tone_classes(self):
        """phreak-articulation/unpatched-operation/continuous-tone-classes"""
        for index in (0, 5, 19):
            with self.subTest(index=index):
                channels = self.render_timeline([((index + 0.5) / 21, 144000)])
                self.assert_reference(channels, channels[1])
                samples = channels[1]
                self.assert_tone(samples[960:20160], index)
                threshold = 0.1 * rms(samples[960:20160])
                for start in range(960, len(samples), 480):
                    self.assertGreater(rms(samples[start:start + 480]), threshold)
                # Independent oscillator/ramp reference at startup, including
                # the first fully open sample and the end of the 1 ms ramp.
                gain = 0.5 if index == 19 else 0.25
                for n in range(96):
                    raw = gain * sum(math.sin(2 * math.pi * hz * (n + 1) / 48000)
                                     for hz in TONE_CASES[index][2])
                    self.assertAlmostEqual(samples[n], raw * min(n / 48, 1), delta=1e-5)

    def test_busy_cadence(self):
        """phreak-articulation/unpatched-operation/busy-cadence"""
        channels = self.render_timeline([(27 / 42, 4 * 48000)])
        for samples in channels:
            self.assert_cadence(samples, 0.5, 0.5)
            for start in range(0, len(samples), 48000):
                self.assert_tone(samples[start + 960:start + 20160], 13)

    def test_ringback_cadence(self):
        """phreak-articulation/unpatched-operation/ringback-cadence"""
        channels = self.render_timeline([(29 / 42, 12 * 48000)])
        for samples in channels:
            self.assert_cadence(samples, 2, 4)
            for start in (0, 6 * 48000):
                self.assert_tone(samples[start + 960:start + 20160], 14)

    def test_cadence_ramps_and_phase_through_silence(self):
        """phreak-articulation/unpatched-operation/busy-cadence
        phreak-articulation/unpatched-operation/ringback-cadence
        """
        for index, on, period, duration in ((13, 24000, 48000, 4),
                                           (14, 96000, 288000, 12)):
            with self.subTest(index=index):
                cadenced, continuous = self.render_helper(index, duration)
                self.assert_reference(self.render_timeline([((index + 0.5) / 21,
                                                            duration * 48000)]), cadenced)
                self.assertEqual(cadenced[:48], continuous[:48])
                # The continuous reference's phases never stop. Comparing every
                # sample catches phase resets/freezes as well as edge shifts.
                for n in range(48, len(cadenced)):
                    p = n % period
                    envelope = max(0, min(1, p / 48, (on - p) / 48))
                    self.assertAlmostEqual(cadenced[n], continuous[n] * envelope,
                                           delta=1e-6, msg=f"sample {n}")

    def test_cadence_restart_and_timebase(self):
        """phreak-articulation/unpatched-operation/cadence-restart-and-timebase"""
        for index, on, off, seconds in ((13, 0.5, 0.5, 4), (14, 2, 4, 12)):
            target = (index + 0.5) / 21
            for note in (48, 72):
                fresh = self.render_timeline([(target, seconds * 48000)], note=note)[1]
                self.assert_cadence(fresh, on, off)
                ratio = 2 ** ((note - 60) / 12)
                for start in range(0, len(fresh), round((on + off) * 48000)):
                    self.assert_tone(fresh[start + 960:start + 20160], index, ratio)
                # Deliberately unaligned event positions, and reset during off,
                # away from a cycle boundary. Reset must reproduce startup.
                prefix, dwell = 1733, seconds * 48000 - 1234
                restart = round(on * 48000) + 480
                dial = self.render_timeline([(1 / 42, prefix + 240)], note=note)[1]
                self.assert_tone(dial[960:], 0, ratio)
                expected = (list(dial[:prefix])
                            + reference_fade(dial[prefix:], fresh[:240])
                            + list(fresh[240:dwell]) + list(fresh[:restart]))
                for block in (1, 7, 12, 24):
                    with self.subTest(index=index, note=note, block=block):
                        channels = self.render_timeline(
                            [(1 / 42, prefix), (target, dwell), "reset", (target, restart)],
                            block, note)
                        self.assert_reference(channels, expected)

    def test_outgoing_cadence_keeps_running_during_fade(self):
        """phreak-articulation/unpatched-operation/cadence-restart-and-timebase"""
        # Cross the outgoing busy voice's closing edge, then its next opening.
        busy = self.render_timeline([(27 / 42, 48240)])[1]
        dial = self.render_timeline([(1 / 42, 480)])[1]
        for start in (24000 - 120, 48000 - 120):
            expected = (list(busy[:start])
                        + reference_fade(busy[start:start + 240], dial[:240])
                        + list(dial[240:]))
            for block in (1, 7, 12, 24):
                with self.subTest(start=start, block=block):
                    self.assert_reference(self.render_timeline(
                        [(27 / 42, start), (1 / 42, 480)], block), expected)

    def test_synthetic_locale_descriptor(self):
        """phreak-tones/locale-table-separation/table-substitution-without-a-locale-control"""
        samples, _ = self.render_helper("synthetic", 4)
        self.assert_cadence(samples, 0.25, 0.75)
        for start in range(0, len(samples), 48000):
            amplitudes, residual = sine_fit(samples[start + 960:start + 10560], (400, 450))
            for amplitude in amplitudes:
                self.assertAlmostEqual(amplitude, 0.25, delta=0.001)
            self.assertLess(residual, 0.001)
        self.test_north_american_table_metadata()
        manifest = json.loads((PACKAGE / "plaits-engine.json").read_text())
        self.assertEqual([control["id"] for control in manifest["controls"]],
                         ["harmonics", "timbre", "morph", "macro"])
        self.assertNotIn("synthetic", json.dumps(manifest).lower())
        for source in (PACKAGE / "src").iterdir():
            self.assertNotIn("synthetic", source.read_text().lower())

    def test_north_american_table_metadata(self):
        # Check labels/counts independently of rendering: an invalid count must
        # fail an assertion, without relying on undefined out-of-bounds audio.
        rows = subprocess.check_output([str(self.driver), "table"], text=True).splitlines()
        self.assertEqual(rows.pop(0), "north-america 21")
        self.assertEqual(len(rows), 21)
        for index, (scenario, label, frequencies) in enumerate(TONE_CASES):
            with self.subTest(scenario=scenario, index=index):
                row = rows[index].split()
                self.assertEqual(row[0], label)
                self.assertEqual(int(row[1]), len(frequencies))
                self.assertEqual(tuple(map(float, row[2:4])),
                                 frequencies if len(frequencies) == 2 else (*frequencies, 0))
                cadence = {13: (0.5, 0.5), 14: (2, 4)}.get(index, (0, 0))
                self.assertEqual(tuple(map(float, row[4:])), cadence)

    def test_north_american_table_and_engine_audio(self):
        for index, (scenario, label, frequencies) in enumerate(TONE_CASES):
            with self.subTest(scenario=scenario, index=index):
                duration = {13: 4, 14: 12}.get(index, 2)
                aux = self.render((index + 0.5) / 21, duration)
                # All entries are on here, including future busy/ring cadences.
                # Fitting exact reference Hz over 400 ms with this residual bound
                # constrains tuning more tightly than 1 Hz and spurs below -40 dBc.
                self.assert_tone(aux[960:20160], index)

    def test_declared_fixed_entry_auditions(self):
        """phreak-package/declared-audio-auditions/every-entry-can-be-auditioned"""
        manifest = json.loads((PACKAGE / "plaits-engine.json").read_text())
        # Decimal preserves trailing zeros: 0.500000000 must not silently
        # become 0.5 before checking the serialized centre precision.
        scenarios = json.loads((PACKAGE / manifest["scenarios"]).read_text(),
                               parse_float=Decimal)
        by_id = {scenario["id"]: scenario for scenario in scenarios}
        self.assertEqual(len(by_id), len(scenarios))
        ids = ["tone-" + {"fsk-space": "fsk-0", "fsk-mark": "fsk-1"}.get(label, label)
               for _, label, _ in TONE_CASES]
        self.assertEqual({id for id in by_id if id.startswith("tone-")}, set(ids))

        for index, id in enumerate(ids):
            with self.subTest(scenario=id):
                scenario = by_id[id]
                duration = {13: 4, 14: 12}.get(index, 2)
                self.assertEqual(set(scenario), {
                    "id", "name", "durationSeconds", "note", "triggerHz", "controls",
                })
                self.assertEqual(scenario["durationSeconds"], duration)
                self.assertEqual(scenario["note"], 60)
                self.assertEqual(scenario["triggerHz"], 0)
                controls = scenario["controls"]
                self.assertEqual(set(controls), {"harmonics", "timbre", "morph", "macro"})
                self.assertEqual(len(controls["harmonics"]), 2)
                self.assertEqual(*controls["harmonics"])
                for centre in controls["harmonics"]:
                    self.assertRegex(str(centre), r"^0\.\d{9,}$")
                    self.assertLessEqual(abs(centre - Decimal(2 * index + 1) / 42),
                                         Decimal("0.0000000005"))
                for control, value in (("timbre", 0), ("morph", 0.5), ("macro", 0.5)):
                    self.assertEqual(controls[control], [value, value])

                # Exercise the public command and its actual declared settings,
                # rather than substituting independently constructed controls.
                output = self.directory / (id + ".wav")
                result = subprocess.run([
                    sys.executable, "-B", str(SDK_DIR / "plaits_lab.py"), "render",
                    str(PACKAGE), "--scenario", id, "--output", str(output),
                ], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                with wave.open(str(output), "rb") as audio:
                    self.assertEqual(audio.getnchannels(), 2)
                    self.assertEqual(audio.getsampwidth(), 2)
                    self.assertEqual(audio.getframerate(), 48000)
                    frames = duration * 48000
                    self.assertEqual(audio.getnframes(), frames)
                    raw = audio.readframes(frames)
                self.assertEqual(len(raw), frames * 4)
                pcm = struct.unpack(f"<{frames * 2}h", raw)
                channels = [[value / 32768 for value in pcm[channel::2]]
                            for channel in (0, 1)]
                self.assert_clean_channels(channels)
                on, off = {13: (0.5, 0.5), 14: (2, 4)}.get(index, (duration, 0))
                for channel, samples in zip(("MAIN", "AUX"), channels):
                    with self.subTest(channel=channel):
                        # Zero off-time also checks every 10 ms window of the
                        # continuous entries, including both single-tone FSKs.
                        self.assert_cadence(samples, on, off)
                        for start in range(0, frames, round((on + off) * 48000)):
                            # Exclude edges, fit every on interval at exact Hz.
                            # The existing residual bound is tighter than 1 Hz
                            # and also rejects extra components above -40 dBc.
                            self.assert_tone(samples[start + 960:
                                                     start + round(on * 48000) - 960], index)

    def render_declared_additional(self, id):
        """Render the shipped JSON via the public SDK, preserving channel order."""
        output = self.directory / (id + ".wav")
        result = subprocess.run([
            sys.executable, "-B", str(SDK_DIR / "plaits_lab.py"), "render",
            str(PACKAGE), "--scenario", id, "--output", str(output),
        ], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        frames = ADDITIONAL_AUDITIONS[id][0] * 48000
        with wave.open(str(output), "rb") as audio:
            self.assertEqual((audio.getnchannels(), audio.getsampwidth(),
                              audio.getframerate(), audio.getnframes()),
                             (2, 2, 48000, frames))
            raw = audio.readframes(frames)
        self.assertEqual(len(raw), frames * 4)
        pcm = struct.unpack(f"<{frames * 2}h", raw)
        # Undo WavWriter's 32767 gain for comparisons with float references.
        channels = [array("f", (x / 32767 for x in pcm[ch::2])) for ch in (0, 1)]
        for samples in channels:
            self.assertGreater(rms(samples), 0.01)
            self.assertLess(max(abs(x) for x in samples), 1)
            self.assertLess(abs(sum(samples) / len(samples)), 0.01)
        return channels

    def assert_pcm_reference(self, samples, reference):
        self.assertEqual(len(samples), len(reference))
        self.assertLessEqual(max(abs(a - b) for a, b in zip(samples, reference)),
                             1 / 32767)

    def test_additional_audition_schema_and_settings(self):
        """phreak-package/declared-audio-auditions/articulation-pitch-and-treatment-auditions"""
        # Actual SDK schema rejects unsupported events/assertions and validates
        # all four ranges, numeric limits, unique IDs and manifest linkage.
        package = SDK.load_package(str(PACKAGE))
        by_id = {s["id"]: s for s in package["scenarios"]}
        notes = (PACKAGE / "AUDITION.md").read_text()
        for id, (seconds, note, trigger, harmonics, timbre) in ADDITIONAL_AUDITIONS.items():
            with self.subTest(scenario=id):
                self.assertIn(id, by_id)
                scenario = by_id[id]
                self.assertEqual([scenario[k] for k in ("durationSeconds", "note", "triggerHz")],
                                 [seconds, note, trigger])
                for control, target in (("harmonics", harmonics), ("timbre", timbre),
                                        ("morph", 0.5), ("macro", 0.5)):
                    expected = target if isinstance(target, list) else [target, target]
                    for actual, value in zip(scenario["controls"][control], expected):
                        self.assertAlmostEqual(actual, value, delta=5e-10)
                self.assertIn(f"| `{id}` |", notes)

    def test_declared_keypress_and_pitch_auditions(self):
        """phreak-package/declared-audio-auditions/articulation-pitch-and-treatment-auditions"""
        for id, index in (("keypress", 5), ("busy-keypress", 13), ("ring-keypress", 14)):
            with self.subTest(scenario=id):
                channels = self.render_declared_additional(id)
                self.assert_clean_channels(channels)
                self.assert_bursts(channels, index)  # All six edges and silent gaps.
                reference, _ = self.render_bursts(index, 3, reference=True)
                for samples in channels:
                    self.assert_pcm_reference(samples, reference)  # Opening/closing LPG.
        for id, index, ratio in (("dial-low", 0, 0.5), ("dial-high", 0, 2),
                                 ("dtmf-high", 5, 2), ("fsk-high", 19, 2)):
            with self.subTest(scenario=id):
                channels = self.render_declared_additional(id)
                self.assert_clean_channels(channels)
                for samples in channels:
                    self.assert_cadence(samples, 2, 0)
                    self.assert_tone(samples[960:], index, ratio)

    def test_declared_static_treatment_auditions(self):
        """phreak-package/declared-audio-auditions/articulation-pitch-and-treatment-auditions"""
        band_pass = None
        for id, index, ratio in (("band-low", 20, 0.125), ("band-high", 19, 4),
                                 ("band-pass", 20, 1)):
            with self.subTest(scenario=id):
                main, aux = self.render_declared_additional(id)
                self.assert_tone(aux[960:], index, ratio)
                hz = TONE_CASES[index][2][0] * ratio
                wet, residual = sine_fit(main[960:], (hz,))
                dry, _ = sine_fit(aux[960:], (hz,))
                gain = 20 * math.log10(wet[0] / dry[0])
                if id == "band-pass":
                    self.assertLess(abs(gain), 3)
                    band_pass = (main, aux)
                else:
                    self.assertLessEqual(gain, -10)
                self.assertLess(residual / (wet[0] / math.sqrt(2)), 0.01)
        saturated, aux = self.render_declared_additional("saturated")
        self.assertEqual(aux, band_pass[1])
        self.assert_tone(aux[960:], 20)
        filtered_harmonics, _ = sine_fit(band_pass[0][960:], (1200, 2400, 3600))
        harmonics, _ = sine_fit(saturated[960:], (1200, 2400, 3600))
        self.assertGreater(harmonics[0], 0.3)
        self.assertLess(harmonics[1] / harmonics[0], 0.01)
        self.assertGreaterEqual(20 * math.log10(
            (harmonics[2] / harmonics[0]) /
            max(filtered_harmonics[2] / filtered_harmonics[0], 1e-12)), 6)
        self.assertTrue(all(len(set(saturated[n:n + 8])) > 1
                            for n in range(960, len(saturated), 8)))
        crushed, aux = self.render_declared_additional("crushed")
        self.assertEqual(aux, band_pass[1])
        self.assert_tone(aux[960:], 20)
        self.assertLessEqual(max(abs(x - round(x * 31 / 2) * 2 / 31)
                                 for x in crushed[960:]), 1 / 32767)
        changes = [n for n in range(961, len(crushed)) if crushed[n] != crushed[n - 1]]
        self.assertGreater(len(changes), 5000)
        self.assertEqual({n % 8 for n in changes}, {0})
        for n in range(960, len(crushed), 8):
            self.assertEqual(len(set(crushed[n:n + 8])), 1)
        images, _ = sine_fit(crushed[960:], (1200, 4800, 7200))
        baseline, _ = sine_fit(saturated[960:], (1200, 4800, 7200))
        for image, original in zip(images[1:], baseline[1:]):
            self.assertGreater(image, 0.01)
            self.assertGreater(image, 10 * original)

    def test_declared_bad_line_sweeps(self):
        """phreak-package/declared-audio-auditions/articulation-pitch-and-treatment-auditions"""
        frames = 6 * 48000
        filtered, clean = self.render_treatment([f"timbre={1 / 3}", (11 / 42, frames)])
        for id, reverse in (("bad-line-sweep", False), ("bad-line-return", True)):
            with self.subTest(scenario=id):
                main, aux = self.render_declared_additional(id)
                self.assert_pcm_reference(aux, clean)
                for start in range(960, frames - 4800, 4800):
                    self.assert_tone(aux[start:start + 4800], 5)
                # Same analytical stage/5 ms ramp oracle as the direct sweep
                # test, using the SDK's frame/(total_frames-1) control timebase.
                mixes = [array("f"), array("f"), array("f")]
                current, targets, starts, ages = [0.0] * 3, [0.0] * 3, [0.0] * 3, [240] * 3
                for block in range(0, frames, 12):
                    t = float32(block / (frames - 1))
                    if reverse:
                        t = float32(1 - t)
                    for stage in range(3):
                        target = max(0, min(1, float32(float32(3 * t) - stage)))
                        if target != targets[stage]:
                            starts[stage], targets[stage], ages[stage] = current[stage], target, 0
                        for _ in range(12):
                            ages[stage] = min(240, ages[stage] + 1)
                            current[stage] = starts[stage] + (targets[stage] - starts[stage]) * ages[stage] / 240
                            mixes[stage].append(current[stage])
                # Two interior windows per stage detect reversed/missing stages
                # and early reduction, without assuming a sweep is stationary.
                for seconds in (0.5, 1.5, 2.5, 3.5, 4.5, 5.5):
                    start = int(seconds * 48000)
                    recovered_hold = []
                    for n in range(start, start + 2400):
                        band, saturation, reduction = (mix[n] for mix in mixes)
                        x = clean[n] + band * (filtered[n] - clean[n])
                        driven = (1 + 7 * saturation) * x
                        x += saturation * (0.8 * driven / (1 + abs(driven)) - x)
                        if reduction == 0:
                            # Compare PCM codes: WavWriter truncates, while
                            # this analytical model uses double arithmetic.
                            self.assertLessEqual(abs(round(main[n] * 32767) - int(x * 32767)), 1)
                        else:
                            recovered_hold.append((main[n] - (1 - reduction) * x) / reduction)
                    if recovered_hold:
                        t = 1 - seconds / 6 if reverse else seconds / 6
                        resolution = math.floor(7 * (3 * t - 2))
                        step, hold = 2 / (2 ** (12 - resolution) - 1), 1 + resolution
                        levels = [round(x / step) for x in recovered_hold]
                        # Undoing the wet mix amplifies both PCM error and the
                        # direct sweep oracle's 1e-5 float tolerance by 1/mix.
                        tolerance = (1 / 32767 + 1e-5) / min(mixes[2][start:start + 2400])
                        self.assertLess(max(abs(x - k * step) for x, k in
                                            zip(recovered_hold, levels)), tolerance)
                        changes = [n for n in range(1, len(levels)) if levels[n] != levels[n - 1]]
                        self.assertGreater(len(changes), 100)
                        self.assertEqual(len({n % hold for n in changes}), 1)

    def test_declared_selection_sweep(self):
        """phreak-package/declared-audio-auditions/articulation-pitch-and-treatment-auditions"""
        channels = self.render_declared_additional("selection-sweep")
        self.assert_clean_channels(channels)
        frames = 21 * 48000
        # First control block at/above each nominal boundary + 0.002. This
        # distinguishes hysteresis from crossing at nominal integer seconds.
        accepted = [0]
        for index in range(1, 21):
            threshold = float32(float32(index / 21) + float32(0.002))
            accepted.append(next(n for n in range(index * 48000, (index + 1) * 48000, 12)
                                 if float32(n / (frames - 1)) >= threshold))
        accepted.append(frames)
        voices = []
        for index in range(21):
            count = accepted[index + 1] - accepted[index] + (240 if index < 20 else 0)
            voice = self.render_timeline([((index + 0.5) / 21, count)])[1]
            voices.append(voice)
            # Verify every entry by spectrum during its on phase, and cadence
            # throughout its dwell. Ring stays on: its sweep dwell is only 1 s.
            for samples in channels:
                dwell = samples[accepted[index] + 960:accepted[index + 1]]
                self.assert_tone(dwell[:9600], index)
                if index == 13:
                    self.assertLess(rms(dwell[24000 - 960:]), 1e-4)
                else:
                    self.assertTrue(all(rms(dwell[n:n + 480]) > 0.02
                                        for n in range(0, len(dwell) - 479, 480)))
        expected = array("f", voices[0][:accepted[1]])
        for index in range(1, 21):
            outgoing_age = accepted[index] - accepted[index - 1]
            expected.extend(reference_fade(voices[index - 1][outgoing_age:outgoing_age + 240],
                                           voices[index][:240]))
            expected.extend(voices[index][240:accepted[index + 1] - accepted[index]])
        for samples in channels:
            # All samples include every 240-sample complementary linear fade,
            # startup/cadence ramps, busy silence and incoming phase restart.
            self.assert_pcm_reference(samples, expected)

    def test_all_centres_after_selection_changes(self):
        # The same 21 scenario IDs apply after upward and downward changes too.
        indices = list(range(21)) + list(reversed(range(20)))
        steps = self.render_steps([(i + 0.5) / 21 for i in indices], 0.44)
        for index, samples in zip(indices, steps):
            with self.subTest(scenario=TONE_CASES[index][0], index=index):
                self.assert_tone(samples[960:20160], index)

    def test_initial_boundaries_and_endpoints(self):
        """phreak-tones/equal-selection-zones/initial-boundaries-and-endpoints"""
        cases = [(-0.1, 0), (0, 0), (1, 20), (1.1, 20)]
        cases.extend((float32(i / 21), i) for i in range(1, 21))
        for harmonics, index in cases:
            with self.subTest(harmonics=harmonics, index=index):
                self.assert_tone(self.render(harmonics, 0.44)[960:20160], index)

    def test_boundary_jitter_and_reversal(self):
        """phreak-tones/selection-hysteresis/boundary-jitter-and-reversal"""
        for i in range(1, 21):
            b = float32(i / 21)
            low = float32(b - float32(0.001))
            high = float32(b + float32(0.001))
            controls = [low] + [low, high] * 10 + [
                float32(b + float32(0.002)),
                float32(b - float32(0.002)),
                float32(b - float32(0.003)),
            ]
            expected = [i - 1] * 21 + [i, i, i - 1]
            steps = self.render_steps(controls)
            # First dwell establishes selection; all measured windows are past
            # startup and allow 6 ms for the separately implemented 5 ms fade.
            for step in range(1, len(steps)):
                with self.subTest(boundary=i, step=step, harmonics=controls[step]):
                    self.assert_tone(steps[step][288:], expected[step])

    def test_hysteresis_exact_thresholds_and_adjacent_floats(self):
        """phreak-tones/selection-hysteresis/boundary-jitter-and-reversal"""
        for i in range(1, 21):
            b = float32(i / 21)
            up = float32(b + float32(0.002))
            down = float32(b - float32(0.002))
            controls = [(i - 0.5) / 21,
                        adjacent_float32(up, -1), up, adjacent_float32(up, 1),
                        adjacent_float32(down, 1), down, adjacent_float32(down, -1)]
            expected = [i - 1, i - 1, i, i, i, i, i - 1]
            steps = self.render_steps(controls)
            for step in range(1, len(steps)):
                with self.subTest(boundary=i, step=step, harmonics=controls[step]):
                    self.assert_tone(steps[step][288:], expected[step])

    def test_reset_clears_selection_history(self):
        """phreak-tones/equal-selection-zones/initial-boundaries-and-endpoints"""
        for i in range(1, 21):
            b = float32(i / 21)
            low, high = b - 0.001, b + 0.001
            steps = self.render_steps([low, "reset", high, low, "reset", low], 0.1)
            for step, index in enumerate([i - 1, i, i, i - 1]):
                with self.subTest(boundary=i, step=step):
                    self.assert_tone(steps[step][960:], index)

    def test_nonadjacent_selection_and_endpoint_reversal(self):
        # Complement the sample-by-sample direct-jump regression with spectra.
        controls = [1 / 42, 41 / 42, 1 / 42, 1.1, -0.1, 35 / 42, 11 / 42]
        indices = [0, 20, 0, 20, 0, 17, 5]
        for step, (samples, index) in enumerate(zip(self.render_steps(controls, 0.1), indices)):
            with self.subTest(step=step, index=index):
                self.assert_tone(samples[960:], index)

    def test_five_millisecond_reference_mixture(self):
        """phreak-tones/selection-crossfade/five-millisecond-transition"""
        old = self.render_timeline([(3 / 42, 6000)])[1]
        new = self.render_timeline([(5 / 42, 1200)])[1]
        expected = (list(old[:4800]) + reference_fade(old[4800:5040], new[:240])
                    + list(new[240:]))
        for block_size in (1, 7, 12, 24):
            with self.subTest(block_size=block_size):
                channels = self.render_timeline([(3 / 42, 4800), (5 / 42, 1200)],
                                                block_size)
                self.assert_reference(channels, expected)
                for samples in channels:
                    self.assertEqual(samples[4800], old[4800])
                    self.assertEqual(samples[5039], new[239])
                    self.assertEqual(samples[5040:], new[240:])

    def test_large_selection_jump_reference_mixture(self):
        """phreak-tones/selection-hysteresis/large-selection-jump"""
        dial = self.render_timeline([(1 / 42, 5040)])[1]
        mark = self.render_timeline([(41 / 42, 5040)])[1]
        expected = (list(dial[:4800])
                    + reference_fade(dial[4800:], mark[:240]) + list(mark[240:4800])
                    + reference_fade(mark[4800:], dial[:240]) + list(dial[240:4800]))
        for block_size in (1, 7, 12, 24):
            with self.subTest(block_size=block_size):
                channels = self.render_timeline(
                    [(1 / 42, 4800), (41 / 42, 4800), (1 / 42, 4800)], block_size)
                self.assert_reference(channels, expected)

    def test_rapid_changes_keep_only_latest_pending_voice(self):
        """phreak-tones/selection-crossfade/rapid-changes-settle"""
        key1 = self.render_timeline([(3 / 42, 1440)])[1]
        key2 = self.render_timeline([(5 / 42, 1440)])[1]
        # Besides the specified FSK request, cover returning to the incoming
        # voice (cancel pending), outgoing voice (finish then fade back), and
        # hysteresis around the pending key-3 zone (retain key 3).
        for final_h, final_index in ((39 / 42, 19), (5 / 42, 2),
                                     (3 / 42, 1), (3 / 21 - 0.001, 3)):
            final = self.render_timeline([((final_index + 0.5) / 21, 1440)])[1]
            expected = list(key1[:48]) + reference_fade(key1[48:288], key2[:240])
            if final_index == 2:
                expected += list(key2[240:1296])
            else:
                expected += reference_fade(key2[240:480], final[:240])
                expected += list(final[240:1056])
            for block_size in (1, 7, 12, 24):
                with self.subTest(final_index=final_index, block_size=block_size):
                    channels = self.render_timeline(
                        [(3 / 42, 48), (5 / 42, 48), (7 / 42, 48), (final_h, 1200)],
                        block_size)
                    self.assert_reference(channels, expected)
                    # Final request is sample 144; by 10 ms + one block only
                    # the latest requested tone may remain, with full amplitude.
                    self.assert_tone(channels[1][144 + 480 + block_size:], final_index)

    def test_reset_during_fade_clears_voices_pending_and_selector(self):
        """phreak-tones/selection-crossfade/rapid-changes-settle"""
        for block_size in (1, 7, 12, 24):
            for target in (3 / 42, 5 / 42, 39 / 42, 3 / 21 - 0.001):
                # Replay after Reset must be identical to a fresh engine,
                # including startup, a later transition, and another queue.
                replay = [(target, 360), (7 / 42, 48), (1 / 42, 720)]
                fresh = self.render_timeline(replay, block_size)
                # Reset with both slots active, at promotion, and during the
                # queued fade after the two voice slots have swapped roles.
                for elapsed in (48, 239, 240, 300, 479):
                    with self.subTest(block_size=block_size, target=target, elapsed=elapsed):
                        prefix = [(3 / 42, 4800), (5 / 42, 12), (7 / 42, 12),
                                  (39 / 42, elapsed - 24)]
                        channels = self.render_timeline(prefix + ["reset"] + replay,
                                                        block_size)
                        for samples, reference in zip(channels, fresh):
                            self.assertEqual(samples[4800 + elapsed:], reference)

    def test_nominal_selector_indices(self):
        # Direct helper checks make endpoint failures deterministic even when a
        # bad index would otherwise dereference beyond the production table.
        cases = [(-0.1, 0), (0, 0), (1, 20), (1.1, 20)]
        cases.extend(((index + 0.5) / 21, index) for index in range(21))
        for harmonics, expected in cases:
            with self.subTest(harmonics=harmonics):
                actual = subprocess.check_output(
                    [str(self.driver), "index", str(harmonics)], text=True)
                self.assertEqual(int(actual), expected)

    def test_clamped_harmonics_endpoints(self):
        for value, centre in [(-0.1, 1 / 42), (0, 1 / 42), (1, 41 / 42), (1.1, 41 / 42)]:
            with self.subTest(harmonics=value):
                self.assertEqual(self.render(value, 0.1), self.render(centre, 0.1))


class DocumentationTests(unittest.TestCase):
    @staticmethod
    def rows(text):
        return [[cell.strip() for cell in line.strip().strip("|").split("|")]
                for line in text.splitlines() if line.startswith("| ")]

    def assert_tone_table(self, text):
        rows = [row for row in self.rows(text) if row[0].isdigit()]
        self.assertEqual(len(rows), 21)
        for index, (row, (_, label, frequencies)) in enumerate(zip(rows, TONE_CASES)):
            with self.subTest(entry=label):
                self.assertEqual(len(row), 6)
                self.assertEqual(int(row[0]), index)
                suffix = {"fsk-space": "fsk-0", "fsk-mark": "fsk-1"}.get(label, label)
                self.assertEqual(row[2], f"`tone-{suffix}`")
                fraction, decimal = row[3].split(" = ")
                self.assertEqual(fraction, f"{2 * index + 1}/42")
                self.assertAlmostEqual(float(decimal), (index + 0.5) / 21, delta=5e-10)
                self.assertEqual(tuple(map(int, row[4].split(" + "))), frequencies)
                expected = {13: "0.5 s on / 0.5 s off", 14: "2 s on / 4 s off"}
                self.assertEqual(row[5], expected.get(index, "Continuous"))

    def test_read_control_contract(self):
        """phreak-package/controls-and-output-descriptions/read-the-control-contract"""
        manifest = SDK.load_package(str(PACKAGE))["manifest"]
        readme = (PACKAGE / "README.md").read_text()
        self.assertEqual([c["id"] for c in manifest["controls"]],
                         ["harmonics", "timbre", "morph", "macro"])
        control_rows = [row for row in self.rows(readme)
                        if row[0] in ("`harmonics`", "`timbre`", "`morph`", "`macro`")]
        self.assertEqual([row[0].strip("`") for row in control_rows],
                         ["harmonics", "timbre", "morph", "macro"])
        for control in manifest["controls"][2:]:
            self.assertIn("no effect", control["description"])
            self.assertIn("v1", control["description"])
        for row in control_rows[2:]:
            self.assertIn("no effect in v1", row[2])
        for token in ("clean at 0", "300–3400 Hz", "1/3", "saturation", "2/3", "reduction"):
            self.assertIn(token, manifest["controls"][1]["description"])
            self.assertIn(token, control_rows[1][2])
        for channel, treatment in (("main", "processed"), ("aux", "untreated")):
            self.assertIn(treatment + " by TIMBRE", manifest["outputs"][channel])
            for term in ("cadence", "LPG bursts"):
                self.assertIn(term, manifest["outputs"][channel])
        for term in ("0.100 s", "rising edge", "idle is silent", "Unpatched", "cadence"):
            self.assertIn(term, manifest["trigger"])
        self.assertIn("MIDI note 60", manifest["description"])
        self.assertIn("same ratio", manifest["description"])
        self.assertEqual(manifest["postProcessing"], {
            "alreadyEnveloped": True, "outGain": 1.0, "auxGain": 1.0,
        })
        self.assert_tone_table(readme)

    def test_audition_notes_and_deferred_checks(self):
        """phreak-package/repeatable-full-validation-and-listening-notes/audition-notes-and-deferred-hardware-checks"""
        notes = (PACKAGE / "AUDITION.md").read_text()
        self.assert_tone_table(notes)
        rows = {row[0].strip("`"): row for row in self.rows(notes)}
        for id, (seconds, note, trigger, harmonics, timbre) in ADDITIONAL_AUDITIONS.items():
            with self.subTest(audition=id):
                row = rows[id]
                self.assertEqual(len(row), 7)
                self.assertEqual(row[1:4], [f"{seconds} s", str(note), str(trigger)])
                for cell, expected in zip(row[4:6], (harmonics, timbre)):
                    if isinstance(expected, list):
                        self.assertEqual(json.loads(cell), expected)
                    else:
                        numerator, _, denominator = cell.partition("/")
                        self.assertAlmostEqual(float(numerator) / float(denominator or 1),
                                               expected)
                self.assertTrue(row[6])
        # Preserve the limitations and an honest, fillable observation record.
        prose = " ".join(notes.split())
        for term in ("MAIN is channel 1", "AUX is channel 2", "0.100 ± 0.010 s",
                     "-80 dBFS", "0.110 s", "within 1 Hz", "0.5 dB", "-40 dBc",
                     "0.010 s RMS", "Strike", "TRIGGER_UNPATCHED", "following block",
                     "cannot maintain the patched state", "pending", "recognition",
                     "switching smoothness", "character", "listener/date", "--full",
                     "unittest discover", "not hardware approval"):
            self.assertIn(term, prose)
        for gate in ("ARM compilation and both firmware layouts",
                     "Physical Tall Dog clone CPU/audio checks", "Palette submission",
                     "Approved catalog and publication"):
            self.assertIn("Deferred", rows[gate][1])

    def test_documented_channel_split_preserves_samples(self):
        """phreak-package/repeatable-full-validation-and-listening-notes/audition-notes-and-deferred-hardware-checks"""
        notes = (PACKAGE / "AUDITION.md").read_text()
        script = notes.split("python3 - <<'PY_SPLIT'\n", 1)[1].split("\nPY_SPLIT", 1)[0]
        with tempfile.TemporaryDirectory(prefix="phreak-docs-") as directory:
            output = Path(directory) / "build/phreak"
            output.mkdir(parents=True)
            # Distinct signed channel data catches swapped, summed, normalized
            # or byte-misaligned output in the exact documented command.
            main = (0, 32767, -32768, 100, -200)
            aux = (1500, -3000, 999, -1, 0)
            interleaved = [x for pair in zip(main, aux) for x in pair]
            with wave.open(str(output / "example.wav"), "wb") as audio:
                audio.setparams((2, 2, 48000, 0, "NONE", "not compressed"))
                audio.writeframes(struct.pack("<10h", *interleaved))
            subprocess.run([sys.executable, "-c", script], cwd=directory, check=True)
            for label, expected in (("main", main), ("aux", aux)):
                with wave.open(str(output / "channels" / f"example-{label}.wav"), "rb") as audio:
                    self.assertEqual((audio.getnchannels(), audio.getsampwidth(),
                                      audio.getframerate(), audio.getnframes()), (1, 2, 48000, 5))
                    self.assertEqual(struct.unpack("<5h", audio.readframes(5)), expected)


class PackageTests(unittest.TestCase):
    def run_command(self, command):
        result = subprocess.run(
            command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_clean_output_manifest_gains(self):
        """phreak-pitch-outputs/clean-and-processed-routing/clean-endpoint-equality"""
        manifest = json.loads((PACKAGE / "plaits-engine.json").read_text())
        self.assertEqual(manifest["postProcessing"], {
            "alreadyEnveloped": True, "outGain": 1.0, "auxGain": 1.0,
        })

    def test_validate_package_by_path(self):
        """phreak-package/community-package-identity/validate-package-by-path"""
        manifest = json.loads((PACKAGE / "plaits-engine.json").read_text())
        expected = {
            "schemaVersion": 1,
            "sdk": "plaits-engine-cpp-v1",
            "packageType": "community",
            "id": "community/phreak",
            "catalogId": "phreak",
            "version": "0.1.0",
            "name": "Phreak",
            "origin": "Community",
            "source": {
                "root": "src",
                "header": "phreak_engine.h",
                "files": ["phreak_engine.cc"],
                "className": "PhreakEngine",
            },
        }
        for key, value in expected.items():
            with self.subTest(field=key):
                self.assertEqual(manifest[key], value)
        # Linking the SDK renderer exercises the class/interface by path,
        # without catalog registration.
        self.run_command([
            sys.executable, "-B", str(SDK_DIR / "plaits_lab.py"), "check",
            str(PACKAGE.relative_to(REPO_ROOT)),
        ])

    def test_licensing_and_portability(self):
        """phreak-package/sdk-compatible-licensing-and-source/licensing-and-portability-gate"""
        # Run actual SDK include/allocation/libm/license policy without edits.
        package = SDK.load_package(str(PACKAGE))
        self.assertEqual(package["manifest"]["license"], "MIT")
        license_text = (PACKAGE / "LICENSE").read_text()
        self.assertIn("Copyright (c) 2026 Matt Policastro", license_text)
        self.assertIn(" ".join(SDK.MIT_BODY.split()), " ".join(license_text.split()))
        for source in sorted((PACKAGE / "src").rglob("*")):
            if source.suffix in (".h", ".cc"):
                with self.subTest(source=source.name):
                    text = source.read_text()
                    self.assertIn("// Copyright 2026 Matt Policastro.", text)
                    self.assertEqual(SDK.source_spdx_id(text), "MIT")

        compiler = shlex.split(os.environ.get("CXX", "c++"))
        with tempfile.TemporaryDirectory(prefix="phreak-cxx98-") as directory:
            for index, source in enumerate(package["source_files"]):
                with self.subTest(translation_unit=source.name):
                    self.run_command([
                        *compiler, "-std=c++98", "-pedantic-errors", "-DTEST",
                        # Repository headers use a trailing enum comma (a
                        # C++11 extension). Keep strict diagnostics on package
                        # code while treating shared headers as dependencies.
                        "-D_USE_MATH_DEFINES", "-isystem", str(REPO_ROOT),
                        "-I", str(package["source_root"]), "-c", str(source),
                        "-o", str(Path(directory) / (str(index) + ".o")),
                    ])


if __name__ == "__main__":
    unittest.main(verbosity=2)
