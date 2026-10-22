#!/usr/bin/env python3
# Copyright 2026 Matt Policastro.
# SPDX-License-Identifier: MIT
"""Phreak v2 package gates. Build output lives only in temporary directories.

The reference tables below are written out independently of the C++ tables:
a test that derived its expectations from the engine could not catch a wrong
frequency or cadence.
"""

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
sys.dont_write_bytecode = True

SR = 48000
SILENCE, TONES, FSK, DPSK, QAM, ANSAM, PROBE = range(7)


def tones(seconds, *hz):
    return (seconds, TONES, hz)


def off(seconds):
    return (seconds, SILENCE, ())


def fsk(seconds, mark, space, baud):
    return (seconds, FSK, (mark, space), baud)


def coin(seconds):
    return tones(seconds, 1700, 2200)


def digit(low, high):
    return [tones(0.09, low, high), off(0.07)]


# (system, [(entry label, [steps])]); a step of 0 seconds holds forever.
REFERENCE = [
    ("north-america", [
        ("dial", [tones(0, 350, 440)]),
        ("key-1", [tones(0, 697, 1209)]), ("key-2", [tones(0, 697, 1336)]),
        ("key-3", [tones(0, 697, 1477)]), ("key-4", [tones(0, 770, 1209)]),
        ("key-5", [tones(0, 770, 1336)]), ("key-6", [tones(0, 770, 1477)]),
        ("key-7", [tones(0, 852, 1209)]), ("key-8", [tones(0, 852, 1336)]),
        ("key-9", [tones(0, 852, 1477)]), ("key-0", [tones(0, 941, 1336)]),
        ("hash", [tones(0, 941, 1477)]), ("star", [tones(0, 941, 1209)]),
        ("busy", [tones(0.5, 480, 620), off(0.5)]),
        ("ring", [tones(2.0, 440, 480), off(4.0)]),
        ("key-a", [tones(0, 697, 1633)]), ("key-b", [tones(0, 770, 1633)]),
        ("key-c", [tones(0, 852, 1633)]), ("key-d", [tones(0, 941, 1633)]),
        ("fsk-space", [tones(0, 2200)]), ("fsk-mark", [tones(0, 1200)]),
    ]),
    ("united-kingdom", [
        ("dial", [tones(0, 350, 440)]),
        ("ring", [tones(0.4, 400, 450), off(0.2), tones(0.4, 400, 450), off(2.0)]),
        ("engaged", [tones(0.375, 400), off(0.375)]),
        ("congestion", [tones(0.4, 400), off(0.35), tones(0.225, 400), off(0.525)]),
        ("unobtainable", [tones(0, 400)]),
    ]),
    ("europe", [
        ("dial", [tones(0, 425)]),
        ("ring", [tones(1.0, 425), off(4.0)]),
        ("busy", [tones(0.5, 425), off(0.5)]),
        ("congestion", [tones(0.25, 425), off(0.25)]),
    ]),
    ("japan", [
        ("dial", [tones(0, 400)]),
        ("ring", [tones(1.0, 392, 408), off(2.0)]),
        ("busy", [tones(0.5, 400), off(0.5)]),
    ]),
    ("blue-box", [
        ("seize", [tones(0, 2600)]), ("kp", [tones(0, 1100, 1700)]),
        ("mf-1", [tones(0, 700, 900)]), ("mf-2", [tones(0, 700, 1100)]),
        ("mf-3", [tones(0, 900, 1100)]), ("mf-4", [tones(0, 700, 1300)]),
        ("mf-5", [tones(0, 900, 1300)]), ("mf-6", [tones(0, 1100, 1300)]),
        ("mf-7", [tones(0, 700, 1500)]), ("mf-8", [tones(0, 900, 1500)]),
        ("mf-9", [tones(0, 1100, 1500)]), ("mf-0", [tones(0, 1300, 1500)]),
        ("st", [tones(0, 1500, 1700)]),
    ]),
    ("specials", [
        ("red-box-nickel", [coin(0.066), off(0.934)]),
        ("red-box-dime", [coin(0.066), off(0.066), coin(0.066), off(0.802)]),
        ("red-box-quarter", [coin(0.033), off(0.033)] * 4 + [coin(0.033), off(0.67)]),
        ("sit-intercept", [tones(0.274, 913.8), tones(0.274, 1370.6),
                           tones(0.380, 1776.7), off(2.0)]),
        ("sit-no-circuit", [tones(0.380, 985.2), tones(0.380, 1428.5),
                            tones(0.380, 1776.7), off(2.0)]),
        ("off-hook-howler", [tones(0.1, 1400, 2060, 2450, 2600), off(0.1)]),
        ("test-1004", [tones(0, 1004)]),
    ]),
    ("modem", [
        ("answer", [(0, ANSAM, (2100,), 15)]),
        ("bell-103-originate", [fsk(0, 1270, 1070, 300)]),
        ("bell-103-answer", [fsk(0, 2225, 2025, 300)]),
        ("v21-channel-1", [fsk(0, 980, 1180, 300)]),
        ("v21-channel-2", [fsk(0, 1650, 1850, 300)]),
        ("bell-202", [fsk(0, 1200, 2200, 1200)]),
        ("caller-id", [tones(2.0, 440, 480), off(0.5), fsk(0.6, 1200, 2200, 1200), off(2.9)]),
        ("v22-originate", [(0, DPSK, (1200,), 600)]),
        ("v22-answer", [(0, DPSK, (2400,), 600)]),
        ("v34-probe", [(0, PROBE, (150, 3750, 900, 1200), 0)]),
        ("training", [(0, QAM, (1920,), 3200)]),
        ("connect", [tones(1.0, 350, 440), off(0.3)]
            + digit(770, 1336) * 3 + digit(941, 1336) + digit(697, 1209)
            + digit(697, 1336) + digit(697, 1477)
            + [off(1.2), tones(2.0, 440, 480), off(0.6), (2.4, ANSAM, (2100,), 15),
               fsk(0.45, 980, 1180, 300), fsk(0.45, 1650, 1850, 300), off(0.1),
               (0.16, PROBE, (150, 3750, 900, 1200), 0), off(0.05),
               (0.55, PROBE, (150, 3750, 900, 1200), 0), off(0.1),
               (0.4, DPSK, (1200,), 600), (2.6, QAM, (1920,), 3200), off(0)]),
    ]),
]

