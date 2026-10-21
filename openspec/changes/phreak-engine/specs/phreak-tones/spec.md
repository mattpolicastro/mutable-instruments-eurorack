## Purpose

Provide the exact North American telephone tone plan and stable, click-resistant
selection, with table-driven infrastructure for future locales.

Audio measurement convention: use 48 kHz, TIMBRE 0 and steady unpatched AUX
windows excluding cadence/crossfade edges and the first 0.020 s. Frequency
error is at most 1 Hz, pair amplitudes differ by at most 0.5 dB, and unwanted
components are below -40 dBc. HARMONICS fractions are exact zone centres;
decimals are rounded conveniences.

## ADDED Requirements

### Requirement: North American tone table

The engine SHALL expose exactly 21 North American entries in the scenario
order below at MIDI note 60. Pairs SHALL contain equal-amplitude sine components;
FSK entries SHALL contain one sine without protocol or data modulation. Clean
AUX SHALL meet the stated spectral tolerances.

#### Scenario: Dial tone

- **WHEN** the `tone-dial` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 1/42 (approximately 0.023809524).
- **THEN** its steady on-state AUX contains 350 Hz and 440 Hz, within the spectral
  tolerances above; the selected entry is index 0.

#### Scenario: Key 1

- **WHEN** the `tone-key-1` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 3/42 (approximately 0.071428571).
- **THEN** its steady on-state AUX contains 697 Hz and 1209 Hz, within the spectral
  tolerances above; the selected entry is index 1.

#### Scenario: Key 2

- **WHEN** the `tone-key-2` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 5/42 (approximately 0.119047619).
- **THEN** its steady on-state AUX contains 697 Hz and 1336 Hz, within the spectral
  tolerances above; the selected entry is index 2.

#### Scenario: Key 3

- **WHEN** the `tone-key-3` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 7/42 (approximately 0.166666667).
- **THEN** its steady on-state AUX contains 697 Hz and 1477 Hz, within the spectral
  tolerances above; the selected entry is index 3.

#### Scenario: Key 4

- **WHEN** the `tone-key-4` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 9/42 (approximately 0.214285714).
- **THEN** its steady on-state AUX contains 770 Hz and 1209 Hz, within the spectral
  tolerances above; the selected entry is index 4.

#### Scenario: Key 5

- **WHEN** the `tone-key-5` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 11/42 (approximately 0.261904762).
- **THEN** its steady on-state AUX contains 770 Hz and 1336 Hz, within the spectral
  tolerances above; the selected entry is index 5.

#### Scenario: Key 6

- **WHEN** the `tone-key-6` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 13/42 (approximately 0.309523810).
- **THEN** its steady on-state AUX contains 770 Hz and 1477 Hz, within the spectral
  tolerances above; the selected entry is index 6.

#### Scenario: Key 7

- **WHEN** the `tone-key-7` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 15/42 (approximately 0.357142857).
- **THEN** its steady on-state AUX contains 852 Hz and 1209 Hz, within the spectral
  tolerances above; the selected entry is index 7.

#### Scenario: Key 8

- **WHEN** the `tone-key-8` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 17/42 (approximately 0.404761905).
- **THEN** its steady on-state AUX contains 852 Hz and 1336 Hz, within the spectral
  tolerances above; the selected entry is index 8.

#### Scenario: Key 9

- **WHEN** the `tone-key-9` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 19/42 (approximately 0.452380952).
- **THEN** its steady on-state AUX contains 852 Hz and 1477 Hz, within the spectral
  tolerances above; the selected entry is index 9.

#### Scenario: Key 0

- **WHEN** the `tone-key-0` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 21/42 (approximately 0.500000000).
- **THEN** its steady on-state AUX contains 941 Hz and 1336 Hz, within the spectral
  tolerances above; the selected entry is index 10.

#### Scenario: Hash key

- **WHEN** the `tone-hash` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 23/42 (approximately 0.547619048).
- **THEN** its steady on-state AUX contains 941 Hz and 1477 Hz, within the spectral
  tolerances above; the selected entry is index 11.

#### Scenario: Star key

- **WHEN** the `tone-star` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 25/42 (approximately 0.595238095).
- **THEN** its steady on-state AUX contains 941 Hz and 1209 Hz, within the spectral
  tolerances above; the selected entry is index 12.

#### Scenario: Busy tone

- **WHEN** the `tone-busy` audition uses a fresh engine that
  renders for 4.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 27/42 (approximately 0.642857143).
- **THEN** its steady on-state AUX contains 480 Hz and 620 Hz, within the spectral
  tolerances above; the selected entry is index 13.

#### Scenario: Ringback tone

- **WHEN** the `tone-ring` audition uses a fresh engine that
  renders for 12.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 29/42 (approximately 0.690476190).
- **THEN** its steady on-state AUX contains 440 Hz and 480 Hz, within the spectral
  tolerances above; the selected entry is index 14.

#### Scenario: Key A

- **WHEN** the `tone-key-a` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 31/42 (approximately 0.738095238).
- **THEN** its steady on-state AUX contains 697 Hz and 1633 Hz, within the spectral
  tolerances above; the selected entry is index 15.

