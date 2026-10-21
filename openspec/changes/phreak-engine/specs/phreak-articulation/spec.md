## Purpose

Make telephone cadence and keypress articulation audible and measurable without
a browser, firmware voice wrapper, or physical module.

## ADDED Requirements

### Requirement: Unpatched operation

With `TRIGGER_UNPATCHED`, the engine SHALL sustain dial, DTMF and FSK entries and
SHALL run busy/ringback on their table-defined cadence, starting in the on phase.
Cadence SHALL use elapsed sample time independently of pitch and block size.
On/off edges SHALL have 0.001 s ramps within their scheduled on intervals.

#### Scenario: Continuous tone classes

- **WHEN** dial at HARMONICS 1/42, key 5 at 11/42, and FSK_0 at 39/42 are each
  rendered unpatched for 3.000 s at MIDI note 60 and TIMBRE 0.
- **THEN** after the first 0.020 s there are no 0.010 s RMS windows below 10%
  of steady RMS; spectra identify 350+440 Hz, 770+1336 Hz, and 2200 Hz respectively.

#### Scenario: Busy cadence

- **WHEN** busy at HARMONICS 27/42 is rendered unpatched for 4.000 s at note 60
  and TIMBRE 0.
- **THEN** 480+620 Hz sounds in [0,0.5), [1,1.5), [2,2.5), [3,3.5) seconds,
  and the intervening 0.500 s intervals are silent; measured edges are within
  0.010 s using 0.010 s RMS windows and a 10%-of-on-RMS threshold.

#### Scenario: Ringback cadence

- **WHEN** ringback at HARMONICS 29/42 is rendered unpatched for 12.000 s at
  note 60 and TIMBRE 0.
- **THEN** 440+480 Hz sounds in [0,2) and [6,8) seconds, with 4.000 s silent
  intervals [2,6) and [8,12); measured edges are within 0.010 s.

#### Scenario: Cadence restart and timebase

- **WHEN** selection enters busy at HARMONICS 27/42 from dial, and in separate
  runs enters ring at 29/42, at MIDI notes 48 and 72 using 1-, 7-, 12-, or 24-sample
  render partitions with control events at identical sample positions.
- **THEN** each incoming voice begins its on phase at selection acceptance,
  with a 0.005 s selection crossfade, and keeps its 0.5/0.5 s or 2/4 s cadence
  within 0.010 s regardless of pitch or partitioning; Reset restarts that phase.

### Requirement: Patched keypress bursts

With TRIG patched the engine SHALL remain silent between rising-edge-triggered
0.100 s keypress bursts for every entry, overriding busy/ring cadences. The
engine SHALL apply its own matched low-pass gates to MAIN and AUX and report
already-enveloped output. HARMONICS SHALL remain live during a burst.

#### Scenario: Periodic keypresses through the LPG

- **WHEN** key 5 at HARMONICS 11/42, note 60 and TIMBRE 0 receives triggers at
  t=0, 0.500, 1.000 and 1.500 s in a 2.000 s render.
- **THEN** both outputs contain 770+1336 Hz bursts lasting 0.100 +/- 0.010 s,
  with a 0.001 s opening, release beginning at 0.096 s and silence by 0.110 s
  after each edge (RMS below -80 dBFS in 0.005 s windows).
- **THEN** the LPG closes in brightness as well as amplitude: direct-render
  samples match the specified LowPassGate contour within 1e-6, and the engine
  reports already-enveloped output so the host adds no second envelope.

#### Scenario: Busy and ring become keypresses

- **WHEN** busy at 27/42 and ringback at 29/42 each receive 2 Hz triggers for
  3.000 s, at note 60 and TIMBRE 0.
- **THEN** each rising edge produces one 0.100 +/- 0.010 s burst of 480+620 Hz
  or 440+480 Hz respectively, including during what would be a free-running
  off interval, with silence by 0.110 s after each edge.

#### Scenario: Patched idle and gate length

- **WHEN** a driver holds patched TRIG low for 7.000 s, then sends one rising
  edge with either a 0.001 s gate or a 1.000 s held-high gate, using key 1 at
  3/42, note 60 and TIMBRE 0.
- **THEN** initial patched idle is silent; either gate produces exactly one
  0.100 +/- 0.010 s 697+1209 Hz burst; neither the falling edge nor continued
  high state starts another burst or changes its deadline.

#### Scenario: Retrigger and live selection

- **WHEN** key 1 at 3/42 is triggered at t=0 and t=0.050 s, and HARMONICS
  changes to key 2 at 5/42 at t=0.070 s, at note 60 and TIMBRE 0.
- **THEN** the second trigger extends the deadline to t=0.150 s without a
  phase reset; the 0.005 s crossfade changes 697+1209 Hz to 697+1336 Hz during
  the burst, with silence by t=0.160 s and no extra queued burst.

#### Scenario: Connection transitions

- **WHEN** unpatched ringback at 29/42 is switched to patched-low at t=0.500 s
  and switched back to unpatched at t=1.000 s, at note 60 and TIMBRE 0.
- **THEN** sound closes within 0.005 s of patching, stays silent without an
  edge, and unpatching restarts a 2.000 s on phase followed by 4.000 s off;
  waiting for triggers never causes an automatic unpatched fallback.
