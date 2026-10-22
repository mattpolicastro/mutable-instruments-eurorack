## Purpose

Let a Plaits Lab package author patch their engine in VCV Rack 2 with Plaits'
controls and jacks, without flashing hardware, and without overlapping
Rubato's VCV Palette.

## ADDED Requirements

### Requirement: One package per build

The plugin SHALL build exactly one package, named by `PACKAGE` as a package
directory or a built-in catalog ID. Sources, engine class, user-data bank,
`alreadyEnveloped` and output gains SHALL come from the SDK, not a list kept by
the plugin. Building without `PACKAGE` SHALL fail with a message naming it,
except for `make clean`.

#### Scenario: Build a community package

- **WHEN** `make RACK_DIR=<sdk> PACKAGE=<community package dir> dist` is run.
- **THEN** a `.vcvplugin` is produced without compiler warnings, and its module
  renders that package's engine.

#### Scenario: Build a built-in by catalog ID

- **WHEN** `make RACK_DIR=<sdk> PACKAGE=chords test` is run.
- **THEN** the build resolves the built-in through `builtin_package` and the
  Rack-free tests pass.

#### Scenario: Package missing

- **WHEN** `make RACK_DIR=<sdk> dist` is run without `PACKAGE`.
- **THEN** make stops with an error naming `PACKAGE`; `make clean` still runs.

### Requirement: Firmware control path

For its one engine, the module SHALL reproduce the firmware Voice's stock
control path:
- FREQ ±4 octaves around note 60, plus V/OCT at 1 V per octave.
- FM, TIMBRE and MORPH attenuverters, using the internal decay envelope when
  TRIG is patched and the jack is not.
- HARMONICS CV.
- A 1 ms TRIG delay, and unpatched, low, rising-edge and high trigger states.
- Accent from LEVEL.
- The low-pass gate for engines that do not envelope themselves.
- The int16 output stage, then ±5 V outputs.

It SHALL render 12-sample blocks at 48 kHz, resampled to Rack's sample rate.

#### Scenario: Pitch tracking

- **WHEN** V/OCT is +1 V, or FREQ is raised 12 semitones.
- **THEN** both produce the same pitch, double the unshifted pitch.

#### Scenario: Patched trigger

- **WHEN** TRIG is patched and held low, then pulsed to 5 V.
- **THEN** the output is quiet while low and sounds after the pulse.

#### Scenario: Output range

- **WHEN** the engine renders at default controls.
- **THEN** every output sample is finite and within ±5 V.

### Requirement: Hidden LPG settings

The LPG's response and decay SHALL be saved settings with no dedicated panel
controls. The context menu SHALL offer "Edit LPG response/decay", which swaps
the TIMBRE and MORPH knobs, and their labels, for the LPG's until unticked.

#### Scenario: Decay shapes a strike

- **WHEN** the LPG articulates a strike with decay at 0 and then at 1.
- **THEN** the output 0.3 to 0.5 s after the strike is at least four times
  louder at decay 1.

### Requirement: Self-enveloping engines

When the package declares `alreadyEnveloped`, the context menu SHALL offer
"With TRIG patched: Engine's own envelope | Plaits LPG", saved with the patch
and defaulting to the engine's own envelope. In Plaits LPG mode the engine
SHALL see TRIG as unpatched and the LPG SHALL articulate it. TRIG unpatched
SHALL be always on in both modes.

#### Scenario: Strike a self-enveloping engine with the LPG

- **WHEN** a self-enveloping package runs in Plaits LPG mode with TRIG patched.
- **THEN** it is quiet while TRIG is low, sounds on a pulse, and decay
  lengthens the strike.

### Requirement: Package control names

The panel title SHALL be the package's name. Panel labels, parameter names,
tooltip descriptions and input names for HARMONICS, TIMBRE, MORPH and MACRO
SHALL use the package manifest's labels and descriptions, falling back to
Plaits' names. Values SHALL survive escaping into C strings and makefiles.

#### Scenario: Labels with awkward characters

- **WHEN** a control description contains quotes, apostrophes, `#` or `$`.
- **THEN** `sources.py` emits flags that compile and reproduce the text.

### Requirement: Scope boundary

The plugin SHALL NOT load Palette configurations, host more than one engine,
switch banks or models, or implement Rubato's firmware options. It SHALL NOT be
submitted to the VCV Library, and the repository SHALL NOT carry prebuilt
plugins.

#### Scenario: Review the contribution

- **WHEN** the pull request is reviewed.
- **THEN** it adds only `alt_firmwares/plaits_lab_sdk/vcv/`, SDK tests for its
  build glue, and a README link; no binaries are tracked.

### Requirement: Documentation and verification

`vcv/README.md` SHALL cover prerequisites (Rack SDK, `jq`, a C++ compiler),
building, testing and installing on macOS, Linux and Windows. It SHALL also
say what is and is not modelled, and the licensing of built plugins. The SDK
README SHALL link it from the audition section. SDK unit tests SHALL cover
`sources.py`, and `make test` SHALL run the voice checks without Rack.

#### Scenario: Run the checks

- **WHEN** the SDK's unit tests and `make test` (for a built-in and a
  community package) are run.
- **THEN** all pass, and the SDK's existing tests are unchanged.
