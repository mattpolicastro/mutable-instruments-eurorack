# Phreak

A Plaits Lab community package (`community/phreak`): telephone signalling as a
voice. HARMONICS picks a tone system (North America, the UK, Europe, Japan, the
blue box, specials and dial-up modems) and MORPH picks a sound within it. LINE
adds an analog or digital bad line, and TWIST balances two-tone pairs.

| SDK control | Panel control | Function |
| --- | --- | --- |
| `harmonics` | HARMONICS | **Tone system**: seven equal zones, with hysteresis. |
| `timbre` | TIMBRE | **Line**, MAIN only: clean at noon (with a ±0.02 dead zone). Counter-clockwise is an analog line: the 300–3400 Hz telephone band, then soft saturation. Clockwise is a digital line: the band, then bit and sample-rate reduction down to 5 bits. |
| `morph` | MORPH | **Tone**: the entries of the selected system in equal zones, with hysteresis and 0.005 s crossfades. |
| `macro` | Fourth control | **Twist**: the balance of a pair's low and high tones. Balanced at noon; one tone alone at either end, at the single-tone level. Single tones and the four-tone howler ignore it. |

MIDI note 60 (C4) plays the authentic frequencies below. FREQUENCY transposes
every component by the same ratio, and the modem symbol rates (and the answer
tone's AM and phase reversals) with it. Cadence and sequence timing do not
change with pitch. MAIN is
processed by LINE; AUX is the clean voice. They are two related mono outputs,
not a stereo pair.

**Articulation.** With TRIG unpatched, every entry plays: continuous tones
sustain, and cadences and sequences loop (a step of 0 s holds forever, as at the
end of `connect`). With TRIG patched, Phreak is silent between keypresses; each
rising edge restarts the entry from its first step and plays one 0.100 s burst
through a matched low-pass gate on both outputs. Gate length does not set the
duration. Phreak envelopes itself (`alreadyEnveloped`).

### Systems and entries

| HARMONICS | System | Entries |
|---|---|---|
| 0.000–0.143 (centre 0.071) | North America | 21 |
| 0.143–0.286 (centre 0.214) | UK (BT) | 5 |
| 0.286–0.429 (centre 0.357) | Europe (CEPT, 425 Hz) | 4 |
| 0.429–0.571 (centre 0.500) | Japan (NTT) | 3 |
| 0.571–0.714 (centre 0.643) | Blue box (Bell System R1 MF) | 13 |
| 0.714–0.857 (centre 0.786) | Specials | 7 |
| 0.857–1.000 (centre 0.929) | Modem | 12 |

#### North America

| MORPH centre | Entry | Sound at MIDI note 60 (Hz, seconds; steps loop) |
|---|---|---|
| 0.024 | `dial` | 350 + 440 |
| 0.071 | `key-1` | 697 + 1209 |
| 0.119 | `key-2` | 697 + 1336 |
| 0.167 | `key-3` | 697 + 1477 |
| 0.214 | `key-4` | 770 + 1209 |
| 0.262 | `key-5` | 770 + 1336 |
| 0.310 | `key-6` | 770 + 1477 |
| 0.357 | `key-7` | 852 + 1209 |
| 0.405 | `key-8` | 852 + 1336 |
| 0.452 | `key-9` | 852 + 1477 |
| 0.500 | `key-0` | 941 + 1336 |
| 0.548 | `hash` | 941 + 1477 |
| 0.595 | `star` | 941 + 1209 |
| 0.643 | `busy` | 480 + 620 for 0.5 s; silence for 0.5 s |
| 0.690 | `ring` | 440 + 480 for 2 s; silence for 4 s |
| 0.738 | `key-a` | 697 + 1633 |
| 0.786 | `key-b` | 770 + 1633 |
| 0.833 | `key-c` | 852 + 1633 |
| 0.881 | `key-d` | 941 + 1633 |
| 0.929 | `fsk-space` | 2200 |
| 0.976 | `fsk-mark` | 1200 |

#### UK (BT)

| MORPH centre | Entry | Sound at MIDI note 60 (Hz, seconds; steps loop) |
|---|---|---|
| 0.100 | `dial` | 350 + 440 |
| 0.300 | `ring` | 400 + 450 for 0.4 s; silence for 0.2 s; 400 + 450 for 0.4 s; silence for 2 s |
| 0.500 | `engaged` | 400 for 0.375 s; silence for 0.375 s |
| 0.700 | `congestion` | 400 for 0.4 s; silence for 0.35 s; 400 for 0.225 s; silence for 0.525 s |
| 0.900 | `unobtainable` | 400 |

#### Europe (CEPT, 425 Hz)

| MORPH centre | Entry | Sound at MIDI note 60 (Hz, seconds; steps loop) |
|---|---|---|
| 0.125 | `dial` | 425 |
| 0.375 | `ring` | 425 for 1 s; silence for 4 s |
| 0.625 | `busy` | 425 for 0.5 s; silence for 0.5 s |
| 0.875 | `congestion` | 425 for 0.25 s; silence for 0.25 s |

#### Japan (NTT)

| MORPH centre | Entry | Sound at MIDI note 60 (Hz, seconds; steps loop) |
|---|---|---|
| 0.167 | `dial` | 400 |
| 0.500 | `ring` | 392 + 408 for 1 s; silence for 2 s |
| 0.833 | `busy` | 400 for 0.5 s; silence for 0.5 s |

#### Blue box (Bell System R1 MF)

| MORPH centre | Entry | Sound at MIDI note 60 (Hz, seconds; steps loop) |
|---|---|---|
| 0.038 | `seize` | 2600 |
| 0.115 | `kp` | 1100 + 1700 |
| 0.192 | `mf-1` | 700 + 900 |
| 0.269 | `mf-2` | 700 + 1100 |
| 0.346 | `mf-3` | 900 + 1100 |
| 0.423 | `mf-4` | 700 + 1300 |
| 0.500 | `mf-5` | 900 + 1300 |
| 0.577 | `mf-6` | 1100 + 1300 |
| 0.654 | `mf-7` | 700 + 1500 |
| 0.731 | `mf-8` | 900 + 1500 |
| 0.808 | `mf-9` | 1100 + 1500 |
| 0.885 | `mf-0` | 1300 + 1500 |
| 0.962 | `st` | 1500 + 1700 |

#### Specials

| MORPH centre | Entry | Sound at MIDI note 60 (Hz, seconds; steps loop) |
|---|---|---|
| 0.071 | `red-box-nickel` | 1700 + 2200 for 0.066 s; silence for 0.934 s |
| 0.214 | `red-box-dime` | 1700 + 2200 for 0.066 s; silence for 0.066 s; 1700 + 2200 for 0.066 s; silence for 0.802 s |
| 0.357 | `red-box-quarter` | 1700 + 2200 for 0.033 s; silence for 0.033 s; 1700 + 2200 for 0.033 s; silence for 0.033 s; 1700 + 2200 for 0.033 s; silence for 0.033 s; 1700 + 2200 for 0.033 s; silence for 0.033 s; 1700 + 2200 for 0.033 s; silence for 0.67 s |
| 0.500 | `sit-intercept` | 913.8 for 0.274 s; 1370.6 for 0.274 s; 1776.7 for 0.38 s; silence for 2 s |
| 0.643 | `sit-no-circuit` | 985.2 for 0.38 s; 1428.5 for 0.38 s; 1776.7 for 0.38 s; silence for 2 s |
| 0.786 | `off-hook-howler` | 1400 + 2060 + 2450 + 2600 for 0.1 s; silence for 0.1 s |
| 0.929 | `test-1004` | 1004 |

#### Modem

| MORPH centre | Entry | Sound at MIDI note 60 (Hz, seconds; steps loop) |
|---|---|---|
| 0.042 | `answer` | V.8 ANSam: 2100 Hz, 15 Hz AM at 20%, phase reversal every 0.45 s |
| 0.125 | `bell-103-originate` | FSK mark 1270 / space 1070, 300 baud |
| 0.208 | `bell-103-answer` | FSK mark 2225 / space 2025, 300 baud |
| 0.292 | `v21-channel-1` | FSK mark 980 / space 1180, 300 baud |
| 0.375 | `v21-channel-2` | FSK mark 1650 / space 1850, 300 baud |
| 0.458 | `bell-202` | FSK mark 1200 / space 2200, 1200 baud |
| 0.542 | `caller-id` | 440 + 480 for 2 s; silence for 0.5 s; FSK mark 1200 / space 2200, 1200 baud for 0.6 s; silence for 2.9 s |
| 0.625 | `v22-originate` | 4-phase DPSK, 1200 Hz carrier, 600 baud |
| 0.708 | `v22-answer` | 4-phase DPSK, 2400 Hz carrier, 600 baud |
| 0.792 | `v34-probe` | tones every 150 Hz from 150 to 3750, except 900, 1200, 1800, 2400 |
| 0.875 | `training` | QAM training, 1920 Hz carrier, 3200 baud |
| 0.958 | `connect` | the full dial-up sequence: dial tone, 555-0123, ringback, answer tone, V.21 exchange, the V.34 L1 and L2 line probes, DPSK, training, then silence (about 13.5 s) |

### Accuracy

Values were checked against primary sources on 2026-10-21: BT SIN 350 (UK),
ETSI ES 201 970 (Europe), NTT's analog interface specification (Japan), ITU-T
Q.311/Q.320 (2600 Hz and R1 MF), Bellcore SR-2275 (coin tones, SIT, howler,
caller ID, the 1004 Hz test tone), and ITU-T V.8, V.21, V.22 and V.34, with
Bell 103/202 from modem datasheets. `VALIDATION.md` lists them.

Deliberate simplifications:
- The modem entries carry random data. They sound like the real signals
  without implementing a protocol, including caller ID's lead-in.
- Japan's ringback (400 Hz modulated at 15-20 Hz) is a 392 + 408 Hz beating
  pair: the right 16 Hz flutter, but no 400 Hz carrier.
- Levels are uniform within an entry, so UK congestion's louder short burst and
  V.34's louder L1 probe are not reproduced.
- The training hiss uses one valid V.34 setting, 3200 baud on 1920 Hz; real
  modems chose among eleven rate and carrier pairs.
- `test-1004` is the North American test tone (ITU-T O.6 recommends 1020 Hz).

### Capability review (Fast FM, linear TZFM, hard sync)

Proposed for the catalog review: decline **Fast FM** and **linear TZFM**, and
use the **shared hard-sync fallback**. Telephone signals have no meaningful
audio-rate or through-zero frequency modulation; a sign-reversed DTMF pair or
modem carrier is not a telephone signal. Ordinary exponential FM through pitch,
and V/OCT, transpose every entry as expected.

### Cost

The QEMU estimate puts Phreak at about 47% of the hardware CPU budget at
worst (likely 41–61%), with LINE fully analog the heaviest setting. The V.34
probe plays one generated cycle rather than 21 sines, which took it from about
twice the budget to about a third. Phreak takes 15,368 bytes of flash: about
9 KB of code and 6 KB of tables and entry labels. Hardware is the authority:
see `VALIDATION.md` for the estimate and the `--cpu-probe` build.

### Development

```sh
python3 alt_firmwares/plaits_lab_sdk/packages/community/phreak/tests/test_phreak.py
python3 alt_firmwares/plaits_lab_sdk/plaits_lab.py check alt_firmwares/plaits_lab_sdk/packages/community/phreak --full
```

The tests compile the engine and `tests/render_cases.cc` with strict C++98
diagnostics. They check every table entry against an independent reference,
cadence and sequence timing, the modem signals, selection and crossfades, both
sides of LINE, TWIST, articulation, pitch, extreme controls, block-size
independence and the declared previews. Set `CXX` to choose the compiler.
Generated objects, binaries and WAVs stay in temporary directories.

`src/phreak_probe_table.h` is generated: one cycle of the V.34 probe, which
plays all 21 tones for the cost of one lookup. After changing the probe, run
`python3 tests/make_probe_table.py` from the package directory; a test fails
while the header is stale.

The package source is MIT-licensed, copyright 2026 Matt Policastro; see
`LICENSE`. Shared Plaits and stmlib headers are included from the repository
with their upstream notices; no upstream DSP source is vendored here.
