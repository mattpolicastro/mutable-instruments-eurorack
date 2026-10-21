## Purpose

Preserve authentic tuning at C4, musical pair transposition, and a predictable
processed MAIN / clean AUX split.

## ADDED Requirements

### Requirement: Common pitch ratio

The engine SHALL reproduce each reference frequency at MIDI note 60 and SHALL
apply the same `2^((note-60)/12)` ratio to both members of a pair and to FSK.
Below the high-frequency ceiling, measured components SHALL be within
max(1 Hz, 0.1%) of their targets. Cadence and burst times SHALL not transpose.

#### Scenario: Octave transposition

- **WHEN** unpatched dial at HARMONICS 1/42 is rendered at notes 48, 60 and 72,
  with TIMBRE 0.
- **THEN** both outputs contain respectively 175+220 Hz, 350+440 Hz and
  700+880 Hz; each pair retains the reference frequency ratio.

#### Scenario: DTMF and FSK transposition

- **WHEN** unpatched key 5 at 11/42 and FSK_0 at 39/42 are rendered at note 72,
  and FSK_1 at 41/42 is rendered at note 48, with TIMBRE 0.
- **THEN** the outputs contain respectively 1540+2672 Hz, 4400 Hz only, and
  600 Hz only; no tone is independently quantized to a musical note.

#### Scenario: High pitch ceiling preserves pairs

- **WHEN** key D at HARMONICS 37/42 is rendered unpatched at MIDI note 120,
  TIMBRE 0, and 48 kHz.
- **THEN** a common capped ratio produces 21600 Hz for the 1633 Hz component
  and `21600*941/1633` Hz for the 941 Hz component, within 0.1%, with finite
  samples and no independent component clamping.

### Requirement: Clean and processed routing

The engine SHALL send bad-line-processed audio to MAIN and untreated audio to
AUX. Both SHALL share pitch, selection, cadence and keypress articulation.
Untreated means exempt from TIMBRE processing, not exempt from articulation.

#### Scenario: Clean endpoint equality

- **WHEN** all 21 entries are rendered at note 60 and TIMBRE 0, both unpatched
  and with 2 Hz triggers, using their centre HARMONICS values.
- **THEN** MAIN and AUX match within 1e-6 in float buffers or one 16-bit PCM
  LSB, including cadence edges, keypress LPG shaping and selection crossfades.

#### Scenario: AUX independence

- **WHEN** key 5 at 11/42, note 60, is rendered in identical fresh runs with
  TIMBRE 0, 1/3, 2/3 and 1, both unpatched and with 2 Hz triggers.
- **THEN** all AUX renders match within 1e-6 or one PCM LSB with 770+1336 Hz
  on-state components, while MAIN changes with the treatment and both channels
  retain the same burst schedule.

### Requirement: Neutral unused controls

MORPH and the SDK fourth control `macro` SHALL have no effect throughout [0,1]
in v1; the macro midpoint SHALL therefore be neutral.

#### Scenario: Neutral control sweeps

- **WHEN** key 5 at HARMONICS 11/42, note 60 and TIMBRE 0.5 is rendered for
  2.000 s, once with MORPH/macro 0.5 and again sweeping each independently
  from 0 to 1, with otherwise identical trigger events and initial state.
- **THEN** both output buffers match their corresponding baseline channels
  within 1e-6 or one 16-bit PCM LSB in unpatched and triggered operation.
