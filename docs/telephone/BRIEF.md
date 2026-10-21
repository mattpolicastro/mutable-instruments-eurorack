# Phreak — a telephone-tone voice for Plaits

A Plaits Lab community engine (`community/phreak`) that plays telephone signalling
tones, inspired by Intellijel Flurry's Phreakbox noise mode: selectable telephone
tones with an adjustable "bad line" treatment. Built with the Plaits Lab SDK in
`alt_firmwares/plaits_lab_sdk` (read its README and the repository AGENTS.md).

Hardware for testing: a Tall Dog Plaits clone (firmware-compatible with Plaits).
Sound goal for v1: recognisable telephone character, an original interpretation —
not a clone of Flurry, whose distortion is undocumented. Tune by ear later.

## Decisions (Matt, 2026-10-21)

- **Tone plan:** North American (Bell precise tone plan) for v1:
  - dial tone 350 + 440 Hz, continuous;
  - busy 480 + 620 Hz, 0.5 s on / 0.5 s off;
  - ringback 440 + 480 Hz, 2 s on / 4 s off;
  - DTMF keys from the standard 4×4 grid: rows 697/770/852/941 Hz, columns
    1209/1336/1477/1633 Hz (1–9, 0, *, #, A–D);
  - FSK_0 / FSK_1 as Bell 202 space/mark: 2200 Hz / 1200 Hz, single tones.

  Other locales (UK, European) should be possible later as additions to a
  data-driven tone table, without changing the engine's structure. v1 exposes
  only the North American table.
- **Selection (HARMONICS):** Flurry's documented order — dial tone, 1–9, 0, #, *,
  busy, ring, A, B, C, D, FSK_0, FSK_1 (21 entries) — spread evenly across the
  knob. Hysteresis so CV near a boundary does not chatter, and a short (about
  5 ms) crossfade when the selection changes so switching does not click.
- **Pitch (FREQUENCY / V/OCT):** the authentic frequencies sound at MIDI note 60
  (C4); other notes transpose both tones of a pair together by the same ratio.
- **Articulation:** with TRIG unpatched the selected tone sounds continuously, and
  busy/ring run their own on/off cadence. With TRIG patched, each trigger plays one
  keypress-length burst (about 100 ms) through the low-pass gate.
- **Outputs:** MAIN is the processed tone; AUX is the clean, untreated tone.
- **Distortion (TIMBRE):** a "bad phone line" sweep. From 0 (clean) upward:
  a 300–3400 Hz telephone band-pass, then soft saturation, then bit/sample-rate
  reduction at the top of the range.
- **MORPH:** neutral (no effect) in v1; chosen after listening.

## Out of scope

Flurry's other modes; a modem protocol (the FSK entries are two tones, not data);
ARM build, CPU measurement on the module, and Palette submission (hardware and
human steps after v1).
