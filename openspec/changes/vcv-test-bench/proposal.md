## Why

The Plaits Lab SDK auditions a package in the browser (`dev`) and renders
declared scenarios (`render`), but neither lets an author patch the engine:
sequence it, feed it CV, or hear TRIG patched. Lyle (Rubato) welcomed a
single-engine VCV Rack test bench for authors as an SDK contribution on
2026-10-21. He also asked that nobody publish a port that loads full Palette
configurations, because his paid VCV Palette covers that. This change
contributes the single-engine module Matt built while auditioning Phreak,
made generic and kept clear of Palette's ground.

## What Changes

- Add `alt_firmwares/plaits_lab_sdk/vcv/`: a VCV Rack 2 plugin that builds one
  Plaits Lab package (directory or built-in catalog ID) into one module.
  The SDK supplies the package's sources, engine class and post-processing.
- Mirror the firmware Voice's stock control path for that one engine: jack
  scaling, TRIG states and delay, accent from LEVEL, the internal decay
  envelope's modulation, the low-pass gate and output stage. Render at 48 kHz
  in 12-sample blocks and resample to Rack's rate.
- Keep the LPG's response and decay as hidden settings, edited through the
  context menu as the hardware's button-hold does. For self-enveloping engines,
  offer a setting to strike them with Plaits' LPG instead of their own envelope.
- Label the panel and tooltips with the package's own control names.
- Add Rack-free tests of the voice (`make test`) and SDK unit tests of the
  build glue, and document building and installing on macOS, Linux and Windows.

Explicitly out of scope: loading Palette configurations; more than one engine
per build; banks or model switching; Rubato's firmware options (gate and
velocity TRIG responses, LEVEL to decay, hold, MODEL CV, linear TZFM, fast FM,
stereo, Drift); polyphony; VCV Library distribution; prebuilt binaries; hardware
CPU or flash estimates; and any Phreak-specific code.
