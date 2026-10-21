# Phreak validation and listening notes

Run from the repository root with Python 3 and a host C++ compiler (`CXX`
selects the compiler for package tests). The manifest and all 37 auditions are
local; no catalog registration, network, submission or hardware is required.
Generated WAVs and binaries belong in ignored `build/` or temporary directories.

Render one audition:

```sh
mkdir -p build/phreak
python3 alt_firmwares/plaits_lab_sdk/plaits_lab.py render \
  alt_firmwares/plaits_lab_sdk/packages/community/phreak \
  --scenario keypress --output build/phreak/keypress.wav
```

Render every declared audition, including all 16 DTMF symbols, both FSK tones,
full busy/ring cycles, keypresses and treatment examples:

```sh
python3 - <<'PY_RENDER'
import json
from pathlib import Path
import subprocess
import sys

package = Path("alt_firmwares/plaits_lab_sdk/packages/community/phreak")
output = Path("build/phreak")
output.mkdir(parents=True, exist_ok=True)
for scenario in json.loads((package / "tests/scenarios.json").read_text()):
    subprocess.run([
        sys.executable, "alt_firmwares/plaits_lab_sdk/plaits_lab.py", "render",
        str(package), "--scenario", scenario["id"],
        "--output", str(output / (scenario["id"] + ".wav")),
    ], check=True)
PY_RENDER
```

The WAV is 48 kHz, 16-bit, two channels: **MAIN is channel 1**, processed by
TIMBRE; **AUX is channel 2**, untreated by TIMBRE. Both retain articulation,
pitch and selection fades. Solo each channel in an audio editor to audition it
independently. At TIMBRE 0 they match within one PCM LSB. MORPH and the fourth
SDK control `macro` stay at 0.5 in every audition and have no effect in v1.
Fixed controls repeat their value at both range endpoints; brackets below
mean a linear SDK sweep. Trigger Hz 0 means unpatched.

The 21 fixed-tone auditions use note 60, TIMBRE 0, MORPH/macro 0.5 and
unpatched TRIG. Each lasts 2 s except `tone-busy` (4 s, four cycles) and
`tone-ring` (12 s, two cycles). Hz and timing apply to both channels:

