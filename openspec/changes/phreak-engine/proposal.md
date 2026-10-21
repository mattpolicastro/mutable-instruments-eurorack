## Why

Phreak provides a playable North American telephone-signalling voice as a
self-contained Plaits Lab community package. `docs/telephone/BRIEF.md` records
Matt's decisions: recognisable telephone tones, musical transposition, triggered
keypresses, and an original adjustable bad-line sound. This change implements
those decisions and makes their acceptance observable in rendered audio.

## What Changes

- Add `alt_firmwares/plaits_lab_sdk/packages/community/phreak/`, identified as
  `community/phreak`, with original C++98 DSP, MIT licensing, manifest, tests,
  declared SDK audition scenarios, and listening notes.
- Implement the 21-entry North American tone table in the specified order,
  evenly spaced HARMONICS zones, hysteresis, and 5 ms selection crossfades.
- Provide free-running continuous tones and busy/ringback cadences, plus 100 ms
  LPG-shaped bursts when TRIG is patched.
- Reference authentic frequencies to MIDI note 60 and transpose each pair
  together. Route the clean voice to AUX and the bad-line voice to MAIN.
- Progress TIMBRE from clean through telephone band-pass, soft saturation, and
  bit/sample-rate reduction. Keep MORPH and the required fourth SDK macro inert.
- Verify behaviour using package-local host rendering and audio measurements,
  and require `plaits_lab.py check <package> --full` to pass.

Explicitly out of scope: other Flurry modes or a claim to reproduce its
undocumented distortion; modem data/protocols; additional exposed locales;
MORPH sound design; stereo reinterpretation of the outputs; changes to SDK,
browser, firmware registry, builder, or approved catalog; ARM builds, module CPU
measurement, hardware qualification, Palette submission, and publication. These
last hardware and human steps remain follow-up work, as the brief specifies.

## Capabilities

### New Capabilities

- `phreak-tones`: complete tone data, North America-only exposure, discrete
  HARMONICS selection, hysteresis, and crossfades.
- `phreak-articulation`: continuous operation, busy/ring cadences, patched-trigger
  keypress bursts, and LPG shaping.
- `phreak-pitch-outputs`: C4 reference, common-ratio pitch tracking, MAIN/AUX
  routing, and neutral unused controls.
- `phreak-bad-line`: staged TIMBRE treatment with a clean endpoint and clean AUX.
- `phreak-package`: SDK package identity, licensing, controls/output descriptions,
  declared auditions, and validation gates.

### Modified Capabilities

None.
