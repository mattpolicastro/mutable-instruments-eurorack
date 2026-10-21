## Context

`docs/telephone/BRIEF.md` is the product authority. Its tone plan, selection
order, pitch reference, articulation, output split, distortion progression,
neutral MORPH, and exclusions are settled decisions.

The SDK accepts community packages with a `plaits-engine.json`, package-local
C++ source, `LICENSE`, and `tests/scenarios.json`. Relevant existing interfaces
are `plaits::Engine` and `EngineParameters` in `plaits/dsp/engine/engine.h`,
`plaits::Sine` in `plaits/dsp/oscillator/sine_oscillator.h`,
`stmlib::SemitonesToRatio`, and `plaits::LowPassGate` in
`plaits/dsp/fx/low_pass_gate.h`. The SDK blank-package generator in
`alt_firmwares/plaits_lab_sdk/plaits_lab.py` supplies the package convention.

The current `render_model.cc` calls `Engine::Render` directly, writes MAIN/AUX
as the two WAV channels, and applies output gains, but does not run a host LPG.
Its scenarios support only a constant note, linear control sweeps, and periodic
triggers; `triggerHz: 0` means unpatched, not patched silence. The live
`wasm_audition.cc` bypasses its external envelope for self-enveloped engines,
but emits `TRIGGER_UNPATCHED` on the block immediately following Strike. It
cannot maintain the patched connection state needed to audition these bursts;
use SDK periodic-trigger renders and the direct driver for burst acceptance.
A browser trigger-state change belongs to a separate host follow-up.
These constraints make internal articulation and a small package-local test
driver necessary; they do not require changing the SDK.

## Goals / Non-Goals

Deliver all five capabilities with measurable host-audio acceptance, a useful
audition set, and a passing full SDK check. Keep the implementation bounded,
allocation-free, and portable C++98. Preserve all existing alternate firmware
behaviour by confining implementation to the new package.

Non-goals are those listed in the proposal. In particular, host CPU smoke
results do not qualify hardware performance. The later Tall Dog Plaits-clone
listening/CPU pass and any publication capability review are not v1 gates.

## Decisions

### Package boundaries and interfaces

Let `P = alt_firmwares/plaits_lab_sdk/packages/community/phreak`. New files:

| File | Responsibility |
| --- | --- |
| `P/plaits-engine.json` | `community/phreak`, catalog ID `phreak`, name `Phreak`, version `0.1.0`, community origin/type, SDK `plaits-engine-cpp-v1` |
| `P/LICENSE` | Complete MIT text, copyright 2026 Matt Policastro |
| `P/src/phreak_engine.h`, `P/src/phreak_engine.cc` | `plaits::PhreakEngine : Engine`; `Init`, `Reset`, no-op `LoadUserData`, and standard `Render` signature |
| `P/src/phreak_tones.h` | `ToneEntry`, `TonePlan`, the constant North American plan, bounded selection and tone-voice helpers |
| `P/src/phreak_articulation.h` | Cadence and burst counters, shared contour, two independent LPG states |
| `P/src/phreak_bad_line.h` | Band-pass, soft saturation, quantizer, and sample-hold state |
| `P/tests/render_cases.cc` | Direct engine driver for stepped controls, trigger flags, reset and block-size cases; writes samples for analysis |
| `P/tests/test_phreak.py` | Dependency-free host build/render/analysis runner using temporary output directories |
| `P/tests/scenarios.json` | Only SDK-supported scenario fields; all four controls use `[start, end]` |
| `P/README.md`, `P/AUDITION.md` | Control/table reference, commands, scenario expectations, listening procedure and results |

The manifest source root is `src`, header `phreak_engine.h`, files
`["phreak_engine.cc"]`, and class name `PhreakEngine`. Helpers are local
headers. All shipped C++ source/header files carry matching copyright and
`SPDX-License-Identifier: MIT` notices. Shared repository headers are included,
not copied; if any source is later vendored, preserve its upstream notices.
No catalog registration is needed to check or render a package by path.

Runtime storage consists of fixed-size members: two tone voices (each up to
two phase accumulators), one pending selection, counters, filters and reduction
state. `Init` uses no allocator storage; neither initialization nor rendering
allocates. Use `Sine` and `SemitonesToRatio`, not libm transcendentals. Includes
stay within the SDK allowlist; do not define repository-owned build macros.
The test driver is host tooling outside `src` and is not linked into the engine.

