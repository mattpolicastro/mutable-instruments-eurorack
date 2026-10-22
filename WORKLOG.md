# WORKLOG

## 2026-10-21

**What:** Took the specloop `phreak-engine` run to completion (20/20 tasks, coverage 52/52) and published it as a draft PR on the new public fork `mattpolicastro/mutable-instruments-eurorack`. Fixed two Plaits Lab SDK live-audition bugs and pushed them for Lyle (`sdk-audition-fixes`). Built a VCV Rack 2 audition module (`vcv-audition`) and a Phreak v2 prototype (`phreak-v2-proto`: seven tone systems including a dial-up modem table, blue-box panel), shared as a Mac build.

**Decisions:**
- The mutation gate now runs the candidate's package tests as well as the trusted checks; trusted-only could never pass (section 1 went from 1/8 to 8/8).
- Fork named `mutable-instruments-eurorack`; `docs/telephone/` published as-is.
- v2 control map follows the speech engines: HARMONICS = tone system, MORPH = tone, TIMBRE = line (clean at noon, analog CCW, digital CW), MACRO = twist.
- v2 skips OpenSpec/specloop; the hand-built prototype is the implementation (no crib to delete). Specloop comes back later for autonomous runs.
- VCV: LPG response/decay are hidden settings as on hardware (right-click edit swaps TIMBRE/MORPH); patched TRIG uses the engine's envelope or Plaits' LPG by config.
- SDK fixes: link wasm with `em++` (Emscripten 6.0.13 broke every engine); Plucked strikes report TRIG patched with a 50 ms gate.
- v2's V.34 probe plays one generated cycle (`src/phreak_probe_table.h`, 1 KB) instead of 21 sines. `qemu/estimate.py --sweep` reported 48% overall but never lands on the probe entry; measured directly it was 1,129 instructions/sample, about 217% of the budget. Now 35%, sweep worst 47% (LINE fully analog), model 15,368 bytes (was 19,584). Lesson: sweep the entries, not just the knob extremes, for table-selected engines.
- Colima on the Mac Studio now uses Rosetta (gcc crashed at random under QEMU); firmware `.bin`/`.elf` byte-identical across both. Restart Colima through launchd, never `colima restart`.

**Next:**
- Lyle replied: both fixes merged upstream (plus his Windows `em++.bat` tweak). He has a paid VCV Palette pending Library review, so we won't build or publish a config-loading port. Sent him the strike sweep CSV and a link to `sdk-vcv-test-bench` (pushed; one commit on his master: the single-engine test bench, spec in `openspec/changes/vcv-test-bench/`). On 2026-10-22 he asked for it as a PR so the credit is ours, with his tweaks to follow before it enters the contributor docs: lylepmills/eurorack#53 (one commit, `sdk-vcv-test-bench`). Task 4.2, the check in Rack, passed (all tasks done).
- v1 is superseded: PR #1 closed unmerged (branch `spec/phreak-engine` kept), specloop run aborted with its evidence kept in `~/.specloop/runs/phreak-engine/`. `specloop finish` would have marked the PR ready instead.
- v2 is on `telephone` as one commit (from `phreak-v2-proto`, which keeps the prototype history and the blue-box VCV theme, local only), alongside upstream's merged SDK fixes and the `sdk-vcv-test-bench` merge. Tables verified against primary sources; host gates, ARM compile and QEMU estimate pass (VALIDATION.md). Left for Matt: listening (AUDITION.md), a `--cpu-probe` build on the Tall Dog (LINE fully analog, `connect`, MORPH sweeps across modem entries), colour, the capability-review position, own envelope vs Plaits LPG, then `submit`. The themed VCV plugin with the cheaper probe is built in the `plaits-telephone-v2proto` worktree's `vcv/dist/`.
- Nightshift: enrol the renamed fork and grant the daemon's token access.
- Non-Mac VCV builds need the Rack cross toolchain.
- The SDK's committed `qemu/cycles_plugin.so` is plugin API 6; Homebrew QEMU 11.1.2 needs 7. A local rebuild needs two callback signatures changed (`vcpu_tb_trans(tb, userdata)`, `plugin_exit(userdata)`); not raised with Lyle (Matt's call).
- Revisit Phreak's tables and other CPU/flash wins before `submit` (leads in Claude memory `phreak-perf-followups`): label strings only tests read, 28-byte `Step` rows, duplicated voice code, the analog line as the CPU worst case.
