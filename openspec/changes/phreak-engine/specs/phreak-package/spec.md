## Purpose

Deliver Phreak as a self-contained, correctly licensed SDK community package
with useful declared auditions and repeatable validation.

## ADDED Requirements

### Requirement: Community package identity

The package SHALL live at
`alt_firmwares/plaits_lab_sdk/packages/community/phreak/` and SHALL validate
against the existing SDK manifest contract, with ID `community/phreak`,
catalogId `phreak`, name `Phreak`, version `0.1.0`, packageType `community`,
origin `Community`, schemaVersion 1 and SDK `plaits-engine-cpp-v1`.
Source SHALL be package-local and implement `plaits::PhreakEngine`.

#### Scenario: Validate package by path

- **WHEN** `python3 alt_firmwares/plaits_lab_sdk/plaits_lab.py check
  alt_firmwares/plaits_lab_sdk/packages/community/phreak` is run.
- **THEN** manifest, source paths and class identity validate without a
  catalog/registry edit; `source.root` is `src`, `source.header` is
  `phreak_engine.h`, and `source.files` lists `phreak_engine.cc`.

### Requirement: Controls and output descriptions

The manifest and README SHALL explain HARMONICS tone selection, TIMBRE bad-line
progression, neutral MORPH, neutral fourth `macro` control, MIDI note 60 reference
and common pitch transposition, patched/unpatched articulation, processed MAIN
and clean AUX. The manifest SHALL list the four controls in SDK order and
declare already-enveloped output with MAIN/AUX gains both 1.0.

#### Scenario: Read the control contract

- **WHEN** a contributor opens the manifest and README.
- **THEN** the controls appear as `harmonics`, `timbre`, `morph`, `macro`;
  MAIN is described as processed and AUX as untreated by TIMBRE, both with
  cadence and LPG bursts; TRIG describes 0.100 s bursts and unpatched cadence.
- **THEN** the README lists all 21 entries and their HARMONICS centre values,
  authentic Hz at note 60, busy 0.5/0.5 s and ring 2/4 s timing, and explicitly
  identifies MORPH and the fourth control as having no effect in v1.

### Requirement: SDK compatible licensing and source

The package SHALL use original MIT-licensed source with a full MIT LICENSE
naming Matt Policastro as the 2026 rights holder, matching manifest license and
per-source copyright/SPDX headers. It SHALL preserve upstream notices if source
is vendored. Production C++ SHALL compile as C++98, stay within the SDK include
allowlist, avoid dynamic allocation and hardware access, and use shared DSP
helpers instead of libm transcendentals.

#### Scenario: Licensing and portability gate

- **WHEN** the package source/license checks and a host
  `-std=c++98 -pedantic-errors` compile of the package translation units run.
- **THEN** they pass with matching `MIT` SPDX tags, full license text and
  rights-holder notices, only allowed includes, fixed-size runtime state,
  no dynamic allocation, and no libm transcendental calls.

### Requirement: Declared audio auditions

`tests/scenarios.json` SHALL declare SDK-renderable auditions using exactly
`id`, `name`, `durationSeconds`, `note`, `triggerHz`, and `controls`. The
`controls` object SHALL contain four `[start,end]` ranges. Every table entry
SHALL have a fixed-centre audition, allowing each tone class and every DTMF
symbol to be heard without moving a knob.
Unless overridden below, note SHALL be 60, triggerHz 0, TIMBRE 0 and
MORPH/macro 0.5; fixed values SHALL be repeated at both range endpoints.

#### Scenario: Every entry can be auditioned

- **WHEN** each of the 21 `tone-*` IDs listed in `phreak-tones/spec.md` is
  rendered using `plaits_lab.py render <package> --scenario <id> --output <wav>`.
- **THEN** it uses that scenario's exact centre HARMONICS (serialized with at least
  nine decimal places), MIDI note 60 and clean TIMBRE, and produces that scenario's
  frequencies within 1 Hz during its on intervals.
- **THEN** `tone-busy` lasts 4 s and presents four 0.5/0.5 s cycles;
  `tone-ring` lasts 12 s and presents two 2/4 s cycles; the remaining entries
  each last 2 s continuously, including 2200 Hz space and 1200 Hz mark.

#### Scenario: Articulation pitch and treatment auditions