### Tone data and selection

`ToneEntry` contains a stable label, one/two oscillator count, reference Hz, and
on/off durations in seconds. `TonePlan` contains a locale ID, entry pointer and
count. `kNorthAmerica` is the sole production plan; the renderer consumes fields
instead of branching on locale or tone names. A test-only synthetic plan proves
the same helper can consume other data. This is extensibility infrastructure,
not a locale control or additional shipped locale.

The 21 tone scenarios in `specs/phreak-tones/spec.md` define the normative
entry order and audio expectations. This table collects their SDK IDs and
HARMONICS centres for implementation and audition:

| Index | Entry | SDK audition ID | Hz | HARMONICS |
| --- | --- | --- | --- | --- |
| 0 | Dial tone | `tone-dial` | 350 + 440 | 1/42 = 0.023809524 |
| 1 | Key 1 | `tone-key-1` | 697 + 1209 | 3/42 = 0.071428571 |
| 2 | Key 2 | `tone-key-2` | 697 + 1336 | 5/42 = 0.119047619 |
| 3 | Key 3 | `tone-key-3` | 697 + 1477 | 7/42 = 0.166666667 |
| 4 | Key 4 | `tone-key-4` | 770 + 1209 | 9/42 = 0.214285714 |
| 5 | Key 5 | `tone-key-5` | 770 + 1336 | 11/42 = 0.261904762 |
| 6 | Key 6 | `tone-key-6` | 770 + 1477 | 13/42 = 0.309523810 |
| 7 | Key 7 | `tone-key-7` | 852 + 1209 | 15/42 = 0.357142857 |
| 8 | Key 8 | `tone-key-8` | 852 + 1336 | 17/42 = 0.404761905 |
| 9 | Key 9 | `tone-key-9` | 852 + 1477 | 19/42 = 0.452380952 |
| 10 | Key 0 | `tone-key-0` | 941 + 1336 | 21/42 = 0.500000000 |
| 11 | Hash key | `tone-hash` | 941 + 1477 | 23/42 = 0.547619048 |
| 12 | Star key | `tone-star` | 941 + 1209 | 25/42 = 0.595238095 |
| 13 | Busy tone | `tone-busy` | 480 + 620 | 27/42 = 0.642857143 |
| 14 | Ringback tone | `tone-ring` | 440 + 480 | 29/42 = 0.690476190 |
| 15 | Key A | `tone-key-a` | 697 + 1633 | 31/42 = 0.738095238 |
| 16 | Key B | `tone-key-b` | 770 + 1633 | 33/42 = 0.785714286 |
| 17 | Key C | `tone-key-c` | 852 + 1633 | 35/42 = 0.833333333 |
| 18 | Key D | `tone-key-d` | 941 + 1633 | 37/42 = 0.880952381 |
| 19 | FSK space | `tone-fsk-0` | 2200 | 39/42 = 0.928571429 |
| 20 | FSK mark | `tone-fsk-1` | 1200 | 41/42 = 0.976190476 |

Clamp HARMONICS to `[0,1]`. At initialization use
`min(20, floor(21 * H))`; nominal boundaries are `i/21`, with equal-width zones
and centre `H=(i+0.5)/21`. A selected index `i` changes upward only at
`H >= (i+1)/21 + 0.002`, or downward at `H < i/21 - 0.002`.
After crossing, choose `min(20, floor(21 * H))` directly, including large jumps.
At exact downward threshold the selection stays; at exact upward threshold it
changes. No comparison extends beyond endpoint entries. The hysteresis index
tracks the latest accepted request, including a queued request during a fade;
the audible outgoing/incoming indices are separate state.

A change starts a 0.005 s linear crossfade between independently running old
and new tone voices; at 48 kHz this is 240 samples with complementary weights.
Initialize the incoming phases to zero and cadence to its on phase. Preserve
outgoing phases and cadence until its weight reaches zero. Crossfading precedes
bad-line processing and affects both outputs. During a fade keep just the latest
pending selection; finish the current fade, then fade to that selection if it
differs. Thus a final rapid request settles within 0.010 s plus one control
block, with at most four sine oscillators active. Retargeting never drops a
nonzero voice abruptly. No interpolation of frequencies between table entries.

