## Context

The module exists on Matt's `vcv-audition` branch (commits `3b5334a2`,
`924201e3`, `a3853867`), stacked on the unmerged Phreak PR, and defaults to
building Phreak. The contribution goes to `lylepmills/eurorack` as a pull
request cut from current upstream `master`, containing only
`alt_firmwares/plaits_lab_sdk/vcv/`, its SDK tests and one README link.

## Decisions

- **One package per build.** `make PACKAGE=<dir | catalog id>` is required;
  there is no default engine. `make clean` works without it. Switching packages
  rebuilds automatically: the SDK fragment is rewritten only when it changes,
  objects depend on it, and the test binary is keyed by its checksum.
- **The SDK is the source of truth.** `vcv/sources.py` imports `plaits_lab.py`
  and emits a makefile fragment from `load_package` / `builtin_package`,
  `engine_translation_units`, `engine_header_define` and the manifest's
  `postProcessing` and controls. It keeps no list of its own.
- **A copy of the stock Voice path, not the firmware Voice.** Rubato's
  `plaits/dsp/voice.h` pulls in builder-generated headers, so `lab_voice.cc`
  mirrors `voice.cc` for one engine with stock option defaults: TRIG response
  "trigger", LEVEL as level, no hold, no MODEL CV. Jack scaling follows VCV's
  Audible Instruments Plaits port. The int16 output stage matches
  `ChannelPostProcessor`; outputs are ±5 V.
- **Hidden LPG settings.** As in Audible Instruments, blue/white LPG knobs sit
  hidden on TIMBRE and MORPH; the context menu's "Edit LPG response/decay"
  swaps them in. Values are saved; the edit mode is not.
- **Self-enveloping engines.** "With TRIG patched: Engine's own envelope |
  Plaits LPG", shown only when the manifest declares `alreadyEnveloped`. In LPG
  mode the engine sees TRIG unpatched and the LPG articulates it. Default is
  the engine's own envelope, which is how the hardware behaves.
- **Identity.** Plugin slug `PlaitsLabTestBench`, name "Plaits Lab Test
  Bench", brand "Plaits Lab"; module slug `PlaitsLabEngine`. The panel title is
  the package's name. Lyle may rename it.
- **Licensing.** Source is MIT, like the SDK. Built plugins link the Rack SDK
  (GPL-3.0); the README says builds are for local use.

## Risks

- **Build platforms.** Validated on macOS arm64. Linux and Windows builds use
  the same `plugin.mk`, but are documented here rather than tested.
- **Drift.** Firmware Voice changes (option defaults, scaling) will not reach
  `lab_voice.cc` automatically. Its header comment names the mirrored source,
  and the tests pin the observable control behaviour.
