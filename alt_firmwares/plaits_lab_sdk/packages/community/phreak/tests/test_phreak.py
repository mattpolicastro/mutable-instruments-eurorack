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

    def render_timeline(self, events, block_size=12, note=60):
        """Sample-timed (HARMONICS, frames) events, with optional reset tokens."""
        output = self.directory / "timeline.f32"
        arguments = [f"note={note}"]
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
                # Deliberately unaligned event positions, and reset during off,
                # away from a cycle boundary. Reset must reproduce startup.
                prefix, dwell = 1733, seconds * 48000 - 1234
                restart = round(on * 48000) + 480
                dial = self.render_timeline([(1 / 42, prefix + 240)], note=note)[1]
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
