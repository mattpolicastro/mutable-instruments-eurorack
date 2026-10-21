# Phreak

A Plaits Lab community package (`community/phreak`, version `0.1.0`).
HARMONICS selects the 21-entry North American telephone tone table, using
`min(20, floor(21 * H))` after clamping H to [0, 1]. Each entry's centre is
`(index + 0.5) / 21`. Both outputs currently render the selected reference-Hz
sines continuously: 0.25 per component for pairs, 0.5 for single-tone FSK.
Pitch transposition, cadence playback, trigger articulation, selection smoothing
and bad-line treatment remain subsequent tasks. TIMBRE, MORPH and macro are
currently inactive; cadence durations are stored in the table for later use.

From your eurorack checkout:

```sh
python3 alt_firmwares/plaits_lab_sdk/packages/community/phreak/tests/test_phreak.py
python3 alt_firmwares/plaits_lab_sdk/plaits_lab.py check alt_firmwares/plaits_lab_sdk/packages/community/phreak --full
```

The package tests check identity, SDK source/license policy, and compile every
package translation unit with `-std=c++98 -pedantic-errors`. They also compile
`tests/render_cases.cc` and render all 21 zone centres through the engine at
48 kHz in 12-sample blocks. Independent frequency references, sine fitting and
residual measurements check tuning, equal pair levels and unwanted components
on AUX; endpoint tests check HARMONICS clamping. Set `CXX` to choose
the compiler. Shared repository headers use a trailing enum comma and are
included with `-isystem`; strict C++98 diagnostics apply to package source.
The shared resource translation unit is compiled separately because it uses a
zero-length array extension.
The full SDK check renders the declared `smoke` scenario with
sanitizers. Both commands keep generated objects, binaries and WAVs in temporary
directories and require no catalog registration.

The original package source is MIT licensed, copyright 2026 Matt Policastro;
see `LICENSE` and the matching source notices. Shared Plaits/stmlib headers are
included from the repository, with their upstream notices intact; no upstream
DSP source is vendored here.

Hardware builds, CPU/audio qualification, listening, submission and publication
remain pending. Host smoke validation does not establish hardware performance.