Use amplitude 0.25 per oscillator for pairs and 0.5 for a single FSK oscillator.
Steady clean pair components have equal amplitude. Oscillators advance through
cadence-off intervals. Free-running onset and cadence edges use 0.001 s linear
ramps inside their scheduled on windows; durations include those ramps.

### Cadence, patched triggers, and LPG ownership

Unpatched dial, DTMF and FSK are continuous. Busy is 0.500 s on / 0.500 s off;
ringback is 2.000 s on / 4.000 s off, starting on after reset or entry selection.
Counters measure samples, never pitch cycles or render-call counts.

`TRIGGER_UNPATCHED` alone controls connection state. When patched, suppress the
free-running cadence for every entry and start one 0.100 s burst on each
`TRIGGER_RISING_EDGE`. A high gate is not a repeated edge; a falling edge does
not truncate a burst. Patched idle stays silent indefinitely. Retriggering
restarts the deadline at the new edge without resetting oscillator phase and
ramps from the current envelope level. HARMONICS remains live during a burst.
Patching without an edge closes current output within 0.005 s; unpatching starts
the selected entry's normal on phase. Reset clears every state, including pending
selection, cadence, burst, filters, and reduction history.

Implement LPG shaping inside the package using two `plaits::LowPassGate`
instances, one shared contour and matching gain/cutoff controls. The contour
attacks over 0.001 s, holds until 0.096 s, and releases over the final 0.004 s;
map contour `e` to gain `e`, normalized cutoff `0.003 + 0.3*e^4`, and HF bleed
0. It is a brief keypress through a low-pass gate, not a gate-length note.
Apply a final linear output taper from 1 at 0.096 s to 0 at 0.100 s to remove
filter residue by the deadline; clear LPG state when idle. At TIMBRE 0 the two
channels use identical inputs and
therefore identical LPG output. Unpatched operation bypasses these LPGs.
Set `*already_enveloped = true` on every render and manifest
`postProcessing.alreadyEnveloped = true`, with both gains 1.0, so a host does
not add a second envelope. This supplies the brief's LPG behaviour even in the
SDK's direct-render path. Later hardware integration must confirm this routing.

### Pitch and outputs

Compute one ratio `stmlib::SemitonesToRatio(note - 60)` and apply it to every
active tone component, divided by `plaits::kSampleRate` for phase increments.
For extreme high notes, cap the common ratio so the highest active reference
frequency stays at or below `0.45 * sample_rate`; do not clamp pair members
independently. During a crossfade use the largest reference frequency across
both voices. Authentic tuning tests use MIDI 48, 60 and 72, below this ceiling.

Signal path: tone voices with cadence -> selection crossfade -> split into
clean AUX and bad-line MAIN -> matched burst LPGs when patched -> output.
Clean AUX excludes TIMBRE's band-pass, saturation and reduction, while retaining
the selected pitch, cadence, crossfade and articulation. MAIN equals AUX at
TIMBRE 0. MORPH and SDK `macro` are ignored across their full ranges, including
the macro midpoint. No true-stereo mode is advertised.

### Bad-line stages

Clamp TIMBRE `t` to `[0,1]`; preserve a true bypass at 0. Use continuous stage
mixes, with no random noise and no treatment state feeding AUX:

| Range | Cumulative treatment |
| --- | --- |
| `0 .. 1/3` | Dry/wet mix `3*t` into a 300 Hz high-pass followed by a 3400 Hz low-pass; both second-order SVFs, Q approximately 0.707, using stmlib's algebraic frequency approximation |
| `1/3 .. 2/3` | Fully filtered signal; saturation wet mix `u=3*t-1`, drive `d=1+7*u`, odd soft curve `0.8*(d*x)/(1+abs(d*x))` |
| `2/3 .. 1` | Fully filtered/saturated signal; reduction wet mix `v=3*t-2`, signed symmetric quantization from 12 to 5 bits and sample hold from 1 to 8 samples (48 kHz to 6 kHz effective updates) |

For reduction, choose bits `12-floor(7*v)` and hold length `1+floor(7*v)`;
round to nearest multiples of `2/(2^bits-1)` with symmetric clipping to `[-1,1]`.
The discrete resolution changes are intentional texture. Smooth changing stage
mix/drive targets over 0.005 s; static settings settle before measurement.
At exact 1/3 only filtering is active; at exact 2/3 saturation is fully active
and reduction is bypassed. At 1 quantized MAIN holds each value for eight samples
in unpatched operation. Fixed cutoffs do not transpose with FREQUENCY.

