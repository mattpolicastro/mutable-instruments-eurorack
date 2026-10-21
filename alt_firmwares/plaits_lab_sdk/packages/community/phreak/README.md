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

With TRIG patched, rising edges replace every entry's free-running cadence
with a fixed 100 ms keypress, including busy and ringback. A shared contour
opens over 1 ms, holds until 96 ms, and releases over the final 4 ms. Separate
Plaits LowPassGate instances process MAIN and AUX with gain `e`, cutoff
`0.003 + 0.3*e^4`, and zero HF bleed. A final linear taper over 96–100 ms
removes filter residue; idle clears the LPGs. At TIMBRE 0 both channels match.
Unpatched audio bypasses the LPGs. The engine always reports already-enveloped
output, and the manifest declares that ownership with both output gains 1.0.
Patched idle stays silent indefinitely. Gate length does not change the burst:
only a rising edge restarts its 100 ms deadline, preserving oscillator phase
and attacking from the current contour level. HARMONICS remains live through
the usual 5 ms selection crossfade. Patching without an edge closes output
immediately; unpatching restarts the selected entry's normal on phase. Both
connection transitions discard the old burst and LPG history. Reset also clears
that state, along with all voice, cadence and pending-selection state.
Pitch transposition and bad-line treatment remain subsequent tasks.
TIMBRE, MORPH and macro are currently inactive.

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
Periodic burst tests render key 5 for 2 s and busy/ringback for 3 s at 2 Hz,
checking both channels' frequencies, 100 ms durations, and silence below
-80 dBFS after 110 ms in 5 ms windows. An independent driver reference uses
the shared LowPassGate primitive with literal contour times and frequencies;
every float sample must match within 1e-6, including attack and closing cutoff.
The key-5 reference also runs across all four partition sizes. Every engine
render in the driver must report already-enveloped output.
The timeline driver accepts `trigger=low`, `trigger=high`, `trigger=rise`, and
`trigger=unpatched` tokens alongside sample-timed selections and `reset`.
Connection tests cover seven-second patched waits, 1 ms and 1 s gates, ringback
patch/unpatch cadence restarts, and clearing a burst across cable changes.
Retrigger tests compare every sample against an independent LPG/crossfade
reference, including edges during attack, hold and release, and the key-1 to
key-2 change at 70 ms after retriggering at 50 ms. Reset with an active burst,
two voices and a queued selection must reproduce a fresh engine in each trigger
state. These cases also run with 1-, 7-, 12- and 24-sample partitions.
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
