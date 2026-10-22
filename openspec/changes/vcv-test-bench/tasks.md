The module already exists on `vcv-audition`; these tasks port it onto
upstream `master` and make it generic. Paths are relative to
`alt_firmwares/plaits_lab_sdk/` unless stated otherwise.

## 1. Port

- [x] 1.1 Cut `sdk-vcv-test-bench` from `upstream/master` and cherry-pick the module commits (`3b5334a2`, `924201e3`, `a3853867`). Confirm only `vcv/` changed. Covers `vcv-test-bench/scope-boundary/review-the-contribution`.

## 2. Make it generic

- [x] 2.1 Require `PACKAGE` (no Phreak default), with an error naming it; let `make clean` run without it. Rename the plugin to `PlaitsLabTestBench` / "Plaits Lab Test Bench" / brand "Plaits Lab". Covers `vcv-test-bench/one-package-per-build/package-missing`.
- [x] 2.2 Remove Phreak-specific code from `tests/test_lab_voice.cc` and the README, keeping the generic voice checks: output range, pitch tracking, patched trigger, LPG decay. Covers `vcv-test-bench/firmware-control-path/pitch-tracking`, `vcv-test-bench/firmware-control-path/patched-trigger`, `vcv-test-bench/firmware-control-path/output-range`, `vcv-test-bench/hidden-lpg-settings/decay-shapes-a-strike`, `vcv-test-bench/self-enveloping-engines/strike-a-self-enveloping-engine-with-the-lpg`.

## 3. SDK tests and docs

- [x] 3.1 Add `tests/test_vcv_sources.py`: `sources.py` resolves a built-in and a community package, emits the engine class, header, gains and enveloped flag, and escapes awkward label text (quotes, `#`, `$`) so it compiles and round-trips. Covers `vcv-test-bench/package-control-names/labels-with-awkward-characters`, `vcv-test-bench/one-package-per-build/build-a-built-in-by-catalog-id`.
- [x] 3.2 Rewrite `vcv/README.md` for authors: prerequisites, build/test/install on macOS, Linux and Windows (MSYS2), what is and isn't modelled, licensing of built plugins. Link it from the SDK README's audition section. Covers `vcv-test-bench/documentation-and-verification/run-the-checks`.

## 4. Validate

- [x] 4.1 Run the SDK's unit tests; run `make test` for `chords` and for a fresh `init` community package (upstream has none with package-local source), including switching between them without a clean; build `dist` without warnings. Record the results for the PR. Covers `vcv-test-bench/one-package-per-build/build-a-community-package`, `vcv-test-bench/documentation-and-verification/run-the-checks`.
- [x] 4.2 Human: load the built module in Rack and check the panel, hidden LPG edit mode and context menu; then decide whether to push and open the PR. (Rack is not installed on the Mac Studio.)