### Verification and audition

Acceptance audio defaults: 48,000 Hz, SDK block size 12 samples (`plaits::kBlockSize`), note 60,
TIMBRE 0, MORPH/macro 0.5, TRIG unpatched, both output gains 1.0. For spectra
use steady on windows excluding the first 0.020 s and all edges; estimate
frequency with sinusoidal fitting/Goertzel or equivalent, within 1 Hz at note
60 and within max(1 Hz, 0.1%) for transposed tones. Check equal pair magnitudes
within 0.5 dB and clean undesired components below -40 dBc. FSK has one component.
For cadence use 0.010 s RMS windows and threshold 10% of on-state RMS, with
0.010 s timing tolerance. For bursts use 0.005 s windows: active duration
0.100 +/- 0.010 s and RMS below -80 dBFS after 0.110 s. Compare floating-point
buffers within 1e-6 or rendered PCM within one 16-bit LSB. Timing tolerance for
control acceptance is one render block; fade duration tolerance is one sample.

`tests/test_phreak.py` compiles/runs the driver and analyses rendered channels.
Add fixtures alongside each implementation increment. Use direct block-driven
events for boundary jitter, rapid reselection, patched silence, gate lengths,
retriggering, and variable block sizes; these cannot be represented by the
current SDK JSON. These cases remain host-automatable, not manual exceptions.
Use fixed 12-sample blocks for SDK parity and partitions of 1/7/12/24 samples for
sample-counter tests, with events at identical sample times. Boundary tests
construct exact thresholds using the same float arithmetic as the engine and
test adjacent representable values as well, avoiding decimal-rounding ambiguity.

`tests/scenarios.json` declares fixed auditions for every table entry, separate
full cadence renders, keypresses, pitch examples, and distortion examples as
specified in `phreak-package/spec.md`. Keep exact measurements in Python and
`AUDITION.md`, not invented JSON schema fields. SDK full checks enforce basic
audio health but do not validate tone identity or cadence; run both suites.
Additionally compile package translation units with `-std=c++98 -pedantic-errors`
because the SDK host renderer itself uses C++11.

Required implementation commands from repository root:

```sh
python3 alt_firmwares/plaits_lab_sdk/packages/community/phreak/tests/test_phreak.py
python3 alt_firmwares/plaits_lab_sdk/plaits_lab.py check alt_firmwares/plaits_lab_sdk/packages/community/phreak --full
```

Put all generated binaries/WAVs/build output in temporary or already-ignored
directories. For this proposal-only change validate document structure and
scenario/task coverage; there is no engine yet to run. For subsequent package
work the repository host test suite remains applicable using the pinned AMD64
container. The brief explicitly defers ARM builds, including both firmware
layouts in the general contributor guide, until the hardware follow-up; do not
claim those builds or module timing were validated by this change.

Human verification: listen to the saved SDK renders for recognisable telephone
character, switching smoothness, and useful bad-line progression; record actual
observations without claiming a Flurry match. Browser continuous-control interaction needs a human browser listening check;
its current Strike limitation is documented above. Physical jack/knob calibration, output levels and CPU headroom on the Tall
Dog clone require their respective host/hardware and remain later checks.

## Risks / Trade-offs

- Internal LPG ownership makes rendered bursts testable and consistent, but the
  fixed contour intentionally does not expose the host's configurable LPG decay.
  Firmware integration needs a later listening check for double enveloping.
- Crossfades briefly contain both tone identities and a bounded pending request
  can lag fast CV by up to 10 ms. This trades immediate hard switching for
  continuity and fixed memory/CPU cost.
- 21 narrow zones need hysteresis small enough to preserve access. The explicit
  0.002 margin and all-boundary tests make this reproducible.
- High-note ratio limiting preserves pairs but stops octave tracking near
  Nyquist. The documented ceiling is outside normal reference auditions.
- Band-pass and nonlinear colour are an original interpretation. Numeric tests
  protect stage order and routing; a listener must judge the musical result.
- Host sanitizers and CPU smoke checks do not establish embedded flash or CPU
  budgets. Before approved-catalog admission, a later change must review Fast FM,
  linear TZFM and native hard sync and record exact coverage in
  `engineCapabilityReview.reviewed`; this draft makes no qualification claims.
