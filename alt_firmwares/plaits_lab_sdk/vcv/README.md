# Plaits Lab Audition (VCV Rack 2)

Builds one Plaits Lab package into a Rack module with Plaits' controls and
jacks, so it can be auditioned and patched without flashing hardware. `dev`'s
browser page is quicker for knob-twiddling; this is for patching, and for the
patched-TRIG behavior the page cannot reach (it never reports TRIG as patched).

## Build

You need the [Rack SDK](https://vcvrack.com/manual/PluginDevelopmentTutorial)
for your platform and `jq`.

```sh
make RACK_DIR=<Rack-SDK> dist                         # Phreak by default
make RACK_DIR=<Rack-SDK> PACKAGE=../packages/community/<name> dist
make RACK_DIR=<Rack-SDK> PACKAGE=chords dist          # a built-in, by catalog ID
make RACK_DIR=<Rack-SDK> test                         # Rack-free checks
```

`sources.py` asks the SDK for the package's sources, engine class and
`postProcessing`, so any package that passes `check` builds. One package per
build: run `make clean` before switching `PACKAGE`.

## Install

Copy `dist/PlaitsLabAudition-2.0.0-<platform>.vcvplugin` into Rack's user
plugins folder and restart Rack. On macOS with Rack 2.4 or later that is
`~/Library/Application Support/Rack2/plugins-mac-arm64/`. The module is
**Plaits Lab Engine**, under the brand **Plaits Lab**, with the package's name
on its panel. If macOS refuses to load a downloaded build, clear the quarantine
flag on the extracted folder: `xattr -dr com.apple.quarantine <folder>`.

## What it models

The firmware Voice's stock control path for a single engine (`src/lab_voice.cc`
mirrors `plaits/dsp/voice.cc`):

- FREQ is ±4 octaves around MIDI note 60; V/OCT adds 1 V per octave.
- The FM, TIMBRE and MORPH attenuverters scale their jacks, or the internal
  decay envelope when TRIG is patched and the jack is not.
- TRIG has a 1 ms delay and reports unpatched, low, rising edge and high exactly
  as the engine sees them on hardware.
- TRIG unpatched is always on. Patched, TRIG strikes Plaits' low-pass gate,
  and LEVEL sets accent and drives the gate.
- The gate's response and decay are hidden settings, as on the hardware, where
  you hold a button and turn TIMBRE and MORPH. Here, right-click → **Edit LPG
  response/decay** swaps those two knobs for blue LPG knobs until you untick it.
- For an engine that envelopes itself, like Phreak, right-click → **With TRIG
  patched** chooses **Engine's own envelope** (the default, as hardware does it)
  or **Plaits LPG**, which plays the engine untriggered and lets the gate strike
  it. The setting is saved with the patch.
- MACRO is the fourth synthesis macro, neutral at noon.

The panel and tooltips use the package's own names for HARMONICS, TIMBRE,
MORPH and MACRO, from its `plaits-engine.json`.

Jack scaling follows VCV's Plaits port (Audible Instruments). Outputs are ±5 V.
The engine renders 12-sample blocks at 48 kHz, which are resampled to Rack's
rate.

It does not model Rubato's firmware options (gate and velocity TRIG responses,
LEVEL to decay, hold-on-trigger, MODEL CV, linear TZFM, fast FM, stereo, Drift),
bank and model switching, or flash and CPU budgets. Use the builder and hardware
for those.