| Index | Entry | SDK ID | HARMONICS centre | Hz at MIDI note 60 | Unpatched timing |
| --- | --- | --- | --- | --- | --- |
| 0 | Dial tone | `tone-dial` | 1/42 = 0.023809524 | 350 + 440 | Continuous |
| 1 | Key 1 | `tone-key-1` | 3/42 = 0.071428571 | 697 + 1209 | Continuous |
| 2 | Key 2 | `tone-key-2` | 5/42 = 0.119047619 | 697 + 1336 | Continuous |
| 3 | Key 3 | `tone-key-3` | 7/42 = 0.166666667 | 697 + 1477 | Continuous |
| 4 | Key 4 | `tone-key-4` | 9/42 = 0.214285714 | 770 + 1209 | Continuous |
| 5 | Key 5 | `tone-key-5` | 11/42 = 0.261904762 | 770 + 1336 | Continuous |
| 6 | Key 6 | `tone-key-6` | 13/42 = 0.309523810 | 770 + 1477 | Continuous |
| 7 | Key 7 | `tone-key-7` | 15/42 = 0.357142857 | 852 + 1209 | Continuous |
| 8 | Key 8 | `tone-key-8` | 17/42 = 0.404761905 | 852 + 1336 | Continuous |
| 9 | Key 9 | `tone-key-9` | 19/42 = 0.452380952 | 852 + 1477 | Continuous |
| 10 | Key 0 | `tone-key-0` | 21/42 = 0.500000000 | 941 + 1336 | Continuous |
| 11 | Hash (#) | `tone-hash` | 23/42 = 0.547619048 | 941 + 1477 | Continuous |
| 12 | Star (*) | `tone-star` | 25/42 = 0.595238095 | 941 + 1209 | Continuous |
| 13 | Busy tone | `tone-busy` | 27/42 = 0.642857143 | 480 + 620 | 0.5 s on / 0.5 s off |
| 14 | Ringback tone | `tone-ring` | 29/42 = 0.690476190 | 440 + 480 | 2 s on / 4 s off |
| 15 | Key A | `tone-key-a` | 31/42 = 0.738095238 | 697 + 1633 | Continuous |
| 16 | Key B | `tone-key-b` | 33/42 = 0.785714286 | 770 + 1633 | Continuous |
| 17 | Key C | `tone-key-c` | 35/42 = 0.833333333 | 852 + 1633 | Continuous |
| 18 | Key D | `tone-key-d` | 37/42 = 0.880952381 | 941 + 1633 | Continuous |
| 19 | FSK space | `tone-fsk-0` | 39/42 = 0.928571429 | 2200 | Continuous |
| 20 | FSK mark | `tone-fsk-1` | 41/42 = 0.976190476 | 1200 | Continuous |

Busy sounds in [0,0.5), [1,1.5), [2,2.5), [3,3.5) s; intervening half-seconds
are silent. Ringback sounds in [0,2) and [6,8) s; [2,6) and [8,12) s are silent.
Onset and cadence edges have 0.001 s ramps inside the on windows.

The 15 additional auditions use these settings:

| SDK ID | Duration | Note | Trigger Hz | HARMONICS | TIMBRE | Measurable expectation |
| --- | --- | --- | --- | --- | --- | --- |
| `keypress` | 3 s | 60 | 2 | 11/42 | 0 | Six 0.100 s LPG bursts of 770+1336 Hz, 0.500 s apart on both channels. |
| `busy-keypress` | 3 s | 60 | 2 | 27/42 | 0 | Six 0.100 s LPG bursts of 480+620 Hz, overriding busy cadence. |
| `ring-keypress` | 3 s | 60 | 2 | 29/42 | 0 | Six 0.100 s LPG bursts of 440+480 Hz, overriding ring cadence. |
| `dial-low` | 2 s | 48 | 0 | 1/42 | 0 | Continuous 175+220 Hz on both channels. |
| `dial-high` | 2 s | 72 | 0 | 1/42 | 0 | Continuous 700+880 Hz on both channels. |
| `dtmf-high` | 2 s | 72 | 0 | 11/42 | 0 | Continuous 1540+2672 Hz on both channels. |
| `fsk-high` | 2 s | 72 | 0 | 39/42 | 0 | Continuous single 4400 Hz tone on both channels. |
| `band-low` | 2 s | 24 | 0 | 41/42 | 1/3 | 150 Hz MAIN at least 10 dB below clean AUX. |
| `band-high` | 2 s | 84 | 0 | 39/42 | 1/3 | 8800 Hz MAIN at least 10 dB below clean AUX. |
| `band-pass` | 2 s | 60 | 0 | 41/42 | 1/3 | 1200 Hz MAIN within 3 dB of clean AUX; no added harmonic above -40 dBc. |
| `saturated` | 2 s | 60 | 0 | 41/42 | 2/3 | MAIN retains 1200 Hz; its 3600 Hz odd harmonic relative to the fundamental is at least 6 dB stronger than in `band-pass`. AUX stays clean. |
| `crushed` | 2 s | 60 | 0 | 41/42 | 1 | MAIN lies on the signed 5-bit grid k*2/31 within one PCM LSB, with eight-sample holds (6000 updates/s) and spectral images. AUX stays clean at 1200 Hz. |
| `bad-line-sweep` | 6 s | 60 | 0 | 11/42 | [0,1] | MAIN progresses through filtering (0–2 s), saturation (2–4 s), then reduction (4–6 s); AUX remains 770+1336 Hz throughout. |
| `bad-line-return` | 6 s | 60 | 0 | 11/42 | [1,0] | MAIN reverses that progression: reduction, saturation, then filter mix returning toward clean; AUX remains 770+1336 Hz throughout. |
| `selection-sweep` | 21 s | 60 | 0 | [0,1] | 0 | Both channels traverse dial, keys 1–9, 0, hash, star, busy, ring, A–D, FSK space (2200 Hz), FSK mark (1200 Hz), with hysteresis and 0.005 s fades. Busy/ring retain cadence. |

Measure spectra in steady on windows, excluding the first 0.020 s and all
selection/cadence/LPG edges. Authentic note-60 frequencies must be within 1 Hz;
transposed frequencies within max(1 Hz, 0.1%). Clean pair amplitudes must agree
within 0.5 dB, with undesired components below -40 dBc. The package's sine-fit
residual checks also reject extra tones in the single-tone FSK auditions.

All keypresses start at 0, 0.5, 1, 1.5, 2 and 2.5 s. Use 0.005 s RMS windows
and a threshold of 10% of steady burst RMS: durations must be 0.100 ± 0.010 s,
with RMS below -80 dBFS after 0.110 s until the next trigger. The matched LPGs
open over 0.001 s, hold through 0.096 s, then close in brightness and amplitude
by 0.100 s. Automated checks compare the full waveform to the existing LPG
reference, including the final taper, within one PCM LSB.

The telephone filter is fixed at 300–3400 Hz and does not transpose. Saturated
MAIN must remain unclipped with absolute DC mean below 0.01 full scale; it has
no enforced eight-sample holds. Sweep mixes and drive follow 0.005 s smoothing,
with intentional discrete bit-depth/hold-length steps only in the upper third.
Both sweeps keep finite bounded output and AUX matches a constant-clean
reference within one PCM LSB. Each SDK sweep starts from a fresh engine; the
separate direct-driver tests cover a continuous out-and-back sweep plus a
0.100 s clean settling tail.

In `selection-sweep`, entry i begins at the first 12-sample control block whose
HARMONICS reaches i/21 + 0.002, approximately i + 0.042 s (i=1…20). Control
acceptance tolerance is one block; linear fades last 240 samples at 48 kHz,
within one sample. Busy starts its 0.500 s on / 0.500 s off cycle on entry.
Ring starts its 2 s on / 4 s off cycle, but this sweep leaves ring after about
1 s, before its off phase. Use the existing `tone-busy` (4 s) and `tone-ring`
(12 s) auditions to hear complete cycles. Cadence measurements use 0.010 s
RMS windows, a 10%-of-on-RMS threshold and ±0.010 s edge tolerance.

Run the package tests to validate SDK schema/settings and measure the actual
declared WAVs using the existing spectral, cadence, LPG and fade helpers:

```sh
python3 -B -m unittest discover \
  -s alt_firmwares/plaits_lab_sdk/packages/community/phreak/tests -p 'test_*.py'
python3 alt_firmwares/plaits_lab_sdk/plaits_lab.py check \
  alt_firmwares/plaits_lab_sdk/packages/community/phreak --full
```

Local validation record, 2026-10-21, task 6.3 working tree: macOS arm64,
Python 3.14.6, Apple clang 21.0.0. These are development results; the acceptance
harness reruns its own checks.

| Check | Actual result |
| --- | --- |
| Package unittest suite above | Passed: 60 tests, including both task 6.3 documentation scenarios and spectral/timing/routing checks. |
| SDK `check --full` above | Passed: all 37 scenarios, host compilation, sanitizers and audio health. Host CPU smoke comparison passed (13.1 ns/sample versus 95.0 for stock two-op-fm); these timings do not predict module performance. |
| Documented batch render and channel split | Passed: 37 saved WAVs and 74 mono files; each mono file has the expected duration and preserves its source channel's PCM samples exactly. |
| Repository pinned AMD64 container host suite | Pending: attempted the contributor-guide command, but sandbox access to the Docker socket was denied before tests could start. |

For separate-channel playback, split the saved WAVs without mixing or
normalizing. This uses only Python's standard library and preserves each
channel's 16-bit samples and level:

```sh
python3 - <<'PY_SPLIT'
from pathlib import Path
import wave

output = Path("build/phreak/channels")
output.mkdir(parents=True, exist_ok=True)
for source in sorted(Path("build/phreak").glob("*.wav")):
    with wave.open(str(source), "rb") as audio:
        assert (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) == (2, 2, 48000)
        frames = audio.readframes(audio.getnframes())
    for channel, label in enumerate(("main", "aux")):
        mono = b"".join(frames[i:i + 2] for i in range(channel * 2, len(frames), 4))
        with wave.open(str(output / (source.stem + "-" + label + ".wav")), "wb") as audio:
            audio.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
            audio.writeframes(mono)
PY_SPLIT
```

Open the `*-main.wav` and `*-aux.wav` files sequentially in a WAV player, or
split the original into mono tracks in an editor and solo one at a time.
Do not sum them or judge the original as a stereo scene. Keep playback gain
fixed when comparing treatment to AUX. On macOS, for example:

```sh
afplay build/phreak/channels/crushed-main.wav
afplay build/phreak/channels/crushed-aux.wav
```

Listen to every `tone-*` file on both channels: record telephone recognition,
DTMF distinctions, the busy/ring silences, and the single-tone space/mark sound.
Then listen to `keypress`, `busy-keypress` and `ring-keypress` for brief LPG
openings/closings and silence between hits. Compare `selection-sweep` on each
channel for switching smoothness or clicks; its short ring segment cannot
replace the 12 s ringback audition. Compare `band-pass`, `saturated`, `crushed`
and both bad-line sweeps against their AUX channels for progressive narrowing,
soft grit and digital texture. These are listening prompts, not observations or
a claim to reproduce Flurry. Also listen to the pitch and stopband examples.

Listening log (2026-10-21): **pending**. This implementation session has no
audio-listening access; automated sample measurements are not listening.
Record listener/date, source revision, scenario IDs, playback device/player,
channel, and time offsets when completing each row; replace pending only with
actual observations, including defects or uncertainty.

| Listening check | Status | Actual observations / listener / date / setup |
| --- | --- | --- |
| Dial, every DTMF key, busy, ringback, both FSK tones: recognition on MAIN and AUX | Pending | — |
| Keypresses: LPG character, silence and cadence override on MAIN and AUX | Pending | — |
| Selection sweep: switching smoothness on MAIN and AUX | Pending | — |
| Bad-line stages and sweeps: character on MAIN, clean AUX comparison | Pending | — |
| Pitch and band-edge examples: transposition and attenuation | Pending | — |
| Live-browser continuous controls: interaction and listening | Pending | — |

Audition saved periodic-trigger WAVs for keypresses: the current live-browser Strike emits `TRIGGER_UNPATCHED` on the
following block and cannot maintain the patched state required for these
bursts. Strike returns to free-running operation instead of preserving patched
idle; it cannot validate burst duration or post-burst silence. Use saved SDK
periodic-trigger renders and the direct-driver tests for those checks. A browser
trigger-state fix is separate follow-up work.

Deferred gates, not completed by host validation:

| Gate | Status and required follow-up |
| --- | --- |
| ARM compilation and both firmware layouts | Deferred to hardware follow-up, including experimental and stock layouts (stock uses `PLAITS_STEREO_ALL=0`). |
| Physical Tall Dog clone CPU/audio checks | Deferred: measure worst-case CPU headroom, listen to MAIN/AUX, check physical jack/knob calibration and output levels, and confirm internal LPG ownership does not cause double enveloping. |
| Palette submission | Deferred; no package has been submitted by this task. |
| Approved catalog and publication | Deferred: hardware probe measurement and listening, maintainer review, and explicit Fast FM, linear TZFM and native hard sync review with `engineCapabilityReview.reviewed` coverage are still required. |

Host sanitizer, spectral/timing and CPU smoke results do not qualify hardware
or establish flash, RAM or real-time CPU budgets. They are not hardware approval.