- **WHEN** the additional declared scenarios below are rendered.
- **THEN** their settings and measurable expectations match this table; MAIN
  is WAV channel 1 and AUX channel 2, and each can be auditioned independently.

| SDK ID | Duration | Note | Trigger Hz | HARMONICS | TIMBRE | Expectation |
| --- | --- | --- | --- | --- | --- | --- |
| `keypress` | 3 s | 60 | 2 | 11/42 | 0 | Six 0.100 s LPG bursts of 770+1336 Hz, 0.500 s apart |
| `busy-keypress` | 3 s | 60 | 2 | 27/42 | 0 | Six 0.100 s bursts of 480+620 Hz |
| `ring-keypress` | 3 s | 60 | 2 | 29/42 | 0 | Six 0.100 s bursts of 440+480 Hz |
| `dial-low` | 2 s | 48 | 0 | 1/42 | 0 | 175+220 Hz |
| `dial-high` | 2 s | 72 | 0 | 1/42 | 0 | 700+880 Hz |
| `dtmf-high` | 2 s | 72 | 0 | 11/42 | 0 | 1540+2672 Hz |
| `fsk-high` | 2 s | 72 | 0 | 39/42 | 0 | 4400 Hz single tone |
| `band-low` | 2 s | 24 | 0 | 41/42 | 1/3 | 150 Hz MAIN at least 10 dB below AUX |
| `band-high` | 2 s | 84 | 0 | 39/42 | 1/3 | 8800 Hz MAIN at least 10 dB below AUX |
| `band-pass` | 2 s | 60 | 0 | 41/42 | 1/3 | 1200 Hz MAIN within 3 dB of AUX |
| `saturated` | 2 s | 60 | 0 | 41/42 | 2/3 | 1200 Hz fundamental plus stronger odd harmonics on MAIN |
| `crushed` | 2 s | 60 | 0 | 41/42 | 1 | MAIN 5-bit grid and 8-sample holds; AUX clean 1200 Hz |
| `bad-line-sweep` | 6 s | 60 | 0 | 11/42 | [0,1] | Filter, saturation, reduction in order; AUX 770+1336 Hz unchanged |
| `bad-line-return` | 6 s | 60 | 0 | 11/42 | [1,0] | Reverse progression; AUX 770+1336 Hz unchanged |
| `selection-sweep` | 21 s | 60 | 0 | [0,1] | 0 | Ordered tone traversal with hysteresis and 0.005 s fades; busy/ring retain cadence |

The tone tables and capability specs supply the numeric tolerances for these
auditions. `AUDITION.md` SHALL record those expectations beside the SDK IDs;
unsupported assertion/event fields SHALL not be added to SDK JSON.

### Requirement: Repeatable full validation and listening notes

The completed engine SHALL pass `plaits_lab.py check <package> --full` including
sanitizers, all declared scenarios and the host CPU smoke check. Package-local
tests SHALL independently verify frequencies, timing, routing and transitions.
Generated binaries, WAVs and build directories SHALL remain untracked.

#### Scenario: Host acceptance run

- **WHEN** `tests/test_phreak.py` and
  `python3 alt_firmwares/plaits_lab_sdk/plaits_lab.py check
  alt_firmwares/plaits_lab_sdk/packages/community/phreak --full` run from the
  repository root on the completed package.
- **THEN** both exit successfully, every declared scenario renders valid
  non-silent finite audio with acceptable DC, and temporary render/build output
  leaves no generated artifacts in the tracked tree.
- **THEN** the local tests also cover patched silence, stepped/jittering controls
  and retriggers through a direct engine driver, without a host application.

#### Scenario: Audition notes and deferred hardware checks

- **WHEN** a contributor follows `AUDITION.md` to render and listen to dial,
  every DTMF key, busy, ringback, both FSK tones, keypress and bad-line examples.
- **THEN** the instructions identify frequencies, HARMONICS values, expected
  timing and separate MAIN/AUX listening using saved renders, documenting the current
  live-browser Strike limitation, with space for actual observations of
  recognition, switching smoothness and bad-line character.
- **THEN** any unperformed listening is labelled pending; ARM builds, physical
  Tall Dog clone CPU/audio checks, Palette submission and publication remain
  explicitly deferred, without treating host validation as hardware approval.