# Declared previews: scenario ID -> (system, entry label) its start selects.
SCENARIO_TARGETS = {
    "na-dial": ("north-america", "dial"), "na-key-5": ("north-america", "key-5"),
    "na-busy": ("north-america", "busy"), "na-ringback": ("north-america", "ring"),
    "na-keypress": ("north-america", "key-5"), "na-sweep": ("north-america", "dial"),
    "uk-ring": ("united-kingdom", "ring"), "uk-engaged": ("united-kingdom", "engaged"),
    "uk-congestion": ("united-kingdom", "congestion"), "europe-ring": ("europe", "ring"),
    "europe-busy": ("europe", "busy"), "japan-ring": ("japan", "ring"),
    "blue-box-seize": ("blue-box", "seize"), "blue-box-call": ("blue-box", "seize"),
    "red-box-quarter": ("specials", "red-box-quarter"),
    "sit-intercept": ("specials", "sit-intercept"),
    "off-hook-howler": ("specials", "off-hook-howler"),
    "modem-answer": ("modem", "answer"), "modem-bell-103": ("modem", "bell-103-originate"),
    "modem-v21": ("modem", "v21-channel-1"), "modem-caller-id": ("modem", "caller-id"),
    "modem-v22": ("modem", "v22-originate"), "modem-v34-probe": ("modem", "v34-probe"),
    "modem-training": ("modem", "training"), "modem-connect": ("modem", "connect"),
    "line-analog": ("north-america", "key-5"), "line-digital": ("north-america", "key-5"),
    "line-sweep": ("north-america", "key-5"), "twist-sweep": ("north-america", "key-5"),
    "system-sweep": ("north-america", "key-0"), "pitch-low": ("north-america", "key-5"),
    "pitch-high": ("north-america", "key-5"),
}


