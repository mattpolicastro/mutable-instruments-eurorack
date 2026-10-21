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
        samples = array("f")
        samples.frombytes(output.read_bytes())
        self.assertEqual(len(samples), 2 * int(seconds * 48000))
        self.assertTrue(all(math.isfinite(x) and abs(x) <= 0.500001 for x in samples))
        return samples[1::2]

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
                amplitudes, residual = sine_fit(aux[960:20160], frequencies)
                level = 0.25 if len(frequencies) == 2 else 0.5
                for amplitude in amplitudes:
                    self.assertAlmostEqual(amplitude, level, delta=0.001)
                self.assertLessEqual(20 * math.log10(max(amplitudes) / min(amplitudes)), 0.5)
                # Fitting exact reference Hz over 400 ms with this residual bound
                # constrains tuning more tightly than 1 Hz and spurs below -40 dBc.
                self.assertLess(residual / (min(amplitudes) / math.sqrt(2)), 0.01)

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
