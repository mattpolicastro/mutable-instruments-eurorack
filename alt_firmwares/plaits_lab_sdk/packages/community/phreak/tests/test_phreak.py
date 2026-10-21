#!/usr/bin/env python3
# Copyright 2026 Matt Policastro.
# SPDX-License-Identifier: MIT
"""Package gates; generated build output lives only in temporary directories."""

import importlib.util
from array import array
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

    def render_timeline(self, events, block_size=12):
        """Sample-timed (HARMONICS, frames) events, with optional reset tokens."""
        output = self.directory / "timeline.f32"
        arguments = []
        frames = 0
        for event in events:
            if event == "reset":
                arguments.append(event)
            else:
                harmonics, count = event
                arguments.extend((str(harmonics), str(count)))
                frames += count
        subprocess.run([str(self.driver), "timeline", str(block_size), str(output),
                        *arguments], check=True)
        return self.read_channels(output, frames)

    def read_channels(self, output, frames):
        samples = array("f")
        samples.frombytes(output.read_bytes())
        self.assertEqual(len(samples), 2 * frames)
        self.assertTrue(all(math.isfinite(x) and abs(x) <= 0.500001 for x in samples))
        return samples[0::2], samples[1::2]

    def read_aux(self, output, frames):
        return self.read_channels(output, frames)[1]

    def assert_reference(self, channels, reference):
        for label, samples in zip(("MAIN", "AUX"), channels):
            with self.subTest(channel=label):
                self.assertEqual(len(samples), len(reference))
                self.assertLessEqual(max(abs(a - b) for a, b in zip(samples, reference)),
                                     1e-6)

    def assert_tone(self, samples, index):
        frequencies = TONE_CASES[index][2]
        amplitudes, residual = sine_fit(samples, frequencies)
        level = 0.25 if len(frequencies) == 2 else 0.5
        for amplitude in amplitudes:
            self.assertAlmostEqual(amplitude, level, delta=0.001)
        self.assertLessEqual(20 * math.log10(max(amplitudes) / min(amplitudes)), 0.5)
        self.assertLess(residual / (min(amplitudes) / math.sqrt(2)), 0.01)

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


class PackageTests(unittest.TestCase):
    def run_command(self, command):
        result = subprocess.run(
            command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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