#### Scenario: Key B

- **WHEN** the `tone-key-b` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 33/42 (approximately 0.785714286).
- **THEN** its steady on-state AUX contains 770 Hz and 1633 Hz, within the spectral
  tolerances above; the selected entry is index 16.

#### Scenario: Key C

- **WHEN** the `tone-key-c` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 35/42 (approximately 0.833333333).
- **THEN** its steady on-state AUX contains 852 Hz and 1633 Hz, within the spectral
  tolerances above; the selected entry is index 17.

#### Scenario: Key D

- **WHEN** the `tone-key-d` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 37/42 (approximately 0.880952381).
- **THEN** its steady on-state AUX contains 941 Hz and 1633 Hz, within the spectral
  tolerances above; the selected entry is index 18.

#### Scenario: FSK space

- **WHEN** the `tone-fsk-0` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 39/42 (approximately 0.928571429).
- **THEN** its steady on-state AUX contains 2200 Hz only, within the spectral
  tolerances above; the selected entry is index 19.

#### Scenario: FSK mark

- **WHEN** the `tone-fsk-1` audition uses a fresh engine that
  renders for 2.000 s at MIDI note 60, TIMBRE 0, TRIG unpatched,
  and HARMONICS 41/42 (approximately 0.976190476).
- **THEN** its steady on-state AUX contains 1200 Hz only, within the spectral
  tolerances above; the selected entry is index 20.

### Requirement: Equal selection zones

The engine SHALL clamp HARMONICS to [0,1], divide that range into 21 equal
nominal zones, and initially select `min(20, floor(21*H))`. It SHALL select
entries discretely, without pitch interpolation between entries.

#### Scenario: Initial boundaries and endpoints

- **WHEN** fresh instances render at HARMONICS 0, 1, and each exact internal
  boundary `i/21` for i=1 through 20, at note 60 and TIMBRE 0.
- **THEN** their settled spectra identify indices 0, 20, and i respectively;
  values -0.1 and 1.1 supplied by a direct driver select 0 and 20 respectively.

### Requirement: Selection hysteresis

The engine SHALL retain index i until HARMONICS reaches `(i+1)/21 + 0.002`
upward or falls strictly below `i/21 - 0.002` downward, where those neighbors
exist. After crossing it SHALL choose the current nominal zone directly.

#### Scenario: Boundary jitter and reversal

- **WHEN** each adjacent pair is exercised at note 60 with 0.020 s dwell per
  control step, starting below boundary b=i/21, alternating b-0.001 and b+0.001
  ten times, then setting b+0.002, b-0.002, and b-0.003.
- **THEN** no jitter step changes the lower tone; b+0.002 selects the upper
  tone; b-0.002 retains it; and b-0.003 selects the lower tone, with spectra
  matching the corresponding table rows after each crossfade.

#### Scenario: Large selection jump

- **WHEN** HARMONICS jumps from 1/42 to 41/42 and later back to 1/42, with
  0.100 s between jumps, at note 60 and TIMBRE 0.
- **THEN** each change crossfades directly between dial's 350+440 Hz and
  FSK_1's 1200 Hz, without stepping through intervening entries.

### Requirement: Selection crossfade

The engine SHALL linearly crossfade outgoing and incoming tone voices over
0.005 s (240 samples at 48 kHz), preserving outgoing phase and using
complementary weights before the output split. It SHALL keep bounded state and
queue only the latest request received during an active fade.

#### Scenario: Five millisecond transition

- **WHEN** unpatched HARMONICS changes from key 1 at 3/42 to key 2 at 5/42,
  after 0.100 s at note 60 and TIMBRE 0.
- **THEN** on the next render block both outputs follow the complementary
  linear mixture of old 697+1209 Hz and new 697+1336 Hz voices for 0.005 s
  within one sample, and then contain only the new voice.
- **THEN** the first fade sample continues the outgoing waveform and the last
  meets the incoming waveform; reference-mixture residual is at most 1e-6
  in float samples or one 16-bit PCM LSB, without a hard phase discontinuity.

#### Scenario: Rapid changes settle

- **WHEN** a direct driver requests key 1, key 2, key 3 and FSK_0 at HARMONICS
  3/42, 5/42, 7/42 and 39/42, spaced 0.001 s apart, then holds FSK_0.
- **THEN** active fades finish without discarding a nonzero voice, only the
  latest pending target is retained, and AUX settles to 2200 Hz within 0.010 s
  plus one control block after the final request, with finite bounded output.

### Requirement: Locale table separation

The engine SHALL read labels, oscillator counts, reference frequencies and
cadence durations from a locale descriptor and its entries. The shipped package
SHALL expose only North America; future table additions SHALL not require
changing oscillator, selection or cadence algorithms.

#### Scenario: Table substitution without a locale control

- **WHEN** the package is inspected and its tone helper is rendered against a
  test-only alternate descriptor containing a 400+450 Hz pair with 0.250 s on /
  0.750 s off timing.
- **THEN** the unchanged helper produces those frequencies and durations,
  while the production descriptor remains the 21-entry North American table
  and neither the manifest nor any control exposes the synthetic locale.
