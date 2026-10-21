#!/usr/bin/env python3
# Copyright 2026 Matt Policastro.
# SPDX-License-Identifier: MIT
"""Package gates; generated build output lives only in temporary directories."""

import importlib.util
import json
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
