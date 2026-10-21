## Purpose

Provide an original, progressively degraded telephone-line sound on MAIN while
preserving a clean AUX reference.

## ADDED Requirements

### Requirement: Clean endpoint and band limitation

TIMBRE 0 SHALL bypass all bad-line processing. From 0 to 1/3 the engine SHALL
progressively mix in a fixed 300–3400 Hz telephone band-pass, without saturation
or digital reduction. This band SHALL not track pitch.

#### Scenario: True clean endpoint

- **WHEN** FSK_1 at HARMONICS 41/42, note 60 and TIMBRE 0 is rendered unpatched
  for 2.000 s, both from Reset and after returning from TIMBRE 1.
- **THEN** after 0.020 s settling MAIN equals AUX within 1e-6 or one PCM LSB,
  with 1200 Hz only and unwanted components below -40 dBc; no held samples,
  quantization or residual filter colour remains from the earlier treatment.

#### Scenario: Telephone band-pass

- **WHEN** unpatched renders hold TIMBRE at 1/3 for FSK_1 at 41/42 and notes
  24 and 60 (150 Hz and 1200 Hz), and FSK_0 at 39/42 and note 84 (8800 Hz).
- **THEN** steady MAIN attenuates 150 Hz and 8800 Hz by at least 10 dB relative
  to AUX, attenuates 1200 Hz by less than 3 dB, and adds no harmonic above
  -40 dBc; a helper sine sweep places the two -3 dB edges within 10% of 300 Hz
  and 3400 Hz, relative to the passband peak.

### Requirement: Progressive soft saturation

Between TIMBRE 1/3 and 2/3 the engine SHALL retain the band-pass and increase
the contribution and drive of bounded, odd-symmetric soft saturation. It SHALL
introduce neither bit quantization nor sample holding in this interval.

#### Scenario: Saturation after filtering

- **WHEN** FSK_1 at HARMONICS 41/42 and note 60 is rendered unpatched at TIMBRE
  1/3 and 2/3, each for 2.000 s.
- **THEN** steady MAIN at 2/3 retains the 1200 Hz fundamental and contains an
  odd harmonic, such as 3600 Hz, at least 6 dB stronger relative to the
  fundamental than at 1/3; AUX is unchanged, and MAIN does not clip or develop
  a DC mean above 0.01 full scale.
- **THEN** direct helper renders of positive/negative input samples satisfy
  odd symmetry within 1e-6 and the filter-then-saturator reference matches the
  engine within 1e-6, making the stage order testable.

### Requirement: Upper range digital reduction

Between TIMBRE 2/3 and 1 the engine SHALL retain filtering and saturation and
progressively mix in signed bit-depth and sample-rate reduction. At TIMBRE 1
the reduction SHALL be 5-bit symmetric quantization and one update every eight
samples, equivalent to 6000 updates/s at 48 kHz.

#### Scenario: Crushed endpoint

- **WHEN** FSK_1 at HARMONICS 41/42, note 60 and TIMBRE 1 is rendered unpatched
  for 2.000 s.
- **THEN** after 0.020 s settling MAIN values lie on the specified 5-bit grid
  `k*2/31` within one PCM LSB, change only at eight-sample hold boundaries, and
  exhibit additional spectral images; AUX remains an untreated 1200 Hz sine.
- **THEN** a TIMBRE 2/3 comparison has no enforced eight-sample holds, proving
  the reduction begins only in the upper third.

### Requirement: Stable treatment sweep

The engine SHALL keep finite bounded output and preserve clean AUX as TIMBRE
crosses stage boundaries. Mix and drive changes SHALL settle over 0.005 s;
intentional discrete bit/hold resolution changes are allowed in the upper third.

#### Scenario: Ordered sweep and recovery

- **WHEN** key 5 at HARMONICS 11/42, note 60 is rendered with TIMBRE sweeping
  0 to 1 over 6.000 s and 1 to 0 over a second 6.000 s, then held at 0 for
  0.100 s, unpatched.
- **THEN** MAIN moves through clean, band-limited, saturated and reduced
  regions in that order and reverses that order on return, with peak at most
  1.0 and finite samples; the final 0.020 s matches AUX within one PCM LSB.
- **THEN** AUX matches a constant-TIMBRE-0 reference within one PCM LSB for
  the entire run, with 770+1336 Hz throughout.
