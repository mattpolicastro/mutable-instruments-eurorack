# Phreak articulation, pitch and treatment auditions

These 15 additional auditions are declared in `tests/scenarios.json`. Render
any SDK ID below from the repository root, saving reproducible audio in ignored
`build/`:

```sh
python3 alt_firmwares/plaits_lab_sdk/plaits_lab.py render \
  alt_firmwares/plaits_lab_sdk/packages/community/phreak \
  --scenario keypress --output build/phreak/keypress.wav
```

The WAV is 48 kHz, 16-bit, two channels: **MAIN is channel 1**, processed by
TIMBRE; **AUX is channel 2**, untreated by TIMBRE. Both retain articulation,
pitch and selection fades. Solo each channel in an audio editor to audition it
independently. At TIMBRE 0 they match within one PCM LSB. MORPH and the fourth
SDK control `macro` stay at 0.5 in every audition and have no effect in v1.
Fixed controls repeat their value at both range endpoints; brackets below
mean a linear SDK sweep. Trigger Hz 0 means unpatched.

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
| `selection-sweep` | 21 s | 60 | 0 | [0,1] | Both channels traverse dial, keys 1–9, 0, hash, star, busy, ring, A–D, FSK space (2200 Hz), FSK mark (1200 Hz), with hysteresis and 0.005 s fades. Busy/ring retain cadence. |

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

Listening observations are pending. Audition saved periodic-trigger WAVs for
keypresses: the current live-browser Strike emits `TRIGGER_UNPATCHED` on the
following block and cannot maintain the patched state required for these
bursts. ARM builds, physical Tall Dog clone CPU/audio checks, Palette submission
and publication remain deferred; host measurements do not qualify hardware.
