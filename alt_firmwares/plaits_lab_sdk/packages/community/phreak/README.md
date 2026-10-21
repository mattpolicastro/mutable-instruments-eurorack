# Phreak

A Plaits Lab community package (`community/phreak`, version `0.1.0`).
This initial scaffold renders a continuous placeholder sine at the MIDI note
on both outputs. All four controls are inactive. Telephone tones, selection,
articulation and bad-line treatment will arrive in subsequent tasks.

From your eurorack checkout:

```sh
python3 alt_firmwares/plaits_lab_sdk/packages/community/phreak/tests/test_phreak.py
python3 alt_firmwares/plaits_lab_sdk/plaits_lab.py check alt_firmwares/plaits_lab_sdk/packages/community/phreak --full
```

The package tests check identity, SDK source/license policy, and compile every
package translation unit with `-std=c++98 -pedantic-errors`. Set `CXX` to choose
the compiler. Shared repository headers use a trailing enum comma and are
included with `-isystem`; strict C++98 diagnostics apply to package source.
The full SDK check renders the declared `smoke` scenario with
sanitizers. Both commands keep generated objects, binaries and WAVs in temporary
directories and require no catalog registration.

The original package source is MIT licensed, copyright 2026 Matt Policastro;
see `LICENSE` and the matching source notices. Shared Plaits/stmlib headers are
included from the repository, with their upstream notices intact; no upstream
DSP source is vendored here.

Hardware builds, CPU/audio qualification, listening, submission and publication
remain pending. Host smoke validation does not establish hardware performance.