def centre(index, count):
    return (index + 0.5) / count


def select(system, label):
    """HARMONICS and MORPH at the centres of a system's and an entry's zones."""
    names = [name for name, _ in REFERENCE]
    s = names.index(system)
    entries = REFERENCE[s][1]
    e = [name for name, _ in entries].index(label)
    return [f"h={centre(s, len(REFERENCE))!r}", f"m={centre(e, len(entries))!r}"]


def rms(samples):
    return math.sqrt(sum(x * x for x in samples) / max(1, len(samples)))


def window(samples, start, end):
    return samples[int(start * SR):int(end * SR)]


def sine_fit(samples, frequencies):
    """Least-squares amplitudes at reference Hz, with arbitrary phases."""
    basis = [[function(2 * math.pi * hz * n / SR) for n in range(len(samples))]
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
    amplitudes = [math.hypot(weights[i], weights[i + 1]) for i in range(0, len(weights), 2)]
    residual = math.sqrt(sum(
        (sample - sum(w * b[n] for w, b in zip(weights, basis))) ** 2
        for n, sample in enumerate(samples)) / len(samples))
    return amplitudes, residual


def band(samples, hz, frame=960):
    """Mean amplitude at one frequency over short frames (Goertzel), so keyed
    signals (FSK bits, phase reversals) do not cancel themselves out."""
    total, frames = 0.0, 0
    coefficient = 2 * math.cos(2 * math.pi * hz / SR)
    for start in range(0, len(samples) - frame + 1, frame):
        s1 = s2 = 0.0
        for x in samples[start:start + frame]:
            s1, s2 = x + coefficient * s1 - s2, s1
        total += 2 * math.sqrt(max(0.0, s1 * s1 + s2 * s2 - coefficient * s1 * s2)) / frame
        frames += 1
    return total / max(1, frames)


class PhreakTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = tempfile.TemporaryDirectory(prefix="phreak-")
        cls.addClassCleanup(directory.cleanup)
        cls.directory = Path(directory.name)
        cls.driver = cls.directory / ("render_cases.exe" if os.name == "nt" else "render_cases")
        compiler = shlex.split(os.environ.get("CXX", "c++"))
        # The shared resource file has a zero-length array extension. Compile it
        # separately; package code and the driver keep strict C++98 checks.
        resources = cls.directory / "resources.o"
        subprocess.run([*compiler, "-std=c++98", "-DTEST", "-O2", "-I", str(REPO_ROOT),
                        "-c", str(REPO_ROOT / "plaits/resources.cc"), "-o", str(resources)],
                       check=True, cwd=REPO_ROOT)
        subprocess.run([
            *compiler, "-std=c++98", "-pedantic-errors", "-DTEST", "-D_USE_MATH_DEFINES",
            "-O2", "-Wall", "-Werror", "-isystem", str(REPO_ROOT),
            "-I", str(PACKAGE / "src"), str(PACKAGE / "tests/render_cases.cc"),
            str(PACKAGE / "src/phreak_engine.cc"), str(REPO_ROOT / "stmlib/dsp/units.cc"),
            str(resources), "-o", str(cls.driver)], check=True, cwd=REPO_ROOT)

    def render(self, *tokens, block=12):
        """MAIN and AUX for a timeline of control tokens and frame counts."""
        output = self.directory / "timeline.f32"
        subprocess.run([str(self.driver), "timeline", str(block), str(output),
                        *(str(t) for t in tokens)], check=True)
        samples = array("f")
        samples.frombytes(output.read_bytes())
        main, aux = samples[0::2], samples[1::2]
        self.assertTrue(all(math.isfinite(x) and abs(x) <= 1.0 for x in main))
        self.assertTrue(all(math.isfinite(x) and abs(x) <= 0.500001 for x in aux))
        return main, aux

    def entry(self, system, label, seconds, *extra, block=12):
        return self.render(*select(system, label), *extra, int(seconds * SR), block=block)

    # --- tables -------------------------------------------------------------

    def test_tables_match_the_reference(self):
        lines = subprocess.run([str(self.driver), "table"], capture_output=True, text=True,
                               check=True).stdout.splitlines()
        systems, entries = [], None
        for line in lines:
            kind, *fields = line.split()
            if kind == "system":
                entries = []
                systems.append((fields[0], entries))
            elif kind == "entry":
                entries.append((fields[0], []))
            else:
                seconds, signal, *hz, rate = map(float, fields)
                entries[-1][1].append((seconds, int(signal), hz, rate))
        self.assertEqual([name for name, _ in systems], [name for name, _ in REFERENCE])
        for (system, actual), (_, expected) in zip(systems, REFERENCE):
            self.assertEqual([label for label, _ in actual], [label for label, _ in expected],
                             system)
            for (label, steps), (_, reference) in zip(actual, expected):
                self.assertEqual(len(steps), len(reference), f"{system}/{label}")
                for (seconds, signal, hz, rate), step in zip(steps, reference):
                    with self.subTest(entry=f"{system}/{label}"):
                        self.assertAlmostEqual(seconds, step[0], places=4)
                        self.assertEqual(signal, step[1])
                        self.assertEqual([h for h in hz if h], [float(h) for h in step[2]])
                        self.assertAlmostEqual(rate, step[3] if len(step) > 3 else 0.0, places=4)

    def test_tone_entries_sound_their_frequencies(self):
        for system, entries in REFERENCE:
            for label, steps in entries:
                seconds, signal, hz = steps[0][:3]
                if signal != TONES:
                    continue
                end = min(seconds or 0.1, 0.1)
                with self.subTest(entry=f"{system}/{label}"):
                    _, aux = self.entry(system, label, end)
                    samples = window(aux, 0.003, end - 0.002)
                    amplitudes, residual = sine_fit(samples, hz)
                    level = 0.5 / len(hz) if len(hz) != 2 else 0.25
                    for amplitude in amplitudes:
                        self.assertAlmostEqual(amplitude, level, delta=0.01 * level + 0.002)
                    self.assertLess(residual, 0.02 * level)

    def test_cadences_and_sequences_keep_time(self):
        for system, entries in REFERENCE:
            for label, steps in entries:
                if len(steps) < 2 or any(step[1] not in (TONES, SILENCE) for step in steps):
                    continue
                cycle = sum(step[0] for step in steps)
                with self.subTest(entry=f"{system}/{label}"):
                    _, aux = self.entry(system, label, cycle + 0.05)
                    start = 0.0
                    for seconds, signal, hz in steps:
                        margin = min(0.004, seconds / 4)
                        part = window(aux, start + margin, start + seconds - margin)
                        if signal == SILENCE:
                            self.assertLess(rms(part), 1e-5)
                        else:
                            amplitudes, _ = sine_fit(part[:2400], hz)
                            level = 0.5 / len(hz) if len(hz) != 2 else 0.25
                            self.assertGreater(min(amplitudes), 0.9 * level)
                        start += seconds

    def test_modem_signals(self):
        _, aux = self.entry("modem", "answer", 1.0)
        self.assertGreater(band(aux, 2100), 0.35)
        self.assertLess(band(aux, 1500), 0.01)
        # 15 Hz AM at 20%: the 2 ms envelope swings between about 0.8 and 1.2.
        envelope = [max(abs(x) for x in aux[i:i + 96]) for i in range(4800, len(aux) - 96, 96)]
        self.assertAlmostEqual(max(envelope) / min(envelope), 1.5, delta=0.15)
        # A phase reversal every 450 ms: the in-phase product flips sign.
        def phase(at):
            part = window(aux, at, at + 0.01)
            n0 = int(at * SR)
            return sum(x * math.sin(2 * math.pi * 2100 * (n0 + n) / SR) for n, x in enumerate(part))
        before, after = phase(0.42), phase(0.46)
        self.assertLess(before * after, 0)

        for label, mark, space, other in (("bell-103-originate", 1270, 1070, 2225),
                                          ("v21-channel-1", 980, 1180, 1750),
                                          ("v21-channel-2", 1650, 1850, 1080),
                                          ("bell-202", 1200, 2200, 3200)):
            with self.subTest(entry=label):
                _, aux = self.entry("modem", label, 1.0)
                self.assertGreater(band(aux, mark), 0.08)
                self.assertGreater(band(aux, space), 0.08)
                self.assertLess(band(aux, other), 0.03)

        for label, carrier in (("v22-originate", 1200), ("v22-answer", 2400)):
            with self.subTest(entry=label):
                _, aux = self.entry("modem", label, 1.0)
                self.assertGreater(band(aux, carrier), 0.1)
                self.assertLess(band(aux, carrier + 900), 0.03)

        _, aux = self.entry("modem", "v34-probe", 0.5)
        part = window(aux, 0.1, 0.5)
        for k in range(1, 26):
            hz = 150 * k
            amplitude = band(part, hz, frame=1920)
            with self.subTest(probe_hz=hz):
                if hz in (900, 1200, 1800, 2400):
                    self.assertLess(amplitude, 0.01)
                else:
                    self.assertGreater(amplitude, 0.04)

        _, aux = self.entry("modem", "training", 1.0)
        for hz in (900, 1920, 3000):  # 3200 baud spreads about 1920 Hz
            self.assertGreater(band(aux, hz), 0.02)
        self.assertLess(band(aux, 4500), 0.5 * band(aux, 1920))

    def test_caller_id_between_rings(self):
        _, aux = self.entry("modem", "caller-id", 6.0)
        self.assertGreater(rms(window(aux, 0.1, 1.9)), 0.2)
        self.assertLess(rms(window(aux, 2.05, 2.45)), 1e-5)
        burst = window(aux, 2.55, 3.05)
        # 1200 baud spreads each tone's energy over more bit transitions.
        self.assertGreater(band(burst, 1200), 0.05)
        self.assertGreater(band(burst, 2200), 0.05)
        self.assertLess(rms(window(aux, 3.15, 5.95)), 1e-5)

    def test_connect_plays_through_then_mutes(self):
        _, aux = self.entry("modem", "connect", 15.0)
        self.assertGreater(rms(window(aux, 0.1, 0.9)), 0.2)            # dial tone
        self.assertGreater(band(window(aux, 4.0, 5.5), 440), 0.1)       # ringback
        self.assertGreater(band(window(aux, 6.4, 8.4), 2100), 0.3)      # answer
        self.assertGreater(band(window(aux, 11.0, 13.3), 1920), 0.02)   # training
        self.assertLess(rms(window(aux, 13.6, 15.0)), 1e-5)             # muted

    # --- selection ----------------------------------------------------------

    def test_harmonics_selects_systems_and_morph_selects_entries(self):
        # MORPH at 0.5 picks a different entry in each system.
        expected = {"north-america": (941, 1336), "united-kingdom": (400,),
                    "europe": (425,), "japan": (392, 408), "blue-box": (900, 1300),
                    "specials": (913.8,)}
        for index, (system, frequencies) in enumerate(expected.items()):
            with self.subTest(system=system):
                _, aux = self.render(f"h={centre(index, 7)!r}", "m=0.5", 4800)
                amplitudes, _ = sine_fit(window(aux, 0.01, 0.1), frequencies)
                self.assertGreater(min(amplitudes), 0.2)

    def test_selection_hysteresis_and_crossfade(self):
        boundary = 5 / 21  # between key-4 (770 + 1209) and key-5 (770 + 1336)
        tokens = [f"h={centre(0, 7)!r}", f"m={boundary - 0.01!r}", 4800]
        for offset in (0.001, -0.001, 0.0015):  # jitter inside the 0.002 margin
            tokens += [f"m={boundary + offset!r}", 480]
        tokens += [2400]
        _, aux = self.render(*tokens)
        amplitudes, _ = sine_fit(aux[-2400:], (1209, 1336))
        self.assertGreater(amplitudes[0], 0.2)
        self.assertLess(amplitudes[1], 0.01)
        # Past the margin it changes, through a 5 ms crossfade with no step.
        _, aux = self.render(f"h={centre(0, 7)!r}", f"m={boundary - 0.01!r}", 4800,
                             f"m={boundary + 0.01!r}", 4800)
        largest_step = max(abs(b - a) for a, b in zip(aux[4700:5400], aux[4701:5401]))
        self.assertLess(largest_step, 0.1)
        amplitudes, _ = sine_fit(aux[-2400:], (1209, 1336))
        self.assertLess(amplitudes[0], 0.01)
        self.assertGreater(amplitudes[1], 0.2)

    # --- LINE (TIMBRE) ------------------------------------------------------

    def test_line_is_clean_at_noon_and_in_the_dead_zone(self):
        for timbre in (0.5, 0.485, 0.515):
            with self.subTest(timbre=timbre):
                main, aux = self.entry("north-america", "key-5", 0.2, f"t={timbre}")
                self.assertEqual(list(main[480:]), list(aux[480:]))

    def test_line_analog_side(self):
        # A quarter turn CCW is the 300-3400 Hz band alone: it removes most of a
        # dial tone two octaves down, and adds no harmonic.
        main, aux = self.entry("north-america", "dial", 0.5, "t=0.25", "n=36")
        self.assertLess(rms(main[4800:]), 0.4 * rms(aux[4800:]))
        main, aux = self.entry("north-america", "fsk-mark", 0.5, "t=0.25")
        self.assertLess(band(main[4800:], 3600), 0.005)
        # Fully CCW, saturation adds a third harmonic the clean channel lacks.
        main, aux = self.entry("north-america", "fsk-mark", 0.5, "t=0")
        self.assertGreater(band(main[4800:], 3600), 10 * band(aux[4800:], 3600) + 0.01)

    def test_line_digital_side(self):
        main, aux = self.entry("north-america", "key-5", 0.5, "t=1")
        self.assertLessEqual(len(set(main[4800:])), 63)  # 5-bit grid
        self.assertNotEqual(list(main[4800:]), list(aux[4800:]))
        # A little CW is band-limiting only: no quantization yet.
        main, aux = self.entry("north-america", "key-5", 0.5, "t=0.6")
        self.assertGreater(len(set(main[4800:])), 1000)
        self.assertNotEqual(list(main[4800:]), list(aux[4800:]))

    # --- TWIST (macro) ------------------------------------------------------

    def test_twist_balances_pairs(self):
        for macro, low, high in ((0.0, 0.5, 0.0), (0.5, 0.25, 0.25), (1.0, 0.0, 0.5),
                                 (0.75, 1 / 6, 1 / 3)):
            with self.subTest(macro=macro):
                _, aux = self.entry("north-america", "key-5", 0.1, f"x={macro}")
                amplitudes, _ = sine_fit(window(aux, 0.01, 0.1), (770, 1336))
                self.assertAlmostEqual(amplitudes[0], low, delta=0.005)
                self.assertAlmostEqual(amplitudes[1], high, delta=0.005)

    def test_twist_leaves_single_and_four_tone_entries(self):
        for macro in (0.0, 1.0):
            with self.subTest(macro=macro):
                _, aux = self.entry("united-kingdom", "unobtainable", 0.1, f"x={macro}")
                amplitudes, _ = sine_fit(window(aux, 0.01, 0.1), (400,))
                self.assertAlmostEqual(amplitudes[0], 0.5, delta=0.005)
                _, aux = self.entry("specials", "off-hook-howler", 0.09, f"x={macro}")
                amplitudes, _ = sine_fit(window(aux, 0.005, 0.09), (1400, 2060, 2450, 2600))
                for amplitude in amplitudes:
                    self.assertAlmostEqual(amplitude, 0.125, delta=0.005)

    # --- articulation and pitch ---------------------------------------------

    def test_unpatched_sustains_and_patched_idle_is_silent(self):
        _, aux = self.entry("north-america", "dial", 1.0)
        self.assertAlmostEqual(rms(window(aux, 0.1, 1.0)), 0.25, delta=0.01)
        _, aux = self.render(*select("north-america", "dial"), "trig=low", SR // 2)
        self.assertLess(max(abs(x) for x in aux), 1e-6)

    def test_keypress_bursts_and_restarts_the_entry(self):
        main, aux = self.render(*select("north-america", "key-5"), "trig=low", 4800,
                                "trig=high", 48, "trig=low", 9600)
        burst = window(aux, 0.1, 0.3)
        self.assertGreater(rms(burst[240:4320]), 0.1)  # sounding through 90 ms
        self.assertLess(rms(burst[5280:]), 1e-4)       # silent by 110 ms
        # The red-box quarter restarts on each strike: every burst opens with a beep.
        tokens = [*select("specials", "red-box-quarter"), "trig=low", 2400]
        for _ in range(3):
            tokens += ["trig=high", 48, "trig=low", 12000]
        _, aux = self.render(*tokens)
        for strike in range(3):
            start = 2400 + strike * 12048
            self.assertGreater(rms(aux[start + 240:start + 1440]), 0.1)

    def test_unpatching_restarts_the_cadence(self):
        _, aux = self.render(*select("united-kingdom", "ring"), 30000, "trig=low", 2400,
                             "trig=unpatched", SR)
        restart = 32400
        self.assertGreater(rms(aux[restart + 480:restart + int(0.39 * SR)]), 0.2)
        self.assertLess(rms(aux[restart + int(0.41 * SR):restart + int(0.59 * SR)]), 1e-5)

    def test_pitch_transposes_every_component(self):
        for note, ratio in ((72, 2.0), (48, 0.5)):
            with self.subTest(note=note):
                _, aux = self.entry("north-america", "key-5", 0.1, f"n={note}")
                amplitudes, residual = sine_fit(window(aux, 0.01, 0.1),
                                                (770 * ratio, 1336 * ratio))
                self.assertGreater(min(amplitudes), 0.24)
                self.assertLess(residual, 0.01)

    def test_every_entry_survives_extreme_controls(self):
        for system, entries in REFERENCE:
            for label, _ in entries:
                with self.subTest(entry=f"{system}/{label}"):
                    self.render(*select(system, label),
                                "t=0", "x=0", "n=-24", 4800, "t=1", "x=1", "n=120", 4800,
                                "trig=low", 2400, "trig=high", 48, "trig=low", 4800)

    def test_rendering_does_not_depend_on_block_size(self):
        tokens = [*select("specials", "sit-intercept"), "t=0.8", 24000]
        _, reference = self.render(*tokens, block=12)
        for block in (1, 7, 24):
            with self.subTest(block=block):
                _, aux = self.render(*tokens, block=block)
                self.assertLess(max(abs(a - b) for a, b in zip(aux, reference)), 1e-6)

    # --- package --------------------------------------------------------------

    def test_declared_scenarios_select_their_targets(self):
        scenarios = json.loads((PACKAGE / "tests/scenarios.json").read_text(encoding="utf-8"))
        self.assertEqual({s["id"] for s in scenarios}, set(SCENARIO_TARGETS))
        for scenario in scenarios:
            system, label = SCENARIO_TARGETS[scenario["id"]]
            harmonics = scenario["controls"]["harmonics"][0]
            morph = scenario["controls"]["morph"][0]
            s = min(len(REFERENCE) - 1, int(harmonics * len(REFERENCE)))
            entries = REFERENCE[s][1]
            e = min(len(entries) - 1, int(morph * len(entries)))
            with self.subTest(scenario=scenario["id"]):
                self.assertEqual((REFERENCE[s][0], entries[e][0]), (system, label))

    def test_manifest_names_the_controls(self):
        manifest = json.loads((PACKAGE / "plaits-engine.json").read_text(encoding="utf-8"))
        labels = {c["id"]: c["label"] for c in manifest["controls"]}
        self.assertEqual(labels, {"harmonics": "Tone system", "timbre": "Line",
                                  "morph": "Tone", "macro": "Twist"})
        self.assertEqual(manifest["postProcessing"],
                         {"alreadyEnveloped": True, "outGain": 1.0, "auxGain": 1.0})


if __name__ == "__main__":
    unittest.main()
