# Phreak

A Plaits Lab community package (`community/phreak`, version `0.1.0`).
HARMONICS selects the 21-entry North American telephone tone table, using
`min(20, floor(21 * H))` after clamping H to [0, 1] on the first render after
Init or Reset. Each entry's centre is `(index + 0.5) / 21`. Once index `i` is
selected, it stays until H reaches `(i + 1) / 21 + 0.002` upward or falls
strictly below `i / 21 - 0.002` downward, where those neighbors exist.
Crossing a threshold selects the current nominal zone directly, including
large jumps. Selection changes use a 5 ms (240-sample) linear crossfade on
both outputs. The outgoing voice keeps running while the incoming voice starts
from zero phase; complementary weights include fully outgoing and fully incoming
endpoints. During a fade only the latest accepted request is retained. The fade
finishes before another starts, so rapid requests settle within 10 ms plus one
control block, with at most two tone voices active. Reset clears both voices,
the fade, pending selection, and hysteresis history.

Both outputs render the selected reference-Hz sines: 0.25 per component for
pairs, 0.5 for single-tone FSK. Dial, DTMF and FSK sustain continuously;
busy runs 0.5 s on / 0.5 s off and ringback runs 2 s on / 4 s off. Each voice
counts elapsed samples independently, starting on at selection or Reset.
Onset and cadence edges use 1 ms linear ramps (48 sample intervals) inside the
on intervals, with oscillators advancing through silence. The opening reaches
unity at sample 48 and the closing reaches zero at the first off sample;
neither ramp changes the scheduled cadence. The outgoing voice keeps its cadence
during a selection fade. Frequency and cadence come from the tone descriptor;
the sole production plan remains the 21-entry North American table.
Pitch transposition, trigger articulation and bad-line treatment remain
subsequent tasks. TIMBRE, MORPH and macro are currently inactive.

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
on AUX. Fresh renders check all 20 exact boundaries and clamped endpoints;
stepped renders check every adjacent pair with 20 ms jitter/reversal dwells,
exact hysteresis thresholds and adjacent floats, resets, and nonadjacent jumps.
Crossfade tests compare both channels against complementary mixtures of
separately rendered voices with a maximum float residual of 1e-6. Sample-timed
requests cover adjacent changes, direct dial/FSK jumps, rapid requests and
pending-target cancellation/reversal. Reset during either fade must match a
fresh engine, including subsequent selection changes. These cases run with
1-, 7-, 12- and 24-sample partitions to check sample-based timing.
Cadence tests cover 3 s continuous renders, four complete busy cycles, two
complete ring cycles, 1 ms edge ramps, phase continuity through silence, and
selection/reset restarts at notes 48/72 with identical sample-timed events in
every partition size. Pitch transposition itself remains task 4.1. A test-only
400+450 Hz descriptor with 0.25/0.75 s cadence exercises the unchanged helper
without adding a production locale or control.
Set `CXX` to choose the compiler. Shared repository headers use a trailing enum comma and are
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
