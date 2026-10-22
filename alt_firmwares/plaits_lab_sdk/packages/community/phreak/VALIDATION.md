# Phreak v2 validation

Run date: 2026-10-21. macOS arm64, Python 3.14.6, Apple clang 21.0.0.
Commands run from the repository root. These are contributor evidence; the
catalog review reruns its own checks.

## Host gates

```sh
python3 -B alt_firmwares/plaits_lab_sdk/packages/community/phreak/tests/test_phreak.py
python3 -B alt_firmwares/plaits_lab_sdk/plaits_lab.py check \
  alt_firmwares/plaits_lab_sdk/packages/community/phreak --full
c++ -std=c++98 -pedantic-errors -DTEST -D_USE_MATH_DEFINES -isystem . \
  -I alt_firmwares/plaits_lab_sdk/packages/community/phreak/src \
  -c alt_firmwares/plaits_lab_sdk/packages/community/phreak/src/phreak_engine.cc -o /tmp/phreak_engine.o
```

| Gate | Result |
| --- | --- |
| Package tests | PASS: 22 tests in 4.2 s. |
| SDK `check --full` | PASS: metadata, source and licence policy, host compile, ASan/UBSan, all 32 declared previews (peak 0.438–0.638, RMS 0.106–0.367, absolute DC at most 0.00017), audio health. |
| Host CPU smoke | 13.1 ns/sample against 94.3 for stock two-op FM: about 0.1x. |
| Strict C++98 compile | PASS (`-pedantic-errors`, `-Wall -Werror` in the test build). |

Native cost by signal, per sample, against stock two-op FM (host only):

| Signal | ns/sample | vs two-op FM |
| --- | --- | --- |
| Two-tone entry (key 5) | about 16–35 | about 0.2–0.4x |
| Four-tone howler, ANSam, FSK, DPSK, QAM | about 15–20 | about 0.16–0.21x |
| V.34 line probe (21 tones) | about 15 | about 0.16x (was about 71 before the table; see below) |

## ARM and CPU estimate

```sh
python3 -B alt_firmwares/plaits_lab_sdk/plaits_lab.py check \
  alt_firmwares/plaits_lab_sdk/packages/community/phreak --full --arm
python3 -B alt_firmwares/plaits_lab_sdk/qemu/estimate.py \
  alt_firmwares/plaits_lab_sdk/packages/community/phreak --sweep
python3 -B alt_firmwares/plaits_lab_sdk/qemu/estimate.py \
  alt_firmwares/plaits_lab_sdk/packages/community/phreak \
  --harmonics 0.929 --morph 0.79 --timbre 0   # the V.34 probe
python3 -B alt_firmwares/plaits_lab_sdk/plaits_lab.py build \
  alt_firmwares/plaits_lab_sdk/packages/community/phreak --hardware --output /tmp/phreak.wav
```

| Gate | Result |
| --- | --- |
| ARM compile (`check --arm`) | PASS. Model size 15,368 bytes of flash: 9,092 code, 6,276 tables, labels and vtable. |
| Local hardware firmware | Links at 44,772 of 229,376 bytes with Phreak alone; v1 links at 34,340, so v2 costs about 10.4 KB more. |
| QEMU sweep (19 positions) | 47% of the CPU budget (likely 41–61%), worst at LINE fully analog: 245.9 instructions/sample; 1.30x spread. |
| V.34 probe, measured directly | 35% (31–45%) at LINE fully analog; 31% at noon. |
| Other modem signals, measured directly | 35–48% across ANSam, Bell 103/202, caller ID, V.22, training and `connect`, at LINE fully analog, noon and fully digital. |

The sweep alone was not enough. Its positions never land on the probe entry
(`modem`, MORPH 0.79), which, summing 21 sines per sample, measured 1,129
instructions/sample: about 217% of the budget (188–279%). The probe now plays
one generated cycle (`src/phreak_probe_table.h`, 1 KB). Every probe tone is a
multiple of the 150 Hz base, so the cycle, indexed by the base phase, is the
same sum at any pitch. The 512-point int16 table with linear interpolation
stays at least 47 dB below the signal; a test fits all 21 tones at a
transposed pitch. The change also cut the model from 19,584 bytes to 15,368.

Not covered by a static estimate: crossfades. While MORPH or HARMONICS moves,
two entries render for the 5 ms fade, so the hardware check should sweep
MORPH across the modem entries with the CPU meter on.

Tooling note: the committed `qemu/cycles_plugin.so` targets QEMU plugin API 6,
and Homebrew's QEMU 11.1.2 requires API 7. These runs used a local rebuild
with two callback signatures updated (`vcpu_tb_trans(tb, userdata)` and
`plugin_exit(userdata)`); the SDK's files were left unchanged.

## Hardware

_Pending, by hand on a Tall Dog Plaits clone: a `build --hardware --cpu-probe`
firmware, with LINE fully analog, the `connect` sequence and MORPH sweeps
across the modem entries as the worst cases, and the listening checklist in
`AUDITION.md`._

## Sources

Checked on 2026-10-21 against primary documents:

| Values | Source |
| --- | --- |
| UK dial (350 + 440), ringing, engaged, congestion, unobtainable | BT SIN 350 Issue 1.5, Table 1 |
| Europe 425 Hz dial, ringing 1/4, busy 0.5/0.5, congestion 0.25/0.25 | ETSI ES 201 970 V1.1.1, cl. 13.3, Table 6 |
| Japan 400 Hz dial, ringback (400 Hz modulated at 15–20 Hz, 1/2), busy 0.5/0.5 | NTT West analog interface specification v6.2, Table 3.3.8 |
| 2600 Hz; R1 MF digits, KP and ST | ITU-T Q.311 §2.1; ITU-T Q.320 |
| Coin tones, SIT (intercept and no-circuit, local), off-hook howler, caller ID timing, 1004 Hz | Bellcore SR-2275 Issue 3 §6.14.3.3, §6.17.3.4.3, §6.20.4, §6.21.2.1, p. 8-15 |
| V.8 ANSam | ITU-T V.8 (11/2000) §7.2 |
| V.21 channels; V.22 carriers and rate | ITU-T V.21 §3; ITU-T V.22 §2.1–2.2 |
| V.34 line probes and training rates | ITU-T V.34 (02/98) §10.1.2.4, §5.2–5.3 |
| Bell 103 and Bell 202 | TDK 73K302L datasheet |

Deliberate simplifications are listed in `README.md` under Accuracy.
