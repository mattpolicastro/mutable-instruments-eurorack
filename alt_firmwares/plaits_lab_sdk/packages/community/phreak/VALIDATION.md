# Phreak host validation — task 6.4

Run date: 2026-10-21. Scope: the completed `community/phreak` package.
Local environment: macOS arm64, Python 3.14.6, Apple clang 21.0.0
(`clang-2100.0.123.102`). Commands below run from the repository root.
Local results are contributor evidence; the acceptance harness reruns its own
checks independently.

## Package commands and results

```sh
mkdir -p build/phreak-validation
python3 -B alt_firmwares/plaits_lab_sdk/packages/community/phreak/tests/test_phreak.py
python3 -B alt_firmwares/plaits_lab_sdk/plaits_lab.py check \
  alt_firmwares/plaits_lab_sdk/packages/community/phreak --full
c++ -std=c++98 -pedantic-errors -DTEST -D_USE_MATH_DEFINES \
  -isystem . -I alt_firmwares/plaits_lab_sdk/packages/community/phreak/src \
  -c alt_firmwares/plaits_lab_sdk/packages/community/phreak/src/phreak_engine.cc \
  -o build/phreak-validation/phreak_engine.o
```

| Gate | Result |
| --- | --- |
| Complete package regression suite | PASS, exit 0: 61 tests in 76.815 s on the final rerun; no failures or skips. |
| SDK `check --full` | PASS, exit 0: metadata, source/license policy, host compilation, ASan/UBSan, all 37 declared scenarios, audio health and host CPU smoke check. |
| Explicit C++98 translation-unit compile | PASS, exit 0; object output confined to ignored `build/phreak-validation/`. |
| Focused `tests/test_phreak.py PackageTests` rerun | PASS, exit 0: 4 tests, including full-check cleanup and licensing/portability. |

The full SDK run reported peaks 0.4965–0.6451, RMS 0.1072–0.4615 and
absolute DC no greater than 0.00020 across the 37 scenarios (including
`smoke`). The SDK renderer rejects non-finite float samples before PCM
conversion. Host CPU smoke measurement: 12.7 ns/sample versus 92.1 ns/sample
for stock two-op FM, reported as 0.1x. This is a host smoke measurement only.

Traceable regression coverage:

- `phreak-package/repeatable-full-validation-and-listening-notes/host-acceptance-run`:
  `PackageTests.test_full_host_acceptance` invokes the actual SDK `--full`
  command, requires a result for every declared scenario plus sanitizer and
  CPU smoke results, checks SDK temporary-directory cleanup, and compares
  package file hashes before/after. Direct-driver patched-idle, jitter/stepped
  selection, and retrigger tests also carry this scenario ID; existing spectral,
  timing, routing and transition assertions remain intact.
- `phreak-package/sdk-compatible-licensing-and-source/licensing-and-portability-gate`:
  `PackageTests.test_licensing_and_portability` checks full MIT text, manifest
  license, 2026 Matt Policastro notices and matching SPDX tags on all shipped
  C++ files, including the host driver. It invokes unchanged SDK source/include
  policy, rejects unqualified/C libm transcendental calls and BufferAllocator
  allocations in production source, and explicitly compiles every manifest
  translation unit with `-std=c++98 -pedantic-errors` into a temporary directory.

Production source review confirms fixed member storage: two tone voices with
two phase/increment slots each, bounded pending selection/counters, two LPG
instances and filter/reduction state. `Init` ignores the allocator. Oscillation
and pitch use shared `Sine` and `SemitonesToRatio` helpers; no upstream code was
vendored and no production DSP changes were needed for this task.

The strict compile treats repository headers as system dependencies because
they contain a trailing enum comma extension. Package code retains strict
C++98 diagnostics. The direct-driver build separately compiles shared
`plaits/resources.cc`, whose zero-length array is an existing extension; this
does not relax the package translation-unit gate.

Initial validation found one failure in the newly added cleanup test: macOS
`xcrun` leaves its `xcrun_db` tool-discovery cache under the requested TMPDIR.
The test now checks that SDK-owned `plaits-lab-*` directories are removed and
then verifies removal of the enclosing temporary directory, which also deletes
the cache. No pre-existing test was weakened, deleted or skipped.

## Repository host suite — operator result

The operator supplied this result in task feedback because Docker is
unavailable in the agent sandbox, and instructed the agent not to run Docker.
It is recorded as operator evidence, not as an agent-executed run.

- Tree: candidate `93fd369`, plus `stm_audio_bootloader` at pinned `b376bd6`.
- Image: `mutable-eurorack-dev:local`, built from `.devcontainer/Dockerfile`
  per AGENTS.md for `linux/amd64`.
- Date/result: 2026-10-21, **PASS**, exit 0, ending
  `Synthesis engine tests passed.`

```sh
docker run --rm --platform linux/amd64 \
  -v <tree>:/workspace -w /workspace \
  mutable-eurorack-dev:local \
  bash -lc 'make -f plaits/test/makefile -j2 && ./plaits_test'
```

Operator caveat: under QEMU AMD64 emulation on Apple Silicon, GCC 11 hit three
random internal compiler errors (segfaults). The unchanged base `fe3a718`
crashes the same way; `make` was rerun incrementally until compilation completed.
The host suite does not compile community packages. This task changes nothing
under `plaits/`, `stmlib/` or `stm_audio_bootloader/`; the separate package checks
above exercise Phreak itself.

## Artifact hygiene and deferred work

Test binaries, float sample files and scenario WAVs use temporary directories;
local command logs and the explicit compile object use ignored
`build/phreak-validation/`. Artifact audit commands:

```sh
git ls-files -- alt_firmwares/plaits_lab_sdk/packages/community/phreak
git status --short --untracked-files=all
git check-ignore build/phreak-validation/phreak_engine.o \
  build/phreak-validation/package-tests-final.log
git diff --check
```

PASS: all 12 already-tracked package files are source, tests, metadata or
documentation; no generated artifacts are tracked in the package. Status
shows only the intended package test/documentation edits and new
`VALIDATION.md`; `check-ignore` confirms the object/log paths are ignored.
The diff whitespace check passes. The full-check test independently verifies
that rendering does not add or modify package files.

ARM compilation, experimental and stock firmware builds, physical Tall Dog
clone CPU/audio checks, Palette submission and publication remain deferred per
the brief. Host validation does not establish hardware approval. Actual
listening remains pending as recorded in [AUDITION.md](AUDITION.md).
